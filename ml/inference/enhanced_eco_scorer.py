"""
🎯 ENHANCED REAL-TIME ECO SCORING SYSTEM
======================================

Production-grade eco scoring system that provides accurate real-time
environmental impact predictions with confidence indicators.

Key Features:
1. Real-time ML model inference with uncertainty quantification
2. Dual validation (ML vs rule-based) comparison
3. Confidence scoring and reliability indicators
4. Comprehensive error handling and fallbacks
5. Performance monitoring and logging

This integrates with your existing pipeline while providing the accuracy
and reliability needed for 95% academic performance.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project root for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.utils.co2_data import load_material_co2_data
except ImportError:
    def load_material_co2_data():
        return {"plastic": 2.0, "aluminum": 8.0, "steel": 2.5}

class EnhancedEcoScorer:
    """
    Production-grade eco scoring system with dual validation
    """
    
    def __init__(self, model_dir=None):
        # Setup paths
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
        default_assets_dir = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))
        self.model_dir = model_dir or default_assets_dir
        self.encoders_dir = os.path.join(self.model_dir, "xgb_encoders")
        
        # Load models and encoders
        self.models = {}
        self.encoders = {}
        self.feature_order = []
        
        # Load CO2 data
        self.material_co2_map = load_material_co2_data()
        
        # Performance tracking
        self.prediction_history = []
        
        # Initialize
        self._load_models_and_encoders()
        self._setup_rule_based_system()
        
        print("🎯 Enhanced Eco Scorer initialized")
        print(f"📁 Model directory: {self.model_dir}")
        print(f"🤖 Available models: {list(self.models.keys())}")
    
    def _load_models_and_encoders(self):
        """Load trained models and encoders"""
        try:
            # Load feature order
            feature_order_path = os.path.join(self.model_dir, "feature_order.json")
            if os.path.exists(feature_order_path):
                with open(feature_order_path, 'r') as f:
                    self.feature_order = json.load(f)
                print(f"📋 Loaded feature order: {len(self.feature_order)} features")
            
            # Load models
            model_files = {
                'xgboost': 'xgboost_model.pkl',
                'ensemble': 'ensemble_model.pkl',
                'eco_model': 'eco_model.pkl'  # Fallback to your existing model
            }
            
            for model_name, filename in model_files.items():
                model_path = os.path.join(self.model_dir, filename)
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    print(f"✅ Loaded {model_name} model")
            
            # Load encoders
            if os.path.exists(self.encoders_dir):
                for encoder_file in os.listdir(self.encoders_dir):
                    if encoder_file.endswith('_encoder.pkl'):
                        encoder_name = encoder_file.replace('_encoder.pkl', '')
                        encoder_path = os.path.join(self.encoders_dir, encoder_file)
                        self.encoders[encoder_name] = joblib.load(encoder_path)
                        print(f"✅ Loaded {encoder_name} encoder")
            
            if not self.models:
                print("⚠️ No models loaded - using rule-based fallback only")
            
        except Exception as e:
            print(f"⚠️ Error loading models: {e}")
            print("🔄 Will use rule-based scoring only")
    
    def _setup_rule_based_system(self):
        """Setup rule-based eco scoring system for comparison"""
        # Material impact scores (kg CO2 per kg)
        self.material_scores = {
            'Aluminum': 8.0, 'Steel': 2.5, 'Glass': 1.2, 'Paper': 1.0,
            'Cardboard': 0.8, 'Plastic': 2.0, 'Cotton': 3.0, 'Polyester': 4.0,
            'Rubber': 1.5, 'Leather': 10.0, 'Wood': 0.5, 'Bamboo': 0.3,
            'Other': 2.0, 'Unknown': 2.0
        }
        
        # Transport impact factors (kg CO2 per kg per 1000km)
        self.transport_factors = {
            'Land': 0.15, 'Air': 0.5, 'Ship': 0.03
        }
        
        # Distance estimates by origin (rough km to UK)
        self.origin_distances = {
            'UK': 0, 'Germany': 800, 'France': 350, 'Italy': 1200,
            'USA': 5500, 'China': 8000, 'Japan': 9600, 'India': 6500,
            'Vietnam': 10500, 'Brazil': 9200, 'Other': 5000
        }
        
        # Eco score thresholds (total kg CO2)
        self.eco_thresholds = {
            'A+': 0.5, 'A': 1.0, 'B': 2.0, 'C': 4.0, 
            'D': 8.0, 'E': 15.0, 'F': float('inf')
        }
    
    def predict_eco_score(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main prediction method - provides both ML and rule-based predictions
        
        Args:
            product_data: Dictionary with product information
            
        Returns:
            Comprehensive prediction result with confidence scoring
        """
        try:
            # Extract product features
            features = self._extract_features(product_data)
            
            # ML predictions (if models available)
            ml_predictions = self._get_ml_predictions(features)
            
            # Rule-based prediction
            rule_prediction = self._get_rule_based_prediction(product_data)
            
            # Calculate confidence and consensus
            confidence_analysis = self._analyze_prediction_confidence(
                ml_predictions, rule_prediction, features
            )
            
            # Generate comprehensive result
            result = {
                'ml_predictions': ml_predictions,
                'rule_based_prediction': rule_prediction,
                'confidence_analysis': confidence_analysis,
                'consensus': self._determine_consensus(ml_predictions, rule_prediction),
                'explanation': self._generate_explanation(product_data, ml_predictions, rule_prediction),
                'data_quality': self._assess_input_quality(product_data),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            # Track prediction for monitoring
            self._track_prediction(product_data, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            return self._get_fallback_prediction(product_data, str(e))
    
    def _extract_features(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and encode features for ML prediction"""
        features = {}
        
        try:
            # Basic features
            material = str(product_data.get('material_type', 'Unknown'))
            transport = str(product_data.get('transport_mode', 'Ship'))
            recyclability = str(product_data.get('recyclability', 'Medium'))
            origin = str(product_data.get('origin', 'Unknown'))
            weight = float(product_data.get('weight_kg', 1.0))
            
            # Encode categorical features
            if 'material' in self.encoders:
                try:
                    features['material_encoded'] = self.encoders['material'].transform([material])[0]
                except ValueError:
                    # Handle unknown categories
                    features['material_encoded'] = 0
            
            if 'transport' in self.encoders:
                try:
                    features['transport_encoded'] = self.encoders['transport'].transform([transport])[0]
                except ValueError:
                    features['transport_encoded'] = 0
            
            if 'recyclability' in self.encoders:
                try:
                    features['recyclability_encoded'] = self.encoders['recyclability'].transform([recyclability])[0]
                except ValueError:
                    features['recyclability_encoded'] = 1  # Medium
            
            if 'origin' in self.encoders:
                try:
                    features['origin_encoded'] = self.encoders['origin'].transform([origin])[0]
                except ValueError:
                    features['origin_encoded'] = 0
            
            # Weight features
            features['weight_log'] = np.log1p(weight)
            features['weight_sqrt'] = np.sqrt(weight)
            
            # Weight binning
            if weight <= 0.5:
                weight_bin = 0
            elif weight <= 2.0:
                weight_bin = 1
            elif weight <= 10.0:
                weight_bin = 2
            else:
                weight_bin = 3
            
            if 'weight_bin' in self.encoders:
                try:
                    features['weight_bin_encoded'] = self.encoders['weight_bin'].transform([str(weight_bin)])[0]
                except ValueError:
                    features['weight_bin_encoded'] = weight_bin
            
            # Enhanced features (if available)
            if 'material_transport' in self.feature_order:
                features['material_transport'] = features.get('material_encoded', 0) * features.get('transport_encoded', 0)
            
            if 'origin_recycle' in self.feature_order:
                features['origin_recycle'] = features.get('origin_encoded', 0) * features.get('recyclability_encoded', 0)
            
            if 'material_weight_interaction' in self.feature_order:
                features['material_weight_interaction'] = features.get('material_encoded', 0) * features.get('weight_log', 0)
            
            # Distance proxy
            distance_proxy = self._get_distance_proxy(origin)
            features['distance_proxy'] = distance_proxy
            features['distance_weight_interaction'] = distance_proxy * features.get('weight_log', 0)
            
        except Exception as e:
            print(f"⚠️ Feature extraction error: {e}")
        
        return features
    
    def _get_distance_proxy(self, origin: str) -> float:
        """Get distance proxy value for origin"""
        distance_map = {
            'UK': 0, 'Germany': 1, 'France': 1, 'Italy': 2, 
            'USA': 3, 'China': 4, 'Japan': 4, 'India': 4, 
            'Brazil': 3, 'Other': 2
        }
        return distance_map.get(origin, 2)
    
    def _get_ml_predictions(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Get predictions from all available ML models"""
        ml_predictions = {}
        
        if not self.models:
            return ml_predictions
        
        try:
            # Prepare feature vector
            if self.feature_order:
                feature_vector = []
                for feature_name in self.feature_order:
                    feature_vector.append(features.get(feature_name, 0))
                feature_vector = np.array(feature_vector).reshape(1, -1)
            else:
                # Fallback feature order
                basic_features = ['material_encoded', 'transport_encoded', 'recyclability_encoded', 
                                'origin_encoded', 'weight_log', 'weight_bin_encoded']
                feature_vector = []
                for feature_name in basic_features:
                    feature_vector.append(features.get(feature_name, 0))
                feature_vector = np.array(feature_vector).reshape(1, -1)
            
            # Get predictions from each model
            for model_name, model in self.models.items():
                try:
                    # Prediction
                    prediction = model.predict(feature_vector)[0]
                    
                    # Prediction probabilities (if available)
                    probabilities = None
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(feature_vector)[0]
                        probabilities = proba.tolist()
                    
                    # Convert prediction to eco score
                    if hasattr(self.encoders.get('label'), 'classes_'):
                        eco_score = self.encoders['label'].classes_[prediction]
                    else:
                        # Fallback mapping
                        score_map = {0: 'A+', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F'}
                        eco_score = score_map.get(prediction, 'C')
                    
                    ml_predictions[model_name] = {
                        'eco_score': eco_score,
                        'raw_prediction': int(prediction),
                        'probabilities': probabilities,
                        'confidence': float(max(probabilities)) if probabilities else 0.7
                    }
                    
                except Exception as e:
                    print(f"⚠️ {model_name} prediction failed: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️ ML prediction error: {e}")
        
        return ml_predictions
    
    def _get_rule_based_prediction(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get rule-based eco score prediction"""
        try:
            # Extract basic data
            material = product_data.get('material_type', 'Unknown')
            transport = product_data.get('transport_mode', 'Ship')
            origin = product_data.get('origin', 'Other')
            weight = float(product_data.get('weight_kg', 1.0))
            
            # Calculate material impact
            material_impact = self.material_scores.get(material, 2.0) * weight
            
            # Calculate transport impact
            distance = self.origin_distances.get(origin, 5000)
            transport_factor = self.transport_factors.get(transport, 0.15)
            transport_impact = (weight * distance * transport_factor) / 1000  # Normalize
            
            # Total CO2 emissions
            total_co2 = material_impact + transport_impact
            
            # Determine eco score
            eco_score = 'F'
            for score, threshold in self.eco_thresholds.items():
                if total_co2 <= threshold:
                    eco_score = score
                    break
            
            # Calculate confidence based on data completeness
            confidence = 0.8  # Base confidence
            if material != 'Unknown':
                confidence += 0.1
            if origin != 'Other':
                confidence += 0.1
            confidence = min(confidence, 1.0)
            
            return {
                'eco_score': eco_score,
                'total_co2_kg': round(total_co2, 3),
                'material_impact': round(material_impact, 3),
                'transport_impact': round(transport_impact, 3),
                'confidence': confidence,
                'explanation': f"Material: {material_impact:.2f} + Transport: {transport_impact:.2f} = {total_co2:.2f} kg CO2"
            }
            
        except Exception as e:
            print(f"⚠️ Rule-based prediction error: {e}")
            return {
                'eco_score': 'C',
                'total_co2_kg': 2.0,
                'confidence': 0.3,
                'explanation': f"Fallback prediction due to error: {e}"
            }
    
    def _analyze_prediction_confidence(self, ml_predictions: Dict, rule_prediction: Dict, features: Dict) -> Dict[str, Any]:
        """Analyze prediction confidence across different methods"""
        confidence_analysis = {
            'overall_confidence': 0.5,
            'agreement_score': 0.0,
            'data_completeness': 0.0,
            'model_consensus': False,
            'reliability_indicators': []
        }
        
        try:
            # Calculate data completeness
            feature_completeness = sum(1 for v in features.values() if v != 0) / len(features) if features else 0
            confidence_analysis['data_completeness'] = feature_completeness
            
            # Analyze ML model agreement
            if len(ml_predictions) > 1:
                ml_scores = [pred['eco_score'] for pred in ml_predictions.values()]
                # Check if all models agree
                if len(set(ml_scores)) == 1:
                    confidence_analysis['model_consensus'] = True
                    confidence_analysis['agreement_score'] = 1.0
                else:
                    # Calculate partial agreement
                    most_common = max(set(ml_scores), key=ml_scores.count)
                    agreement_ratio = ml_scores.count(most_common) / len(ml_scores)
                    confidence_analysis['agreement_score'] = agreement_ratio
            
            # Compare ML vs rule-based
            if ml_predictions and rule_prediction:
                best_ml_score = list(ml_predictions.values())[0]['eco_score']
                rule_score = rule_prediction['eco_score']
                
                if best_ml_score == rule_score:
                    confidence_analysis['reliability_indicators'].append("ML and rule-based agree")
                    confidence_analysis['overall_confidence'] += 0.2
                else:
                    confidence_analysis['reliability_indicators'].append("ML and rule-based disagree")
            
            # Factor in individual model confidences
            if ml_predictions:
                avg_ml_confidence = np.mean([pred.get('confidence', 0.5) for pred in ml_predictions.values()])
                confidence_analysis['overall_confidence'] = avg_ml_confidence * 0.7 + confidence_analysis['data_completeness'] * 0.3
            else:
                confidence_analysis['overall_confidence'] = rule_prediction.get('confidence', 0.5) * 0.8
            
            # Add quality indicators
            if confidence_analysis['overall_confidence'] >= 0.8:
                confidence_analysis['reliability_indicators'].append("High confidence prediction")
            elif confidence_analysis['overall_confidence'] >= 0.6:
                confidence_analysis['reliability_indicators'].append("Medium confidence prediction")
            else:
                confidence_analysis['reliability_indicators'].append("Low confidence - use with caution")
            
        except Exception as e:
            print(f"⚠️ Confidence analysis error: {e}")
        
        return confidence_analysis
    
    def _determine_consensus(self, ml_predictions: Dict, rule_prediction: Dict) -> Dict[str, Any]:
        """Determine consensus prediction from all methods"""
        try:
            # Collect all predictions
            all_scores = []
            
            # Add ML predictions
            for model_name, prediction in ml_predictions.items():
                confidence = prediction.get('confidence', 0.5)
                all_scores.append({
                    'score': prediction['eco_score'],
                    'confidence': confidence,
                    'method': f"ML_{model_name}",
                    'weight': confidence * 0.8  # ML gets higher base weight
                })
            
            # Add rule-based prediction
            if rule_prediction:
                all_scores.append({
                    'score': rule_prediction['eco_score'],
                    'confidence': rule_prediction.get('confidence', 0.5),
                    'method': 'rule_based',
                    'weight': rule_prediction.get('confidence', 0.5) * 0.6
                })
            
            if not all_scores:
                return {'eco_score': 'C', 'confidence': 0.3, 'method': 'fallback'}
            
            # Weighted voting
            score_weights = {}
            for pred in all_scores:
                score = pred['score']
                weight = pred['weight']
                if score in score_weights:
                    score_weights[score] += weight
                else:
                    score_weights[score] = weight
            
            # Get consensus score
            consensus_score = max(score_weights.keys(), key=lambda k: score_weights[k])
            consensus_weight = score_weights[consensus_score]
            total_weight = sum(score_weights.values())
            consensus_confidence = consensus_weight / total_weight if total_weight > 0 else 0.5
            
            # Determine method
            contributing_methods = [pred['method'] for pred in all_scores if pred['score'] == consensus_score]
            method_description = f"Consensus from: {', '.join(contributing_methods)}"
            
            return {
                'eco_score': consensus_score,
                'confidence': float(consensus_confidence),
                'method': method_description,
                'vote_distribution': score_weights
            }
            
        except Exception as e:
            print(f"⚠️ Consensus determination error: {e}")
            return {'eco_score': 'C', 'confidence': 0.3, 'method': 'error_fallback'}
    
    def _generate_explanation(self, product_data: Dict, ml_predictions: Dict, rule_prediction: Dict) -> str:
        """Generate human-readable explanation of the prediction"""
        try:
            material = product_data.get('material_type', 'Unknown')
            weight = product_data.get('weight_kg', 1.0)
            transport = product_data.get('transport_mode', 'Ship')
            origin = product_data.get('origin', 'Unknown')
            
            explanation = f"Environmental impact assessment for {material} product ({weight}kg) "
            explanation += f"from {origin} via {transport} transport."
            
            if ml_predictions:
                ml_score = list(ml_predictions.values())[0]['eco_score']
                explanation += f" ML model predicts: {ml_score}."
            
            if rule_prediction:
                rule_score = rule_prediction['eco_score']
                co2_estimate = rule_prediction.get('total_co2_kg', 0)
                explanation += f" Rule-based calculation: {rule_score} ({co2_estimate}kg CO2)."
            
            return explanation
            
        except Exception as e:
            return f"Prediction generated with limited data quality: {e}"
    
    def _assess_input_quality(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of input data"""
        quality_factors = {
            'material_specified': product_data.get('material_type', 'Unknown') != 'Unknown',
            'weight_provided': product_data.get('weight_kg', 0) > 0,
            'origin_known': product_data.get('origin', 'Unknown') != 'Unknown',
            'transport_specified': product_data.get('transport_mode', 'Unknown') != 'Unknown'
        }
        
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            'quality_score': quality_score,
            'quality_factors': quality_factors,
            'grade': 'High' if quality_score >= 0.8 else 'Medium' if quality_score >= 0.5 else 'Low'
        }
    
    def _get_fallback_prediction(self, product_data: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Provide fallback prediction when main prediction fails"""
        return {
            'ml_predictions': {},
            'rule_based_prediction': {
                'eco_score': 'C',
                'total_co2_kg': 2.0,
                'confidence': 0.3,
                'explanation': f"Fallback prediction due to error: {error_msg}"
            },
            'confidence_analysis': {
                'overall_confidence': 0.3,
                'reliability_indicators': ['Fallback prediction - limited accuracy']
            },
            'consensus': {
                'eco_score': 'C',
                'confidence': 0.3,
                'method': 'fallback'
            },
            'explanation': f"Unable to generate accurate prediction: {error_msg}",
            'data_quality': {'quality_score': 0.2, 'grade': 'Low'},
            'error': error_msg,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def _track_prediction(self, product_data: Dict[str, Any], result: Dict[str, Any]):
        """Track prediction for performance monitoring"""
        try:
            tracking_entry = {
                'timestamp': result['timestamp'],
                'input_quality': result['data_quality']['quality_score'],
                'consensus_confidence': result['consensus']['confidence'],
                'consensus_score': result['consensus']['eco_score'],
                'ml_available': bool(result['ml_predictions']),
                'rule_based_available': bool(result['rule_based_prediction'])
            }
            
            self.prediction_history.append(tracking_entry)
            
            # Keep only last 1000 predictions for memory management
            if len(self.prediction_history) > 1000:
                self.prediction_history = self.prediction_history[-1000:]
                
        except Exception as e:
            print(f"⚠️ Prediction tracking error: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self.prediction_history:
            return {'error': 'No prediction history available'}
        
        try:
            df = pd.DataFrame(self.prediction_history)
            
            metrics = {
                'total_predictions': len(df),
                'avg_confidence': float(df['consensus_confidence'].mean()),
                'avg_input_quality': float(df['input_quality'].mean()),
                'ml_availability_rate': float(df['ml_available'].mean()),
                'score_distribution': df['consensus_score'].value_counts().to_dict(),
                'recent_performance': {
                    'last_24h_count': len(df[df['timestamp'] > (pd.Timestamp.now() - pd.Timedelta(days=1))]),
                    'avg_confidence_24h': float(df[df['timestamp'] > (pd.Timestamp.now() - pd.Timedelta(days=1))]['consensus_confidence'].mean()) if len(df) > 0 else 0
                }
            }
            
            return metrics
            
        except Exception as e:
            return {'error': f'Performance metrics calculation failed: {e}'}

# Convenience functions for integration
def predict_product_eco_score(product_data: Dict[str, Any], model_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function for single product eco score prediction
    
    Args:
        product_data: Product information dictionary
        model_dir: Optional custom model directory
        
    Returns:
        Eco score prediction with confidence analysis
    """
    scorer = EnhancedEcoScorer(model_dir)
    return scorer.predict_eco_score(product_data)

def main():
    """Test the enhanced eco scorer"""
    # Test product data
    test_product = {
        'material_type': 'Aluminum',
        'weight_kg': 0.5,
        'transport_mode': 'Ship',
        'origin': 'China',
        'recyclability': 'High'
    }
    
    print("🧪 Testing Enhanced Eco Scorer")
    scorer = EnhancedEcoScorer()
    result = scorer.predict_eco_score(test_product)
    
    print(f"\n🎯 Prediction Results:")
    print(f"Consensus Score: {result['consensus']['eco_score']}")
    print(f"Confidence: {result['consensus']['confidence']:.3f}")
    print(f"Method: {result['consensus']['method']}")
    print(f"Explanation: {result['explanation']}")
    
    if result['ml_predictions']:
        print(f"\n🤖 ML Predictions:")
        for model, pred in result['ml_predictions'].items():
            print(f"  {model}: {pred['eco_score']} (confidence: {pred['confidence']:.3f})")
    
    if result['rule_based_prediction']:
        print(f"\n📏 Rule-based: {result['rule_based_prediction']['eco_score']} ({result['rule_based_prediction']['total_co2_kg']} kg CO2)")

if __name__ == "__main__":
    main()