"""
Clinical model for Clinical_02 — GradientBoosting on the clinical risk factors.

Chosen over the Keras ensemble (which overfit the small synthetic data and did
not respond to risk factors): GB generalizes to novel patients and weights the
clinical features sensibly (cholesterol, cardiovascular_disease, age, HbA1c...).

14 model features (12 clinical/numeric + smoking score + family history),
trained on data/Data_real_train.csv at load time.
"""
import os
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_CSV = os.path.join(HERE, "..", "data", "Data_real_train.csv")

# 14 numeric/clinical base features (severity intentionally excluded — leaky)
NUM_FEATURES = ["age", "height_cm", "weight_kg", "bmi",
                "years_smoked", "years_since_quit",
                "hba1c", "cholesterol",
                "hypertension", "diabetes", "cardiovascular_disease",
                "chronic_diseases", "obesity", "gestational_diabetes"]
_SMOKE = {"non-smoker": 0, "ex-smoker": 1, "current smoker": 2}
_WORK = {"office": 0, "factory": 1}
# Human-readable labels for the decision-tree / factor display
RISK_LABELS = {
    "cholesterol": "ارتفاع الكوليسترول", "cardiovascular_disease": "أمراض القلب والأوعية",
    "hba1c": "السكر التراكمي", "diabetes": "السكري", "hypertension": "ارتفاع الضغط",
    "chronic_diseases": "أمراض مزمنة", "obesity": "السمنة", "age": "العمر",
    "smoker_score": "التدخين", "has_family_history": "تاريخ عائلي",
    "gestational_diabetes": "سكري الحمل", "bmi": "كتلة الجسم",
}


def _haz(v):
    if isinstance(v, (list, tuple)):
        return "; ".join(str(x) for x in v) if v else None
    return v or None


def _yn(v) -> int:
    """Interpret yes/no/true/1/Arabic etc. as 1, and no/false/0/empty as 0."""
    if isinstance(v, bool):
        return int(v)
    if v in (None, "", 0, "0"):
        return 0
    return 0 if str(v).strip().lower() in ("no", "false", "none", "لا", "كلا", "non") else 1


class HeartModel:
    # 18 base features = 14 numeric/clinical + 3 encoded + has_family_history
    FEATURES = NUM_FEATURES + ["gender_encoded", "smoking_encoded",
                               "workplace_encoded", "has_family_history"]

    def __init__(self):
        df = pd.read_csv(TRAIN_CSV)
        X = self._frame(df)
        self.median = X.median()
        y = (df["ThalassemiaStatus"].str.lower() == "abnormal").astype(int)
        self.model = GradientBoostingClassifier(random_state=42).fit(X.fillna(self.median), y)
        self.importance = dict(zip(self.FEATURES, self.model.feature_importances_))

    def _frame(self, df):
        def col(name):
            return df[name].astype(str).str.lower() if name in df else pd.Series("", index=df.index)
        d = pd.DataFrame(index=df.index)
        for c in NUM_FEATURES:
            d[c] = pd.to_numeric(df.get(c), errors="coerce")
        d["gender_encoded"] = col("gender").map({"male": 1, "female": 0})
        d["smoking_encoded"] = col("smoking_status").map(_SMOKE)
        d["workplace_encoded"] = col("workplace_type").map(_WORK)
        d["has_family_history"] = df["family_history"].notna().astype(int) if "family_history" in df else 0
        return d[self.FEATURES]

    @staticmethod
    def _level(p):
        if p >= 0.8:
            return "CRITICAL"
        if p >= 0.6:
            return "HIGH"
        if p >= 0.4:
            return "MODERATE"
        return "LOW"

    def build_row(self, base: dict) -> dict:
        h, w, bmi = base.get("height_cm"), base.get("weight_kg"), base.get("bmi")
        if not bmi and h and w:
            bmi = round(float(w) / ((float(h) / 100.0) ** 2), 1)
        def n(v, d):
            try:
                return float(str(v).split()[0]) if v not in (None, "") else d
            except (ValueError, TypeError):
                return d
        return {
            "age": base.get("age"), "height_cm": h, "weight_kg": w, "bmi": bmi,
            "gender": base.get("gender"),
            "smoking_status": base.get("smoking_status"),
            "workplace_type": base.get("workplace_type"),
            "years_smoked": n(base.get("years_smoked"), 0),
            "years_since_quit": n(base.get("years_since_quit"), 0),
            "family_history": "yes" if _yn(base.get("family_history")) else None,
            "hypertension": _yn(base.get("hypertension")),
            "diabetes": _yn(base.get("diabetes")),
            "cardiovascular_disease": _yn(base.get("cardiovascular_disease")),
            "chronic_diseases": _yn(base.get("chronic_diseases")),
            "hba1c": n(base.get("hba1c"), 5.4),
            "cholesterol": n(base.get("cholesterol"), 190),
            "obesity": int((bmi or 0) >= 30),
            "gestational_diabetes": _yn(base.get("gestational_diabetes")),
        }

    def predict(self, base: dict) -> dict:
        row = self.build_row(base)
        d = self._frame(pd.DataFrame([row])).fillna(self.median)
        prob = float(self.model.predict_proba(d)[0][1])
        # active risk factors present in this patient (for the decision tree)
        present = []
        for f in ["cardiovascular_disease", "diabetes", "hypertension", "chronic_diseases",
                  "obesity", "gestational_diabetes"]:
            if row.get(f):
                present.append(f)
        if row["cholesterol"] >= 240:
            present.append("cholesterol")
        if row["hba1c"] >= 6.5:
            present.append("hba1c")
        if (row["age"] or 0) >= 60:
            present.append("age")
        if row["smoking_status"] in ("current smoker", "ex-smoker"):
            present.append("smoker_score")
        if row["family_history"]:
            present.append("has_family_history")
        return {"probability": prob, "risk_level": self._level(prob),
                "row": row, "present_factors": present}

    def top_importance(self, k=6):
        return sorted(self.importance.items(), key=lambda x: -x[1])[:k]


heart_model = HeartModel()
