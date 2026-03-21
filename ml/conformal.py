"""
conformal.py
============
Split-conformal calibration for the ImpactTracker XGBoost classifier.

Conformal prediction provides *mathematically guaranteed* prediction sets:
  "The true grade is in {B, C, D} with ≥95% probability"
  (guaranteed regardless of model calibration quality)

Theory:
  For a calibration set of n samples, compute nonconformity scores:
    s_i = 1 - p_hat(y_true_i | x_i)   (softmax probability of the true class)

  The (1-α) conformal quantile is:
    q_hat = ⌈(n+1)(1-α)⌉/n quantile of {s_1, ..., s_n}

  Prediction set for a new x:
    C(x) = { y : 1 - p_hat(y | x) ≤ q_hat }
         = { y : p_hat(y | x) ≥ 1 - q_hat }

  Marginal coverage guarantee: P(y_true ∈ C(x)) ≥ 1 - α  (Vovk et al.)

Usage:
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/conformal.py
"""

import os, json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
BASE_CSV   = os.path.join(BASE, "..", "common", "data", "csv", "expanded_eco_dataset.csv")
LIVE_CSV   = os.path.join(BASE, "live_scraped.csv")
MODEL      = os.path.join(BASE, "xgb_model.json")
ENC_DIR    = os.path.join(BASE, "xgb_encoders")
OUT        = os.path.join(BASE, "conformal_config.json")

GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]
ALPHA_LEVELS = [0.10, 0.05, 0.01]   # → 90%, 95%, 99% coverage

# ── DEFRA grade thresholds (mirrors production + retrain.py exactly) ──────────
def co2_to_grade(co2: float) -> str:
    if co2 <= 0.05: return "A+"
    if co2 <= 0.15: return "A"
    if co2 <= 0.40: return "B"
    if co2 <= 1.00: return "C"
    if co2 <= 2.50: return "D"
    if co2 <= 5.00: return "E"
    return "F"

# ── Load model and encoders ───────────────────────────────────────────────────
print("Loading model and encoders…")
model = xgb.XGBClassifier()
model.load_model(MODEL)

le_mat = joblib.load(os.path.join(ENC_DIR, "material_encoder.pkl"))
le_trn = joblib.load(os.path.join(ENC_DIR, "transport_encoder.pkl"))
le_rec = joblib.load(os.path.join(ENC_DIR, "recyclability_encoder.pkl"))
le_ori = joblib.load(os.path.join(ENC_DIR, "origin_encoder.pkl"))
le_lbl = joblib.load(os.path.join(ENC_DIR, "label_encoder.pkl"))

def safe_enc(enc, val, default):
    try:    return int(enc.transform([val])[0])
    except:
        try: return int(enc.transform([default])[0])
        except: return 0

def build_row(row):
    mat = safe_enc(le_mat, row["material"], "Other")
    trn = safe_enc(le_trn, row["transport"], "Air")
    rec = safe_enc(le_rec, row["recyclability"], "Medium")
    ori = safe_enc(le_ori, row["origin"], "China")
    w   = float(row["weight"])
    wl  = float(np.log1p(max(w, 0)))
    wb  = float(0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3)
    return [mat, trn, rec, ori, wl, wb, float(mat)*float(trn), float(ori)*float(rec)]

# ── Load and clean dataset ────────────────────────────────────────────────────
print("Loading dataset…")
dfs = []
if os.path.exists(BASE_CSV):
    base = pd.read_csv(BASE_CSV)
    dfs.append(base)
    print(f"  Base dataset: {len(base):,} rows")
if os.path.exists(LIVE_CSV):
    live = pd.read_csv(LIVE_CSV)
    dfs.append(live)
    print(f"  Live scraped: {len(live):,} rows")

df = pd.concat(dfs, ignore_index=True)
required = ["material", "transport", "recyclability", "origin", "weight", "co2_emissions"]
df = df.dropna(subset=required)
for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.strip().str.title()
df["weight"]        = pd.to_numeric(df["weight"],        errors="coerce")
df["co2_emissions"] = pd.to_numeric(df["co2_emissions"], errors="coerce")
df = df.dropna(subset=["weight", "co2_emissions"])
df = df[df["weight"] > 0]

# Re-derive labels (same as retrain.py)
df["true_eco_score"] = df["co2_emissions"].apply(co2_to_grade)
print(f"  Clean rows: {len(df):,}")

# ── Build feature matrix ──────────────────────────────────────────────────────
print("Building feature matrix…")
X = np.array([build_row(r) for _, r in df.iterrows()])
y_str = df["true_eco_score"].values
y_enc = le_lbl.transform(y_str)

# ── Split: 60% train | 20% calibration | 20% test ────────────────────────────
# Use the SAME random_state=42 as retrain.py so the test set is independent
# of the training data. Calibration comes from the 80% non-test portion.
idx = np.arange(len(X))
idx_trainval, idx_test = train_test_split(idx, test_size=0.20, random_state=42, stratify=y_enc)
# 25% of the 80% trainval → 20% of total for calibration
idx_train, idx_cal   = train_test_split(idx_trainval, test_size=0.25, random_state=0, stratify=y_enc[idx_trainval])

X_cal, y_cal = X[idx_cal], y_enc[idx_cal]
X_te,  y_te  = X[idx_test], y_enc[idx_test]

print(f"  Calibration set: {len(X_cal):,} samples")
print(f"  Test set:        {len(X_te):,} samples")

# ── Compute nonconformity scores on calibration set ───────────────────────────
print("\nComputing nonconformity scores…")
proba_cal = model.predict_proba(X_cal)   # shape (n_cal, n_classes)

# s_i = 1 - p(y_true | x_i)
true_probs = proba_cal[np.arange(len(y_cal)), y_cal]
scores = 1.0 - true_probs

print(f"  Score statistics: min={scores.min():.4f}  median={np.median(scores):.4f}  max={scores.max():.4f}")

# ── Compute q_hat for each alpha ──────────────────────────────────────────────
n = len(scores)
q_hats = {}
for alpha in ALPHA_LEVELS:
    # Conformal quantile: ceil((n+1)(1-alpha)) / n
    level = np.ceil((n + 1) * (1 - alpha)) / n
    level = min(level, 1.0)
    q_hat = float(np.quantile(scores, level))
    q_hats[str(1 - alpha)] = round(q_hat, 6)
    print(f"  q_hat (α={alpha:.2f}, {int((1-alpha)*100)}% coverage): {q_hat:.4f}")

# ── Verify empirical coverage on held-out test set ───────────────────────────
print("\nVerifying empirical coverage on test set…")
proba_te = model.predict_proba(X_te)
class_order = list(le_lbl.classes_)

coverage_results = {}
avg_set_sizes    = {}
for alpha in ALPHA_LEVELS:
    key    = str(1 - alpha)
    q_hat  = q_hats[key]
    # Prediction set: all classes where 1 - p(y | x) ≤ q_hat  ↔  p(y | x) ≥ 1 - q_hat
    threshold = 1.0 - q_hat
    sets = [[class_order[j] for j in range(len(class_order)) if proba_te[i, j] >= threshold]
            for i in range(len(y_te))]
    # Coverage: fraction of samples where y_true ∈ prediction set
    y_te_str = le_lbl.inverse_transform(y_te)
    covered  = [y_te_str[i] in sets[i] for i in range(len(y_te))]
    cov = float(np.mean(covered))
    avg_size = float(np.mean([len(s) for s in sets]))
    coverage_results[key] = round(cov, 4)
    avg_set_sizes[key]    = round(avg_size, 2)
    print(f"  {int((1-alpha)*100)}% target → empirical coverage: {cov:.4f}  avg set size: {avg_size:.2f}")

# ── Save config ───────────────────────────────────────────────────────────────
config = {
    "description": (
        "Split-conformal calibration for ImpactTracker XGBoost. "
        "q_hat values are the nonconformity thresholds computed on a held-out "
        "calibration set (20% of dataset). Coverage is guaranteed marginally: "
        "P(y_true in C(x)) >= 1 - alpha."
    ),
    "n_calibration":       n,
    "class_order":         class_order,
    "q_hat":               q_hats,
    "empirical_coverage":  coverage_results,
    "avg_set_size":        avg_set_sizes,
    "alpha_levels":        ALPHA_LEVELS,
}

with open(OUT, "w") as f:
    json.dump(config, f, indent=2)

print(f"\n✅ Saved → {OUT}")

# ── Print a few example prediction sets ──────────────────────────────────────
print("\nExample prediction sets (95% confidence):")
q95 = q_hats["0.95"]
threshold_95 = 1.0 - q95
for i in range(min(5, len(X_te))):
    ps = [class_order[j] for j in range(len(class_order)) if proba_te[i, j] >= threshold_95]
    true = le_lbl.inverse_transform([y_te[i]])[0]
    conf = round(float(proba_te[i].max()) * 100, 1)
    print(f"  True: {true}  | Set: {{{', '.join(ps)}}}  | Softmax conf: {conf}%")
