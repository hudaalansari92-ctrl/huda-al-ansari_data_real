

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

try:
    # المرجع الوحيد لأسماء الحقول السريرية
    from config.field_definitions import ASKED_FIELDS, FIELD_OPTIONS
except Exception:  # pragma: no cover - fallback إذا تعذّر الاستيراد
    ASKED_FIELDS = [
        "age",
        "gender",
        "height_cm",
        "weight_kg",
        "smoking_status",
        "workplace_type",
        "environmental_hazards",
        "family_history",
    ]
    FIELD_OPTIONS = {}

logger = logging.getLogger('priority_scorer')


@dataclass
class QuestionPriority:
    """أولوية سؤال معين"""
    field_name: str  # اسم الحقل (age, smoking_status, etc)
    priority_score: float  # درجة الأولوية (0.0-1.0)
    reasoning_ar: str  # السبب بالعربية
    reasoning_en: str  # السبب بالإنجليزية
    risk_contribution: float  # مدى إسهام الحقل في الخطر
    is_critical: bool  # هل هو سؤال حرج؟


class PriorityScorer:
    """
    نظام حساب الأولويات
    يحدد أي سؤال يجب طرحه بناءً على الحقائق الموجودة
    يعمل على الحقول السريرية الـ 8 (ASKED_FIELDS)
    """

    def __init__(self):
        """تهيئة نظام الأولويات"""
        # الأوزان الأساسية لكل حقل سريري (تستخدم أسماء ASKED_FIELDS الموحدة)
        # age/gender/smoking_status/family_history عوامل خطر عالية القيمة
        # height_cm/weight_kg لازمان لحساب BMI
        # workplace_type/environmental_hazards مخاطر مهنية وبيئية
        self.base_weights = {
            'age': 0.22,                    # أهم عامل خطر ديموغرافي — يُسأل أولاً
            'gender': 0.18,                 # حقل ديموغرافي أساسي — يُسأل مبكراً
            'smoking_status': 0.16,         # عامل خطر سلوكي رئيسي
            'family_history': 0.14,         # عامل خطر وراثي مهم
            'weight_kg': 0.10,              # لازم لحساب مؤشر كتلة الجسم
            'height_cm': 0.08,              # لازم لحساب مؤشر كتلة الجسم
            'environmental_hazards': 0.07,  # مخاطر بيئية مهنية
            'workplace_type': 0.05,         # نوع بيئة العمل
        }

        # ضمان تغطية كل الحقول المطلوبة في الحوار (حتى لو أُضيفت حقول لاحقاً)
        for field_name in ASKED_FIELDS:
            self.base_weights.setdefault(field_name, 0.05)

        # الأسئلة الحرجة (يجب طرحها أولاً) — عوامل الخطر عالية القيمة
        self.critical_fields = ['age', 'smoking_status', 'family_history']

        # الأسئلة الداعمة
        self.supporting_fields = ['workplace_type', 'environmental_hazards']

    def calculate_priorities(self,
                            facts: Dict,
                            current_risk_level: str = 'LOW',
                            answered_fields: List[str] = None) -> List[QuestionPriority]:
        """
        حساب أولويات جميع الأسئلة

        Args:
            facts: الحقائق المجمعة حتى الآن
            current_risk_level: مستوى الخطر الحالي
            answered_fields: الحقول التي تمت الإجابة عليها

        Returns:
            قائمة بالأولويات مرتبة تنازلياً
        """
        if answered_fields is None:
            answered_fields = []

        priorities = []

        for field_name, base_weight in self.base_weights.items():
            # إذا تم الإجابة على السؤال، تخطاه
            if field_name in answered_fields:
                continue

            # حساب الأولوية
            priority_score = self._calculate_priority_score(
                field_name,
                base_weight,
                facts,
                current_risk_level,
                answered_fields
            )

            # توليد التفسير
            reasoning_ar, reasoning_en = self._generate_reasoning(
                field_name,
                priority_score,
                current_risk_level,
                facts
            )

            # تحديد إذا كان حرج
            is_critical = field_name in self.critical_fields and priority_score > 0.7

            # حساب مساهمة الحقل في الخطر
            risk_contribution = self._calculate_risk_contribution(field_name, facts)

            priority = QuestionPriority(
                field_name=field_name,
                priority_score=priority_score,
                reasoning_ar=reasoning_ar,
                reasoning_en=reasoning_en,
                risk_contribution=risk_contribution,
                is_critical=is_critical
            )

            priorities.append(priority)

        # ترتيب تنازلي حسب الأولوية
        priorities.sort(key=lambda x: x.priority_score, reverse=True)

        # تسجيل النتائج
        logger.info(f"تم حساب {len(priorities)} أولويات")
        for p in priorities[:3]:
            logger.info(f"  {p.field_name}: {p.priority_score:.2f} ({p.reasoning_ar})")

        return priorities

    def _calculate_priority_score(self,
                                  field_name: str,
                                  base_weight: float,
                                  facts: Dict,
                                  current_risk_level: str,
                                  answered_fields: List[str]) -> float:
        """حساب درجة أولوية حقل معين"""

        # 1. الوزن الأساسي
        score = base_weight

        # 2. gender يُسأل مباشرة بعد age (حقل ديموغرافي أساسي)
        if field_name == 'gender' and 'age' in answered_fields and 'gender' not in answered_fields:
            score += 0.50

        # 3. إذا كان الحقل حرجاً، زيادة الأولوية
        if field_name in self.critical_fields:
            score += 0.15

        # 4. بناءً على مستوى الخطر الحالي
        risk_multiplier = {
            'LOW': 1.0,
            'MODERATE': 1.2,
            'MEDIUM': 1.3,
            'HIGH': 1.5,
            'CRITICAL': 2.0
        }
        score *= risk_multiplier.get(current_risk_level, 1.0)

        # 5. إذا كان لدينا حقائق تشير لخطر، زيادة أولوية الحقول الداعمة
        if self._indicates_risk(facts):
            if field_name in self.supporting_fields:
                score += 0.10

        # 6. الحد الأقصى للدرجة هو 1.0
        return min(score, 1.0)

    def _indicates_risk(self, facts: Dict) -> bool:
        """هل الحقائق تشير لوجود خطر؟"""
        # المدخّن الحالي عامل خطر واضح
        if facts.get('smoking_status') == 'current smoker':
            return True

        # تاريخ عائلي إيجابي
        if facts.get('family_history') == 'yes':
            return True

        # العمر المتقدم عامل خطر
        age = facts.get('age', 0)
        if isinstance(age, (int, float)) and age >= 60:
            return True

        return False

    def _calculate_risk_contribution(self, field_name: str, facts: Dict) -> float:
        """حساب مدى إسهام الحقل في الخطر"""

        if field_name == 'smoking_status':
            status = facts.get('smoking_status')
            if status == 'current smoker':
                return 0.40  # أكبر مساهمة
            if status == 'ex-smoker':
                return 0.15
            return 0.0

        elif field_name == 'family_history':
            if facts.get('family_history') == 'yes':
                return 0.30
            return 0.0

        elif field_name == 'age':
            age = facts.get('age', 0)
            if isinstance(age, (int, float)) and age >= 60:
                return 0.25
            if isinstance(age, (int, float)) and age >= 45:
                return 0.10
            return 0.0

        elif field_name == 'weight_kg':
            # وزن مرتفع قد يدل على ارتفاع مؤشر كتلة الجسم
            weight = facts.get('weight_kg', 0)
            if isinstance(weight, (int, float)) and weight >= 90:
                return 0.15
            return 0.0

        elif field_name in ['workplace_type', 'environmental_hazards']:
            if facts.get('workplace_type') == 'factory' or facts.get('environmental_hazards'):
                return 0.10
            return 0.0

        return 0.0

    def _generate_reasoning(self,
                           field_name: str,
                           priority_score: float,
                           current_risk_level: str,
                           facts: Dict) -> Tuple[str, str]:
        """توليد تفسير الأولوية بالعربية والإنجليزية"""

        reasoning_template_ar = {
            'age': "العمر عامل خطر معروف — يُسأل أولاً",
            'gender': "الجنس يؤثر على مخاطر الإصابة",
            'smoking_status': f"التدخين عامل خطر رئيسي. الخطر الحالي: {current_risk_level}",
            'family_history': "التاريخ العائلي عامل خطر وراثي مهم",
            'weight_kg': "الوزن لازم لحساب مؤشر كتلة الجسم",
            'height_cm': "الطول لازم لحساب مؤشر كتلة الجسم",
            'workplace_type': "نوع بيئة العمل يؤثر على المخاطر المهنية",
            'environmental_hazards': "المخاطر البيئية تساهم في الخطر العام",
        }

        reasoning_template_en = {
            'age': "Known age risk factor — asked first",
            'gender': "Affects disease susceptibility",
            'smoking_status': f"Major behavioral risk factor. Current risk: {current_risk_level}",
            'family_history': "Important hereditary risk factor",
            'weight_kg': "Weight needed to compute BMI",
            'height_cm': "Height needed to compute BMI",
            'workplace_type': "Workplace type affects occupational risk",
            'environmental_hazards': "Environmental hazards contribute to overall risk",
        }

        reasoning_ar = reasoning_template_ar.get(
            field_name,
            f"أولوية: {priority_score:.1%}"
        )
        reasoning_en = reasoning_template_en.get(
            field_name,
            f"Priority: {priority_score:.1%}"
        )

        return reasoning_ar, reasoning_en

    def get_next_question(self,
                         facts: Dict,
                         current_risk_level: str = 'LOW',
                         answered_fields: List[str] = None) -> Optional[QuestionPriority]:
        """
        الحصول على السؤال ذو الأولوية الأعلى

        Args:
            facts: الحقائق المجمعة
            current_risk_level: مستوى الخطر
            answered_fields: الحقول المجاب عنها

        Returns:
            أولى سؤال ذو أولوية عالية، أو None إذا تمت الإجابة على جميع الأسئلة
        """
        if answered_fields is None:
            answered_fields = []

        priorities = self.calculate_priorities(facts, current_risk_level, answered_fields)

        if priorities:
            next_q = priorities[0]
            logger.info(f"السؤال التالي: {next_q.field_name} (أولوية: {next_q.priority_score:.2f})")
            return next_q

        logger.info("لا توجد أسئلة متبقية")
        return None

    def get_critical_questions_first(self,
                                    facts: Dict,
                                    answered_fields: List[str] = None) -> List[QuestionPriority]:
        """
        الحصول على الأسئلة الحرجة أولاً
        """
        if answered_fields is None:
            answered_fields = []

        priorities = self.calculate_priorities(facts, 'CRITICAL', answered_fields)

        # رشح الأسئلة الحرجة فقط
        critical = [p for p in priorities if p.is_critical]

        return critical[:5]  # أعلى 5 أسئلة حرجة

    def adjust_priority_based_on_risk(self,
                                     priorities: List[QuestionPriority],
                                     current_risk_level: str) -> List[QuestionPriority]:
        """
        تعديل الأولويات بناءً على مستوى الخطر
        """
        risk_boost = {
            'CRITICAL': 0.30,
            'HIGH': 0.15,
            'MODERATE': 0.05,
            'MEDIUM': 0.05,
            'LOW': 0.0
        }

        boost = risk_boost.get(current_risk_level, 0.0)

        for priority in priorities:
            # زيادة أولويات الأسئلة الحرجة عند وجود خطر عالي
            if priority.is_critical and boost > 0:
                priority.priority_score = min(priority.priority_score + boost, 1.0)

        # إعادة الترتيب
        priorities.sort(key=lambda x: x.priority_score, reverse=True)

        return priorities

    def get_priority_distribution(self,
                                 priorities: List[QuestionPriority]) -> Dict:
        """الحصول على توزيع الأولويات"""
        high_priority = [p for p in priorities if p.priority_score >= 0.7]
        medium_priority = [p for p in priorities if 0.3 <= p.priority_score < 0.7]
        low_priority = [p for p in priorities if p.priority_score < 0.3]

        return {
            'high': len(high_priority),
            'medium': len(medium_priority),
            'low': len(low_priority),
            'high_list': high_priority,
            'medium_list': medium_priority,
            'low_list': low_priority,
            'total_unanswered': len(priorities)
        }

    def should_ask_urgent(self, facts: Dict) -> bool:
        """هل يجب طرح أسئلة عاجلة؟"""
        # المدخّن الحالي مع تاريخ عائلي إيجابي حالة تستدعي تركيزاً
        if facts.get('smoking_status') == 'current smoker' and facts.get('family_history') == 'yes':
            return True

        # عمر متقدم جداً
        age = facts.get('age', 0)
        if isinstance(age, (int, float)) and age >= 75:
            return True

        return False


# مثال على الاستخدام
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # إنشاء نظام حساب الأولويات
    scorer = PriorityScorer()

    # حقائق المريض
    facts = {
        'age': 55,
        'gender': 'male',
        'smoking_status': 'current smoker',
        'family_history': 'yes',
    }

    answered = ['age', 'gender', 'smoking_status', 'family_history']

    print("\n1. حساب الأولويات:")
    print("=" * 60)
    priorities = scorer.calculate_priorities(facts, 'HIGH', answered)

    for p in priorities[:5]:
        print(f"\n{p.field_name}:")
        print(f"  أولوية: {p.priority_score:.2f}")
        print(f"  السبب: {p.reasoning_ar}")
        print(f"  مساهمة الخطر: {p.risk_contribution:.2f}")
        print(f"  حرج: {p.is_critical}")

    print("\n2. السؤال التالي:")
    print("=" * 60)
    next_q = scorer.get_next_question(facts, 'HIGH', answered)
    if next_q:
        print(f"السؤال: {next_q.field_name}")
        print(f"السبب: {next_q.reasoning_ar}")

    print("\n3. الأسئلة الحرجة:")
    print("=" * 60)
    critical = scorer.get_critical_questions_first(facts, answered)
    for c in critical:
        print(f"  - {c.field_name} ({c.priority_score:.2f})")

    print("\n4. توزيع الأولويات:")
    print("=" * 60)
    dist = scorer.get_priority_distribution(priorities)
    print(f"أولويات عالية: {dist['high']}")
    print(f"أولويات متوسطة: {dist['medium']}")
    print(f"أولويات منخفضة: {dist['low']}")
