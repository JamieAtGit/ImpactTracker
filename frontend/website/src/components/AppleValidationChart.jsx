import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell,
} from "recharts";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const CATEGORY_COLORS = {
  "iPhone":       "#22d3ee",
  "MacBook":      "#a78bfa",
  "iPad":         "#34d399",
  "Apple Watch":  "#fb923c",
  "AirPods":      "#f472b6",
  "Mac":          "#60a5fa",
  "HomePod":      "#facc15",
};

const GRADE_COLORS = {
  "A+": "#06d6a0", "A": "#10b981", "B": "#22c55e",
  "C": "#eab308", "D": "#f59e0b", "E": "#ef4444", "F": "#dc2626",
};

function SummaryBadge({ value, label, sub, color = "text-cyan-400" }) {
  return (
    <div className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-5 text-center">
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
      <div className="text-slate-300 text-sm font-medium mt-1">{label}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </div>
  );
}

function CustomScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl p-3 text-xs max-w-xs shadow-xl">
      <p className="text-slate-200 font-semibold mb-1">{d.product}</p>
      <p className="text-slate-400">{d.category} · {d.weight_kg} kg</p>
      <div className="mt-2 space-y-1">
        <p>
          <span className="text-slate-500">Our estimate:</span>{" "}
          <span className="text-cyan-300 font-mono">{d.our_defra_co2_kg} kg</span>{" "}
          <span className="font-bold" style={{ color: GRADE_COLORS[d.our_ml_grade] }}>({d.our_ml_grade})</span>
        </p>
        <p>
          <span className="text-slate-500">Apple verified:</span>{" "}
          <span className="text-purple-300 font-mono">{d.apple_co2_total_kg} kg</span>{" "}
          <span className="font-bold" style={{ color: GRADE_COLORS[d.apple_implied_grade] }}>({d.apple_implied_grade})</span>
        </p>
        <p>
          <span className="text-slate-500">Capture rate:</span>{" "}
          <span className="text-amber-300 font-mono">{d.capture_of_total_pct}%</span>
        </p>
        <p>
          <span className="text-slate-500">Underestimated by:</span>{" "}
          <span className="text-red-300 font-mono">{d.underestimation_factor}×</span>
        </p>
      </div>
    </div>
  );
}

export default function AppleValidationChart() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch(`${BASE_URL}/api/apple-validation`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-40 text-slate-500">Loading validation data…</div>
  );
  if (!data) return (
    <div className="flex items-center justify-center h-40 text-red-400">Could not load Apple validation data</div>
  );

  const { summary, products, per_category } = data;

  // Scatter plot: our CO₂ vs Apple's CO₂ (log scale via log transform)
  const scatterPoints = products.map(p => ({
    ...p,
    x: Math.log10(p.our_defra_co2_kg + 0.01),
    y: Math.log10(p.apple_co2_total_kg),
  }));

  // Group scatter by category for multi-colour
  const byCategory = {};
  scatterPoints.forEach(p => {
    if (!byCategory[p.category]) byCategory[p.category] = [];
    byCategory[p.category].push(p);
  });

  // Per-category underestimation bar chart
  const categoryBars = per_category.map(c => ({
    name: c.category,
    factor: Math.round(c.mean_underest_factor),
  })).sort((a, b) => b.factor - a.factor);

  // Per-product comparison (sorted by Apple CO₂)
  const sorted = [...products].sort((a, b) => a.apple_co2_total_kg - b.apple_co2_total_kg);

  return (
    <div className="space-y-8">

      {/* Context */}
      <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl p-5">
        <p className="text-slate-300 text-sm leading-relaxed">
          Apple publishes a <strong className="text-slate-200">Product Environmental Report (PER)</strong> for every
          product it sells, independently audited to <strong className="text-slate-200">ISO 14040/14044</strong> lifecycle
          assessment standards. These reports disclose verified total CO₂e (kg) broken down by manufacturing,
          transport, use, and end-of-life stages. This validation compares our model's predictions against
          <strong className="text-slate-200"> {data.n_products} Apple products</strong> — data the model was never trained on.
        </p>
        <p className="text-xs text-slate-500 mt-2">
          Source: <a href="https://www.apple.com/environment/reports/" className="text-cyan-500 hover:underline" target="_blank" rel="noreferrer">apple.com/environment/reports</a>
          {" "}· Reports span {Math.min(...products.map(p => p.report_year))}–{Math.max(...products.map(p => p.report_year))}
        </p>
      </div>

      {/* Summary badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryBadge
          value={`${summary.grade_agreement_pct}%`}
          label="Grade Agreement"
          sub="ML grade vs Apple's implied grade"
          color="text-amber-400"
        />
        <SummaryBadge
          value={`${summary.mean_capture_of_comparable_pct}%`}
          label="CO₂ Captured"
          sub="Of Apple's mfg + transport CO₂"
          color="text-red-400"
        />
        <SummaryBadge
          value={`${summary.median_underestimation_factor}×`}
          label="Underestimation"
          sub="Median factor vs Apple's total"
          color="text-orange-400"
        />
        <SummaryBadge
          value={data.n_products}
          label="Products Tested"
          sub="Across 7 Apple categories"
          color="text-cyan-400"
        />
      </div>

      {/* Scatter plot */}
      <div>
        <h5 className="text-sm font-semibold text-slate-300 mb-1">
          Our Estimate vs Apple's Verified CO₂ (log scale)
        </h5>
        <p className="text-xs text-slate-500 mb-4">
          Points on the dashed diagonal would indicate perfect agreement. Points below it mean we are underestimating.
          Hover for product details.
        </p>
        <div className="flex flex-wrap gap-3 mb-4">
          {Object.entries(CATEGORY_COLORS).map(([cat, col]) => (
            <span key={cat} className="flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: col }} />
              {cat}
            </span>
          ))}
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="x"
                type="number"
                name="Our CO₂ (log₁₀)"
                domain={[-2, 3]}
                tickFormatter={v => `${Math.pow(10, v).toFixed(1)}`}
                label={{ value: "Our Estimate (kg CO₂, log scale)", position: "insideBottom", offset: -15, fill: "#94a3b8", fontSize: 11 }}
                tick={{ fill: "#94a3b8", fontSize: 10 }}
              />
              <YAxis
                dataKey="y"
                type="number"
                name="Apple's CO₂ (log₁₀)"
                domain={[0, 3]}
                tickFormatter={v => `${Math.pow(10, v).toFixed(0)}`}
                label={{ value: "Apple Verified (kg CO₂, log scale)", angle: -90, position: "insideLeft", offset: 15, fill: "#94a3b8", fontSize: 11 }}
                tick={{ fill: "#94a3b8", fontSize: 10 }}
              />
              <Tooltip content={<CustomScatterTooltip />} />
              {/* Perfect agreement line (log space: y = x) */}
              <ReferenceLine
                segment={[{ x: -2, y: -2 }, { x: 3, y: 3 }]}
                stroke="#475569"
                strokeDasharray="6 4"
                label={{ value: "Perfect agreement", fill: "#475569", fontSize: 10, position: "insideTopLeft" }}
              />
              {Object.entries(byCategory).map(([cat, pts]) => (
                <Scatter
                  key={cat}
                  name={cat}
                  data={pts}
                  fill={CATEGORY_COLORS[cat]}
                  opacity={0.85}
                  r={5}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Per-category underestimation */}
      <div>
        <h5 className="text-sm font-semibold text-slate-300 mb-1">Average Underestimation Factor by Category</h5>
        <p className="text-xs text-slate-500 mb-4">
          How many times larger Apple's verified CO₂ is compared to our estimate. Higher = larger gap.
        </p>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categoryBars} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit="×" />
              <Tooltip
                formatter={v => [`${v}×`, "Underestimation"]}
                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              />
              <Bar dataKey="factor" radius={[4, 4, 0, 0]}>
                {categoryBars.map((entry, i) => (
                  <Cell key={i} fill={CATEGORY_COLORS[entry.name] || "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Product table */}
      <div>
        <h5 className="text-sm font-semibold text-slate-300 mb-3">Per-Product Breakdown</h5>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-left">
                <th className="py-2 px-3 text-slate-400">Product</th>
                <th className="py-2 px-3 text-slate-400">Our grade</th>
                <th className="py-2 px-3 text-slate-400">Apple grade</th>
                <th className="py-2 px-3 text-slate-400">Our CO₂</th>
                <th className="py-2 px-3 text-slate-400">Apple total</th>
                <th className="py-2 px-3 text-slate-400">Capture</th>
                <th className="py-2 px-3 text-slate-400">Factor</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((p, i) => (
                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                  <td className="py-1.5 px-3 text-slate-300">{p.product}</td>
                  <td className="py-1.5 px-3">
                    <span className="font-bold" style={{ color: GRADE_COLORS[p.our_ml_grade] }}>
                      {p.our_ml_grade}
                    </span>
                  </td>
                  <td className="py-1.5 px-3">
                    <span className="font-bold" style={{ color: GRADE_COLORS[p.apple_implied_grade] }}>
                      {p.apple_implied_grade}
                    </span>
                  </td>
                  <td className="py-1.5 px-3 font-mono text-slate-300">{p.our_defra_co2_kg} kg</td>
                  <td className="py-1.5 px-3 font-mono text-purple-300">{p.apple_co2_total_kg} kg</td>
                  <td className="py-1.5 px-3 font-mono text-amber-400">{p.capture_of_total_pct}%</td>
                  <td className="py-1.5 px-3 font-mono text-red-400">{p.underestimation_factor}×</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interpretation */}
      <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl p-5 space-y-3">
        <h5 className="text-sm font-semibold text-slate-200">Interpretation</h5>
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-300">Grade agreement of {summary.grade_agreement_pct}%</strong> reflects
          a fundamental scope mismatch, not model error. Our system predicts grades using transport emissions
          and bulk material manufacturing intensity (DEFRA 2023 factors). Apple's verified figures cover the
          full lifecycle — including semiconductor fabrication, multi-tier supply chain transport, use-phase
          electricity, and end-of-life processing.
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-300">The {summary.median_underestimation_factor}× median underestimation</strong> is
          dominated by semiconductor manufacturing energy. Producing 1 kg of integrated circuits requires
          approximately 630 kg CO₂e — roughly 80× the DEFRA aluminum intensity factor of 8 kg/kg used for the
          chassis. Apple Watches and AirPods show the largest gaps ({categoryBars[0]?.factor}× and {categoryBars[1]?.factor}×)
          because they are lightweight but contain dense, energy-intensive electronics.
        </p>
        <p className="text-xs text-slate-400 leading-relaxed">
          <strong className="text-slate-300">What this means for the system:</strong> ImpactTracker is accurate
          for products where transport and bulk material manufacturing dominate — textiles, packaging, heavy goods,
          food containers. For consumer electronics, it provides a lower bound on environmental impact and correctly
          signals relative comparisons (heavier, air-freighted products rank worse), but the absolute CO₂ figure
          substantially underestimates true lifecycle impact.
        </p>
        <div className="grid grid-cols-2 gap-2 pt-2">
          {summary.what_formula_misses?.map((item, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-slate-500">
              <span className="text-red-500 mt-0.5 flex-shrink-0">✗</span>
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
