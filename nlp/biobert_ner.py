

import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger('biobert_ner')


_AR_DIACRITICS = re.compile(r'[ً-ٰٟـ]')

_NORMAL_WORDS = {
    # Modern Standard Arabic
    'طبيعي', 'طبيعى', 'طبيعيه', 'طبيعية', 'طبيعيا',
    'عادي', 'عادى', 'عاديه', 'عادية',
    'سليم', 'سليمه', 'سليمة',
    # Iraqi / Levantine dialect
    'منيح', 'زين', 'كويس', 'كويسه', 'تمام', 'بخير', 'مظبوط', 'مضبوط',
    # English (single tokens)
    'normal', 'ok', 'okay', 'fine', 'healthy', 'good', 'great',
    'perfect', 'excellent', 'fantastic', 'awesome', 'stable',
    'steady', 'regular', 'alright', 'allright', 'swell', 'lovely',
    'clear', 'controlled', 'managed', 'unremarkable',
}

# Multi-word English phrases that signal "normal" (checked separately)
_NORMAL_PHRASES_EN = (
    'all good', 'all clear', 'all fine', 'no problem', 'no problems',
    'no issues', 'no issue', 'nothing wrong', 'within range',
    'within normal range', 'within normal', 'under control',
    'in control', 'no complaints',
)

# Sensible defaults for the 8 clinical base fields when a field is absent.
# (gender intentionally omitted — there is no neutral default for it.)
_NORMAL_DEFAULTS = {
    'smoking_status':        'non-smoker',
    'workplace_type':        'office',
    'environmental_hazards': [],
    'family_history':        'no',
}


class BioBERTNER:
    """
    BioBERT Named Entity Recognition - Unified Strategy
    استراتيجية موحدة لاستخراج الحقول السريرية الأساسية الثمانية
    """

    def __init__(self):
        """تهيئة BioBERT NER مع استراتيجية موحدة"""
        self.medical_patterns = self._init_medical_patterns()
        self.medical_keywords = self._init_medical_keywords()
        logger.info("BioBERT NER initialized with unified strategy")

    @staticmethod
    def _normalize_ar(text: str) -> str:
        """
        تطبيع النص العربي:
        - إزالة التشكيل (الحركات)
        - توحيد الألف: أ إ آ ٱ → ا
        - توحيد الياء: ى → ي
        - توحيد التاء المربوطة: ة → ه
        """
        if not text:
            return ''
        text = _AR_DIACRITICS.sub('', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ٱ', 'ا')
        text = text.replace('ى', 'ي').replace('ؤ', 'و').replace('ئ', 'ي')
        text = text.replace('ة', 'ه')
        return text.lower().strip()

    @classmethod
    def _is_normal_only(cls, text: str) -> bool:
        """
        هل النص يدل على 'طبيعي' فقط — كلمة واحدة أو عبارة قصيرة بالإنكليزية
        مثل 'all good' / 'no problem' / 'within normal range'؟
        """
        if not text:
            return False
        clean = cls._normalize_ar(text)
        if re.search(r'\d', clean):
            return False

        # Check English multi-word phrases first (e.g., "all good", "no problem")
        clean_squeezed = re.sub(r'\s+', ' ', clean).strip()
        if any(phrase in clean_squeezed for phrase in _NORMAL_PHRASES_EN):
            # Make sure the WHOLE message is just the phrase (+ filler words)
            stripped = clean_squeezed
            for phrase in _NORMAL_PHRASES_EN:
                stripped = stripped.replace(phrase, ' ')
            leftover = re.findall(r'[؀-ۿa-z]+', stripped)
            filler = {'is', 'are', 'it', 'the', 'a', 'my', 'im', "i'm", 'feel', 'feeling'}
            if all(t in filler for t in leftover):
                return True

        # Single-word / standalone token check
        tokens = re.findall(r'[؀-ۿa-z]+', clean)
        if not tokens:
            return False
        filler = {'هو', 'هي', 'و', 'يكون', 'is', 'are', 'it', 'the', 'a',
                  'my', 'im', 'feel', 'feeling', 'all', 'pretty', 'quite', 'very'}
        meaningful = [t for t in tokens if t not in filler]
        if not meaningful:
            return False
        return all(t in _NORMAL_WORDS for t in meaningful)

    @classmethod
    def _smart_normal_default(cls, field_name: str, text: str):
        """
        إذا كان النص يدل على 'طبيعي' فقط، أرجع القيمة الافتراضية للحقل.
        وإلا أرجع None لترك المنطق الأصلي يكمل عمله.
        """
        if cls._is_normal_only(text):
            return _NORMAL_DEFAULTS.get(field_name)
        return None

    def _init_medical_patterns(self) -> Dict:
        """
        تهيئة Regex Patterns للحقول السريرية الأساسية

        UNIFIED PATTERN STRUCTURE:
        كل حقل له مجموعة patterns تبحث عن:
        1. العربية والإنجليزية
        2. مع/بدون علامات ترقيم
        3. أشكال مختلفة للتعبير
        """
        return {
            # 1. age (العمر)
            'age': [
                r'(?:عمر(?:ي)?|Age)\s*:?\s*(\d{1,3})\s*(?:سنة|عام|year|yr)?',
                r'(\d{1,3})\s*(?:سنة|عام|year|years\s*old|yrs?)',
                r'أنا\s+(?:عمري)?\s*(\d{1,3})',
                r'I\s+am\s+(\d{1,3})\s*(?:years\s*old)?',
            ],

            # 2. gender (الجنس)
            'gender': [
                r'(?:جنس|الجنس|Sex|Gender)\s*:?\s*(ذكر|أنثى|انثى|رجل|امرأة|امراه|Male|Female|M|F)',
                r'\b(ذكر|أنثى|انثى|رجل|امرأة|امراه|Male|Female)\b',
            ],

            # 3. height_cm (الطول)
            'height_cm': [
                # Arabic: طولي 175 سم  /  طول 1.80 متر
                r'(?:طول(?:ي)?|الطول)\s*:?\s*(\d{1,3}(?:\.\d+)?)\s*(سم|cm|سنتيمتر|سنتي)?',
                r'(?:طول(?:ي)?|الطول)\s*:?\s*(\d(?:\.\d+)?)\s*(م|متر|m|meter)\b',
                # English: height 175 cm  /  height 1.8 m
                r'(?:height|tall)\s*:?\s*(\d{1,3}(?:\.\d+)?)\s*(cm|centimet)',
                r'(?:height|tall)\s*:?\s*(\d(?:\.\d+)?)\s*(m|meter)\b',
                # bare value with explicit unit anywhere
                r'(\d{1,3}(?:\.\d+)?)\s*(cm|سم)\b',
                r'(\d(?:\.\d+)?)\s*(m|متر)\b',
            ],

            # 4. weight_kg (الوزن)
            'weight_kg': [
                r'(?:وزن(?:ي)?|الوزن)\s*:?\s*(\d{1,3}(?:\.\d+)?)\s*(?:كيلو(?:غرام|غم)?|كغم|كجم|كغ|kg|kilo)?',
                r'(?:weight|weigh)\s*:?\s*(\d{1,3}(?:\.\d+)?)\s*(?:kg|kilo|kgs)?',
                r'(\d{1,3}(?:\.\d+)?)\s*(?:كيلو(?:غرام|غم)?|كغم|كجم|kg)\b',
            ],
        }

    def _init_medical_keywords(self) -> Dict:
        """
        تهيئة Keywords للحقول السريرية الأساسية

        UNIFIED KEYWORD STRUCTURE:
        كل حقل له keywords للبحث النصي عندما تفشل patterns
        """
        return {
            # age / height / weight — numeric, handled by patterns
            'age': {},
            'height_cm': {},
            'weight_kg': {},

            # gender (الجنس)
            'gender': {
                'male':   ['ذكر', 'رجل', 'male', 'man'],
                'female': ['أنثى', 'انثى', 'امرأة', 'امراه', 'female', 'woman'],
            },

            # smoking_status (حالة التدخين)
            'smoking_status': {
                'non-smoker': [
                    'غير مدخن', 'لا أدخن', 'لا ادخن', 'لست مدخن', 'لا أدخّن',
                    'non-smoker', 'non smoker', 'nonsmoker', 'never smoked',
                    "don't smoke", 'do not smoke', 'no smoking',
                ],
                'ex-smoker': [
                    'مدخن سابق', 'مدخّن سابق', 'سابقا مدخن', 'أقلعت', 'اقلعت',
                    'توقفت عن التدخين', 'تركت التدخين', 'former smoker',
                    'ex-smoker', 'ex smoker', 'quit smoking', 'used to smoke',
                    'stopped smoking',
                ],
                'current smoker': [
                    'مدخن', 'مدخّن', 'أدخن', 'ادخن', 'أدخّن', 'smoker', 'smoke',
                    'i smoke', 'current smoker', 'currently smoke',
                ],
            },

            # workplace_type (نوع مكان العمل)
            'workplace_type': {
                'office':  ['مكتب', 'office', 'desk job', 'administrative'],
                'factory': ['مصنع', 'معمل', 'factory', 'plant', 'industrial'],
            },

            # environmental_hazards (المخاطر البيئية) — list output
            'environmental_hazards': {
                'stress':     ['توتر', 'ضغط نفسي', 'إجهاد', 'اجهاد', 'stress'],
                'pollution':  ['تلوث', 'تلوّث', 'pollution', 'polluted'],
                'noise':      ['ضوضاء', 'ضجيج', 'noise', 'noisy'],
                'dust':       ['غبار', 'أتربة', 'اتربة', 'dust'],
                'chemicals':  ['مواد كيميائية', 'كيماويات', 'كيميائية', 'chemical', 'chemicals'],
                'shift work': ['ورديات', 'وردية', 'شفتات', 'شفت', 'shift work', 'shifts', 'night shift'],
            },

            # family_history (التاريخ العائلي)
            'family_history': {
                'indicators': [
                    'تاريخ عائلي', 'تاريخ عائلى', 'وراثي', 'وراثة', 'عائلي',
                    'family history', 'genetic', 'hereditary', 'runs in the family',
                ],
                'yes': ['نعم', 'يوجد', 'موجود', 'عندي', 'لدي', 'yes', 'positive', 'present', 'have'],
                'no':  ['لا يوجد', 'لا توجد', 'ليس لدي', 'ما عندي', 'لا', 'no', 'none', 'negative', 'absent'],
            },
        }

    def extract_entities(self, text: str) -> Dict[str, any]:
        """
        استخراج الحقول السريرية الأساسية الثمانية باستخدام استراتيجية موحدة

        UNIFIED EXTRACTION STRATEGY:
        كل حقل يتبع نفس الاستراتيجية:
        1. استدعاء extraction method الخاص به
        2. if value is not None: → تخزين

        Args:
            text: النص المُدخل

        Returns:
            dict: الحقول السريرية المُستخرجة (المفاتيح القانونية فقط)
        """
        entities = {}

        # 1. age (العمر)
        age = self._extract_age(text)
        if age is not None:
            entities['age'] = age

        # 2. gender (الجنس)
        gender = self._extract_gender(text)
        if gender is not None:
            entities['gender'] = gender

        # 3. height_cm (الطول)
        height = self._extract_height_cm(text)
        if height is not None:
            entities['height_cm'] = height

        # 4. weight_kg (الوزن)
        weight = self._extract_weight_kg(text)
        if weight is not None:
            entities['weight_kg'] = weight

        # 5. smoking_status (حالة التدخين)
        smoking = self._extract_smoking_status(text)
        if smoking is not None:
            entities['smoking_status'] = smoking

        # 6. workplace_type (نوع مكان العمل)
        workplace = self._extract_workplace_type(text)
        if workplace is not None:
            entities['workplace_type'] = workplace

        # 7. environmental_hazards (المخاطر البيئية)
        hazards = self._extract_environmental_hazards(text)
        if hazards:
            entities['environmental_hazards'] = hazards

        # 8. family_history (التاريخ العائلي)
        family = self._extract_family_history(text)
        if family is not None:
            entities['family_history'] = family

        # 9-18. الحقول السريرية (احتياطي عند نفاد Groq)
        entities.update(self._extract_clinical(text))

        logger.info(f"Extracted {len(entities)} entities from text")
        return entities

    # خريطة الأمراض (نعم/لا) → كلماتها المفتاحية
    _DISEASE_KW = {
        'hypertension': ('ضغط', 'ارتفاع الضغط', 'hypertension', 'blood pressure'),
        'diabetes': ('سكري', 'سكر', 'diabet', 'diabetic'),
        'cardiovascular_disease': ('امراض قلب', 'مرض قلب', 'قلب', 'شريان', 'cardio', 'heart disease', 'cvd'),
        'chronic_diseases': ('مزمن', 'chronic'),
        'obesity': ('سمنة', 'بدين', 'بدانة', 'obes', 'overweight'),
        'gestational_diabetes': ('سكري الحمل', 'سكري حمل', 'حمل', 'gestational'),
    }
    _NEG_TOKENS = (' لا ', 'ولا', 'بدون', 'ليس', 'no ', 'not ', 'without', 'لايوجد', 'لا يوجد')

    def _extract_clinical(self, text: str) -> Dict[str, any]:
        """استخراج الحقول السريرية بالـ regex/الكلمات (احتياطي بدون Groq)."""
        out: Dict[str, any] = {}
        norm = self._normalize_ar(text)

        # أمراض نعم/لا — موجودة الكلمة بدون نفي قبلها → yes، مع نفي → no
        for field, kws in self._DISEASE_KW.items():
            for kw in kws:
                kwn = self._normalize_ar(kw)
                idx = norm.find(kwn)
                if idx == -1:
                    continue
                window = norm[max(0, idx - 9):idx]
                negated = any(tok.strip() and self._normalize_ar(tok) in window
                              for tok in self._NEG_TOKENS)
                out[field] = 'no' if negated else 'yes'
                break

        # قيم رقمية — تُطبَّع الكلمات المفتاحية مثل النص (ة→ه، ؤ→و ...)
        def _grp(keywords):
            return '|'.join(re.escape(self._normalize_ar(k)) for k in keywords)

        def num(keywords, dec=True, suffix=''):
            unit = r'(\d+(?:\.\d+)?)' if dec else r'(\d+)'
            m = re.search(r'(?:' + _grp(keywords) + r')\D{0,15}' + unit + suffix, norm)
            return m.group(1) if m else None

        yr = r'\s*(?:' + _grp(['سنة', 'سنوات', 'عام', 'سنه']) + r'|year)'

        hba1c = num(['تراكمي', 'hba1c', 'a1c'])
        if hba1c:
            out['hba1c'] = float(hba1c)
        chol = num(['كوليسترول', 'كولسترول', 'cholesterol'], dec=False)
        if chol:
            out['cholesterol'] = int(chol)
        bmi = num(['مؤشر كتلة', 'كتلة الجسم', 'كتلة', 'bmi'])
        if bmi:
            out['bmi'] = float(bmi)
        ys = num(['دخن', 'ادخن', 'تدخين', 'smok'], dec=False, suffix=yr)
        if ys:
            out['years_smoked'] = int(ys)
        yq = num(['اقلع', 'توقف', 'quit', 'stopped'], dec=False, suffix=yr)
        if yq:
            out['years_since_quit'] = int(yq)

        return out

    # ========================================
    # EXTRACTION METHODS - UNIFIED STRATEGY
    # جميع Methods تتبع نفس الاستراتيجية:
    # 1. Try Regex Patterns
    # 2. Try Keyword Matching
    # 3. Normalize Value
    # ========================================

    def _extract_age(self, text: str) -> Optional[int]:
        """
        استخراج العمر (age)

        Strategy:
        1. Try regex patterns
        2. Validate range (1-120)
        3. Return int
        """
        for pattern in self.medical_patterns['age']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 1 <= age <= 120:
                    return age
        return None

    def _extract_gender(self, text: str) -> Optional[str]:
        """
        استخراج الجنس (gender) → "male" | "female"

        Strategy:
        1. Try regex patterns
        2. Try keyword matching
        3. Normalize to male/female
        """
        # Step 1: Try regex patterns
        for pattern in self.medical_patterns['gender']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).lower()
                if value in ['ذكر', 'رجل', 'male', 'm']:
                    return 'male'
                elif value in ['أنثى', 'انثى', 'امرأة', 'امراه', 'female', 'f']:
                    return 'female'

        # Step 2: Keyword matching
        text_lower = text.lower()
        if any(kw in text_lower for kw in self.medical_keywords['gender']['male']):
            return 'male'
        elif any(kw in text_lower for kw in self.medical_keywords['gender']['female']):
            return 'female'

        return None

    def _extract_height_cm(self, text: str) -> Optional[float]:
        """
        استخراج الطول (height_cm) بالسنتيمتر

        Strategy:
        1. Try regex patterns (سم / cm / متر / m)
        2. Convert meters → centimeters ("1.80 m" → 180)
        3. Validate range (50-260 cm)
        4. Return number (int when whole)
        """
        for pattern in self.medical_patterns['height_cm']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = (match.group(2) or '').lower() if match.lastindex and match.lastindex >= 2 else ''

                # Determine if the value is in meters and convert to cm.
                is_meter = unit in ('م', 'متر', 'm', 'meter')
                if is_meter or (not unit and value < 3):
                    value = value * 100.0

                if 50 <= value <= 260:
                    return int(value) if value == int(value) else round(value, 1)
        return None

    def _extract_weight_kg(self, text: str) -> Optional[float]:
        """
        استخراج الوزن (weight_kg) بالكيلوغرام

        Strategy:
        1. Try regex patterns (كيلو / كغم / kg)
        2. Validate range (20-400 kg)
        3. Return number (int when whole)
        """
        for pattern in self.medical_patterns['weight_kg']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if 20 <= value <= 400:
                    return int(value) if value == int(value) else round(value, 1)
        return None

    def _extract_smoking_status(self, text: str) -> Optional[str]:
        """
        استخراج حالة التدخين (smoking_status)
        → "non-smoker" | "ex-smoker" | "current smoker"

        Strategy:
        1. Keyword matching, most-specific first (non-smoker, then ex-smoker,
           then current smoker) so that "غير مدخّن" / "مدخّن سابق" are not
           mis-classified as "current smoker".
        2. Smart normal handler — "طبيعي" alone → non-smoker
        """
        clean = self._normalize_ar(text)
        kws = self.medical_keywords['smoking_status']

        # Negation / non-smoker first (most specific).
        if any(self._normalize_ar(kw) in clean for kw in kws['non-smoker']):
            return 'non-smoker'
        # Ex-smoker next (e.g. "مدخّن سابق", "أقلعت").
        if any(self._normalize_ar(kw) in clean for kw in kws['ex-smoker']):
            return 'ex-smoker'
        # Current smoker last.
        if any(self._normalize_ar(kw) in clean for kw in kws['current smoker']):
            return 'current smoker'

        # Smart normal handler — "طبيعي" alone → non-smoker
        smart = self._smart_normal_default('smoking_status', text)
        if smart is not None:
            return smart

        return None

    def _extract_workplace_type(self, text: str) -> Optional[str]:
        """
        استخراج نوع مكان العمل (workplace_type) → "office" | "factory"

        Strategy:
        1. Keyword matching (factory most specific first)
        """
        clean = self._normalize_ar(text)
        kws = self.medical_keywords['workplace_type']

        if any(self._normalize_ar(kw) in clean for kw in kws['factory']):
            return 'factory'
        if any(self._normalize_ar(kw) in clean for kw in kws['office']):
            return 'office'

        return None

    def _extract_environmental_hazards(self, text: str) -> List[str]:
        """
        استخراج المخاطر البيئية (environmental_hazards) → list

        Strategy:
        1. Scan for every hazard keyword; collect all matches into a list.
        2. Preserve canonical order; no duplicates.
        """
        clean = self._normalize_ar(text)
        hazards: List[str] = []
        for canonical, keywords in self.medical_keywords['environmental_hazards'].items():
            if any(self._normalize_ar(kw) in clean for kw in keywords):
                hazards.append(canonical)
        return hazards

    def _extract_family_history(self, text: str) -> Optional[str]:
        """
        استخراج التاريخ العائلي (family_history) → "yes" | "no"

        Strategy:
        1. Require a family-history indicator.
        2. Resolve yes/no, checking negation ("لا يوجد") first.
        3. Smart normal handler — "طبيعي" alone → no
        """
        clean = self._normalize_ar(text)
        kws = self.medical_keywords['family_history']

        has_indicator = any(self._normalize_ar(kw) in clean for kw in kws['indicators'])
        if has_indicator:
            # Negation first (more specific, e.g. "لا يوجد تاريخ عائلي").
            if any(self._normalize_ar(kw) in clean for kw in kws['no']):
                return 'no'
            if any(self._normalize_ar(kw) in clean for kw in kws['yes']):
                return 'yes'
            # Indicator mentioned without an explicit yes/no qualifier →
            # presence of the topic implies a positive family history.
            return 'yes'

        # Smart normal handler — "طبيعي" alone → no
        smart = self._smart_normal_default('family_history', text)
        if smart is not None:
            return smart

        return None

    def get_entity_confidence(self, entity_name: str, entity_value: any) -> float:
        """
        حساب ثقة الاستخراج (confidence score)

        Args:
            entity_name: اسم المعلومة
            entity_value: قيمة المعلومة

        Returns:
            نسبة الثقة (0.0 - 1.0)
        """
        # نسبة الثقة الافتراضية
        base_confidence = 0.85

        # رفع الثقة للحقول ذات القيم الرقمية الدقيقة
        if entity_name in ['age', 'height_cm', 'weight_kg']:
            return 0.95

        # ثقة عالية للحقول التصنيفية الواضحة
        if entity_name in ['gender', 'workplace_type']:
            return 0.9

        return base_confidence
