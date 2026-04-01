import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ModernCard, ModernButton, ModernBadge } from "./ModernLayout";
import MLvsDEFRAChart from "./MLvsDefraChart";
import CarbonMetricsCircle from "./CarbonMetricsCircle";
import ShapExplanation from "./ShapExplanation";
import CounterfactualExplanation from "./CounterfactualExplanation";
import AlternativeRecommendations from "./AlternativeRecommendations";
import ConfidenceDistributionChart from "./ConfidenceDistributionChart";
import ConformalPredictionBadge from "./ConformalPredictionBadge";
import LifecycleAssessment from "./LifecycleAssessment";
import ImageMaterialAnalysis from "./ImageMaterialAnalysis";
import { getMaterialAvg } from "../services/api";

const TABS = ["Specifications", "Overview", "Deep Analysis"];

function Tab({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
        active
          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
          : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
      }`}
    >
      {label}
    </button>
  );
}

function ScoreCard({ icon, label, score, sub, accentClass }) {
  return (
    <div className={`p-4 glass-card rounded-xl border-t-2 ${accentClass} flex flex-col gap-1`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-base">{icon}</span>
        <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-2xl font-bold text-slate-100">{score}</div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}

function Row({ label, value, badge, badgeVariant }) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-slate-700/40 last:border-0">
      <span className="text-slate-400 text-sm">{label}</span>
      {badge
        ? <ModernBadge variant={badgeVariant || "default"} size="sm">{value}</ModernBadge>
        : <span className="text-slate-200 text-sm font-medium text-right max-w-[55%]">{value}</span>
      }
    </div>
  );
}

export default function ProductImpactCard({ result, showML, toggleShowML }) {
  const [activeTab, setActiveTab] = React.useState(0);
  const [materialAvg, setMaterialAvg] = React.useState(null);
  const tabBarRef = React.useRef(null);

  const handleTabChange = React.useCallback((i) => {
    setActiveTab(i);
    // After the AnimatePresence transition begins, scroll the tab bar into view
    // so the user lands at the top of the new tab content rather than wherever
    // the previous tab's scroll position left them.
    requestAnimationFrame(() => {
      tabBarRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  }, []);

  const attr = result.attributes || {};
  const originKm = parseFloat(attr.distance_from_origin_km || 0);
  const ukKm     = parseFloat(attr.distance_from_uk_hub_km || 0);

  const mlScore         = attr.eco_score_ml || "N/A";
  const mlConfidence    = attr.eco_score_ml_confidence || "N/A";
  const ruleScore       = attr.eco_score_rule_based || "N/A";
  const methodAgreement = attr.method_agreement || "No";
  const co2UncertaintyPct = attr.co2_uncertainty_pct ?? null;
  const dataQuality = attr.data_quality || null;

  const carbonKg    = parseFloat(attr.carbon_kg || 0);
  const _treesExact = carbonKg / 21;
  const treesCount  = Math.ceil(_treesExact) || 1;
  const treesLabel  = _treesExact < 1
    ? `${Math.round(_treesExact * 365)}d tree absorption`
    : `${treesCount} tree${treesCount > 1 ? "s" : ""} to offset`;

  const _parsedPrice = parseFloat(attr.price);
  const price = (!isNaN(_parsedPrice) && _parsedPrice > 0) ? _parsedPrice : null;
  const co2PerPound = (price && carbonKg > 0)
    ? (carbonKg / price).toFixed(3) : null;

  const confidence = typeof mlConfidence === "number" ? mlConfidence
    : typeof mlConfidence === "string" && mlConfidence.includes("%")
      ? parseFloat(mlConfidence) : null;

  const getEmojiForScore = s => ({ "A+": "🌍", A: "🌿", B: "🍃", C: "🌱", D: "⚠️", E: "❌", F: "💀" }[s] || "🔍");
  const getScoreVariant  = s => (s === "A+" || s === "A" ? "success" : s === "B" || s === "C" ? "warning" : "error");

  const equivalents = carbonKg > 0 ? [
    { icon: "🚗", label: "km driven",        value: Math.round(carbonKg / 0.21).toLocaleString() },
    { icon: "📱", label: "phone charges",     value: Math.round(carbonKg / 0.005).toLocaleString() },
    { icon: "💻", label: "hrs laptop use",    value: Math.round(carbonKg / 0.05).toLocaleString() },
    { icon: "✈️", label: "% LHR→JFK flight", value: `${(carbonKg / 300 * 100).toFixed(1)}%` },
    { icon: "🌳", label: treesLabel,          value: _treesExact < 1 ? `${Math.round(_treesExact * 365)}d` : treesCount },
  ] : [];

  React.useEffect(() => {
    const mat = attr.material_type;
    if (!mat || mat === "Not found") return;
    getMaterialAvg(mat)
      .then(d => { if (d.avg_co2_kg && d.sample_size >= 5) setMaterialAvg(d); })
      .catch(() => {});
  }, [attr.material_type]);

  // Primary material display
  const primaryMaterial = attr.materials?.primary_material && attr.materials.primary_material !== "Mixed"
    ? attr.materials.primary_material : attr.material_type || "Unknown";
  const materialTier = attr.materials?.tier;
  const materialConf = attr.materials?.confidence;

  return (
    <ModernCard className="max-w-5xl mx-auto" solid>

      {/* ── Header ── */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="status-indicator status-success" />
            <span className="text-slate-300 text-sm font-medium">Impact Analysis Complete</span>
          </div>
          <ModernBadge variant={methodAgreement === "Yes" ? "success" : "warning"} size="sm">
            {methodAgreement === "Yes" ? "🤝 Methods Agree" : "⚡ Methods Disagree"}
          </ModernBadge>
        </div>

        {result.title && result.title !== "Unknown Product" && (
          <div className="p-4 bg-slate-800/60 rounded-xl border border-slate-700/60">
            <p className="text-xs text-slate-500 mb-1 flex items-center gap-1.5">
              <span>📦</span> Product Analysed
            </p>
            <p className="text-base font-semibold text-cyan-300 leading-snug line-clamp-2">
              {result.title}
            </p>
            {result.attributes?.brand && result.attributes.brand !== "Unknown" && (
              <p className="text-xs text-slate-400 mt-1">
                by <span className="text-amber-400 font-medium">{result.attributes.brand}</span>
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── Score cards ── */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <ScoreCard
          icon="🧠"
          label="ML Grade"
          score={`${getEmojiForScore(mlScore)} ${mlScore}`}
          sub={confidence ? `${confidence.toFixed(1)}% confidence` : "XGBoost classifier"}
          accentClass="border-cyan-500"
        />
        <ScoreCard
          icon="📊"
          label="Formula Grade"
          score={`${getEmojiForScore(ruleScore)} ${ruleScore}`}
          sub="CO₂ threshold method"
          accentClass="border-amber-500"
        />
        <ScoreCard
          icon="💨"
          label="CO₂ Estimate"
          score={carbonKg > 0 ? `${carbonKg} kg` : "N/A"}
          sub={co2UncertaintyPct != null ? `±${co2UncertaintyPct}% uncertainty` : "Formula-based"}
          accentClass="border-red-500"
        />
      </div>

      {/* ── Tabs ── */}
      <div ref={tabBarRef} className="flex items-center gap-2 mb-5 p-1 bg-slate-800/50 rounded-xl border border-slate-700/40">
        {TABS.map((t, i) => (
          <Tab key={t} label={t} active={activeTab === i} onClick={() => handleTabChange(i)} />
        ))}
      </div>

      {/* ── Tab content ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.22 }}
        >

          {/* ════ SPECIFICATIONS ════ */}
          {activeTab === 0 && (
            <div className="space-y-4">

              {/* Weights */}
              <div className="glass-card rounded-xl p-4">
                <h4 className="text-slate-300 font-semibold text-sm mb-3">⚖️ Weight</h4>
                <Row label="Product weight" value={`${attr.raw_product_weight_kg} kg`} />
                <Row label="Weight incl. packaging" value={`${attr.weight_kg} kg`} />
                {(() => {
                  const env = result?.data?.environmental_metrics;
                  if (!env?.efficiency || !env?.efficiency_label) return null;
                  const variantMap = { Excellent: "success", Good: "success", Average: "warning", Poor: "error" };
                  return (
                    <>
                      <Row
                        label="Packaging density"
                        value={`${env.efficiency_label} · ${env.efficiency} kg/L`}
                        badge
                        badgeVariant={variantMap[env.efficiency_label] || "default"}
                      />
                      <p className="text-slate-600 text-xs mt-1 leading-relaxed">
                        How efficiently the product fills its box. Lower density = more empty space in packaging.
                      </p>
                    </>
                  );
                })()}
              </div>

              {/* Origin & manufacturing — grouped */}
              <div className="glass-card rounded-xl p-4">
                <h4 className="text-slate-300 font-semibold text-sm mb-3">🌐 Origin & Manufacturing</h4>
                <Row
                  label="Country of origin"
                  value={attr.country_of_origin || attr.origin || "Unknown"}
                  badge badgeVariant="default"
                />
                {attr.facility_origin && attr.facility_origin !== "Unknown" && (
                  <Row label="Manufacturing facility" value={attr.facility_origin} />
                )}
                <Row label="Transport mode" value={attr.transport_mode || "Unknown"} />
                <Row label="International distance" value={`${originKm.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} km`} />
                <Row label="UK hub distance" value={`${ukKm.toFixed(0)} km`} />
              </div>

              {/* Materials */}
              <div className="glass-card rounded-xl p-4">
                <h4 className="text-slate-300 font-semibold text-sm mb-3">🧱 Materials</h4>

                {/* Primary material */}
                <Row
                  label="Primary material"
                  value={
                    attr.materials?.primary_percentage && !isNaN(parseFloat(attr.materials.primary_percentage))
                      ? `${primaryMaterial} · ${attr.materials.primary_percentage}%`
                      : primaryMaterial
                  }
                  badge
                  badgeVariant="info"
                />

                {/* Secondary material — first secondary only */}
                {attr.materials?.secondary_materials?.length > 0 && (
                  <Row
                    label="Secondary material"
                    value={
                      attr.materials.secondary_materials[0].percentage &&
                      !isNaN(parseFloat(attr.materials.secondary_materials[0].percentage))
                        ? `${attr.materials.secondary_materials[0].name} · ${attr.materials.secondary_materials[0].percentage}%`
                        : attr.materials.secondary_materials[0].name
                    }
                    badge
                    badgeVariant="default"
                  />
                )}

                {/* Tertiary materials — remaining secondaries, if any */}
                {attr.materials?.secondary_materials?.length > 1 && (
                  <div className="pt-2 pb-1">
                    <p className="text-slate-500 text-xs mb-1.5">Tertiary materials</p>
                    <div className="flex flex-wrap gap-1.5">
                      {attr.materials.secondary_materials.slice(1).map((m, i) => (
                        <span key={i} className="px-2 py-1 text-xs bg-slate-800 text-slate-300 rounded-md border border-slate-600">
                          {m.name}{m.percentage && !isNaN(parseFloat(m.percentage)) ? ` · ${m.percentage}%` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* All detected materials */}
                {attr.materials?.all_materials?.length > 0 && (
                  <div className="pt-3 mt-1 border-t border-slate-700/40">
                    <p className="text-slate-400 text-xs font-medium mb-2">All detected materials</p>
                    <div className="space-y-1.5">
                      {attr.materials.all_materials.map((m, i) => {
                        const pct = m.weight ? (m.weight * 100).toFixed(0) : m.percentage || null;
                        return (
                          <div key={i} className="flex items-center justify-between">
                            <span className="text-slate-300 text-xs">{m.name}</span>
                            {pct && (
                              <div className="flex items-center gap-2">
                                <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-cyan-500/60 rounded-full"
                                    style={{ width: `${Math.min(parseFloat(pct), 100)}%` }}
                                  />
                                </div>
                                <span className="text-slate-500 text-xs w-8 text-right">{pct}%</span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Detection metadata — moved to bottom */}
                <div className="pt-3 mt-1 border-t border-slate-700/40 space-y-0">
                  {materialTier && (
                    <Row label="Detection tier" value={`Tier ${materialTier}: ${attr.materials?.tier_name || ""}`} />
                  )}
                  {materialConf && (
                    <Row label="Detection confidence" value={`${((materialConf || 0) * 100).toFixed(0)}%`} />
                  )}
                  {attr.materials?.environmental_impact_score && (
                    <Row label="Material impact score" value={`${attr.materials.environmental_impact_score} kg CO₂/kg`} />
                  )}
                  {dataQuality && (
                    <div className="flex justify-between items-center py-2.5 border-b border-slate-700/40 last:border-0">
                      <span className="text-slate-400 text-sm">Overall data quality</span>
                      <ModernBadge
                        variant={dataQuality === "high" ? "success" : dataQuality === "medium" ? "warning" : "error"}
                        size="sm"
                      >
                        {dataQuality.charAt(0).toUpperCase() + dataQuality.slice(1)}
                      </ModernBadge>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Image Material Analysis */}
              {attr.image_url && attr.image_url !== "Not found" && (
                <ImageMaterialAnalysis
                  imageUrl={attr.image_url}
                  title={result.title}
                  galleryImages={attr.gallery_images}
                  specMaterials={attr.materials}
                />
              )}

              {/* Recyclability */}
              <div className="glass-card rounded-xl p-4">
                <h4 className="text-slate-300 font-semibold text-sm mb-3">♻️ End-of-Life</h4>
                <Row
                  label="Recyclability"
                  value={attr.recyclability || "Unknown"}
                  badge
                  badgeVariant={attr.recyclability === "High" ? "success" : attr.recyclability === "Medium" ? "warning" : "error"}
                />
                {attr.recyclability_percentage && (
                  <Row label="Recyclable content" value={`${attr.recyclability_percentage}%`} />
                )}
                {attr.recyclability_description && (
                  <p className="text-slate-500 text-xs mt-2 leading-relaxed">{attr.recyclability_description}</p>
                )}
              </div>

              {/* Eco Certifications */}
              {attr.certifications?.length > 0 && (
                <div className="glass-card rounded-xl p-4">
                  <h4 className="text-slate-300 font-semibold text-sm mb-3">🏅 Certifications</h4>
                  <div className="flex flex-wrap gap-2">
                    {attr.certifications.map((cert) => {
                      const style =
                        cert === "FSC Certified" || cert === "Organic" || cert === "Rainforest Alliance"
                          ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                          : cert === "Fair Trade" || cert === "B Corp" || cert === "GOTS"
                          ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300"
                          : cert === "ENERGY STAR"
                          ? "bg-blue-500/15 border-blue-500/40 text-blue-300"
                          : cert === "Carbon Neutral"
                          ? "bg-violet-500/15 border-violet-500/40 text-violet-300"
                          : "bg-slate-700/50 border-slate-600/60 text-slate-300";
                      return (
                        <span
                          key={cert}
                          className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${style}`}
                        >
                          {cert}
                        </span>
                      );
                    })}
                  </div>
                  <p className="text-slate-600 text-xs mt-2 leading-relaxed">
                    Detected from Amazon product listing — verify on product page.
                  </p>
                </div>
              )}

              {/* Seller info */}
              {(attr.sold_by || attr.dispatched_from || price) && (
                <div className="glass-card rounded-xl p-4">
                  <h4 className="text-slate-300 font-semibold text-sm mb-3">🛒 Listing Details</h4>
                  {price && <Row label="Price" value={`£${price.toFixed(2)}`} />}
                  {co2PerPound && <Row label="CO₂ per £ spent" value={`${co2PerPound} kg/£`} />}
                  {attr.sold_by && attr.sold_by !== "Not found" && <Row label="Sold by" value={attr.sold_by} />}
                  {attr.dispatched_from && attr.dispatched_from !== "Not found" && <Row label="Dispatched from" value={attr.dispatched_from} />}
                </div>
              )}
            </div>
          )}

          {/* ════ OVERVIEW ════ */}
          {activeTab === 1 && (
            <div className="space-y-5">

              {/* Carbon metrics circle */}
              <CarbonMetricsCircle
                carbonKg={attr.carbon_kg}
                ecoScore={attr.eco_score_ml}
                recyclability={attr.recyclability}
                recyclabilityPercentage={attr.recyclability_percentage}
                treesToOffset={treesCount}
              />

              {/* Equivalents */}
              {equivalents.length > 0 && (
                <div className="glass-card p-5 rounded-xl">
                  <h4 className="text-slate-200 font-semibold text-sm mb-4 flex items-center gap-2">
                    <span>🌍</span> That's equivalent to…
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                    {equivalents.map(eq => (
                      <div key={eq.label} className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-3 text-center">
                        <div className="text-2xl mb-1">{eq.icon}</div>
                        <div className="text-slate-100 font-bold text-base font-mono">{eq.value}</div>
                        <div className="text-slate-500 text-xs mt-0.5 leading-tight">{eq.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Material Swap Suggestion */}
              {(() => {
                const materialCF = (attr.counterfactuals || [])
                  .filter(cf => cf.changed_feature === "material" && cf.co2_reduction_kg > 0)
                  .sort((a, b) => b.co2_reduction_kg - a.co2_reduction_kg)[0];
                if (!materialCF) return null;
                return (
                  <div className="p-4 rounded-xl bg-emerald-500/8 border border-emerald-500/30">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center flex-shrink-0">
                        <span className="text-lg">♻️</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-slate-200 font-semibold text-sm">Material Swap Opportunity</p>
                        <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">
                          Switching to <span className="text-emerald-400 font-medium">{materialCF.changed_value}</span> could save{" "}
                          <span className="text-emerald-400 font-bold">−{materialCF.co2_reduction_kg} kg CO₂</span>
                          {materialCF.co2_reduction_pct > 0 && (
                            <span className="text-emerald-500/80"> ({materialCF.co2_reduction_pct}% less)</span>
                          )}
                          {" "}and improve the grade from{" "}
                          <span className="text-amber-400 font-bold">{materialCF.current_grade}</span> to{" "}
                          <span className="text-emerald-400 font-bold">{materialCF.new_grade}</span>.
                        </p>
                        <p className="text-slate-600 text-xs mt-1">See Deep Analysis tab for full counterfactual breakdown</p>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Lifecycle Assessment */}
              <LifecycleAssessment attr={attr} />

              {/* Climate Pledge */}
              {attr.climate_pledge_friendly !== undefined && (
                <div className={`p-4 rounded-xl border ${attr.climate_pledge_friendly ? "bg-emerald-500/8 border-emerald-500/30" : "bg-slate-800/40 border-slate-700/40"}`}>
                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${attr.climate_pledge_friendly ? "bg-emerald-500/20" : "bg-slate-700/60"}`}>
                      <span className="text-lg">{attr.climate_pledge_friendly ? "🌿" : "🔍"}</span>
                    </div>
                    <div>
                      <p className="text-slate-200 font-medium text-sm">Amazon Climate Pledge Friendly</p>
                      {attr.climate_pledge_friendly ? (
                        <>
                          <p className="text-emerald-400 text-xs mt-0.5">✅ Badge detected on this listing</p>
                          <p className="text-slate-500 text-xs mt-1">
                            Our ML grade is <span className="text-slate-300 font-medium">{mlScore}</span>
                            {mlScore > "C" ? " — our model flags higher environmental cost despite the badge." : " — consistent with the badge."}
                          </p>
                        </>
                      ) : (
                        <>
                          <p className="text-slate-400 text-xs mt-0.5">No badge found on this listing</p>
                          <p className="text-slate-500 text-xs mt-1">Our ML grade: <span className="text-slate-300 font-medium">{mlScore}</span></p>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Material average comparison */}
              {materialAvg && carbonKg > 0 && (() => {
                const diff = ((carbonKg - materialAvg.avg_co2_kg) / materialAvg.avg_co2_kg * 100).toFixed(0);
                const better = carbonKg < materialAvg.avg_co2_kg;
                return (
                  <div className="glass-card p-5 rounded-xl">
                    <h4 className="text-slate-200 font-semibold text-sm mb-3 flex items-center gap-2">
                      <span>📊</span> vs. Similar Products
                    </h4>
                    <p className="text-slate-500 text-xs mb-3">
                      Average CO₂ across {materialAvg.sample_size} {attr.material_type} products in our database
                    </p>
                    <div className="space-y-1.5">
                      <Row label="This product" value={`${carbonKg.toFixed(2)} kg CO₂`} />
                      <Row label={`${attr.material_type} average`} value={`${materialAvg.avg_co2_kg.toFixed(2)} kg CO₂`} />
                    </div>
                    <div className={`flex items-center gap-2 mt-3 px-3 py-2 rounded-lg text-sm font-medium ${better ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                      <span>{better ? "✅" : "⚠️"}</span>
                      <span>{better ? `${Math.abs(diff)}% below` : `${Math.abs(diff)}% above`} average for {attr.material_type} products</span>
                    </div>
                  </div>
                );
              })()}

              {/* Add to basket */}
              <div className="flex justify-center pt-1">
                <button
                  onClick={() => window.dispatchEvent(new CustomEvent("basket:add", {
                    detail: { title: result.title, grade: mlScore, co2: attr.carbon_kg }
                  }))}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600/20 border border-emerald-500/40 hover:bg-emerald-600/30 hover:border-emerald-500/70 text-emerald-400 text-sm font-medium transition-colors"
                >
                  <span>🧺</span> Add to Carbon Basket
                </button>
              </div>

              {/* Alternatives */}
              <AlternativeRecommendations
                grade={mlScore}
                category={attr.category}
                currentCo2={attr.carbon_kg}
                productTitle={result.title}
              />
            </div>
          )}

          {/* ════ DEEP ANALYSIS ════ */}
          {activeTab === 2 && (
            <div className="space-y-6">

              {/* ML vs DEFRA */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <h4 className="text-slate-200 font-semibold text-sm">📊 Methodology Comparison</h4>
                  <ModernButton variant={showML ? "default" : "accent"} size="sm" onClick={toggleShowML} className="flex items-center gap-2">
                    <span>💡</span>
                    <span>{showML ? "Show Comparison" : "AI Only"}</span>
                  </ModernButton>
                </div>
                <div className="text-center mb-3">
                  <ModernBadge variant={showML ? "warning" : "success"} size="sm">
                    {showML ? "🧠 AI Prediction Only" : "⚡ AI vs Standard Method"}
                  </ModernBadge>
                </div>
                <MLvsDEFRAChart showML={showML} result={result} />
              </div>

              {attr.shap_explanation && <ShapExplanation data={attr.shap_explanation} />}

              {attr.proba_distribution?.length > 0 && (
                <ConfidenceDistributionChart data={attr.proba_distribution} predictedGrade={mlScore} />
              )}

              {attr.conformal_sets && (
                <ConformalPredictionBadge conformalSets={attr.conformal_sets} predictedGrade={mlScore} />
              )}

              {attr.counterfactuals?.length > 0 && (
                <CounterfactualExplanation data={attr.counterfactuals} />
              )}
            </div>
          )}

        </motion.div>
      </AnimatePresence>
    </ModernCard>
  );
}
