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
  Legend,
} from "recharts";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const FEATURE_COLORS = {
  material:  "#8b5cf6", // purple
  transport: "#f97316", // orange
  origin:    "#22d3ee", // cyan
  weight:    "#4ade80", // green
};

const FEATURE_LABELS = {
  material:  "Material",
  transport: "Transport",
  origin:    "Origin",
  weight:    "Weight",
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 text-xs shadow-xl max-w-xs">
      <p className="text-slate-200 font-semibold mb-1">{d.name}</p>
      <p className="text-slate-400">
        Grade changes in{" "}
        <span className="font-bold" style={{ color: FEATURE_COLORS[d.feature] }}>
          {d.grade_change_pct.toFixed(1)}%
        </span>{" "}
        of cases
      </p>
      {d.n_tested > 0 && (
        <p className="text-slate-500 mt-1">
          {d.n_affected} / {d.n_tested} samples affected
        </p>
      )}
    </div>
  );
};

function FeatureDot({ color }) {
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full mr-1.5"
      style={{ backgroundColor: color }}
    />
  );
}

export default function SensitivityAnalysisChart() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(false);
  const [activeFeature, setActiveFeature] = useState("all");

  useEffect(() => {
    fetch(`${BASE_URL}/api/sensitivity`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) { setError(true); }
        else { setData(d); }
        setLoading(false);
      })
      .catch(() => { setError(true); setLoading(false); });
  }, []);

  if (loading) return <p className="text-slate-400 text-sm text-center py-8">Loading sensitivity analysis...</p>;
  if (error)   return <p className="text-red-400 text-sm text-center py-8">Failed to load sensitivity results.</p>;

  const summary = data.summary;
  const allPerts = data.perturbations;

  // Filter and sort
  const displayed = allPerts
    .filter((p) => activeFeature === "all" || p.feature === activeFeature)
    .sort((a, b) => b.grade_change_pct - a.grade_change_pct)
    .slice(0, 20); // cap at 20 items for readability

  const airToShip = summary.transport_air_to_ship_pct;
  const mostSensitive = summary.most_sensitive_feature;

  return (
    <div className="space-y-6">

      {/* Key callout */}
      <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
        <p className="text-orange-300 text-xs font-semibold mb-1">Highest Sensitivity — Motivates Conformal Prediction</p>
        <p className="text-slate-300 text-sm">
          <strong className="text-slate-100 capitalize">{mostSensitive} mode</strong> has the highest
          average sensitivity across all perturbation types.{" "}
          {airToShip != null && (
            <>
              Switching from <strong className="text-slate-100">Air</strong> to{" "}
              <strong className="text-slate-100">Ship</strong> transport changes the eco grade in{" "}
              <span className="text-orange-300 font-bold">{airToShip.toFixed(1)}%</span> of cases.{" "}
            </>
          )}
          This directly motivates the conformal prediction sets shown on each result — they capture
          this uncertainty by returning a <em>set</em> of plausible grades rather than a single point estimate.
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(summary.avg_grade_change_by_feature ?? {}).map(([feat, avg]) => (
          <div
            key={feat}
            className="rounded-lg p-3 border"
            style={{
              backgroundColor: `${FEATURE_COLORS[feat]}18`,
              borderColor: `${FEATURE_COLORS[feat]}40`,
            }}
          >
            <p className="text-xs font-medium mb-1" style={{ color: FEATURE_COLORS[feat] }}>
              {FEATURE_LABELS[feat] ?? feat}
            </p>
            <p className="text-lg font-bold text-slate-100">{avg.toFixed(1)}%</p>
            <p className="text-xs text-slate-500">avg grade change</p>
          </div>
        ))}
      </div>

      {/* Feature filter */}
      <div className="flex flex-wrap gap-2">
        {["all", "material", "transport", "origin", "weight"].map((f) => (
          <button
            key={f}
            onClick={() => setActiveFeature(f)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors border ${
              activeFeature === f
                ? "border-slate-500 text-slate-100 bg-slate-700"
                : "border-slate-700 text-slate-400 bg-transparent hover:text-slate-300"
            }`}
            style={
              activeFeature === f && f !== "all"
                ? { borderColor: `${FEATURE_COLORS[f]}60`, color: FEATURE_COLORS[f], backgroundColor: `${FEATURE_COLORS[f]}18` }
                : {}
            }
          >
            {f === "all" ? "All" : FEATURE_LABELS[f]}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div>
        <p className="text-xs text-slate-500 mb-3">
          % of test samples where the predicted eco grade changes when the feature is perturbed.
          Showing top {displayed.length} perturbations.
        </p>
        <ResponsiveContainer width="100%" height={Math.max(240, displayed.length * 22)}>
          <BarChart
            data={displayed}
            layout="vertical"
            margin={{ top: 4, right: 60, left: 200, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis
              type="number"
              tickFormatter={(v) => `${v.toFixed(0)}%`}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#475569" }}
              tickLine={{ stroke: "#475569" }}
              domain={[0, 100]}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "#cbd5e1", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={195}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148,163,184,0.05)" }} />
            <Bar dataKey="grade_change_pct" radius={[0, 4, 4, 0]}>
              {displayed.map((entry, i) => (
                <Cell key={i} fill={FEATURE_COLORS[entry.feature] ?? "#64748b"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-slate-400">
        {Object.entries(FEATURE_COLORS).map(([feat, color]) => (
          <span key={feat} className="flex items-center">
            <FeatureDot color={color} />
            {FEATURE_LABELS[feat]}
          </span>
        ))}
      </div>

    </div>
  );
}
