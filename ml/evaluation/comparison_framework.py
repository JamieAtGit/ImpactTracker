"""
Amazon Product Analysis: Rule-Based vs ML-Based Environmental Impact Prediction
For dissertation analysis comparing your existing scraping approach with machine learning
"""
import pandas as pd
import numpy as np
import json
import time
import re
import os
import joblib
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

@dataclass
class PredictionResult:
    """Standard format for both rule-based and ML predictions"""
    product_id: str
    eco_score: str
    confidence: float
    co2_kg: float
    processing_time_ms: float
    method: str  # "rule_based" or "ml_based"
    features_used: Dict
    explanation: str

class AmazonComparisonFramework:
    """Framework for comparing your Amazon scraping rules vs ML approaches"""
    
    def __init__(self, results_dir: str = "comparison_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        # Paths and encoder loading for RF model compatibility
        script_dir = os.path.dirname(__file__)
        self.project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
        self.ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(self.project_root, "ml"))
        self.encoders_dir = os.path.join(self.ML_ASSETS_DIR, "encoders")
        self.rf_encoders = {}
        self.feature_cols = [
            "material_encoded",
            "transport_encoded",
            "recycle_encoded",
            "origin_encoded",
            "weight_log",
            "weight_bin_encoded"
        ]
        self._load_rf_encoders()
        
        self.metrics = {
            "accuracy": [],
            "consistency": [],
            "speed": [],
            "interpretability": [],
            "coverage": []
        }
    
    def run_comparative_analysis(self, 
                                test_products: List[Dict],
                                rule_based_predictor: Callable,
                                ml_model,
                                ground_truth: Dict = None) -> Dict:
        """Run comprehensive comparison between both approaches"""
        
        print("🔬 Running Rule-Based vs ML Comparison...")
        
        # Collect predictions from both methods
        rule_predictions = self._run_rule_based_predictions(test_products, rule_based_predictor)
        ml_predictions = self._run_ml_predictions(test_products, ml_model)
        
        # Core comparison metrics
        comparison_results = {
            "dataset_info": {
                "total_products": len(test_products),
                "analysis_date": str(pd.Timestamp.now()),
                "product_categories": self._analyze_product_categories(test_products)
            },
            "performance_comparison": self._compare_performance(rule_predictions, ml_predictions, ground_truth),
            "consistency_analysis": self._analyze_consistency(rule_predictions, ml_predictions),
            "speed_comparison": self._compare_speed(rule_predictions, ml_predictions),
            "interpretability_analysis": self._analyze_interpretability(rule_predictions, ml_predictions),
            "coverage_analysis": self._analyze_coverage(rule_predictions, ml_predictions),
            "agreement_analysis": self._analyze_agreement(rule_predictions, ml_predictions),
            "error_pattern_analysis": self._analyze_error_patterns(rule_predictions, ml_predictions, ground_truth),
            "use_case_recommendations": self._generate_use_case_recommendations(rule_predictions, ml_predictions)
        }
        
        # Save detailed results
        self._save_comparison_results(comparison_results)
        
        # Generate visualization
        self._create_comparison_visualizations(rule_predictions, ml_predictions)
        
        return comparison_results
    
    def _run_rule_based_predictions(self, products: List[Dict], predictor: Callable) -> List[PredictionResult]:
        """Run rule-based predictions and collect timing/explanation data"""
        predictions = []
        
        print("  🔧 Running rule-based predictions...")
        
        for i, product in enumerate(products):
            start_time = time.perf_counter()
            
            try:
                # Your existing rule-based calculation
                result = predictor(product)
                
                processing_time = (time.perf_counter() - start_time) * 1000
                
                prediction = PredictionResult(
                    product_id=product.get('id', f"product_{i}"),
                    eco_score=result.get('eco_score', 'C'),
                    confidence=result.get('confidence', 0.7),  # Rule-based has fixed confidence
                    co2_kg=result.get('co2_kg', 0.0),
                    processing_time_ms=processing_time,
                    method="rule_based",
                    features_used=result.get('features_used', {}),
                    explanation=self._generate_rule_explanation(result)
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                print(f"    ⚠️ Rule-based prediction failed for product {i}: {e}")
                # Add failed prediction
                predictions.append(PredictionResult(
                    product_id=f"product_{i}",
                    eco_score="F",
                    confidence=0.0,
                    co2_kg=0.0,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    method="rule_based",
                    features_used={},
                    explanation="Prediction failed"
                ))
        
        return predictions
    
    def _run_ml_predictions(self, products: List[Dict], model) -> List[PredictionResult]:
        """Run ML predictions and collect timing/explanation data"""
        predictions = []
        
        print("  🤖 Running ML predictions...")
        
        for i, product in enumerate(products):
            start_time = time.perf_counter()
            
            try:
                # Prepare features for ML model (adapt to your preprocessing)
                features_df, original_features = self._prepare_ml_features(product)
                
                # Predict
                prediction_scores = model.predict(features_df)
                eco_score = prediction_scores[0]
                
                # Get confidence if available
                confidence = 0.8  # Default
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(features_df)
                    confidence = float(np.max(probabilities[0]))
                
                processing_time = (time.perf_counter() - start_time) * 1000
                
                prediction = PredictionResult(
                    product_id=product.get('id', f"product_{i}"),
                    eco_score=eco_score,
                    confidence=confidence,
                    co2_kg=self._estimate_co2_from_score(eco_score, product),
                    processing_time_ms=processing_time,
                    method="ml_based",
                    features_used=original_features,
                    explanation=self._generate_ml_explanation(model, features_df)
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                print(f"    ⚠️ ML prediction failed for product {i}: {e}")
                predictions.append(PredictionResult(
                    product_id=f"product_{i}",
                    eco_score="F",
                    confidence=0.0,
                    co2_kg=0.0,
                    processing_time_ms=(time.perf_counter() - start_time) * 1000,
                    method="ml_based",
                    features_used={},
                    explanation="Prediction failed"
                ))
        
        return predictions
    
    def _compare_performance(self, rule_preds: List[PredictionResult], 
                           ml_preds: List[PredictionResult],
                           ground_truth: Dict = None) -> Dict:
        """Compare prediction accuracy if ground truth is available"""
        
        if ground_truth is None:
            # Without ground truth, compare agreement and distribution
            return {
                "ground_truth_available": False,
                "prediction_agreement": self._calculate_agreement_rate(rule_preds, ml_preds),
                "score_distributions": {
                    "rule_based": self._get_score_distribution(rule_preds),
                    "ml_based": self._get_score_distribution(ml_preds)
                }
            }
        
        # With ground truth, calculate accuracy metrics
        rule_accuracy = self._calculate_accuracy(rule_preds, ground_truth)
        ml_accuracy = self._calculate_accuracy(ml_preds, ground_truth)
        
        return {
            "ground_truth_available": True,
            "rule_based_accuracy": rule_accuracy,
            "ml_based_accuracy": ml_accuracy,
            "accuracy_difference": ml_accuracy - rule_accuracy,
            "prediction_agreement": self._calculate_agreement_rate(rule_preds, ml_preds)
        }
    
    def _analyze_consistency(self, rule_preds: List[PredictionResult], 
                           ml_preds: List[PredictionResult]) -> Dict:
        """Analyze prediction consistency within similar product groups"""
        
        # Group by similar characteristics
        rule_consistency = self._calculate_internal_consistency(rule_preds)
        ml_consistency = self._calculate_internal_consistency(ml_preds)
        
        return {
            "rule_based_consistency": rule_consistency,
            "ml_based_consistency": ml_consistency,
            "consistency_winner": "rule_based" if rule_consistency > ml_consistency else "ml_based"
        }
    
    def _compare_speed(self, rule_preds: List[PredictionResult], 
                      ml_preds: List[PredictionResult]) -> Dict:
        """Compare processing speed between methods"""
        
        rule_times = [p.processing_time_ms for p in rule_preds]
        ml_times = [p.processing_time_ms for p in ml_preds]
        
        return {
            "rule_based": {
                "mean_time_ms": float(np.mean(rule_times)),
                "median_time_ms": float(np.median(rule_times)),
                "std_time_ms": float(np.std(rule_times))
            },
            "ml_based": {
                "mean_time_ms": float(np.mean(ml_times)),
                "median_time_ms": float(np.median(ml_times)),
                "std_time_ms": float(np.std(ml_times))
            },
            "speed_ratio": float(np.mean(ml_times) / np.mean(rule_times)),
            "speed_winner": "rule_based" if np.mean(rule_times) < np.mean(ml_times) else "ml_based"
        }
    
    def _analyze_interpretability(self, rule_preds: List[PredictionResult], 
                                ml_preds: List[PredictionResult]) -> Dict:
        """Analyze interpretability of predictions"""
        
        rule_interpretability = {
            "explanation_available": all(len(p.explanation) > 0 for p in rule_preds),
            "feature_transparency": "high",  # Rules are explicit
            "decision_path_clarity": "high",
            "average_explanation_length": np.mean([len(p.explanation) for p in rule_preds])
        }
        
        ml_interpretability = {
            "explanation_available": all(len(p.explanation) > 0 for p in ml_preds),
            "feature_transparency": "medium",  # Feature importance available
            "decision_path_clarity": "low",   # Black box
            "average_explanation_length": np.mean([len(p.explanation) for p in ml_preds])
        }
        
        return {
            "rule_based": rule_interpretability,
            "ml_based": ml_interpretability,
            "interpretability_winner": "rule_based"  # Rules are inherently more interpretable
        }
    
    def _analyze_coverage(self, rule_preds: List[PredictionResult], 
                         ml_preds: List[PredictionResult]) -> Dict:
        """Analyze how well each method handles different product types"""
        
        rule_success_rate = len([p for p in rule_preds if p.confidence > 0]) / len(rule_preds)
        ml_success_rate = len([p for p in ml_preds if p.confidence > 0]) / len(ml_preds)
        
        return {
            "rule_based_coverage": rule_success_rate,
            "ml_based_coverage": ml_success_rate,
            "coverage_winner": "rule_based" if rule_success_rate > ml_success_rate else "ml_based",
            "failed_predictions": {
                "rule_based": len(rule_preds) - len([p for p in rule_preds if p.confidence > 0]),
                "ml_based": len(ml_preds) - len([p for p in ml_preds if p.confidence > 0])
            }
        }
    
    def _analyze_agreement(self, rule_preds: List[PredictionResult], 
                          ml_preds: List[PredictionResult]) -> Dict:
        """Analyze where methods agree/disagree"""
        
        agreements = []
        disagreements = []
        
        for rule_pred, ml_pred in zip(rule_preds, ml_preds):
            if rule_pred.eco_score == ml_pred.eco_score:
                agreements.append({
                    "product_id": rule_pred.product_id,
                    "agreed_score": rule_pred.eco_score,
                    "rule_confidence": rule_pred.confidence,
                    "ml_confidence": ml_pred.confidence
                })
            else:
                disagreements.append({
                    "product_id": rule_pred.product_id,
                    "rule_score": rule_pred.eco_score,
                    "ml_score": ml_pred.eco_score,
                    "rule_confidence": rule_pred.confidence,
                    "ml_confidence": ml_pred.confidence
                })
        
        agreement_rate = len(agreements) / len(rule_preds)
        
        return {
            "agreement_rate": agreement_rate,
            "total_agreements": len(agreements),
            "total_disagreements": len(disagreements),
            "top_disagreements": disagreements[:10],  # Show top 10 disagreements
            "agreement_by_confidence": self._analyze_agreement_by_confidence(agreements, disagreements)
        }
    
    def _generate_use_case_recommendations(self, rule_preds: List[PredictionResult], 
                                         ml_preds: List[PredictionResult]) -> Dict:
        """Generate recommendations for when to use each approach"""
        
        rule_times = [p.processing_time_ms for p in rule_preds]
        ml_times = [p.processing_time_ms for p in ml_preds]
        
        recommendations = {
            "rule_based_best_for": [],
            "ml_based_best_for": [],
            "hybrid_approach_for": []
        }
        
        # Speed-based recommendations
        if np.mean(rule_times) < np.mean(ml_times):
            recommendations["rule_based_best_for"].append("Real-time applications requiring fast response")
        
        # Interpretability recommendations
        recommendations["rule_based_best_for"].append("Applications requiring explainable decisions")
        recommendations["rule_based_best_for"].append("Regulatory compliance scenarios")
        
        # Accuracy recommendations
        recommendations["ml_based_best_for"].append("Complex products with many features")
        recommendations["ml_based_best_for"].append("Large-scale batch processing")
        
        # Hybrid recommendations
        recommendations["hybrid_approach_for"].append("Use rules for simple products, ML for complex ones")
        recommendations["hybrid_approach_for"].append("Use rules as fallback when ML confidence is low")
        
        return recommendations
    
    def _prepare_ml_features(self, product: Dict) -> Tuple[pd.DataFrame, Dict]:
        """Prepare features for ML model using saved encoders and expected columns.
        Returns a single-row DataFrame matching the trained RF schema and a dict of original features."""
        # Safe numeric parsing
        def safe_float(val, default=1.0):
            if val is None:
                return float(default)
            if isinstance(val, (int, float, np.number)):
                try:
                    return float(val)
                except Exception:
                    return float(default)
            try:
                s = str(val).strip().replace(',', '')
                match = re.search(r"[-+]?\d*\.?\d+", s)
                return float(match.group(0)) if match else float(default)
            except Exception:
                return float(default)

        material = str(product.get('material', 'Plastic')).strip().title()
        transport = str(product.get('transport', 'Ship')).strip().title()
        recyclability = str(product.get('recyclability', 'Medium')).strip().title()
        origin = str(product.get('origin', 'China')).strip().title()
        weight_val = safe_float(product.get('weight', 1.0), 1.0)
        weight_log = float(np.log1p(weight_val))

        # Compute weight_bin labels identical to training (bins: [0, 0.5, 2, 10, 100] -> labels [0,1,2,3])
        try:
            bin_edges = [0, 0.5, 2, 10, 100]
            bin_labels = [0, 1, 2, 3]
            # Find bin index
            bin_index = None
            for idx in range(len(bin_edges) - 1):
                if bin_edges[idx] <= weight_val <= bin_edges[idx + 1]:
                    bin_index = bin_labels[idx]
                    break
            if bin_index is None:
                bin_index = bin_labels[-1] if weight_val > bin_edges[-1] else bin_labels[0]
            weight_bin_label_str = str(bin_index)
        except Exception:
            weight_bin_label_str = '1'

        # Use saved encoders; fall back to simple mapping if missing
        def encode_val(enc, val, default=0):
            try:
                return int(enc.transform([val])[0])
            except Exception:
                return int(default)

        material_enc = encode_val(self.rf_encoders.get('material'), material, 0)
        transport_enc = encode_val(self.rf_encoders.get('transport'), transport, 0)
        recycle_enc = encode_val(self.rf_encoders.get('recycle'), recyclability, 0)
        origin_enc = encode_val(self.rf_encoders.get('origin'), origin, 0)
        weight_bin_enc = encode_val(self.rf_encoders.get('weight_bin'), weight_bin_label_str, 1)

        row = {
            "material_encoded": material_enc,
            "transport_encoded": transport_enc,
            "recycle_encoded": recycle_enc,
            "origin_encoded": origin_enc,
            "weight_log": weight_log,
            "weight_bin_encoded": weight_bin_enc
        }
        df_row = pd.DataFrame([row], columns=self.feature_cols)
        original_features = {
            "material": material,
            "transport": transport,
            "recyclability": recyclability,
            "origin": origin,
            "weight": weight_val,
            "weight_log": weight_log,
            "weight_bin": weight_bin_label_str
        }
        return df_row, original_features

    def _load_rf_encoders(self):
        """Load RF encoders saved during training from ml/encoders."""
        try:
            files = {
                'material': 'material_encoder.pkl',
                'transport': 'transport_encoder.pkl',
                'recycle': 'recycle_encoder.pkl',
                'origin': 'origin_encoder.pkl',
                'label': 'label_encoder.pkl',
                'weight_bin': 'weight_bin_encoder.pkl'
            }
            for key, fname in files.items():
                fpath = os.path.join(self.encoders_dir, fname)
                if os.path.exists(fpath):
                    self.rf_encoders[key] = joblib.load(fpath)
        except Exception:
            # Keep encoders dict possibly partial; runtime will fall back for missing keys
            pass
    
    def _estimate_co2_from_score(self, eco_score: str, product: Dict) -> float:
        """Estimate CO2 from eco score for comparison"""
        score_to_co2 = {'A+': 0.5, 'A': 1.0, 'B': 1.5, 'C': 2.5, 'D': 4.0, 'E': 6.0, 'F': 8.0}
        return score_to_co2.get(eco_score, 2.0)
    
    def _generate_rule_explanation(self, result: Dict) -> str:
        """Generate explanation for rule-based prediction"""
        return f"Score based on: {result.get('carbon_score', 0):.1f} carbon + {result.get('weight_score', 0):.1f} weight + {result.get('recycle_score', 0):.1f} recyclability"
    
    def _generate_ml_explanation(self, model, features) -> str:
        """Generate explanation for ML prediction"""
        # Handle CalibratedClassifierCV wrapping RF
        importances = None
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'calibrated_classifiers_') and len(model.calibrated_classifiers_) > 0:
            est = getattr(model.calibrated_classifiers_[0], 'estimator', None)
            if est is not None and hasattr(est, 'feature_importances_'):
                importances = est.feature_importances_
        if importances is not None:
            feature_names = ["material", "transport", "recyclability", "origin", "weight_log", "weight_bin"]
            top_features = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:3]
            return f"Top factors: {', '.join([f[0] for f in top_features])}"
        return "ML prediction based on trained model"
    
    def _calculate_agreement_rate(self, rule_preds: List[PredictionResult], 
                                 ml_preds: List[PredictionResult]) -> float:
        """Calculate rate of agreement between methods"""
        agreements = sum(1 for r, m in zip(rule_preds, ml_preds) if r.eco_score == m.eco_score)
        return agreements / len(rule_preds)
    
    def _get_score_distribution(self, predictions: List[PredictionResult]) -> Dict:
        """Get distribution of predicted scores"""
        scores = [p.eco_score for p in predictions]
        unique, counts = np.unique(scores, return_counts=True)
        return dict(zip(unique.tolist(), counts.tolist()))
    
    def _calculate_accuracy(self, predictions: List[PredictionResult], ground_truth: Dict) -> float:
        """Calculate accuracy against ground truth"""
        correct = 0
        total = 0
        
        for pred in predictions:
            if pred.product_id in ground_truth:
                if pred.eco_score == ground_truth[pred.product_id]:
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def _calculate_internal_consistency(self, predictions: List[PredictionResult]) -> float:
        """Calculate internal consistency of predictions"""
        # Simple consistency metric: variance of confidence scores
        confidences = [p.confidence for p in predictions if p.confidence > 0]
        return float(1 - np.var(confidences)) if confidences else 0.0
    
    def _analyze_product_categories(self, products: List[Dict]) -> Dict:
        """Analyze distribution of product categories"""
        categories = {}
        for product in products:
            category = product.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _analyze_error_patterns(self, rule_preds: List[PredictionResult], 
                               ml_preds: List[PredictionResult],
                               ground_truth: Dict = None) -> Dict:
        """Analyze common error patterns for both methods"""
        if ground_truth is None:
            return {"analysis": "No ground truth available for error pattern analysis"}
        
        rule_errors = []
        ml_errors = []
        
        for rule_pred, ml_pred in zip(rule_preds, ml_preds):
            if rule_pred.product_id in ground_truth:
                true_score = ground_truth[rule_pred.product_id]
                
                if rule_pred.eco_score != true_score:
                    rule_errors.append(f"{true_score}→{rule_pred.eco_score}")
                
                if ml_pred.eco_score != true_score:
                    ml_errors.append(f"{true_score}→{ml_pred.eco_score}")
        
        return {
            "rule_based_common_errors": self._get_top_errors(rule_errors),
            "ml_based_common_errors": self._get_top_errors(ml_errors),
            "error_rate_comparison": {
                "rule_based": len(rule_errors) / len(rule_preds),
                "ml_based": len(ml_errors) / len(ml_preds)
            }
        }
    
    def _get_top_errors(self, errors: List[str]) -> List[Dict]:
        """Get most common error patterns"""
        from collections import Counter
        error_counts = Counter(errors)
        return [{"pattern": pattern, "count": count} for pattern, count in error_counts.most_common(5)]
    
    def _analyze_agreement_by_confidence(self, agreements: List[Dict], disagreements: List[Dict]) -> Dict:
        """Analyze agreement patterns by confidence levels"""
        high_conf_agreements = len([a for a in agreements if a['rule_confidence'] > 0.7 and a['ml_confidence'] > 0.7])
        low_conf_disagreements = len([d for d in disagreements if d['rule_confidence'] < 0.5 or d['ml_confidence'] < 0.5])
        
        return {
            "high_confidence_agreements": high_conf_agreements,
            "low_confidence_disagreements": low_conf_disagreements,
            "pattern": "Higher confidence correlates with agreement" if high_conf_agreements > low_conf_disagreements else "Mixed pattern"
        }
    
    def _save_comparison_results(self, results: Dict):
        """Save comparison results to file"""
        output_file = self.results_dir / "rule_vs_ml_comparison.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"💾 Comparison results saved to {output_file}")
    
    def _create_comparison_visualizations(self, rule_preds: List[PredictionResult], 
                                        ml_preds: List[PredictionResult]):
        """Create visualization comparing both approaches"""
        # Score distribution comparison
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        rule_scores = [p.eco_score for p in rule_preds]
        ml_scores = [p.eco_score for p in ml_preds]
        
        scores = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
        rule_counts = [rule_scores.count(s) for s in scores]
        ml_counts = [ml_scores.count(s) for s in scores]
        
        x = np.arange(len(scores))
        width = 0.35
        
        plt.bar(x - width/2, rule_counts, width, label='Rule-based', alpha=0.8)
        plt.bar(x + width/2, ml_counts, width, label='ML-based', alpha=0.8)
        plt.xlabel('Eco Score')
        plt.ylabel('Count')
        plt.title('Score Distribution Comparison')
        plt.xticks(x, scores)
        plt.legend()
        
        # Processing time comparison
        plt.subplot(1, 2, 2)
        rule_times = [p.processing_time_ms for p in rule_preds]
        ml_times = [p.processing_time_ms for p in ml_preds]
        
        plt.boxplot([rule_times, ml_times], labels=['Rule-based', 'ML-based'])
        plt.ylabel('Processing Time (ms)')
        plt.title('Processing Speed Comparison')
        plt.yscale('log')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / "comparison_visualization.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Visualization saved to {self.results_dir}/comparison_visualization.png")

# Integration with your existing Amazon scraping code
def create_amazon_rule_predictor():
    """Create a wrapper for your existing Amazon rule-based prediction"""
    def predict_with_amazon_rules(product: Dict) -> Dict:
        """
        This should integrate with your existing calculate_eco_score functions
        from backend.api.routes.api.py and backend.api.app.py
        """
        try:
            # Import your existing functions
            import sys
            import os
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            sys.path.insert(0, project_root)
            
            # Try to import your existing eco score calculation
            from backend.api.routes.api import calculate_eco_score
            
            # Extract features from Amazon product with robust numeric parsing
            def safe_float(val, default=1.0):
                if val is None:
                    return float(default)
                if isinstance(val, (int, float, np.number)):
                    try:
                        return float(val)
                    except Exception:
                        return float(default)
                try:
                    s = str(val).strip().replace(',', '')
                    match = re.search(r"[-+]?\d*\.?\d+", s)
                    return float(match.group(0)) if match else float(default)
                except Exception:
                    return float(default)

            weight = safe_float(product.get('weight', 1.0), 1.0)
            material = product.get('material', 'Plastic')
            recyclability = product.get('recyclability', 'Medium')
            origin = product.get('origin', 'China')
            transport = product.get('transport', 'Ship')
            
            # Calculate using your existing rule-based method
            carbon_kg = weight * 0.5  # Simplified CO2 calculation
            distance_km = 8000 if origin != 'UK' else 500  # Simplified distance
            
            eco_score = calculate_eco_score(carbon_kg, recyclability, distance_km, weight)
            
            return {
                'eco_score': eco_score,
                'confidence': 0.8,
                'co2_kg': carbon_kg,
                'features_used': {
                    'weight': weight, 
                    'material': material,
                    'recyclability': recyclability,
                    'origin': origin,
                    'transport': transport
                },
                'carbon_score': max(0, 10 - carbon_kg * 5),
                'weight_score': max(0, 10 - weight * 2),
                'recycle_score': {'Low': 2, 'Medium': 6, 'High': 10}.get(recyclability, 5)
            }
            
        except ImportError:
            # Fallback simplified calculation if imports fail
            def safe_float(val, default=1.0):
                if val is None:
                    return float(default)
                if isinstance(val, (int, float, np.number)):
                    try:
                        return float(val)
                    except Exception:
                        return float(default)
                try:
                    s = str(val).strip().replace(',', '')
                    match = re.search(r"[-+]?\d*\.?\d+", s)
                    return float(match.group(0)) if match else float(default)
                except Exception:
                    return float(default)
            weight = safe_float(product.get('weight', 1.0), 1.0)
            material = product.get('material', 'Plastic')
            
            carbon_score = max(0, 10 - weight * 2)
            material_score = 8 if material in ['Glass', 'Aluminum'] else 5
            total_score = (carbon_score + material_score) / 2
            
            if total_score >= 9:
                eco_score = "A+"
            elif total_score >= 7:
                eco_score = "A"
            elif total_score >= 5:
                eco_score = "B"
            else:
                eco_score = "C"
            
            return {
                'eco_score': eco_score,
                'confidence': 0.8,
                'co2_kg': weight * 0.5,
                'features_used': {'weight': weight, 'material': material},
                'carbon_score': carbon_score,
                'weight_score': material_score,
                'recycle_score': material_score
            }
    
    return predict_with_amazon_rules

if __name__ == "__main__":
    # Example usage with Amazon products
    framework = AmazonComparisonFramework()
    
    # Load Amazon test products from your dataset
    try:
        import pandas as pd
        import os
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
        # Prefer common dataset if present, else fallback to consolidated ml copy
        common_csv = os.path.join(project_root, "common", "data", "csv", "eco_dataset.csv")
        ml_csv = os.path.join(project_root, "ml", "eco_dataset.csv")
        dataset_path = common_csv if os.path.exists(common_csv) else ml_csv
        df = pd.read_csv(dataset_path)
        
        # Sample 100 products for comparison
        test_df = df.sample(n=min(100, len(df)), random_state=42)
        test_products = test_df.to_dict('records')
        
        print(f"📦 Loaded {len(test_products)} Amazon products for comparison")
        
        # Create predictors
        amazon_rule_predictor = create_amazon_rule_predictor()
        
        # Load your ML model
        import joblib
        ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))
        model_path = os.path.join(ML_ASSETS_DIR, "eco_model.pkl")
        if not os.path.exists(model_path):
            model_path = os.path.join(project_root, "ml", "eco_model.pkl")
        ml_model = joblib.load(model_path)
        
        # Run comparison
        results = framework.run_comparative_analysis(
            test_products=test_products,
            rule_based_predictor=amazon_rule_predictor,
            ml_model=ml_model
        )
        
        print("✅ Amazon product comparison analysis complete!")
        print(f"Agreement rate: {results['agreement_analysis']['agreement_rate']:.2%}")
        print(f"Rule-based avg time: {results['speed_comparison']['rule_based']['mean_time_ms']:.1f}ms")
        print(f"ML avg time: {results['speed_comparison']['ml_based']['mean_time_ms']:.1f}ms")
        
        # Perfect for dissertation: quantified comparison of both approaches
        
    except FileNotFoundError:
        print("⚠️ Could not find Amazon dataset. Please ensure the path is correct.")
    except Exception as e:
        print(f"⚠️ Error: {e}")
        print("Please ensure the model and data files are available.")