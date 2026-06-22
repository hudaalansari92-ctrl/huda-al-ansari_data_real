"""
Clinical ML predictor (Clinical_Final) — thin wrapper over the good clinical GB
model (engine.clinical_model.heart_model). Kept for backward-compatibility with
the chatbot, which calls `clinical_ml_predictor.predict_from_features(...)`.
"""
from engine.clinical_model import heart_model


def _wrap(r: dict) -> dict:
    p = r["probability"]
    return {
        "probability": p,
        "prediction": "Positive" if p > 0.5 else "Negative",
        "confidence": max(p, 1 - p),
        "risk_level": r["risk_level"],
        "source": "Clinical GB model",
    }


class _ClinicalMLPredictor:
    def predict_from_base(self, base: dict) -> dict:
        return _wrap(heart_model.predict(base or {}))

    # the chatbot passes the derived-feature row; heart_model re-reads the same keys
    def predict_from_features(self, feats: dict) -> dict:
        return _wrap(heart_model.predict(feats or {}))


clinical_ml_predictor = _ClinicalMLPredictor()
