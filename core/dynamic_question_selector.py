
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# المرجع الوحيد لأسماء الحقول السريرية (8 حقول يسألها الحوار)
from config.field_definitions import ASKED_FIELDS, FIELD_OPTIONS
# نصوص الأسئلة والأمثلة جاهزة ومفتاحها أسماء الحقول السريرية نفسها
from config.question_examples import QUESTION_EXAMPLES, get_question_info

logger = logging.getLogger('dynamic_question_selector')


# نوع كل حقل سريري في الحوار: number / choice / yesno / text
_FIELD_QUESTION_TYPES: Dict[str, str] = {
    'age': 'number',
    'gender': 'choice',
    'height_cm': 'number',
    'weight_kg': 'number',
    'smoking_status': 'choice',
    'workplace_type': 'choice',
    'environmental_hazards': 'text',
    'family_history': 'yesno',
}

# قواعد التحقق للحقول الرقمية (تطابق VALUE_RANGES في field_definitions)
_FIELD_VALIDATION_RULES: Dict[str, Dict] = {
    'age': {'min': 0, 'max': 150},
    'height_cm': {'min': 50, 'max': 250},
    'weight_kg': {'min': 20, 'max': 400},
}

# خيارات عربية موازية للخيارات الإنجليزية في FIELD_OPTIONS (لعرض الواجهة)
_FIELD_CHOICES_AR: Dict[str, List[str]] = {
    'gender': ['ذكر', 'أنثى'],
    'smoking_status': ['غير مدخّن', 'مدخّن سابق', 'مدخّن حالي'],
    'workplace_type': ['مكتب', 'مصنع'],
    'environmental_hazards': ['توتر', 'تلوّث', 'ضوضاء', 'غبار',
                              'مواد كيميائية', 'عمل بنظام الورديات'],
    'family_history': ['نعم', 'لا'],
}


@dataclass
class Question:
    """تعريف سؤال"""
    field_name: str
    question_ar: str  # السؤال بالعربية
    question_en: str  # السؤال بالإنجليزية
    question_type: str  # text, number, choice, yesno
    choices_ar: Optional[List[str]] = None
    choices_en: Optional[List[str]] = None
    validation_rules: Optional[Dict] = None
    examples_ar: Optional[List[str]] = None
    examples_en: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None


class DynamicQuestionSelector:
    """
    نظام اختيار الأسئلة الديناميكي
    يختار السؤال التالي بناءً على الحقائق والأولويات الحالية

    يعمل على الحقول السريرية الـ 8 (ASKED_FIELDS): العمر، الجنس، الطول،
    الوزن، حالة التدخين، نوع مكان العمل، المخاطر البيئية، التاريخ العائلي.
    (الميزة التاسعة bmi تُحسب تلقائياً من الطول والوزن فلا يُسأل عنها.)
    """

    def __init__(self):
        """تهيئة نظام اختيار الأسئلة"""
        self.questions = self._initialize_questions()
        self.question_order = []  # ترتيب الأسئلة الديناميكي
        self.asked_questions = []  # الأسئلة التي تم طرحها

    def _initialize_questions(self) -> Dict[str, Question]:
        """تهيئة قائمة الأسئلة المتاحة من تعريفات الحقول السريرية الموحدة.

        نبني كائن Question لكل حقل في ASKED_FIELDS بإعادة استخدام نصوص
        الأسئلة والأمثلة من config.question_examples وخيارات FIELD_OPTIONS.
        """
        questions: Dict[str, Question] = {}

        for field_name in ASKED_FIELDS:
            info_ar = get_question_info(field_name, 'ar') or {}
            info_en = get_question_info(field_name, 'en') or {}

            questions[field_name] = Question(
                field_name=field_name,
                question_ar=info_ar.get('question', ''),
                question_en=info_en.get('question', ''),
                question_type=_FIELD_QUESTION_TYPES.get(field_name, 'text'),
                choices_ar=_FIELD_CHOICES_AR.get(field_name),
                choices_en=FIELD_OPTIONS.get(field_name),
                validation_rules=_FIELD_VALIDATION_RULES.get(field_name),
                examples_ar=info_ar.get('examples', []),
                examples_en=info_en.get('examples', []),
            )

        return questions

    def get_question(self,
                    field_name: str,
                    language: str = 'ar') -> Optional[Question]:
        """
        الحصول على سؤال معين

        Args:
            field_name: اسم الحقل
            language: اللغة ('ar' أو 'en')

        Returns:
            كائن السؤال أو None
        """
        return self.questions.get(field_name)

    def select_next_question(self,
                            priorities: List,
                            facts: Dict,
                            language: str = 'ar') -> Optional[Dict]:
        """
        اختيار السؤال التالي بناءً على الأولويات

        Args:
            priorities: قائمة الأولويات من PriorityScorer
            facts: الحقائق المجمعة
            language: اللغة

        Returns:
            كائن السؤال مع البيانات الكاملة أو None
        """
        # الحصول على أول سؤال ذو أولوية عالية
        if not priorities:
            logger.warning("لا توجد أولويات متاحة")
            return None

        for priority in priorities:
            field_name = priority.field_name

            # تخطي الحقول التي تمت الإجابة عليها
            if field_name in facts and facts[field_name]:
                continue

            # الحصول على السؤال
            question = self.get_question(field_name, language)
            if not question:
                continue

            # تسجيل السؤال
            self.asked_questions.append(field_name)
            logger.info(f"تم اختيار السؤال: {field_name} (أولوية: {priority.priority_score:.2f})")

            # بناء استجابة شاملة
            return {
                'field_name': question.field_name,
                'question': question.question_ar if language == 'ar' else question.question_en,
                'question_type': question.question_type,
                'choices': question.choices_ar if language == 'ar' else question.choices_en,
                'examples': question.examples_ar if language == 'ar' else question.examples_en,
                'priority': priority.priority_score,
                'is_critical': priority.is_critical,
                'reasoning': priority.reasoning_ar if language == 'ar' else priority.reasoning_en,
                'validation_rules': question.validation_rules,
                'follow_up': question.follow_up_questions
            }

        logger.info("لا توجد أسئلة متبقية")
        return None

    def get_adaptive_question(self,
                             priorities: List,
                             facts: Dict,
                             current_risk_level: str,
                             language: str = 'ar') -> Optional[Dict]:
        """
        اختيار سؤال متكيف بناءً على مستوى الخطر

        إذا كان الخطر عالياً، اسأل الأسئلة الحرجة أولاً
        إذا كان الخطر منخفضاً، يمكن السؤال بشكل متدرج
        """
        if current_risk_level in ['CRITICAL', 'HIGH']:
            # أسئلة حرجة فقط
            critical_priorities = [p for p in priorities if p.is_critical]
            if critical_priorities:
                return self.select_next_question(critical_priorities, facts, language)

        # الأسئلة العادية
        return self.select_next_question(priorities, facts, language)

    def get_sequential_questions(self,
                                priorities: List,
                                facts: Dict,
                                count: int = 3,
                                language: str = 'ar') -> List[Dict]:
        """
        الحصول على عدة أسئلة متتالية

        Args:
            priorities: الأولويات
            facts: الحقائق
            count: عدد الأسئلة
            language: اللغة

        Returns:
            قائمة الأسئلة التالية
        """
        questions = []

        for _ in range(count):
            q = self.select_next_question(priorities, facts, language)
            if q:
                questions.append(q)
                # إضافة حقيقة مؤقتة لتخطي هذا السؤال في التكرار التالي
                facts[q['field_name']] = '__placeholder__'
            else:
                break

        return questions

    def get_follow_up_questions(self,
                               field_name: str,
                               language: str = 'ar') -> List[str]:
        """
        الحصول على الأسئلة المتابعة لسؤال معين

        الحقول السريرية الحالية مستقلة، فلا توجد أسئلة متابعة افتراضية،
        لكن الواجهة محفوظة لأي إعداد مستقبلي.
        """
        question = self.get_question(field_name)
        if question and question.follow_up_questions:
            return question.follow_up_questions
        return []

    def customize_question(self,
                          field_name: str,
                          custom_text_ar: str,
                          custom_text_en: str,
                          language: str = 'ar') -> Optional[Dict]:
        """
        تخصيص نص السؤال بناءً على السياق

        مثال: إذا كان هناك علامات خطر، اجعل السؤال أكثر حدة
        """
        question = self.get_question(field_name)
        if not question:
            return None

        return {
            'field_name': question.field_name,
            'question': custom_text_ar if language == 'ar' else custom_text_en,
            'question_type': question.question_type,
            'choices': question.choices_ar if language == 'ar' else question.choices_en,
            'examples': question.examples_ar if language == 'ar' else question.examples_en
        }

    def adjust_questions_for_risk(self,
                                 priorities: List,
                                 current_risk_level: str) -> List:
        """
        تعديل الأسئلة بناءً على مستوى الخطر

        الخطر العالي = أسئلة مركزة على عوامل الخطر
        الخطر المنخفض = أسئلة أكثر استرخاءً
        """
        adjusted = []

        for priority in priorities:
            if current_risk_level == 'CRITICAL':
                # ركز على الأسئلة الحرجة
                if priority.is_critical:
                    adjusted.append(priority)

            elif current_risk_level == 'HIGH':
                # أولويات عالية ومتوسطة
                if priority.priority_score >= 0.5:
                    adjusted.append(priority)

            else:
                # جميع الأسئلة
                adjusted.append(priority)

        return adjusted

    def get_question_statistics(self) -> Dict:
        """إحصائيات الأسئلة"""
        return {
            'total_questions': len(self.questions),
            'questions_asked': len(set(self.asked_questions)),
            'questions_remaining': len(self.questions) - len(set(self.asked_questions)),
            'asked_list': list(set(self.asked_questions)),
            'available_questions': list(self.questions.keys())
        }

    def reset(self):
        """إعادة تعيين الحالة"""
        self.question_order = []
        self.asked_questions = []
        logger.info("تم إعادة تعيين نظام اختيار الأسئلة")


# مثال على الاستخدام
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from priority_scorer import PriorityScorer

    # إنشاء الأنظمة
    scorer = PriorityScorer()
    selector = DynamicQuestionSelector()

    # حقائق المريض (الحقول السريرية)
    facts = {
        'age': 55,
    }

    answered = ['age']

    print("\n1. اختيار السؤال التالي:")
    print("=" * 60)

    # حساب الأولويات
    priorities = scorer.calculate_priorities(facts, 'HIGH', answered)

    # اختيار السؤال
    next_q = selector.select_next_question(priorities, facts, language='ar')

    if next_q:
        print(f"السؤال: {next_q['question']}")
        print(f"النوع: {next_q['question_type']}")
        print(f"الأولوية: {next_q['priority']:.2f}")
        print(f"السبب: {next_q['reasoning']}")
        if next_q['choices']:
            print(f"الخيارات: {', '.join(next_q['choices'])}")
        if next_q['examples']:
            print(f"أمثلة: {', '.join(next_q['examples'])}")

    print("\n2. الأسئلة المتابعة:")
    print("=" * 60)
    follow_ups = selector.get_follow_up_questions('family_history')
    for fu in follow_ups:
        print(f"  - {fu}")

    print("\n3. إحصائيات الأسئلة:")
    print("=" * 60)
    stats = selector.get_question_statistics()
    print(f"إجمالي الأسئلة: {stats['total_questions']}")
    print(f"الأسئلة المطروحة: {stats['questions_asked']}")
    print(f"الأسئلة المتبقية: {stats['questions_remaining']}")
