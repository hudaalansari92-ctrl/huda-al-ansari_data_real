

from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
import json
import logging

try:
    # العتبات الطبية الموحّدة — المصدر الوحيد للحقيقة
    from config.field_definitions import (
        MEDICAL_THRESHOLDS,
        VALUE_RANGES,
        ASKED_FIELDS,
    )
except Exception:  # pragma: no cover - fallback إذا تعذّر الاستيراد
    MEDICAL_THRESHOLDS = {
        "age_young": 45,
        "age_middle": 60,
        "age_senior": 75,
        "bmi_normal": 25.0,
        "bmi_overweight": 30.0,
    }
    VALUE_RANGES = {
        "age": (0, 150),
        "height_cm": (50, 250),
        "weight_kg": (20, 400),
        "bmi": (10, 80),
    }
    ASKED_FIELDS = [
        "age", "gender", "height_cm", "weight_kg",
        "smoking_status", "workplace_type",
        "environmental_hazards", "family_history",
    ]

logger = logging.getLogger('self_dialog_manager')


# المخاطر المهنية التي نعتبرها عوامل خطر عند العمل في مصنع
OCCUPATIONAL_HAZARDS = {"chemicals", "dust", "stress", "shift work"}


@dataclass
class InternalThought:
    """فكرة داخلية للـ Chatbot"""
    thought: str  # الفكرة بالعربية
    thought_en: str  # الفكرة بالإنجليزية
    category: str  # analysis, inference, decision, warning
    confidence: float  # درجة الثقة (0.0-1.0)
    timestamp: datetime
    language: str = 'ar'  # اللغة المستخدمة


@dataclass
class SelfUpdate:
    """تحديث ذاتي للحالة"""
    update_type: str  # fact_added, inference_made, priority_changed, warning_triggered
    details: Dict
    timestamp: datetime
    impact_level: str  # low, medium, high, critical


class SelfDialogManager:
    """
    مدير الحوار الذاتي
    يدير تفكير الـ Chatbot الداخلي وكيفية تحديث نفسه
    (استدلال سريري-مهني: العمر، مؤشر كتلة الجسم، التدخين،
     بيئة العمل، التاريخ العائلي).
    """

    def __init__(self, language: str = 'ar'):
        """
        تهيئة مدير الحوار الذاتي

        Args:
            language: اللغة الافتراضية ('ar' أو 'en')
        """
        self.language = language
        self.internal_thoughts: List[InternalThought] = []
        self.self_updates: List[SelfUpdate] = []
        self.current_facts: Dict = {}
        self.current_inferences: Dict = {}
        self.current_risk_level: str = 'LOW'
        self.confidence_score: float = 0.0

    def analyze_answer(self,
                      fact_type: str,
                      fact_value: str,
                      existing_facts: Dict) -> InternalThought:
        """
        تحليل إجابة المستخدم والتحدث مع النفس عنها

        Args:
            fact_type: نوع الحقيقة (age, smoking_status, workplace_type, ...)
            fact_value: قيمة الحقيقة
            existing_facts: الحقائق الموجودة حالياً

        Returns:
            InternalThought: فكرة داخلية
        """
        thought_ar = self._generate_thought_ar(fact_type, fact_value, existing_facts)
        thought_en = self._generate_thought_en(fact_type, fact_value, existing_facts)

        confidence = self._calculate_thought_confidence(fact_type, fact_value)

        internal_thought = InternalThought(
            thought=thought_ar,
            thought_en=thought_en,
            category='analysis',
            confidence=confidence,
            timestamp=datetime.now(),
            language=self.language
        )

        self.internal_thoughts.append(internal_thought)
        logger.info(f"[تحليل داخلي] {fact_type}: {thought_ar}")

        return internal_thought

    def _generate_thought_ar(self,
                            fact_type: str,
                            fact_value: str,
                            existing_facts: Dict) -> str:
        """توليد أفكار داخلية بالعربية"""
        thoughts = {
            'age': {
                'elderly': f"العمر {fact_value} سنة... فئة كبار السن (≥75)، عامل خطر مهم! ",
                'senior': f"العمر {fact_value} سنة... فئة متقدمة (≥60)، عامل خطر. ",
                'middle': f"العمر {fact_value} سنة... فئة متوسطة، انتبه قليلاً.",
                'info': f"تم تسجيل العمر: {fact_value} سنة"
            },
            'weight_kg': {
                'obese': f"الوزن {fact_value} كغ مع هذا الطول... سمنة (BMI≥30)، عامل خطر! ",
                'overweight': f"الوزن {fact_value} كغ... وزن زائد (BMI 25-30). ",
                'normal': f"الوزن {fact_value} كغ... ضمن المعدل الطبيعي. ",
                'info': f"تم تسجيل الوزن: {fact_value} كغ"
            },
            'smoking_status': {
                'high': "مدخّن حالي! هذا عامل خطر عالٍ! ",
                'moderate': "مدخّن سابق... خطر متوسط، يستحق المتابعة.",
                'low': "غير مدخّن... ممتاز! ",
                'info': "تم تسجيل حالة التدخين"
            },
            'workplace_type': {
                'high': "يعمل في مصنع... بيئة قد تحمل مخاطر مهنية. ",
                'low': "يعمل في مكتب... بيئة منخفضة المخاطر نسبياً. ",
                'info': "تم تسجيل نوع بيئة العمل"
            },
            'environmental_hazards': {
                'high': f"تعرّض لمخاطر بيئية: {fact_value}... عامل خطر مهني! ",
                'low': "لا توجد مخاطر بيئية كبيرة... جيد! ",
                'info': "تم تسجيل المخاطر البيئية"
            },
            'family_history': {
                'yes': "تاريخ عائلي إيجابي! عامل خطر وراثي مهم! ",
                'no': "لا يوجد تاريخ عائلي... جيد! ",
                'info': "تم تسجيل التاريخ العائلي"
            }
        }

        # اختر الفكرة المناسبة
        if fact_type in thoughts:
            category = self._categorize_value(fact_type, fact_value, existing_facts)
            return thoughts[fact_type].get(category, f"تم تسجيل {fact_type}: {fact_value}")

        return f"تم تسجيل {fact_type}: {fact_value}"

    def _generate_thought_en(self,
                            fact_type: str,
                            fact_value: str,
                            existing_facts: Dict) -> str:
        """توليد أفكار داخلية بالإنجليزية"""
        thoughts = {
            'age': {
                'elderly': f"Age {fact_value}... Elderly (>=75), important risk factor! ",
                'senior': f"Age {fact_value}... Senior (>=60), risk factor. ",
                'middle': f"Age {fact_value}... Middle-aged, some caution.",
                'info': f"Age registered: {fact_value} years"
            },
            'weight_kg': {
                'obese': f"Weight {fact_value} kg at this height... Obese (BMI>=30), risk factor! ",
                'overweight': f"Weight {fact_value} kg... Overweight (BMI 25-30). ",
                'normal': f"Weight {fact_value} kg... Normal range. ",
                'info': f"Weight registered: {fact_value} kg"
            },
            'smoking_status': {
                'high': "Current smoker! High risk factor! ",
                'moderate': "Ex-smoker... Moderate risk, worth monitoring.",
                'low': "Non-smoker... Excellent! ",
                'info': "Smoking status registered"
            },
            'workplace_type': {
                'high': "Works in a factory... Environment may carry occupational hazards. ",
                'low': "Works in an office... Relatively low-risk environment. ",
                'info': "Workplace type registered"
            },
            'environmental_hazards': {
                'high': f"Exposed to environmental hazards: {fact_value}... Occupational risk! ",
                'low': "No major environmental hazards... Good! ",
                'info': "Environmental hazards registered"
            },
            'family_history': {
                'yes': "Positive family history! Important hereditary risk factor! ",
                'no': "No family history... Good! ",
                'info': "Family history registered"
            }
        }

        if fact_type in thoughts:
            category = self._categorize_value(fact_type, fact_value, existing_facts)
            return thoughts[fact_type].get(category, f"{fact_type} registered: {fact_value}")

        return f"{fact_type} registered: {fact_value}"

    def _categorize_value(self, fact_type: str, fact_value: str,
                          existing_facts: Optional[Dict] = None) -> str:
        """تصنيف قيمة الحقيقة (high, moderate, low, obese, senior, yes, no, ...)"""
        fact_value_str = str(fact_value).lower()
        existing_facts = existing_facts or {}

        # تصنيف العمر إلى فئات (young/middle/senior/elderly)
        if fact_type == 'age':
            age = self._extract_number(fact_value)
            if age is None:
                return 'info'
            if age >= MEDICAL_THRESHOLDS['age_senior']:      # >=75
                return 'elderly'
            elif age >= MEDICAL_THRESHOLDS['age_middle']:    # >=60
                return 'senior'
            elif age >= MEDICAL_THRESHOLDS['age_young']:     # >=45
                return 'middle'
            return 'info'

        # تصنيف الوزن حسب مؤشر كتلة الجسم (يحتاج الطول)
        elif fact_type == 'weight_kg':
            bmi = self._compute_bmi(
                self._extract_number(fact_value),
                self._extract_number(existing_facts.get('height_cm'))
            )
            if bmi is None:
                return 'info'
            if bmi >= MEDICAL_THRESHOLDS['bmi_overweight']:  # >=30
                return 'obese'
            elif bmi >= MEDICAL_THRESHOLDS['bmi_normal']:    # >=25
                return 'overweight'
            return 'normal'

        # تصنيف حالة التدخين
        elif fact_type == 'smoking_status':
            if 'current' in fact_value_str or 'حالي' in fact_value_str:
                return 'high'
            elif 'ex' in fact_value_str or 'سابق' in fact_value_str:
                return 'moderate'
            elif 'non' in fact_value_str or 'غير' in fact_value_str:
                return 'low'
            return 'info'

        # تصنيف بيئة العمل
        elif fact_type == 'workplace_type':
            if 'factory' in fact_value_str or 'مصنع' in fact_value_str:
                return 'high'
            elif 'office' in fact_value_str or 'مكتب' in fact_value_str:
                return 'low'
            return 'info'

        # تصنيف المخاطر البيئية
        elif fact_type == 'environmental_hazards':
            hazards = self._extract_hazards(fact_value)
            if hazards & OCCUPATIONAL_HAZARDS:
                return 'high'
            elif hazards:
                return 'low'
            return 'low'

        # تصنيف التاريخ العائلي (نعم/لا)
        elif fact_type == 'family_history':
            if 'yes' in fact_value_str or 'نعم' in fact_value_str:
                return 'yes'
            return 'no'

        return 'info'

    def _extract_number(self, value) -> Optional[float]:
        """استخراج رقم من النص أو القيمة الرقمية"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            import re
            numbers = re.findall(r'\d+\.?\d*', str(value))
            if numbers:
                return float(numbers[0])
        except Exception:
            pass
        return None

    def _compute_bmi(self, weight_kg: Optional[float],
                     height_cm: Optional[float]) -> Optional[float]:
        """حساب مؤشر كتلة الجسم BMI = الوزن(كغ) / (الطول(م))^2"""
        try:
            if weight_kg and height_cm and height_cm > 0:
                height_m = height_cm / 100.0
                return weight_kg / (height_m * height_m)
        except Exception:
            pass
        return None

    def _extract_hazards(self, value) -> set:
        """استخراج مجموعة المخاطر البيئية من قائمة أو نص"""
        if isinstance(value, (list, tuple, set)):
            return {str(h).strip().lower() for h in value if str(h).strip()}
        text = str(value).lower()
        found = set()
        known = {"stress", "pollution", "noise", "dust", "chemicals", "shift work"}
        for hazard in known:
            if hazard in text:
                found.add(hazard)
        return found

    def _calculate_thought_confidence(self, fact_type: str, fact_value: str) -> float:
        """حساب درجة ثقة الفكرة الداخلية"""
        # أرقام واضحة = ثقة عالية
        if self._extract_number(fact_value) is not None:
            return 0.95
        # حقول تصنيفية معروفة = ثقة عالية
        elif fact_type in ('smoking_status', 'workplace_type',
                           'family_history', 'gender', 'environmental_hazards'):
            return 0.90
        return 0.75

    def infer_from_facts(self, facts: Dict) -> InternalThought:
        """
        الاستنتاج من الحقائق المجمعة
        الـ Chatbot يفكر: "ماذا تعني هذه الحقائق مجموعة؟"
        """
        inference_ar = self._generate_inference_ar(facts)
        inference_en = self._generate_inference_en(facts)

        confidence = self._calculate_inference_confidence(facts)

        internal_thought = InternalThought(
            thought=inference_ar,
            thought_en=inference_en,
            category='inference',
            confidence=confidence,
            timestamp=datetime.now(),
            language=self.language
        )

        self.internal_thoughts.append(internal_thought)
        logger.info(f"[استنتاج] {inference_ar}")

        return internal_thought

    def _safe_int(self, value, default=0) -> int:
        """تحويل آمن للقيمة إلى عدد صحيح"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                # استخراج الأرقام من النص
                import re
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
            return default
        except Exception:
            return default

    def _collect_risk_factors(self, facts: Dict, lang: str = 'ar') -> List[str]:
        """عدّ عوامل الخطر السريرية-المهنية وإرجاع وصفها."""
        parts: List[str] = []

        # العمر
        age = self._extract_number(facts.get('age'))
        if age is not None:
            if age >= MEDICAL_THRESHOLDS['age_senior']:      # >=75
                parts.append("العمر ≥75 (كبار السن)" if lang == 'ar'
                             else "Age >=75 (elderly)")
            elif age >= MEDICAL_THRESHOLDS['age_middle']:    # >=60
                parts.append("العمر ≥60" if lang == 'ar' else "Age >=60")

        # مؤشر كتلة الجسم
        bmi = self._extract_number(facts.get('bmi'))
        if bmi is None:
            bmi = self._compute_bmi(
                self._extract_number(facts.get('weight_kg')),
                self._extract_number(facts.get('height_cm'))
            )
        if bmi is not None:
            if bmi >= MEDICAL_THRESHOLDS['bmi_overweight']:  # >=30
                parts.append("سمنة (BMI≥30)" if lang == 'ar'
                             else "Obese (BMI>=30)")
            elif bmi >= MEDICAL_THRESHOLDS['bmi_normal']:    # >=25
                parts.append("وزن زائد (BMI 25-30)" if lang == 'ar'
                             else "Overweight (BMI 25-30)")

        # التدخين
        smoking = str(facts.get('smoking_status', '')).lower()
        if 'current' in smoking:
            parts.append("مدخّن حالي" if lang == 'ar' else "Current smoker")
        elif 'ex' in smoking:
            parts.append("مدخّن سابق" if lang == 'ar' else "Ex-smoker")

        # التاريخ العائلي
        if str(facts.get('family_history', '')).lower() in ('yes', 'نعم', 'true', '1'):
            parts.append("تاريخ عائلي إيجابي" if lang == 'ar'
                         else "Positive family history")

        # المخاطر المهنية (مصنع + مخاطر بيئية)
        workplace = str(facts.get('workplace_type', '')).lower()
        hazards = self._extract_hazards(facts.get('environmental_hazards', []))
        occ_hazards = hazards & OCCUPATIONAL_HAZARDS
        if 'factory' in workplace and occ_hazards:
            joined = ', '.join(sorted(occ_hazards))
            parts.append(f"خطر مهني (مصنع: {joined})" if lang == 'ar'
                         else f"Occupational risk (factory: {joined})")
        elif occ_hazards:
            joined = ', '.join(sorted(occ_hazards))
            parts.append(f"مخاطر بيئية ({joined})" if lang == 'ar'
                         else f"Environmental hazards ({joined})")

        return parts

    def _generate_inference_ar(self, facts: Dict) -> str:
        """توليد استنتاج بالعربية"""
        inference_parts = self._collect_risk_factors(facts, lang='ar')
        risk_factors = len(inference_parts)

        # بناء الاستنتاج
        if risk_factors >= 4:
            return f" CRITICAL! لدينا {risk_factors} عوامل خطر: {', '.join(inference_parts)}. خطر صحي-مهني عالٍ جداً!"
        elif risk_factors >= 3:
            return f" SERIOUS! {risk_factors} عوامل خطر: {', '.join(inference_parts)}. خطر عالٍ، يستحق متابعة دقيقة."
        elif risk_factors >= 2:
            return f" لدينا {risk_factors} عوامل خطر: {', '.join(inference_parts)}. يجب الاستمرار في التقييم."
        elif risk_factors == 1:
            return f" عامل خطر واحد: {inference_parts[0]}. ننتبه له ونكمل."
        else:
            return "الحمد لله، لا توجد عوامل خطر واضحة حتى الآن."

    def _generate_inference_en(self, facts: Dict) -> str:
        """توليد استنتاج بالإنجليزية"""
        inference_parts = self._collect_risk_factors(facts, lang='en')
        risk_factors = len(inference_parts)

        if risk_factors >= 4:
            return f" CRITICAL! {risk_factors} risk factors: {', '.join(inference_parts)}. Very high clinical-occupational risk!"
        elif risk_factors >= 3:
            return f" SERIOUS! {risk_factors} risk factors: {', '.join(inference_parts)}. High risk, close monitoring needed."
        elif risk_factors >= 2:
            return f" {risk_factors} risk factors: {', '.join(inference_parts)}. Continue assessment."
        elif risk_factors == 1:
            return f" One risk factor: {inference_parts[0]}. Note it and continue."
        else:
            return "Good news, no obvious risk factors detected so far."

    def _calculate_inference_confidence(self, facts: Dict) -> float:
        """حساب ثقة الاستنتاج"""
        # كل حقيقة تضيف ثقة
        facts_count = len([v for v in facts.values() if v])
        base_confidence = min(0.5 + (facts_count * 0.1), 0.95)
        return base_confidence

    def make_decision(self, facts: Dict, inferences: Dict) -> InternalThought:
        """
        اتخاذ قرار بناءً على الحقائق والاستنتاجات
        "ماذا يجب أن أسأل التالي؟"
        """
        decision_ar = self._generate_decision_ar(facts, inferences)
        decision_en = self._generate_decision_en(facts, inferences)

        internal_thought = InternalThought(
            thought=decision_ar,
            thought_en=decision_en,
            category='decision',
            confidence=0.85,
            timestamp=datetime.now(),
            language=self.language
        )

        self.internal_thoughts.append(internal_thought)
        logger.info(f"[قرار] {decision_ar}")

        return internal_thought

    def _generate_decision_ar(self, facts: Dict, inferences: Dict) -> str:
        """توليد قرار بالعربية"""
        answered = len([v for v in facts.values() if v])

        # تحديد السؤال التالي (ترتيب الأولوية السريرية)
        if not facts.get('age'):
            return "يجب أسأل عن العمر أولاً - أساس التقييم! "
        elif not facts.get('smoking_status'):
            return "حالة التدخين عامل خطر مهم! سأسأل عنها التالي."
        elif not facts.get('weight_kg') or not facts.get('height_cm'):
            return "أحتاج الطول والوزن لحساب مؤشر كتلة الجسم (BMI)."
        elif not facts.get('workplace_type'):
            return "بيئة العمل مهمة للمخاطر المهنية. يجب السؤال عنها."
        elif not facts.get('environmental_hazards'):
            return "المخاطر البيئية في العمل تستحق السؤال."
        elif not facts.get('family_history'):
            return "التاريخ العائلي عامل خطر وراثي. سأسأل عنه."
        else:
            return f"تم جمع {answered} معلومات. سأكمل الأسئلة الباقية."

    def _generate_decision_en(self, facts: Dict, inferences: Dict) -> str:
        """توليد قرار بالإنجليزية"""
        answered = len([v for v in facts.values() if v])

        if not facts.get('age'):
            return "Must ask about age first - basis of assessment! "
        elif not facts.get('smoking_status'):
            return "Smoking status is an important risk factor! Will ask next."
        elif not facts.get('weight_kg') or not facts.get('height_cm'):
            return "Need height and weight to compute BMI."
        elif not facts.get('workplace_type'):
            return "Workplace type matters for occupational risk. Must ask."
        elif not facts.get('environmental_hazards'):
            return "Environmental hazards at work are worth asking about."
        elif not facts.get('family_history'):
            return "Family history is a hereditary risk factor. Will ask."
        else:
            return f"Collected {answered} data points. Continue with remaining questions."

    def trigger_warning(self,
                       warning_type: str,
                       severity: str,
                       details: Dict) -> InternalThought:
        """
        تنبيه من الخطر
        الـ Chatbot يتحدث مع نفسه: "هذا خطير جداً!"
        """
        warning_ar = self._generate_warning_ar(warning_type, severity, details)
        warning_en = self._generate_warning_en(warning_type, severity, details)

        internal_thought = InternalThought(
            thought=warning_ar,
            thought_en=warning_en,
            category='warning',
            confidence=1.0,
            timestamp=datetime.now(),
            language=self.language
        )

        self.internal_thoughts.append(internal_thought)
        logger.warning(f"[تحذير] {warning_ar}")

        return internal_thought

    def _generate_warning_ar(self, warning_type: str, severity: str, details: Dict) -> str:
        """توليد تحذير بالعربية"""
        warnings = {
            'critical_symptoms': {
                'critical': " تحذير حرج! مؤشرات صحية-مهنية خطيرة تتطلب اهتماماً فورياً!",
                'high': " تحذير مهم! عوامل خطر خطيرة!",
                'medium': " انتبه! هذه مؤشرات تحتاج متابعة."
            },
            'multiple_risk_factors': {
                'critical': " خطر صحي-مهني عالٍ جداً! (4+ عوامل خطر)",
                'high': " خطر صحي-مهني عالٍ! (3+ عوامل خطر)",
                'medium': "خطر متوسط. يجب متابعة دقيقة."
            },
            'occupational_risk': {
                'critical': " بيئة عمل عالية الخطورة مع تعرّض لمخاطر متعددة!",
                'high': " مخاطر مهنية مهمة في بيئة العمل!",
                'medium': "مخاطر مهنية تحتاج انتباهاً."
            }
        }

        if warning_type in warnings:
            return warnings[warning_type].get(severity, "تحذير: هناك مؤشرات قد تحتاج اهتمام.")

        return f"تحذير: {warning_type}"

    def _generate_warning_en(self, warning_type: str, severity: str, details: Dict) -> str:
        """توليد تحذير بالإنجليزية"""
        warnings = {
            'critical_symptoms': {
                'critical': " CRITICAL WARNING! Serious clinical-occupational indicators need immediate attention!",
                'high': " IMPORTANT WARNING! Serious risk factors!",
                'medium': " Caution! These indicators need monitoring."
            },
            'multiple_risk_factors': {
                'critical': " Very high clinical-occupational risk! (4+ risk factors)",
                'high': " High clinical-occupational risk! (3+ risk factors)",
                'medium': "Moderate risk. Close monitoring required."
            },
            'occupational_risk': {
                'critical': " High-hazard work environment with multiple exposures!",
                'high': " Significant occupational hazards in the workplace!",
                'medium': "Occupational hazards need attention."
            }
        }

        if warning_type in warnings:
            return warnings[warning_type].get(severity, "Warning: Indicators may need attention.")

        return f"Warning: {warning_type}"

    def self_update(self,
                   update_type: str,
                   details: Dict) -> SelfUpdate:
        """
        تحديث الحالة الذاتية
        الـ Chatbot يحدث نفسه
        """
        impact_level = self._calculate_impact(update_type, details)
        update = SelfUpdate(
            update_type=update_type,
            details=details,
            timestamp=datetime.now(),
            impact_level=impact_level
        )

        self.self_updates.append(update)
        logger.info(f"[تحديث ذاتي] {update_type}: {impact_level}")

        return update

    def _calculate_impact(self, update_type: str, details: Dict) -> str:
        """حساب مستوى التأثير"""
        if update_type in ['warning_triggered', 'critical_symptom']:
            return 'critical'
        elif update_type in ['risk_level_changed', 'inference_made']:
            return 'high'
        elif update_type in ['priority_changed', 'fact_added']:
            return 'medium'
        return 'low'

    def get_internal_monologue(self) -> str:
        """الحصول على سلسلة التفكير الداخلية الكاملة"""
        monologue = " [سلسلة التفكير الداخلية]\n" + "="*50 + "\n"

        for thought in self.internal_thoughts[-5:]:  # آخر 5 أفكار
            monologue += f" {thought.thought}\n"

        return monologue

    def get_summary(self) -> Dict:
        """ملخص حالة الـ Chatbot"""
        return {
            'thoughts_count': len(self.internal_thoughts),
            'updates_count': len(self.self_updates),
            'last_thought': self.internal_thoughts[-1] if self.internal_thoughts else None,
            'current_risk_level': self.current_risk_level,
            'confidence_score': self.confidence_score,
            'internal_monologue': self.get_internal_monologue()
        }


# مثال على الاستخدام
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # إنشاء مدير الحوار الذاتي
    dialog_manager = SelfDialogManager(language='ar')

    # محاكاة حوار (الحقول السريرية الجديدة)
    facts = {
        'age': 67,
        'gender': 'male',
        'height_cm': 175,
        'weight_kg': 98,
        'smoking_status': 'current smoker',
        'workplace_type': 'factory',
        'environmental_hazards': ['dust', 'chemicals'],
        'family_history': 'yes',
    }

    # تحليل إجابة
    print("\n1. تحليل الإجابة:")
    print("" * 50)
    thought = dialog_manager.analyze_answer('age', '67', facts)
    print(f"الفكرة: {thought.thought}")
    print(f"الثقة: {thought.confidence}")

    # الاستنتاج
    print("\n2. الاستنتاج:")
    print("" * 50)
    inference = dialog_manager.infer_from_facts(facts)
    print(f"الاستنتاج: {inference.thought}")

    # القرار
    print("\n3. القرار:")
    print("" * 50)
    decision = dialog_manager.make_decision(facts, {})
    print(f"القرار: {decision.thought}")

    # التحذير
    print("\n4. التحذير:")
    print("" * 50)
    warning = dialog_manager.trigger_warning(
        'multiple_risk_factors',
        'critical',
        {'count': 4}
    )
    print(f"التحذير: {warning.thought}")

    # الملخص
    print("\n5. الملخص:")
    print("" * 50)
    summary = dialog_manager.get_summary()
    print(f"عدد الأفكار: {summary['thoughts_count']}")
    print(f"عدد التحديثات: {summary['updates_count']}")
    print(f"مستوى الخطر الحالي: {summary['current_risk_level']}")
