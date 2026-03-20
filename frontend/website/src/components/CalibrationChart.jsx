import React from "react";
import {
  ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";

export default function CalibrationChart({ calibrationData }) {
  if (!calibrationData) return (
    <div className="flex items-center justify-center h-48 text-slate-500">
      No calibration data available
    </div>
  );

  const { mean_predicted_prob, fraction_of_positives, brier_score } = calibrationData;

  const points = mean_predicted_prob.map((x, i) => ({
    predicted: x,
    actual: fraction_of_positives[i],
  }));

  // Perfect calibration reference points
  const perfectLine = [{ predicted: 0, actual: 0 }, { predicted: 1, actual: 1 }];

  return (
    <div className="space-y-4">
      <p className="text-slate-400 text-sm">
        A reliability (calibration) diagram compares the model's stated confidence against
        actual observed frequencies. Points on the diagonal indicate perfect calibration —
        when the model says "60% confidence", 60% of those predictions are correct.
        Computed over all 7 classes (one-vs-rest) using 5-fold OOF probabilities.
      </p>

      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-cyan-400"></div>
          <span className="text-slate-300">XGBoost calibration</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-slate-500" style={{ borderTop: "2px dashed" }}></div>
          <span className="text-slate-400">Perfect calibration</span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-1">
          <span className="text-slate-400 text-xs">Brier Score: </span>
          <span className="text-cyan-300 font-mono text-xs font-bold">{brier_score.toFixed(4)}</span>
          <span className="text-slate-500 text-xs ml-1">(lower = better, 0 = perfect)</span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 10, right: 20, bottom: 25, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="predicted"
              type="number"
              domain={[0, 1]}
              tickFormatter={v => `${(v * 100).toFixed(0)}%`}
              label={{ value: "Mean Predicted Probability", position: "insideBottom", offset: -12, fill: "#94a3b8", fontSize: 12 }}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <YAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={v => `${(v * 100).toFixed(0)}%`}
              label={{ value: "Fraction of Positives", angle: -90, position: "insideLeft", offset: 10, fill: "#94a3b8", fontSize: 12 }}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <Tooltip
              formatter={(val) => [`${(val * 100).toFixed(1)}%`]}
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            {/* Perfect diagonal */}
            <Line
              data={perfectLine}
              dataKey="actual"
              stroke="#475569"
              strokeDasharray="6 4"
              strokeWidth={1.5}
              dot={false}
              name="Perfect calibration"
            />
            {/* Actual calibration curve */}
            <Line
              data={points}
              dataKey="actual"
              stroke="#22d3ee"
              strokeWidth={2.5}
              dot={{ fill: "#22d3ee", r: 4, strokeWidth: 0 }}
              name="XGBoost"
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-300">Interpretation:</strong> The XGBoost model is well-calibrated
          at low predicted probabilities but slightly over-confident at mid-to-high probabilities
          (curve dips below the diagonal). This is typical of tree-based models and can be addressed
          with Platt scaling or isotonic regression post-processing. The low Brier score of{" "}
          <span className="text-cyan-300 font-mono">{brier_score.toFixed(4)}</span> indicates overall
          good probabilistic accuracy.
        </p>
      </div>
    </div>
  );
}
