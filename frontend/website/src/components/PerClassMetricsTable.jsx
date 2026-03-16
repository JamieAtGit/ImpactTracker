import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const GRADE_COLORS = {
  "A+": { bg: "bg-teal-500/20", text: "text-teal-300", border: "border-teal-500/30" },
  "A":  { bg: "bg-green-500/20", text: "text-green-300", border: "border-green-500/30" },
  "B":  { bg: "bg-lime-500/20",  text: "text-lime-300",  border: "border-lime-500/30"  },
  "C":  { bg: "bg-yellow-500/20",text: "text-yellow-300",border: "border-yellow-500/30"},
  "D":  { bg: "bg-orange-500/20",text: "text-orange-300",border: "border-orange-500/30"},
  "E":  { bg: "bg-red-400/20",   text: "text-red-300",   border: "border-red-400/30"   },
  "F":  { bg: "bg-red-700/20",   text: "text-red-400",   border: "border-red-700/30"   },
};

function PercentBar({ value, color = "bg-cyan-500" }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-slate-300 w-12 text-right">{(value * 100).toFixed(1)}%</span>
    </div>
  );
}

function ConfusionMatrix({ matrix, labels, title, highlight }) {
  if (!matrix || !labels) return null;

  const maxVal = Math.max(...matrix.flat());

  const cellOpacity = (val, i, j) => {
    if (i === j) return Math.min(0.8, 0.2 + (val / maxVal) * 0.6);
    return Math.min(0.6, (val / maxVal) * 0.6);
  };

  return (
    <div>
      <h5 className="text-base font-medium text-slate-200 mb-3">{title}</h5>
      <div className="overflow-x-auto">
        <table className="text-xs border border-slate-700 rounded-lg overflow-hidden">
          <thead>
            <tr>
              <th className="p-2 bg-slate-800 text-slate-400 border-r border-b border-slate-700 text-left">
                True↓ Pred→
              </th>
              {labels.map((l) => (
                <th key={l} className="p-2 bg-slate-800 border-r border-b border-slate-700 text-center">
                  <span className={`font-bold ${GRADE_COLORS[l]?.text || "text-slate-300"}`}>{l}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                <td className="p-2 bg-slate-800 border-r border-b border-slate-700 font-bold text-center">
                  <span className={GRADE_COLORS[labels[i]]?.text || "text-slate-300"}>{labels[i]}</span>
                </td>
                {row.map((val, j) => (
                  <td
                    key={j}
                    className="p-2 border-r border-b border-slate-700 text-center font-medium transition-all"
                    style={{
                      backgroundColor: i === j
                        ? `rgba(6, 182, 212, ${cellOpacity(val, i, j)})`
                        : val > 0
                        ? `rgba(239, 68, 68, ${cellOpacity(val, i, j)})`
                        : "transparent",
                      color: val > 0 ? "#e2e8f0" : "#475569",
                    }}
                  >
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500 mt-2">
        Diagonal = correct predictions (cyan). Off-diagonal = misclassifications (red intensity ∝ count).
      </p>
    </div>
  );
}

export default function PerClassMetricsTable() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/all-model-metrics`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error || !d.xgboost) { setError(true); }
        else { setMetrics(d); }
        setLoading(false);
      })
      .catch(() => { setError(true); setLoading(false); });
  }, []);

  if (loading) return <p className="text-slate-400 text-sm text-center py-8">Loading metrics...</p>;
  if (error)   return <p className="text-red-400 text-sm text-center py-8">Failed to load metrics.</p>;

  const xgb = metrics.xgboost;
  const rf  = metrics.random_forest;

  const classEntries = Object.entries(xgb.report).filter(
    ([k]) => !["accuracy", "macro avg", "weighted avg"].includes(k)
  );

  // Sort grades in logical order
  const gradeOrder = ["A+", "A", "B", "C", "D", "E", "F"];
  classEntries.sort(([a], [b]) => gradeOrder.indexOf(a) - gradeOrder.indexOf(b));

  // Backend filters out 'macro avg' from the report — compute it from class entries
  const macroAvg = xgb.report["macro avg"] ?? (() => {
    const vals = classEntries.map(([, m]) => m);
    const avg = (key) => vals.reduce((s, m) => s + (m[key] || 0), 0) / (vals.length || 1);
    return { precision: avg("precision"), recall: avg("recall"), "f1-score": avg("f1-score"), support: vals.reduce((s, m) => s + (m.support || 0), 0) };
  })();

  return (
    <div className="space-y-10">

      {/* Per-Class Breakdown Table */}
      <div>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-2 h-8 bg-gradient-to-b from-purple-400 to-cyan-400 rounded-full" />
          <h4 className="text-lg font-display text-slate-200">XGBoost Per-Class Performance</h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-300 font-medium">Grade</th>
                <th className="text-left py-3 px-4 text-slate-300 font-medium">Precision</th>
                <th className="text-left py-3 px-4 text-slate-300 font-medium">Recall</th>
                <th className="text-left py-3 px-4 text-slate-300 font-medium">F1-Score</th>
                <th className="text-right py-3 px-4 text-slate-300 font-medium">Test Samples</th>
              </tr>
            </thead>
            <tbody>
              {classEntries.map(([grade, m], i) => {
                const colors = GRADE_COLORS[grade] || {};
                return (
                  <motion.tr
                    key={grade}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center justify-center w-10 h-7 rounded-md text-sm font-bold border ${colors.bg} ${colors.text} ${colors.border}`}>
                        {grade}
                      </span>
                    </td>
                    <td className="py-4 px-4 w-36">
                      <PercentBar value={m.precision} color="bg-blue-500" />
                    </td>
                    <td className="py-4 px-4 w-36">
                      <PercentBar value={m.recall} color="bg-purple-500" />
                    </td>
                    <td className="py-4 px-4 w-36">
                      <PercentBar
                        value={m["f1-score"]}
                        color={m["f1-score"] >= 0.9 ? "bg-green-500" : m["f1-score"] >= 0.8 ? "bg-cyan-500" : "bg-yellow-500"}
                      />
                    </td>
                    <td className="py-4 px-4 text-right text-slate-400">{m.support}</td>
                  </motion.tr>
                );
              })}
              {/* Macro averages row */}
              <tr className="border-t-2 border-slate-600 bg-slate-800/20">
                <td className="py-3 px-4 text-slate-300 font-medium text-xs uppercase tracking-wide">Macro Avg</td>
                <td className="py-3 px-4 w-36">
                  <PercentBar value={macroAvg.precision} color="bg-slate-400" />
                </td>
                <td className="py-3 px-4 w-36">
                  <PercentBar value={macroAvg.recall} color="bg-slate-400" />
                </td>
                <td className="py-3 px-4 w-36">
                  <PercentBar value={macroAvg["f1-score"]} color="bg-slate-400" />
                </td>
                <td className="py-3 px-4 text-right text-slate-400">{macroAvg.support}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Key Insight Callout */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-teal-500/10 border border-teal-500/30 rounded-lg p-3">
            <p className="text-teal-300 text-xs font-medium mb-1">Best Predicted Class</p>
            <p className="text-slate-300 text-xs">
              <strong>A+</strong> achieves 99.9% F1 — the model reliably identifies the most eco-friendly products from weight and origin features alone.
            </p>
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <p className="text-yellow-300 text-xs font-medium mb-1">Hardest to Distinguish</p>
            <p className="text-slate-300 text-xs">
              <strong>A</strong> and <strong>B</strong> grade products share similar feature profiles — both are lightweight, low-distance items with overlapping material types.
            </p>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
            <p className="text-blue-300 text-xs font-medium mb-1">Class Balance</p>
            <p className="text-slate-300 text-xs">
              SMOTE synthetic oversampling balanced ~339 samples per class in the test set, preventing the model from biasing towards majority grades.
            </p>
          </div>
        </div>
      </div>

      {/* Side-by-Side Confusion Matrices */}
      <div>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded-full" />
          <h4 className="text-lg font-display text-slate-200">Confusion Matrix Comparison</h4>
        </div>
        <p className="text-sm text-slate-400 mb-5">
          Each cell shows how many test samples with a given true grade were predicted as each grade.
          Darker diagonal = better performance.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ConfusionMatrix
            matrix={rf?.confusion_matrix}
            labels={rf?.labels}
            title="Random Forest (84.9% accuracy)"
          />
          <ConfusionMatrix
            matrix={xgb?.confusion_matrix}
            labels={xgb?.labels}
            title="XGBoost (86.6% accuracy)"
          />
        </div>
      </div>

    </div>
  );
}
