import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ModernBadge } from "./ModernLayout";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const GRADE_STYLES = {
  "A+": { badge: "success",  glow: "border-emerald-500/40", label: "text-emerald-400" },
  "A":  { badge: "success",  glow: "border-green-500/40",   label: "text-green-400"   },
  "B":  { badge: "info",     glow: "border-cyan-500/40",    label: "text-cyan-400"    },
  "C":  { badge: "warning",  glow: "border-yellow-500/40",  label: "text-yellow-400"  },
  "D":  { badge: "warning",  glow: "border-amber-500/40",   label: "text-amber-400"   },
  "E":  { badge: "error",    glow: "border-orange-500/40",  label: "text-orange-400"  },
  "F":  { badge: "error",    glow: "border-red-500/40",     label: "text-red-400"     },
};

const RECYCLABILITY_VARIANT = { High: "success", Medium: "warning", Low: "error" };

const TRANSPORT_ICONS = { Ship: "🚢", Truck: "🚚", Air: "✈️", Road: "🚚" };

function truncate(str, max = 72) {
  if (!str) return "—";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

function AlternativeCard({ alt, index, currentCo2 }) {
  const style  = GRADE_STYLES[alt.grade] || GRADE_STYLES["F"];
  const saving = currentCo2 && alt.co2_emissions != null
    ? Math.max(0, currentCo2 - alt.co2_emissions)
    : null;
  const savingPct = saving != null && currentCo2 > 0
    ? Math.round((saving / currentCo2) * 100)
    : null;

  return (
    <motion.div
      className={`flex flex-col p-4 rounded-xl bg-slate-900/60 border ${style.glow} border hover:border-opacity-80 transition-all duration-200`}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.07 }}
    >
      {/* Grade + CO₂ */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <ModernBadge variant={style.badge} size="md">
          {alt.grade}
        </ModernBadge>
        {alt.co2_emissions != null && (
          <span className="text-xs font-medium text-slate-400">
            {alt.co2_emissions.toFixed(3)}{" "}
            <span className="text-slate-500">kg CO₂</span>
          </span>
        )}
      </div>

      {/* Title */}
      <p className="text-sm font-medium text-slate-200 leading-snug mb-3 flex-1">
        {truncate(alt.title)}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {alt.material && (
          <span className="px-2 py-0.5 rounded-md text-xs bg-slate-800 border border-slate-700 text-slate-300">
            {alt.material}
          </span>
        )}
        {alt.origin && (
          <span className="px-2 py-0.5 rounded-md text-xs bg-slate-800 border border-slate-700 text-slate-300">
            {TRANSPORT_ICONS[alt.transport] || "📦"} {alt.origin}
          </span>
        )}
        {alt.recyclability && (
          <ModernBadge variant={RECYCLABILITY_VARIANT[alt.recyclability] || "default"} size="sm">
            ♻️ {alt.recyclability}
          </ModernBadge>
        )}
      </div>

      {/* CO₂ saving vs current product */}
      {saving != null && saving > 0 && (
        <div className="mt-auto pt-2 border-t border-slate-700/60">
          <p className="text-xs text-emerald-400 font-medium">
            Saves ~{saving.toFixed(3)} kg CO₂
            {savingPct != null && <span className="text-emerald-500/70 ml-1">({savingPct}% less)</span>}
          </p>
        </div>
      )}
    </motion.div>
  );
}

export default function AlternativeRecommendations({ grade, category, currentCo2 }) {
  const [alternatives, setAlternatives] = useState([]);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);

  useEffect(() => {
    // Only fetch if the grade is D, E or F (recommendation is meaningful)
    const gradeOrder = ["A+", "A", "B", "C", "D", "E", "F"];
    const idx = gradeOrder.indexOf(grade);
    if (idx < 4) return; // A+/A/B/C — no recommendation needed

    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ grade });
    if (category) params.set("category", category);

    fetch(`${BASE_URL}/api/alternatives?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setAlternatives(data.alternatives || []);
      })
      .catch((err) => {
        console.error("Alternatives fetch error:", err);
        setError("Could not load alternatives.");
      })
      .finally(() => setLoading(false));
  }, [grade, category]);

  // Don't render if grade is good or nothing to show
  const gradeOrder = ["A+", "A", "B", "C", "D", "E", "F"];
  if (gradeOrder.indexOf(grade) < 4) return null;
  if (!loading && alternatives.length === 0 && !error) return null;

  return (
    <motion.div
      className="mt-6 p-5 bg-slate-800/40 rounded-xl border border-slate-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
            <span className="text-lg">🌱</span>
          </div>
          <div>
            <h4 className="text-base font-display font-semibold text-slate-200">
              Greener Alternatives
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Similar products with a better eco grade from our dataset
            </p>
          </div>
        </div>
        {!loading && alternatives.length > 0 && (
          <ModernBadge variant="success" size="sm">
            {alternatives.length} found
          </ModernBadge>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center gap-3 py-6 justify-center text-slate-500">
          <div className="w-5 h-5 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin" />
          <span className="text-sm">Searching dataset…</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <p className="text-sm text-red-400 py-4 text-center">{error}</p>
      )}

      {/* Cards grid */}
      {!loading && alternatives.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {alternatives.map((alt, i) => (
            <AlternativeCard
              key={i}
              alt={alt}
              index={i}
              currentCo2={currentCo2}
            />
          ))}
        </div>
      )}

      {/* Footer note */}
      {!loading && alternatives.length > 0 && (
        <p className="mt-4 text-xs text-slate-600 leading-relaxed border-t border-slate-700/50 pt-3">
          Alternatives sourced from our product impact dataset ({">"}50,000 products).
          CO₂ estimates use the same rule-based methodology applied to the scanned product.
          Actual emissions may vary based on retailer, packaging and delivery conditions.
        </p>
      )}
    </motion.div>
  );
}
