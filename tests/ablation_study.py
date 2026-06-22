"""
Ablation Study — دراسة إزالة المكونات (Clinical schema)

The project migrated from an 11-field cardiac schema to an 8-field clinical
base schema. Inputs are now derived into the 26 engineered domain features
(engine.feature_deriver.FEATURE_NAMES) and scored by a sklearn model.

This ablation removes one feature group per experiment to measure each
group's contribution, using 5-fold stratified cross-validation on the
labelled domain feature dataset (data/domain_features.csv, label = high_risk).

Usage:
    python tests/ablation_study.py
"""

import sys
import os
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.feature_deriver import FEATURE_NAMES, derive  # noqa: E402

logging.basicConfig(level=logging.WARNING)
warnings.filterwarnings('ignore')

LABEL_COL = 'high_risk'


# ═══════════════════════════════════════════════════════
#  تحميل البيانات (26 derived features + label)
# ═══════════════════════════════════════════════════════

def load_domain_data() -> pd.DataFrame:
    """تحميل بيانات الميزات المشتقّة (26 feature + high_risk)."""
    local_path = Path(__file__).parent.parent / 'data' / 'domain_features.csv'
    if local_path.exists():
        print(f"[+] Loading derived features from {local_path}")
        return pd.read_csv(local_path)

    print("[!] domain_features.csv not found. Generating synthetic dataset...")
    return generate_synthetic_data()


def generate_synthetic_data(n_high=63, n_low=24) -> pd.DataFrame:
    """
    توليد بيانات اصطناعية: 8 حقول أساسية -> derive() -> 26 ميزة + label.
    Mirrors the clinical base schema, not the old cardiac one.
    """
    rng = np.random.default_rng(42)
    rows = []

    def make(label):
        if label == 1:  # high risk
            base = {
                'age': int(rng.integers(58, 82)),
                'gender': rng.choice(['male', 'female'], p=[0.7, 0.3]),
                'height_cm': float(rng.integers(160, 185)),
                'weight_kg': float(rng.integers(85, 115)),
                'smoking_status': rng.choice(
                    ['current smoker', 'ex-smoker', 'non-smoker'],
                    p=[0.6, 0.25, 0.15]),
                'workplace_type': rng.choice(['factory', 'office'], p=[0.65, 0.35]),
                'environmental_hazards': list(rng.choice(
                    ['stress', 'pollution', 'noise', 'dust', 'chemicals', 'shift work'],
                    size=int(rng.integers(2, 5)), replace=False)),
                'family_history': rng.choice(['yes', 'no'], p=[0.6, 0.4]),
            }
        else:  # low risk
            base = {
                'age': int(rng.integers(22, 50)),
                'gender': rng.choice(['male', 'female'], p=[0.5, 0.5]),
                'height_cm': float(rng.integers(160, 185)),
                'weight_kg': float(rng.integers(55, 80)),
                'smoking_status': rng.choice(
                    ['current smoker', 'ex-smoker', 'non-smoker'],
                    p=[0.1, 0.2, 0.7]),
                'workplace_type': rng.choice(['factory', 'office'], p=[0.3, 0.7]),
                'environmental_hazards': list(rng.choice(
                    ['stress', 'pollution', 'noise', 'dust', 'chemicals', 'shift work'],
                    size=int(rng.integers(0, 2)), replace=False)),
                'family_history': rng.choice(['yes', 'no'], p=[0.2, 0.8]),
            }
        feats = derive(base)
        feats[LABEL_COL] = label
        return feats

    for _ in range(n_high):
        rows.append(make(1))
    for _ in range(n_low):
        rows.append(make(0))

    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


# ═══════════════════════════════════════════════════════
#  أدوات مساعدة
# ═══════════════════════════════════════════════════════

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    """حساب مقاييس الأداء."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    balanced_acc = (recall + specificity) / 2

    return {
        'accuracy': round(accuracy * 100, 2),
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1_score': round(f1 * 100, 2),
        'specificity': round(specificity * 100, 2),
        'balanced_accuracy': round(balanced_acc * 100, 2),
    }


def _train_rf():
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_split=4,
        min_samples_leaf=2, random_state=42, n_jobs=-1
    )


def calculate_metrics_cv(df: pd.DataFrame, feature_cols: List[str],
                         n_folds=5) -> Dict:
    """
    تدريب RandomForest على feature_cols فقط وتقييمه بـ Stratified K-Fold.
    إزالة مجموعة ميزات = تمرير قائمة أعمدة أصغر.
    """
    from sklearn.model_selection import StratifiedKFold

    X_all = df[feature_cols].fillna(0).values
    y_all = df[LABEL_COL].values
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    fold_metrics = []
    for train_idx, test_idx in skf.split(X_all, y_all):
        model = _train_rf()
        model.fit(X_all[train_idx], y_all[train_idx])
        y_pred = model.predict(X_all[test_idx])
        fold_metrics.append(calculate_metrics(y_all[test_idx], y_pred))

    avg = {}
    for key in fold_metrics[0]:
        values = [m[key] for m in fold_metrics]
        avg[key] = round(float(np.mean(values)), 2)
        avg[f'{key}_std'] = round(float(np.std(values)), 2)
    avg['fold_details'] = fold_metrics
    return avg


# ═══════════════════════════════════════════════════════
#  مجموعات الميزات (لإزالتها في التجارب)
# ═══════════════════════════════════════════════════════

HAZARD_COLS = [c for c in FEATURE_NAMES if c.startswith('hazard_')]
SMOKING_COLS = [c for c in FEATURE_NAMES if c.startswith('smoker_')]
BMI_COLS = [c for c in FEATURE_NAMES if c.startswith('bmi') or c == 'weight_kg' or c == 'height_cm']
DEMOGRAPHIC_COLS = ['age', 'age_risk_score', 'is_male', 'is_female', 'bmi']


def _without(cols):
    return [c for c in FEATURE_NAMES if c not in cols]


# ═══════════════════════════════════════════════════════
#  تجارب Ablation (مع Cross-Validation)
# ═══════════════════════════════════════════════════════

def experiment_full_system(df, n_folds=5) -> Dict:
    """تجربة 1: النظام الكامل — كل الـ26 ميزة مشتقّة (Baseline)."""
    return calculate_metrics_cv(df, list(FEATURE_NAMES), n_folds)


def experiment_no_hazards(df, n_folds=5) -> Dict:
    """تجربة 2: بدون ميزات المخاطر البيئية (hazard_*)."""
    return calculate_metrics_cv(df, _without(HAZARD_COLS), n_folds)


def experiment_no_smoking(df, n_folds=5) -> Dict:
    """تجربة 3: بدون ميزات التدخين (smoker_*)."""
    return calculate_metrics_cv(df, _without(SMOKING_COLS), n_folds)


def experiment_no_bmi(df, n_folds=5) -> Dict:
    """تجربة 4: بدون ميزات الـ BMI / القياسات الجسدية."""
    return calculate_metrics_cv(df, _without(BMI_COLS), n_folds)


def experiment_demographics_only(df, n_folds=5) -> Dict:
    """تجربة 5: الخصائص الديموغرافية فقط (العمر، الجنس، BMI)."""
    return calculate_metrics_cv(df, DEMOGRAPHIC_COLS, n_folds)


def experiment_simple_rules(df, n_folds=5) -> Dict:
    """
    تجربة 6: قواعد IF/ELSE بسيطة (Chatbot العادي) — بدون ML.
    Score مبني على الميزات المشتقّة الأساسية.
    """
    from sklearn.model_selection import StratifiedKFold

    y_all = df[LABEL_COL].values
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    def rule_predict(sub: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in sub.iterrows():
            score = 0
            if row.get('age', 0) >= 55:
                score += 1
            if row.get('bmi_obese', 0) == 1 or row.get('bmi_overweight', 0) == 1:
                score += 1
            if row.get('smoker_current', 0) == 1:
                score += 1
            if row.get('has_family_history', 0) == 1:
                score += 1
            if sum(row.get(h, 0) for h in HAZARD_COLS) >= 2:
                score += 1
            preds.append(1 if score >= 3 else 0)
        return np.array(preds)

    fold_metrics = []
    for _, test_idx in skf.split(df, y_all):
        sub = df.iloc[test_idx]
        y_pred = rule_predict(sub)
        fold_metrics.append(calculate_metrics(y_all[test_idx], y_pred))

    avg = {}
    for key in fold_metrics[0]:
        values = [m[key] for m in fold_metrics]
        avg[key] = round(float(np.mean(values)), 2)
        avg[f'{key}_std'] = round(float(np.std(values)), 2)
    avg['fold_details'] = fold_metrics
    return avg


# ═══════════════════════════════════════════════════════
#  التنفيذ الرئيسي
# ═══════════════════════════════════════════════════════

def run_ablation_study():
    """تنفيذ Ablation Study الكامل مع 5-Fold Cross-Validation."""

    print("=" * 70)
    print("  Ablation Study — دراسة إزالة المكونات")
    print("  Clinical Risk Assessment System (8-field base -> 26 features)")
    print("  Method: 5-Fold Stratified Cross-Validation")
    print("=" * 70)

    df = load_domain_data()

    if LABEL_COL not in df.columns:
        print(f"[!] ERROR: No '{LABEL_COL}' label column found!")
        return

    # تأكّد من توفّر كل أعمدة الميزات
    for col in FEATURE_NAMES:
        if col not in df.columns:
            df[col] = 0

    y_true = df[LABEL_COL].values
    print(f"\n[+] Dataset: {len(df)} records, {len(FEATURE_NAMES)} derived features")
    print(f"    High risk: {int(sum(y_true))} ({sum(y_true)/len(y_true)*100:.1f}%)")
    print(f"    Low risk:  {len(y_true) - int(sum(y_true))} "
          f"({(len(y_true)-sum(y_true))/len(y_true)*100:.1f}%)")

    experiments = [
        ("1. Full System (Baseline)", "النظام الكامل", experiment_full_system),
        ("2. Without Hazard Features", "بدون المخاطر البيئية", experiment_no_hazards),
        ("3. Without Smoking Features", "بدون ميزات التدخين", experiment_no_smoking),
        ("4. Without BMI/Body Features", "بدون مؤشر الكتلة", experiment_no_bmi),
        ("5. Demographics Only", "الديموغرافيا فقط", experiment_demographics_only),
        ("6. Simple IF/ELSE (Traditional)", "قواعد بسيطة (تقليدي)", experiment_simple_rules),
    ]

    results = []
    baseline_acc = None

    print(f"\n{'='*70}")
    print(f"  {'Experiment':<35} {'Accuracy':>10} {'F1-Score':>10} {'Drop':>10}")
    print(f"{'='*70}")

    for name, name_ar, func in experiments:
        try:
            print(f"\n[*] Running: {name}...")
            metrics = func(df, n_folds=5)

            if baseline_acc is None:
                baseline_acc = metrics['accuracy']
                drop = 0
            else:
                drop = round(baseline_acc - metrics['accuracy'], 2)

            results.append({
                'experiment': name,
                'experiment_ar': name_ar,
                'metrics': metrics,
                'drop': drop,
            })

            drop_str = "—" if drop == 0 else f"-{drop:.2f}%"
            print(f"  {name:<35} {metrics['accuracy']:>8.2f}% "
                  f"{metrics['f1_score']:>9.2f}% {drop_str:>10}")

        except Exception as e:
            print(f"  [!] ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'experiment': name,
                'experiment_ar': name_ar,
                'metrics': {'accuracy': 0, 'f1_score': 0, 'precision': 0,
                            'recall': 0, 'specificity': 0, 'balanced_accuracy': 0},
                'drop': baseline_acc or 0,
            })

    # ═══════ النتائج التفصيلية ═══════
    print(f"\n{'='*70}")
    print("  DETAILED RESULTS (5-Fold CV Average ± Std)")
    print(f"{'='*70}")

    for r in results:
        m = r['metrics']
        print(f"\n  {r['experiment']}")
        print(f"    Accuracy:    {m['accuracy']:.2f}% ± {m.get('accuracy_std', 0):.2f}%")
        print(f"    F1-Score:    {m['f1_score']:.2f}% ± {m.get('f1_score_std', 0):.2f}%")
        print(f"    Precision:   {m['precision']:.2f}% ± {m.get('precision_std', 0):.2f}%")
        print(f"    Recall:      {m['recall']:.2f}% ± {m.get('recall_std', 0):.2f}%")
        print(f"    Specificity: {m['specificity']:.2f}% ± {m.get('specificity_std', 0):.2f}%")
        if r['drop'] > 0:
            print(f"    Drop:        -{r['drop']:.2f}%")

    # ═══════ حفظ النتائج ═══════
    output = {
        'dataset': {
            'total_records': len(df),
            'num_features': len(FEATURE_NAMES),
            'high_risk': int(sum(y_true)),
            'low_risk': int(len(y_true) - sum(y_true)),
        },
        'method': '5-Fold Stratified Cross-Validation',
        'experiments': []
    }

    for r in results:
        m = r['metrics']
        exp_data = {
            'name': r['experiment'],
            'name_ar': r['experiment_ar'],
            'accuracy': m['accuracy'],
            'accuracy_std': m.get('accuracy_std', 0),
            'f1_score': m['f1_score'],
            'f1_score_std': m.get('f1_score_std', 0),
            'precision': m['precision'],
            'precision_std': m.get('precision_std', 0),
            'recall': m['recall'],
            'recall_std': m.get('recall_std', 0),
            'specificity': m['specificity'],
            'specificity_std': m.get('specificity_std', 0),
            'drop_from_baseline': r['drop'],
        }
        if 'fold_details' in m:
            exp_data['fold_details'] = m['fold_details']
        output['experiments'].append(exp_data)

    output_path = Path(__file__).parent / 'ablation_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Results saved to: {output_path}")

    # ═══════ مساهمة كل مكوّن ═══════
    print(f"\n{'='*70}")
    print("  COMPONENT CONTRIBUTION (sorted by impact)")
    print(f"{'='*70}")

    contributions = [(r['experiment'], r['drop']) for r in results if r['drop'] > 0]
    contributions.sort(key=lambda x: x[1], reverse=True)

    for name, drop in contributions:
        bar = '#' * int(drop)
        print(f"  {name:<35} -{drop:.2f}% {bar}")

    if not contributions:
        print("  (No positive drops — baseline may need more data)")

    print(f"\n{'='*70}")
    print("  CONCLUSION")
    print(f"{'='*70}")
    if baseline_acc and results:
        simple_acc = results[-1]['metrics']['accuracy']
        improvement = baseline_acc - simple_acc
        print(f"  Full system accuracy:      {baseline_acc:.2f}%")
        print(f"  Simple rules accuracy:     {simple_acc:.2f}%")
        print(f"  Improvement over simple:   +{improvement:.2f}%")
        if contributions:
            top = contributions[0]
            print(f"  Most impactful component:  {top[0]} (-{top[1]:.2f}% when removed)")

    return output


if __name__ == '__main__':
    run_ablation_study()
