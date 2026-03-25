
import React from "react";
import { motion } from "framer-motion";
import { ModernCard, ModernButton, ModernBadge } from "./ModernLayout";
import MLvsDEFRAChart from "./MLvsDefraChart";
import CarbonMetricsCircle from "./CarbonMetricsCircle";
import ShapExplanation from "./ShapExplanation";
import CounterfactualExplanation from "./CounterfactualExplanation";
import AlternativeRecommendations from "./AlternativeRecommendations";
import ConfidenceDistributionChart from "./ConfidenceDistributionChart";
import ConformalPredictionBadge from "./ConformalPredictionBadge";

export default function ProductImpactCard({ result, showML, toggleShowML }) {
  const attr = result.attributes || {};
  const originKm = parseFloat(attr.distance_from_origin_km || 0);
  const ukKm = parseFloat(attr.distance_from_uk_hub_km || 0);
  
  // Get both predictions for comparison
  const mlScore = attr.eco_score_ml || "N/A";
  const mlConfidence = attr.eco_score_ml_confidence || "N/A";
  const ruleScore = attr.eco_score_rule_based || "N/A";
  const methodAgreement = attr.method_agreement || "No";
  const _treesExact = (parseFloat(attr.carbon_kg) || 0) / 21;
  const treesToOffset = Math.ceil(_treesExact) || 1;
  const treesDisplay = _treesExact < 1
    ? `${Math.round(_treesExact * 365)} days of tree absorption`
    : `${treesToOffset} tree${treesToOffset > 1 ? "s" : ""}`;
  
  // For the main eco score display (use ML score as primary)
  const ecoScore = mlScore;
  const confidence = typeof mlConfidence === 'number' ? mlConfidence : 
                    typeof mlConfidence === 'string' && mlConfidence.includes('%') ? 
                    parseFloat(mlConfidence) : null;
  
  const getEmojiForScore = (score) => ({
    "A+": "🌍", A: "🌿", B: "🍃", C: "🌱", D: "⚠️", E: "❌", F: "💀"
  }[score] || "🔍");

  const emoji = getEmojiForScore(ecoScore);

  const [materialAvg, setMaterialAvg] = React.useState(null);
  const _parsedPrice = parseFloat(attr.price);
  const price = (!isNaN(_parsedPrice) && _parsedPrice > 0) ? _parsedPrice : null;
  const co2PerPound = (price && attr.carbon_kg && price > 0)
    ? (parseFloat(attr.carbon_kg) / price).toFixed(3)
    : null;

  // CO₂ real-world equivalents
  const carbonKg = parseFloat(attr.carbon_kg || 0);
  const equivalents = carbonKg > 0 ? [
    { icon: "🚗", label: "km driven", value: Math.round(carbonKg / 0.21) },
    { icon: "📱", label: "phone charges", value: Math.round(carbonKg / 0.005) },
    { icon: "💻", label: "hrs laptop use", value: Math.round(carbonKg / 0.05) },
    { icon: "✈️", label: "% LHR→JFK flight", value: (carbonKg / 300 * 100).toFixed(1) },
  ] : [];

  React.useEffect(() => {
    const mat = attr.material_type;
    if (!mat || mat === 'Not found') return;
    const BASE_URL = import.meta.env.VITE_API_BASE_URL;
    fetch(`${BASE_URL}/api/material-avg?material=${encodeURIComponent(mat)}`)
      .then(r => r.json())
      .then(d => { if (d.avg_co2_kg && d.sample_size >= 5) setMaterialAvg(d); })
      .catch(() => {});
  }, [attr.material_type]);

  return (
    <ModernCard className="max-w-6xl mx-auto" solid>
      {/* Header with Product Name */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4 mb-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="status-indicator status-success"></div>
            <h3 className="text-xl font-display text-slate-200">
              🌍 Impact Analysis Complete
            </h3>
          </div>
          {/* Product Name Display - MAIN INSTANCE */}
          {result.title && result.title !== "Unknown Product" && (
            <div className="ml-8 p-3 bg-slate-800/50 rounded-lg border border-slate-700" data-component="main-product-title">
              <p className="text-sm text-slate-400 mb-2 flex items-center gap-2">
                <span>📦</span> Product Analyzed:
              </p>
              <p className="text-lg font-medium text-cyan-300 leading-relaxed">
                {result.title}
              </p>
              {result.attributes?.brand && result.attributes.brand !== "Unknown" && (
                <p className="text-sm text-slate-400 mt-1">
                  by <span className="text-amber-400">{result.attributes.brand}</span>
                </p>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <ModernBadge 
            variant={methodAgreement === "Yes" ? "success" : "warning"}
            size="sm"
          >
            {methodAgreement === "Yes" ? "🤝 Methods Agree" : "⚡ Methods Disagree"}
          </ModernBadge>
        </div>
      </div>

      {/* Method Comparison Section */}
      <motion.div
        className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        {/* ML Prediction */}
        <div className="p-4 glass-card rounded-lg border-l-4 border-cyan-500">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">🧠</span>
            <h4 className="text-lg font-medium text-slate-200">ML Prediction</h4>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getEmojiForScore(mlScore)}</span>
              <ModernBadge 
                variant={
                  mlScore === 'A+' || mlScore === 'A' ? 'success' : 
                  mlScore === 'B' || mlScore === 'C' ? 'warning' : 'error'
                } 
                size="md"
              >
                {mlScore || 'N/A'}
              </ModernBadge>
            </div>
            <p className="text-sm text-slate-400">
              Confidence: {typeof mlConfidence === 'number' ? `${mlConfidence}%` : mlConfidence || 'N/A'}
            </p>
            <p className="text-xs text-slate-500">
              Enhanced XGBoost (11 features)
            </p>
          </div>
        </div>

        {/* Rule-Based Prediction */}
        <div className="p-4 glass-card rounded-lg border-l-4 border-amber-500">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-lg">📊</span>
            <h4 className="text-lg font-medium text-slate-200">Standard Method</h4>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getEmojiForScore(ruleScore)}</span>
              <ModernBadge 
                variant={
                  ruleScore === 'A+' || ruleScore === 'A' ? 'success' : 
                  ruleScore === 'B' || ruleScore === 'C' ? 'warning' : 'error'
                } 
                size="md"
              >
                {ruleScore || 'N/A'}
              </ModernBadge>
            </div>
            <p className="text-sm text-slate-400">
              Confidence: 80%
            </p>
            <p className="text-xs text-slate-500">
              Traditional calculation method
            </p>
          </div>
        </div>
      </motion.div>

      {/* Product Title */}
      <motion.div
        className="mb-6 p-4 glass-card rounded-lg"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h4 className="text-lg font-medium text-slate-200 leading-tight">
          {result.title}
        </h4>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Details */}
        <motion.div
          className="space-y-4"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h4 className="text-lg font-display text-slate-200 mb-4">
            Product Specifications
          </h4>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">Weight (Raw):</span>
              <span className="font-medium text-slate-200">
                {attr.raw_product_weight_kg} kg
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">Weight (+ Packaging):</span>
              <span className="font-medium text-slate-200">
                {attr.weight_kg} kg
              </span>
            </div>
            
            <div className="p-3 glass-card rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-slate-400">Country of Origin:</span>
                <ModernBadge variant="default" size="sm">
                  {attr.country_of_origin || attr.origin}
                </ModernBadge>
              </div>
              {attr.facility_origin && attr.facility_origin !== "Unknown" && (
                <div className="pt-2 border-t border-slate-700">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Manufacturing Facility:</span>
                    <span className="text-xs text-slate-300 font-medium">
                      {attr.facility_origin}
                    </span>
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-3 glass-card rounded-lg">
              {/* Enhanced Materials Display with 5-Tier Intelligence */}
              {console.log("🐛 DEBUG ProductImpactCard - Full result:", result)}
              {console.log("🐛 DEBUG ProductImpactCard - attr:", attr)}
              {console.log("🐛 DEBUG ProductImpactCard - attr.materials:", attr.materials)}
              {console.log("🐛 DEBUG ProductImpactCard - attr.material_type:", attr.material_type)}
              {attr.materials?.tier && attr.materials?.primary_material && 
               attr.materials?.primary_material !== 'Mixed' && attr.materials?.primary_material !== 'Unknown' ? (
                <>
                  {/* Primary Material with Tier Info */}
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-400">Primary Material:</span>
                    <div className="flex items-center gap-2">
                      <ModernBadge variant="info" size="sm">
                        {attr.materials.primary_material}
                        {attr.materials.primary_percentage && !isNaN(parseFloat(attr.materials.primary_percentage)) ? ` (${attr.materials.primary_percentage}%)` : ''}
                      </ModernBadge>
                    </div>
                  </div>
                  
                  {/* Tier & Confidence Info */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-xs text-emerald-400">
                      Tier {attr.materials.tier}: {attr.materials.tier_name}
                    </span>
                    <span className="text-xs text-emerald-400">
                      {((attr.materials.confidence || 0) * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  
                  {/* Secondary Materials */}
                  {attr.materials?.secondary_materials && attr.materials.secondary_materials.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-700">
                      <p className="text-xs text-slate-500 mb-2">Secondary Materials:</p>
                      <div className="flex flex-wrap gap-1">
                        {attr.materials.secondary_materials.map((material, index) => (
                          <span 
                            key={index}
                            className="inline-block px-2 py-1 text-xs bg-slate-800 text-slate-300 rounded border border-slate-600"
                          >
                            {material.name} {material.percentage && !isNaN(parseFloat(material.percentage)) ? `(${material.percentage}%)` : ''}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Environmental Impact Score */}
                  {attr.materials?.environmental_impact_score && (
                    <div className="mt-2 pt-2 border-t border-slate-700">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-500">Material Impact Score:</span>
                        <span className="text-xs text-amber-400 font-medium">
                          {attr.materials.environmental_impact_score} kg CO₂/kg
                        </span>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {/* Fallback to basic material display */}
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-400">Material Type:</span>
                    <ModernBadge variant="info" size="sm">
                      {attr.material_type || "Unknown"}
                    </ModernBadge>
                  </div>
                  
                  {/* Show tier info even for fallback */}
                  {attr.materials?.tier && (
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-yellow-400">
                        Tier {attr.materials.tier}: {attr.materials.tier_name || 'Basic detection'}
                      </span>
                      <span className="text-xs text-yellow-400">
                        {((attr.materials.confidence || 0.3) * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                  )}
                  
                  {/* Show any available materials breakdown */}
                  {attr.materials?.all_materials && attr.materials.all_materials.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-700">
                      <p className="text-xs text-slate-500 mb-2">Material Breakdown:</p>
                      <div className="flex flex-wrap gap-1">
                        {attr.materials.all_materials.map((material, index) => (
                          <span 
                            key={index}
                            className="inline-block px-2 py-1 text-xs bg-slate-800 text-slate-300 rounded border border-slate-600"
                          >
                            {material.name} {material.weight && !isNaN(material.weight) ? `(${(material.weight * 100).toFixed(0)}%)` : ''}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
            
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">Transport Mode:</span>
              <span className="font-medium text-slate-200">
                {attr.transport_mode}
              </span>
            </div>
            
            <div className="p-3 glass-card rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-slate-400">Recyclability:</span>
                <ModernBadge 
                  variant={attr.recyclability === 'High' ? 'success' : 
                         attr.recyclability === 'Medium' ? 'warning' : 'error'} 
                  size="sm"
                >
                  {attr.recyclability}
                </ModernBadge>
              </div>
              {attr.recyclability_percentage && (
                <div className="text-xs text-slate-500 mt-1">
                  {attr.recyclability_percentage}% recyclable
                  {attr.recyclability_description && (
                    <div className="mt-1 text-slate-400">
                      {attr.recyclability_description}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Sold by / Dispatched from */}
            {(attr.sold_by || attr.dispatched_from) && (
              <div className="p-3 glass-card rounded-lg space-y-2">
                {attr.sold_by && attr.sold_by !== "Not found" && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Sold by:</span>
                    <span className="text-slate-200 text-sm font-medium text-right max-w-[55%] truncate">
                      {attr.sold_by}
                    </span>
                  </div>
                )}
                {attr.dispatched_from && attr.dispatched_from !== "Not found" && (
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Dispatched from:</span>
                    <span className="text-slate-200 text-sm font-medium text-right max-w-[55%] truncate">
                      {attr.dispatched_from}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>

        {/* Environmental Impact */}
        <motion.div
          className="space-y-4"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h4 className="text-lg font-display text-slate-200 mb-4">
            Environmental Impact
          </h4>
          
          {/* Eco Score Display */}
          <div className="p-6 glass-card rounded-lg border border-cyan-500/30">
            <div className="text-center space-y-3">
              <div className="flex items-center justify-center gap-3">
                <span className="text-4xl font-display font-bold text-cyan-400">
                  {ecoScore}
                </span>
                <span className="text-3xl">{emoji}</span>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Eco Score</p>
                <ModernBadge variant="info" size="sm">
                  {typeof confidence === "number"
                    ? `${confidence.toFixed(1)}% confidence`
                    : "Confidence: N/A"}
                </ModernBadge>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">Carbon Emissions:</span>
              <span className="font-medium text-red-400">
                {attr.carbon_kg} kg CO₂
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">🌳 Trees to Offset:</span>
              <ModernBadge variant="success" size="sm">
                {treesDisplay}
              </ModernBadge>
            </div>
            
            {/* Price & CO₂ per £ */}
            {price && (
              <div className="p-3 glass-card rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Price:</span>
                  <span className="font-medium text-slate-200">£{price.toFixed(2)}</span>
                </div>
                {co2PerPound && (
                  <div className="flex justify-between items-center mt-1.5">
                    <span className="text-slate-400 text-xs">CO₂ per £ spent:</span>
                    <span className="text-amber-400 font-mono text-xs">{co2PerPound} kg/£</span>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">International Distance:</span>
              <span className="font-medium text-slate-200">
                {originKm.toFixed(1)} km
              </span>
            </div>
            
            <div className="flex justify-between items-center p-3 glass-card rounded-lg">
              <span className="text-slate-400">UK Hub Distance:</span>
              <span className="font-medium text-slate-200">
                {ukKm.toFixed(1)} km
              </span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Charts Section */}
      <motion.div
        className="mt-8 space-y-8"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        {/* Carbon Metrics Circle */}
        <CarbonMetricsCircle
          carbonKg={attr.carbon_kg}
          ecoScore={attr.eco_score_ml}
          recyclability={attr.recyclability}
          recyclabilityPercentage={attr.recyclability_percentage}
          treesToOffset={treesToOffset}
        />

        {/* CO₂ Real-World Equivalents */}
        {equivalents.length > 0 && (
          <motion.div
            className="glass-card p-5 rounded-xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h4 className="text-slate-200 font-display font-semibold mb-4 flex items-center gap-2">
              <span>🌍</span> That's equivalent to…
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {equivalents.map(eq => (
                <div key={eq.label} className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-3 text-center">
                  <div className="text-2xl mb-1">{eq.icon}</div>
                  <div className="text-slate-100 font-bold text-lg font-mono">{eq.value}</div>
                  <div className="text-slate-500 text-xs mt-0.5">{eq.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Amazon Climate Pledge Friendly */}
        {attr.climate_pledge_friendly !== undefined && (
          <motion.div
            className={`p-4 rounded-xl border ${attr.climate_pledge_friendly ? 'bg-emerald-500/8 border-emerald-500/30' : 'bg-slate-800/40 border-slate-700/40'}`}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25 }}
          >
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${attr.climate_pledge_friendly ? 'bg-emerald-500/20' : 'bg-slate-700/60'}`}>
                <span className="text-xl">{attr.climate_pledge_friendly ? '🌿' : '🔍'}</span>
              </div>
              <div className="flex-1">
                <p className="text-slate-200 font-medium text-sm">
                  Amazon Climate Pledge Friendly
                </p>
                {attr.climate_pledge_friendly ? (
                  <>
                    <p className="text-emerald-400 text-xs mt-0.5">✅ Badge detected on this listing</p>
                    <p className="text-slate-500 text-xs mt-1">
                      Amazon's label and our ML model {mlScore <= 'C' ? 'agree' : 'disagree'} — our grade is <span className="text-slate-300 font-medium">{mlScore}</span>.
                      {mlScore > 'C' ? ' Our model flags higher environmental cost despite the badge.' : ''}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-slate-400 text-xs mt-0.5">No badge found on this listing</p>
                    <p className="text-slate-500 text-xs mt-1">
                      Amazon has not labelled this product as Climate Pledge Friendly. Our ML grade is <span className="text-slate-300 font-medium">{mlScore}</span>.
                    </p>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Material Average Comparison */}
        {materialAvg && attr.carbon_kg && (
          <motion.div
            className="glass-card p-5 rounded-xl"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h4 className="text-slate-200 font-display font-semibold mb-3 flex items-center gap-2">
              <span>📊</span> vs. Similar Products
            </h4>
            <p className="text-slate-500 text-xs mb-3">
              Average CO₂ across {materialAvg.sample_size} {attr.material_type} products in our database
            </p>
            {(() => {
              const thisVal = parseFloat(attr.carbon_kg);
              const avgVal  = materialAvg.avg_co2_kg;
              const diff    = ((thisVal - avgVal) / avgVal * 100).toFixed(0);
              const better  = thisVal < avgVal;
              return (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">This product</span>
                    <span className="text-slate-200 font-mono">{thisVal.toFixed(2)} kg CO₂</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">{attr.material_type} average</span>
                    <span className="text-slate-400 font-mono">{avgVal.toFixed(2)} kg CO₂</span>
                  </div>
                  <div className={`flex items-center gap-2 mt-2 px-3 py-2 rounded-lg text-sm font-medium ${better ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    <span>{better ? '✅' : '⚠️'}</span>
                    <span>
                      {better
                        ? `${Math.abs(diff)}% below average for ${attr.material_type} products`
                        : `${Math.abs(diff)}% above average for ${attr.material_type} products`
                      }
                    </span>
                  </div>
                </div>
              );
            })()}
          </motion.div>
        )}

        {/* ML vs DEFRA Chart with Toggle */}
        <div className="space-y-4">
          {/* Toggle Button */}
          <div className="flex justify-between items-center">
            <h4 className="text-lg font-display text-slate-200">
              📊 Methodology Comparison
            </h4>
            <ModernButton
              variant={showML ? "default" : "accent"}
              size="sm"
              onClick={toggleShowML}
              className="flex items-center gap-2"
            >
              <span>💡</span>
              <span>
                {showML ? "Show Comparison" : "AI Only"}
              </span>
            </ModernButton>
          </div>
          
          {/* Comparison Mode Indicator */}
          <div className="text-center">
            <ModernBadge 
              variant={showML ? "warning" : "success"}
              size="sm"
            >
              {showML 
                ? "🧠 AI Prediction Only" 
                : "⚡ AI vs Standard Method Comparison"
              }
            </ModernBadge>
            <p className="text-xs text-slate-500 mt-2">
              {showML 
                ? "Click toggle to compare AI vs traditional calculation method" 
                : "Comparing advanced AI model against standard environmental calculation"
              }
            </p>
          </div>

          {/* Chart */}
          <MLvsDEFRAChart
            showML={showML}
            result={result}
          />
        </div>

        {/* SHAP per-prediction explanation */}
        {attr.shap_explanation && (
          <ShapExplanation data={attr.shap_explanation} />
        )}

        {/* Grade probability distribution */}
        {attr.proba_distribution && attr.proba_distribution.length > 0 && (
          <ConfidenceDistributionChart
            data={attr.proba_distribution}
            predictedGrade={mlScore}
          />
        )}

        {/* Conformal prediction sets */}
        {attr.conformal_sets && (
          <ConformalPredictionBadge
            conformalSets={attr.conformal_sets}
            predictedGrade={mlScore}
          />
        )}

        {/* Counterfactual explanations — what single change would improve the grade */}
        {attr.counterfactuals && attr.counterfactuals.length > 0 && (
          <CounterfactualExplanation data={attr.counterfactuals} />
        )}

        {/* Add to Carbon Basket */}
        <motion.div
          className="mt-6 flex justify-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.6 }}
        >
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("basket:add", {
              detail: { title: result.title, grade: mlScore, co2: attr.carbon_kg }
            }))}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600/20 border border-emerald-500/40 hover:bg-emerald-600/30 hover:border-emerald-500/70 text-emerald-400 text-sm font-medium transition-colors"
          >
            <span>🧺</span>
            Add to Carbon Basket
          </button>
        </motion.div>

        {/* Greener alternatives from the dataset (only shown for D / E / F grades) */}
        <AlternativeRecommendations
          grade={mlScore}
          category={attr.category}
          currentCo2={attr.carbon_kg}
          productTitle={result.title}
        />
      </motion.div>
    </ModernCard>
  );
}
