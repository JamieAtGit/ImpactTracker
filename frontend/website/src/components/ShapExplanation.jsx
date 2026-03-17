import React from "react";
import { motion } from "framer-motion";

function ShapBar({ name, shapValue, rawValue, maxAbs, index }) {
  const pct = maxAbs > 0 ? Math.abs(shapValue) / maxAbs : 0;
  const isPositive = shapValue >= 0;
  const barPct = `${Math.round(pct * 100)}%`;

  return (
    <motion.div
      className="flex items-center gap-3 py-1.5"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4 }}
    >
      {/* Feature label */}
      <div className="w-36 shrink-0 text-right">
        <span className="text-xs text-slate-300">{name}</span>
        {rawValue && (
          <span className="block text-xs text-slate-500 truncate">{rawValue}</span>
        )}
      </div>

      {/* Diverging bar */}
      <div className="flex-1 flex items-center gap-0.5 min-w-0">
        {/* Left (negative) side */}
        <div className="flex-1 flex justify-end h-5">
          {!isPositive && (
            <motion.div
              className="h-full bg-red-500/60 rounded-l-sm"
              initial={{ width: 0 }}
              animate={{ width: barPct }}
              transition={{ delay: index * 0.05 + 0.1, duration: 0.5, ease: "easeOut" }}
            />
          )}
        </div>
        {/* Centre axis */}
        <div className="w-px h-6 bg-slate-600 shrink-0" />
        {/* Right (positive) side */}
        <div className="flex-1 h-5">
          {isPositive && (
            <motion.div
              className="h-full bg-emerald-500/60 rounded-r-sm"
              initial={{ width: 0 }}
              animate={{ width: barPct }}
              transition={{ delay: index * 0.05 + 0.1, duration: 0.5, ease: "easeOut" }}
            />
          )}
        </div>
      </div>

      {/* Numeric value */}
      <div
        className={`w-16 shrink-0 text-right font-mono text-xs ${
          isPositive ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {isPositive ? "+" : ""}
        {shapValue.toFixed(3)}
      </div>
    </motion.div>
  );
}

export default function ShapExplanation({ data }) {
  if (!data || !data.features || data.features.length === 0) return null;

  const maxAbs = Math.max(...data.features.map((f) => Math.abs(f.shap_value)));
  const topFeatures = data.features.slice(0, 8); // show top 8

  return (
    <div className="mt-6 p-5 bg-slate-800/40 rounded-xl border border-slate-700/50">
      {/* Header */}
      <div className="flex items-start gap-2 mb-1">
        <span className="text-base mt-0.5">🔬</span>
        <div>
          <h4 className="text-sm font-semibold text-slate-200">
            Why grade{" "}
            <span className="text-cyan-400 font-bold">{data.predicted_class}</span>?
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            SHAP values — each feature's contribution to this specific prediction.{" "}
            <span className="text-emerald-400">Green pushes the grade up</span>,{" "}
            <span className="text-red-400">red pushes it down</span>.
          </p>
        </div>
      </div>

      {/* Column headers */}
      <div className="flex items-center gap-3 mt-4 pb-2 border-b border-slate-700/50">
        <div className="w-36 shrink-0 text-right text-xs text-slate-600">Feature</div>
        <div className="flex-1 flex items-center gap-0.5">
          <div className="flex-1 text-right text-xs text-slate-600 pr-2">← Lower grade</div>
          <div className="w-px h-4 bg-slate-600 shrink-0" />
          <div className="flex-1 text-xs text-slate-600 pl-2">Higher grade →</div>
        </div>
        <div className="w-16 shrink-0 text-right text-xs text-slate-600">SHAP</div>
      </div>

      {/* Bars */}
      <div className="mt-1 space-y-0.5">
        {topFeatures.map((f, i) => (
          <ShapBar
            key={f.name}
            name={f.name}
            shapValue={f.shap_value}
            rawValue={f.raw_value}
            maxAbs={maxAbs}
            index={i}
          />
        ))}
      </div>

      {/* Citation footer */}
      <p className="text-xs text-slate-600 mt-4 pt-3 border-t border-slate-700/40">
        Computed using SHapley Additive exPlanations (Lundberg &amp; Lee, NeurIPS 2017) with
        TreeExplainer for XGBoost. Base expected value:{" "}
        <span className="font-mono">{data.base_value?.toFixed(3)}</span>. Sorted by absolute
        contribution magnitude.
      </p>
    </div>
  );
}
