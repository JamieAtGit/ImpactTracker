import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend,
} from "recharts";
import ModernLayout, { ModernCard, ModernSection, ModernBadge } from "../components/ModernLayout";
import Header from "../components/Header";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

// ── Small helpers ──────────────────────────────────────────────────────────────
function KpiCard({ icon, value, label, sub, color = "text-cyan-400" }) {
  return (
    <motion.div
      className="glass-card p-5"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="text-2xl mb-3">{icon}</div>
      <div className={`text-2xl font-bold font-mono ${color}`}>{value ?? "—"}</div>
      <div className="text-slate-300 text-sm font-medium mt-1">{label}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </motion.div>
  );
}

function TabButton({ id, label, icon, active, onClick }) {
  return (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
        active
          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
          : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
      }`}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
}

function EmptyState({ message = "No data available." }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 text-slate-500 gap-2">
      <span className="text-3xl">📭</span>
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function EnterprisePage() {
  const [overview, setOverview]   = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [tab, setTab]             = useState("overview");

  useEffect(() => {
    Promise.all([
      fetch(`${BASE_URL}/api/enterprise/dashboard/overview`, { credentials: "include" })
        .then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${BASE_URL}/api/enterprise/analytics/carbon-trends`, { credentials: "include" })
        .then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([ov, an]) => {
      setOverview(ov);
      setAnalytics(an);
      setLoading(false);
    });
  }, []);

  const tabs = [
    { id: "overview",   label: "Overview",    icon: "📊" },
    { id: "analytics",  label: "Analytics",   icon: "📈" },
    { id: "suppliers",  label: "Suppliers",   icon: "🏭" },
    { id: "compliance", label: "Compliance",  icon: "✅" },
  ];

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-10">

            {/* ── Hero ── */}
            <ModernSection>
              <motion.div
                className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-indigo-900/60 via-slate-900/80 to-slate-900/60 border border-indigo-500/20 p-10"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
              >
                {/* background glow */}
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

                <div className="relative max-w-3xl">
                  <div className="inline-flex items-center gap-2 bg-indigo-500/15 border border-indigo-500/30 rounded-full px-4 py-1.5 text-xs text-indigo-300 font-medium mb-5">
                    🏢 Enterprise Carbon Intelligence
                  </div>

                  <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-4 leading-tight">
                    Supply Chain<br />
                    <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                      Carbon Dashboard
                    </span>
                  </h1>

                  <p className="text-slate-300 text-lg leading-relaxed mb-6 max-w-2xl">
                    Impact Tracker's enterprise layer gives procurement and sustainability teams
                    a real-time view of Scope 3 emissions across their entire product portfolio —
                    so you can identify hotspots, benchmark suppliers, and produce audit-ready
                    compliance reports without manual spreadsheet work.
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {["Scope 3 Tracking", "Supplier Benchmarking", "GRI / CDP / TCFD Ready", "AI-Powered Insights"].map(tag => (
                      <span key={tag} className="bg-slate-800/80 border border-slate-600/50 text-slate-300 text-xs rounded-full px-3 py-1">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            </ModernSection>

            {/* ── What this page is for ── */}
            <ModernSection>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    icon: "🔍",
                    title: "Identify Carbon Hotspots",
                    desc: "See which products and suppliers drive the most emissions in your portfolio, ranked by CO₂e contribution.",
                    color: "from-red-500/10 to-orange-500/10 border-red-500/20",
                  },
                  {
                    icon: "📉",
                    title: "Find Reduction Opportunities",
                    desc: "AI surfaces actionable changes — swap materials, reroute transport, source closer — with estimated savings.",
                    color: "from-emerald-500/10 to-cyan-500/10 border-emerald-500/20",
                  },
                  {
                    icon: "📋",
                    title: "Stay Compliance-Ready",
                    desc: "All data is structured for GRI, CDP, TCFD, and SBTi frameworks so your sustainability reports write themselves.",
                    color: "from-indigo-500/10 to-purple-500/10 border-indigo-500/20",
                  },
                ].map(c => (
                  <motion.div
                    key={c.title}
                    className={`rounded-xl bg-gradient-to-br ${c.color} border p-5`}
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                  >
                    <div className="text-2xl mb-3">{c.icon}</div>
                    <h3 className="text-slate-100 font-semibold mb-2">{c.title}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed">{c.desc}</p>
                  </motion.div>
                ))}
              </div>
            </ModernSection>

            {/* ── Tabs ── */}
            <div className="flex flex-wrap gap-1 bg-slate-800/50 rounded-xl p-1 w-fit">
              {tabs.map(t => (
                <TabButton key={t.id} {...t} active={tab === t.id} onClick={setTab} />
              ))}
            </div>

            {loading && (
              <ModernCard>
                <div className="flex items-center justify-center h-40 text-slate-500 gap-3">
                  <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  Loading enterprise data…
                </div>
              </ModernCard>
            )}

            {/* ── Overview Tab ── */}
            {!loading && tab === "overview" && (
              <div className="space-y-8">
                {overview ? (
                  <>
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
                        value={`${overview.executive_summary?.average_carbon_footprint_kg ?? "—"} kg`}
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
                        value={`${overview.executive_summary?.sustainability_score_percentage ?? "—"}%`}
                        label="High Recyclability"
                        sub="Products in portfolio"
                        color="text-emerald-400"
                      />
                    </div>

                    {overview.carbon_insights?.carbon_hotspots?.length > 0 && (
                      <ModernCard solid>
                        <h3 className="text-slate-200 font-semibold mb-4 flex items-center gap-2">
                          <span className="text-red-400">🔥</span> Carbon Hotspots
                          <span className="text-slate-500 text-sm font-normal ml-1">— highest-emission products</span>
                        </h3>
                        <div className="space-y-2">
                          {overview.carbon_insights.carbon_hotspots.map((h, i) => (
                            <div key={i} className="flex items-center justify-between bg-slate-800/40 border border-slate-700/40 rounded-lg px-4 py-3">
                              <div className="flex items-center gap-3">
                                <span className="text-slate-600 font-mono text-xs w-5">#{i + 1}</span>
                                <span className="text-slate-300 text-sm">{h.product}</span>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-slate-500 text-xs hidden sm:block">{h.brand}</span>
                                <span className="text-red-400 font-mono text-sm font-bold">{h.carbon_kg} kg</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ModernCard>
                    )}

                    {overview.carbon_insights?.monthly_trends?.length > 0 && (
                      <ModernCard solid>
                        <h3 className="text-slate-200 font-semibold mb-4">📅 Carbon Trend — last 6 months</h3>
                        <div className="h-56">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={overview.carbon_insights.monthly_trends}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                              <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit=" kg" />
                              <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
                              <Line type="monotone" dataKey="avg_carbon_kg" stroke="#6366f1" strokeWidth={2} dot={false} name="Avg CO₂ (kg)" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </ModernCard>
                    )}
                  </>
                ) : (
                  <ModernCard>
                    <EmptyState message="Could not load overview data. Check the backend is running." />
                  </ModernCard>
                )}
              </div>
            )}

            {/* ── Analytics Tab ── */}
            {!loading && tab === "analytics" && (
              <div className="space-y-8">
                {analytics ? (
                  <>
                    {analytics.carbon_trends?.material_impact_analysis && (
                      <ModernCard solid>
                        <h3 className="text-slate-200 font-semibold mb-4">🧱 Average CO₂ by Material</h3>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={Object.entries(analytics.carbon_trends.material_impact_analysis)
                                .map(([k, v]) => ({ name: k, avg: v.avg_carbon_kg }))
                                .sort((a, b) => b.avg - a.avg)
                                .slice(0, 10)}
                              margin={{ top: 5, right: 20, bottom: 35, left: 20 }}
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
                      </ModernCard>
                    )}

                    {analytics.carbon_trends?.transportation_analysis && (
                      <ModernCard solid>
                        <h3 className="text-slate-200 font-semibold mb-4">🚚 CO₂ by Transport Mode</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {Object.entries(analytics.carbon_trends.transportation_analysis).map(([mode, data]) => (
                            <div key={mode} className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4 text-center">
                              <div className="text-xl font-bold font-mono text-amber-400">{data.avg_carbon_kg} kg</div>
                              <div className="text-slate-300 text-sm mt-1 capitalize">{mode}</div>
                              <div className={`text-xs mt-1.5 font-medium ${data.efficiency_rating === "Efficient" ? "text-emerald-400" : "text-red-400"}`}>
                                {data.efficiency_rating}
                              </div>
                            </div>
                          ))}
                        </div>
                      </ModernCard>
                    )}

                    {analytics.reduction_opportunities?.length > 0 && (
                      <ModernCard solid>
                        <h3 className="text-slate-200 font-semibold mb-4">💡 Top Reduction Opportunities</h3>
                        <div className="space-y-2">
                          {analytics.reduction_opportunities.slice(0, 5).map((op, i) => (
                            <div key={i} className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg px-4 py-3 flex items-start justify-between gap-4">
                              <div>
                                <div className="text-slate-200 text-sm font-medium">{op.action}</div>
                                <div className="text-slate-500 text-xs mt-0.5">
                                  Saves ~{op.potential_carbon_saved} kg CO₂ · {op.improvement_percentage}% reduction
                                </div>
                              </div>
                              <ModernBadge variant={op.business_impact === "High" ? "error" : "warning"} size="sm">
                                {op.business_impact}
                              </ModernBadge>
                            </div>
                          ))}
                        </div>
                      </ModernCard>
                    )}
                  </>
                ) : (
                  <ModernCard>
                    <EmptyState message="Could not load analytics data." />
                  </ModernCard>
                )}
              </div>
            )}

            {/* ── Suppliers Tab ── */}
            {!loading && tab === "suppliers" && (
              <div className="space-y-6">
                <ModernCard solid>
                  <div className="mb-4">
                    <h3 className="text-slate-200 font-semibold">🏭 Supplier Sustainability Rankings</h3>
                    <p className="text-slate-500 text-sm mt-1">Suppliers ranked by average carbon footprint per product. Lower is better.</p>
                  </div>
                  {overview?.supplier_intelligence?.top_sustainable_suppliers?.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-700">
                            <th className="py-3 px-4 text-left text-slate-400 font-medium">Rank</th>
                            <th className="py-3 px-4 text-left text-slate-400 font-medium">Origin</th>
                            <th className="py-3 px-4 text-left text-slate-400 font-medium">Avg CO₂</th>
                            <th className="py-3 px-4 text-left text-slate-400 font-medium">Products</th>
                            <th className="py-3 px-4 text-left text-slate-400 font-medium">Sustainability Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {overview.supplier_intelligence.top_sustainable_suppliers.map((s, i) => (
                            <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                              <td className="py-3 px-4 text-slate-500 font-mono text-sm">#{i + 1}</td>
                              <td className="py-3 px-4 text-slate-200 font-medium">{s.origin}</td>
                              <td className="py-3 px-4 font-mono text-orange-400">{s.avg_carbon} kg</td>
                              <td className="py-3 px-4 text-slate-400">{s.product_count}</td>
                              <td className="py-3 px-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex-1 h-1.5 bg-slate-700 rounded-full max-w-28">
                                    <div
                                      className="h-full bg-emerald-500 rounded-full"
                                      style={{ width: `${Math.min(s.sustainability_score, 100)}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-mono text-emerald-400 w-12 text-right">
                                    {s.sustainability_score?.toFixed(1)}%
                                  </span>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <EmptyState message="No supplier data available." />
                  )}
                </ModernCard>
              </div>
            )}

            {/* ── Compliance Tab ── */}
            {!loading && tab === "compliance" && (
              <div className="space-y-6">
                <ModernCard solid>
                  <div className="mb-6">
                    <h3 className="text-slate-200 font-semibold">📋 Regulatory Readiness</h3>
                    <p className="text-slate-500 text-sm mt-1">
                      Impact Tracker structures all emission data to meet major sustainability reporting frameworks
                      out of the box — no manual reformatting required.
                    </p>
                  </div>

                  {overview?.compliance_ready?.reporting_standards?.length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      {overview.compliance_ready.reporting_standards.map(std => (
                        <div key={std} className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 text-center">
                          <div className="text-emerald-400 text-2xl font-bold mb-2">✓</div>
                          <div className="text-slate-200 text-sm font-semibold">{std}</div>
                          <div className="text-slate-500 text-xs mt-1">Ready</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      {["GRI Standards", "CDP Disclosure", "TCFD Framework", "SBTi Compatible"].map(std => (
                        <div key={std} className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 text-center">
                          <div className="text-emerald-400 text-2xl font-bold mb-2">✓</div>
                          <div className="text-slate-200 text-sm font-semibold">{std}</div>
                          <div className="text-slate-500 text-xs mt-1">Ready</div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                      <div className="text-xl font-bold text-cyan-400">
                        {overview?.compliance_ready?.scope_3_coverage ?? "Category 1"}
                      </div>
                      <div className="text-slate-300 text-sm mt-1">Scope 3 Coverage</div>
                      <div className="text-slate-500 text-xs mt-1">Purchased goods &amp; services</div>
                    </div>
                    <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                      <div className="text-xl font-bold text-purple-400">
                        {overview?.compliance_ready?.data_quality_score ?? "AI-verified"}
                      </div>
                      <div className="text-slate-300 text-sm mt-1">Data Quality</div>
                      <div className="text-slate-500 text-xs mt-1">ML-validated sources</div>
                    </div>
                    <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl p-5">
                      <div className="text-xl font-bold text-amber-400">
                        {overview?.compliance_ready?.last_updated ?? "Real-time"}
                      </div>
                      <div className="text-slate-300 text-sm mt-1">Data Freshness</div>
                      <div className="text-slate-500 text-xs mt-1">Continuous monitoring</div>
                    </div>
                  </div>
                </ModernCard>

                <ModernCard>
                  <h3 className="text-slate-200 font-semibold mb-3">ℹ️ About Enterprise Access</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    This dashboard aggregates emission data from all products tracked through Impact Tracker.
                    For dedicated enterprise accounts with custom supplier onboarding, white-label reporting,
                    and API access, contact us via the{" "}
                    <a href="/contact" className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2">
                      contact page
                    </a>.
                  </p>
                </ModernCard>
              </div>
            )}

          </div>
        ),
      }}
    </ModernLayout>
  );
}
