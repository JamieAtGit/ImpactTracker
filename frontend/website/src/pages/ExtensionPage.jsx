import React from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function ExtensionPage() {
  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-8">
            {/* Hero Section */}
            <ModernSection className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-6"
              >
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-2xl mb-6">
                  <span className="text-3xl">🧩</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight">
                  <span className="text-slate-100">Install the</span>
                  <br />
                  <span className="bg-gradient-to-r from-green-400 via-cyan-500 to-blue-400 bg-clip-text text-transparent">
                    Impact Tracker Extension
                  </span>
                </h1>
                <motion.p
                  className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  Get real-time environmental impact assessments while browsing Amazon. 
                  See eco-scores, material analysis, and sustainability recommendations instantly.
                </motion.p>
              </motion.div>
            </ModernSection>

            {/* Download Button */}
            <ModernSection>
              <div className="flex justify-center">
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                >
                  <ModernButton
                    variant="accent"
                    size="lg"
                    icon="⬇️"
                    className="min-w-64"
                    onClick={() => window.open(`${import.meta.env.VITE_API_BASE_URL}/static/my-extension.zip`, "_blank")}
                  >
                    Download Extension
                  </ModernButton>
                </motion.div>
              </div>
            </ModernSection>

            {/* Features Grid */}
            <div className="grid md:grid-cols-2 gap-8">
              <ModernSection delay={0.3}>
                <ModernCard solid>
                  <div className="space-y-6">
                    <h2 className="text-xl font-display text-slate-200 flex items-center gap-3">
                      <span className="text-2xl">✨</span>
                      What You'll Get
                    </h2>
                    <ul className="space-y-4">
                      <li className="flex items-start gap-3">
                        <span className="text-xl">🧠</span>
                        <span className="text-slate-300">Automatic eco score predictions as you browse products</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-xl">♻️</span>
                        <span className="text-slate-300">Detailed material tooltips with environmental insights</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-xl">📊</span>
                        <span className="text-slate-300">Emissions estimator based on weight and transport type</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="text-xl">🧪</span>
                        <span className="text-slate-300">Data backed by machine learning and verified sources</span>
                      </li>
                    </ul>
                  </div>
                </ModernCard>
              </ModernSection>

              <ModernSection delay={0.4}>
                <ModernCard solid>
                  <div className="space-y-6">
                    <h2 className="text-xl font-display text-slate-200 flex items-center gap-3">
                      <span className="text-2xl">🛠</span>
                      How to Install
                    </h2>
                    <ol className="space-y-4">
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-sm font-bold rounded-full flex items-center justify-center">1</span>
                        <span className="text-slate-300">Unzip the downloaded extension file.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-sm font-bold rounded-full flex items-center justify-center">2</span>
                        <span className="text-slate-300">Open Chrome and go to <code className="bg-slate-700 px-2 py-1 rounded text-cyan-400 text-sm">chrome://extensions</code>.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-sm font-bold rounded-full flex items-center justify-center">3</span>
                        <span className="text-slate-300">Enable "Developer mode" in the top-right corner.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-sm font-bold rounded-full flex items-center justify-center">4</span>
                        <span className="text-slate-300">Click "Load unpacked" and select the unzipped folder.</span>
                      </li>
                      <li className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-sm font-bold rounded-full flex items-center justify-center">5</span>
                        <span className="text-slate-300">Visit Amazon and see Impact Tracker in action!</span>
                      </li>
                    </ol>
                  </div>
                </ModernCard>
              </ModernSection>
            </div>

            {/* Preview Section */}
            <ModernSection 
              title="Extension Preview" 
              icon={true}
              delay={0.5}
            >
              <ModernCard solid className="p-8">
                <div className="space-y-8">
                  <div className="text-center">
                    <p className="text-slate-400">
                      See how the extension enhances your Amazon shopping experience with real-time environmental insights
                    </p>
                  </div>
                  
                  {/* Amazon Product Page Mockup */}
                  <div className="relative bg-white rounded-xl overflow-hidden border-2 border-slate-600">
                    {/* Amazon Header */}
                    <div className="bg-slate-900 p-4 flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-orange-400 font-bold text-lg">amazon</div>
                        <div className="bg-slate-700 px-3 py-1 rounded text-slate-300 text-sm">Search: "wireless headphones"</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">ET</span>
                        </div>
                        <span className="text-cyan-400 text-sm font-medium">EcoTracker Active</span>
                      </div>
                    </div>
                    
                    {/* Product Content */}
                    <div className="p-6 bg-white">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Product Image Area */}
                        <div className="relative">
                          <div className="bg-slate-100 rounded-lg p-8 flex items-center justify-center h-64">
                            <div className="text-center">
                              <div className="w-32 h-32 bg-slate-300 rounded-lg mx-auto mb-4 flex items-center justify-center">
                                <span className="text-4xl">🎧</span>
                              </div>
                              <p className="text-slate-600 text-sm">Sony WH-1000XM4 Headphones</p>
                            </div>
                          </div>
                          
                          {/* Extension Tooltip */}
                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8, delay: 1.5 }}
                            className="absolute top-4 right-4 bg-slate-900 rounded-xl p-4 shadow-2xl border border-cyan-500/20 min-w-64"
                          >
                            <div className="space-y-4">
                              <div className="flex items-center justify-between">
                                <h3 className="text-cyan-400 font-semibold">Environmental Impact</h3>
                                <div className="w-6 h-6 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
                                  <span className="text-white text-xs">🌍</span>
                                </div>
                              </div>
                              
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-slate-300 text-sm">Eco Score</span>
                                  <div className="flex items-center space-x-2">
                                    <div className="text-green-400 font-bold">B+</div>
                                    <div className="text-slate-400 text-xs">(85/100)</div>
                                  </div>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-slate-300 text-sm">Material</span>
                                  <span className="text-slate-400 text-sm">Recycled Plastic</span>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-slate-300 text-sm">Carbon Footprint</span>
                                  <span className="text-orange-400 text-sm font-medium">2.4 kg CO₂</span>
                                </div>
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-slate-300 text-sm">Recyclability</span>
                                  <span className="text-green-400 text-sm">High</span>
                                </div>
                              </div>
                              
                              <div className="pt-3 border-t border-slate-700">
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-slate-400">Powered by ML predictions</span>
                                  <div className="w-1 h-1 bg-slate-600 rounded-full"></div>
                                  <span className="text-xs text-cyan-400">85.8% accuracy</span>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        </div>
                        
                        {/* Product Details */}
                        <div className="space-y-4">
                          <h1 className="text-2xl font-bold text-slate-900">
                            Sony WH-1000XM4 Wireless Noise Canceling Headphones
                          </h1>
                          
                          <div className="flex items-center space-x-4">
                            <div className="flex text-orange-400">
                              {'★'.repeat(4)}{'☆'.repeat(1)}
                            </div>
                            <span className="text-blue-600 text-sm">28,547 ratings</span>
                          </div>
                          
                          <div className="text-3xl font-bold text-slate-900">
                            £279.00
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-600">Material:</span>
                              <span className="text-slate-900">Recycled Plastic</span>
                              <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 2.0 }}
                                className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full border border-green-200"
                              >
                                ♻️ Eco-Friendly
                              </motion.div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-600">Weight:</span>
                              <span className="text-slate-900">254g</span>
                            </div>
                          </div>
                          
                          <div className="pt-4">
                            <button className="bg-orange-400 hover:bg-orange-500 text-white px-8 py-3 rounded-lg font-medium transition-colors">
                              Add to Cart
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Extension Features Highlight */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 2.5 }}
                      className="text-center p-4 bg-slate-800/50 rounded-lg"
                    >
                      <div className="text-2xl mb-2">🎯</div>
                      <h4 className="font-medium text-slate-200 mb-1">Real-time Analysis</h4>
                      <p className="text-slate-400 text-sm">Instant eco-scores powered by machine learning</p>
                    </motion.div>
                    
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 2.7 }}
                      className="text-center p-4 bg-slate-800/50 rounded-lg"
                    >
                      <div className="text-2xl mb-2">📊</div>
                      <h4 className="font-medium text-slate-200 mb-1">Detailed Metrics</h4>
                      <p className="text-slate-400 text-sm">Material analysis and carbon footprint data</p>
                    </motion.div>
                    
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 2.9 }}
                      className="text-center p-4 bg-slate-800/50 rounded-lg"
                    >
                      <div className="text-2xl mb-2">🔄</div>
                      <h4 className="font-medium text-slate-200 mb-1">Seamless Integration</h4>
                      <p className="text-slate-400 text-sm">Works naturally with your Amazon browsing</p>
                    </motion.div>
                  </div>
                </div>
              </ModernCard>
            </ModernSection>

            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
