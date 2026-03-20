"""
compute_evaluation.py
=====================
Produces evaluation_results.json — all academic evaluation metrics for the
ImpactTracker XGBoost model.  Run once locally; commit the JSON; the backend
serves it statically so Railway never needs to recompute it.

Outputs
-------
ml/evaluation_results.json   (committed to repo, served by backend)

Metrics computed
----------------
  • 5-fold cross-validation  (accuracy, macro-F1, log-loss, Brier score)
  • Paired t-test  (XGBoost vs Random Forest across CV folds)
  • McNemar's test (ML predictions vs rule-based grades, test set)
  • Multi-class ROC curves  (one-vs-rest, AUC per grade + macro)
  • Calibration / reliability diagram  (mean predicted prob vs fraction positive)
  • Dataset distribution  (grade, material, origin, CO₂ histogram)
  • Confusion matrix  (from held-out test set, 20 %)

Usage
-----
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/compute_evaluation.py
"""

import os, json, warnings
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    roc_curve, auc, accuracy_score, f1_score,
    log_loss, brier_score_loss, confusion_matrix
)
from sklearn.calibration import calibration_curve
from scipy import stats

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE  = os.path.dirname(os.path.abspath(__file__))
CSV   = os.path.join(BASE, "eco_dataset.csv")
MODEL = os.path.join(BASE, "xgb_model.json")
ENC   = os.path.join(BASE, "xgb_encoders")
OUT   = os.path.join(BASE, "evaluation_results.json")

GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]

# ── Grade thresholds (rule-based) ─────────────────────────────────────────────
def co2_to_grade(co2) -> str:
    try:
        co2 = float(co2)
    except (TypeError, ValueError):
        return "C"
    if co2 <= 0.05:  return "A+"
    if co2 <= 0.15:  return "A"
    if co2 <= 0.40:  return "B"
    if co2 <= 1.00:  return "C"
    if co2 <= 2.50:  return "D"
    if co2 <= 5.00:  return "E"
    return "F"

# ── Load & encode dataset ─────────────────────────────────────────────────────
print("Loading dataset …")
df = pd.read_csv(CSV).dropna(subset=["material", "transport", "recyclability",
                                      "origin", "weight", "true_eco_score", "co2_emissions"])
df = df[df["true_eco_score"].isin(GRADE_ORDER)].reset_index(drop=True)
print(f"  {len(df):,} rows after cleaning")

le_mat  = joblib.load(os.path.join(ENC, "material_encoder.pkl"))
le_trn  = joblib.load(os.path.join(ENC, "transport_encoder.pkl"))
le_rec  = joblib.load(os.path.join(ENC, "recyclability_encoder.pkl"))
le_ori  = joblib.load(os.path.join(ENC, "origin_encoder.pkl"))
le_lbl  = joblib.load(os.path.join(ENC, "label_encoder.pkl"))

def safe_enc(enc, val, default):
    try:
        return int(enc.transform([val])[0])
    except Exception:
        try:
            return int(enc.transform([default])[0])
        except Exception:
            return 0

def build_features(row):
    mat = safe_enc(le_mat, row["material"], "Other")
    trn = safe_enc(le_trn, row["transport"], "Ship")
    rec = safe_enc(le_rec, row["recyclability"], "Medium")
    ori = safe_enc(le_ori, str(row["origin"]).title(), "Unknown")
    w   = float(row["weight"])
    wl  = float(np.log1p(max(w, 0)))
    wb  = float(0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3)
    return [mat, trn, rec, ori, wl, wb, float(mat)*float(trn), float(ori)*float(rec)]

print("Encoding features …")
X = np.array([build_features(r) for _, r in df.iterrows()])
y_raw  = df["true_eco_score"].values                      # string grades
y      = le_lbl.transform(y_raw)                          # integer labels
y_rule = np.array([co2_to_grade(c) for c in df["co2_emissions"]])  # rule-based grade strings
classes = list(le_lbl.classes_)   # ['A', 'A+', 'B', 'C', 'D', 'E', 'F']
n_cls = len(classes)

# ── Train/test split — use index arrays so all arrays stay aligned ─────────────
idx = np.arange(len(X))
idx_tr, idx_te = train_test_split(idx, test_size=0.20, random_state=42, stratify=y)
X_tr, X_te = X[idx_tr], X[idx_te]
y_tr, y_te = y[idx_tr], y[idx_te]
y_te_str  = le_lbl.inverse_transform(y_te)   # true labels (str) for test set
y_rule_te = y_rule[idx_te]                   # rule-based grades for test set
y_raw_te  = y_raw[idx_te]                    # ground-truth grades (str) for test set

# ── Load XGBoost model ────────────────────────────────────────────────────────
print("Loading XGBoost model …")
model = xgb.XGBClassifier()
model.load_model(MODEL)

# ── 1. Cross-validation ───────────────────────────────────────────────────────
print("Computing 5-fold cross-validation …")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_acc, cv_f1, cv_ll, cv_brier = [], [], [], []
for fold, (tri, tei) in enumerate(skf.split(X, y), 1):
    Xf_tr, Xf_te = X[tri], X[tei]
    yf_tr, yf_te = y[tri], y[tei]
    m = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                           use_label_encoder=False, eval_metric="mlogloss",
                           random_state=42, verbosity=0)
    m.fit(Xf_tr, yf_tr)
    yf_pred  = m.predict(Xf_te)
    yf_proba = m.predict_proba(Xf_te)
    cv_acc.append(float(accuracy_score(yf_te, yf_pred)))
    cv_f1.append(float(f1_score(yf_te, yf_pred, average="macro", zero_division=0)))
    cv_ll.append(float(log_loss(yf_te, yf_proba)))
    # multiclass Brier
    yf_bin = label_binarize(yf_te, classes=list(range(n_cls)))
    cv_brier.append(float(np.mean([brier_score_loss(yf_bin[:, c], yf_proba[:, c])
                                   for c in range(n_cls)])))
    print(f"  Fold {fold}: acc={cv_acc[-1]:.4f}  F1={cv_f1[-1]:.4f}  "
          f"LogLoss={cv_ll[-1]:.4f}  Brier={cv_brier[-1]:.4f}")

# Compare with RF baseline for t-test
rf_acc = []
for tri, tei in skf.split(X, y):
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X[tri], y[tri])
    rf_acc.append(float(accuracy_score(y[tei], rf.predict(X[tei]))))

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
        "t_statistic": round(float(t_stat), 4),
        "p_value":     round(float(p_val_ttest), 5),
        "significant_at_0_05": bool(p_val_ttest < 0.05),
    }
}
print(f"CV done: acc={np.mean(cv_acc):.4f}±{np.std(cv_acc):.4f}  "
      f"p(XGB>RF)={p_val_ttest:.4f}")

# ── 2. ROC curves ─────────────────────────────────────────────────────────────
print("Computing ROC curves …")
# Use cross_val_predict for unbiased out-of-fold probabilities
y_proba_oof = cross_val_predict(model, X, y, cv=skf, method="predict_proba")

y_bin = label_binarize(y, classes=list(range(n_cls)))
roc_data = {}
auc_scores = []
for i, cls_name in enumerate(classes):
    fpr, tpr, _ = roc_curve(y_bin[:, i], y_proba_oof[:, i])
    roc_auc = float(auc(fpr, tpr))
    auc_scores.append(roc_auc)
    # downsample to 50 points for JSON compactness
    step = max(1, len(fpr) // 50)
    roc_data[cls_name] = {
        "fpr":  [round(v, 4) for v in fpr[::step].tolist()],
        "tpr":  [round(v, 4) for v in tpr[::step].tolist()],
        "auc":  round(roc_auc, 4),
    }
    print(f"  {cls_name}: AUC={roc_auc:.4f}")

# Macro-average ROC
all_fpr = np.unique(np.concatenate([roc_curve(y_bin[:, i], y_proba_oof[:, i])[0]
                                     for i in range(n_cls)]))
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
print(f"  Macro AUC: {roc_data['macro']['auc']:.4f}")

# ── 3. Calibration curve ──────────────────────────────────────────────────────
print("Computing calibration …")
# Aggregate across all classes (one-vs-rest)
all_probs, all_true = [], []
for i in range(n_cls):
    all_probs.extend(y_proba_oof[:, i].tolist())
    all_true.extend((y == i).astype(int).tolist())

all_probs = np.array(all_probs)
all_true  = np.array(all_true)

frac_pos, mean_pred = calibration_curve(all_true, all_probs, n_bins=10, strategy="uniform")
calibration_data = {
    "mean_predicted_prob": [round(v, 4) for v in mean_pred.tolist()],
    "fraction_of_positives": [round(v, 4) for v in frac_pos.tolist()],
    "brier_score": round(float(brier_score_loss(all_true, all_probs)), 4),
    "note": "Aggregated one-vs-rest across all 7 grade classes (5-fold OOF predictions)"
}
print(f"  Brier score: {calibration_data['brier_score']:.4f}")

# ── 4. McNemar's test (ML vs rule-based on test set) ─────────────────────────
print("Computing McNemar's test …")
y_pred_ml   = model.predict(X_te)
y_pred_str  = le_lbl.inverse_transform(y_pred_ml)

ml_correct   = (y_pred_str  == y_raw_te)
rule_correct = (y_rule_te   == y_raw_te)

n10 = int(np.sum( ml_correct & ~rule_correct))  # ML right, rule wrong
n01 = int(np.sum(~ml_correct &  rule_correct))  # ML wrong, rule right

# McNemar statistic with continuity correction
if (n01 + n10) > 0:
    mcnemar_stat = (abs(n01 - n10) - 1.0)**2 / (n01 + n10)
    mcnemar_p    = float(1 - stats.chi2.cdf(mcnemar_stat, df=1))
else:
    mcnemar_stat, mcnemar_p = 0.0, 1.0

ml_acc   = float(accuracy_score(y_raw_te, y_pred_str))
rule_acc = float(accuracy_score(y_raw_te, y_rule_te))

mcnemar_data = {
    "ml_accuracy":   round(ml_acc,   4),
    "rule_accuracy": round(rule_acc, 4),
    "n_test":        int(len(y_raw_te)),
    "n10_ml_right_rule_wrong": n10,
    "n01_ml_wrong_rule_right": n01,
    "mcnemar_statistic": round(float(mcnemar_stat), 4),
    "p_value": round(mcnemar_p, 5),
    "significant_at_0_05": bool(mcnemar_p < 0.05),
    "interpretation": (
        "ML significantly outperforms rule-based (p<0.05)"
        if mcnemar_p < 0.05
        else "No statistically significant difference detected (p≥0.05)"
    )
}
print(f"  ML acc={ml_acc:.4f}  Rule acc={rule_acc:.4f}  "
      f"n10={n10}  n01={n01}  p={mcnemar_p:.5f}")


# ── 5. Confusion matrix (test set, from deployed model) ───────────────────────
y_pred_ml_te = model.predict(X_te)
cm = confusion_matrix(y_te, y_pred_ml_te).tolist()
test_acc = float(accuracy_score(y_te, y_pred_ml_te))
test_f1  = float(f1_score(y_te, y_pred_ml_te, average="macro", zero_division=0))
print(f"Test set: acc={test_acc:.4f}  macro-F1={test_f1:.4f}")

# ── 6. Dataset distribution ───────────────────────────────────────────────────
print("Computing dataset distributions …")

grade_dist = df["true_eco_score"].value_counts().to_dict()
grade_dist = {k: int(v) for k, v in sorted(grade_dist.items(),
                                             key=lambda x: GRADE_ORDER.index(x[0]))}

material_dist = (df["material"].value_counts().head(15).to_dict())
material_dist = {k: int(v) for k, v in material_dist.items()}

origin_dist = (df["origin"].str.title().value_counts().head(15).to_dict())
origin_dist = {k: int(v) for k, v in origin_dist.items()}

transport_dist = df["transport"].value_counts().to_dict()
transport_dist = {k: int(v) for k, v in transport_dist.items()}

co2_vals = pd.to_numeric(df["co2_emissions"], errors="coerce").dropna().values
co2_hist, co2_edges = np.histogram(np.log1p(co2_vals), bins=20)
co2_distribution = {
    "histogram_counts":     co2_hist.tolist(),
    "histogram_bin_edges_log1p": [round(v, 3) for v in co2_edges.tolist()],
    "mean":   round(float(co2_vals.mean()),   3),
    "median": round(float(np.median(co2_vals)), 3),
    "p25":    round(float(np.percentile(co2_vals, 25)), 3),
    "p75":    round(float(np.percentile(co2_vals, 75)), 3),
    "max":    round(float(co2_vals.max()),    3),
}

dataset_stats = {
    "total_rows":      len(df),
    "grade_distribution":    grade_dist,
    "material_distribution": material_dist,
    "origin_distribution":   origin_dist,
    "transport_distribution": transport_dist,
    "co2_distribution":      co2_distribution,
    "train_size": len(X_tr),
    "test_size":  len(X_te),
}

# ── Assemble & save ───────────────────────────────────────────────────────────
results = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "model": "XGBoost (n_features=8, n_classes=7)",
    "dataset": CSV,
    "classes": classes,
    "grade_order": GRADE_ORDER,
    "cross_validation":  cv_results,
    "roc_curves":        roc_data,
    "calibration":       calibration_data,
    "mcnemar_test":      mcnemar_data,
    "confusion_matrix": {
        "matrix": cm,
        "labels": classes,
        "test_accuracy": round(test_acc, 4),
        "test_f1_macro": round(test_f1, 4),
    },
    "dataset_statistics": dataset_stats,
}

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved → {OUT}")
print(f"   CV acc:    {np.mean(cv_acc):.4f} ± {np.std(cv_acc):.4f}")
print(f"   Macro AUC: {roc_data['macro']['auc']:.4f}")
print(f"   Brier:     {calibration_data['brier_score']:.4f}")
print(f"   McNemar p: {mcnemar_p:.5f}")
