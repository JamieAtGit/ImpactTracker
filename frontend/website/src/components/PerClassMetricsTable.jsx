import React from "react";
import { motion } from "framer-motion";

const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"];

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

function ConfusionMatrix({ matrix, labels, title }) {
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

function computeFromConfusionMatrix(matrix, labels) {
  const cm = matrix;
  const result = {};
  for (let i = 0; i < labels.length; i++) {
    const tp = cm[i][i];
    const fp = cm.reduce((s, row) => s + row[i], 0) - tp;
    const fn = cm[i].reduce((s, v) => s + v, 0) - tp;
    const support = cm[i].reduce((s, v) => s + v, 0);
    const precision = (tp + fp) > 0 ? tp / (tp + fp) : 0;
    const recall    = (tp + fn) > 0 ? tp / (tp + fn) : 0;
    const f1        = (precision + recall) > 0 ? 2 * precision * recall / (precision + recall) : 0;
    result[labels[i]] = { precision, recall, f1, support };
  }
  const keys = Object.keys(result);
  result["macro"] = {
    precision: keys.reduce((s, k) => s + result[k].precision, 0) / keys.length,
    recall:    keys.reduce((s, k) => s + result[k].recall,    0) / keys.length,
    f1:        keys.reduce((s, k) => s + result[k].f1,        0) / keys.length,
  };
  return result;
}

export default function PerClassMetricsTable({ evaluationData }) {
  if (!evaluationData) {
    return <p className="text-slate-400 text-sm text-center py-8">Loading metrics...</p>;
  }

  // Use pre-computed per_class_metrics if available, otherwise compute from confusion matrix
  const pcm = evaluationData.per_class_metrics
    ?? computeFromConfusionMatrix(
        evaluationData.confusion_matrix?.matrix,
        evaluationData.confusion_matrix?.labels
      );

  const cm    = evaluationData.confusion_matrix;
  const accPct = cm?.test_accuracy != null
    ? `${(cm.test_accuracy * 100).toFixed(1)}%`
    : "—";

  // Sort grades in logical order, excluding "macro"
  const classEntries = GRADE_ORDER
    .filter((g) => pcm[g] != null)
    .map((g) => [g, pcm[g]]);

  const macroAvg = pcm["macro"] ?? null;

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
                        value={m.f1}
                        color={m.f1 >= 0.9 ? "bg-green-500" : m.f1 >= 0.8 ? "bg-cyan-500" : "bg-yellow-500"}
                      />
                    </td>
                    <td className="py-4 px-4 text-right text-slate-400">{m.support ?? "—"}</td>
                  </motion.tr>
                );
              })}
              {/* Macro averages row */}
              {macroAvg && (
                <tr className="border-t-2 border-slate-600 bg-slate-800/20">
                  <td className="py-3 px-4 text-slate-300 font-medium text-xs uppercase tracking-wide">Macro Avg</td>
                  <td className="py-3 px-4 w-36">
                    <PercentBar value={macroAvg.precision} color="bg-slate-400" />
                  </td>
                  <td className="py-3 px-4 w-36">
                    <PercentBar value={macroAvg.recall} color="bg-slate-400" />
                  </td>
                  <td className="py-3 px-4 w-36">
                    <PercentBar value={macroAvg.f1} color="bg-slate-400" />
                  </td>
                  <td className="py-3 px-4 text-right text-slate-400">
                    {classEntries.reduce((s, [, m]) => s + (m.support ?? 0), 0)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Key Insight Callout */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-teal-500/10 border border-teal-500/30 rounded-lg p-3">
            <p className="text-teal-300 text-xs font-medium mb-1">Best Predicted Class</p>
            <p className="text-slate-300 text-xs">
              <strong>A+</strong> achieves 100% F1 — the model reliably identifies the most eco-friendly products from weight and origin features alone.
            </p>
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <p className="text-yellow-300 text-xs font-medium mb-1">Hardest to Distinguish</p>
            <p className="text-slate-300 text-xs">
              <strong>D</strong> and <strong>E</strong> grade products share similar feature profiles — both are mid-weight items with overlapping transport modes.
            </p>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
            <p className="text-blue-300 text-xs font-medium mb-1">Class Balance</p>
            <p className="text-slate-300 text-xs">
              SMOTE synthetic oversampling balanced classes during training, preventing the model from biasing towards majority grades.
            </p>
          </div>
        </div>
      </div>

      {/* Confusion Matrix */}
      <div>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-2 h-8 bg-gradient-to-b from-blue-400 to-purple-400 rounded-full" />
          <h4 className="text-lg font-display text-slate-200">Confusion Matrix</h4>
        </div>
        <p className="text-sm text-slate-400 mb-5">
          Each cell shows how many test samples with a given true grade were predicted as each grade.
          Darker diagonal = better performance.
        </p>
        <ConfusionMatrix
          matrix={cm?.matrix}
          labels={cm?.labels}
          title={`XGBoost (${accPct} accuracy)`}
        />
      </div>

    </div>
  );
}
