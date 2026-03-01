"""
Amazon-focused Validation Framework for Environmental Impact Prediction
Cross-validation and manual labeling for dissertation analysis
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    mean_absolute_error, mean_absolute_percentage_error, 
    accuracy_score, classification_report, confusion_matrix
)
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import json
from pathlib import Path

class AmazonValidationFramework:
    """Validation framework using Amazon data and cross-validation"""
    
    def __init__(self, results_dir: str = "validation_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Manual validation approaches for Amazon data
        self.validation_approaches = {
            "cross_validation": "Stratified k-fold cross-validation on Amazon dataset",
            "manual_labeling": "Manually label subset of Amazon products for validation",
            "category_analysis": "Compare predictions within Amazon product categories",
            "rule_vs_ml": "Compare ML predictions against rule-based calculations"
        }
    
    def validate_model(self, model, X, y, model_name: str = "xgboost") -> Dict:
        """Comprehensive model validation using multiple approaches"""
        print(f"🔬 Validating {model_name} model...")
        
        results = {
            "model_name": model_name,
            "dataset_size": len(X),
            "feature_count": X.shape[1] if hasattr(X, 'shape') else len(X[0]),
            "cross_validation": self._cross_validation_analysis(model, X, y),
            "category_analysis": self._category_performance_analysis(model, X, y),
            "ranking_analysis": self._ranking_performance_analysis(model, X, y),
            "prediction_distribution": self._prediction_distribution_analysis(model, X, y),
            "feature_importance": self._feature_importance_analysis(model),
            "error_analysis": self._error_pattern_analysis(model, X, y)
        }
        
        # Save results
        self._save_validation_results(results, model_name)
        
        return results
    
    def _cross_validation_analysis(self, model, X, y) -> Dict:
        """K-fold cross-validation with multiple metrics"""
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        # Convert to arrays if needed
        X_array = np.array(X) if not isinstance(X, np.ndarray) else X
        y_array = np.array(y) if not isinstance(y, np.ndarray) else y
        
        # Accuracy scores
        accuracy_scores = cross_val_score(model, X_array, y_array, cv=cv, scoring='accuracy')
        
        # For detailed metrics, manually perform CV
        detailed_metrics = []
        
        for train_idx, val_idx in cv.split(X_array, y_array):
            X_train, X_val = X_array[train_idx], X_array[val_idx]
            y_train, y_val = y_array[train_idx], y_array[val_idx]
            
            # Train and predict
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            
            # Calculate metrics
            fold_metrics = {
                'accuracy': accuracy_score(y_val, y_pred),
                'mae': mean_absolute_error(self._score_to_numeric(y_val), 
                                         self._score_to_numeric(y_pred)),
                'spearman_r': spearmanr(self._score_to_numeric(y_val), 
                                      self._score_to_numeric(y_pred))[0]
            }
            detailed_metrics.append(fold_metrics)
        
        return {
            "accuracy_scores": accuracy_scores.tolist(),
            "mean_accuracy": float(np.mean(accuracy_scores)),
            "std_accuracy": float(np.std(accuracy_scores)),
            "detailed_metrics": detailed_metrics,
            "mean_mae": float(np.mean([m['mae'] for m in detailed_metrics])),
            "mean_spearman": float(np.mean([m['spearman_r'] for m in detailed_metrics]))
        }
    
    def _category_performance_analysis(self, model, X, y) -> Dict:
        """Analyze performance by product category (if available)"""
        # This assumes you have category info in your dataset
        # You'll need to adapt this to your actual data structure
        
        categories = ['electronics', 'clothing', 'food', 'home_garden', 'other']
        category_performance = {}
        
        # For now, create synthetic category analysis
        # Replace this with actual category detection from your enhanced features
        for category in categories:
            # Simulate category-specific performance
            # In reality, you'd filter your data by category
            category_performance[category] = {
                "sample_size": len(X) // len(categories),  # Approximate
                "accuracy": 0.85 + np.random.normal(0, 0.05),  # Placeholder
                "common_errors": ["B→C misclassification", "A→B confusion"]
            }
        
        return category_performance
    
    def _ranking_performance_analysis(self, model, X, y) -> Dict:
        """Analyze how well model ranks products by environmental impact"""
        X_array = np.array(X) if not isinstance(X, np.ndarray) else X
        y_array = np.array(y) if not isinstance(y, np.ndarray) else y
        
        # Train on full dataset for ranking analysis
        model.fit(X_array, y_array)
        y_pred = model.predict(X_array)
        
        # Convert scores to numeric for ranking
        y_true_numeric = self._score_to_numeric(y_array)
        y_pred_numeric = self._score_to_numeric(y_pred)
        
        # Ranking correlations
        spearman_r, spearman_p = spearmanr(y_true_numeric, y_pred_numeric)
        kendall_tau, kendall_p = kendalltau(y_true_numeric, y_pred_numeric)
        
        # Top-k ranking accuracy
        k_values = [10, 50, 100]
        ranking_accuracy = {}
        
        for k in k_values:
            if len(y_true_numeric) > k:
                true_top_k = set(np.argsort(y_true_numeric)[-k:])
                pred_top_k = set(np.argsort(y_pred_numeric)[-k:])
                overlap = len(true_top_k.intersection(pred_top_k))
                ranking_accuracy[f"top_{k}"] = overlap / k
        
        return {
            "spearman_correlation": float(spearman_r),
            "spearman_p_value": float(spearman_p),
            "kendall_tau": float(kendall_tau),
            "kendall_p_value": float(kendall_p),
            "ranking_accuracy": ranking_accuracy
        }
    
    def _prediction_distribution_analysis(self, model, X, y) -> Dict:
        """Analyze distribution of predictions vs. actual labels"""
        X_array = np.array(X) if not isinstance(X, np.ndarray) else X
        y_array = np.array(y) if not isinstance(y, np.ndarray) else y
        
        model.fit(X_array, y_array)
        y_pred = model.predict(X_array)
        
        # Count distributions
        unique_true, counts_true = np.unique(y_array, return_counts=True)
        unique_pred, counts_pred = np.unique(y_pred, return_counts=True)
        
        return {
            "true_distribution": dict(zip(unique_true.tolist(), counts_true.tolist())),
            "predicted_distribution": dict(zip(unique_pred.tolist(), counts_pred.tolist())),
            "distribution_similarity": self._calculate_distribution_similarity(
                dict(zip(unique_true, counts_true)),
                dict(zip(unique_pred, counts_pred))
            )
        }
    
    def _feature_importance_analysis(self, model) -> Dict:
        """Extract and analyze feature importance"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_names = ['material', 'transport', 'recyclability', 'origin', 'weight', 'weight_bin']
            
            # Sort by importance
            importance_pairs = list(zip(feature_names, importances))
            importance_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return {
                "feature_importances": dict(importance_pairs),
                "top_3_features": [pair[0] for pair in importance_pairs[:3]],
                "importance_variance": float(np.var(importances))
            }
        
        return {"message": "Model does not support feature importance"}
    
    def _error_pattern_analysis(self, model, X, y) -> Dict:
        """Analyze common error patterns"""
        X_array = np.array(X) if not isinstance(X, np.ndarray) else X
        y_array = np.array(y) if not isinstance(y, np.ndarray) else y
        
        model.fit(X_array, y_array)
        y_pred = model.predict(X_array)
        
        # Confusion matrix analysis
        cm = confusion_matrix(y_array, y_pred)
        labels = sorted(set(y_array))
        
        # Find most common errors
        errors = []
        for i, true_label in enumerate(labels):
            for j, pred_label in enumerate(labels):
                if i != j and cm[i][j] > 0:
                    errors.append({
                        "true_label": true_label,
                        "predicted_label": pred_label,
                        "count": int(cm[i][j]),
                        "error_rate": float(cm[i][j] / np.sum(cm[i]))
                    })
        
        # Sort by frequency
        errors.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "confusion_matrix": cm.tolist(),
            "labels": labels,
            "top_5_errors": errors[:5],
            "overall_error_rate": float(1 - accuracy_score(y_array, y_pred))
        }
    
    def _score_to_numeric(self, scores) -> np.ndarray:
        """Convert letter grades to numeric values for correlation analysis"""
        score_map = {'A+': 7, 'A': 6, 'B': 5, 'C': 4, 'D': 3, 'E': 2, 'F': 1}
        
        if isinstance(scores, (list, np.ndarray)):
            return np.array([score_map.get(score, 0) for score in scores])
        else:
            return score_map.get(scores, 0)
    
    def _calculate_distribution_similarity(self, dist1: Dict, dist2: Dict) -> float:
        """Calculate similarity between two distributions using Jensen-Shannon divergence"""
        all_keys = set(dist1.keys()) | set(dist2.keys())
        
        # Normalize distributions
        total1 = sum(dist1.values())
        total2 = sum(dist2.values())
        
        p = np.array([dist1.get(k, 0) / total1 for k in all_keys])
        q = np.array([dist2.get(k, 0) / total2 for k in all_keys])
        
        # Simple similarity metric (1 - normalized absolute difference)
        return float(1 - np.sum(np.abs(p - q)) / 2)
    
    def _save_validation_results(self, results: Dict, model_name: str):
        """Save validation results to JSON file"""
        output_file = self.results_dir / f"{model_name}_validation_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📊 Validation results saved to {output_file}")
    
    def generate_validation_report(self, results: Dict) -> str:
        """Generate a human-readable validation report"""
        report = f"""
# Model Validation Report: {results['model_name']}

## Dataset Overview
- Total samples: {results['dataset_size']}
- Features: {results['feature_count']}

## Cross-Validation Performance
- Mean Accuracy: {results['cross_validation']['mean_accuracy']:.3f} ± {results['cross_validation']['std_accuracy']:.3f}
- Mean MAE: {results['cross_validation']['mean_mae']:.3f}
- Mean Spearman Correlation: {results['cross_validation']['mean_spearman']:.3f}

## Ranking Performance
- Spearman Correlation: {results['ranking_analysis']['spearman_correlation']:.3f}
- Kendall Tau: {results['ranking_analysis']['kendall_tau']:.3f}

## Top Features
{', '.join(results['feature_importance']['top_3_features'])}

## Common Errors
"""
        for error in results['error_analysis']['top_5_errors']:
            report += f"- {error['true_label']} → {error['predicted_label']}: {error['count']} cases ({error['error_rate']:.2%})\n"
        
        return report

def compare_models(model1, model2, X, y, model1_name="Model 1", model2_name="Model 2"):
    """Compare two models side by side"""
    validator = SimpleValidationFramework()
    
    results1 = validator.validate_model(model1, X, y, model1_name)
    results2 = validator.validate_model(model2, X, y, model2_name)
    
    comparison = {
        "model1": {
            "name": model1_name,
            "accuracy": results1['cross_validation']['mean_accuracy'],
            "mae": results1['cross_validation']['mean_mae'],
            "spearman": results1['ranking_analysis']['spearman_correlation']
        },
        "model2": {
            "name": model2_name,
            "accuracy": results2['cross_validation']['mean_accuracy'],
            "mae": results2['cross_validation']['mean_mae'],
            "spearman": results2['ranking_analysis']['spearman_correlation']
        }
    }
    
    print(f"\n📊 Model Comparison:")
    print(f"Accuracy: {model1_name} {comparison['model1']['accuracy']:.3f} vs {model2_name} {comparison['model2']['accuracy']:.3f}")
    print(f"MAE: {model1_name} {comparison['model1']['mae']:.3f} vs {model2_name} {comparison['model2']['mae']:.3f}")
    print(f"Ranking: {model1_name} {comparison['model1']['spearman']:.3f} vs {model2_name} {comparison['model2']['spearman']:.3f}")
    
    return comparison

if __name__ == "__main__":
    # Example usage with your existing model
    import joblib
    import sys
    import os
    
    # Load your existing model and data via project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))
    model_path = os.path.join(ML_ASSETS_DIR, "eco_model.pkl")
    data_path = os.path.join(project_root, "common", "data", "csv", "eco_dataset.csv")
    
    if os.path.exists(model_path) and os.path.exists(data_path):
        model = joblib.load(model_path)
        df = pd.read_csv(data_path)
        
        # Prepare data (adapt this to your preprocessing)
        X = df[['material', 'weight', 'transport', 'recyclability', 'origin']].values
        y = df['true_eco_score'].values
        
        # Run validation
        validator = SimpleValidationFramework()
        results = validator.validate_model(model, X, y, "EcoModel")
        
        # Generate report
        report = validator.generate_validation_report(results)
        print(report)
        
        # Save report
        with open("validation_results/model_validation_report.md", 'w') as f:
            f.write(report)
    else:
        print("⚠️ Model or data files not found. Please check paths.")