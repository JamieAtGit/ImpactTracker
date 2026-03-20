import React, { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from "recharts";

const GRADE_COLORS = {
  "A+": "#06d6a0",
  "A":  "#10b981",
  "B":  "#22c55e",
  "C":  "#eab308",
  "D":  "#f59e0b",
  "E":  "#ef4444",
  "F":  "#dc2626",
  "macro": "#a78bfa",
};

const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F", "macro"];

function buildCurvePoints(fpr, tpr) {
  return fpr.map((x, i) => ({ fpr: x, tpr: tpr[i] }));
}

export default function ROCCurveChart({ rocData, classes }) {
  const [visibleClasses, setVisibleClasses] = useState(
    new Set(["macro", ...(classes || [])])
  );

  if (!rocData) return (
    <div className="flex items-center justify-center h-64 text-slate-500">
      No ROC data available
    </div>
  );

  const allKeys = GRADE_ORDER.filter(k => rocData[k]);

  const toggleClass = (cls) => {
    setVisibleClasses(prev => {
      const next = new Set(prev);
      if (next.has(cls)) { next.delete(cls); } else { next.add(cls); }
      return next;
    });
  };

  // Build merged dataset: index by fpr of macro curve
  const macroPoints = buildCurvePoints(rocData.macro.fpr, rocData.macro.tpr);

  return (
    <div className="space-y-4">
      <p className="text-slate-400 text-sm">
        One-vs-rest ROC curves computed using out-of-fold (OOF) probabilities from 5-fold cross-validation,
        eliminating train-set overfitting. Each curve shows the true positive rate vs false positive rate
        trade-off for classifying one eco grade against all others.
      </p>

      {/* Class toggle buttons */}
      <div className="flex flex-wrap gap-2">
        {allKeys.map(cls => (
          <button
            key={cls}
            onClick={() => toggleClass(cls)}
            className={`px-3 py-1 rounded-full text-xs font-bold border transition-all duration-150 ${
              visibleClasses.has(cls)
                ? "border-transparent opacity-100"
                : "opacity-30"
            }`}
            style={{
              backgroundColor: visibleClasses.has(cls)
                ? GRADE_COLORS[cls] + "33"
                : "transparent",
              borderColor: GRADE_COLORS[cls],
              color: GRADE_COLORS[cls],
            }}
          >
            {cls === "macro" ? "Macro Avg" : `Grade ${cls}`}
            {rocData[cls] && ` (${rocData[cls].auc.toFixed(3)})`}
          </button>
        ))}
      </div>

      {/* Chart — one per visible class, overlaid */}
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="fpr"
              type="number"
              domain={[0, 1]}
              tickFormatter={v => v.toFixed(1)}
              label={{ value: "False Positive Rate", position: "insideBottom", offset: -10, fill: "#94a3b8", fontSize: 12 }}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <YAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={v => v.toFixed(1)}
              label={{ value: "True Positive Rate", angle: -90, position: "insideLeft", offset: 10, fill: "#94a3b8", fontSize: 12 }}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <Tooltip
              formatter={(val, name) => [val.toFixed(4), name]}
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            {/* Diagonal chance line */}
            <ReferenceLine
              segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
              stroke="#475569"
              strokeDasharray="6 4"
              label={{ value: "Chance", fill: "#475569", fontSize: 11, position: "insideTopRight" }}
            />
            {allKeys.filter(cls => visibleClasses.has(cls) && rocData[cls]).map(cls => {
              const pts = buildCurvePoints(rocData[cls].fpr, rocData[cls].tpr);
              return (
                <Line
                  key={cls}
                  data={pts}
                  dataKey="tpr"
                  name={cls === "macro" ? `Macro Avg (AUC=${rocData[cls].auc.toFixed(3)})` : `${cls} (AUC=${rocData[cls].auc.toFixed(3)})`}
                  stroke={GRADE_COLORS[cls]}
                  strokeWidth={cls === "macro" ? 2.5 : 1.5}
                  dot={false}
                  strokeDasharray={cls === "macro" ? "none" : "none"}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* AUC table */}
      <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
        {allKeys.map(cls => (
          <div key={cls} className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-2 text-center">
            <div className="text-xs font-bold" style={{ color: GRADE_COLORS[cls] }}>
              {cls === "macro" ? "Macro" : cls}
            </div>
            <div className="text-sm font-mono text-slate-200 mt-0.5">
              {rocData[cls]?.auc.toFixed(3) ?? "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
