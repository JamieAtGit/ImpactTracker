import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, CartesianGrid,
} from "recharts";
import ModernLayout, { ModernCard, ModernSection, ModernBadge } from "../components/ModernLayout";
import Header from "../components/Header";
import useAuth from "../hooks/useAuth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const GRADE_COLOURS = {
  "A+": { badge: "success", bar: "#06d6a0", text: "text-emerald-400" },
  "A":  { badge: "success", bar: "#10b981", text: "text-green-400"   },
  "B":  { badge: "info",    bar: "#22d3ee", text: "text-cyan-400"    },
  "C":  { badge: "warning", bar: "#f59e0b", text: "text-amber-400"   },
  "D":  { badge: "warning", bar: "#f97316", text: "text-orange-400"  },
  "E":  { badge: "error",   bar: "#ef4444", text: "text-red-400"     },
  "F":  { badge: "error",   bar: "#dc2626", text: "text-red-500"     },
};

function StatCard({ icon, value, label, sub, color = "text-cyan-400" }) {
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

export default function HistoryPage() {
  const { user } = useAuth();
  const [history, setHistory]   = useState([]);
  const [stats, setStats]       = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [fetchError, setFetchError] = useState(false);
  const [search, setSearch]     = useState("");

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    Promise.all([
      fetch(`${BASE_URL}/api/my/history`,          { credentials: "include" }).then(r => r.ok ? r.json() : []),
      fetch(`${BASE_URL}/api/my/stats`,            { credentials: "include" }).then(r => r.ok ? r.json() : null),
      fetch(`${BASE_URL}/api/my/carbon-timeline`,  { credentials: "include" }).then(r => r.ok ? r.json() : null),
    ]).then(([h, s, t]) => {
      setHistory(h);
      setStats(s);
      setTimeline(t?.timeline ?? []);
      setLoading(false);
    }).catch(() => { setFetchError(true); setLoading(false); });
  }, [user]);

  const filtered = history.filter(item =>
    !search || item.title?.toLowerCase().includes(search.toLowerCase()) ||
    item.material?.toLowerCase().includes(search.toLowerCase()) ||
    item.brand?.toLowerCase().includes(search.toLowerCase())
  );

  const gradeChartData = stats?.grade_distribution
    ? Object.entries(stats.grade_distribution).map(([g, count]) => ({ grade: g, count }))
    : [];

  if (!user) {
    return (
      <ModernLayout>
        {{
          nav: <Header />,
          content: (
            <ModernSection className="text-center">
              <ModernCard className="max-w-md mx-auto">
                <div className="space-y-4">
                  <div className="text-4xl">🔒</div>
                  <h2 className="text-xl font-display text-slate-200">Sign in to see your history</h2>
                  <p className="text-slate-400 text-sm">Your scan history and personal stats are saved to your account.</p>
                  <Link to="/login">
                    <button className="btn-primary px-6 py-2 mt-2">Log in</button>
                  </Link>
                </div>
              </ModernCard>
            </ModernSection>
          ),
        }}
      </ModernLayout>
    );
  }

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-10">

            {/* ── Hero ── */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight mb-3">
                  <span className="text-slate-100">Your</span>{" "}
                  <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                    Carbon History
                  </span>
                </h1>
                <p className="text-slate-400 text-lg max-w-xl">
                  Every product you've scanned, your personal CO₂ stats, and your grade breakdown — all in one place.
                </p>
              </motion.div>
            </ModernSection>

            {fetchError && (
              <ModernCard>
                <div className="flex items-center gap-3 text-red-400 text-sm py-2">
                  <span>⚠️</span>
                  <span>Could not load your history. Check your connection and refresh.</span>
                </div>
              </ModernCard>
            )}

            {loading ? (
              <ModernCard>
                <div className="flex items-center justify-center h-40 gap-3 text-slate-500">
                  <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                  Loading your history…
                </div>
              </ModernCard>
            ) : fetchError ? null : (
              <>
                {/* ── Stats grid ── */}
                {stats && stats.total_scans > 0 && (
                  <ModernSection title="Your Stats" icon={true}>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                      <StatCard
                        icon="🔍"
                        value={stats.total_scans}
                        label="Total Scans"
                        sub="Products analysed"
                        color="text-cyan-400"
                      />
                      <StatCard
                        icon="🌍"
                        value={stats.avg_co2_kg != null ? `${stats.avg_co2_kg} kg` : null}
                        label="Avg CO₂ / Product"
                        sub="CO₂e per scan"
                        color="text-orange-400"
                      />
                      <StatCard
                        icon="📦"
                        value={stats.total_co2_kg != null ? `${stats.total_co2_kg} kg` : null}
                        label="Total CO₂ Tracked"
                        sub="Combined footprint"
                        color="text-purple-400"
                      />
                      <StatCard
                        icon="🏆"
                        value={stats.best_grade || "—"}
                        label="Best Grade Seen"
                        sub={stats.top_material ? `Top material: ${stats.top_material}` : undefined}
                        color={GRADE_COLOURS[stats.best_grade]?.text ?? "text-emerald-400"}
                      />
                    </div>

                    {gradeChartData.length > 0 && (
                      <ModernCard solid>
                        <h3 className="text-slate-300 font-medium mb-4 text-sm">Grade Distribution</h3>
                        <div className="h-40">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={gradeChartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                              <XAxis dataKey="grade" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
                              <Tooltip
                                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                cursor={{ fill: "rgba(255,255,255,0.05)" }}
                              />
                              <Bar dataKey="count" name="Scans" radius={[4, 4, 0, 0]}>
                                {gradeChartData.map(d => (
                                  <Cell key={d.grade} fill={GRADE_COLOURS[d.grade]?.bar ?? "#6366f1"} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </ModernCard>
                    )}

                    {timeline.length >= 2 && (
                      <ModernCard solid>
                        <h3 className="text-slate-300 font-medium mb-1 text-sm">Monthly Carbon Footprint</h3>
                        <p className="text-slate-500 text-xs mb-4">CO₂ kg tracked per month from your scanned products</p>
                        <div className="h-48">
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={timeline} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                              <XAxis
                                dataKey="month"
                                tick={{ fill: "#94a3b8", fontSize: 11 }}
                                tickFormatter={m => m.slice(5)}
                              />
                              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} unit=" kg" />
                              <Tooltip
                                contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                                formatter={(v, _) => [`${v} kg CO₂`, "Monthly total"]}
                                labelFormatter={m => `Month: ${m}`}
                              />
                              <Line
                                type="monotone"
                                dataKey="co2_kg"
                                stroke="#22d3ee"
                                strokeWidth={2}
                                dot={{ fill: "#22d3ee", r: 4 }}
                                activeDot={{ r: 6 }}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </ModernCard>
                    )}
                  </ModernSection>
                )}

                {/* ── Scan history ── */}
                <ModernSection title="Scan History" icon={true}>
                  {history.length === 0 ? (
                    <ModernCard className="text-center">
                      <div className="space-y-3 py-6">
                        <div className="text-4xl">📭</div>
                        <p className="text-slate-300 font-medium">No scans yet</p>
                        <p className="text-slate-500 text-sm">Head to the{" "}
                          <Link to="/predict" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2">Predict page</Link>
                          {" "}and scan your first product.
                        </p>
                      </div>
                    </ModernCard>
                  ) : (
                    <>
                      {/* Search */}
                      <div className="mb-4">
                        <input
                          type="text"
                          value={search}
                          onChange={e => setSearch(e.target.value)}
                          placeholder="Search by product, brand or material…"
                          className="w-full md:w-80 px-4 py-2 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                        />
                      </div>

                      <ModernCard solid className="p-0 overflow-hidden">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-slate-700">
                                <th className="text-left px-4 py-3 text-slate-400 font-medium">Product</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium">Grade</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium">CO₂</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium hidden sm:table-cell">Origin</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium hidden md:table-cell">Transport</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium hidden md:table-cell">Date</th>
                                <th className="text-left px-4 py-3 text-slate-400 font-medium hidden lg:table-cell">Quality</th>
                              </tr>
                            </thead>
                            <tbody>
                              {filtered.map((item, i) => (
                                <motion.tr
                                  key={item.id}
                                  className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                                  initial={{ opacity: 0, y: 8 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  transition={{ duration: 0.25, delay: i * 0.03 }}
                                >
                                  <td className="px-4 py-3">
                                    <div className="max-w-[220px] truncate text-slate-200" title={item.title}>
                                      {item.title}
                                    </div>
                                    {(item.brand || item.material) && (
                                      <div className="text-slate-500 text-xs mt-0.5">
                                        {[item.brand, item.material].filter(Boolean).join(" · ")}
                                      </div>
                                    )}
                                  </td>
                                  <td className="px-4 py-3">
                                    {item.eco_grade ? (
                                      <ModernBadge variant={GRADE_COLOURS[item.eco_grade]?.badge ?? "info"} size="sm">
                                        {item.eco_grade}
                                      </ModernBadge>
                                    ) : (
                                      <span className="text-slate-600 text-xs">—</span>
                                    )}
                                  </td>
                                  <td className="px-4 py-3 font-mono text-slate-300">
                                    {item.co2_kg != null ? `${item.co2_kg.toFixed(2)} kg` : <span className="text-slate-600">—</span>}
                                  </td>
                                  <td className="px-4 py-3 text-slate-400 hidden sm:table-cell">
                                    {item.origin || <span className="text-slate-600">—</span>}
                                  </td>
                                  <td className="px-4 py-3 text-slate-400 hidden md:table-cell capitalize">
                                    {item.transport_mode || <span className="text-slate-600">—</span>}
                                  </td>
                                  <td className="px-4 py-3 text-slate-500 text-xs hidden md:table-cell">
                                    {item.scanned_at
                                      ? new Date(item.scanned_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
                                      : "—"}
                                  </td>
                                  <td className="px-4 py-3 hidden lg:table-cell">
                                    {item.data_quality ? (
                                      <ModernBadge
                                        variant={item.data_quality === "high" ? "success" : item.data_quality === "medium" ? "warning" : "error"}
                                        size="sm"
                                      >
                                        {item.data_quality}
                                      </ModernBadge>
                                    ) : (
                                      <span className="text-slate-600 text-xs">—</span>
                                    )}
                                  </td>
                                </motion.tr>
                              ))}
                              {filtered.length === 0 && (
                                <tr>
                                  <td colSpan={7} className="text-center py-8 text-slate-500">
                                    No results match "{search}"
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </ModernCard>
                    </>
                  )}
                </ModernSection>
              </>
            )}

          </div>
        ),
      }}
    </ModernLayout>
  );
}
