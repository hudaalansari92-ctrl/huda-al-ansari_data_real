

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import logging
from dataclasses import asdict

# استيراد المكونات
from core.self_dialog_manager import SelfDialogManager, InternalThought
from core.priority_scorer import PriorityScorer, QuestionPriority
from core.dynamic_question_selector import DynamicQuestionSelector, Question
from nlp.biobert_ner import BioBERTNER, _NORMAL_DEFAULTS
from engine.domain_rules_engine import DomainRulesEngine

# Clinical ML pipeline (v9.0.0) — 9 base → 26 engineered → clinical_model.pkl
from engine.feature_deriver import derive as derive_features, FEATURE_NAMES
from engine.clinical_ml_predictor import clinical_ml_predictor
from engine.domain_pipeline import domain_pipeline
from engine.final_decision_engine import final_decision_engine
import pandas as pd

# Groq API components (v7.0.0)
from groq_api.groq_client import GroqClient
from groq_api.result_interpreter import ResultInterpreter
from groq_api.recommendation_engine import RecommendationEngine

# Smart Conversation components (v8.0.0)
from groq_api.groq_ner import GroqNER
from groq_api.conversation_manager import SmartConversationManager

# Clinical field schema (single source of truth)
from config.field_definitions import ASKED_FIELDS, BASE_FIELDS

logger = logging.getLogger('integrated_chatbot')

# الميزات الرقمية المستمرة ضمن الـ 26 (الباقي ثنائي 0/1)
_CONTINUOUS_FEATS = ('age', 'bmi', 'height_cm', 'weight_kg')


# Progressive disclosure: each field has 3 increasingly helpful phrasings.
# L1 is the original question. L2 adds a concrete example. L3 is the
# "last try" version with a clear template + warning that the chatbot
# will move on next. Used by the 3-strikes auto-skip flow so the patient
# is gradually guided to the answer rather than seeing the same prompt
# repeated word-for-word.
_PROGRESSIVE_PROMPTS = {
    'age': {
        'ar': [
            'ما هو عمرك؟',
            'اكتب عمرك بالأرقام، مثل: 45',
            'آخر محاولة — رقم فقط بين 1 و 120 (مثل: 50)، وإلا سننتقل.',
        ],
        'en': [
            'What is your age?',
            'Please type your age as a number, e.g., 45.',
            'Last try — just a number between 1 and 120 (e.g., 50), otherwise we will move on.',
        ],
    },
    'gender': {
        'ar': [
            'ما هو جنسك؟',
            "اكتب 'ذكر' أو 'أنثى'.",
            "آخر محاولة — M للذكر، F للأنثى، وإلا سننتقل.",
        ],
        'en': [
            'What is your gender?',
            "Type 'male' or 'female'.",
            "Last try — M for male, F for female, otherwise we will move on.",
        ],
    },
    'height_cm': {
        'ar': [
            'كم طولك بالسنتيمتر؟',
            "اكتب الطول بالسنتيمتر (مثل: 175)، أو بالمتر (مثل: 1.75).",
            "آخر محاولة — رقم بين 50 و 250 سم (مثل: 170)، وإلا سننتقل.",
        ],
        'en': [
            'What is your height in centimeters?',
            "Type your height in cm (e.g., 175), or in meters (e.g., 1.75).",
            "Last try — a number between 50 and 250 cm (e.g., 170), otherwise we will move on.",
        ],
    },
    'weight_kg': {
        'ar': [
            'كم وزنك بالكيلوغرام؟',
            "اكتب الوزن بالكيلوغرام (مثل: 80).",
            "آخر محاولة — رقم بين 20 و 400 كغم (مثل: 75)، وإلا سننتقل.",
        ],
        'en': [
            'What is your weight in kilograms?',
            "Type your weight in kg (e.g., 80).",
            "Last try — a number between 20 and 400 kg (e.g., 75), otherwise we will move on.",
        ],
    },
    'smoking_status': {
        'ar': [
            'ما حالتك مع التدخين؟',
            "اكتب 'غير مدخّن' أو 'مدخّن سابق' أو 'مدخّن حالي'.",
            "آخر محاولة — غير مدخّن / سابق / حالي، وإلا سننتقل.",
        ],
        'en': [
            'What is your smoking status?',
            "Type 'non-smoker', 'ex-smoker', or 'current smoker'.",
            "Last try — non-smoker / ex-smoker / current smoker, otherwise we will move on.",
        ],
    },
    'workplace_type': {
        'ar': [
            'ما نوع مكان عملك؟',
            "اكتب 'مكتب' أو 'مصنع'.",
            "آخر محاولة — مكتب أو مصنع، وإلا سننتقل.",
        ],
        'en': [
            'What is your workplace type?',
            "Type 'office' or 'factory'.",
            "Last try — office or factory, otherwise we will move on.",
        ],
    },
    'environmental_hazards': {
        'ar': [
            'هل تتعرّض لمخاطر بيئية في عملك؟',
            "اذكر المخاطر: توتر، تلوّث، ضوضاء، غبار، مواد كيميائية، ورديات — أو 'لا يوجد'.",
            "آخر محاولة — اذكر ما ينطبق أو اكتب 'لا يوجد'، وإلا سننتقل.",
        ],
        'en': [
            'Are you exposed to environmental hazards at work?',
            "List them: stress, pollution, noise, dust, chemicals, shift work — or 'none'.",
            "Last try — list what applies or type 'none', otherwise we will move on.",
        ],
    },
    'family_history': {
        'ar': [
            'هل يوجد تاريخ عائلي لأمراض القلب؟',
            "اكتب 'نعم' أو 'لا'.",
            "آخر محاولة — نعم أو لا، وإلا سننتقل.",
        ],
        'en': [
            'Is there a family history of heart disease?',
            "Type 'yes' or 'no'.",
            "Last try — yes or no, otherwise we will move on.",
        ],
    },
}


class IntegratedSelfReasoningChatbot:
    """
    الـ Chatbot الذي يتحدث مع نفسه ويحدث نفسه
    يجمع:
    - Self-Dialog Manager (الحوار الذاتي)
    - Priority Scorer (حساب الأولويات)
    - Dynamic Question Selector (اختيار الأسئلة)
    """
    
    def __init__(self, language: str = 'ar', groq_api_key: str = None):
        """
        تهيئة الـ Chatbot المتكامل

        Args:
            language: اللغة الافتراضية ('ar' أو 'en')
            groq_api_key: مفتاح Groq API (اختياري)
        """
        self.language = language

        # المكونات الأساسية
        self.dialog_manager = SelfDialogManager(language)
        self.priority_scorer = PriorityScorer()
        self.question_selector = DynamicQuestionSelector()

        # المكونات الجديدة - BioBERT NER & Domain Rules
        self.biobert_ner = BioBERTNER()
        self.domain_rules = DomainRulesEngine()

        # Groq API components (v7.0.0)
        self.groq_client = GroqClient(api_key=groq_api_key)
        self.result_interpreter = ResultInterpreter(self.groq_client)
        self.recommendation_engine = RecommendationEngine(self.groq_client)

        # Smart Conversation components (v8.0.0)
        self.groq_ner = GroqNER(self.groq_client)
        self.conversation_manager = SmartConversationManager(self.groq_client, language)

        # حالة الجلسة
        self.session_id = str(datetime.now().timestamp())
        self.facts: Dict = {}
        self.inferences: Dict = {}
        self.current_risk_level = 'LOW'
        self.confidence_score = 0.0
        self.conversation_history: List[Dict] = []
        self.answered_fields: List[str] = []

        # حالة Domain Assessment
        self.domain_assessment = None

        # The field the chatbot is about to ask for. Used by the context
        # extractor to interpret short replies ("لا", "120", "Chol 310")
        # in the right field's context. Initialised here so the very
        # first turn already has a deterministic value.
        self._last_asked_field: Optional[str] = None

        # 3-strikes auto-skip: track how many times each field failed
        # extraction. After MAX_ATTEMPTS failures, the chatbot stores the
        # clinical default and marks the field as 'skipped' so the
        # patient can move on instead of being stuck in a loop.
        self.MAX_ATTEMPTS = 3
        self._field_attempts: Dict[str, int] = {}
        # Per-field metadata: {'BloodPressure': {'source': 'user'|'skipped',
        # 'attempts': int}}
        self._field_metadata: Dict[str, Dict] = {}

        logger.info(f"تم إنشاء جلسة جديدة: {self.session_id}")
        if self.groq_client.is_available:
            logger.info("Groq API connected successfully")
    
    def process_answer(self, field_name: str, answer_value: str) -> Dict:
        """
        معالجة إجابة المستخدم والتحدث مع النفس
        
        Args:
            field_name: اسم الحقل
            answer_value: قيمة الإجابة
            
        Returns:
            قاموس يحتوي على:
            - الفكرة الداخلية
            - الاستنتاجات
            - التحديثات
            - السؤال التالي
        """
        logger.info(f"معالجة الإجابة: {field_name} = {answer_value}")
        
        # الخطوة 1: تطبيع القيمة (تحويل الأرقام من string إلى int/float)
        normalized_value = self._normalize_value(field_name, answer_value)
        
        # الخطوة 2: تخزين الحقيقة
        self.facts[field_name] = normalized_value
        self.answered_fields.append(field_name)
        logger.info(f"تم تخزين الحقيقة: {field_name} = {normalized_value}")

        # Successful direct answer → mark as user-confirmed and reset
        # the 3-strikes counter for this field.
        self._field_attempts.pop(field_name, None)
        self._field_metadata[field_name] = {
            'source': 'user',
            'attempts': 1,
        }
        
        # الخطوة 3: الحوار الذاتي - تحليل الإجابة
        thought = self.dialog_manager.analyze_answer(
            field_name,
            normalized_value,
            self.facts
        )
        
        # الخطوة 3: الاستنتاج من الحقائق
        inference = self.dialog_manager.infer_from_facts(self.facts)
        
        # الخطوة 3.5: تقييم Domain Rules (إذا كانت البيانات كافية)
        domain_assessment = self.get_domain_assessment()
        
        # الخطوة 4: تحديث مستوى الخطر
        self.current_risk_level = self._calculate_risk_level()
        self.confidence_score = self._calculate_confidence()
        
        # الخطوة 5: التحقق من التحذيرات
        warning = None
        if self._should_warn():
            warning = self.dialog_manager.trigger_warning(
                'critical_symptoms',
                self._get_warning_severity(),
                {'field': field_name, 'value': answer_value}
            )
        
        # الخطوة 6: اتخاذ قرار عن السؤال التالي
        decision = self.dialog_manager.make_decision(self.facts, self.inferences)
        
        # الخطوة 7: حساب الأولويات الجديدة
        priorities = self.priority_scorer.calculate_priorities(
            self.facts,
            self.current_risk_level,
            self.answered_fields
        )
        
        # الخطوة 8: اختيار السؤال التالي
        next_question = self._select_next_question(priorities)
        
        # بناء الاستجابة الكاملة
        response = {
            'step': len(self.conversation_history) + 1,
            'field_processed': field_name,
            'internal_thought': {
                'thought': thought.thought,
                'category': thought.category,
                'confidence': thought.confidence
            },
            'inference': {
                'thought': inference.thought,
                'confidence': inference.confidence
            },
            'current_status': {
                'risk_level': self.current_risk_level,
                'confidence_score': self.confidence_score,
                'facts_collected': len(self.answered_fields),
                'total_facts': len(ASKED_FIELDS)
            },
            'domain_assessment': domain_assessment if domain_assessment else None,
            'warning': {
                'triggered': warning is not None,
                'message': warning.thought if warning else None
            } if warning else None,
            'decision': {
                'message': decision.thought
            },
            'next_question': next_question if next_question else {
                'message': 'تم جمع جميع المعلومات اللازمة',
                'message_en': 'All required information collected'
            },
            'progress': {
                'percentage': int((len(self.answered_fields) / len(ASKED_FIELDS)) * 100),
                'answered': len(self.answered_fields),
                'remaining': len(ASKED_FIELDS) - len(self.answered_fields)
            }
        }
        
        # حفظ في السجل
        self.conversation_history.append(response)
        
        return response
    
    def extract_fields_from_text(self, text: str) -> Dict:
        """
        استخراج المعلومات الطبية من النص الحر باستخدام BioBERT NER
        
        Args:
            text: النص المدخل
            
        Returns:
            قاموس بالحقول المستخرجة
        """
        logger.info(f"Extracting fields from text using BioBERT NER")

        # استخدام BioBERT NER لاستخراج المعلومات
        entities = self.biobert_ner.extract_entities(text)

        # Universal hallucination guard — same filter the smart path uses.
        # Free-text input may produce values for fields the patient never
        # mentioned (e.g. a stray "62" matching Age's number-only pattern
        # while answering a different question). The exempt field is the
        # one the chatbot just asked about, since a single-word answer
        # like "طبيعي" is legitimate even with no field keyword.
        entities = self._reject_phantom_fields(
            text, entities, source='biobert',
            exempt_field=getattr(self, '_last_asked_field', None)
        )

        result = {
            'extracted': [],
            'unprocessed': []
        }

        # معالجة المعلومات المستخرجة
        for field_name, field_value in entities.items():
            # تحويل أسماء الحقول للنظام
            field_ar = self._get_field_arabic_name(field_name)
            
            result['extracted'].append({
                'field': field_name,
                'field_ar': field_ar,
                'value': field_value,
                'confidence': self.biobert_ner.get_entity_confidence(field_name, field_value)
            })
            
            # تخزين في facts (مع تطبيع القيمة)
            normalized_value = self._normalize_value(field_name, field_value)
            self.facts[field_name] = normalized_value
            if field_name not in self.answered_fields:
                self.answered_fields.append(field_name)
        
        logger.info(f"Extracted {len(result['extracted'])} fields using BioBERT")

        # Successful extraction → mark all touched fields as user-confirmed
        # and reset their failed-attempt counter.
        for item in result['extracted']:
            fname = item['field']
            self._field_attempts.pop(fname, None)
            self._field_metadata[fname] = {
                'source': 'user',
                'attempts': 1,
            }

        return result

    # --- 3-strikes auto-skip helpers --------------------------------------

    def register_failed_attempt(self, field_name: Optional[str] = None) -> Dict:
        """
        Patient sent something we couldn't extract. Bump the attempt
        counter for the currently-asked field. After MAX_ATTEMPTS misses
        we auto-skip the field with the clinical default so the
        conversation can move on.

        Args:
            field_name: which field the failed attempt was for. Defaults
                to whichever field was last asked by the chatbot.

        Returns:
            dict with keys:
              - field            : str (the field the counter is for)
              - attempts         : int (1-based, how many tries so far)
              - remaining        : int (how many tries are left)
              - auto_skipped     : bool (True if we just hit MAX_ATTEMPTS)
              - skipped_value    : the default that was written (if skipped)
              - max_attempts     : MAX_ATTEMPTS for the UI
        """
        field_name = field_name or self._last_asked_field
        if not field_name:
            return {'field': None, 'attempts': 0, 'remaining': self.MAX_ATTEMPTS,
                    'auto_skipped': False, 'skipped_value': None,
                    'max_attempts': self.MAX_ATTEMPTS, 'next_prompt': None}

        self._field_attempts[field_name] = self._field_attempts.get(field_name, 0) + 1
        attempts = self._field_attempts[field_name]
        remaining = max(0, self.MAX_ATTEMPTS - attempts)

        if attempts < self.MAX_ATTEMPTS:
            logger.info(f"[3-strikes] {field_name}: attempt {attempts}/{self.MAX_ATTEMPTS}")
            # Progressive rephrase: after N failures we show the (N+1)-th
            # increasingly-helpful version of the question. Cap at the
            # last available level so even attempt 4+ stays consistent.
            next_prompt = self.get_rephrased_question(field_name, attempts)
            return {
                'field': field_name,
                'attempts': attempts,
                'remaining': remaining,
                'auto_skipped': False,
                'skipped_value': None,
                'max_attempts': self.MAX_ATTEMPTS,
                'next_prompt': next_prompt,
            }

        # We hit the cap → auto-skip with the clinical default.
        default_value = _NORMAL_DEFAULTS.get(field_name)
        if default_value is None:
            # Age / Sex have no clinical "normal" → just give up cleanly.
            default_value = 'UNKNOWN'

        normalized = self._normalize_value(field_name, default_value)
        self.facts[field_name] = normalized
        if field_name not in self.answered_fields:
            self.answered_fields.append(field_name)
        self._field_metadata[field_name] = {
            'source': 'skipped',
            'attempts': attempts,
        }
        logger.warning(
            f"[3-strikes] {field_name}: skipped after {attempts} attempts, "
            f"filled with default={normalized}"
        )
        return {
            'field': field_name,
            'attempts': attempts,
            'remaining': 0,
            'auto_skipped': True,
            'skipped_value': normalized,
            'max_attempts': self.MAX_ATTEMPTS,
            'next_prompt': None,
        }

    def get_field_metadata(self) -> Dict[str, Dict]:
        """Return per-field source/attempt metadata for UI badges."""
        return dict(self._field_metadata)

    # --- Groq hallucination guard ----------------------------------------
    # If Groq's LLM extracts a field whose textual keyword family is
    # absent from the patient's input, treat it as a hallucination and
    # drop it. Keeps Age=62 when the patient says "أبلغ 62 عاماً" but
    # rejects the phantom FastingBS=0 the LLM tacked on.
    _FIELD_KEYWORDS = {
        'age':            ('عمر', 'سنة', 'سنوات', 'عام', 'عاما', 'بلغ', 'age', 'year', 'old', 'aged'),
        'gender':         ('ذكر', 'انثى', 'أنثى', 'رجل', 'امرأ', 'male', 'female', 'man', 'woman', 'gender', 'sex'),
        'height_cm':      ('طول', 'سم', 'سنتيمتر', 'متر', 'height', 'tall', 'cm', 'm '),
        'weight_kg':      ('وزن', 'كيلو', 'كغم', 'كجم', 'weight', 'weigh', 'kg', 'kilo'),
        'smoking_status': ('دخان', 'تدخين', 'مدخن', 'سيجار', 'أقلع', 'اقلع', 'smok', 'smoke', 'cigarette', 'tobacco'),
        'workplace_type': ('عمل', 'اعمل', 'أعمل', 'وظيف', 'مكتب', 'مصنع', 'معمل', 'work', 'office', 'factory', 'job'),
        'environmental_hazards': ('توتر', 'ضغط نفسي', 'تلوث', 'تلوّث', 'ضوضاء', 'غبار', 'كيميا', 'كيماو', 'ورديات', 'شفت',
                                  'stress', 'pollution', 'noise', 'dust', 'chemical', 'shift', 'hazard'),
        'family_history': ('عائل', 'وراث', 'اهل', 'أهل', 'family', 'hereditary', 'genetic', 'relatives', 'parents'),
        # --- clinical risk factors ---
        'hypertension': ('ضغط', 'ارتفاع الضغط', 'hypertension', 'blood pressure', 'bp', 'hypertensive'),
        'diabetes': ('سكري', 'سكر', 'diabet', 'diabetic', 'sugar'),
        'cardiovascular_disease': ('قلب', 'شريان', 'شرايين', 'اوعية', 'أوعية', 'تاجي', 'cardio', 'heart',
                                   'cvd', 'vascular', 'cad', 'coronary'),
        'chronic_diseases': ('مزمن', 'مزمنة', 'chronic'),
        'obesity': ('سمنة', 'بدين', 'بدانة', 'وزن زائد', 'obes', 'overweight'),
        'gestational_diabetes': ('سكري الحمل', 'سكري حمل', 'الحمل', 'حمل', 'gestational'),
        'hba1c': ('تراكمي', 'السكر التراكمي', 'hba1c', 'a1c', 'glycated', 'glycosylated'),
        'cholesterol': ('كوليسترول', 'كولسترول', 'cholesterol', 'ldl', 'hdl', 'دهون', 'lipid'),
        'years_smoked': ('سنة', 'سنوات', 'عام', 'دخّن', 'دخن', 'year', 'smok'),
        'years_since_quit': ('أقلع', 'اقلع', 'توقف', 'منذ', 'quit', 'since', 'stopped'),
        'bmi': ('مؤشر كتلة', 'كتلة الجسم', 'bmi', 'مؤشر'),
    }

    @classmethod
    def _field_keyword_present(cls, field: str, text: str) -> bool:
        """Cheap textual check: does `text` mention anything about `field`?"""
        if not text:
            return False
        # Normalise BOTH sides with BioBERT's helper so أ/إ/آ/ئ etc. collapse
        # the same way in the text and in the keywords (otherwise an Arabic
        # keyword like "عائل" would never match the normalised "عايل").
        haystack = BioBERTNER._normalize_ar(text)
        return any(BioBERTNER._normalize_ar(kw) in haystack
                   for kw in cls._FIELD_KEYWORDS.get(field, ()))

    @classmethod
    def _reject_phantom_fields(
        cls, text: str, extracted: Dict, source: str = 'unknown',
        exempt_field: Optional[str] = None
    ) -> Dict:
        """
        Drop any field that has no related keyword in `text`. Applied to
        every extractor (Groq, BioBERT, context fallback) so phantom
        values never reach self.facts no matter which layer produced them.

        Args:
            text: the patient's raw input
            extracted: dict of field → value from one extractor
            source: short label for logs ("groq", "biobert", "context")
            exempt_field: a field that bypasses the check, used for the
                field the chatbot just asked about — a one-word reply
                like "طبيعي" is a legitimate answer to that question
                even though no field keyword is present.
        """
        clean = {}
        for field, value in (extracted or {}).items():
            if field == exempt_field or cls._field_keyword_present(field, text):
                clean[field] = value
            else:
                logger.warning(
                    f"[hallucination-guard:{source}] Dropping phantom "
                    f"{field}={value!r} — no related keyword in input: {text[:60]!r}"
                )
        return clean

    # Back-compat alias for the Groq-only name used in older callers.
    @classmethod
    def _reject_groqs_phantom_fields(cls, text: str, groq_extracted: Dict) -> Dict:
        return cls._reject_phantom_fields(text, groq_extracted, source='groq')

    def get_rephrased_question(
        self, field_name: str, attempt_num: int = 0,
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Return the progressively-helpful rephrasing of `field_name`'s
        question for the given attempt number.

        attempt_num is how many times the patient has already failed:
          0 → original phrasing (L1)
          1 → with concrete example (L2)
          2 → final-try phrasing with skip warning (L3)

        Returns None for fields without a prepared rephrasing (e.g.,
        fields not in _PROGRESSIVE_PROMPTS).
        """
        lang = language or self.language or 'ar'
        prompts = _PROGRESSIVE_PROMPTS.get(field_name, {}).get(lang)
        if not prompts:
            return None
        idx = min(max(attempt_num, 0), len(prompts) - 1)
        return prompts[idx]

    def get_domain_assessment(self) -> Optional[Dict]:
        """
        تقييم شامل باستخدام الـ Domain Pipeline السريري.

        WORKFLOW (الاستراتيجية: 9 → 26 → نموذج → قواعد):
        1. التأكد من جمع الحقول السريرية المطلوبة
        2. اشتقاق الـ 26 ميزة عبر feature_deriver
        3. تطبيق domain_rules.json السريري على الميزات المشتقة
        4. إرجاع تقييم كامل (ميزات ثنائية/مستمرة + قواعد + رؤى طبية)

        Returns:
            تقييم كامل إذا اكتملت الحقول، وإلا None
        """
        # نحتاج معظم الحقول الأصل الـ 8 قبل التقييم
        if len(self.answered_fields) < len(ASKED_FIELDS):
            return None

        # تشغيل الـ pipeline السريري الكامل (derive → ML → rules → fusion)
        pipe = domain_pipeline.assess(self.facts)
        feats = pipe['derived_features']
        triggered = pipe['rules']['triggered']
        risk_level = pipe['rules']['risk_level']  # Low / Medium / High

        # بناء تقييم بالشكل المتوقع من باقي النظام (insights + triggered_rules)
        binary = {k: v for k, v in feats.items() if k not in _CONTINUOUS_FEATS}
        continuous = {k: feats[k] for k in _CONTINUOUS_FEATS if k in feats}
        result = {
            'status': 'complete',
            'derived_features': feats,
            'binary_features': binary,
            'continuous_features': continuous,
            'triggered_rules': triggered,
            'ml': pipe['ml'],
            'pipeline': pipe,
            'insights': {
                'risk_level': risk_level,
                'triggered_rules_count': len(triggered),
                'top_rules': triggered[:5],
                'risk_factors_ar': self._clinical_risk_factors(feats, 'ar'),
                'risk_factors_en': self._clinical_risk_factors(feats, 'en'),
                'recommendations_ar': self._clinical_recommendations(risk_level, 'ar'),
                'recommendations_en': self._clinical_recommendations(risk_level, 'en'),
            },
        }

        self.domain_assessment = result

        # توحيد مستوى الخطر (LOW/MODERATE/HIGH)
        risk_mapping = {'Low': 'LOW', 'Medium': 'MODERATE', 'High': 'HIGH'}
        self.current_risk_level = risk_mapping.get(risk_level, 'LOW')

        triggered_count = len(triggered)
        self.confidence_score = min(0.95, 0.7 + (triggered_count * 0.01))

        logger.info(f"Clinical domain assessment complete: {risk_level}, "
                    f"{triggered_count} rules triggered")
        return result

    # ── مساعدات سريرية: عوامل الخطر والتوصيات من الميزات المشتقة ──
    def _clinical_risk_factors(self, feats: Dict, lang: str = 'ar') -> List[str]:
        """استخراج عوامل الخطر النشطة كنص مقروء من الميزات الـ 26."""
        labels = {
            'age_senior':   ('عمر متقدم (60–75)', 'Senior age (60–75)'),
            'age_elderly':  ('عمر كبير (75+)', 'Elderly age (75+)'),
            'bmi_overweight': ('زيادة في الوزن', 'Overweight'),
            'bmi_obese':    ('سمنة', 'Obesity'),
            'smoker_current': ('مدخّن حالي', 'Current smoker'),
            'smoker_ex':    ('مدخّن سابق', 'Ex-smoker'),
            'has_family_history': ('تاريخ عائلي لأمراض القلب', 'Family history of heart disease'),
            'work_factory': ('بيئة عمل صناعية', 'Factory work environment'),
            'hazard_stress': ('تعرّض للتوتر', 'Exposure to stress'),
            'hazard_pollution': ('تعرّض للتلوّث', 'Exposure to pollution'),
            'hazard_noise': ('تعرّض للضوضاء', 'Exposure to noise'),
            'hazard_dust':  ('تعرّض للغبار', 'Exposure to dust'),
            'hazard_chemicals': ('تعرّض لمواد كيميائية', 'Exposure to chemicals'),
            'hazard_shift_work': ('عمل بنظام الورديات', 'Shift work'),
        }
        idx = 0 if lang == 'ar' else 1
        return [labels[k][idx] for k in labels if int(feats.get(k, 0)) == 1]

    def _clinical_recommendations(self, risk_level: str, lang: str = 'ar') -> List[str]:
        """توصيات عامة حسب مستوى الخطر (تُكمَّل بتوصيات Groq عند توفّرها)."""
        recs = {
            'High': (
                ['مراجعة طبيب القلب في أقرب وقت', 'إجراء فحوصات قلبية شاملة',
                 'ضبط عوامل الخطر (التدخين، الوزن، بيئة العمل)'],
                ['Consult a cardiologist as soon as possible',
                 'Undergo a comprehensive cardiac evaluation',
                 'Control risk factors (smoking, weight, work environment)'],
            ),
            'Medium': (
                ['متابعة دورية مع الطبيب', 'تحسين نمط الحياة والنشاط البدني',
                 'تقليل التعرّض للمخاطر البيئية'],
                ['Schedule periodic medical follow-up',
                 'Improve lifestyle and physical activity',
                 'Reduce exposure to environmental hazards'],
            ),
            'Low': (
                ['الحفاظ على نمط حياة صحي', 'فحص دوري سنوي'],
                ['Maintain a healthy lifestyle', 'Annual routine check-up'],
            ),
        }
        idx = 0 if lang == 'ar' else 1
        return recs.get(risk_level, recs['Low'])[idx]
    
    # ──────────────────────────────────────────────────────────────────
    #  Context-aware extraction
    # ──────────────────────────────────────────────────────────────────
    # When the chatbot has just asked for a specific field, the patient
    # often replies with a short / partial answer that the field-agnostic
    # NER pipeline cannot parse on its own ("كلا", "120", "Chol 310",
    # "نبضات قلبي 120"). This helper interprets such an answer in the
    # context of the asked field so the conversation does not loop on
    # the same question.
    _YES_WORDS = {
        # Arabic
        'نعم', 'أيوا', 'أيوة', 'أيوه', 'اي', 'إي', 'بلى', 'يوجد',
        'موجود', 'أعاني', 'صحيح', 'أكيد',
        # English
        'yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'true', 'correct',
        'affirmative', 'absolutely',
    }
    _NO_WORDS = {
        # Arabic
        'لا', 'كلا', 'كلّا', 'مافي', 'ما في', 'ما يوجد', 'ما عندي',
        'ما أعاني', 'لا أعاني', 'لا يوجد', 'لا أشكي', 'أبداً', 'لم',
        # English
        'no', 'n', 'nope', 'nah', 'never', 'none', 'false', 'negative',
        "don't", 'not at all', 'without',
    }
    _NORMAL_WORDS = {
        # Arabic
        'طبيعي', 'عادي', 'سليم', 'بخير', 'مظبوط', 'مضبوط', 'تمام',
        # English
        'normal', 'fine', 'healthy', 'ok', 'okay', 'good', 'great',
        'within range', 'within normal', 'unremarkable',
    }

    # Arabic diacritics, tatweel, and the various alif / ya / ta-marbuta
    # forms that patients often type interchangeably. Stripping them lets a
    # short reply like "كلّاْ" / "أنْثى" / "الذكَر" match the canonical
    # keywords we look for ("كلا" / "أنثى" / "الذكر").
    _AR_DIACRITICS = 'ًٌٍَُِّْٰٕٖٓٔٗ٘'
    _AR_TATWEEL = 'ـ'

    @classmethod
    def _normalize_ar(cls, text: str) -> str:
        """Lower-case + strip Arabic diacritics + unify common letter
        variants so dialect / typo spellings still match our keywords."""
        if not text:
            return ''
        s = str(text)
        # Remove tashkeel
        for ch in cls._AR_DIACRITICS:
            s = s.replace(ch, '')
        # Remove tatweel
        s = s.replace(cls._AR_TATWEEL, '')
        # Unify alif forms (أ إ آ ٱ ا → ا)
        for ch in 'أإآٱ':
            s = s.replace(ch, 'ا')
        # Unify ya forms (ى → ي) and ta-marbuta (ة → ه)
        s = s.replace('ى', 'ي').replace('ة', 'ه')
        # Drop trailing punctuation noise that breaks substring matches
        s = s.replace('،', ' ').replace('؟', ' ').replace('!', ' ')
        return s.lower()

    @classmethod
    def _has_word(cls, text_lower: str, words) -> bool:
        """Substring match for long keywords, word-boundary match for
        short ones (≤ 3 chars). Without the boundary check, single
        letters like "n", "y", "m" would match every word that simply
        contains that letter ("angina" → "n", "hypertension" → "n"),
        flooding the classifier with false positives.
        """
        import re as _re
        norm = cls._normalize_ar(text_lower)
        for w in words:
            nw = cls._normalize_ar(w)
            if not nw:
                continue
            if len(nw) <= 3:
                # Word-boundary match for very short tokens
                if _re.search(r'(?<![\w]) ?' + _re.escape(nw) + r' ?(?![\w])', norm):
                    return True
            else:
                if nw in norm:
                    return True
        return False

    # ──────────────────────────────────────────────────────────────────
    # Helpers used by _smart_extract_for_field
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _arabic_to_western_digits(s: str) -> str:
        """٠١٢٣٤٥٦٧٨٩ -> 0123456789 (Eastern Arabic-Indic + Persian)."""
        table = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
        return s.translate(table)

    @staticmethod
    def _first_int(text: str, lo: int, hi: int):
        """First integer in [lo, hi] found in `text`, else None."""
        import re as _re
        for m in _re.finditer(r'\d+', text):
            try:
                v = int(m.group(0))
            except ValueError:
                continue
            if lo <= v <= hi:
                return v
        return None

    @staticmethod
    def _first_float(text: str, lo: float, hi: float):
        """First float in [lo, hi] found in `text`, else None."""
        import re as _re
        for m in _re.finditer(r'\d+(?:\.\d+)?', text):
            try:
                v = float(m.group(0))
            except ValueError:
                continue
            if lo <= v <= hi:
                return v
        return None

    def _smart_extract_for_field(self, field_name: str, raw_text: str):
        """Interpret `raw_text` as an answer to a question about
        `field_name`. Returns the extracted value, or None.

        Each clinical field has its own ruleset combining:
          - numeric extraction with a valid clinical range,
          - dialectal Arabic / English keyword lookups (with diacritics
            and alif / ya / ta-marbuta normalised away),
          - explicit handling of "normal / healthy" answers,
          - explicit handling of negations and the qualitative scale
            (low / moderate / high) when the patient does not give a
            precise number.
        """
        import re as _re
        if raw_text is None:
            return None
        text = str(raw_text).strip()
        if not text:
            return None

        # Convert Arabic-Indic / Persian digits so numeric checks work uniformly.
        text = self._arabic_to_western_digits(text)
        # `text_lower` is the Arabic-normalised + lower-cased form used by
        # every substring check below.
        text_lower = self._normalize_ar(text)
        # "غير طبيعي" / "non-normal" / "abnormal" must override the plain
        # NORMAL check, otherwise the trailing word "طبيعي" is mistaken
        # for a healthy reply.
        _abnormal_markers = ('غير طبيعي', 'غير عادي', 'ليس طبيعي', 'ليس عادي',
                             'abnormal', 'not normal', 'non-normal')
        is_abnormal = any(m in text_lower for m in _abnormal_markers)
        is_normal = (not is_abnormal) and self._has_word(text_lower, self._NORMAL_WORDS)
        is_no     = self._has_word(text_lower, self._NO_WORDS)
        is_yes    = self._has_word(text_lower, self._YES_WORDS)

        # ─────────────────────── 1. age ───────────────────────
        if field_name == 'age':
            v = self._first_int(text, 1, 120)
            if v is not None:
                return v
            if 'طفل' in text_lower or 'baby' in text_lower or 'child' in text_lower or 'kid' in text_lower:
                return 10
            if 'مراهق' in text_lower or 'teenager' in text_lower or 'teen' in text_lower:
                return 16
            if 'شاب' in text_lower or 'young' in text_lower or 'youth' in text_lower:
                return 25
            if 'بالغ' in text_lower or 'adult' in text_lower or 'middle-aged' in text_lower:
                return 45
            if ('كبير' in text_lower or 'مسن' in text_lower or 'elderly' in text_lower
                    or 'old' in text_lower or 'aged' in text_lower or 'senior' in text_lower):
                return 70
            return None

        # ─────────────────────── 2. gender ───────────────────────
        if field_name == 'gender':
            stripped = text_lower.strip()
            if (stripped in ('f', 'female', 'fem')
                    or 'انثي' in text_lower or 'امراه' in text_lower
                    or 'بنت' in text_lower or 'سيده' in text_lower
                    or 'female' in text_lower or 'woman' in text_lower
                    or 'lady' in text_lower or 'girl' in text_lower
                    or 'gal' in text_lower):
                return 'female'
            if (stripped in ('m', 'male', 'masc')
                    or 'ذكر' in text_lower or 'رجل' in text_lower
                    or 'ولد' in text_lower or 'male' in text_lower
                    or 'man' in text_lower or 'guy' in text_lower
                    or 'boy' in text_lower or 'gentleman' in text_lower):
                return 'male'
            return None

        # ─────────────────────── 3. height_cm ───────────────────────
        if field_name == 'height_cm':
            # متر / m مع كسر عشري (1.75) → سنتيمتر
            mf = _re.search(r'(\d\.\d{1,2})\s*(?:m\b|متر)', text, _re.IGNORECASE)
            if mf:
                return round(float(mf.group(1)) * 100)
            v = self._first_int(text, 50, 250)
            if v is not None:
                return v
            f = self._first_float(text, 1.2, 2.5)
            if f is not None:  # قيمة بالمتر بدون وحدة صريحة
                return round(f * 100)
            return None

        # ─────────────────────── 4. weight_kg ───────────────────────
        if field_name == 'weight_kg':
            v = self._first_float(text, 20, 400)
            if v is not None:
                return int(v) if float(v).is_integer() else v
            return None

        # ─────────────────────── 5. smoking_status ───────────────────────
        if field_name == 'smoking_status':
            # الترتيب مهم: غير مدخّن ثم سابق ثم حالي (كلها تحوي "مدخن")
            if (is_no or 'غير مدخن' in text_lower or 'لا ادخن' in text_lower
                    or 'ما ادخن' in text_lower or 'non-smoker' in text_lower
                    or 'non smoker' in text_lower or 'never' in text_lower
                    or 'nonsmoker' in text_lower or "don't smoke" in text_lower):
                return 'non-smoker'
            if ('سابق' in text_lower or 'اقلعت' in text_lower or 'قلعت' in text_lower
                    or 'توقفت' in text_lower or 'تركت' in text_lower
                    or 'ex-smoker' in text_lower or 'ex smoker' in text_lower
                    or 'former' in text_lower or 'quit' in text_lower
                    or 'stopped' in text_lower or 'used to smoke' in text_lower):
                return 'ex-smoker'
            if ('مدخن' in text_lower or 'ادخن' in text_lower or 'دخان' in text_lower
                    or 'سيجار' in text_lower or 'smoke' in text_lower
                    or 'smoker' in text_lower or 'cigarette' in text_lower
                    or 'tobacco' in text_lower or is_yes):
                return 'current smoker'
            return None

        # ─────────────────────── 6. workplace_type ───────────────────────
        if field_name == 'workplace_type':
            if ('مصنع' in text_lower or 'معمل' in text_lower
                    or 'factory' in text_lower or 'plant' in text_lower
                    or 'industrial' in text_lower or 'workshop' in text_lower):
                return 'factory'
            if ('مكتب' in text_lower or 'اداري' in text_lower
                    or 'office' in text_lower or 'desk' in text_lower
                    or 'administrative' in text_lower or 'clerical' in text_lower):
                return 'office'
            return None

        # ─────────────────────── 7. environmental_hazards ───────────────────────
        if field_name == 'environmental_hazards':
            hazard_map = {
                'stress':     ('توتر', 'ضغط نفسي', 'اجهاد', 'stress'),
                'pollution':  ('تلوث', 'pollution', 'polluted'),
                'noise':      ('ضوضاء', 'ضجيج', 'noise', 'noisy'),
                'dust':       ('غبار', 'اتربه', 'dust', 'dusty'),
                'chemicals':  ('كيميا', 'كيماو', 'chemical'),
                'shift work': ('ورديات', 'شفت', 'shift', 'night shift'),
            }
            found = []
            for canon, cues in hazard_map.items():
                if any(c in text_lower for c in cues):
                    found.append(canon)
            if found:
                return found
            # "لا يوجد" / "none" → قائمة فارغة (إجابة صريحة بعدم وجود مخاطر)
            if is_no or is_normal or 'none' in text_lower or 'لا يوجد' in text_lower:
                return []
            return None

        # ─────────────────────── 8. family_history ───────────────────────
        if field_name == 'family_history':
            if (is_no or 'لا يوجد' in text_lower or 'no family' in text_lower
                    or 'لا تاريخ' in text_lower or 'negative' in text_lower):
                return 'no'
            if (is_yes or 'يوجد' in text_lower or 'نعم' in text_lower
                    or 'عائلي' in text_lower or 'وراثي' in text_lower
                    or 'family history' in text_lower or 'hereditary' in text_lower
                    or 'genetic' in text_lower or 'positive' in text_lower):
                return 'yes'
            return None

        # ──────── 9. أمراض نعم/لا (ضغط، سكري، قلب، مزمنة، سمنة، سكري حمل) ────────
        if field_name in ('hypertension', 'diabetes', 'cardiovascular_disease',
                           'chronic_diseases', 'obesity', 'gestational_diabetes'):
            # نفي / طبيعي / سليم → لا
            if (is_no or is_normal or 'لا يوجد' in text_lower
                    or 'ما عندي' in text_lower or 'negative' in text_lower
                    or 'none' in text_lower):
                return 'no'
            # نعم / مرتفع / عالي / مصاب → نعم
            if (is_yes or 'مرتفع' in text_lower or 'عالي' in text_lower
                    or 'مصاب' in text_lower or 'عندي' in text_lower
                    or 'positive' in text_lower or 'high' in text_lower):
                return 'yes'
            # ذكر اسم المرض نفسه = نعم (مثل "ضغط"، "سكري")
            if self._field_keyword_present(field_name, text):
                return 'yes'
            return None

        # ──────── 10. HbA1c (السكر التراكمي) ────────
        if field_name == 'hba1c':
            v = self._first_float(text, 3.0, 20.0)
            if v is not None:
                return v
            if is_normal:
                return 5.4
            if 'مرتفع' in text_lower or 'عالي' in text_lower or 'high' in text_lower:
                return 7.5
            return None

        # ──────── 11. الكوليسترول ────────
        if field_name == 'cholesterol':
            v = self._first_int(text, 80, 500)
            if v is not None:
                return v
            if is_normal:
                return 190
            if 'مرتفع' in text_lower or 'عالي' in text_lower or 'high' in text_lower:
                return 250
            return None

        # ──────── 12. مؤشر كتلة الجسم ────────
        if field_name == 'bmi':
            v = self._first_float(text, 10.0, 80.0)
            if v is not None:
                return v
            return None

        # ──────── 13. سنوات التدخين / سنوات الإقلاع ────────
        if field_name in ('years_smoked', 'years_since_quit'):
            v = self._first_int(text, 0, 90)
            if v is not None:
                return v
            if is_no or is_normal:
                return 0
            return None

        return None

    def _normalize_value(self, field_name: str, value):
        """
        تطبيع القيمة - تحويل الأرقام من string إلى int/float
        
        Args:
            field_name: اسم الحقل (استخدام أسماء BioBERT الموحدة)
            value: القيمة (قد تكون string أو int أو float)
            
        Returns:
            القيمة المطبّعة (int/float للحقول الرقمية، string للباقي)
        """
        # إذا كانت القيمة بالفعل رقماً، أرجعها كما هي
        if isinstance(value, (int, float)):
            return value

        # القوائم (environmental_hazards) تبقى كما هي
        if isinstance(value, (list, tuple)):
            return list(value)

        # الحقول الرقمية الأصل الـ 9
        numeric_fields = ['age', 'height_cm', 'weight_kg', 'bmi']

        if field_name in numeric_fields:
            try:
                # محاولة تحويلها إلى int أولاً
                if '.' not in str(value):
                    return int(value)
                else:
                    return float(value)
            except (ValueError, TypeError):
                # إذا فشل التحويل، أرجع القيمة كما هي
                return value

        # الحقول غير الرقمية - أرجعها كـ string
        return str(value)

    def _get_field_arabic_name(self, field_name: str) -> str:
        """تحويل اسم الحقل للعربية — يعتمد على مصدر الترجمة الموحّد."""
        from config.translations import get_field_name
        return get_field_name(field_name, 'ar')
    
    def _safe_int(self, value, default=0) -> int:
        """تحويل آمن للقيمة إلى عدد صحيح"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                import re
                numbers = re.findall(r'\d+', value)
                if numbers:
                    return int(numbers[0])
            return default
        except:
            return default
    
    def _calculate_risk_level(self) -> str:
        """حساب مستوى الخطر بناءً على الحقائق المجمعة"""
        # استخدام Domain Rules إذا كان التقييم متاحاً
        if self.domain_assessment:
            # New structure: domain_assessment['insights']['risk_level']
            if isinstance(self.domain_assessment, dict):
                if 'insights' in self.domain_assessment:
                    risk_level = self.domain_assessment['insights'].get('risk_level', 'UNKNOWN')
                    # Map from 'Low'/'Medium'/'High' to old format
                    risk_mapping = {'Low': 'LOW', 'Medium': 'MODERATE', 'High': 'HIGH'}
                    return risk_mapping.get(risk_level, 'LOW')
                # Old structure fallback
                elif 'risk_level' in self.domain_assessment:
                    return self.domain_assessment['risk_level']
        
        # الطريقة القديمة كـ fallback — عوامل الخطر السريرية
        risk_count = self._count_clinical_risk_factors()

        # تصنيف المستوى
        if risk_count >= 4:
            return 'CRITICAL'
        elif risk_count >= 3:
            return 'HIGH'
        elif risk_count >= 2:
            return 'MODERATE'
        else:
            return 'LOW'

    def _compute_bmi(self):
        """حساب مؤشر كتلة الجسم من الطول والوزن (أو إرجاع bmi المخزّن)."""
        bmi = self.facts.get('bmi')
        try:
            if bmi:
                return float(bmi)
        except (TypeError, ValueError):
            pass
        try:
            h = float(self.facts.get('height_cm', 0))
            w = float(self.facts.get('weight_kg', 0))
            if h and w:
                return w / ((h / 100.0) ** 2)
        except (TypeError, ValueError):
            pass
        return None

    def _count_clinical_risk_factors(self) -> int:
        """عدّ عوامل الخطر السريرية من الحقول الأصل الـ 9."""
        risk_count = 0
        if self._safe_int(self.facts.get('age', 0)) >= 60:
            risk_count += 1
        bmi = self._compute_bmi()
        if bmi and bmi >= 30:
            risk_count += 1
        smk = str(self.facts.get('smoking_status', '')).lower()
        if smk == 'current smoker':
            risk_count += 2  # وزن أعلى
        elif smk == 'ex-smoker':
            risk_count += 1
        fh = str(self.facts.get('family_history', '')).lower()
        if fh and fh not in ('no', 'none', '', '0', 'false', 'لا', 'لا يوجد'):
            risk_count += 1
        hazards = self.facts.get('environmental_hazards') or []
        if self.facts.get('workplace_type') == 'factory' and hazards:
            risk_count += 1
        return risk_count
    
    def _calculate_confidence(self) -> float:
        """حساب درجة الثقة"""
        # استخدام Domain Rules confidence إذا كان متاحاً
        if self.domain_assessment and 'confidence' in self.domain_assessment:
            return self.domain_assessment['confidence']
        
        # الطريقة القديمة كـ fallback
        facts_count = len(self.answered_fields)
        base_confidence = min(0.3 + (facts_count * 0.055), 0.95)
        
        # زيادة الثقة إذا كانت الأجوبة واضحة (عوامل خطر سريرية رئيسية)
        high_quality_facts = sum(1 for f in self.answered_fields
                                if f in ['smoking_status', 'family_history', 'age'])

        confidence = base_confidence + (high_quality_facts * 0.05)
        return min(confidence, 1.0)

    def _should_warn(self) -> bool:
        """هل يجب تحذير المستخدم؟"""
        # تحذير إذا كان مدخّناً حالياً مع تاريخ عائلي
        fh = str(self.facts.get('family_history', '')).lower()
        if (self.facts.get('smoking_status') == 'current smoker'
                and fh not in ('no', 'none', '', '0', 'false', 'لا', 'لا يوجد')):
            return True

        # تحذير إذا كانت السمنة شديدة
        bmi = self._compute_bmi()
        if bmi and bmi >= 35:
            return True

        # تحذير إذا كان هناك خطر حرج
        if self.current_risk_level == 'CRITICAL':
            return True

        return False
    
    def _get_warning_severity(self) -> str:
        """تحديد شدة التحذير"""
        if self.current_risk_level == 'CRITICAL':
            return 'critical'
        elif self.current_risk_level == 'HIGH':
            return 'high'
        else:
            return 'medium'
    
    def _select_next_question(self, priorities: List[QuestionPriority]) -> Optional[Dict]:
        """اختيار السؤال التالي"""
        if not priorities:
            return None
        
        # في حالة الخطر العالي، اختر أسئلة حرجة
        if self.current_risk_level in ['CRITICAL', 'HIGH']:
            critical = [p for p in priorities if p.is_critical]
            if critical:
                priorities = critical
        
        # اختر السؤال
        next_q = self.question_selector.select_next_question(
            priorities,
            self.facts,
            self.language
        )
        
        return next_q
    
    def set_groq_api_key(self, api_key: str):
        """Update Groq API key at runtime"""
        self.groq_client.set_api_key(api_key)
        self.result_interpreter = ResultInterpreter(self.groq_client)
        self.recommendation_engine = RecommendationEngine(self.groq_client)
        self.groq_ner = GroqNER(self.groq_client)
        self.conversation_manager = SmartConversationManager(self.groq_client, self.language)
        logger.info(f"Groq API key updated, available: {self.groq_client.is_available}")

    @property
    def conversation_mode(self) -> str:
        """Return current conversation mode: 'smart' or 'classic'"""
        return "smart" if self.groq_client.is_available else "classic"

    def _autofill_derived_facts(self):
        """ملء الحقول القابلة للاستنتاج منطقياً حتى يكتمل العدّ بدقة دون
        طرح أسئلة لا معنى لها (bmi من الطول/الوزن، السمنة من bmi، وسنوات
        الإقلاع/التدخين وسكري الحمل من حالة التدخين والجنس)."""
        f = self.facts

        def _set(field, value):
            if value is not None and field not in self.answered_fields:
                f[field] = value
                self.answered_fields.append(field)

        # bmi من الطول والوزن
        if not f.get('bmi') and f.get('height_cm') and f.get('weight_kg'):
            try:
                h = float(f['height_cm']) / 100.0
                w = float(f['weight_kg'])
                if h > 0:
                    _set('bmi', round(w / (h * h), 1))
            except (ValueError, TypeError):
                pass

        # السمنة من bmi
        if not f.get('obesity') and f.get('bmi'):
            try:
                _set('obesity', 'yes' if float(f['bmi']) >= 30 else 'no')
            except (ValueError, TypeError):
                pass

        # سنوات التدخين/الإقلاع حسب حالة التدخين
        smoke = str(f.get('smoking_status', '')).strip().lower()
        if smoke in ('non-smoker', 'غير مدخن', 'غير مدخّن'):
            _set('years_smoked', 0)
            _set('years_since_quit', 0)
        elif smoke in ('current smoker', 'مدخن حالي', 'مدخّن حالي'):
            _set('years_since_quit', 0)

        # سكري الحمل لا ينطبق على الذكور
        if str(f.get('gender', '')).strip().lower() in ('male', 'ذكر'):
            _set('gestational_diabetes', 'no')

    def process_smart_input(self, text: str) -> Dict:
        """
        معالجة النص الحر من المريض — الوضع الذكي (v8.0.0)

        1. يستخرج الحقول باستخدام Groq NER (+ BioBERT كاحتياط)
        2. يخزن الحقول ويحدث الحالة
        3. يولد رد طبيب طبيعي باستخدام ConversationManager

        Args:
            text: ما كتبه المريض (نص حر بالعربية أو الإنجليزية)

        Returns:
            Dict مع: mode, extracted_fields, doctor_response, progress, warning, next_field
        """
        logger.info(f"Smart input processing: '{text[:60]}...'")

        # === الخطوة 0: تفسير سياقي للسؤال المطروح ===
        # Catches short replies ("كلا", "120", "Chol 310") that the
        # generic NER pipeline would miss.
        context_extracted = {}
        last_asked = getattr(self, '_last_asked_field', None)

        # First-best target: the field the chatbot just asked for.
        if last_asked and last_asked not in self.answered_fields:
            ctx_value = self._smart_extract_for_field(last_asked, text)
            if ctx_value is not None:
                context_extracted[last_asked] = ctx_value
                logger.info(f"Context-aware extraction (asked): {last_asked} = {ctx_value}")

        # Fallback safety net: for very short / terse replies (≤ 30 chars)
        # also try every remaining unanswered field, since the patient
        # almost certainly meant to answer the most relevant pending
        # question. The priority scorer's order is honoured, so the
        # highest-priority field gets matched first.
        if not context_extracted and text and len(text.strip()) <= 30:
            ordered_remaining = [
                f for f in (
                    'gender', 'smoking_status', 'family_history', 'workplace_type',
                    'environmental_hazards', 'age', 'height_cm', 'weight_kg',
                )
                if f not in self.answered_fields
            ]
            for f in ordered_remaining:
                ctx_value = self._smart_extract_for_field(f, text)
                if ctx_value is not None:
                    context_extracted[f] = ctx_value
                    logger.info(f"Context-aware extraction (fallback): {f} = {ctx_value}")
                    break  # one field per short reply

        # === الخطوة 1: استخراج الحقول ===
        # Try Groq NER first
        groq_extracted = self.groq_ner.extract(text)

        # Try BioBERT as supplement/fallback
        biobert_extracted = self.biobert_ner.extract_entities(text)

        # Universal hallucination guard: every extractor (context fallback,
        # Groq LLM, BioBERT regex) must produce fields whose keyword
        # family actually appears in the patient's input — otherwise the
        # value is a phantom and gets dropped. The field the chatbot
        # just asked about (`last_asked`) is exempt, because a one-word
        # reply like "طبيعي" is a legitimate answer to that question
        # even with no field-name keyword in the text.
        groq_extracted = self._reject_phantom_fields(
            text, groq_extracted, source='groq', exempt_field=last_asked
        )
        biobert_extracted = self._reject_phantom_fields(
            text, biobert_extracted, source='biobert', exempt_field=last_asked
        )
        # The context fallback's first-best hit IS the asked field, so it's
        # already legitimate. Only the secondary "≤30 char safety net" can
        # pick up an unrelated field — filter just that case.
        context_extracted = self._reject_phantom_fields(
            text, context_extracted, source='context', exempt_field=last_asked
        )

        # Merge: context > Groq > BioBERT, then fill gaps
        merged_extracted = {}
        all_fields = set(
            list(context_extracted.keys())
            + list(groq_extracted.keys())
            + list(biobert_extracted.keys())
        )

        for field in all_fields:
            if field in self.answered_fields:
                continue  # Skip already answered
            if field in context_extracted:
                merged_extracted[field] = context_extracted[field]
            elif field in groq_extracted:
                merged_extracted[field] = groq_extracted[field]
            elif field in biobert_extracted:
                merged_extracted[field] = biobert_extracted[field]

        logger.info(f"Merged extraction: {len(merged_extracted)} new fields "
                    f"(Groq: {len(groq_extracted)}, BioBERT: {len(biobert_extracted)})")

        # === الخطوة 2: تخزين الحقول ===
        # Pick up Groq's per-field confidence (written by GroqNER.extract).
        groq_conf = getattr(self.groq_ner, 'last_confidences', {}) or {}
        extracted_details = []
        for field_name, value in merged_extracted.items():
            normalized = self._normalize_value(field_name, value)
            self.facts[field_name] = normalized
            if field_name not in self.answered_fields:
                self.answered_fields.append(field_name)

            if field_name in context_extracted:
                source = 'context'
                conf = 1.0
            elif field_name in groq_extracted:
                source = 'groq'
                conf = float(groq_conf.get(field_name, 0.85))
            else:
                source = 'biobert'
                conf = 0.75  # regex match is decent but lacks model context
            extracted_details.append({
                'field': field_name,
                'field_ar': self._get_field_arabic_name(field_name),
                'value': normalized,
                'source': source,
                'confidence': conf,
            })

        # اشتقاق تلقائي للحقول القابلة للاستنتاج (لتجنّب أسئلة بلا فائدة)
        self._autofill_derived_facts()

        # === الخطوة 3: تحديث الحالة ===
        self.current_risk_level = self._calculate_risk_level()
        self.confidence_score = self._calculate_confidence()

        # Internal dialog for each extracted field
        last_thought = None
        for detail in extracted_details:
            thought = self.dialog_manager.analyze_answer(
                detail['field'], detail['value'], self.facts
            )
            last_thought = thought

        inference = self.dialog_manager.infer_from_facts(self.facts)

        # Domain assessment check
        domain_assessment = self.get_domain_assessment()

        # === الخطوة 4: تحديد الحقل التالي ===
        remaining_fields = [f for f in ASKED_FIELDS
            if f not in self.answered_fields
        ]

        priorities = self.priority_scorer.calculate_priorities(
            self.facts, self.current_risk_level, self.answered_fields
        )

        next_field = None
        next_question_classic = None
        if priorities:
            next_field = priorities[0].field_name
            next_question_classic = self._select_next_question(priorities)

        # Remember which field the chatbot is about to ask for, so the
        # next turn can interpret short answers in this context.
        self._last_asked_field = next_field

        # === الخطوة 5: Warning check ===
        warning = None
        if self._should_warn():
            warning = self.dialog_manager.trigger_warning(
                'critical_symptoms',
                self._get_warning_severity(),
                {'text': text}
            )

        # === الخطوة 6: توليد رد الطبيب الذكي ===
        doctor_response = None
        mode = "smart"

        if next_field and self.groq_client.is_available:
            doctor_response = self.conversation_manager.generate_response_with_question(
                patient_message=text,
                extracted_fields=merged_extracted,
                collected_facts=self.facts,
                remaining_fields=remaining_fields,
                next_field=next_field,
                risk_level=self.current_risk_level
            )
        elif not remaining_fields and self.groq_client.is_available:
            # All fields collected
            doctor_response = self.conversation_manager._generate_completion_message(self.facts)

        # Fallback to classic if Groq conversation fails
        if not doctor_response:
            mode = "classic"
            logger.info("Falling back to classic mode for this turn")

        # === بناء الاستجابة ===
        response = {
            'mode': mode,
            'step': len(self.conversation_history) + 1,
            'extracted_fields': extracted_details,
            'doctor_response': doctor_response,
            'next_field': next_field,
            'next_question': next_question_classic,  # Classic fallback
            'internal_thought': {
                'thought': last_thought.thought if last_thought else '',
                'category': last_thought.category if last_thought else 'analysis',
                'confidence': last_thought.confidence if last_thought else 0
            },
            'inference': {
                'thought': inference.thought,
                'confidence': inference.confidence
            },
            'current_status': {
                'risk_level': self.current_risk_level,
                'confidence_score': self.confidence_score,
                'facts_collected': len(self.answered_fields),
                'total_facts': len(ASKED_FIELDS)
            },
            'domain_assessment': domain_assessment,
            'warning': {
                'triggered': warning is not None,
                'message': warning.thought if warning else None
            },
            'progress': {
                'percentage': int((len(self.answered_fields) / len(ASKED_FIELDS)) * 100),
                'answered': len(self.answered_fields),
                'remaining': len(ASKED_FIELDS) - len(self.answered_fields)
            },
            'all_complete': len(remaining_fields) == 0
        }

        self.conversation_history.append(response)
        return response

    def get_smart_greeting(self) -> Optional[str]:
        """
        Get the initial doctor greeting for smart mode.
        Returns None if Groq is unavailable.
        """
        return self.conversation_manager.generate_greeting()

    def get_current_status(self) -> Dict:
        """الحصول على الحالة الحالية"""
        return {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'language': self.language,
            'facts_count': len(self.answered_fields),
            'risk_level': self.current_risk_level,
            'confidence': self.confidence_score,
            'conversation_length': len(self.conversation_history),
            'internal_monologue': self.dialog_manager.get_internal_monologue()
        }
    
    def get_final_assessment(self) -> Dict:
        """
        الحصول على التقييم النهائي الشامل
        
        يدمج:
        1. Domain Rules Analysis
        2. Advanced Features Generation
        3. ML Model Prediction
        4. Final Decision (Rule-Based Decision Tree)
        
        Returns:
            التقييم الشامل النهائي
        """
        if len(self.answered_fields) < len(ASKED_FIELDS):  # يجب جمع معظم الحقائق
            return {
                'status': 'incomplete',
                'message': 'لم يتم جمع معلومات كافية',
                'facts_collected': len(self.answered_fields),
                'facts_needed': len(ASKED_FIELDS)
            }
        
        logger.info("Generating comprehensive final assessment with ML integration")
        
        # 1. Domain Rules Analysis السريري (derive → rules) — موجود بالفعل
        domain_assessment = self.domain_assessment or self.get_domain_assessment() or {}

        # 2. الميزات المهندَسة التي يستهلكها النموذج السريري (18 ميزة).
        #    القرار النهائي يعتمد على نموذج GB (domain_assessment['ml']) لا على
        #    هندسة الـ 26 ميزة القديمة، لذا لا نُمرّر advanced_features للمحرّك القديم.
        derived = domain_assessment.get('derived_features') or {}

        def _is_flag_on(v):
            return (isinstance(v, (int, float)) and not isinstance(v, bool)
                    and int(v) == 1)

        features_summary = {
            'derived_features': derived,
            'active': [k for k, v in derived.items()
                       if k not in _CONTINUOUS_FEATS and _is_flag_on(v)],
        }
        advanced_features = None
        logger.info(f"Engineered {len([k for k in derived if k != 'risk_probability'])} "
                    f"clinical model features")

        # 3. ML Model Prediction (النموذج السريري clinical_model.pkl)
        try:
            ml_prediction = (domain_assessment.get('ml')
                             or clinical_ml_predictor.predict_from_features(derived))
            logger.info(f"ML Prediction: {ml_prediction.get('prediction')} "
                        f"(prob: {ml_prediction.get('probability', 0):.2%})")
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            ml_prediction = {'probability': 0.0, 'prediction': 'Unknown',
                             'confidence': 0.0, 'risk_level': 'UNKNOWN',
                             'source': 'Error'}

        # 4. Final Decision using Rule-Based Decision Tree
        try:
            if advanced_features is not None:
                final_decision = final_decision_engine.make_decision(
                    domain_assessment,
                    ml_prediction,
                    advanced_features
                )
                logger.info(f"Final Decision: {final_decision.get('final_risk_level')}")
            else:
                final_decision = self._generate_fallback_decision(domain_assessment)
        except Exception as e:
            logger.error(f"Error in final decision: {e}")
            final_decision = self._generate_fallback_decision(domain_assessment)
        
        # مزامنة مستوى الخطر مع القرار النهائي
        if final_decision and 'final_risk_level' in final_decision:
            self.current_risk_level = final_decision['final_risk_level']

        # 5. Groq AI Enhancement (v7.0.0)
        groq_interpretation = None
        groq_recommendations = None

        if self.groq_client.is_available and final_decision:
            try:
                groq_interpretation = self.result_interpreter.interpret(
                    final_decision, self.facts, self.language
                )
                logger.info("Groq interpretation generated")
            except Exception as e:
                logger.error(f"Error generating Groq interpretation: {e}")

            try:
                groq_recommendations = self.recommendation_engine.recommend(
                    final_decision, self.facts, self.language
                )
                logger.info("Groq recommendations generated")
            except Exception as e:
                logger.error(f"Error generating Groq recommendations: {e}")

        # بناء التقييم الشامل
        assessment = {
            'status': 'complete',

            # القسم 1: Domain Rules Analysis
            'domain_rules': domain_assessment,

            # القسم 2: Engineered Features
            # 26 ميزة مهندَسة مشتقة من الـ 9 ميزات الأصل
            # (5 عمر + 3 BMI + 2 جنس + 3 تدخين + 1 تاريخ عائلي
            #  + 2 عمل + 6 مخاطر + 4 رقمية خام = 26)، مطابقة لـ
            # models/feature_names.json.
            'advanced_features': {
                'summary': features_summary,
                'total_features': len([k for k in derived if k != 'risk_probability'])
            },

            # القسم 3: ML Model Prediction
            'ml_prediction': ml_prediction,

            # القسم 4: Final Decision
            'final_decision': final_decision,

            # القسم 5: Groq AI Enhancement (v7.0.0)
            'groq_interpretation': groq_interpretation,
            'groq_recommendations': groq_recommendations,
            'groq_available': self.groq_client.is_available,

            # معلومات عامة
            'metadata': {
                'facts_collected': len(self.answered_fields),
                'facts_summary': self.facts,
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'version': '7.0.0'
            }
        }

        return assessment
    
    def _generate_fallback_decision(self, domain_assessment: Dict) -> Dict:
        """
        توليد قرار احتياطي في حالة فشل ML
        
        Args:
            domain_assessment: تقييم القواعد الطبية
            
        Returns:
            قرار احتياطي بسيط
        """
        # The domain engine returns its risk_level inside
        # domain_assessment['insights'] (capitalised as Low / Medium / High).
        # Read it from the correct location and normalise to upper-case so
        # the downstream risk_mapping always finds it.
        insights = domain_assessment.get('insights', {}) or {}
        domain_risk_raw = (
            insights.get('risk_level')
            or domain_assessment.get('risk_level')
            or 'UNKNOWN'
        )
        domain_risk = str(domain_risk_raw).upper()

        # تحويل من Domain risk لـ Final risk
        risk_mapping = {
            'CRITICAL': 'HIGH',
            'HIGH': 'HIGH',
            'MEDIUM': 'MODERATE',
            'MODERATE': 'MODERATE',
            'LOW': 'LOW',
            'UNKNOWN': 'MODERATE'
        }

        final_risk = risk_mapping.get(domain_risk, 'MODERATE')
        
        return {
            'final_risk_level': final_risk,
            'final_risk_level_ar': self._translate_risk_level(final_risk),
            'confidence': 0.60,
            'reasoning_en': f'Based on domain rules analysis only (ML unavailable)',
            'reasoning_ar': f'بناءً على القواعد الطبية فقط (ML غير متاح)',
            'sources': {
                'domain_rules': {
                    'risk_level': domain_risk
                }
            },
            'recommendations': domain_assessment.get('insights', {}).get('recommendations_ar', []),
            'metadata': {
                'fallback': True,
                'domain_risk': domain_risk
            }
        }
    
    def _translate_risk_level(self, risk_level: str) -> str:
        """ترجمة مستوى الخطر للعربية"""
        translations = {
            'CRITICAL': 'حرج',
            'HIGH': 'عالي',
            'MODERATE': 'متوسط',
            'LOW': 'منخفض'
        }
        return translations.get(risk_level, risk_level)
    
    def _generate_diagnosis(self) -> str:
        """توليد التشخيص"""
        if self.current_risk_level == 'CRITICAL':
            return 'احتمالية عالية جداً لأمراض القلب - يجب استشارة طبيب فوراً'
        elif self.current_risk_level == 'HIGH':
            return 'احتمالية عالية لأمراض القلب - يجب استشارة طبيب متخصص'
        elif self.current_risk_level == 'MODERATE':
            return 'احتمالية متوسطة لأمراض القلب - يجب متابعة دقيقة'
        else:
            return 'احتمالية منخفضة لأمراض القلب - استمر في نمط حياة صحي'

    def _calculate_risk_score(self) -> float:
        """حساب درجة الخطر من 0-10"""
        risk_scores = {
            'CRITICAL': 8.5,
            'HIGH': 6.5,
            'MODERATE': 4.0,
            'LOW': 2.0
        }
        return risk_scores.get(self.current_risk_level, 0)
    
    def _generate_recommendations(self) -> List[str]:
        """توليد التوصيات"""
        recommendations = []
        
        if self.current_risk_level in ['CRITICAL', 'HIGH']:
            recommendations.append("استشارة طبيب قلب متخصص بشكل عاجل")
            recommendations.append("إجراء فحوصات قلبية شاملة")

        if self.facts.get('smoking_status') == 'current smoker':
            recommendations.append("الإقلاع عن التدخين فوراً")

        bmi = self._compute_bmi()
        if bmi and bmi >= 30:
            recommendations.append("إنقاص الوزن وتحسين نمط التغذية")
        elif bmi and bmi >= 25:
            recommendations.append("ضبط الوزن وزيادة النشاط البدني")

        hazards = self.facts.get('environmental_hazards') or []
        if self.facts.get('workplace_type') == 'factory' and hazards:
            recommendations.append("استخدام معدات الحماية وتقليل التعرّض للمخاطر المهنية")

        fh = str(self.facts.get('family_history', '')).lower()
        if fh and fh not in ('no', 'none', '', '0', 'false', 'لا', 'لا يوجد'):
            recommendations.append("فحص دوري مبكر بسبب التاريخ العائلي")

        if not recommendations:
            recommendations.append("الاستمرار في نمط حياة صحي")
            recommendations.append("المتابعة الدورية مع الطبيب")

        return recommendations
    
    def _generate_full_reasoning(self) -> str:
        """توليد التفسير الكامل للتشخيص"""
        reasoning = " التحليل الكامل:\n"
        reasoning += "=" * 50 + "\n"
        
        # عوامل الخطر الموجودة (سريرية)
        risk_factors = []

        age = self._safe_int(self.facts.get('age', 0))
        if age >= 60:
            risk_factors.append(f" العمر: {age} سنة (≥ 60)")

        bmi = self._compute_bmi()
        if bmi and bmi >= 30:
            risk_factors.append(f" سمنة: مؤشر كتلة الجسم {bmi:.1f}")
        elif bmi and bmi >= 25:
            risk_factors.append(f" زيادة وزن: مؤشر كتلة الجسم {bmi:.1f}")

        smk = str(self.facts.get('smoking_status', '')).lower()
        if smk == 'current smoker':
            risk_factors.append(" مدخّن حالي")
        elif smk == 'ex-smoker':
            risk_factors.append(" مدخّن سابق")

        fh = str(self.facts.get('family_history', '')).lower()
        if fh and fh not in ('no', 'none', '', '0', 'false', 'لا', 'لا يوجد'):
            risk_factors.append(" تاريخ عائلي لأمراض القلب")

        hazards = self.facts.get('environmental_hazards') or []
        if self.facts.get('workplace_type') == 'factory' and hazards:
            risk_factors.append(f" بيئة عمل صناعية مع مخاطر: {', '.join(hazards)}")

        reasoning += "\n".join(risk_factors) if risk_factors else " لا توجد عوامل خطر واضحة"
        
        reasoning += "\n\n" + "=" * 50 + "\n"
        reasoning += f"النتيجة النهائية: {self._generate_diagnosis()}\n"
        reasoning += f"درجة الخطر: {self.current_risk_level} ({self._calculate_risk_score():.1f}/10)\n"
        reasoning += f"درجة الثقة: {self.confidence_score:.0%}\n"
        
        return reasoning
    
    def export_session(self) -> Dict:
        """تصدير جلسة كاملة"""
        return {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'language': self.language,
            'facts': self.facts,
            'risk_level': self.current_risk_level,
            'confidence': self.confidence_score,
            'conversation_history': self.conversation_history,
            'assessment': self.get_final_assessment(),
            'internal_monologue': self.dialog_manager.get_internal_monologue()
        }
    
    def save_session(self, filepath: str):
        """حفظ الجلسة في ملف"""
        import json
        
        session_data = self.export_session()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"تم حفظ الجلسة في: {filepath}")


# مثال على الاستخدام
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print(" SELF-REASONING CHATBOT - Integrated Demo")
    print("="*70 + "\n")
    
    # إنشاء الـ Chatbot
    chatbot = IntegratedSelfReasoningChatbot(language='ar')
    
    # محاكاة حوار كامل (الحقول السريرية الأصل الـ 8)
    answers = [
        ('age', '58'),
        ('gender', 'male'),
        ('height_cm', '175'),
        ('weight_kg', '95'),
        ('smoking_status', 'current smoker'),
        ('workplace_type', 'factory'),
        ('environmental_hazards', 'dust, chemicals'),
        ('family_history', 'yes'),
    ]
    
    for field, value in answers:
        print(f"\n المستخدم: {field} = {value}")
        print("" * 70)
        
        # معالجة الإجابة
        response = chatbot.process_answer(field, value)
        
        # عرض النتائج
        print(f"\n الفكرة الداخلية:")
        print(f"   {response['internal_thought']['thought']}")
        
        print(f"\n الاستنتاج:")
        print(f"   {response['inference']['thought']}")
        
        print(f"\n الحالة الحالية:")
        print(f"   مستوى الخطر: {response['current_status']['risk_level']}")
        print(f"   ثقة: {response['current_status']['confidence_score']:.0%}")
        print(f"   {response['current_status']['facts_collected']}/{response['current_status']['total_facts']} معلومات")
        
        if response.get('warning') and response['warning']['triggered']:
            print(f"\n تحذير:")
            print(f"   {response['warning']['message']}")
        
        if response['next_question']:
            print(f"\n السؤال التالي:")
            print(f"   {response['next_question'].get('question', response['next_question'].get('message'))}")
    
    # التقييم النهائي
    print("\n" + "="*70)
    print(" التقييم النهائي")
    print("="*70 + "\n")
    
    assessment = chatbot.get_final_assessment()
    
    print(assessment.get('reasoning', ''))
    print("\n" + "="*70)
    print(" الجلسة انتهت بنجاح!")
    print("="*70 + "\n")
