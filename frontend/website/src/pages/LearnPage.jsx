import React, { useState } from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";
import ImportantChart from "../components/ImportantChart";
import ModelInfoModal from "../components/ModelInfoModal";
import ModelMetricsChart from "../components/ModelMetricsChart";
import Footer from "../components/Footer";

export default function LearnPage() {
  const [showModal, setShowModal] = useState(false);

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-24">
            {/* Hero Section */}
            <ModernSection className="text-center mb-24">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-12"
              >
                <div className="space-y-8">
                  <h1 className="text-5xl md:text-6xl font-display font-bold leading-tight">
                    <span className="text-slate-100">Machine Learning</span>
                    <br />
                    <span className="bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
                      Model Documentation
                    </span>
                  </h1>
                  <motion.p
                    className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                  >
                    Comprehensive technical documentation of our environmental impact prediction system, 
                    including XGBoost model architecture, training methodology, and performance analysis.
                  </motion.p>
                </div>
                
                {/* Key Metrics Overview */}
                <motion.div
                  className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-12"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.6 }}
                >
                  <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-cyan-400 mb-2">85.8%</div>
                    <div className="text-slate-300 font-medium">Model Accuracy</div>
                    <div className="text-slate-500 text-sm">XGBoost Classifier</div>
                  </div>
                  <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-purple-400 mb-2">11</div>
                    <div className="text-slate-300 font-medium">Feature Vector</div>
                    <div className="text-slate-500 text-sm">Enhanced Model</div>
                  </div>
                  <div className="glass-card p-6 text-center">
                    <div className="text-3xl font-bold text-green-400 mb-2">4.5K</div>
                    <div className="text-slate-300 font-medium">Training Samples</div>
                    <div className="text-slate-500 text-sm">Balanced Dataset</div>
                  </div>
                </motion.div>
              </motion.div>
            </ModernSection>

            {/* Model Info Button */}
            <ModernSection>
              <div className="flex justify-center">
                <ModernButton
                  variant="secondary"
                  onClick={() => setShowModal(true)}
                  icon="🔬"
                >
                  About the Model
                </ModernButton>
              </div>
            </ModernSection>

            {/* Feature Importance Section */}
            <ModernSection 
              title="Feature Importance Analysis" 
              icon={true}
              delay={0.2}
            >
              <ModernCard solid className="p-8">
                <div className="space-y-8">
                  <div className="text-center">
                    <p className="text-slate-400">
                      Understanding which factors most influence environmental impact scores
                    </p>
                  </div>
                  <div className="min-h-[600px] w-full">
                    <ImportantChart />
                  </div>
                </div>
              </ModernCard>
            </ModernSection>

            {/* Model Metrics Section */}
            <ModernSection 
              title="Model Performance Metrics" 
              icon={true}
              delay={0.4}
              className="mt-32"
            >
              <ModernCard solid className="p-8">
                <div className="space-y-8">
                  <div className="text-center">
                    <p className="text-slate-400">
                      Real-world accuracy and performance statistics of our prediction model
                    </p>
                  </div>
                  <div className="min-h-[500px] flex items-start justify-center">
                    <ModelMetricsChart />
                  </div>
                </div>
              </ModernCard>
            </ModernSection>

            {/* Training Pipeline Documentation */}
            <ModernSection 
              title="Training Pipeline Architecture" 
              icon={true}
              delay={0.6}
              className="mt-32 mb-24"
            >
              <div className="space-y-20">
                {/* train_model.py Documentation */}
                <ModernCard solid className="p-8">
                  <div className="space-y-8">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-xl flex items-center justify-center">
                        <span className="text-white text-xl">📊</span>
                      </div>
                      <div>
                        <h3 className="text-2xl font-display text-slate-200">train_model.py</h3>
                        <p className="text-slate-400">Random Forest Baseline Implementation</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-lg font-medium text-cyan-400 mb-3">Data Preprocessing Pipeline</h4>
                          <div className="bg-slate-800/50 p-4 rounded-lg space-y-2">
                            <code className="text-sm text-slate-300 block">df = pd.read_csv("eco_dataset.csv")</code>
                            <code className="text-sm text-slate-300 block">df = df.dropna(subset=["material", "true_eco_score"])</code>
                            <code className="text-sm text-slate-300 block">encoders = &#123;'material': LabelEncoder(), ...&#125;</code>
                            <code className="text-sm text-slate-300 block">X_train, X_test = train_test_split(X, y, test_size=0.2)</code>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-lg font-medium text-cyan-400 mb-3">Model Configuration</h4>
                          <ul className="space-y-2 text-sm text-slate-300">
                            <li>• <strong>Algorithm:</strong> RandomForestClassifier</li>
                            <li>• <strong>Estimators:</strong> 100 decision trees</li>
                            <li>• <strong>Max Depth:</strong> 10 levels</li>
                            <li>• <strong>Features:</strong> 6-dimensional vector</li>
                            <li>• <strong>Criterion:</strong> Gini impurity</li>
                          </ul>
                        </div>
                      </div>
                      
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-lg font-medium text-cyan-400 mb-3">Performance Metrics</h4>
                          <div className="grid grid-cols-2 gap-4">
                            <div className="bg-slate-800/50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-green-400">81.5%</div>
                              <div className="text-slate-400 text-sm">Accuracy</div>
                            </div>
                            <div className="bg-slate-800/50 p-4 rounded-lg text-center">
                              <div className="text-2xl font-bold text-blue-400">81.7%</div>
                              <div className="text-slate-400 text-sm">F1-Score</div>
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="text-lg font-medium text-cyan-400 mb-3">Output Artifacts</h4>
                          <ul className="space-y-2 text-sm text-slate-300">
                            <li>• <code className="bg-slate-700 px-2 py-1 rounded">eco_model.pkl</code></li>
                            <li>• <code className="bg-slate-700 px-2 py-1 rounded">confusion_matrix.png</code></li>
                            <li>• <code className="bg-slate-700 px-2 py-1 rounded">feature_importance.png</code></li>
                            <li>• <code className="bg-slate-700 px-2 py-1 rounded">metrics.json</code></li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </ModernCard>

                {/* train_xgboost.py Documentation */}
                <ModernCard solid className="p-8">
                  <div className="space-y-8">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-400 rounded-xl flex items-center justify-center">
                        <span className="text-white text-xl">🚀</span>
                      </div>
                      <div>
                        <h3 className="text-2xl font-display text-slate-200">train_xgboost.py</h3>
                        <p className="text-slate-400">Enhanced XGBoost Implementation</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-lg font-medium text-purple-400 mb-3">Enhanced Features</h4>
                          <div className="space-y-3">
                            <div className="bg-slate-800/50 p-3 rounded">
                              <div className="text-sm font-medium text-slate-200">Core Features (6)</div>
                              <div className="text-xs text-slate-400">material, transport, recyclability, origin, weight_log, weight_bin</div>
                            </div>
                            <div className="bg-slate-800/50 p-3 rounded">
                              <div className="text-sm font-medium text-slate-200">Enhanced Features (+5)</div>
                              <div className="text-xs text-slate-400">packaging_type, size_category, quality_level, pack_size, material_confidence</div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-lg font-medium text-purple-400 mb-3">Hyperparameter Tuning</h4>
                          <div className="bg-slate-800/50 p-4 rounded-lg space-y-2">
                            <code className="text-xs text-slate-300 block">param_grid = &#123;</code>
                            <code className="text-xs text-slate-300 block">  'n_estimators': [100, 200, 300],</code>
                            <code className="text-xs text-slate-300 block">  'max_depth': [3, 6, 10],</code>
                            <code className="text-xs text-slate-300 block">  'learning_rate': [0.01, 0.1, 0.2]</code>
                            <code className="text-xs text-slate-300 block">&#125;</code>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-6">
                        <div>
                          <h4 className="text-lg font-medium text-purple-400 mb-3">Advanced Techniques</h4>
                          <ul className="space-y-2 text-sm text-slate-300">
                            <li>• <strong>SMOTE:</strong> Synthetic oversampling</li>
                            <li>• <strong>RandomizedSearchCV:</strong> 100 iterations</li>
                            <li>• <strong>Early Stopping:</strong> Patience=10</li>
                            <li>• <strong>Cross-Validation:</strong> 5-fold stratified</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                    
                    <div className="border-t border-slate-700 pt-6">
                      <h4 className="text-lg font-medium text-purple-400 mb-4">Performance Comparison</h4>
                      <div className="grid grid-cols-3 gap-6">
                        <div className="text-center">
                          <div className="text-3xl font-bold text-purple-400">85.8%</div>
                          <div className="text-slate-300 font-medium">XGBoost Accuracy</div>
                          <div className="text-green-400 text-sm">+4.3% improvement</div>
                        </div>
                        <div className="text-center">
                          <div className="text-3xl font-bold text-purple-400">85.9%</div>
                          <div className="text-slate-300 font-medium">F1-Score</div>
                          <div className="text-green-400 text-sm">+4.2% improvement</div>
                        </div>
                        <div className="text-center">
                          <div className="text-3xl font-bold text-purple-400">11</div>
                          <div className="text-slate-300 font-medium">Feature Dimensions</div>
                          <div className="text-blue-400 text-sm">+5 enhanced features</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </ModernCard>
              </div>
            </ModernSection>

            {/* How It Works Section */}
            <ModernSection 
              title="How Predictions Are Made" 
              icon={true}
              delay={0.8}
              className="mt-32"
            >
              <ModernCard solid>
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">
                        🧠 Machine Learning Process
                      </h4>
                      <p className="text-slate-300 leading-relaxed">
                        Our system uses advanced XGBoost algorithms with label encoders to process 
                        product data. Each input is carefully analyzed and weighted based on its 
                        environmental impact potential.
                      </p>
                    </div>
                    
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">
                        📊 Confidence Scoring
                      </h4>
                      <p className="text-slate-300 leading-relaxed">
                        We use <code className="bg-slate-700 px-2 py-1 rounded text-cyan-400">predict_proba</code> to 
                        calculate confidence levels for each prediction, ensuring you know how reliable 
                        each assessment is.
                      </p>
                    </div>
                    
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">
                        🔍 Key Factors
                      </h4>
                      <p className="text-slate-300 leading-relaxed">
                        The model analyzes weight, material composition, origin location, transport 
                        methods, and recyclability to generate comprehensive sustainability scores.
                      </p>
                    </div>
                    
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">
                        ⚡ Real-time Analysis
                      </h4>
                      <p className="text-slate-300 leading-relaxed">
                        Our optimized pipeline provides instant results while maintaining high 
                        accuracy across diverse product categories and geographical regions.
                      </p>
                    </div>
                  </div>
                </div>
              </ModernCard>
            </ModernSection>

            <Footer />

            <ModelInfoModal isOpen={showModal} onClose={() => setShowModal(false)} />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
