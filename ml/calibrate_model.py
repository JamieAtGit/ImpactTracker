"""
Post-hoc probability calibration for the production XGBoost eco-grade model.

Background
----------
Raw XGBoost predict_proba() output is often over-confident — max-class
probabilities cluster near 1.0 even when the model is genuinely uncertain.
Isotonic regression calibration (Zadrozny & Elkan, 2002) maps these raw
scores to better-calibrated probability estimates without retraining.

Method
------
- cv='prefit' — the XGBoost model is already trained; only the calibration
  mapping (one isotonic regressor per class) is fitted on a held-out
  calibration set (25% of data, stratified).
- Saves calibrated_model.pkl — a sklearn CalibratedClassifierCV wrapper
  with the same predict / predict_proba interface as XGBClassifier.
- Saves calibration_results.json — reliability diagram data (fraction of
  positives vs mean predicted probability, per class) for dissertation figures.

Usage
-----
    cd ImpactTracker
    python ml/calibrate_model.py

Outputs
-------
    ml/calibrated_model.pkl
    ml/calibration_results.json
"""
import os
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.model_selection import train_test_split

# ── Paths ────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

ENCODERS_DIR    = os.path.join(_HERE, "encoders")
MODEL_PATH      = os.path.join(_HERE, "xgb_model.json")
DATA_PATH       = os.path.join(_ROOT, "common", "data", "csv", "expanded_eco_dataset.csv")
OUTPUT_MODEL    = os.path.join(_HERE, "calibrated_model.pkl")
OUTPUT_METRICS  = os.path.join(_HERE, "calibration_results.json")

# Class order matches label_encoder.pkl
GRADE_CLASSES = ["A", "A+", "B", "C", "D", "E", "F"]


def _load_encoders() -> dict:
    encoders = {}
    for name, filename in [
        ("material",  "material_encoder.pkl"),
        ("transport", "transport_encoder.pkl"),
        ("recycle",   "recycle_encoder.pkl"),
        ("origin",    "origin_encoder.pkl"),
        ("weight_bin","weight_bin_encoder.pkl"),
        ("label",     "label_encoder.pkl"),
    ]:
        path = os.path.join(ENCODERS_DIR, filename)
        if os.path.exists(path):
            encoders[name] = joblib.load(path)
        else:
            print(f"  ⚠️  {filename} not found — using fallback integer 0")
    return encoders


def _safe_enc(val: str, enc, default: str) -> int:
    if enc is None:
        return 0
    for attempt in (str(val).title().strip(), default):
        try:
            return int(enc.transform([attempt])[0])
        except Exception:
            pass
    return 0


def _build_features(df: pd.DataFrame, encoders: dict):
    """Reproduce the 8-feature vector used by the production prediction pipeline."""
    X_rows, y_rows = [], []
    for _, row in df.iterrows():
        mat  = str(row.get("material",      "Other")).title().strip()
        trn  = str(row.get("transport",     "Land")).title().strip()
        rec  = str(row.get("recyclability", "Medium")).title().strip()
        orig = str(row.get("origin",        "Other")).title().strip()
        w    = float(row["weight"]) if pd.notna(row.get("weight")) else 1.0
        w    = max(w, 0.0)

        me = _safe_enc(mat,       encoders.get("material"),  "Other")
        te = _safe_enc(trn,       encoders.get("transport"), "Land")
        re = _safe_enc(rec,       encoders.get("recycle"),   "Medium")
        oe = _safe_enc(orig,      encoders.get("origin"),    "Other")
        wl = float(np.log1p(w))
        # Raw bin integer (0–3), then encode through weight_bin encoder
        wb_raw = 0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3
        wb = _safe_enc(str(wb_raw), encoders.get("weight_bin"), "0")

        X_rows.append([
            me, te, re, oe, wl, wb,
            float(me) * float(te),   # interaction: material × transport
            float(oe) * float(re),   # interaction: origin × recyclability
        ])

        score = str(row.get("true_eco_score", "C")).strip()
        y_rows.append(_safe_enc(score, encoders.get("label"), "C"))

    return np.array(X_rows, dtype=float), np.array(y_rows)


def _reliability_data(y_true, y_proba, label_classes) -> dict:
    """Compute reliability diagram data per class (for dissertation figures)."""
    results = {}
    for i, grade in enumerate(label_classes):
        if i >= y_proba.shape[1]:
            break
        binary = (y_true == i).astype(int)
        prob   = y_proba[:, i]
        try:
            frac_pos, mean_pred = calibration_curve(binary, prob, n_bins=10)
            results[grade] = {
                "fraction_positive": frac_pos.tolist(),
                "mean_predicted":    mean_pred.tolist(),
            }
        except Exception:
            pass
    return results


def main():
    print("=" * 60)
    print("Eco-grade model probability calibration")
    print("=" * 60)

    # ── Load encoders ────────────────────────────────────────────
    print("\n[1/5] Loading production encoders…")
    encoders = _load_encoders()
    label_enc = encoders.get("label")
    label_classes = list(label_enc.classes_) if label_enc else GRADE_CLASSES

    # ── Load and filter training data ────────────────────────────
    print(f"\n[2/5] Loading dataset from {DATA_PATH}…")
    df = pd.read_csv(DATA_PATH)
    valid_grades = {"A+", "A", "B", "C", "D", "E", "F"}
    df = df[df["true_eco_score"].isin(valid_grades)].dropna(
        subset=["true_eco_score", "weight"]
    ).reset_index(drop=True)
    print(f"      {len(df):,} rows after filtering")

    # ── Build feature matrix ─────────────────────────────────────
    print("\n[3/5] Encoding features (matching production pipeline)…")
    X, y = _build_features(df, encoders)

    # Hold out 25% as calibration set (stratified)
    X_main, X_cal, y_main, y_cal = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    print(f"      Calibration set: {len(X_cal):,} samples")

    # ── Load pre-trained XGBoost model ───────────────────────────
    print(f"\n[4/5] Loading XGBoost model from {MODEL_PATH}…")
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(MODEL_PATH)

    # Measure raw confidence distribution
    raw_proba    = xgb_model.predict_proba(X_cal)
    raw_max      = np.max(raw_proba, axis=1)
    raw_mean     = float(raw_max.mean())
    raw_over90   = float((raw_max > 0.90).mean())
    print(f"      Raw model  — mean max confidence: {raw_mean:.1%},  "
          f">90%: {raw_over90:.1%}")

    # ── Fit isotonic calibration ──────────────────────────────────
    # cv='prefit' — model is already trained; only fit the isotonic mapping.
    print("\n[5/5] Fitting isotonic calibration on held-out set…")
    calibrated = CalibratedClassifierCV(xgb_model, method="isotonic", cv="prefit")
    calibrated.fit(X_cal, y_cal)

    # Measure calibrated confidence distribution
    cal_proba  = calibrated.predict_proba(X_cal)
    cal_max    = np.max(cal_proba, axis=1)
    cal_mean   = float(cal_max.mean())
    cal_over90 = float((cal_max > 0.90).mean())
    print(f"      Calibrated — mean max confidence: {cal_mean:.1%},  "
          f">90%: {cal_over90:.1%}")

    # Check accuracy didn't degrade
    raw_preds  = xgb_model.predict(X_cal)
    cal_preds  = calibrated.predict(X_cal)
    raw_acc  = float(np.mean(raw_preds  == y_cal))
    cal_acc  = float(np.mean(cal_preds  == y_cal))
    print(f"      Raw accuracy: {raw_acc:.1%}  →  Calibrated accuracy: {cal_acc:.1%}")

    # ── Save calibrated model ─────────────────────────────────────
    joblib.dump(calibrated, OUTPUT_MODEL)
    print(f"\n✅ Calibrated model saved → {OUTPUT_MODEL}")

    # ── Save calibration metrics ──────────────────────────────────
    results = {
        "method":               "isotonic_regression",
        "calibration_set_size": int(len(X_cal)),
        "label_classes":        label_classes,
        "raw_model": {
            "mean_max_confidence": raw_mean,
            "pct_over_90":         raw_over90,
            "accuracy":            raw_acc,
            "reliability_data":    _reliability_data(y_cal, raw_proba,  label_classes),
        },
        "calibrated_model": {
            "mean_max_confidence": cal_mean,
            "pct_over_90":         cal_over90,
            "accuracy":            cal_acc,
            "reliability_data":    _reliability_data(y_cal, cal_proba, label_classes),
        },
    }
    with open(OUTPUT_METRICS, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"✅ Calibration metrics saved → {OUTPUT_METRICS}")

    print("\n" + "=" * 60)
    print(f"  Mean max confidence:  {raw_mean:.1%}  →  {cal_mean:.1%}")
    print(f"  Predictions >90% conf:{raw_over90:.1%}  →  {cal_over90:.1%}")
    print(f"  Accuracy:             {raw_acc:.1%}  →  {cal_acc:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
