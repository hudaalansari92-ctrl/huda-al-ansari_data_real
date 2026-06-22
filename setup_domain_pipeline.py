"""
Set up the Data_real DOMAIN pipeline for this system:
  1. Convert the Step6 Data_real domain rules -> app condition format -> domain_rules.json
  2. Copy the derived-features dataset into data/
  3. Train the model on the 26 derived domain features (80/20) -> models/
"""
import os, re, json, pickle, shutil
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix

from engine.feature_deriver import FEATURE_NAMES, derive

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..")
RULES_SRC = os.path.join(PROJ, "domain_outputs_real", "domain_report.json")
DATA_SRC = os.path.join(PROJ, "Data", "Data_real_domain.csv")
DATA_DST = os.path.join(HERE, "data", "domain_features.csv")
MODELS = os.path.join(HERE, "models")
os.makedirs(MODELS, exist_ok=True)


def convert_condition(desc, ftype):
    desc = desc.strip()
    if ftype == "continuous" or ">" in desc or "<" in desc:
        return None
    if ftype == "not" or desc.upper().startswith("NOT "):
        m = re.match(r"NOT\s+(\w+)", desc, re.I)
        return f"{m.group(1)}=0" if m else None
    return re.sub(r"\s*=\s*", "=", desc)


# 1) rules
rep = json.load(open(RULES_SRC, encoding="utf-8"))
out_rules, dropped = [], 0
for r in rep["rules"]:
    c = convert_condition(r["condition"], r.get("feature_type", "binary"))
    if c is None:
        dropped += 1
        continue
    out_rules.append({"rule_id": r["rule_id"], "condition": c,
                      "feature_name": r.get("feature_name", ""),
                      "feature_type": r.get("feature_type", "binary"),
                      "confidence": r.get("confidence", 0), "lift": r.get("lift", 0),
                      "weight": r.get("weight", 0)})
json.dump({"timestamp": rep.get("timestamp", ""),
           "model_type": "Data_real Domain Inference Engine",
           "model_configuration": {"optimal_threshold": rep["model_configuration"]["optimal_threshold"],
                                   "total_rules": len(out_rules),
                                   "binary_features": rep["model_configuration"]["binary_features"],
                                   "continuous_features": rep["model_configuration"]["continuous_features"]},
           "performance": rep.get("performance", {}), "rules": out_rules},
          open(os.path.join(HERE, "domain_rules.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)
print(f"Rules: converted {len(out_rules)} (dropped {dropped} continuous) -> domain_rules.json")

# 2) data — derive domain features from the ORIGINAL 87 rows (leakage-free)
orig = pd.read_csv(os.path.join(PROJ, "Data", "Data_real.csv"), sep=";")
rows = []
for _, r in orig.iterrows():
    base = {"age": r.get("age"), "gender": r.get("gender"), "height_cm": r.get("height_cm"),
            "weight_kg": r.get("weight_kg"), "bmi": r.get("bmi"), "smoking_status": r.get("smoking_status"),
            "workplace_type": r.get("workplace_type"), "environmental_hazards": r.get("environmental_hazards"),
            "family_history": r.get("family_history") if pd.notna(r.get("family_history")) else False}
    feats = derive(base)
    feats["high_risk"] = int(str(r.get("ThalassemiaStatus")).lower() == "abnormal")
    rows.append(feats)
df = pd.DataFrame(rows)
df.to_csv(DATA_DST, index=False)
print(f"Data: derived {df.shape} from 87 originals -> data/domain_features.csv")

# 3) model — split FIRST (test stays real), oversample TRAIN only
X = df[FEATURE_NAMES]
y = df["high_risk"].astype(int)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
tr = pd.concat([Xtr, ytr], axis=1)
pos, neg = tr[tr.high_risk == 1], tr[tr.high_risk == 0]
N = 240
npos = round(N * len(pos) / len(tr)); nneg = N - npos
tr_os = pd.concat([pos.sample(npos, replace=True, random_state=42),
                   neg.sample(nneg, replace=True, random_state=42)])
model = GradientBoostingClassifier(random_state=42)
model.fit(tr_os[FEATURE_NAMES], tr_os["high_risk"])
proba = model.predict_proba(Xte)[:, 1]
pred = (proba > 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(yte, pred, labels=[0, 1]).ravel()
metrics = {"accuracy": accuracy_score(yte, pred), "f1": f1_score(yte, pred, zero_division=0),
           "auc_roc": roc_auc_score(yte, proba) if len(set(yte)) > 1 else 0.0,
           "n_test": int(len(yte))}

pickle.dump(model, open(os.path.join(MODELS, "clinical_model.pkl"), "wb"))
json.dump(FEATURE_NAMES, open(os.path.join(MODELS, "feature_names.json"), "w"), indent=2)
json.dump({"model_name": "domain_gradient_boosting", "model_type": "sklearn",
           "timestamp": datetime.now().isoformat(), "num_features": len(FEATURE_NAMES),
           "n_train": int(len(Xtr)), "n_test": int(len(Xte)), "test_metrics": metrics,
           "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}},
          open(os.path.join(MODELS, "metadata.json"), "w"), indent=2)
print(f"Model: trained on {len(FEATURE_NAMES)} features. TEST:",
      {k: round(v, 3) for k, v in metrics.items()})
