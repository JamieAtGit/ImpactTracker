import React, { useState } from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton, ModernInput, ModernBadge } from "../components/ModernLayout";
import Header from "../components/Header";
import ChallengeForm from "../components/ChallengeForm";
import Footer from "../components/Footer";
import toast from "react-hot-toast";
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function PredictPage() {
  const [form, setForm] = useState({
    title: "",
    material: "Plastic",
    weight: 1.0,
    transport: "Air",
    recyclability: "Low",
    origin: "China",
  });

  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Calculate distance from origin to UK for backend compatibility
      const originHubs = {
        "China": { lat: 39.9, lon: 116.4 },
        "USA": { lat: 39.8, lon: -98.6 },
        "Germany": { lat: 51.2, lon: 10.4 },
        "UK": { lat: 54.8, lon: -4.6 },
        "France": { lat: 46.6, lon: 1.9 },
        "Italy": { lat: 42.5, lon: 12.6 },
        "Other": { lat: 54.8, lon: -4.6 }
      };
      
      const ukHub = { lat: 54.8, lon: -4.6 };
      const originCoords = originHubs[form.origin] || originHubs["Other"];
      
      // Simple haversine calculation
      const haversine = (lat1, lon1, lat2, lon2) => {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      };
      
      const distance = haversine(originCoords.lat, originCoords.lon, ukHub.lat, ukHub.lon);
      
      // Enhanced payload with all required fields
      const enhancedForm = {
        ...form,
        distance_origin_to_uk: distance,
        override_transport_mode: form.transport,
        title: form.title || "Manual Test Product"
      };

      console.log("🔍 Sending enhanced form:", enhancedForm);

      const response = await fetch(`${BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(enhancedForm),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to predict");
      }

      const data = await response.json();
      setResult(data);
      toast.success("✅ Prediction successful!");
    } catch (error) {
      console.error("Prediction error:", error);
      toast.error(`❌ Failed to predict: ${error.message}`);
    }
  };

  const sendFeedback = async (vote) => {
    const feedback = {
      vote,
      title: result.raw_input?.title || "unknown",
      prediction: result.predicted_label,
      confidence: result.confidence,
      raw_input: result.raw_input,
      encoded_input: result.encoded_input,
      feature_impact: result.feature_impact,
      timestamp: new Date().toISOString(),
    };

    await fetch(`${BASE_URL}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedback),
    });

    toast.success("✅ Thanks for your feedback!");
  };

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
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight">
                  <span className="text-slate-100">Predict environmental</span>
                  <br />
                  <span className="bg-gradient-to-r from-green-400 via-cyan-500 to-blue-400 bg-clip-text text-transparent">
                    impact scores
                  </span>
                </h1>
                <motion.p
                  className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  Test our AI model with custom product specifications and get instant 
                  sustainability assessments with confidence scores.
                </motion.p>
              </motion.div>
            </ModernSection>

            {/* Prediction Form */}
            <ModernSection>
              <ModernCard className="max-w-2xl mx-auto" solid hover>
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-display text-slate-200 mb-2">
                      AI Prediction Form
                    </h2>
                    <p className="text-slate-400 text-sm">
                      Enter product details to get an environmental impact prediction
                    </p>
                  </div>

                  <motion.form 
                    onSubmit={handleSubmit} 
                    className="space-y-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                  >
                    <ModernInput
                      label="Product Title"
                      name="title"
                      type="text"
                      value={form.title}
                      onChange={handleChange}
                      placeholder="e.g., Eco-Friendly Bamboo Toothbrush"
                      icon="📝"
                      required
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <ModernInput
                        label="Material"
                        name="material"
                        type="text"
                        value={form.material}
                        onChange={handleChange}
                        placeholder="e.g., Plastic, Wood, Metal"
                        icon="🏗️"
                      />

                      <ModernInput
                        label="Weight (kg)"
                        name="weight"
                        type="number"
                        step="0.1"
                        value={form.weight}
                        onChange={handleChange}
                        placeholder="1.0"
                        icon="⚖️"
                      />

                      <ModernInput
                        label="Transport Mode"
                        name="transport"
                        type="text"
                        value={form.transport}
                        onChange={handleChange}
                        placeholder="e.g., Air, Sea, Road"
                        icon="🚛"
                      />

                      <ModernInput
                        label="Recyclability"
                        name="recyclability"
                        type="text"
                        value={form.recyclability}
                        onChange={handleChange}
                        placeholder="e.g., High, Medium, Low"
                        icon="♻️"
                      />
                    </div>

                    <ModernInput
                      label="Origin Country"
                      name="origin"
                      type="text"
                      value={form.origin}
                      onChange={handleChange}
                      placeholder="e.g., China, Germany, USA"
                      icon="🌍"
                    />

                    <div className="flex justify-center pt-4">
                      <ModernButton
                        type="submit"
                        variant="accent"
                        size="lg"
                        icon="🔍"
                        className="min-w-48"
                      >
                        Predict Eco Score
                      </ModernButton>
                    </div>
                  </motion.form>
                </div>
              </ModernCard>
            </ModernSection>

            {/* Prediction Result */}
            {result && (
              <ModernSection delay={0.2}>
                <ModernCard className="max-w-2xl mx-auto" solid>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5 }}
                    className="space-y-6"
                  >
                    <div className="text-center">
                      <div className="status-indicator status-success mx-auto mb-3"></div>
                      <h3 className="text-xl font-display text-slate-200 mb-2">
                        🎯 Prediction Complete
                      </h3>
                    </div>

                    {/* Product Title Display */}
                    {form.title && (
                      <div className="text-center mb-4">
                        <p className="text-slate-500 text-sm mb-1">Product Analyzed:</p>
                        <p className="text-lg font-medium text-cyan-300 leading-relaxed">
                          {form.title}
                        </p>
                      </div>
                    )}

                    <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 p-6 rounded-lg border border-blue-500/30">
                      <div className="text-center space-y-4">
                        <div>
                          <p className="text-slate-400 text-sm mb-2">Predicted Eco Score</p>
                          <ModernBadge 
                            variant={
                              result.predicted_label === 'A+' || result.predicted_label === 'A' ? 'success' : 
                              result.predicted_label === 'B' || result.predicted_label === 'C' ? 'warning' : 'error'
                            } 
                            size="md"
                          >
                            <span className="text-lg font-bold">{result.predicted_label}</span>
                          </ModernBadge>
                        </div>
                        
                        <div>
                          <p className="text-slate-400 text-sm">Confidence Level</p>
                          <p className="text-cyan-400 font-medium">{result.confidence}</p>
                        </div>
                      </div>
                    </div>

                    {/* Eco Score Calculation Explanation */}
                    <div className="mt-6 p-4 bg-slate-800/30 rounded-lg border border-slate-600/30">
                      <h4 className="text-slate-300 font-medium mb-3 flex items-center gap-2">
                        🧮 How This Score Was Calculated
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                        <div className="space-y-2">
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Material:</span> {form.material}
                          </p>
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Weight:</span> {form.weight}kg
                          </p>
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Origin:</span> {form.origin}
                          </p>
                        </div>
                        <div className="space-y-2">
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Transport:</span> {form.transport}
                          </p>
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Recyclability:</span> {form.recyclability}
                          </p>
                          <p className="text-slate-400">
                            <span className="text-cyan-400 font-medium">Method:</span> Enhanced XGBoost ML
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-600/30">
                        <p className="text-xs text-slate-500 leading-relaxed">
                          Our AI model analyzes material composition, weight, transport distance, recyclability, 
                          and origin location to predict environmental impact scores (A+ to F scale). Higher scores 
                          indicate more sustainable products with lower carbon footprints.
                        </p>
                      </div>
                    </div>

                    <ChallengeForm
                      productId={result.raw_input?.product_id || "unknown"}
                      predictedScore={result.predicted_label}
                    />

                    <div className="flex items-center justify-center gap-6 p-4 glass-card rounded-lg">
                      <span className="text-slate-400 text-sm">Was this prediction helpful?</span>
                      <div className="flex gap-3">
                        <motion.button 
                          onClick={() => sendFeedback("up")} 
                          className="w-10 h-10 glass-card rounded-lg flex items-center justify-center hover:bg-green-500/20 transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                        >
                          👍
                        </motion.button>
                        <motion.button 
                          onClick={() => sendFeedback("down")} 
                          className="w-10 h-10 glass-card rounded-lg flex items-center justify-center hover:bg-red-500/20 transition-colors"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                        >
                          👎
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                </ModernCard>
              </ModernSection>
            )}

            {/* Footer */}
            <motion.footer
              className="text-center py-12 mt-16"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <ModernCard className="max-w-md mx-auto text-center">
                <div className="space-y-2">
                  <p className="text-slate-300 font-medium">
                    © 2025 Impact Tracker
                  </p>
                  <p className="text-slate-400 text-sm">
                    Testing sustainability predictions 🧪
                  </p>
                </div>
              </ModernCard>
            </motion.footer>
            
            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
