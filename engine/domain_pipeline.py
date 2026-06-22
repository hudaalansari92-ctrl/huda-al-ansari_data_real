"""
Domain pipeline (Clinical_Final) — keeps the SAME interface the chatbot expects
(`derived_features`, `rules`, `ml`) but powered by the good clinical GB model.

    facts (collected by the chatbot)  ->  clinical model  ->  risk + factors
                                       ->  rules-style triggered factors.
"""
from engine.clinical_model import heart_model, RISK_LABELS

_CONTINUOUS = {"age", "height_cm", "weight_kg", "bmi", "hba1c", "cholesterol", "risk_probability"}


def _risk3(level: str) -> str:
    return {"CRITICAL": "High", "HIGH": "High", "MODERATE": "Medium", "LOW": "Low"}.get(level, "Low")


# مستوى الخطر (3 فئات) -> رمز العرض + الاسم العربي
_RISK3_UP = {"High": "HIGH", "Medium": "MEDIUM", "Low": "LOW"}
_RISK_AR = {"HIGH": "عالي", "MEDIUM": "متوسط", "LOW": "منخفض"}


class DomainPipeline:
    def assess(self, facts: dict) -> dict:
        ml = heart_model.predict(facts)
        prob, level = ml["probability"], ml["risk_level"]
        present = ml["present_factors"]
        row = ml["row"]

        derived = dict(row)
        derived["risk_probability"] = round(prob, 4)

        imp = dict(heart_model.importance)
        triggered = []
        for i, f in enumerate(present, 1):
            triggered.append({
                "rule_id": f"R{i}",
                "condition": f"{f}=1",
                "feature_name": f,
                "label_ar": RISK_LABELS.get(f, f),
                "confidence": round(0.5 + min(imp.get(f, 0.05) * 2, 0.49), 3),
                "lift": 1.0,
                "weight": round(imp.get(f, 0.02), 4),
            })
        triggered.sort(key=lambda r: r["weight"], reverse=True)

        risk3 = _risk3(level)
        risk3_up = _RISK3_UP.get(risk3, "LOW")
        factor_labels = [RISK_LABELS.get(f, f) for f in present]

        return {
            "status": "complete",
            "derived_features": derived,
            # هيكل insights الذي يتوقّعه عرض "القسم الأول: تحليل القواعد الطبية"
            "insights": {
                "risk_level": risk3_up,
                "risk_level_ar": _RISK_AR.get(risk3_up, "منخفض"),
                "triggered_rules_count": len(triggered),
                "risk_factors": factor_labels,
                "risk_factors_ar": factor_labels,
                "framingham_score": 0,
            },
            "rules": {"triggered": triggered, "risk_level": _risk3(level), "score": prob},
            "ml": {
                "probability": prob,
                "prediction": "Positive" if prob > 0.5 else "Negative",
                "confidence": max(prob, 1 - prob),
                "risk_level": level,
                "source": "Clinical GB model",
            },
            "present_factors": present,
            "factor_labels": [RISK_LABELS.get(f, f) for f in present],
        }


domain_pipeline = DomainPipeline()
