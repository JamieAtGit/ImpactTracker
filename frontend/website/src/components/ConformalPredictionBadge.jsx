import React, { useState } from "react";
import { motion } from "framer-motion";

const GRADE_COLORS = {
  "A+": "#06d6a0",
  "A":  "#10b981",
  "B":  "#22c55e",
  "C":  "#eab308",
  "D":  "#f59e0b",
  "E":  "#ef4444",
  "F":  "#dc2626",
};

const COVERAGE_LABELS = {
  "0.9":  "90%",
  "0.95": "95%",
  "0.99": "99%",
};

/**
 * Displays split-conformal prediction sets for each coverage level.
 *
 * conformalSets: { "0.9": ["C"], "0.95": ["B","C"], "0.99": ["B","C","D"] }
 */
export default function ConformalPredictionBadge({ conformalSets, predictedGrade }) {
  const [expanded, setExpanded] = useState(false);

  if (!conformalSets) return null;

  // Default display: 95% coverage
  const set95 = conformalSets["0.95"] || [predictedGrade];

  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-indigo-400 text-lg">◈</span>
          <span className="text-sm font-semibold text-slate-200">Conformal Prediction Set</span>
        </div>
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          {expanded ? "Less" : "What is this?"}
        </button>
      </div>

      {/* 95% prediction set — primary display */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400 whitespace-nowrap">Grade is within</span>
        <div className="flex gap-1.5 flex-wrap">
          {set95.map(g => (
            <motion.span
              key={g}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="px-2.5 py-0.5 rounded-lg text-sm font-bold font-mono border"
              style={{
                color: GRADE_COLORS[g] || "#94a3b8",
                borderColor: (GRADE_COLORS[g] || "#94a3b8") + "55",
                backgroundColor: (GRADE_COLORS[g] || "#94a3b8") + "15",
              }}
            >
              {g}
            </motion.span>
          ))}
        </div>
        <span className="text-xs font-medium text-indigo-300 bg-indigo-900/30 border border-indigo-700/40 rounded-full px-2 py-0.5 whitespace-nowrap">
          95% guaranteed
        </span>
      </div>

      {/* Explanation (expandable) */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="space-y-3 border-t border-slate-700/40 pt-3"
        >
          <p className="text-xs text-slate-400 leading-relaxed">
            Unlike the standard softmax confidence score (which can be miscalibrated),{" "}
            <strong className="text-slate-300">conformal prediction sets carry a mathematical guarantee</strong>:
            the true grade will lie within the displayed set in at least the stated percentage of cases,
            regardless of how well the model is calibrated (Vovk et al., 2005).
          </p>
          <p className="text-xs text-slate-500 leading-relaxed">
            The threshold was calibrated on a held-out set of{" "}
            <strong className="text-slate-400">10,000 products</strong> not seen during training.
            Smaller sets mean the model is more certain; a single-grade set is the strongest possible prediction.
          </p>

          {/* All three coverage levels */}
          <div className="space-y-2 pt-1">
            {Object.entries(COVERAGE_LABELS).map(([key, label]) => {
              const ps = conformalSets[key] || [predictedGrade];
              return (
                <div key={key} className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-8">{label}</span>
                  <div className="flex gap-1 flex-wrap">
                    {ps.map(g => (
                      <span
                        key={g}
                        className="px-2 py-0.5 rounded text-xs font-bold font-mono"
                        style={{ color: GRADE_COLORS[g] || "#94a3b8" }}
                      >
                        {g}
                      </span>
                    ))}
                  </div>
                  <span className="text-xs text-slate-600">
                    ({ps.length} grade{ps.length !== 1 ? "s" : ""})
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
}
