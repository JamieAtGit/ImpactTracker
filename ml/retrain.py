"""
retrain.py
==========
Manually triggered retraining script for the ImpactTracker XGBoost model.

Run this when you have accumulated ~10% more data (scraped products or new CSV data).
This script will:
  1. Load the 50k base dataset + any live-scraped products
  2. Re-derive grade labels using the correct DEFRA CO₂ thresholds
     (fixes a previously identified labelling inconsistency in all prior datasets)
  3. Retrain XGBoost with the exact same 8-feature vector used in production
  4. Save new model + updated encoders
  5. Re-run the full evaluation suite and update evaluation_results.json

Usage:
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/retrain.py

Output:
  ml/xgb_model.json               (replaces production model)
  ml/xgb_encoders/*.pkl           (updated encoders)
  ml/evaluation_results.json      (updated evaluation metrics)
"""

import os, sys, json, warnings, subprocess
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    accuracy_score, f1_score, log_loss, brier_score_loss,
    confusion_matrix, roc_curve, auc
)
from sklearn.calibration import calibration_curve
from imblearn.over_sampling import SMOTE
from scipy import stats

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
BASE_CSV   = os.path.join(BASE, "..", "common", "data", "csv", "expanded_eco_dataset.csv")
LIVE_CSV   = os.path.join(BASE, "live_scraped.csv")
MODEL_OUT  = os.path.join(BASE, "xgb_model.json")
ENC_DIR    = os.path.join(BASE, "xgb_encoders")
EVAL_OUT   = os.path.join(BASE, "evaluation_results.json")
os.makedirs(ENC_DIR, exist_ok=True)

GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]

# ── DEFRA grade thresholds (single source of truth) ───────────────────────────
def co2_to_grade(co2: float) -> str:
    """Assign eco grade from CO₂ value using DEFRA thresholds."""
    if co2 <= 0.05: return "A+"
    if co2 <= 0.15: return "A"
    if co2 <= 0.40: return "B"
    if co2 <= 1.00: return "C"
    if co2 <= 2.50: return "D"
    if co2 <= 5.00: return "E"
    return "F"

# ── Load datasets ──────────────────────────────────────────────────────────────
print("=" * 60)
print("ImpactTracker — Model Retraining Pipeline")
print("=" * 60)

dfs = []

# Base 50k dataset
if os.path.exists(BASE_CSV):
    base = pd.read_csv(BASE_CSV)
    base = base[base["true_eco_score"].isin(GRADE_ORDER)].copy()
    dfs.append(("50k base", base))
    print(f"  Loaded base dataset:  {len(base):>6,} rows")
else:
    print(f"  WARNING: Base CSV not found at {BASE_CSV}")

# Live scraped data (appended by backend on every successful scrape)
if os.path.exists(LIVE_CSV):
    live = pd.read_csv(LIVE_CSV)
    live = live[live["true_eco_score"].isin(GRADE_ORDER)].copy()
    dfs.append(("live scraped", live))
    print(f"  Loaded live scraped:  {len(live):>6,} rows")
else:
    print(f"  No live_scraped.csv yet — training on base dataset only")

df = pd.concat([d for _, d in dfs], ignore_index=True)
print(f"  Combined:             {len(df):>6,} rows")

# ── Clean ──────────────────────────────────────────────────────────────────────
required = ["material", "transport", "recyclability", "origin", "weight", "co2_emissions"]
df = df.dropna(subset=required)
for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.strip().str.title()
df["weight"]        = pd.to_numeric(df["weight"],        errors="coerce")
df["co2_emissions"] = pd.to_numeric(df["co2_emissions"], errors="coerce")
df = df.dropna(subset=["weight", "co2_emissions"])
df = df[df["weight"] > 0]

# ── Re-derive grade labels from CO₂ using DEFRA thresholds ────────────────────
# (Fixes the labelling inconsistency identified in the original training data
#  where labels were only 26% consistent with the production DEFRA thresholds)
df["true_eco_score"] = df["co2_emissions"].apply(co2_to_grade)
print(f"\n  Grade distribution after DEFRA re-labelling:")
dist = df["true_eco_score"].value_counts()
for g in GRADE_ORDER:
    count = dist.get(g, 0)
    bar = "█" * (count // 500)
    print(f"    {g:3}: {count:6,}  {bar}")

# ── Fit encoders on combined data ──────────────────────────────────────────────
print("\n  Fitting encoders on combined dataset…")
le_mat  = LabelEncoder().fit(df["material"])
le_trn  = LabelEncoder().fit(df["transport"])
le_rec  = LabelEncoder().fit(df["recyclability"])
le_ori  = LabelEncoder().fit(df["origin"])
le_lbl  = LabelEncoder().fit(df["true_eco_score"])

joblib.dump(le_mat, os.path.join(ENC_DIR, "material_encoder.pkl"))
joblib.dump(le_trn, os.path.join(ENC_DIR, "transport_encoder.pkl"))
joblib.dump(le_rec, os.path.join(ENC_DIR, "recyclability_encoder.pkl"))
joblib.dump(le_ori, os.path.join(ENC_DIR, "origin_encoder.pkl"))
joblib.dump(le_lbl, os.path.join(ENC_DIR, "label_encoder.pkl"))

# weight_bin encoder for backward compat (not used in 8-feature vector directly)
le_wb = LabelEncoder().fit(["0","1","2","3"])
joblib.dump(le_wb, os.path.join(ENC_DIR, "weight_bin_encoder.pkl"))

print(f"    Materials:      {len(le_mat.classes_)} unique values")
print(f"    Origins:        {len(le_ori.classes_)} unique values")
print(f"    Grade classes:  {list(le_lbl.classes_)}")

# ── Build feature matrix (exact same 8 features as production) ─────────────────
def safe_enc(enc, val):
    try:    return int(enc.transform([val])[0])
    except: return 0

def build_row(r):
    mat = safe_enc(le_mat, r["material"])
    trn = safe_enc(le_trn, r["transport"])
    rec = safe_enc(le_rec, r["recyclability"])
    ori = safe_enc(le_ori, r["origin"])
    w   = float(r["weight"])
    wl  = float(np.log1p(max(w, 0)))
    wb  = float(0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3)
    return [mat, trn, rec, ori, wl, wb, float(mat) * float(trn), float(ori) * float(rec)]

print("\n  Building 8-feature vectors…")
X = np.array([build_row(r) for _, r in df.iterrows()])
y = le_lbl.transform(df["true_eco_score"].values)
n_cls = len(le_lbl.classes_)
classes = list(le_lbl.classes_)

# ── SMOTE to balance classes ───────────────────────────────────────────────────
print("  Applying SMOTE to balance classes…")
X_bal, y_bal = SMOTE(random_state=42).fit_resample(X, y)
print(f"  Post-SMOTE: {len(X_bal):,} samples ({n_cls} classes × {len(X_bal)//n_cls:,} each)")

# ── Train/test split ───────────────────────────────────────────────────────────
idx = np.arange(len(X_bal))
idx_tr, idx_te = train_test_split(idx, test_size=0.20, random_state=42, stratify=y_bal)
X_tr, X_te = X_bal[idx_tr], X_bal[idx_te]
y_tr, y_te = y_bal[idx_tr], y_bal[idx_te]

# ── Train XGBoost ──────────────────────────────────────────────────────────────
print("\n  Training XGBoost classifier…")
model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=7,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42,
    verbosity=0,
)
model.fit(X_tr, y_tr)
model.save_model(MODEL_OUT)
print(f"  ✅ Model saved → {MODEL_OUT}")

# Quick test set check
y_pred   = model.predict(X_te)
test_acc = float(accuracy_score(y_te, y_pred))
test_f1  = float(f1_score(y_te, y_pred, average="macro", zero_division=0))
print(f"  Test accuracy: {test_acc:.4f}   Macro F1: {test_f1:.4f}")

# ── Full evaluation suite ──────────────────────────────────────────────────────
print("\n  Running full evaluation suite (5-fold CV + ROC + calibration)…")

# Need unbalanced X/y for CV (no data leakage through SMOTE)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# 5-fold CV on balanced data is fine for comparing folds
cv_acc, cv_f1, cv_ll, cv_brier = [], [], [], []
for fold, (tri, tei) in enumerate(skf.split(X_bal, y_bal), 1):
    m = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                           use_label_encoder=False, eval_metric="mlogloss",
                           random_state=42, verbosity=0)
    m.fit(X_bal[tri], y_bal[tri])
    yp  = m.predict(X_bal[tei])
    ypr = m.predict_proba(X_bal[tei])
    yb  = label_binarize(y_bal[tei], classes=list(range(n_cls)))
    cv_acc.append(float(accuracy_score(y_bal[tei], yp)))
    cv_f1.append(float(f1_score(y_bal[tei], yp, average="macro", zero_division=0)))
    cv_ll.append(float(log_loss(y_bal[tei], ypr)))
    cv_brier.append(float(np.mean([brier_score_loss(yb[:, c], ypr[:, c]) for c in range(n_cls)])))
    print(f"    Fold {fold}: acc={cv_acc[-1]:.4f}  F1={cv_f1[-1]:.4f}")

# RF baseline
rf_acc = []
for tri, tei in skf.split(X_bal, y_bal):
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_bal[tri], y_bal[tri])
    rf_acc.append(float(accuracy_score(y_bal[tei], rf.predict(X_bal[tei]))))

t_stat, p_val_ttest = stats.ttest_rel(cv_acc, rf_acc)

cv_results = {
    "folds": 5,
    "xgboost": {
        "accuracy_mean":  round(float(np.mean(cv_acc)),   4),
        "accuracy_std":   round(float(np.std(cv_acc)),    4),
        "f1_macro_mean":  round(float(np.mean(cv_f1)),    4),
        "f1_macro_std":   round(float(np.std(cv_f1)),     4),
        "log_loss_mean":  round(float(np.mean(cv_ll)),    4),
        "brier_mean":     round(float(np.mean(cv_brier)), 4),
        "per_fold_acc":   [round(v, 4) for v in cv_acc],
    },
    "random_forest": {
        "accuracy_mean":  round(float(np.mean(rf_acc)), 4),
        "accuracy_std":   round(float(np.std(rf_acc)),  4),
        "per_fold_acc":   [round(v, 4) for v in rf_acc],
    },
    "paired_t_test": {
        "t_statistic":        round(float(t_stat), 4),
        "p_value":            round(float(p_val_ttest), 5),
        "significant_at_0_05": bool(p_val_ttest < 0.05),
    }
}

# ROC curves (OOF probabilities)
y_proba_oof = cross_val_predict(model, X_bal, y_bal, cv=skf, method="predict_proba")
y_bin = label_binarize(y_bal, classes=list(range(n_cls)))
roc_data = {}
for i, cls_name in enumerate(classes):
    fpr, tpr, _ = roc_curve(y_bin[:, i], y_proba_oof[:, i])
    roc_auc = float(auc(fpr, tpr))
    step = max(1, len(fpr) // 50)
    roc_data[cls_name] = {
        "fpr":  [round(v, 4) for v in fpr[::step].tolist()],
        "tpr":  [round(v, 4) for v in tpr[::step].tolist()],
        "auc":  round(roc_auc, 4),
    }

all_fpr = np.unique(np.concatenate([roc_curve(y_bin[:, i], y_proba_oof[:, i])[0] for i in range(n_cls)]))
mean_tpr = np.zeros_like(all_fpr)
for i in range(n_cls):
    fpr_i, tpr_i, _ = roc_curve(y_bin[:, i], y_proba_oof[:, i])
    mean_tpr += np.interp(all_fpr, fpr_i, tpr_i)
mean_tpr /= n_cls
step = max(1, len(all_fpr) // 60)
roc_data["macro"] = {
    "fpr":  [round(v, 4) for v in all_fpr[::step].tolist()],
    "tpr":  [round(v, 4) for v in mean_tpr[::step].tolist()],
    "auc":  round(float(auc(all_fpr, mean_tpr)), 4),
}

# Calibration
all_probs = np.concatenate([y_proba_oof[:, i] for i in range(n_cls)])
all_true  = np.concatenate([(y_bal == i).astype(int) for i in range(n_cls)])
frac_pos, mean_pred = calibration_curve(all_true, all_probs, n_bins=10, strategy="uniform")
calibration_data = {
    "mean_predicted_prob":    [round(v, 4) for v in mean_pred.tolist()],
    "fraction_of_positives":  [round(v, 4) for v in frac_pos.tolist()],
    "brier_score":            round(float(brier_score_loss(all_true, all_probs)), 4),
    "note": "Aggregated one-vs-rest across all 7 grade classes (5-fold OOF predictions)"
}

# McNemar's test — ML vs rule-based on test set (original unbalanced data)
# Re-split original unbalanced data to get a fair test set
idx_raw = np.arange(len(X))
idx_tr_raw, idx_te_raw = train_test_split(idx_raw, test_size=0.20, random_state=42, stratify=y)
X_te_raw  = X[idx_te_raw]
y_te_raw  = y[idx_te_raw]
y_true_str = le_lbl.inverse_transform(y_te_raw)

y_pred_raw = model.predict(X_te_raw)
y_pred_str = le_lbl.inverse_transform(y_pred_raw)

# Rule-based grades (derived from CO2, same DEFRA thresholds)
y_rule = np.array([co2_to_grade(c) for c in df["co2_emissions"].values])
y_rule_te = y_rule[idx_te_raw]

ml_correct   = (y_pred_str == y_true_str)
rule_correct = (y_rule_te  == y_true_str)
n10 = int(np.sum( ml_correct & ~rule_correct))
n01 = int(np.sum(~ml_correct &  rule_correct))
if (n01 + n10) > 0:
    mcnemar_stat = (abs(n01 - n10) - 1.0)**2 / (n01 + n10)
    mcnemar_p    = float(1 - stats.chi2.cdf(mcnemar_stat, df=1))
else:
    mcnemar_stat, mcnemar_p = 0.0, 1.0

ml_acc_raw   = float(accuracy_score(y_true_str, y_pred_str))
rule_acc_raw = float(accuracy_score(y_true_str, y_rule_te))

mcnemar_data = {
    "ml_accuracy":               round(ml_acc_raw,   4),
    "rule_accuracy":             round(rule_acc_raw, 4),
    "n_test":                    int(len(y_true_str)),
    "n10_ml_right_rule_wrong":   n10,
    "n01_ml_wrong_rule_right":   n01,
    "mcnemar_statistic":         round(float(mcnemar_stat), 4),
    "p_value":                   round(mcnemar_p, 5),
    "significant_at_0_05":       bool(mcnemar_p < 0.05),
    "interpretation": (
        "ML significantly outperforms rule-based (p<0.05)"
        if mcnemar_p < 0.05
        else "No statistically significant difference detected (p≥0.05)"
    )
}

# Confusion matrix
cm = confusion_matrix(y_te, y_pred).tolist()

# Dataset statistics
grade_dist = {g: int((df["true_eco_score"] == g).sum()) for g in GRADE_ORDER if (df["true_eco_score"] == g).any()}
material_dist = {k: int(v) for k, v in df["material"].value_counts().head(15).items()}
origin_dist   = {k: int(v) for k, v in df["origin"].value_counts().head(15).items()}
transport_dist = {k: int(v) for k, v in df["transport"].value_counts().items()}
co2_vals = df["co2_emissions"].values
co2_hist, co2_edges = np.histogram(np.log1p(co2_vals), bins=20)
co2_distribution = {
    "histogram_counts":          co2_hist.tolist(),
    "histogram_bin_edges_log1p": [round(v, 3) for v in co2_edges.tolist()],
    "mean":   round(float(co2_vals.mean()),            3),
    "median": round(float(np.median(co2_vals)),        3),
    "p25":    round(float(np.percentile(co2_vals, 25)), 3),
    "p75":    round(float(np.percentile(co2_vals, 75)), 3),
    "max":    round(float(co2_vals.max()),              3),
}
dataset_stats = {
    "total_rows":             len(df),
    "grade_distribution":     grade_dist,
    "material_distribution":  material_dist,
    "origin_distribution":    origin_dist,
    "transport_distribution": transport_dist,
    "co2_distribution":       co2_distribution,
    "train_size":             len(X_tr),
    "test_size":              len(X_te),
    "live_scraped_rows":      len(dfs[1][1]) if len(dfs) > 1 else 0,
}

# ── Compute per-class precision / recall / F1 from confusion matrix ────────────
cm_np = np.array(cm)
per_class_metrics = {}
for i, label in enumerate(classes):
    tp = int(cm_np[i, i])
    fp = int(cm_np[:, i].sum()) - tp
    fn = int(cm_np[i, :].sum()) - tp
    support = int(cm_np[i, :].sum())
    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec  = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1s  = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    per_class_metrics[label] = {
        "precision": round(prec, 4),
        "recall":    round(rec,  4),
        "f1":        round(f1s,  4),
        "support":   support,
    }
macro_p = round(sum(v["precision"] for v in per_class_metrics.values()) / len(per_class_metrics), 4)
macro_r = round(sum(v["recall"]    for v in per_class_metrics.values()) / len(per_class_metrics), 4)
macro_f = round(sum(v["f1"]        for v in per_class_metrics.values()) / len(per_class_metrics), 4)
per_class_metrics["macro"] = {"precision": macro_p, "recall": macro_r, "f1": macro_f}

# ── Assemble and save evaluation_results.json ──────────────────────────────────
results = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "model":        "XGBoost (n_features=8, n_classes=7)",
    "dataset":      f"50k base + {dataset_stats['live_scraped_rows']} live scraped",
    "classes":      classes,
    "grade_order":  GRADE_ORDER,
    "cross_validation":  cv_results,
    "roc_curves":        roc_data,
    "calibration":       calibration_data,
    "mcnemar_test":      mcnemar_data,
    "confusion_matrix": {
        "matrix":        cm,
        "labels":        classes,
        "test_accuracy": round(test_acc, 4),
        "test_f1_macro": round(test_f1,  4),
    },
    "per_class_metrics":  per_class_metrics,
    "dataset_statistics": dataset_stats,
}

with open(EVAL_OUT, "w") as f:
    json.dump(results, f, indent=2)

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("✅ Retraining complete")
print(f"   Total training rows:  {len(df):,} (pre-SMOTE)")
print(f"   Post-SMOTE:           {len(X_bal):,}")
print(f"   CV accuracy:          {np.mean(cv_acc):.4f} ± {np.std(cv_acc):.4f}")
print(f"   Macro AUC:            {roc_data['macro']['auc']:.4f}")
print(f"   Test accuracy (raw):  {ml_acc_raw:.4f}")
print(f"   Rule-based accuracy:  {rule_acc_raw:.4f}")
print(f"   McNemar p:            {mcnemar_p:.5f}")
print(f"   Model saved:          {MODEL_OUT}")
print(f"   Evaluation saved:     {EVAL_OUT}")
print("=" * 60)

# ── Post-hoc calibration ───────────────────────────────────────────────────────
# Re-run calibrate_model.py so calibrated_model.pkl stays in sync with the
# freshly trained xgb_model.json.  Without this step the production app would
# serve stale probability estimates after every retrain.
print("\n  Running post-hoc isotonic calibration…")
calibrate_script = os.path.join(BASE, "calibrate_model.py")
result = subprocess.run([sys.executable, calibrate_script], check=True)
print("  ✅ calibrated_model.pkl updated")
