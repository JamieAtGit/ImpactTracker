"""
ablation.py
===========
Feature ablation study for ImpactTracker XGBoost model.

Measures how much accuracy drops when each feature (or feature group) is
zeroed out on the raw (unbalanced) test set, reflecting real-world distribution.

Usage:
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/ablation.py

Output:
  ml/ablation_results.json
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
BASE_CSV = os.path.join(BASE, "..", "common", "data", "csv", "expanded_eco_dataset.csv")
ENC_DIR  = os.path.join(BASE, "xgb_encoders")
MODEL    = os.path.join(BASE, "xgb_model.json")
OUT      = os.path.join(BASE, "ablation_results.json")

GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]

FEATURE_NAMES = [
    "Material Type",
    "Transport Mode",
    "Recyclability",
    "Origin Country",
    "Weight (log)",
    "Weight (bin)",
    "Material × Transport",
    "Origin × Recyclability",
]

# ── DEFRA thresholds ───────────────────────────────────────────────────────────
def co2_to_grade(co2: float) -> str:
    if co2 <= 0.05: return "A+"
    if co2 <= 0.15: return "A"
    if co2 <= 0.40: return "B"
    if co2 <= 1.00: return "C"
    if co2 <= 2.50: return "D"
    if co2 <= 5.00: return "E"
    return "F"

# ── Load encoders ──────────────────────────────────────────────────────────────
print("Loading encoders...")
le_mat = joblib.load(os.path.join(ENC_DIR, "material_encoder.pkl"))
le_trn = joblib.load(os.path.join(ENC_DIR, "transport_encoder.pkl"))
le_rec = joblib.load(os.path.join(ENC_DIR, "recyclability_encoder.pkl"))
le_ori = joblib.load(os.path.join(ENC_DIR, "origin_encoder.pkl"))
le_lbl = joblib.load(os.path.join(ENC_DIR, "label_encoder.pkl"))

# ── Load model ─────────────────────────────────────────────────────────────────
print("Loading model...")
model = xgb.XGBClassifier()
model.load_model(MODEL)

# ── Load dataset ───────────────────────────────────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(BASE_CSV)
required = ["material", "transport", "recyclability", "origin", "weight", "co2_emissions"]
df = df.dropna(subset=required)
for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.strip().str.title()
df["weight"]        = pd.to_numeric(df["weight"],        errors="coerce")
df["co2_emissions"] = pd.to_numeric(df["co2_emissions"], errors="coerce")
df = df.dropna(subset=["weight", "co2_emissions"])
df = df[df["weight"] > 0]

# Re-derive labels using DEFRA thresholds
df["true_eco_score"] = df["co2_emissions"].apply(co2_to_grade)
df = df[df["true_eco_score"].isin(GRADE_ORDER)]

print(f"Dataset size: {len(df):,} rows")

# ── Helper: safe encode ────────────────────────────────────────────────────────
def safe_enc(enc, val):
    try:    return int(enc.transform([val])[0])
    except: return 0

# ── Build feature matrix ───────────────────────────────────────────────────────
def build_features(df_in):
    rows = []
    for _, r in df_in.iterrows():
        mat = safe_enc(le_mat, r["material"])
        trn = safe_enc(le_trn, r["transport"])
        rec = safe_enc(le_rec, r["recyclability"])
        ori = safe_enc(le_ori, r["origin"])
        w   = float(r["weight"])
        wl  = float(np.log1p(max(w, 0)))
        wb  = float(0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3)
        rows.append([mat, trn, rec, ori, wl, wb, float(mat) * float(trn), float(ori) * float(rec)])
    return np.array(rows)

print("Building feature matrix...")
X = build_features(df)

# Encode labels — handle unseen labels gracefully
known_classes = set(le_lbl.classes_)
mask = df["true_eco_score"].isin(known_classes)
X = X[mask.values]
y_raw = df["true_eco_score"].values[mask.values]
y = le_lbl.transform(y_raw)

print(f"Feature matrix shape: {X.shape}")

# ── Raw (unbalanced) test split ────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"Test set size: {len(X_test):,}")

# ── Baseline accuracy ──────────────────────────────────────────────────────────
y_pred_baseline = model.predict(X_test)
baseline_acc = float(accuracy_score(y_test, y_pred_baseline))
print(f"Baseline accuracy: {baseline_acc:.4f}")

# ── Ablation function ──────────────────────────────────────────────────────────
def ablate(indices):
    X_abl = X_test.copy()
    for idx in indices:
        X_abl[:, idx] = 0
    y_pred = model.predict(X_abl)
    return float(accuracy_score(y_test, y_pred))

# ── Individual feature ablation ────────────────────────────────────────────────
print("\nRunning individual feature ablation...")
features = []
for i, name in enumerate(FEATURE_NAMES):
    abl_acc = ablate([i])
    drop = round(baseline_acc - abl_acc, 4)
    features.append({
        "name":             name,
        "index":            i,
        "accuracy_drop":    drop,
        "ablated_accuracy": round(abl_acc, 4),
    })
    print(f"  [{i}] {name:30s}: ablated={abl_acc:.4f}  drop={drop:+.4f}")

# Sort by accuracy_drop descending and add importance_rank
features.sort(key=lambda x: x["accuracy_drop"], reverse=True)
for rank, feat in enumerate(features, 1):
    feat["importance_rank"] = rank

# ── Group ablation ─────────────────────────────────────────────────────────────
print("\nRunning group ablation...")
groups_def = [
    {"name": "Material features",  "indices": [0, 6]},
    {"name": "Transport features", "indices": [1, 6]},
    {"name": "Weight features",    "indices": [4, 5]},
    {"name": "Origin features",    "indices": [3, 7]},
]
groups = []
for g in groups_def:
    abl_acc = ablate(g["indices"])
    drop = round(baseline_acc - abl_acc, 4)
    groups.append({
        "name":             g["name"],
        "indices":          g["indices"],
        "accuracy_drop":    drop,
        "ablated_accuracy": round(abl_acc, 4),
    })
    print(f"  {g['name']:25s}: ablated={abl_acc:.4f}  drop={drop:+.4f}")

# ── Save results ───────────────────────────────────────────────────────────────
results = {
    "baseline_accuracy": round(baseline_acc, 4),
    "features": features,
    "groups":   groups,
}

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved ablation results to {OUT}")
print("Done.")
