import React from "react";
import { motion } from "framer-motion";
import { ModernBadge } from "./ModernLayout";

const GRADE_COLORS = {
  "A+": { bg: "bg-emerald-500/20", border: "border-emerald-500/50", text: "text-emerald-400" },
  "A":  { bg: "bg-green-500/20",   border: "border-green-500/50",   text: "text-green-400"   },
  "B":  { bg: "bg-cyan-500/20",    border: "border-cyan-500/50",    text: "text-cyan-400"    },
  "C":  { bg: "bg-yellow-500/20",  border: "border-yellow-500/50",  text: "text-yellow-400"  },
  "D":  { bg: "bg-amber-500/20",   border: "border-amber-500/50",   text: "text-amber-400"   },
  "E":  { bg: "bg-orange-500/20",  border: "border-orange-500/50",  text: "text-orange-400"  },
  "F":  { bg: "bg-red-500/20",     border: "border-red-500/50",     text: "text-red-400"     },
};

const FEATURE_ICONS = {
  origin:    "📍",
  material:  "🧱",
  transport: "🚚",
};

function GradePill({ grade }) {
  const colors = GRADE_COLORS[grade] || GRADE_COLORS["F"];
  return (
    <span
      className={`inline-flex items-center justify-center w-10 h-10 rounded-lg font-display font-bold text-lg border ${colors.bg} ${colors.border} ${colors.text}`}
    >
      {grade}
    </span>
  );
}

function ImprovementArrow({ grades }) {
  return (
    <div className="flex items-center gap-1 text-emerald-400">
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
      <span className="text-sm font-semibold">{grades} grade{grades > 1 ? "s" : ""}</span>
    </div>
  );
}

export default function CounterfactualExplanation({ data }) {
  if (!data || data.length === 0) return null;

  return (
    <motion.div
      className="mt-6 p-5 bg-slate-800/40 rounded-xl border border-slate-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-violet-500/20 border border-violet-500/40 flex items-center justify-center">
            <span className="text-lg">🔄</span>
          </div>
          <div>
            <h4 className="text-base font-display font-semibold text-slate-200">
              What Would Improve This?
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Counterfactual analysis — single-feature interventions
            </p>
          </div>
        </div>
        <ModernBadge variant="info" size="sm">
          {data.length} scenario{data.length > 1 ? "s" : ""}
        </ModernBadge>
      </div>

      {/* Scenario cards */}
      <div className="space-y-3">
        {data.map((cf, i) => (
          <motion.div
            key={i}
            className="p-4 rounded-lg bg-slate-900/50 border border-slate-700/60 hover:border-violet-500/40 transition-colors duration-200"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: i * 0.08 }}
          >
            <div className="flex items-start gap-4">
              {/* Feature icon */}
              <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-lg">
                {FEATURE_ICONS[cf.changed_feature] || "✏️"}
              </div>

              {/* Main content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200 mb-2">{cf.change}</p>

                {/* Grade transition */}
                <div className="flex items-center gap-3 mb-3">
                  <GradePill grade={cf.current_grade} />
                  <svg className="w-5 h-5 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                  <GradePill grade={cf.new_grade} />
                  <ImprovementArrow grades={cf.grades_improved} />
                </div>

                {/* Metrics row */}
                <div className="flex flex-wrap gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">New CO₂:</span>
                    <span className="font-medium text-slate-300">
                      {cf.estimated_co2} kg
                    </span>
                  </div>
                  {cf.co2_reduction_kg > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-500">Reduction:</span>
                      <span className="font-semibold text-emerald-400">
                        −{cf.co2_reduction_kg} kg
                        {cf.co2_reduction_pct > 0 && (
                          <span className="ml-1 text-emerald-500/80">({cf.co2_reduction_pct}%)</span>
                        )}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">Change:</span>
                    <span className="font-medium text-violet-300">{cf.changed_value}</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Academic footer */}
      <p className="mt-4 text-xs text-slate-600 leading-relaxed border-t border-slate-700/50 pt-3">
        Counterfactual explanations generated by independently varying each input feature and
        re-predicting with the trained XGBoost model.{" "}
        <span className="text-slate-500">
          Method: Wachter, Mittelstadt &amp; Russell (2017).{" "}
          <em>Counterfactual Explanations without Opening the Black Box.</em>{" "}
          Harvard Journal of Law &amp; Technology, 31(2).
        </span>
      </p>
    </motion.div>
  );
}
