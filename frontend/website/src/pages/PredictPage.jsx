import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection } from "../components/ModernLayout";
import Header from "../components/Header";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;
const UK_HUB = { lat: 54.8, lon: -4.6 };

// ── Static data ────────────────────────────────────────────────────────────────

const ORIGIN_HUBS = {
  "UK":           { lat: 54.8,  lon: -4.6,    flag: "🇬🇧" },
  "Germany":      { lat: 51.2,  lon: 10.4,    flag: "🇩🇪" },
  "France":       { lat: 46.6,  lon: 1.9,     flag: "🇫🇷" },
  "Netherlands":  { lat: 52.3,  lon: 5.3,     flag: "🇳🇱" },
  "Poland":       { lat: 51.9,  lon: 19.1,    flag: "🇵🇱" },
  "Spain":        { lat: 40.5,  lon: -3.7,    flag: "🇪🇸" },
  "Italy":        { lat: 42.5,  lon: 12.6,    flag: "🇮🇹" },
  "Turkey":       { lat: 38.9,  lon: 35.2,    flag: "🇹🇷" },
  "India":        { lat: 20.6,  lon: 78.9,    flag: "🇮🇳" },
  "Bangladesh":   { lat: 23.7,  lon: 90.4,    flag: "🇧🇩" },
  "Vietnam":      { lat: 14.1,  lon: 108.3,   flag: "🇻🇳" },
  "Indonesia":    { lat: -0.8,  lon: 113.9,   flag: "🇮🇩" },
  "China":        { lat: 39.9,  lon: 116.4,   flag: "🇨🇳" },
  "Japan":        { lat: 36.2,  lon: 138.3,   flag: "🇯🇵" },
  "South Korea":  { lat: 36.5,  lon: 127.8,   flag: "🇰🇷" },
  "USA":          { lat: 39.8,  lon: -98.6,   flag: "🇺🇸" },
  "Canada":       { lat: 56.1,  lon: -106.3,  flag: "🇨🇦" },
  "Mexico":       { lat: 23.6,  lon: -102.6,  flag: "🇲🇽" },
  "Brazil":       { lat: -14.2, lon: -51.9,   flag: "🇧🇷" },
  "Australia":    { lat: -25.3, lon: 133.8,   flag: "🇦🇺" },
};

const MATERIALS = [
  { value: "Bamboo",          icon: "🎋", label: "Bamboo" },
  { value: "Paper",           icon: "📄", label: "Paper" },
  { value: "Glass",           icon: "🫙", label: "Glass" },
  { value: "Cotton",          icon: "🧺", label: "Cotton" },
  { value: "Wood",            icon: "🪵", label: "Wood" },
  { value: "Cardboard",       icon: "📦", label: "Cardboard" },
  { value: "Aluminum",        icon: "🥤", label: "Aluminium" },
  { value: "Stainless Steel", icon: "🔩", label: "Steel" },
  { value: "Metal",           icon: "⚙️", label: "Metal" },
  { value: "Ceramic",         icon: "🏺", label: "Ceramic" },
  { value: "Rubber",          icon: "⚫", label: "Rubber" },
  { value: "Plastic",         icon: "🧴", label: "Plastic" },
  { value: "Mixed",           icon: "🗂️", label: "Mixed" },
];

const TRANSPORT_OPTIONS = [
  { value: "Ship",  icon: "🚢", label: "Ship",  sub: "Lowest emissions" },
  { value: "Truck", icon: "🚛", label: "Truck", sub: "Mid emissions" },
  { value: "Air",   icon: "✈️", label: "Air",   sub: "Highest emissions" },
];

const RECYCLABILITY_OPTIONS = [
  { value: "High",   label: "High",   sub: "e.g. glass, paper" },
  { value: "Medium", label: "Medium", sub: "e.g. steel, cotton" },
  { value: "Low",    label: "Low",    sub: "e.g. plastic, rubber" },
];

const PRESETS = [
  { name: "Phone Case",   icon: "📱", config: { material: "Plastic",         weight: 0.1, transport: "Air",   recyclability: "Low",    origin: "China"      } },
  { name: "Water Bottle", icon: "💧", config: { material: "Stainless Steel", weight: 0.5, transport: "Ship",  recyclability: "High",   origin: "China"      } },
  { name: "T-Shirt",      icon: "👕", config: { material: "Cotton",          weight: 0.2, transport: "Air",   recyclability: "High",   origin: "Bangladesh" } },
  { name: "Coffee Maker", icon: "☕", config: { material: "Mixed",           weight: 1.5, transport: "Ship",  recyclability: "Low",    origin: "China"      } },
  { name: "Bamboo Set",   icon: "🎋", config: { material: "Bamboo",          weight: 0.3, transport: "Ship",  recyclability: "High",   origin: "China"      } },
  { name: "Laptop",       icon: "💻", config: { material: "Metal",           weight: 2.0, transport: "Air",   recyclability: "Low",    origin: "China"      } },
  { name: "Kids Toy",     icon: "🧸", config: { material: "Plastic",         weight: 0.3, transport: "Air",   recyclability: "Low",    origin: "China"      } },
  { name: "Glass Jar",    icon: "🫙", config: { material: "Glass",           weight: 0.4, transport: "Truck", recyclability: "High",   origin: "Germany"    } },
];

const GRADE_CFG = {
  "A+": { color: "#06d6a0", ring: "ring-emerald-500/60", bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Excellent"      },
  "A":  { color: "#10b981", ring: "ring-green-500/60",   bg: "bg-green-500/10",   text: "text-green-400",   label: "Very Good"      },
  "B":  { color: "#22d3ee", ring: "ring-cyan-500/60",    bg: "bg-cyan-500/10",    text: "text-cyan-400",    label: "Good"           },
  "C":  { color: "#f59e0b", ring: "ring-amber-500/60",   bg: "bg-amber-500/10",   text: "text-amber-400",   label: "Average"        },
  "D":  { color: "#f97316", ring: "ring-orange-500/60",  bg: "bg-orange-500/10",  text: "text-orange-400",  label: "Below Average"  },
  "E":  { color: "#ef4444", ring: "ring-red-400/60",     bg: "bg-red-400/10",     text: "text-red-400",     label: "Poor"           },
  "F":  { color: "#dc2626", ring: "ring-red-600/60",     bg: "bg-red-600/10",     text: "text-red-500",     label: "Very Poor"      },
};

const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"];
const GRADE_VAL   = Object.fromEntries(GRADE_ORDER.map((g, i) => [g, 6 - i]));

// Sensitivity alternatives to try in parallel
const ALT_CHECKS = [
  { label: "Ship transport",      icon: "🚢", change: { transport: "Ship"  } },
  { label: "Truck transport",     icon: "🚛", change: { transport: "Truck" } },
  { label: "Bamboo material",     icon: "🎋", change: { material: "Bamboo",  recyclability: "High" } },
  { label: "Paper material",      icon: "📄", change: { material: "Paper",   recyclability: "High" } },
  { label: "Glass material",      icon: "🫙", change: { material: "Glass",   recyclability: "High" } },
  { label: "Cotton material",     icon: "🧺", change: { material: "Cotton",  recyclability: "High" } },
  { label: "UK sourcing",         icon: "🇬🇧", change: { origin: "UK"      } },
  { label: "European sourcing",   icon: "🇩🇪", change: { origin: "Germany" } },
  { label: "High recyclability",  icon: "♻️",  change: { recyclability: "High" } },
  { label: "Optimal combination", icon: "⭐",  change: { material: "Bamboo", transport: "Ship", origin: "UK", recyclability: "High" } },
];

// ── Helpers ────────────────────────────────────────────────────────────────────

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function distanceKm(origin) {
  const hub = ORIGIN_HUBS[origin] || ORIGIN_HUBS["China"];
  return haversine(hub.lat, hub.lon, UK_HUB.lat, UK_HUB.lon);
}

async function fetchGrade(config) {
  const res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      material: config.material,
      weight: config.weight,
      transport: config.transport,
      recyclability: config.recyclability,
      origin: config.origin,
      distance_origin_to_uk: distanceKm(config.origin),
      override_transport_mode: config.transport,
      title: "Impact Explorer",
    }),
  });
  if (!res.ok) throw new Error("predict failed");
  return res.json();
}

function gradeImprovement(from, to) {
  return (GRADE_VAL[to] ?? 0) - (GRADE_VAL[from] ?? 0);
}

const DEFAULT_CONFIG = PRESETS[0].config;

// ── Sub-components ─────────────────────────────────────────────────────────────

function PresetBar({ active, onSelect }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
      {PRESETS.map(p => (
        <motion.button
          key={p.name}
          onClick={() => onSelect(p.config)}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          className={`flex-shrink-0 flex flex-col items-center gap-1.5 px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
            active === p.name
              ? "bg-indigo-600/20 border-indigo-500/60 text-indigo-300"
              : "glass-card border-slate-700/50 text-slate-400 hover:text-slate-200"
          }`}
        >
          <span className="text-2xl">{p.icon}</span>
          <span className="whitespace-nowrap">{p.name}</span>
        </motion.button>
      ))}
    </div>
  );
}

function TransportSelector({ value, onChange }) {
  return (
    <div>
      <p className="text-slate-400 text-sm mb-2">Transport Mode</p>
      <div className="grid grid-cols-3 gap-2">
        {TRANSPORT_OPTIONS.map(t => (
          <motion.button
            key={t.value}
            onClick={() => onChange(t.value)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className={`flex flex-col items-center gap-1 py-3 px-2 rounded-xl border text-center transition-all ${
              value === t.value
                ? "bg-blue-600/20 border-blue-500/60 text-blue-300"
                : "glass-card border-slate-700/40 text-slate-400 hover:border-slate-500"
            }`}
          >
            <span className="text-xl">{t.icon}</span>
            <span className="text-sm font-medium text-slate-200">{t.label}</span>
            <span className="text-xs text-slate-500">{t.sub}</span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function MaterialGrid({ value, onChange }) {
  return (
    <div>
      <p className="text-slate-400 text-sm mb-2">Material</p>
      <div className="flex flex-wrap gap-2">
        {MATERIALS.map(m => (
          <motion.button
            key={m.value}
            onClick={() => onChange(m.value)}
            whileTap={{ scale: 0.95 }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm transition-all ${
              value === m.value
                ? "bg-cyan-600/20 border-cyan-500/60 text-cyan-300"
                : "glass-card border-slate-700/40 text-slate-400 hover:border-slate-500"
            }`}
          >
            <span>{m.icon}</span>
            <span>{m.label}</span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function OriginSelector({ value, onChange }) {
  return (
    <div>
      <p className="text-slate-400 text-sm mb-2">Country of Origin</p>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-cyan-500/50"
      >
        {Object.entries(ORIGIN_HUBS).map(([name, { flag }]) => (
          <option key={name} value={name}>{flag} {name}</option>
        ))}
      </select>
    </div>
  );
}

function WeightSlider({ value, onChange }) {
  const STOPS = [0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20];
  const idx = STOPS.reduce((best, v, i) =>
    Math.abs(v - value) < Math.abs(STOPS[best] - value) ? i : best, 0);

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <p className="text-slate-400 text-sm">Weight</p>
        <span className="text-cyan-400 font-mono text-sm font-medium">{value} kg</span>
      </div>
      <input
        type="range"
        min={0}
        max={STOPS.length - 1}
        step={1}
        value={idx}
        onChange={e => onChange(STOPS[parseInt(e.target.value)])}
        className="w-full accent-cyan-500"
      />
      <div className="flex justify-between text-slate-600 text-xs mt-1">
        <span>50g</span><span>500g</span><span>2 kg</span><span>10 kg</span><span>20 kg</span>
      </div>
    </div>
  );
}

function RecyclabilityToggle({ value, onChange }) {
  return (
    <div>
      <p className="text-slate-400 text-sm mb-2">Recyclability</p>
      <div className="grid grid-cols-3 gap-2">
        {RECYCLABILITY_OPTIONS.map(r => (
          <motion.button
            key={r.value}
            onClick={() => onChange(r.value)}
            whileTap={{ scale: 0.97 }}
            className={`py-2 px-2 rounded-lg border text-center transition-all ${
              value === r.value
                ? r.value === "High"   ? "bg-emerald-600/20 border-emerald-500/60 text-emerald-300"
                : r.value === "Medium" ? "bg-amber-600/20 border-amber-500/60 text-amber-300"
                                       : "bg-red-600/20 border-red-500/60 text-red-300"
                : "glass-card border-slate-700/40 text-slate-400 hover:border-slate-500"
            }`}
          >
            <div className="text-sm font-medium text-slate-200">{r.label}</div>
            <div className="text-xs text-slate-500 mt-0.5 hidden sm:block">{r.sub}</div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function GradeDisplay({ grade, confidence, loading }) {
  const cfg = GRADE_CFG[grade] || GRADE_CFG["C"];
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Big grade ring */}
      <AnimatePresence mode="wait">
        <motion.div
          key={grade || "loading"}
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.6, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 22 }}
          className={`relative w-32 h-32 rounded-full ring-4 ${cfg.ring} ${cfg.bg} flex items-center justify-center`}
        >
          {loading ? (
            <div className="w-8 h-8 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
          ) : (
            <span className={`text-5xl font-black font-display ${cfg.text}`}>{grade ?? "?"}</span>
          )}
        </motion.div>
      </AnimatePresence>

      {!loading && grade && (
        <motion.div
          key={grade + "-label"}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <p className={`text-lg font-semibold ${cfg.text}`}>{cfg.label}</p>
          {confidence != null && (
            <p className="text-slate-500 text-xs mt-1">
              {confidence.toFixed(0)}% model confidence
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
}

function GradeScale({ currentGrade }) {
  return (
    <div className="flex items-center justify-between gap-1">
      {GRADE_ORDER.map(g => {
        const cfg = GRADE_CFG[g];
        const active = g === currentGrade;
        return (
          <div key={g} className="flex flex-col items-center gap-1 flex-1">
            <motion.div
              animate={{ scale: active ? 1.25 : 1 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`w-full h-2 rounded-full transition-all ${
                active ? "" : "opacity-30"
              }`}
              style={{ backgroundColor: cfg.color }}
            />
            <span className={`text-xs font-mono font-bold transition-all ${
              active ? cfg.text : "text-slate-600"
            }`}>{g}</span>
          </div>
        );
      })}
    </div>
  );
}

function ProbBars({ proba, currentGrade }) {
  if (!proba?.length) return null;
  const sorted = [...GRADE_ORDER].map(g => {
    const entry = proba.find(p => p.grade === g);
    return { grade: g, probability: entry?.probability ?? 0 };
  });
  return (
    <div className="space-y-1.5">
      {sorted.map(({ grade, probability }) => {
        const cfg = GRADE_CFG[grade];
        const active = grade === currentGrade;
        return (
          <div key={grade} className="flex items-center gap-2">
            <span className={`text-xs font-mono w-5 text-right font-bold ${active ? cfg.text : "text-slate-500"}`}>
              {grade}
            </span>
            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${probability}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="h-full rounded-full"
                style={{ backgroundColor: cfg.color, opacity: active ? 1 : 0.4 }}
              />
            </div>
            <span className={`text-xs font-mono w-10 text-right ${active ? cfg.text : "text-slate-600"}`}>
              {probability.toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

function InsightCard({ insight, currentGrade }) {
  const improvement = insight.improvement;
  const newCfg = GRADE_CFG[insight.newGrade] || GRADE_CFG["C"];
  const curCfg = GRADE_CFG[currentGrade] || GRADE_CFG["C"];

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-center gap-3 p-3 rounded-xl border ${
        improvement > 1
          ? "bg-emerald-500/5 border-emerald-500/25"
          : "bg-slate-800/40 border-slate-700/40"
      }`}
    >
      <span className="text-xl flex-shrink-0">{insight.icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-slate-300 text-sm font-medium">{insight.label}</p>
        <p className="text-slate-500 text-xs mt-0.5">{insight.description}</p>
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <span className={`text-sm font-bold font-mono ${curCfg.text}`}>{currentGrade}</span>
        <span className="text-slate-600">→</span>
        <span className={`text-sm font-bold font-mono ${newCfg.text}`}>{insight.newGrade}</span>
        {improvement > 0 && (
          <span className="text-emerald-400 text-xs font-medium">
            +{improvement}
          </span>
        )}
      </div>
    </motion.div>
  );
}

function ConfigPanel({ config, onChange, label }) {
  return (
    <div className="space-y-6">
      {label && (
        <p className="text-slate-400 text-sm font-medium uppercase tracking-wider">{label}</p>
      )}
      <TransportSelector value={config.transport} onChange={v => onChange({ ...config, transport: v })} />
      <MaterialGrid       value={config.material}  onChange={v => onChange({ ...config, material: v })} />
      <OriginSelector     value={config.origin}    onChange={v => onChange({ ...config, origin: v })} />
      <WeightSlider       value={config.weight}    onChange={v => onChange({ ...config, weight: v })} />
      <RecyclabilityToggle value={config.recyclability} onChange={v => onChange({ ...config, recyclability: v })} />
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function PredictPage() {
  const [config, setConfig]         = useState(DEFAULT_CONFIG);
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(true);
  const [apiError, setApiError]     = useState(false);
  const [insights, setInsights]     = useState([]);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [activePreset, setActivePreset]       = useState(PRESETS[0].name);
  const [compareMode, setCompareMode]         = useState(false);
  const [config2, setConfig2]       = useState(PRESETS[1].config);
  const [result2, setResult2]       = useState(null);
  const [loading2, setLoading2]     = useState(false);
  const debounceRef  = useRef(null);
  const debounceRef2 = useRef(null);

  // ── Auto-predict on config change ──
  const predict = useCallback(async (cfg, setRes, setLoad) => {
    setLoad(true);
    setApiError(false);
    try {
      const data = await fetchGrade(cfg);
      setRes(data);
    } catch (e) {
      console.error("predict error", e);
      setApiError(true);
    } finally {
      setLoad(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => predict(config, setResult, setLoading), 380);
    return () => clearTimeout(debounceRef.current);
  }, [config, predict]);

  useEffect(() => {
    if (!compareMode) return;
    if (debounceRef2.current) clearTimeout(debounceRef2.current);
    debounceRef2.current = setTimeout(() => predict(config2, setResult2, setLoading2), 380);
    return () => clearTimeout(debounceRef2.current);
  }, [config2, compareMode, predict]);

  // ── Sensitivity analysis ──
  useEffect(() => {
    if (!result?.predicted_label) return;
    const currentGrade = result.predicted_label;
    setInsightsLoading(true);

    const candidates = ALT_CHECKS.filter(alt => {
      const keys = Object.keys(alt.change);
      return keys.some(k => config[k] !== alt.change[k]);
    });

    Promise.allSettled(
      candidates.map(alt =>
        fetchGrade({ ...config, ...alt.change })
          .then(data => ({ alt, newGrade: data.predicted_label }))
      )
    ).then(results => {
      const improvements = results
        .filter(r => r.status === "fulfilled")
        .map(r => r.value)
        .map(({ alt, newGrade }) => ({
          ...alt,
          newGrade,
          improvement: gradeImprovement(currentGrade, newGrade),
          description: buildDescription(alt.change, config),
        }))
        .filter(i => i.improvement > 0)
        .sort((a, b) => b.improvement - a.improvement);

      setInsights(improvements.slice(0, 5));
      setInsightsLoading(false);
    });
  }, [result]);

  function buildDescription(change, cfg) {
    const parts = [];
    if (change.transport && change.transport !== cfg.transport)
      parts.push(`switch from ${cfg.transport} to ${change.transport}`);
    if (change.material && change.material !== cfg.material)
      parts.push(`use ${change.material} instead of ${cfg.material}`);
    if (change.origin && change.origin !== cfg.origin)
      parts.push(`source from ${change.origin} instead of ${cfg.origin}`);
    if (change.recyclability && change.recyclability !== cfg.recyclability)
      parts.push(`increase recyclability to ${change.recyclability}`);
    return parts.length ? parts.join(", ") : "adjust this parameter";
  }

  function applyPreset(presetConfig) {
    const match = PRESETS.find(p =>
      Object.keys(p.config).every(k => p.config[k] === presetConfig[k])
    );
    setActivePreset(match?.name ?? null);
    setConfig(presetConfig);
    setInsights([]);
  }

  const currentGrade = result?.predicted_label;
  const origin1km = Math.round(distanceKm(config.origin));

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-8">

            {/* ── Hero ── */}
            <ModernSection>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="max-w-2xl"
              >
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight mb-3">
                  <span className="text-slate-100">Impact</span>{" "}
                  <span className="bg-gradient-to-r from-green-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
                    Explorer
                  </span>
                </h1>
                <p className="text-slate-400 text-lg leading-relaxed">
                  Adjust material, transport, origin and weight — the AI grade updates live.
                  See exactly what changes would have the biggest effect on a product's environmental impact.
                </p>
              </motion.div>
            </ModernSection>

            {/* ── Preset picker ── */}
            <ModernSection>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-slate-400 text-sm">Start with a product type:</p>
                <button
                  onClick={() => setCompareMode(m => !m)}
                  className={`text-sm px-3 py-1.5 rounded-lg border transition-all ${
                    compareMode
                      ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300"
                      : "glass-card border-slate-700/50 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {compareMode ? "⚡ Compare ON" : "⚡ Compare two products"}
                </button>
              </div>
              <PresetBar active={activePreset} onSelect={applyPreset} />
            </ModernSection>

            {/* ── Main two-column layout ── */}
            {!compareMode ? (
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">

                {/* Left: configurator */}
                <div className="lg:col-span-3">
                  <ModernCard solid>
                    <ConfigPanel config={config} onChange={cfg => { setConfig(cfg); setActivePreset(null); setInsights([]); }} />
                  </ModernCard>
                </div>

                {/* Right: results (sticky) */}
                <div className="lg:col-span-2 lg:sticky lg:top-28 space-y-4">
                  {apiError && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-xs">
                      Could not reach the prediction API. Check your connection or try again.
                    </div>
                  )}
                  <ModernCard solid>
                    <div className="space-y-5">
                      <GradeDisplay grade={currentGrade} confidence={result?.confidence != null ? parseFloat(result.confidence) : null} loading={loading} />
                      {currentGrade && <GradeScale currentGrade={currentGrade} />}
                    </div>
                  </ModernCard>

                  {result?.proba_distribution?.length > 0 && (
                    <ModernCard solid>
                      <p className="text-slate-400 text-xs mb-3 uppercase tracking-wider">Grade Probabilities</p>
                      <ProbBars proba={result.proba_distribution} currentGrade={currentGrade} />
                    </ModernCard>
                  )}

                  <ModernCard solid>
                    <div className="space-y-2 text-xs text-slate-500">
                      <div className="flex justify-between">
                        <span>Origin distance</span>
                        <span className="text-slate-400 font-mono">{origin1km.toLocaleString()} km</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Material</span>
                        <span className="text-slate-400">{config.material}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Transport</span>
                        <span className="text-slate-400">{config.transport}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Weight</span>
                        <span className="text-slate-400 font-mono">{config.weight} kg</span>
                      </div>
                    </div>
                  </ModernCard>
                </div>
              </div>
            ) : (
              /* ── Compare mode ── */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { cfg: config,  setCfg: c => { setConfig(c); setInsights([]); },  res: result,  load: loading,  label: "Product A" },
                  { cfg: config2, setCfg: setConfig2, res: result2, load: loading2, label: "Product B" },
                ].map(({ cfg, setCfg, res, load, label }) => {
                  const grade = res?.predicted_label;
                  const gcfg = GRADE_CFG[grade];
                  return (
                    <div key={label} className="space-y-4">
                      <div className="flex items-center justify-between">
                        <p className="text-slate-300 font-semibold">{label}</p>
                        {grade && gcfg && (
                          <span className={`text-2xl font-black font-mono ${gcfg.text}`}>{grade}</span>
                        )}
                      </div>
                      <ModernCard solid>
                        <ConfigPanel config={cfg} onChange={setCfg} />
                      </ModernCard>
                      {grade && (
                        <ModernCard solid>
                          <GradeDisplay grade={grade} confidence={res?.confidence != null ? parseFloat(res.confidence) : null} loading={load} />
                          <div className="mt-4">
                            <GradeScale currentGrade={grade} />
                          </div>
                        </ModernCard>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── Insights ── */}
            {!compareMode && (
              <ModernSection title="What would improve this?" icon>
                {insightsLoading ? (
                  <div className="flex items-center gap-3 text-slate-500 text-sm py-4">
                    <div className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
                    Analysing alternatives…
                  </div>
                ) : insights.length > 0 ? (
                  <div className="space-y-2">
                    {insights.map((ins, i) => (
                      <motion.div
                        key={ins.label}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.06 }}
                      >
                        <InsightCard insight={ins} currentGrade={currentGrade} />
                      </motion.div>
                    ))}
                    <p className="text-slate-600 text-xs mt-3 pl-1">
                      Click any insight below to apply it instantly.
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {insights.map(ins => (
                        <motion.button
                          key={ins.label}
                          onClick={() => {
                            setConfig(c => ({ ...c, ...ins.change }));
                            setInsights([]);
                            setActivePreset(null);
                          }}
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs rounded-lg hover:bg-emerald-500/20 transition-all"
                        >
                          <span>{ins.icon}</span>
                          Apply: {ins.label}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                ) : currentGrade && !insightsLoading ? (
                  <ModernCard>
                    <div className="text-center py-4">
                      <span className="text-2xl">🏆</span>
                      <p className="text-emerald-400 font-medium mt-2">
                        {currentGrade === "A+" || currentGrade === "A"
                          ? "This is already near-optimal! Very little room to improve."
                          : "No improvements found with the options tested."}
                      </p>
                    </div>
                  </ModernCard>
                ) : null}
              </ModernSection>
            )}

            {/* ── What the model actually uses ── */}
            <ModernSection>
              <ModernCard>
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <span className="text-2xl flex-shrink-0">ℹ️</span>
                  <div>
                    <h3 className="text-slate-300 font-medium mb-1">How grades are calculated</h3>
                    <p className="text-slate-500 text-sm leading-relaxed">
                      Grades are predicted by an XGBoost classifier trained on 50,000+ products.
                      It uses material type, transport mode, origin distance, weight and recyclability as inputs.
                      <strong className="text-slate-400"> Transport mode and origin distance are the biggest factors</strong> — air freight
                      from far away almost always results in a D or below, regardless of material.
                      These grades indicate relative environmental impact — not an absolute CO₂ measurement.
                    </p>
                  </div>
                </div>
              </ModernCard>
            </ModernSection>

          </div>
        ),
      }}
    </ModernLayout>
  );
}
