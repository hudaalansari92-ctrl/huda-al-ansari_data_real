"""
Unit tests for the clinical assessment pipeline.

The project was migrated from an 11-field cardiac schema (Keras model) to an
8-field clinical base schema (sklearn GradientBoosting model). These tests
cover the new pipeline:

- engine.feature_deriver.derive / FEATURE_NAMES   (8 base -> 26 derived)
- engine.clinical_ml_predictor.clinical_ml_predictor
- engine.domain_pipeline.domain_pipeline
"""

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Shared fixtures — clinical 8-field base dicts
# ---------------------------------------------------------------------------

@pytest.fixture
def low_risk_base():
    """Low-risk clinical profile (8 base fields)."""
    return {
        'age': 30,
        'gender': 'female',
        'height_cm': 165,
        'weight_kg': 58,
        'smoking_status': 'non-smoker',
        'workplace_type': 'office',
        'environmental_hazards': [],
        'family_history': 'no',
    }


@pytest.fixture
def high_risk_base():
    """High-risk clinical profile (8 base fields)."""
    return {
        'age': 76,
        'gender': 'male',
        'height_cm': 170,
        'weight_kg': 95,
        'smoking_status': 'current smoker',
        'workplace_type': 'factory',
        'environmental_hazards': ['stress', 'pollution', 'dust',
                                  'chemicals', 'shift work'],
        'family_history': 'yes',
    }


VALID_RISK_LEVELS = {'LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'UNKNOWN'}


# ===================================================================
# 1. TestFeatureDeriver
# ===================================================================

class TestFeatureDeriver:

    def test_derive_returns_all_features(self, low_risk_base):
        """derive() should return exactly len(FEATURE_NAMES) == 26 keys."""
        from engine.feature_deriver import derive, FEATURE_NAMES
        feats = derive(low_risk_base)
        assert len(FEATURE_NAMES) == 26
        assert len(feats) == len(FEATURE_NAMES)

    def test_derive_keys_match_feature_names(self, high_risk_base):
        """Keys and order must equal FEATURE_NAMES exactly."""
        from engine.feature_deriver import derive, FEATURE_NAMES
        feats = derive(high_risk_base)
        assert list(feats.keys()) == FEATURE_NAMES

    def test_feature_names_match_models_json(self):
        """FEATURE_NAMES must match models/feature_names.json."""
        import json
        from engine.feature_deriver import FEATURE_NAMES
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'models', 'feature_names.json'
        )
        with open(path, encoding='utf-8') as f:
            saved = json.load(f)
        assert FEATURE_NAMES == saved

    def test_bmi_auto_derived(self):
        """bmi should be auto-derived from height + weight when absent."""
        from engine.feature_deriver import derive
        base = {
            'age': 40, 'gender': 'male', 'height_cm': 180, 'weight_kg': 81,
            'smoking_status': 'non-smoker', 'workplace_type': 'office',
            'environmental_hazards': [], 'family_history': 'no',
        }
        feats = derive(base)
        # 81 / 1.8^2 == 25.0
        assert feats['bmi'] == pytest.approx(25.0, abs=0.1)

    def test_gender_and_smoking_one_hot(self, high_risk_base):
        """One-hot encodings should reflect the base values."""
        from engine.feature_deriver import derive
        feats = derive(high_risk_base)
        assert feats['is_male'] == 1
        assert feats['is_female'] == 0
        assert feats['smoker_current'] == 1
        assert feats['smoker_never'] == 0
        assert feats['has_family_history'] == 1
        assert feats['work_factory'] == 1

    def test_hazard_flags(self, high_risk_base):
        """Environmental hazards list should map to hazard_* flags."""
        from engine.feature_deriver import derive
        feats = derive(high_risk_base)
        assert feats['hazard_stress'] == 1
        assert feats['hazard_pollution'] == 1
        assert feats['hazard_chemicals'] == 1
        assert feats['hazard_shift_work'] == 1
        assert feats['hazard_noise'] == 0


# ===================================================================
# 2. TestClinicalMLPredictor
# ===================================================================

class TestClinicalMLPredictor:

    def test_predict_from_base_returns_dict(self, low_risk_base):
        from engine.clinical_ml_predictor import clinical_ml_predictor
        result = clinical_ml_predictor.predict_from_base(low_risk_base)
        assert isinstance(result, dict)
        for key in ('probability', 'prediction', 'confidence',
                    'risk_level', 'source'):
            assert key in result, f"Missing key: {key}"

    def test_probability_range(self, high_risk_base):
        """Probability must be in [0, 1]."""
        from engine.clinical_ml_predictor import clinical_ml_predictor
        result = clinical_ml_predictor.predict_from_base(high_risk_base)
        prob = result['probability']
        assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"

    def test_risk_level_valid(self, high_risk_base):
        from engine.clinical_ml_predictor import clinical_ml_predictor
        result = clinical_ml_predictor.predict_from_base(high_risk_base)
        assert result['risk_level'] in VALID_RISK_LEVELS

    def test_prediction_values(self, low_risk_base):
        from engine.clinical_ml_predictor import clinical_ml_predictor
        result = clinical_ml_predictor.predict_from_base(low_risk_base)
        assert result['prediction'] in ('Positive', 'Negative', 'Unknown')

    def test_predict_from_features_matches_base(self, high_risk_base):
        """predict_from_features(derive(base)) == predict_from_base(base)."""
        from engine.feature_deriver import derive
        from engine.clinical_ml_predictor import clinical_ml_predictor
        feats = derive(high_risk_base)
        from_feats = clinical_ml_predictor.predict_from_features(feats)
        from_base = clinical_ml_predictor.predict_from_base(high_risk_base)
        assert from_feats['probability'] == pytest.approx(
            from_base['probability']
        )
        assert from_feats['risk_level'] == from_base['risk_level']

    def test_confidence_range(self, low_risk_base):
        from engine.clinical_ml_predictor import clinical_ml_predictor
        result = clinical_ml_predictor.predict_from_base(low_risk_base)
        assert 0.0 <= result['confidence'] <= 1.0


# ===================================================================
# 3. TestDomainPipeline
# ===================================================================

class TestDomainPipeline:

    def test_assess_returns_structure(self, low_risk_base):
        """assess() should return the documented top-level keys."""
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(low_risk_base)
        for key in ('derived_features', 'active_features', 'ml',
                    'rules', 'decision', 'decision_tree_path'):
            assert key in result, f"Missing key: {key}"

    def test_assess_final_risk_level_non_empty(self, high_risk_base):
        """decision.final_risk_level must be a non-empty string."""
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(high_risk_base)
        final = result['decision']['final_risk_level']
        assert isinstance(final, str)
        assert final != ''
        assert final in VALID_RISK_LEVELS

    def test_assess_derived_features_count(self, high_risk_base):
        """derived_features must have 26 entries matching FEATURE_NAMES."""
        from engine.feature_deriver import FEATURE_NAMES
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(high_risk_base)
        assert len(result['derived_features']) == len(FEATURE_NAMES)

    def test_assess_ml_probability_range(self, low_risk_base):
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(low_risk_base)
        prob = result['ml']['probability']
        assert 0.0 <= prob <= 1.0

    def test_assess_active_features_subset(self, high_risk_base):
        """active_features should be a subset of the derived feature keys."""
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(high_risk_base)
        active = result['active_features']
        assert isinstance(active, list)
        derived_keys = set(result['derived_features'].keys())
        assert set(active).issubset(derived_keys)

    def test_assess_rules_structure(self, high_risk_base):
        from engine.domain_pipeline import domain_pipeline
        result = domain_pipeline.assess(high_risk_base)
        rules = result['rules']
        assert 'triggered' in rules
        assert 'risk_level' in rules
        assert isinstance(rules['triggered'], list)


# ===================================================================
# 4. TestIntegration
# ===================================================================

class TestIntegration:

    def test_full_pipeline_both_profiles(self, low_risk_base, high_risk_base):
        """Both profiles should flow end-to-end through assess()."""
        from engine.domain_pipeline import domain_pipeline
        for base in (low_risk_base, high_risk_base):
            result = domain_pipeline.assess(base)
            assert 0.0 <= result['ml']['probability'] <= 1.0
            assert result['decision']['final_risk_level'] in VALID_RISK_LEVELS

    def test_pipeline_consistency(self, high_risk_base):
        """Running the same base twice should produce identical decisions."""
        from engine.domain_pipeline import domain_pipeline
        r1 = domain_pipeline.assess(high_risk_base)
        r2 = domain_pipeline.assess(high_risk_base)
        assert (r1['decision']['final_risk_level']
                == r2['decision']['final_risk_level'])
        assert r1['ml']['probability'] == pytest.approx(
            r2['ml']['probability']
        )


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-q']))
