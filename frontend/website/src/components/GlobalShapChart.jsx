import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const FEATURE_LABELS = {
  transport_mode:            "Transport Mode",
  material:                  "Material",
  origin:                    "Country of Origin",
  weight_kg:                 "Weight (kg)",
  recyclability:             "Recyclability",
  distance_from_origin_km:   "Origin Distance (km)",
  distance_from_uk_hub_km:   "UK Hub Distance (km)",
  raw_product_weight_kg:     "Raw Weight (kg)",
  packaging_weight_kg:       "Packaging Weight",
  material_impact_score:     "Material Impact Score",
  co2_emissions:             "CO₂ Emissions",
};

// Cyan-to-teal gradient colours, most-important = most vivid
const BAR_COLOURS = [
  "#06b6d4", "#22d3ee", "#34d399", "#6ee7b7",
  "#67e8f9", "#a5f3fc", "#cffafe", "#e0f2fe",
];

export default function GlobalShapChart() {
  const [data,    setData]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [meta,    setMeta]    = useState(null);

  useEffect(() => {
    fetch(`${BASE_URL}/api/global-shap`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(json => {
        setData(json.features || json.feature_importances || []);
        setMeta({ sample_size: json.sample_size, citation: json.citation });
      })
      .catch(err => {
        console.error("Global SHAP fetch error:", err);
        setError("Could not load global SHAP data.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center gap-3 py-12 text-slate-500">
      <div className="w-5 h-5 border-2 border-slate-600 border-t-cyan-500 rounded-full animate-spin" />
      <span className="text-sm">Computing global SHAP values…</span>
    </div>
  );

  if (error) return <p className="text-red-400 text-sm py-4 text-center">{error}</p>;
  if (!data.length) return null;

  const max = data[0]?.importance || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <p className="text-slate-400 text-sm text-center mb-6">
        Mean |SHAP| values across {meta?.sample_size ?? "N"} sampled products — higher = stronger influence on eco grade
      </p>

      <div className="space-y-3">
        {data.map((d, i) => {
          const pct = (d.importance / max) * 100;
          const label = FEATURE_LABELS[d.feature] || d.feature;
          return (
            <motion.div
              key={d.feature}
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.45, delay: i * 0.06 }}
            >
              {/* Feature name */}
              <span className="w-40 text-right text-xs text-slate-400 flex-shrink-0 truncate" title={label}>
                {label}
              </span>

              {/* Animated bar */}
              <div className="flex-1 h-6 bg-slate-800 rounded-md overflow-hidden">
                <motion.div
                  className="h-full rounded-md"
                  style={{ backgroundColor: BAR_COLOURS[i % BAR_COLOURS.length] }}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6, delay: i * 0.06, ease: "easeOut" }}
                />
              </div>

              {/* Value */}
              <span className="w-16 text-xs text-slate-400 flex-shrink-0 font-mono">
                {d.importance.toFixed(4)}
              </span>
            </motion.div>
          );
        })}
      </div>

      {/* Academic footer */}
      <p className="mt-6 text-xs text-slate-600 leading-relaxed border-t border-slate-700/50 pt-4">
        Global feature importance computed via{" "}
        <code className="text-slate-500">shap.TreeExplainer</code> applied to the trained XGBoost classifier.
        Each bar shows the mean absolute SHAP value across all grades, averaged over the sample.{" "}
        {meta?.citation && <span className="text-slate-500">{meta.citation}</span>}
      </p>
    </motion.div>
  );
}
