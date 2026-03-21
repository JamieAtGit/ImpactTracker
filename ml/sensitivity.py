"""
sensitivity.py
==============
Sensitivity analysis for ImpactTracker XGBoost model.

Answers: "If the scraper misidentifies a feature, how often does the eco grade change?"

For each test sample, perturbs categorical features and weight, then measures
what fraction of samples have their predicted grade changed.

Usage:
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/sensitivity.py

Output:
  ml/sensitivity_results.json
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(os.path.abspath(__file__))
BASE_CSV = os.path.join(BASE, "..", "common", "data", "csv", "expanded_eco_dataset.csv")
ENC_DIR  = os.path.join(BASE, "xgb_encoders")
MODEL    = os.path.join(BASE, "xgb_model.json")
OUT      = os.path.join(BASE, "sensitivity_results.json")

GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]

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
df["true_eco_score"] = df["co2_emissions"].apply(co2_to_grade)
df = df[df["true_eco_score"].isin(GRADE_ORDER)].reset_index(drop=True)

print(f"Dataset size: {len(df):,} rows")

# ── Helper: safe encode ────────────────────────────────────────────────────────
def safe_enc(enc, val):
    try:    return int(enc.transform([val])[0])
    except: return 0

# ── Build feature matrix (returns numpy array aligned with df) ─────────────────
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

known_classes = set(le_lbl.classes_)
mask = df["true_eco_score"].isin(known_classes)
X = X[mask.values]
df_clean = df[mask].reset_index(drop=True)
y = le_lbl.transform(df_clean["true_eco_score"].values)

# ── Raw test split (same seed as ablation.py / retrain.py) ────────────────────
_, X_test, _, y_test, _, df_test = train_test_split(
    X, y, df_clean, test_size=0.20, random_state=42, stratify=y
)
X_test = np.array(X_test)
df_test = df_test.reset_index(drop=True)

print(f"Test set size: {len(X_test):,}")

# ── Baseline predictions ───────────────────────────────────────────────────────
y_pred_base = model.predict(X_test)
n_samples = len(X_test)

# ── Frequency-ordered alternatives ────────────────────────────────────────────
mat_freq  = df_clean["material"].value_counts().index.tolist()
trn_freq  = df_clean["transport"].value_counts().index.tolist()
ori_freq  = df_clean["origin"].value_counts().index.tolist()
rec_vals  = df_clean["recyclability"].value_counts().index.tolist()

# ── Perturbation helper ────────────────────────────────────────────────────────
def grade_change_for_perturbation(X_base, df_ref, y_pred_base, perturb_fn, selector_fn=None):
    """
    Returns (grade_change_pct, n_affected, n_tested).
    selector_fn: optional function(row_df) -> bool, filters which rows to test.
    perturb_fn: function(X_row, df_row) -> X_row_perturbed (modifies a copy)
    """
    n_tested = 0
    n_changed = 0
    X_perturbed = []
    indices = []

    for i in range(len(X_base)):
        row_df = df_ref.iloc[i]
        if selector_fn is not None and not selector_fn(row_df):
            continue
        x_orig = X_base[i].copy()
        x_new  = perturb_fn(x_orig, row_df)
        if x_new is None:
            continue
        X_perturbed.append(x_new)
        indices.append(i)
        n_tested += 1

    if n_tested == 0:
        return 0.0, 0, 0

    X_arr = np.array(X_perturbed)
    y_new = model.predict(X_arr)
    for k, i in enumerate(indices):
        if y_new[k] != y_pred_base[i]:
            n_changed += 1

    pct = round(100.0 * n_changed / n_tested, 2)
    return pct, n_changed, n_tested

# ── Material perturbations ─────────────────────────────────────────────────────
print("\nRunning material perturbations...")
perturbations = []

top_materials = mat_freq[:8]  # Test top 8 materials
for from_mat in top_materials:
    # Find top 3 alternatives
    alts = [m for m in mat_freq if m != from_mat][:3]
    for to_mat in alts:
        to_enc = safe_enc(le_mat, to_mat)

        def make_mat_perturb(t_enc):
            def perturb(x, row):
                x2 = x.copy()
                mat_orig = int(x[0])
                trn_orig = int(x[1])
                x2[0] = float(t_enc)
                x2[6] = float(t_enc) * float(trn_orig)
                return x2
            return perturb

        pct, n_changed, n_tested = grade_change_for_perturbation(
            X_test, df_test, y_pred_base,
            make_mat_perturb(to_enc),
            selector_fn=lambda row, fm=from_mat: row["material"] == fm
        )
        perturbations.append({
            "name":             f"Material: {from_mat} → {to_mat}",
            "feature":          "material",
            "from":             from_mat,
            "to":               to_mat,
            "grade_change_pct": pct,
            "n_affected":       n_changed,
            "n_tested":         n_tested,
        })
        print(f"  Material {from_mat} → {to_mat}: {pct}% ({n_changed}/{n_tested})")

# ── Transport perturbations ────────────────────────────────────────────────────
print("\nRunning transport perturbations...")
transport_pairs = [
    ("Air", "Ship"), ("Air", "Land"),
    ("Ship", "Air"), ("Ship", "Land"),
    ("Land", "Air"), ("Land", "Ship"),
]
for from_t, to_t in transport_pairs:
    to_enc = safe_enc(le_trn, to_t)

    def make_trn_perturb(t_enc):
        def perturb(x, row):
            x2 = x.copy()
            mat_orig = int(x[0])
            x2[1] = float(t_enc)
            x2[6] = float(mat_orig) * float(t_enc)
            return x2
        return perturb

    pct, n_changed, n_tested = grade_change_for_perturbation(
        X_test, df_test, y_pred_base,
        make_trn_perturb(to_enc),
        selector_fn=lambda row, ft=from_t: row["transport"] == ft
    )
    perturbations.append({
        "name":             f"Transport: {from_t} → {to_t}",
        "feature":          "transport",
        "from":             from_t,
        "to":               to_t,
        "grade_change_pct": pct,
        "n_affected":       n_changed,
        "n_tested":         n_tested,
    })
    print(f"  Transport {from_t} → {to_t}: {pct}% ({n_changed}/{n_tested})")

# ── Origin perturbations ───────────────────────────────────────────────────────
print("\nRunning origin perturbations...")
top_origins = ori_freq[:6]
for from_ori in top_origins:
    alts = [o for o in ori_freq if o != from_ori][:3]
    for to_ori in alts:
        to_enc = safe_enc(le_ori, to_ori)

        def make_ori_perturb(t_enc):
            def perturb(x, row):
                x2 = x.copy()
                rec_orig = int(x[2])
                x2[3] = float(t_enc)
                x2[7] = float(t_enc) * float(rec_orig)
                return x2
            return perturb

        pct, n_changed, n_tested = grade_change_for_perturbation(
            X_test, df_test, y_pred_base,
            make_ori_perturb(to_enc),
            selector_fn=lambda row, fo=from_ori: row["origin"] == fo
        )
        perturbations.append({
            "name":             f"Origin: {from_ori} → {to_ori}",
            "feature":          "origin",
            "from":             from_ori,
            "to":               to_ori,
            "grade_change_pct": pct,
            "n_affected":       n_changed,
            "n_tested":         n_tested,
        })
        print(f"  Origin {from_ori} → {to_ori}: {pct}% ({n_changed}/{n_tested})")

# ── Weight perturbations ───────────────────────────────────────────────────────
print("\nRunning weight perturbations...")

def weight_to_bin(w):
    return 0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3

for factor, label in [(0.8, "-20%"), (1.2, "+20%"), (0.5, "-50%"), (1.5, "+50%")]:
    def make_weight_perturb(f):
        def perturb(x, row):
            x2 = x.copy()
            w_orig = float(row["weight"])
            w_new  = max(0.001, w_orig * f)
            x2[4] = float(np.log1p(w_new))
            x2[5] = float(weight_to_bin(w_new))
            return x2
        return perturb

    pct, n_changed, n_tested = grade_change_for_perturbation(
        X_test, df_test, y_pred_base,
        make_weight_perturb(factor)
    )
    perturbations.append({
        "name":             f"Weight {label}",
        "feature":          "weight",
        "from":             "original",
        "to":               f"×{factor}",
        "grade_change_pct": pct,
        "n_affected":       n_changed,
        "n_tested":         n_tested,
    })
    print(f"  Weight {label}: {pct}% ({n_changed}/{n_tested})")

# ── Summary statistics ─────────────────────────────────────────────────────────
feature_groups = {}
for p in perturbations:
    feat = p["feature"]
    if feat not in feature_groups:
        feature_groups[feat] = []
    feature_groups[feat].append(p["grade_change_pct"])

avg_by_feature = {k: round(sum(v) / len(v), 2) for k, v in feature_groups.items()}
most_sensitive = max(avg_by_feature, key=avg_by_feature.get)

air_to_ship = next(
    (p["grade_change_pct"] for p in perturbations
     if p["feature"] == "transport" and p["from"] == "Air" and p["to"] == "Ship"),
    None
)
weight_20 = next(
    (p["grade_change_pct"] for p in perturbations
     if p["feature"] == "weight" and p["to"] == "×1.2"),
    None
)
weight_50 = next(
    (p["grade_change_pct"] for p in perturbations
     if p["feature"] == "weight" and p["to"] == "×1.5"),
    None
)

summary = {
    "most_sensitive_feature":   most_sensitive,
    "avg_grade_change_by_feature": avg_by_feature,
    "transport_air_to_ship_pct": air_to_ship,
    "weight_20pct_change_pct":  weight_20,
    "weight_50pct_change_pct":  weight_50,
}

# ── Save results ───────────────────────────────────────────────────────────────
results = {
    "n_samples":     n_samples,
    "perturbations": perturbations,
    "summary":       summary,
}

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nMost sensitive feature: {most_sensitive}")
print(f"Saved sensitivity results to {OUT}")
print("Done.")
