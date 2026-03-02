#!/usr/bin/env python3
"""
ML rigor pipeline for ImpactTracker.

What this adds:
- Stratified cross-validation comparison (XGBoost vs RandomForest)
- Fold-level metrics for reproducible reporting
- Probability quality metrics (multiclass Brier score, ECE)
- Statistical significance test on fold F1-macro
- Optional probability calibration assessment for XGBoost

Usage:
  python ml/evaluation/ml_rigor_pipeline.py --max-rows 30000
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

import xgboost as xgb


RANDOM_STATE = 42


@dataclass
class PreparedData:
    X: np.ndarray
    y: np.ndarray
    feature_names: List[str]
    label_encoder: LabelEncoder


def resolve_dataset_path(project_root: Path) -> Path:
    candidates = [
        project_root / "common" / "data" / "csv" / "enhanced_amazon_dataset.csv",
        project_root / "common" / "data" / "csv" / "expanded_eco_dataset.csv",
        project_root / "common" / "data" / "csv" / "enhanced_eco_dataset.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No supported dataset found in common/data/csv")


def _normalize_string_col(series: pd.Series) -> pd.Series:
    return series.astype(str).fillna("Unknown").str.strip().str.title()


def _compute_multiclass_brier(y_true: np.ndarray, y_proba: np.ndarray, n_classes: int) -> float:
    one_hot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_proba - one_hot) ** 2, axis=1)))


def _compute_ece(y_true: np.ndarray, y_proba: np.ndarray, bins: int = 10) -> float:
    confidences = np.max(y_proba, axis=1)
    predictions = np.argmax(y_proba, axis=1)
    accuracies = (predictions == y_true).astype(float)

    bin_edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0

    for left, right in zip(bin_edges[:-1], bin_edges[1:]):
        in_bin = (confidences > left) & (confidences <= right)
        if not np.any(in_bin):
            continue
        prop = np.mean(in_bin)
        avg_conf = float(np.mean(confidences[in_bin]))
        avg_acc = float(np.mean(accuracies[in_bin]))
        ece += prop * abs(avg_conf - avg_acc)

    return float(ece)


def prepare_dataset(dataset_path: Path, max_rows: int | None = None) -> PreparedData:
    df = pd.read_csv(dataset_path)

    required_columns = ["material", "transport", "recyclability", "origin", "weight", "true_eco_score"]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df.dropna(subset=["true_eco_score", "weight"]).copy()
    df = df[df["true_eco_score"].astype(str).isin(["A+", "A", "B", "C", "D", "E", "F"])]

    if max_rows and max_rows > 0 and len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=RANDOM_STATE)

    for column in ["material", "transport", "recyclability", "origin"]:
        df[column] = _normalize_string_col(df[column])

    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df = df.dropna(subset=["weight"]).copy()

    df["weight_log"] = np.log1p(df["weight"])
    df["weight_bin"] = pd.cut(df["weight"], bins=[0, 0.5, 2, 10, 100, np.inf], labels=[0, 1, 2, 3, 4])
    df["weight_bin"] = df["weight_bin"].astype(str)

    enc_material = LabelEncoder()
    enc_transport = LabelEncoder()
    enc_recyclability = LabelEncoder()
    enc_origin = LabelEncoder()
    enc_weight_bin = LabelEncoder()
    enc_label = LabelEncoder()

    df["material_encoded"] = enc_material.fit_transform(df["material"])
    df["transport_encoded"] = enc_transport.fit_transform(df["transport"])
    df["recyclability_encoded"] = enc_recyclability.fit_transform(df["recyclability"])
    df["origin_encoded"] = enc_origin.fit_transform(df["origin"])
    df["weight_bin_encoded"] = enc_weight_bin.fit_transform(df["weight_bin"])
    df["label_encoded"] = enc_label.fit_transform(df["true_eco_score"])

    feature_names = [
        "material_encoded",
        "transport_encoded",
        "recyclability_encoded",
        "origin_encoded",
        "weight_log",
        "weight_bin_encoded",
    ]

    X = df[feature_names].to_numpy(dtype=float)
    y = df["label_encoded"].to_numpy(dtype=int)

    return PreparedData(X=X, y=y, feature_names=feature_names, label_encoder=enc_label)


def build_models(n_classes: int) -> Dict[str, object]:
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    xgb_model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=n_classes,
        n_estimators=350,
        max_depth=7,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.5,
        random_state=RANDOM_STATE,
        eval_metric="mlogloss",
        tree_method="hist",
    )

    return {"random_forest": rf, "xgboost": xgb_model}


def evaluate_models_cv(data: PreparedData, folds: int = 5) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    models = build_models(n_classes=len(np.unique(data.y)))

    rows: List[Dict[str, float | int | str]] = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(data.X, data.y), start=1):
        X_train, X_test = data.X[train_idx], data.X[test_idx]
        y_train, y_test = data.y[train_idx], data.y[test_idx]

        for model_name, model in models.items():
            if model_name == "xgboost":
                sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
                model.fit(X_train, y_train, sample_weight=sample_weight)
            else:
                model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)

            row = {
                "model": model_name,
                "fold": fold_idx,
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
                "f1_weighted": float(f1_score(y_test, y_pred, average="weighted")),
                "log_loss": float(log_loss(y_test, y_proba, labels=np.arange(len(np.unique(data.y))))),
                "brier_multiclass": _compute_multiclass_brier(y_test, y_proba, n_classes=len(np.unique(data.y))),
                "ece": _compute_ece(y_test, y_proba, bins=10),
            }
            rows.append(row)

    fold_df = pd.DataFrame(rows)

    summary: Dict[str, Dict[str, float]] = {}
    for model_name, group in fold_df.groupby("model"):
        summary[model_name] = {
            "accuracy_mean": float(group["accuracy"].mean()),
            "accuracy_std": float(group["accuracy"].std(ddof=0)),
            "f1_macro_mean": float(group["f1_macro"].mean()),
            "f1_macro_std": float(group["f1_macro"].std(ddof=0)),
            "f1_weighted_mean": float(group["f1_weighted"].mean()),
            "log_loss_mean": float(group["log_loss"].mean()),
            "brier_multiclass_mean": float(group["brier_multiclass"].mean()),
            "ece_mean": float(group["ece"].mean()),
        }

    return fold_df, summary


def evaluate_calibration(data: PreparedData) -> Dict[str, float]:
    X_train, X_test, y_train, y_test = train_test_split(
        data.X, data.y, test_size=0.2, random_state=RANDOM_STATE, stratify=data.y
    )

    base_xgb = build_models(n_classes=len(np.unique(data.y)))["xgboost"]
    sample_weight = compute_sample_weight(class_weight="balanced", y=y_train)
    base_xgb.fit(X_train, y_train, sample_weight=sample_weight)
    base_proba = base_xgb.predict_proba(X_test)
    base_pred = base_xgb.predict(X_test)

    calibrated = CalibratedClassifierCV(base_xgb, cv=3, method="sigmoid")
    calibrated.fit(X_train, y_train)
    cal_proba = calibrated.predict_proba(X_test)
    cal_pred = calibrated.predict(X_test)

    n_classes = len(np.unique(data.y))

    return {
        "raw_accuracy": float(accuracy_score(y_test, base_pred)),
        "calibrated_accuracy": float(accuracy_score(y_test, cal_pred)),
        "raw_f1_macro": float(f1_score(y_test, base_pred, average="macro")),
        "calibrated_f1_macro": float(f1_score(y_test, cal_pred, average="macro")),
        "raw_log_loss": float(log_loss(y_test, base_proba, labels=np.arange(n_classes))),
        "calibrated_log_loss": float(log_loss(y_test, cal_proba, labels=np.arange(n_classes))),
        "raw_brier": _compute_multiclass_brier(y_test, base_proba, n_classes),
        "calibrated_brier": _compute_multiclass_brier(y_test, cal_proba, n_classes),
        "raw_ece": _compute_ece(y_test, base_proba, bins=10),
        "calibrated_ece": _compute_ece(y_test, cal_proba, bins=10),
    }


def statistical_test(fold_df: pd.DataFrame) -> Dict[str, float | str | None]:
    rf = fold_df[fold_df["model"] == "random_forest"].sort_values("fold")["f1_macro"].to_numpy()
    xgb_scores = fold_df[fold_df["model"] == "xgboost"].sort_values("fold")["f1_macro"].to_numpy()

    if len(rf) != len(xgb_scores) or len(rf) == 0:
        return {"test": "unavailable", "p_value": None, "effect": None, "winner": None}

    t_stat, t_p = ttest_rel(xgb_scores, rf)

    try:
        w_stat, w_p = wilcoxon(xgb_scores, rf)
    except ValueError:
        w_p = None

    delta = float(np.mean(xgb_scores - rf))
    winner = "xgboost" if delta > 0 else "random_forest"

    return {
        "test": "paired_t_test",
        "p_value": float(t_p),
        "wilcoxon_p_value": float(w_p) if w_p is not None else None,
        "mean_f1_macro_delta_xgb_minus_rf": delta,
        "winner": winner,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML rigor evaluation pipeline")
    parser.add_argument("--max-rows", type=int, default=0, help="Optional row cap for faster iteration")
    parser.add_argument("--folds", type=int, default=5, help="Number of stratified CV folds")
    args = parser.parse_args()

    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    dataset_path = resolve_dataset_path(project_root)

    max_rows = args.max_rows if args.max_rows and args.max_rows > 0 else None
    data = prepare_dataset(dataset_path, max_rows=max_rows)

    fold_df, summary = evaluate_models_cv(data, folds=args.folds)
    calibration = evaluate_calibration(data)
    stats = statistical_test(fold_df)

    reports_dir = project_root / "ml" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    fold_path = reports_dir / "ml_rigor_cv_folds.csv"
    fold_df.to_csv(fold_path, index=False)

    report = {
        "dataset": {
            "path": str(dataset_path),
            "rows_used": int(len(data.y)),
            "features": data.feature_names,
            "classes": list(map(str, data.label_encoder.classes_)),
            "folds": args.folds,
        },
        "model_summary": summary,
        "calibration": calibration,
        "statistical_test": stats,
    }

    report_path = reports_dir / "ml_rigor_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("✅ ML rigor pipeline complete")
    print(f"📄 Fold metrics: {fold_path}")
    print(f"📄 Summary report: {report_path}")
    print("\n=== Quick Summary ===")
    for model_name, metrics in summary.items():
        print(
            f"{model_name}: F1-macro={metrics['f1_macro_mean']:.4f}±{metrics['f1_macro_std']:.4f}, "
            f"Accuracy={metrics['accuracy_mean']:.4f}, ECE={metrics['ece_mean']:.4f}"
        )
    print(
        f"Calibration (XGB): raw ECE={calibration['raw_ece']:.4f} -> calibrated ECE={calibration['calibrated_ece']:.4f}"
    )


if __name__ == "__main__":
    main()
