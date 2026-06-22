"""
Feature deriver: turn the user's BASE input fields (entered at session start)
into the 26 engineered DOMAIN features the model and rules consume.

Base input fields (adopted / essential):
    age, gender, height_cm, weight_kg, bmi, smoking_status,
    workplace_type, environmental_hazards (list), family_history (bool)

Derived domain features (26) — same order/columns as Data_real_domain.csv.
"""
import numpy as np

# Exact feature order the model + rules expect (matches Data_real_domain.csv).
FEATURE_NAMES = [
    "age_young", "age_middle", "age_senior", "age_elderly", "age_risk_score",
    "bmi_normal", "bmi_overweight", "bmi_obese",
    "is_male", "is_female",
    "smoker_current", "smoker_ex", "smoker_never",
    "has_family_history",
    "work_office", "work_factory",
    "hazard_stress", "hazard_pollution", "hazard_noise",
    "hazard_dust", "hazard_chemicals", "hazard_shift_work",
    "age", "bmi", "height_cm", "weight_kg",
]

# The base fields the UI collects.
BASE_FIELDS = ["age", "gender", "height_cm", "weight_kg", "bmi",
               "smoking_status", "workplace_type", "environmental_hazards",
               "family_history"]

HAZARD_OPTIONS = ["stress", "pollution", "noise", "dust", "chemicals", "shift work"]


def _num(v, default=0.0):
    """Parse to float, treating None / NaN / non-numeric as default."""
    try:
        v = float(v)
        return default if v != v else v  # NaN != NaN
    except (TypeError, ValueError):
        return default


def derive(base: dict) -> dict:
    """Derive the 26 domain features from the base input dict."""
    d = {}
    age = _num(base.get("age"))
    bmi = _num(base.get("bmi"))
    height = _num(base.get("height_cm"))
    weight = _num(base.get("weight_kg"))
    if not bmi and height and weight:
        bmi = weight / ((height / 100.0) ** 2)

    # Age categories
    d["age_young"] = int(age < 45)
    d["age_middle"] = int(45 <= age < 60)
    d["age_senior"] = int(60 <= age < 75)
    d["age_elderly"] = int(age >= 75)
    d["age_risk_score"] = int(np.where(age < 45, 0, np.where(age < 55, 1, np.where(age < 65, 2, 3))))

    # BMI categories
    d["bmi_normal"] = int(bmi < 25)
    d["bmi_overweight"] = int(25 <= bmi < 30)
    d["bmi_obese"] = int(bmi >= 30)

    # Gender
    g = str(base.get("gender", "")).lower()
    d["is_male"] = int(g == "male")
    d["is_female"] = int(g == "female")

    # Smoking
    s = str(base.get("smoking_status", "")).lower()
    d["smoker_current"] = int(s == "current smoker")
    d["smoker_ex"] = int(s == "ex-smoker")
    d["smoker_never"] = int(s == "non-smoker")

    # Family history (truthy = present)
    fh = base.get("family_history")
    d["has_family_history"] = int(bool(fh) and str(fh).lower() not in ("", "no", "none", "0", "false"))

    # Workplace
    w = str(base.get("workplace_type", "")).lower()
    d["work_office"] = int(w == "office")
    d["work_factory"] = int(w == "factory")

    # Environmental hazards (list, comma/; string, or missing/NaN)
    hz = base.get("environmental_hazards", [])
    if isinstance(hz, str):
        hz = [h.strip() for h in hz.replace(";", ",").split(",")]
    elif not isinstance(hz, (list, tuple)):
        hz = []  # NaN / None / float
    hz = [str(h).lower() for h in hz]
    d["hazard_stress"] = int(any("stress" in h for h in hz))
    d["hazard_pollution"] = int(any("pollution" in h for h in hz))
    d["hazard_noise"] = int(any("noise" in h for h in hz))
    d["hazard_dust"] = int(any("dust" in h for h in hz))
    d["hazard_chemicals"] = int(any("chemical" in h for h in hz))
    d["hazard_shift_work"] = int(any("shift" in h for h in hz))

    # Continuous raw
    d["age"] = age
    d["bmi"] = round(bmi, 1)
    d["height_cm"] = height
    d["weight_kg"] = weight

    return {k: d[k] for k in FEATURE_NAMES}
