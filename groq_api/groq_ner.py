"""
Groq-Powered Smart NER — استخراج ذكي للبيانات الطبية
Extracts multiple medical fields from free-form patient text using Groq LLM.
Falls back gracefully if Groq is unavailable.
"""

import json
import re
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# الحقول السريرية الأصل الـ 8 (bmi محسوب تلقائياً) مع أنواعها ونطاقاتها.
# القيم القانونية تطابق تماماً ما يتوقعه engine/feature_deriver.derive().
FIELD_SCHEMA = {
    "age": {"type": "int", "min": 1, "max": 120},
    "gender": {"type": "choice", "values": ["male", "female"]},
    "height_cm": {"type": "int", "min": 50, "max": 250},
    "weight_kg": {"type": "float", "min": 20, "max": 400},
    "smoking_status": {"type": "choice",
                       "values": ["non-smoker", "ex-smoker", "current smoker"]},
    "workplace_type": {"type": "choice", "values": ["office", "factory"]},
    "environmental_hazards": {"type": "list",
                              "values": ["stress", "pollution", "noise",
                                         "dust", "chemicals", "shift work"]},
    "family_history": {"type": "choice", "values": ["yes", "no"]},
    # --- clinical risk factors ---
    "hypertension": {"type": "choice", "values": ["yes", "no"]},
    "diabetes": {"type": "choice", "values": ["yes", "no"]},
    "cardiovascular_disease": {"type": "choice", "values": ["yes", "no"]},
    "chronic_diseases": {"type": "choice", "values": ["yes", "no"]},
    "gestational_diabetes": {"type": "choice", "values": ["yes", "no"]},
    "hba1c": {"type": "float", "min": 3, "max": 20},
    "cholesterol": {"type": "int", "min": 80, "max": 500},
    "bmi": {"type": "float", "min": 10, "max": 80},
    "obesity": {"type": "choice", "values": ["yes", "no"]},
    "years_smoked": {"type": "int", "min": 0, "max": 90},
    "years_since_quit": {"type": "int", "min": 0, "max": 90},
}

SYSTEM_PROMPT = """You are a clinical data extraction system. Extract structured occupational/clinical fields from patient text.
The patient may write in Arabic or English. Extract ALL fields you can identify.

Fields to extract (use EXACTLY these names and value formats — all lowercase):

1. age: integer (1-120)
   - Arabic: "عمري 45", "عندي 55 سنة" — English: "I am 45 years old", "age 55"

2. gender: MUST be exactly "male" or "female"
   - "ذكر"/"رجل" → "male", "أنثى"/"امرأة" → "female"

3. height_cm: integer centimeters (50-250)
   - "طولي 175 سم" → 175, "1.80 m" → 180, "height 168 cm" → 168

4. weight_kg: number kilograms (20-400)
   - "وزني 95 كيلو" → 95, "weight 80 kg" → 80

5. smoking_status: MUST be one of: "non-smoker", "ex-smoker", "current smoker"
   - "غير مدخّن"/"لا أدخّن" → "non-smoker"
   - "مدخّن سابق"/"أقلعت عن التدخين"/"quit smoking" → "ex-smoker"
   - "مدخّن"/"أدخّن حالياً"/"I smoke" → "current smoker"

6. workplace_type: MUST be "office" or "factory"
   - "مكتب"/"أعمل في مكتب" → "office"
   - "مصنع"/"معمل"/"أعمل في مصنع" → "factory"

7. environmental_hazards: a JSON array (list) of any of:
   ["stress", "pollution", "noise", "dust", "chemicals", "shift work"]
   - "توتر"/"ضغط نفسي" → "stress", "تلوّث" → "pollution", "ضوضاء" → "noise",
     "غبار" → "dust", "مواد كيميائية" → "chemicals",
     "عمل بالورديات"/"shift" → "shift work"
   - "أتعرّض للغبار والمواد الكيميائية" → ["dust", "chemicals"]
   - "لا يوجد"/"none" → [] (or omit the field)

8. family_history: MUST be "yes" or "no" — family history of heart disease
   - "يوجد تاريخ عائلي"/"نعم" → "yes", "لا يوجد"/"لا" → "no"

9. hypertension: "yes"/"no" — high blood pressure
   - "ضغط"/"ارتفاع ضغط"/"مصاب بالضغط" → "yes"

10. diabetes: "yes"/"no" — diabetes mellitus
   - "سكري"/"مصاب بالسكر" → "yes"

11. cardiovascular_disease: "yes"/"no" — heart / cardiovascular disease
   - "أمراض قلب"/"مريض قلب"/"شرايين" → "yes"

12. chronic_diseases: "yes"/"no" — any chronic disease
   - "أمراض مزمنة"/"مرض مزمن" → "yes"

13. gestational_diabetes: "yes"/"no" — history of gestational diabetes (females)
   - "سكري الحمل" → "yes"

14. hba1c: number (%) — glycated hemoglobin / السكر التراكمي
   - "التراكمي 8"/"HbA1c 6.5" → 8 / 6.5

15. cholesterol: integer mg/dL
   - "الكوليسترول 250"/"cholesterol 280" → 250 / 280

16. obesity: "yes"/"no" — obesity
   - "سمنة"/"بدين"/"وزن زائد"/"obese" → "yes"

17. years_smoked: integer — number of years the patient has smoked
   - "أدخّن من 30 سنة"/"smoked for 20 years" → 30 / 20

18. years_since_quit: integer — years since quitting smoking
   - "أقلعت من 5 سنوات"/"quit 5 years ago" → 5

19. bmi: number — body mass index (only if explicitly stated)
   - "مؤشر كتلة الجسم 32"/"BMI 28" → 32 / 28

CRITICAL RULES:
- Return ONLY a valid JSON object. No extra text, no markdown.
- For EACH extracted field, also return a confidence score in [0.0, 1.0]
  in a parallel key "<field>_confidence" so the schema stays flat:
      { "<field>": <value>, "<field>_confidence": <float 0..1> }
- High confidence (>= 0.9) = explicit numeric or unambiguous keyword.
- Medium (0.7-0.9) = clear qualitative phrasing.
- Low (< 0.7) = inferred. Skip the field entirely if confidence < 0.5.
- Do NOT guess values not mentioned. Use EXACT lowercase field names/values.

Example input: "أنا رجل عمري 55 سنة، طولي 175 وأزن 95، مدخّن وأشتغل بمصنع وأتعرّض للغبار"
Example output: {
  "age": 55, "age_confidence": 0.98,
  "gender": "male", "gender_confidence": 0.97,
  "height_cm": 175, "height_cm_confidence": 0.95,
  "weight_kg": 95, "weight_kg_confidence": 0.95,
  "smoking_status": "current smoker", "smoking_status_confidence": 0.9,
  "workplace_type": "factory", "workplace_type_confidence": 0.92,
  "environmental_hazards": ["dust"], "environmental_hazards_confidence": 0.85
}"""


class GroqNER:
    """
    Smart NER using Groq LLM — extracts medical fields from free-form text.
    Falls back to empty dict if Groq is unavailable.
    """

    def __init__(self, groq_client):
        self.groq_client = groq_client
        # Per-field confidence from the last extract() call. The integrated
        # chatbot reads this so the UI can display a "Groq NER applied"
        # message with the confidence per extracted field.
        self.last_confidences: Dict[str, float] = {}

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract medical fields from free-form patient text.

        Args:
            text: Patient's free-form message (Arabic or English)

        Returns:
            Dict of validated extracted fields. Empty dict if extraction fails.
            Example: {"Age": 45, "BloodPressure": "150/90", "ChestPain": "ATA"}

        Side effect: writes per-field confidence scores from the same
        Groq response into self.last_confidences, e.g.
            {"Age": 0.98, "BloodPressure": 0.99, "ChestPain": 0.72}
        """
        self.last_confidences = {}
        if not text or not text.strip():
            return {}

        if not self.groq_client or not self.groq_client.is_available:
            logger.warning("Groq not available for Smart NER")
            return {}

        try:
            response = self.groq_client.chat(
                system_prompt=SYSTEM_PROMPT,
                user_message=text.strip(),
                temperature=0.1,
                max_tokens=500
            )

            if not response:
                logger.warning("Empty response from Groq NER")
                return {}

            parsed = self._parse_response(response)

            # Separate value entries from confidence entries.
            raw_confidences = {}
            value_only = {}
            for k, v in parsed.items():
                if k.endswith('_confidence'):
                    field = k[:-len('_confidence')]
                    try:
                        raw_confidences[field] = max(0.0, min(1.0, float(v)))
                    except (TypeError, ValueError):
                        continue
                else:
                    value_only[k] = v

            validated = self._validate_fields(value_only)

            # Keep only confidences for fields that actually validated.
            self.last_confidences = {
                f: raw_confidences.get(f, 0.85)  # safe default if model omitted it
                for f in validated.keys()
            }

            logger.info(
                f"Groq NER extracted {len(validated)} fields with confidence "
                f"{self.last_confidences} from: '{text[:50]}...'"
            )
            return validated

        except Exception as e:
            logger.error(f"Smart NER extraction failed: {e}")
            return {}

    def _parse_response(self, response: str) -> Dict:
        """Parse JSON from Groq response, handle malformed JSON."""
        response = response.strip()

        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try extracting any JSON object
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse Groq NER response: {response[:100]}")
        return {}

    def _validate_fields(self, extracted: Dict) -> Dict:
        """Validate each extracted field against known schema."""
        validated = {}

        for field, value in extracted.items():
            if field not in FIELD_SCHEMA:
                logger.debug(f"Ignoring unknown field: {field}")
                continue

            schema = FIELD_SCHEMA[field]
            validated_value = self._validate_single_field(field, value, schema)

            if validated_value is not None:
                validated[field] = validated_value
            else:
                logger.debug(f"Validation failed for {field}={value}")

        return validated

    def _validate_single_field(self, field: str, value: Any, schema: Dict) -> Optional[Any]:
        """Validate a single field value against its schema."""
        field_type = schema["type"]

        if field_type == "int":
            try:
                val = int(float(str(value)))
                if schema["min"] <= val <= schema["max"]:
                    return val
            except (ValueError, TypeError):
                pass
            return None

        elif field_type == "float":
            try:
                val = round(float(str(value)), 1)
                if schema["min"] <= val <= schema["max"]:
                    return val
            except (ValueError, TypeError):
                pass
            return None

        elif field_type == "choice":
            # Handle both string and numeric choices
            valid_values = schema["values"]
            # Try exact match
            if value in valid_values:
                return value
            # Try string conversion
            str_val = str(value).strip()
            for v in valid_values:
                if str(v).lower() == str_val.lower():
                    return v
            return None

        elif field_type == "list":
            # Normalise to a list, then keep only known hazard values
            # (case-insensitive, substring-tolerant). Returns [] if none match,
            # which feature_deriver handles as "no hazards".
            valid_values = schema["values"]
            if isinstance(value, str):
                items = [p.strip() for p in value.replace(";", ",").split(",")]
            elif isinstance(value, (list, tuple)):
                items = [str(p).strip() for p in value]
            else:
                return None
            out = []
            for item in items:
                low = item.lower()
                for v in valid_values:
                    if v in low or low in v:
                        if v not in out:
                            out.append(v)
                        break
            return out if out else None

        elif field_type == "pattern":
            str_val = str(value).strip()
            if re.match(schema["pattern"], str_val):
                # Additional BP validation
                if field == "BloodPressure":
                    parts = str_val.split("/")
                    sys_val = int(parts[0])
                    dia_val = int(parts[1])
                    if 60 <= sys_val <= 250 and 30 <= dia_val <= 150:
                        return str_val
                    return None
                return str_val
            return None

        return None
