"""
Tests for the domain assessment pipeline:
base features -> derive (26) -> ML model -> rules -> fused decision + tree.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.feature_deriver import derive, FEATURE_NAMES
from engine.domain_pipeline import domain_pipeline

BASE = {"age": 72, "gender": "male", "height_cm": 170, "weight_kg": 95, "bmi": None,
        "smoking_status": "current smoker", "workplace_type": "factory",
        "environmental_hazards": ["stress", "pollution"], "family_history": True}


def test_derive_shapes():
    f = derive(BASE)
    assert len(f) == 26 and list(f.keys()) == FEATURE_NAMES
    assert f["age_senior"] == 1 and f["bmi_obese"] == 1 and f["smoker_current"] == 1
    assert f["is_male"] == 1 and f["hazard_stress"] == 1 and f["has_family_history"] == 1


def test_derive_handles_missing():
    f = derive({"age": None, "gender": "", "environmental_hazards": None})
    assert all(v == v for v in f.values())  # no NaN


def test_pipeline_structure():
    r = domain_pipeline.assess(BASE)
    for key in ("derived_features", "ml", "rules", "decision", "decision_tree_path"):
        assert key in r
    assert r["decision"]["final_risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert 0.0 <= r["ml"]["probability"] <= 1.0
    assert isinstance(r["rules"]["triggered"], list)


if __name__ == "__main__":
    test_derive_shapes()
    test_derive_handles_missing()
    test_pipeline_structure()
    print("All domain pipeline tests passed.")
