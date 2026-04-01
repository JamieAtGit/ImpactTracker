import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

function dropColor(drop) {
  if (drop >= 0.5)  return "#ef4444"; // red-500 — very high impact
  if (drop >= 0.2)  return "#f97316"; // orange-500
  if (drop >= 0.08) return "#eab308"; // yellow-500
  if (drop >= 0.04) return "#84cc16"; // lime-500
  return "#22c55e";                   // green-500 — low impact
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-slate-200 font-semibold mb-1">{d.name}</p>
      <p className="text-slate-400">Ablated accuracy: <span className="text-slate-200">{(d.ablated_accuracy * 100).toFixed(1)}%</span></p>
      <p className="text-slate-400">Accuracy drop: <span style={{ color: dropColor(d.accuracy_drop) }}>{(d.accuracy_drop * 100).toFixed(2)}%</span></p>
      <p className="text-slate-400">Importance rank: <span className="text-slate-200">#{d.importance_rank}</span></p>
    </div>
  );
};

export default function AblationStudyChart() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(false);
  const [view, setView]     = useState("features"); // "features" | "groups"

  useEffect(() => {
    fetch(`${BASE_URL}/api/ablation`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) { setError(true); }
        else { setData(d); }
        setLoading(false);
      })
      .catch(() => { setError(true); setLoading(false); });
  }, []);

  if (loading) return <p className="text-slate-400 text-sm text-center py-8">Loading ablation study...</p>;
  if (error)   return <p className="text-red-400 text-sm text-center py-8">Failed to load ablation results.</p>;

  const features = [...data.features].sort((a, b) => b.accuracy_drop - a.accuracy_drop);
  const groups   = [...data.groups].sort((a, b) => b.accuracy_drop - a.accuracy_drop);
  const chartData = view === "features" ? features : groups;
  const topFeature = features[0];

  return (
    <div className="space-y-6">

      {/* Summary callout */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
        <p className="text-blue-300 text-xs font-semibold mb-1">Most Important Feature</p>
        <p className="text-slate-300 text-sm">
          <strong className="text-slate-100">{topFeature.name}</strong> is the most critical feature —
          removing it causes accuracy to drop from{" "}
          <span className="text-slate-100">{(data.baseline_accuracy * 100).toFixed(1)}%</span> to{" "}
          <span className="text-red-400">{(topFeature.ablated_accuracy * 100).toFixed(1)}%</span>{" "}
          (a <span className="text-red-400">{(topFeature.accuracy_drop * 100).toFixed(1)} percentage point</span> drop).
        </p>
      </div>

      {/* Dataset note */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-3">
        <p className="text-amber-300/80 text-xs leading-relaxed">
          <strong className="text-amber-300">Dataset note:</strong> The {(data.baseline_accuracy * 100).toFixed(1)}% baseline
          is measured on a held-out 20% split of the 50,000-row expanded training dataset (same synthetic
          distribution). The independently-evaluated held-out test accuracy is{" "}
          <strong className="text-amber-200">86.6%</strong> (see Per-Class Performance above). The ablation
          figures here are valid for <em>relative</em> feature importance — the drops show how much each
          feature contributes — not as an absolute accuracy claim.
        </p>
      </div>

      {/* Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setView("features")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            view === "features"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-slate-300"
          }`}
        >
          Individual Features
        </button>
        <button
          onClick={() => setView("groups")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            view === "groups"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
              : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-slate-300"
          }`}
        >
          Feature Groups
        </button>
      </div>

      {/* Horizontal bar chart */}
      <div>
        <p className="text-xs text-slate-500 mb-3">
          Baseline accuracy: <span className="text-slate-300">{(data.baseline_accuracy * 100).toFixed(1)}%</span>
          {" "}— bars show accuracy drop when that feature is zeroed out on the raw test set.
        </p>
        <ResponsiveContainer width="100%" height={view === "features" ? 320 : 200}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 60, left: 160, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#475569" }}
              tickLine={{ stroke: "#475569" }}
              domain={[0, "dataMax + 0.05"]}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "#cbd5e1", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={155}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148,163,184,0.05)" }} />
            <Bar dataKey="accuracy_drop" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={dropColor(entry.accuracy_drop)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detail table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-2 px-3 text-slate-400 font-medium">Rank</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">Feature</th>
              <th className="text-right py-2 px-3 text-slate-400 font-medium">Ablated Acc.</th>
              <th className="text-right py-2 px-3 text-slate-400 font-medium">Drop</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((row, i) => (
              <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                <td className="py-2 px-3 text-slate-500">
                  {view === "features" ? `#${row.importance_rank}` : `—`}
                </td>
                <td className="py-2 px-3 text-slate-300">{row.name}</td>
                <td className="py-2 px-3 text-right text-slate-300">
                  {(row.ablated_accuracy * 100).toFixed(1)}%
                </td>
                <td className="py-2 px-3 text-right font-semibold" style={{ color: dropColor(row.accuracy_drop) }}>
                  −{(row.accuracy_drop * 100).toFixed(2)}pp
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}
