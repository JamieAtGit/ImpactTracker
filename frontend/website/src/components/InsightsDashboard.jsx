import React, { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { motion } from "framer-motion";
import { ModernCard, ModernBadge } from "./ModernLayout";

const MODERN_COLORS = [
  "#06D6A0", // Emerald green
  "#3B82F6", // Professional blue  
  "#8B5CF6", // Deep purple
  "#F59E0B", // Amber
  "#EF4444", // Coral red
  "#06B6D4", // Cyan
  "#10B981", // Green
  "#6366F1", // Indigo
  "#EC4899", // Pink
  "#84CC16"  // Lime
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card-solid p-3 shadow-lg">
        <p className="text-slate-200 font-medium text-sm">{`${label}`}</p>
        <p className="text-slate-300 text-sm">
          <span className="text-cyan-400">Count:</span>{" "}
          <span className="font-semibold">{payload[0].value}</span>
        </p>
      </div>
    );
  }
  return null;
};

const StatCard = ({ title, value, subtitle, color = "blue" }) => {
  const colorMap = {
    blue: "from-blue-500 to-cyan-500",
    purple: "from-purple-500 to-violet-500",
    green: "from-green-500 to-emerald-500",
    amber: "from-amber-500 to-orange-500"
  };

  return (
    <motion.div
      className="glass-card p-4 text-center"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className={`w-12 h-12 mx-auto mb-3 rounded-xl bg-gradient-to-br ${colorMap[color]} flex items-center justify-center`}>
        <span className="text-white font-bold text-lg">{value}</span>
      </div>
      <h3 className="text-slate-200 font-medium text-sm">{title}</h3>
      {subtitle && <p className="text-slate-400 text-xs mt-1">{subtitle}</p>}
    </motion.div>
  );
};

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function InsightsDashboard() {
  const [scoreData, setScoreData] = useState([]);
  const [materialData, setMaterialData] = useState([]);
  const [stats, setStats] = useState({
    total_products: 0,
    total_materials: 0,
    total_predictions: 0,
    recent_activity: 0
  });

  
  useEffect(() => {
    // Use the new enhanced dashboard metrics endpoint
    fetch(`${BASE_URL}/api/dashboard-metrics`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          console.error("Dashboard metrics error:", data.error);
          return;
        }

        // Update stats with real data instead of placeholders
        setStats(data.stats || {});
        setScoreData(data.score_distribution || []);
        setMaterialData(data.material_distribution || []);
      })
      .catch((err) => {
        console.error("Failed to load dashboard metrics:", err);
        // Fallback to eco-data endpoint with metadata
        fetch(`${BASE_URL}/api/eco-data?limit=5000`)
          .then((res) => res.json())
          .then((response) => {
            // Handle new response format with metadata
            const data = response.products || response;
            const metadata = response.metadata || {};
            
            if (!Array.isArray(data)) return;

            const scores = data.map((d) => d.true_eco_score).filter(Boolean);
            const materials = data.map((d) => d.material).filter(Boolean);

            // ✅ Score breakdown
            const scoreCounts = scores.reduce((acc, score) => {
              acc[score] = (acc[score] || 0) + 1;
              return acc;
            }, {});
            setScoreData(
              Object.entries(scoreCounts).map(([score, count]) => ({
                name: score,
                value: count,
              }))
            );

            // ✅ Top materials (deduped + sorted)
            const deduped = materials.reduce((acc, curr) => {
              const existing = acc.find((item) => item.name === curr);
              if (existing) existing.value += 1;
              else acc.push({ name: curr, value: 1 });
              return acc;
            }, []);
            setMaterialData(deduped.sort((a, b) => b.value - a.value).slice(0, 10));
            
            // Use metadata for accurate total count
            setStats({
              total_products: metadata.total_products_in_dataset || data.length,
              total_materials: deduped.length,
              total_predictions: 0,
              recent_activity: 0
            });
            
            console.log(`📊 Dashboard loaded: ${metadata.products_returned || data.length} of ${metadata.total_products_in_dataset || 'unknown'} total products`);
          })
          .catch(() => console.error("All dashboard endpoints failed"));
      });
  }, []);

  return (
    <div className="space-y-8">
      {/* Statistics Grid */}
      <motion.div
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <StatCard
          title="Total Products"
          value={stats.total_products}
          subtitle="In database"
          color="blue"
        />
        <StatCard
          title="Materials"
          value={stats.total_materials}
          subtitle="Different types"
          color="purple"
        />
        <StatCard
          title="Predictions Made"
          value={stats.total_predictions}
          subtitle="ML predictions"
          color="green"
        />
        <StatCard
          title="Recent Activity"
          value={stats.recent_activity}
          subtitle="This session"
          color="amber"
        />
      </motion.div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Eco Score Distribution */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
        >
          <ModernCard solid>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-display text-slate-200">
                    Eco Score Distribution
                  </h3>
                  <div className="group relative">
                    <div className="w-5 h-5 rounded-full bg-cyan-500/20 flex items-center justify-center cursor-help">
                      <span className="text-cyan-400 text-xs">🔍</span>
                    </div>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 border border-slate-600">
                      Distribution of environmental impact scores (A+ = best, F = worst)
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"></div>
                    </div>
                  </div>
                </div>
                <ModernBadge variant="info" size="sm">
                  {scoreData.length} scores
                </ModernBadge>
              </div>
              
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={scoreData} 
                    margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
                  >
                    <XAxis 
                      dataKey="name" 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#cbd5e1', fontSize: 12 }}
                    />
                    <YAxis 
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#cbd5e1', fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar 
                      dataKey="value" 
                      fill="url(#barGradient)" 
                      radius={[6, 6, 0, 0]}
                    />
                    <defs>
                      <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#06d6a0" />
                        <stop offset="100%" stopColor="#3b82f6" />
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ModernCard>
        </motion.div>

        {/* Materials Distribution */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: "easeOut" }}
        >
          <ModernCard solid className="p-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-display text-slate-200">
                    Material Distribution
                  </h3>
                  <div className="group relative">
                    <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center cursor-help">
                      <span className="text-green-400 text-xs">🔍</span>
                    </div>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 border border-slate-600">
                      Breakdown of materials used across all analyzed products
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"></div>
                    </div>
                  </div>
                </div>
                <ModernBadge variant="success" size="sm">
                  {materialData.length} types
                </ModernBadge>
              </div>
              
              <div className="h-96 relative">
                <div className="absolute inset-0 bg-gradient-to-br from-slate-800/20 to-slate-900/40 rounded-xl border border-slate-700/30"></div>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <defs>
                      {MODERN_COLORS.map((color, index) => (
                        <linearGradient key={index} id={`gradient-${index}`} x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor={color} stopOpacity={1} />
                          <stop offset="100%" stopColor={color} stopOpacity={0.7} />
                        </linearGradient>
                      ))}
                      <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                        <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="#000000" floodOpacity="0.3"/>
                      </filter>
                    </defs>
                    <Pie
                      data={materialData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={85}
                      innerRadius={45}
                      paddingAngle={3}
                      isAnimationActive={true}
                      animationBegin={0}
                      animationDuration={2000}
                      animationEasing="ease-out"
                      stroke="#0f172a"
                      strokeWidth={3}
                      filter="url(#shadow)"
                    >
                      {materialData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={`url(#gradient-${index % MODERN_COLORS.length})`}
                          stroke="#0f172a"
                          strokeWidth={3}
                          style={{
                            filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))',
                            transition: 'all 0.3s ease'
                          }}
                        />
                      ))}
                    </Pie>
                    
                    {/* Enhanced Central label */}
                    <g>
                      <circle cx="50%" cy="50%" r="40" fill="rgba(15, 23, 42, 0.95)" stroke="rgba(6, 182, 212, 0.3)" strokeWidth="1"/>
                      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                        <tspan x="50%" dy="-0.8em" className="fill-slate-100 text-lg font-bold" style={{fontSize: '14px'}}>
                          MATERIALS
                        </tspan>
                        <tspan x="50%" dy="1.6em" className="fill-cyan-400 text-sm font-semibold" style={{fontSize: '12px'}}>
                          ANALYSIS
                        </tspan>
                        <tspan x="50%" dy="1.4em" className="fill-slate-400 text-xs" style={{fontSize: '10px'}}>
                          {materialData.length} Types
                        </tspan>
                      </text>
                    </g>
                    
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0];
                          const total = materialData.reduce((sum, item) => sum + item.value, 0);
                          const percentage = ((data.value / total) * 100).toFixed(1);
                          return (
                            <div className="glass-card-solid p-5 shadow-2xl border border-slate-600 min-w-52">
                              <div className="flex items-center gap-3 mb-3">
                                <div 
                                  className="w-4 h-4 rounded-full shadow-md" 
                                  style={{backgroundColor: MODERN_COLORS[materialData.findIndex(item => item.name === data.name) % MODERN_COLORS.length]}}
                                ></div>
                                <p className="text-slate-100 font-bold text-base">{data.name}</p>
                              </div>
                              <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                  <span className="text-slate-300 text-sm font-medium">Product Count:</span>
                                  <span className="text-cyan-400 font-bold text-lg">{data.value}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                  <span className="text-slate-300 text-sm font-medium">Market Share:</span>
                                  <span className="text-purple-400 font-bold text-lg">{percentage}%</span>
                                </div>
                                <div className="pt-2 border-t border-slate-600">
                                  <span className="text-slate-400 text-xs">Material analysis based on ML predictions</span>
                                </div>
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    
                    <Legend 
                      content={({ payload }) => (
                        <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm pt-6">
                          {payload.slice(0, 8).map((entry, index) => {
                            const materialItem = materialData.find(item => item.name === entry.value);
                            const total = materialData.reduce((sum, item) => sum + item.value, 0);
                            const percentage = materialItem ? ((materialItem.value / total) * 100).toFixed(0) : 0;
                            
                            return (
                              <div key={index} className="flex items-center gap-3 group cursor-pointer">
                                <div 
                                  className="w-4 h-4 rounded-full flex-shrink-0 shadow-md border-2 border-slate-500 group-hover:scale-125 transition-all duration-300" 
                                  style={{
                                    backgroundColor: MODERN_COLORS[payload.findIndex(item => item.value === entry.value) % MODERN_COLORS.length],
                                    boxShadow: `0 0 8px ${MODERN_COLORS[payload.findIndex(item => item.value === entry.value) % MODERN_COLORS.length]}40`
                                  }}
                                ></div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between">
                                    <span className="text-slate-300 font-medium truncate group-hover:text-slate-200 transition-colors">
                                      {entry.value}
                                    </span>
                                    <span className="text-slate-400 text-xs font-medium ml-2">
                                      {percentage}%
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                          {payload.length > 8 && (
                            <div className="col-span-2 text-center pt-2 border-t border-slate-700">
                              <span className="text-slate-500 text-xs">
                                +{payload.length - 8} more materials
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ModernCard>
        </motion.div>
      </div>
    </div>
  );
}
