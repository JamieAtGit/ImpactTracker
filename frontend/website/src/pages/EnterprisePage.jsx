import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Header from "../components/Header";
import Footer from "../components/Footer";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend,
} from "recharts";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const GRADE_COLORS = {
  "A+": "#06d6a0", A: "#10b981", "B+": "#22c55e", B: "#84cc16",
  "C+": "#eab308", C: "#f59e0b", D: "#ef4444",
};

function KpiCard({ icon, value, label, sub, color = "text-cyan-400" }) {
  return (
    <motion.div
      className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
      <div className="text-slate-300 text-sm font-medium mt-1">{label}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </motion.div>
  );
}

function SectionHeader({ title, sub }) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold text-slate-100">{title}</h2>
      {sub && <p className="text-sm text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function EnterprisePage() {
  const [overview, setOverview]   = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [tab, setTab]             = useState("overview");

  useEffect(() => {
    Promise.all([
      fetch(`${BASE_URL}/api/enterprise/dashboard/overview`).then(r => r.ok ? r.json() : null),
      fetch(`${BASE_URL}/api/enterprise/analytics/carbon-trends`).then(r => r.ok ? r.json() : null),
    ]).then(([ov, an]) => {
      setOverview(ov);
      setAnalytics(an);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const tabs = [
    { id: "overview",   label: "Overview"  },
    { id: "analytics",  label: "Analytics" },
    { id: "suppliers",  label: "Suppliers" },
    { id: "compliance", label: "Compliance" },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <Header />

      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full px-4 py-1.5 text-xs text-indigo-300 font-medium mb-6">
              Enterprise Carbon Intelligence
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">
              Supply Chain Carbon Dashboard
            </h1>
            <p className="text-slate-400 text-lg max-w-2xl">
              AI-powered carbon intelligence for procurement teams. Track, analyse, and reduce
              Scope 3 emissions across your entire supplier network.
            </p>
            <div className="flex flex-wrap gap-3 mt-6 text-xs text-slate-400">
              {["GRI Compliant", "CDP Ready", "TCFD Aligned", "SBTi Compatible"].map(s => (
                <span key={s} className="bg-slate-800 border border-slate-700 rounded-full px-3 py-1">{s}</span>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-800/50 rounded-xl p-1 mb-10 w-fit">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === t.id
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center h-48 text-slate-500">
            Loading enterprise data…
          </div>
        )}

        {/* ── Overview Tab ── */}
        {!loading && tab === "overview" && overview && (
          <div className="space-y-10">
            <SectionHeader
              title="Executive Summary"
              sub="Real-time carbon intelligence across your product portfolio"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <KpiCard
                icon="📦"
                value={overview.executive_summary?.total_products_analyzed?.toLocaleString()}
                label="Products Analysed"
                sub="Across all categories"
                color="text-cyan-400"
              />
              <KpiCard
                icon="🌍"
                value={`${overview.executive_summary?.average_carbon_footprint_kg} kg`}
                label="Avg Carbon Footprint"
                sub="CO₂e per product"
                color="text-orange-400"
              />
              <KpiCard
                icon="🏭"
                value={overview.executive_summary?.total_suppliers_tracked?.toLocaleString()}
                label="Suppliers Tracked"
                sub="Origin countries"
                color="text-purple-400"
              />
              <KpiCard
                icon="♻️"
                value={`${overview.executive_summary?.sustainability_score_percentage}%`}
                label="High Recyclability"
                sub="Products in portfolio"
                color="text-emerald-400"
              />
            </div>

            {/* Carbon hotspots */}
            {overview.carbon_insights?.carbon_hotspots?.length > 0 && (
              <div>
                <SectionHeader title="Carbon Hotspots" sub="Highest-emission products in your portfolio" />
                <div className="space-y-2">
                  {overview.carbon_insights.carbon_hotspots.map((h, i) => (
                    <div key={i} className="flex items-center justify-between bg-slate-800/40 border border-slate-700/40 rounded-lg px-4 py-3">
                      <span className="text-slate-300 text-sm">{h.product}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-slate-500 text-xs">{h.brand}</span>
                        <span className="text-red-400 font-mono text-sm font-bold">{h.carbon_kg} kg</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Monthly trend */}
            {overview.carbon_insights?.monthly_trends?.length > 0 && (
              <div>
                <SectionHeader title="Carbon Trend (6 months)" sub="Average CO₂e per product over time" />
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={overview.carbon_insights.monthly_trends}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit=" kg" />
                      <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
                      <Line type="monotone" dataKey="avg_carbon_kg" stroke="#6366f1" strokeWidth={2} dot={false} name="Avg CO₂ kg" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Analytics Tab ── */}
        {!loading && tab === "analytics" && analytics && (
          <div className="space-y-10">
            <SectionHeader
              title="Carbon Analytics"
              sub="Emissions breakdown by material and transport mode"
            />

            {/* Material impact */}
            {analytics.carbon_trends?.material_impact_analysis && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Average CO₂ by Material</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={Object.entries(analytics.carbon_trends.material_impact_analysis)
                        .map(([k, v]) => ({ name: k, avg: v.avg_carbon_kg }))
                        .sort((a, b) => b.avg - a.avg)
                        .slice(0, 10)}
                      margin={{ top: 5, right: 20, bottom: 30, left: 20 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} angle={-30} textAnchor="end" />
                      <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit=" kg" />
                      <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
                      <Bar dataKey="avg" name="Avg CO₂ (kg)" radius={[4, 4, 0, 0]}>
                        {Object.entries(analytics.carbon_trends.material_impact_analysis)
                          .slice(0, 10)
                          .map((_, i) => <Cell key={i} fill={i < 3 ? "#ef4444" : i < 6 ? "#f59e0b" : "#22d3ee"} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Transport analysis */}
            {analytics.carbon_trends?.transportation_analysis && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">CO₂ by Transport Mode</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(analytics.carbon_trends.transportation_analysis).map(([mode, data]) => (
                    <div key={mode} className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4 text-center">
                      <div className="text-xl font-bold font-mono text-amber-400">{data.avg_carbon_kg} kg</div>
                      <div className="text-slate-300 text-sm mt-1">{mode}</div>
                      <div className={`text-xs mt-1 ${data.efficiency_rating === "Efficient" ? "text-emerald-400" : "text-red-400"}`}>
                        {data.efficiency_rating}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reduction opportunities */}
            {analytics.reduction_opportunities?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Top Reduction Opportunities</h3>
                <div className="space-y-2">
                  {analytics.reduction_opportunities.slice(0, 5).map((op, i) => (
                    <div key={i} className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg px-4 py-3 flex items-start justify-between gap-4">
                      <div>
                        <div className="text-slate-200 text-sm font-medium">{op.action}</div>
                        <div className="text-slate-500 text-xs mt-0.5">
                          Potential saving: {op.potential_carbon_saved} kg CO₂ · {op.improvement_percentage}% reduction
                        </div>
                      </div>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${
                        op.business_impact === "High"
                          ? "bg-red-500/15 text-red-400"
                          : "bg-yellow-500/15 text-yellow-400"
                      }`}>{op.business_impact} impact</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Suppliers Tab ── */}
        {!loading && tab === "suppliers" && overview && (
          <div className="space-y-8">
            <SectionHeader
              title="Supplier Intelligence"
              sub="Sustainability rankings across your supply chain"
            />
            {overview.supplier_intelligence?.top_sustainable_suppliers?.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700 text-left">
                      <th className="py-3 px-4 text-slate-400">Rank</th>
                      <th className="py-3 px-4 text-slate-400">Supplier / Origin</th>
                      <th className="py-3 px-4 text-slate-400">Avg CO₂ (kg)</th>
                      <th className="py-3 px-4 text-slate-400">Products</th>
                      <th className="py-3 px-4 text-slate-400">Sustainability Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.supplier_intelligence.top_sustainable_suppliers.map((s, i) => (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                        <td className="py-2 px-4 text-slate-500 font-mono">#{i + 1}</td>
                        <td className="py-2 px-4 text-slate-200">{s.origin}</td>
                        <td className="py-2 px-4 font-mono text-orange-400">{s.avg_carbon}</td>
                        <td className="py-2 px-4 text-slate-400">{s.product_count}</td>
                        <td className="py-2 px-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-slate-700 rounded-full max-w-24">
                              <div
                                className="h-full bg-emerald-500 rounded-full"
                                style={{ width: `${Math.min(s.sustainability_score, 100)}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono text-emerald-400">
                              {s.sustainability_score?.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── Compliance Tab ── */}
        {!loading && tab === "compliance" && overview && (
          <div className="space-y-8">
            <SectionHeader
              title="Compliance Reporting"
              sub="Regulatory readiness across major sustainability frameworks"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {overview.compliance_ready?.reporting_standards?.map(std => (
                <div key={std} className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 text-center">
                  <div className="text-emerald-400 text-2xl font-bold mb-1">✓</div>
                  <div className="text-slate-200 text-sm font-semibold">{std}</div>
                  <div className="text-slate-500 text-xs mt-1">Framework ready</div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                <div className="text-xl font-bold text-cyan-400">{overview.compliance_ready?.scope_3_coverage}</div>
                <div className="text-slate-300 text-sm mt-1">Scope 3 Coverage</div>
                <div className="text-slate-500 text-xs mt-1">Purchased goods & services</div>
              </div>
              <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                <div className="text-xl font-bold text-purple-400">{overview.compliance_ready?.data_quality_score}</div>
                <div className="text-slate-300 text-sm mt-1">Data Quality Score</div>
                <div className="text-slate-500 text-xs mt-1">Verified data sources</div>
              </div>
              <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                <div className="text-xl font-bold text-amber-400">{overview.compliance_ready?.last_updated}</div>
                <div className="text-slate-300 text-sm mt-1">Last Updated</div>
                <div className="text-slate-500 text-xs mt-1">Continuous monitoring</div>
              </div>
            </div>
          </div>
        )}

        {!loading && !overview && (
          <div className="flex items-center justify-center h-48 text-slate-500">
            Could not load enterprise data. Ensure the backend is running.
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
