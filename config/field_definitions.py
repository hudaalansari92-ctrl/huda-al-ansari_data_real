"""
تعريفات الحقول الطبية الموحدة
Unified Medical Field Definitions

هذا الملف هو المرجع الوحيد لأسماء الحقول في كل المشروع.
All modules MUST import field names from here — never hardcode them.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════
# ACC/AHA 2019 Cardiovascular Risk Stratification Thresholds
# Reference: Arnett DK et al., 2019 ACC/AHA Guideline on the Primary
# Prevention of Cardiovascular Disease. Circulation 2019;140(11):e596–e646.
# doi:10.1161/CIR.0000000000000678
# ═══════════════════════════════════════════════════════════════════════════
ACC_AHA_THRESHOLD_MODERATE = 0.05   # 5%   — borderline risk
ACC_AHA_THRESHOLD_HIGH = 0.075      # 7.5% — intermediate-to-high risk
ACC_AHA_THRESHOLD_CRITICAL = 0.20   # 20%  — very high / critical risk


# ═══════════════════════════════════════════════════════════════════════════
# مستويات الخطر الموحدة — تُستخدم في كل الموديولات
# ═══════════════════════════════════════════════════════════════════════════

class RiskLevel(Enum):
    """
    Cardiovascular risk stratification — unified across all system components.

    Thresholds follow the 2019 ACC/AHA Primary Prevention Guideline [1]
    and the 2018 AHA/ACC Cholesterol Management Guideline [2]:

        Low         : prob < 5%       → no/very low CVD risk
        Moderate    : 5%  ≤ prob < 7.5% → borderline risk
        High        : 7.5% ≤ prob < 20% → intermediate-to-high risk
        Critical    : prob ≥ 20%      → very high / established CVD risk

    References
    ----------
    [1] Arnett DK, Blumenthal RS, Albert MA, et al. 2019 ACC/AHA Guideline
        on the Primary Prevention of Cardiovascular Disease. Circulation.
        2019;140(11):e596–e646. doi:10.1161/CIR.0000000000000678
    [2] Grundy SM, Stone NJ, Bailey AL, et al. 2018 AHA/ACC Cholesterol
        Management Guideline. Circulation. 2019;139(25):e1082–e1143.
        doi:10.1161/CIR.0000000000000625
    """

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_probability(cls, prob: float) -> "RiskLevel":
        """Map a model probability to a clinical risk category per ACC/AHA 2019."""
        if prob >= ACC_AHA_THRESHOLD_CRITICAL:   # ≥20% → very high / critical
            return cls.CRITICAL
        elif prob >= ACC_AHA_THRESHOLD_HIGH:     # 7.5%–<20% → intermediate-to-high
            return cls.HIGH
        elif prob >= ACC_AHA_THRESHOLD_MODERATE: # 5%–<7.5% → borderline / moderate
            return cls.MODERATE
        return cls.LOW                           # <5% → low risk

    @classmethod
    def from_domain_label(cls, label: str) -> "RiskLevel":
        """تحويل من تسميات Domain Rules (Low/Medium/High) إلى RiskLevel"""
        mapping = {
            "low": cls.LOW,
            "medium": cls.MODERATE,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        return mapping.get(label.lower(), cls.LOW)

    def to_arabic(self) -> str:
        return {
            "LOW": "منخفض",
            "MODERATE": "متوسط",
            "HIGH": "عالي",
            "CRITICAL": "حرج",
        }[self.value]

    def to_numeric(self) -> float:
        """قيمة رقمية للمقارنات"""
        return {"LOW": 0.25, "MODERATE": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}[
            self.value
        ]


# ═══════════════════════════════════════════════════════════════════════════
# أسماء الحقول السريرية — المرجع الوحيد
# Clinical base fields — single source of truth.
#
# الاستراتيجية: 9 ميزات أصل (حوار) → derive() → 26 ميزة مهندَسة → النموذج.
# الأسماء هنا تطابق engine/feature_deriver.BASE_FIELDS بالضبط.
# ملاحظة: bmi يُحسب تلقائياً من الطول/الوزن، فلا يُسأل عنه مباشرةً في الحوار.
# ═══════════════════════════════════════════════════════════════════════════

# الميزات الأصل الـ 9 (تطابق feature_deriver.BASE_FIELDS)
BASE_FIELDS: List[str] = [
    "age",
    "gender",
    "height_cm",
    "weight_kg",
    "bmi",
    "smoking_status",
    "workplace_type",
    "environmental_hazards",
    "family_history",
]

# الحقول الـ 18 التي يجمعها الحوار (تطابق ميزات النموذج: 14 رقمية/سريرية
# + gender/smoking/workplace المرمّزة + family_history). severity مستثنى (مسرّب).
ASKED_FIELDS: List[str] = [
    "age",
    "gender",
    "height_cm",
    "weight_kg",
    "bmi",
    "smoking_status",
    "years_smoked",
    "years_since_quit",
    "workplace_type",
    "family_history",
    "hypertension",
    "diabetes",
    "cardiovascular_disease",
    "chronic_diseases",
    "obesity",
    "gestational_diabetes",
    "hba1c",
    "cholesterol",
]

# أسماء موحّدة عبر كل المشروع. لم نعد نملك طبقتين (داخلية/نموذج) لأن
# feature_deriver يستهلك أسماء الأصل مباشرةً، فالاسم الداخلي = اسم النموذج.
INTERNAL_FIELDS: List[str] = ASKED_FIELDS
MODEL_FIELDS: List[str] = BASE_FIELDS

# لم يعُد هناك إعادة تسمية بين الطبقتين — التحويل أصبح هوية (identity).
INTERNAL_TO_MODEL: Dict[str, str] = {f: f for f in BASE_FIELDS}

# القيم المسموحة للحقول التصنيفية (تطابق المنطق في feature_deriver.derive).
FIELD_OPTIONS: Dict[str, List[str]] = {
    "gender": ["male", "female"],
    "smoking_status": ["non-smoker", "ex-smoker", "current smoker"],
    "workplace_type": ["office", "factory"],
    "environmental_hazards": ["stress", "pollution", "noise", "dust",
                              "chemicals", "shift work"],
    "family_history": ["yes", "no"],
}

MODEL_TO_INTERNAL: Dict[str, str] = {v: k for k, v in INTERNAL_TO_MODEL.items()}


def to_model_name(internal_name: str) -> str:
    """تحويل اسم داخلي إلى اسم النموذج"""
    return INTERNAL_TO_MODEL.get(internal_name, internal_name)


def to_internal_name(model_name: str) -> str:
    """تحويل اسم النموذج إلى اسم داخلي"""
    return MODEL_TO_INTERNAL.get(model_name, model_name)


def convert_facts_to_model(facts: Dict) -> Dict:
    """تحويل facts dict من الأسماء الداخلية إلى أسماء النموذج"""
    return {INTERNAL_TO_MODEL.get(k, k): v for k, v in facts.items()}


def convert_facts_to_internal(facts: Dict) -> Dict:
    """تحويل facts dict من أسماء النموذج إلى الأسماء الداخلية"""
    return {MODEL_TO_INTERNAL.get(k, k): v for k, v in facts.items()}


# ═══════════════════════════════════════════════════════════════════════════
# الثوابت الطبية — مكان واحد لكل العتبات
# ═══════════════════════════════════════════════════════════════════════════

MEDICAL_THRESHOLDS = {
    # فئات العمر (تطابق age_young/middle/senior/elderly في feature_deriver)
    "age_young": 45,     # < 45  → young
    "age_middle": 60,    # 45–60 → middle
    "age_senior": 75,    # 60–75 → senior, ≥75 → elderly
    # فئات مؤشر كتلة الجسم BMI (WHO)
    "bmi_normal": 25.0,      # < 25     → normal
    "bmi_overweight": 30.0,  # 25–30    → overweight, ≥30 → obese
}

# ═══════════════════════════════════════════════════════════════════════════
# نطاقات القيم المقبولة (الحقول الرقمية الأصل)
# ═══════════════════════════════════════════════════════════════════════════

VALUE_RANGES: Dict[str, Tuple[float, float]] = {
    "age": (0, 150),
    "height_cm": (50, 250),
    "weight_kg": (20, 400),
    "bmi": (10, 80),
}


def validate_numeric_field(field_name: str, value) -> Optional[float]:
    """التحقق من القيمة الرقمية ضمن النطاق المقبول.
    يرجع القيمة إذا صحيحة، None إذا خارج النطاق أو غير رقمية.
    """
    if field_name not in VALUE_RANGES:
        return None
    try:
        num = float(value)
    except (ValueError, TypeError):
        return None
    lo, hi = VALUE_RANGES[field_name]
    if lo <= num <= hi:
        return num
    return None
