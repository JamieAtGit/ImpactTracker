import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";
import { motion } from "framer-motion";

const GRADE_COLORS = {
  "A+": "#06d6a0", "A": "#10b981", "B": "#22c55e",
  "C":  "#eab308", "D": "#f59e0b", "E": "#ef4444", "F": "#dc2626",
};
const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"];

const PALETTE = [
  "#22d3ee", "#a78bfa", "#34d399", "#fb923c",
  "#f472b6", "#60a5fa", "#facc15", "#4ade80",
  "#f87171", "#c084fc", "#38bdf8", "#fbbf24",
  "#86efac", "#f9a8d4", "#93c5fd",
];

function SmallBarChart({ data, title, colorFn, maxBars = 12 }) {
  const trimmed = data.slice(0, maxBars);
  const maxVal = Math.max(...trimmed.map(d => d.value));
  return (
    <div>
      <h5 className="text-sm font-medium text-slate-300 mb-3">{title}</h5>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={trimmed}
            margin={{ top: 5, right: 10, bottom: 40, left: 10 }}
            barCategoryGap="20%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="name"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              angle={-30}
              textAnchor="end"
              interval={0}
            />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              labelStyle={{ color: "#e2e8f0" }}
              itemStyle={{ color: "#94a3b8" }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {trimmed.map((entry, i) => (
                <Cell key={i} fill={colorFn(entry, i)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function DatasetDistributionCharts({ datasetStats }) {
  if (!datasetStats) return (
    <div className="flex items-center justify-center h-32 text-slate-500">
      Loading dataset statistics…
    </div>
  );

  const {
    total_rows, grade_distribution, material_distribution,
    origin_distribution, transport_distribution, co2_distribution,
    train_size, test_size,
  } = datasetStats;

  const gradeData = GRADE_ORDER
    .filter(g => grade_distribution[g] !== undefined)
    .map(g => ({ name: g, value: grade_distribution[g] }));

  const materialData = Object.entries(material_distribution || {})
    .map(([k, v]) => ({ name: k, value: v }))
    .sort((a, b) => b.value - a.value);

  const originData = Object.entries(origin_distribution || {})
    .map(([k, v]) => ({ name: k, value: v }))
    .sort((a, b) => b.value - a.value);

  const transportData = Object.entries(transport_distribution || {})
    .map(([k, v]) => ({ name: k, value: v }))
    .sort((a, b) => b.value - a.value);

  // CO₂ histogram
  const co2Hist = (co2_distribution?.histogram_counts || []).map((count, i) => {
    const edges = co2_distribution.histogram_bin_edges_log1p;
    const lo = Math.exp(edges[i]) - 1;
    const hi = Math.exp(edges[i + 1]) - 1;
    return { name: `${lo.toFixed(2)}–${hi.toFixed(2)}`, value: count };
  });

  return (
    <div className="space-y-8">
      {/* Summary badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total samples", value: total_rows?.toLocaleString(), color: "text-cyan-400" },
          { label: "Training set", value: train_size?.toLocaleString(), color: "text-purple-400", sub: `${((train_size / total_rows) * 100).toFixed(0)}% of data` },
          { label: "Test set", value: test_size?.toLocaleString(), color: "text-amber-400", sub: `${((test_size / total_rows) * 100).toFixed(0)}% of data` },
          { label: "Eco grade classes", value: "7", color: "text-green-400", sub: "A+ through F" },
        ].map((item, i) => (
          <motion.div
            key={item.label}
            className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 text-center"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <div className={`text-2xl font-bold font-mono ${item.color}`}>{item.value}</div>
            <div className="text-slate-400 text-xs mt-1">{item.label}</div>
            {item.sub && <div className="text-slate-600 text-xs">{item.sub}</div>}
          </motion.div>
        ))}
      </div>

      {/* Grade distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <SmallBarChart
          data={gradeData}
          title="Grade Distribution (true labels)"
          colorFn={(entry) => GRADE_COLORS[entry.name] || "#94a3b8"}
        />
        <SmallBarChart
          data={transportData}
          title="Transport Mode Distribution"
          colorFn={(_, i) => PALETTE[i % PALETTE.length]}
        />
      </div>

      {/* Material distribution */}
      <SmallBarChart
        data={materialData}
        title="Top 12 Materials"
        colorFn={(_, i) => PALETTE[i % PALETTE.length]}
        maxBars={12}
      />

      {/* Origin distribution */}
      <SmallBarChart
        data={originData}
        title="Top 12 Countries of Origin"
        colorFn={(_, i) => PALETTE[i % PALETTE.length]}
        maxBars={12}
      />

      {/* CO₂ histogram */}
      <div>
        <h5 className="text-sm font-medium text-slate-300 mb-1">CO₂ Distribution (log-scaled bins)</h5>
        <p className="text-xs text-slate-500 mb-3">
          Mean: {co2_distribution?.mean} kg &nbsp;|&nbsp;
          Median: {co2_distribution?.median} kg &nbsp;|&nbsp;
          P25–P75: {co2_distribution?.p25}–{co2_distribution?.p75} kg &nbsp;|&nbsp;
          Max: {co2_distribution?.max} kg
        </p>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={co2Hist} margin={{ top: 5, right: 10, bottom: 55, left: 10 }} barCategoryGap="5%">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#94a3b8", fontSize: 9 }}
                angle={-45}
                textAnchor="end"
                interval={1}
              />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Bar dataKey="value" fill="#22d3ee" radius={[3, 3, 0, 0]} name="Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
