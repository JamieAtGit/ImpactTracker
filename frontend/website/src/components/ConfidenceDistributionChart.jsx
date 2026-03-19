import React from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
} from "recharts";

// Grade order and colours consistent with the rest of the app
const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"];

const GRADE_COLOURS = {
  "A+": "#10b981",
  "A":  "#06d6a0",
  "B":  "#06b6d4",
  "C":  "#f59e0b",
  "D":  "#f97316",
  "E":  "#ef4444",
  "F":  "#dc2626",
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { grade, probability } = payload[0].payload;
  return (
    <div className="glass-card-solid px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-slate-200 mb-0.5">Grade {grade}</p>
      <p className="text-slate-300">{probability.toFixed(1)}% probability</p>
    </div>
  );
}

export default function ConfidenceDistributionChart({ data, predictedGrade }) {
  if (!data || data.length === 0) return null;

  // Sort into canonical grade order
  const sorted = [...data].sort(
    (a, b) => GRADE_ORDER.indexOf(a.grade) - GRADE_ORDER.indexOf(b.grade)
  );

  // Entropy-based uncertainty indicator (higher = more uncertain)
  const entropy = sorted.reduce((acc, { probability: p }) => {
    const pFrac = p / 100;
    return acc - (pFrac > 0 ? pFrac * Math.log2(pFrac) : 0);
  }, 0);
  const maxEntropy = Math.log2(sorted.length);
  const certaintyPct = Math.round((1 - entropy / maxEntropy) * 100);

  return (
    <motion.div
      className="mt-6 p-5 bg-slate-800/40 rounded-xl border border-slate-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.05 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center flex-shrink-0">
            <span className="text-lg">📊</span>
          </div>
          <div>
            <h4 className="text-base font-display font-semibold text-slate-200">
              Grade Probability Distribution
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Model confidence across all 7 eco-grade classes
            </p>
          </div>
        </div>

        {/* Certainty pill */}
        <div className="flex-shrink-0 text-right">
          <div className={`text-sm font-bold ${certaintyPct >= 75 ? "text-emerald-400" : certaintyPct >= 50 ? "text-amber-400" : "text-red-400"}`}>
            {certaintyPct}%
          </div>
          <div className="text-xs text-slate-500">certainty</div>
        </div>
      </div>

      {/* Bar chart */}
      <ResponsiveContainer width="100%" height={130}>
        <BarChart data={sorted} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <XAxis
            dataKey="grade"
            tick={{ fill: "#94a3b8", fontSize: 12, fontFamily: "IBM Plex Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis domain={[0, 100]} hide />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="probability" radius={[4, 4, 0, 0]} maxBarSize={48}>
            {sorted.map((entry) => (
              <Cell
                key={entry.grade}
                fill={GRADE_COLOURS[entry.grade] || "#64748b"}
                opacity={entry.grade === predictedGrade ? 1 : 0.3}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Interpretation note */}
      <p className="text-xs text-slate-600 mt-3 leading-relaxed border-t border-slate-700/50 pt-3">
        The highlighted bar is the predicted grade. A peaked single bar indicates high model
        certainty; a flatter distribution across multiple grades indicates the product sits near
        a grade boundary and the prediction should be interpreted with more caution.
      </p>
    </motion.div>
  );
}
