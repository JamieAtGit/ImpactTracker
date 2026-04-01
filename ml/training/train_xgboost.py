import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, RandomizedSearchCV, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from scipy import stats
from scipy.stats import friedmanchisquare
from imblearn.over_sampling import SMOTE
from collections import Counter
import json

# === Paths ===
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))
model_dir = ML_ASSETS_DIR
encoders_dir = os.path.join(ML_ASSETS_DIR, "xgb_encoders")
os.makedirs(model_dir, exist_ok=True)
os.makedirs(encoders_dir, exist_ok=True)

# CSV path — override via environment variable or falls back to the primary dataset
csv_path = os.environ.get("TRAINING_CSV", os.path.join(ML_ASSETS_DIR, "eco_dataset.csv"))

# === Load and preprocess enhanced dataset ===
df = pd.read_csv(csv_path)  # Load with headers
print(f"📊 Loaded enhanced dataset with {len(df)} rows and {len(df.columns)} columns")
print(f"📋 Columns: {list(df.columns)}")

# Filter for valid eco scores and remove NaN
df = df[df["true_eco_score"].isin(["A+", "A", "B", "C", "D", "E", "F"])].dropna(subset=["true_eco_score"])
print(f"📊 After filtering: {len(df)} rows")

# === Clean up string fields
for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.title().str.strip()

# === Weight prep
df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
df.dropna(subset=["weight"], inplace=True)
df["weight_log"] = np.log1p(df["weight"])
df["weight_bin"] = pd.cut(df["weight"], bins=[0, 0.5, 2, 10, 100], labels=[0, 1, 2, 3])

# === Label encoding for original features
encoders = {
    'material': LabelEncoder(),
    'transport': LabelEncoder(),
    'recyclability': LabelEncoder(),
    'origin': LabelEncoder(),
    'label': LabelEncoder(),
    'weight_bin': LabelEncoder()
}

for key in encoders:
    col = key if key != "label" else "true_eco_score"
    df[f"{key}_encoded"] = encoders[key].fit_transform(df[col].astype(str))

# === Encode new categorical features if they exist
if 'packaging_type' in df.columns:
    encoders['packaging_type'] = LabelEncoder()
    df['packaging_type_encoded'] = encoders['packaging_type'].fit_transform(df['packaging_type'].astype(str))

if 'size_category' in df.columns:
    encoders['size_category'] = LabelEncoder()
    df['size_category_encoded'] = encoders['size_category'].fit_transform(df['size_category'].astype(str))

if 'quality_level' in df.columns:
    encoders['quality_level'] = LabelEncoder()
    df['quality_level_encoded'] = encoders['quality_level'].fit_transform(df['quality_level'].astype(str))

# === Enhanced feature selection
feature_cols = [
    "material_encoded",
    "transport_encoded", 
    "recyclability_encoded",
    "origin_encoded",
    "weight_log",
    "weight_bin_encoded"
]

# Add enhanced features if they exist
if 'packaging_type_encoded' in df.columns:
    feature_cols.append('packaging_type_encoded')
if 'size_category_encoded' in df.columns:
    feature_cols.append('size_category_encoded')
if 'quality_level_encoded' in df.columns:
    feature_cols.append('quality_level_encoded')
if 'pack_size' in df.columns:
    df['pack_size'] = pd.to_numeric(df['pack_size'], errors='coerce').fillna(1)
    feature_cols.append('pack_size')
if 'material_confidence' in df.columns:
    feature_cols.append('material_confidence')

print(f"🎯 Using {len(feature_cols)} features: {feature_cols}")
X = df[feature_cols].astype(float)
y = df["label_encoded"]

# === Save feature order
with open(os.path.join(model_dir, "feature_order.json"), "w") as f:
    json.dump(feature_cols, f)

# === Balance the data
X_balanced, y_balanced = SMOTE(random_state=42).fit_resample(X, y)

# === Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, stratify=y_balanced, random_state=42
)

# === Class weights
counter = Counter(y_balanced)
total = sum(counter.values())
class_weights = {cls: total / count for cls, count in counter.items()}
sample_weights = [class_weights[i] for i in y_train]

# === Enhanced ML Validation with Statistical Rigor ===
print("\n🧪 STATISTICAL VALIDATION PHASE")
print("=" * 50)

# 1. K-Fold Cross-Validation (Academic Standard)
skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
base_model = xgb.XGBClassifier(
    use_label_encoder=False,
    eval_metric="mlogloss",
    n_estimators=300,
    max_depth=7,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    random_state=42
)

# Cross-validation scores
cv_scores = cross_val_score(base_model, X_balanced, y_balanced, cv=skf, scoring='f1_macro')
print(f"\n📊 10-Fold Cross-Validation Results:")
print(f"   Mean F1: {cv_scores.mean():.4f} (±{cv_scores.std() * 2:.4f})")
print(f"   Individual folds: {[round(score, 4) for score in cv_scores]}")

# Statistical significance test
if cv_scores.std() > 0:
    t_stat, p_value = stats.ttest_1samp(cv_scores, 0.5)  # Test against random chance
    print(f"   Statistical significance: p={p_value:.6f} {'✅ Significant' if p_value < 0.05 else '❌ Not significant'}")

# 2. Hyperparameter Optimization with Cross-Validation
print(f"\n🔧 Hyperparameter Optimization:")
params = {
    "n_estimators": [200, 300, 400],
    "max_depth": [6, 7, 8],
    "learning_rate": [0.05, 0.08, 0.1],
    "subsample": [0.7, 0.85, 0.9],
    "colsample_bytree": [0.7, 0.85, 0.9]
}

search = RandomizedSearchCV(
    base_model, 
    params, 
    scoring="f1_macro", 
    n_iter=20,  # More thorough search
    cv=5,  # 5-fold for hyperparameter search
    n_jobs=-1,
    random_state=42
)
search.fit(X_train, y_train, sample_weight=sample_weights)
model = search.best_estimator_
print(f"   Best parameters: {search.best_params_}")
print(f"   Best CV score: {search.best_score_:.4f}")

# === Comprehensive Model Evaluation ===
print(f"\n📈 FINAL MODEL EVALUATION")
print("=" * 50)

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)

# Basic metrics
acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average="macro")
f1_weighted = f1_score(y_test, y_pred, average="weighted")
report = classification_report(y_test, y_pred, target_names=encoders['label'].classes_, output_dict=True)

# Confidence intervals for accuracy (Wilson score interval)
n = len(y_test)
p = acc
z = 1.96  # 95% confidence
wilson_center = (p + z**2/(2*n)) / (1 + z**2/n)
wilson_width = z * np.sqrt((p*(1-p) + z**2/(4*n)) / n) / (1 + z**2/n)
conf_lower = wilson_center - wilson_width
conf_upper = wilson_center + wilson_width

print(f"\n🎯 Performance Metrics:")
print(f"   Accuracy: {acc:.4f} (95% CI: [{conf_lower:.4f}, {conf_upper:.4f}])")
print(f"   Macro F1: {f1:.4f}")
print(f"   Weighted F1: {f1_weighted:.4f}")

# Per-class performance
print(f"\n📊 Per-Class Performance:")
for class_name in encoders['label'].classes_:
    if class_name in report:
        precision = report[class_name]['precision']
        recall = report[class_name]['recall']
        f1_class = report[class_name]['f1-score']
        support = report[class_name]['support']
        print(f"   {class_name}: P={precision:.3f}, R={recall:.3f}, F1={f1_class:.3f} (n={support})")

# Feature importance analysis
if hasattr(model, 'feature_importances_'):
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🔍 Top 5 Most Important Features:")
    for idx, row in importance_df.head().iterrows():
        print(f"   {row['feature']:20}: {row['importance']:.4f}")

# === Save model + encoders
joblib.dump(model, os.path.join(model_dir, "eco_model.pkl"))
for name, enc in encoders.items():
    joblib.dump(enc, os.path.join(encoders_dir, f"{name}_encoder.pkl"))

# === Model Comparison & Bias Analysis ===
print(f"\n🔬 BIAS AND ROBUSTNESS ANALYSIS")
print("=" * 50)

# Check for bias across different categories
bias_results = {}

# Origin bias analysis
if 'origin_encoded' in X_test.columns:
    origins = X_test['origin_encoded'].unique()
    origin_performance = {}
    for origin in origins:
        mask = X_test['origin_encoded'] == origin
        if mask.sum() > 5:  # Only analyze if sufficient samples
            origin_acc = accuracy_score(y_test[mask], y_pred[mask])
            origin_name = encoders['origin'].inverse_transform([origin])[0]
            origin_performance[origin_name] = {
                'accuracy': round(origin_acc, 4),
                'sample_count': int(mask.sum())
            }
    
    bias_results['origin_bias'] = origin_performance
    print(f"\n📍 Performance by Origin:")
    for origin, perf in origin_performance.items():
        print(f"   {origin:15}: {perf['accuracy']:.4f} (n={perf['sample_count']})")

# Material bias analysis
if 'material_encoded' in X_test.columns:
    materials = X_test['material_encoded'].unique()
    material_performance = {}
    for material in materials:
        mask = X_test['material_encoded'] == material
        if mask.sum() > 5:
            material_acc = accuracy_score(y_test[mask], y_pred[mask])
            material_name = encoders['material'].inverse_transform([material])[0]
            material_performance[material_name] = {
                'accuracy': round(material_acc, 4),
                'sample_count': int(mask.sum())
            }
    
    bias_results['material_bias'] = material_performance
    print(f"\n🧱 Performance by Material:")
    for material, perf in material_performance.items():
        print(f"   {material:15}: {perf['accuracy']:.4f} (n={perf['sample_count']})")

# === Enhanced Metrics for Academic Rigor ===
enhanced_metrics = {
    # Basic performance
    "accuracy": round(acc, 4),
    "accuracy_95_ci_lower": round(conf_lower, 4),
    "accuracy_95_ci_upper": round(conf_upper, 4),
    "f1_macro": round(f1, 4),
    "f1_weighted": round(f1_weighted, 4),
    
    # Cross-validation results
    "cv_mean_f1": round(cv_scores.mean(), 4),
    "cv_std_f1": round(cv_scores.std(), 4),
    "cv_scores": [round(score, 4) for score in cv_scores],
    
    # Statistical significance
    "statistical_significance_p": round(p_value, 6) if 'p_value' in locals() else None,
    "significantly_better_than_random": p_value < 0.05 if 'p_value' in locals() else None,
    
    # Model details
    "best_hyperparameters": search.best_params_,
    "best_cv_score": round(search.best_score_, 4),
    "feature_count": len(feature_cols),
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    
    # Feature importance
    "feature_importance": importance_df.to_dict('records') if 'importance_df' in locals() else None,
    
    # Bias analysis
    "bias_analysis": bias_results,
    
    # Full classification report
    "detailed_report": report
}

# Save enhanced metrics
with open(os.path.join(model_dir, "xgb_metrics_enhanced.json"), "w") as f:
    json.dump(enhanced_metrics, f, indent=2)

print(f"\n✅ ACADEMIC-GRADE MODEL COMPLETE")
print(f"   📊 10-fold CV F1: {cv_scores.mean():.4f} ±{cv_scores.std()*2:.4f}")
print(f"   🎯 Test Accuracy: {acc:.4f} (95% CI: [{conf_lower:.4f}, {conf_upper:.4f}])")
print(f"   📈 Statistical Significance: {'✅ Yes' if p_value < 0.05 else '❌ No'} (p={p_value:.6f})" if 'p_value' in locals() else "")
print(f"   💾 Enhanced metrics saved to xgb_metrics_enhanced.json")

print("✅ Model, encoders, and metrics saved successfully.")
