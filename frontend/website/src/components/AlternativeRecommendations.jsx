import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ModernBadge } from "./ModernLayout";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const GRADE_STYLES = {
  "A+": { badge: "success", border: "border-emerald-500/40", glow: "hover:border-emerald-500/70" },
  "A":  { badge: "success", border: "border-green-500/40",   glow: "hover:border-green-500/70"   },
  "B":  { badge: "info",    border: "border-cyan-500/40",    glow: "hover:border-cyan-500/70"    },
  "C":  { badge: "warning", border: "border-yellow-500/40",  glow: "hover:border-yellow-500/70"  },
  "D":  { badge: "warning", border: "border-amber-500/40",   glow: "hover:border-amber-500/70"   },
  "E":  { badge: "error",   border: "border-orange-500/40",  glow: "hover:border-orange-500/70"  },
  "F":  { badge: "error",   border: "border-red-500/40",     glow: "hover:border-red-500/70"     },
};

const RECYCLABILITY_VARIANT = { High: "success", Medium: "warning", Low: "error" };
const TRANSPORT_ICONS = { Ship: "🚢", Truck: "🚚", Air: "✈️", Road: "🚚" };

const MATCH_LABELS = {
  keyword:  { text: "Similar product",  color: "text-emerald-400" },
  category: { text: "Same category",    color: "text-cyan-400"    },
  fallback: { text: "Eco-friendly pick", color: "text-amber-400"  },
};

function truncate(str, max = 68) {
  if (!str) return "—";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

function Co2Bar({ altCo2, currentCo2 }) {
  if (!altCo2 || !currentCo2 || currentCo2 <= 0) return null;
  const maxVal = Math.max(altCo2, currentCo2);
  const altPct = Math.round((altCo2 / maxVal) * 100);
  const curPct = 100;
  const saving = Math.max(0, currentCo2 - altCo2);
  const savingPct = Math.round((saving / currentCo2) * 100);

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/60 space-y-2">
      {/* Current */}
      <div className="flex items-center gap-2 text-xs">
        <span className="w-16 text-right text-slate-500 flex-shrink-0">Current</span>
        <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
          <div className="h-full rounded-full bg-red-500/70" style={{ width: `${curPct}%` }} />
        </div>
        <span className="w-14 text-slate-400 flex-shrink-0">{currentCo2.toFixed(3)} kg</span>
      </div>
      {/* Alternative */}
      <div className="flex items-center gap-2 text-xs">
        <span className="w-16 text-right text-emerald-400 flex-shrink-0">This alt.</span>
        <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-emerald-500"
            initial={{ width: 0 }}
            animate={{ width: `${altPct}%` }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          />
        </div>
        <span className="w-14 text-emerald-400 flex-shrink-0">{altCo2.toFixed(3)} kg</span>
      </div>
      {saving > 0 && (
        <p className="text-xs text-emerald-400 font-medium text-right">
          Saves ~{saving.toFixed(3)} kg CO₂
          <span className="text-emerald-500/70 ml-1">({savingPct}% less)</span>
        </p>
      )}
    </div>
  );
}

function AlternativeCard({ alt, index, currentCo2 }) {
  const style = GRADE_STYLES[alt.grade] || GRADE_STYLES["F"];
  const match = MATCH_LABELS[alt.matched_by] || MATCH_LABELS.fallback;

  return (
    <motion.div
      className={`flex flex-col p-4 rounded-xl bg-slate-900/60 border ${style.border} ${style.glow} transition-colors duration-200`}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      {/* Grade + match type */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <ModernBadge variant={style.badge} size="md">{alt.grade}</ModernBadge>
        <span className={`text-xs font-medium ${match.color}`}>{match.text}</span>
      </div>

      {/* Title */}
      <p className="text-sm font-medium text-slate-200 leading-snug mb-3 flex-1">
        {truncate(alt.title)}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5">
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

      {/* CO₂ comparison bar */}
      <Co2Bar altCo2={alt.co2_emissions} currentCo2={currentCo2} />
    </motion.div>
  );
}

const GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"];

export default function AlternativeRecommendations({ grade, category, currentCo2, productTitle }) {
  const [alternatives, setAlternatives] = useState([]);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);

  useEffect(() => {
    const idx = GRADE_ORDER.indexOf(grade);
    if (idx < 4) return; // Only show for D / E / F

    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ grade });
    if (productTitle) params.set("title", productTitle);
    if (category)     params.set("category", category);

    fetch(`${BASE_URL}/api/alternatives?${params}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data) => setAlternatives(data.alternatives || []))
      .catch((err) => { console.error("Alternatives fetch error:", err); setError("Could not load alternatives."); })
      .finally(() => setLoading(false));
  }, [grade, category, productTitle]);

  if (GRADE_ORDER.indexOf(grade) < 4) return null;
  if (!loading && alternatives.length === 0 && !error) return null;

  const keywordsUsed = alternatives[0]?.keywords_used;

  return (
    <motion.div
      className="mt-6 p-5 bg-slate-800/40 rounded-xl border border-slate-700/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5 gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center flex-shrink-0">
            <span className="text-lg">🌱</span>
          </div>
          <div>
            <h4 className="text-base font-display font-semibold text-slate-200">
              Greener Alternatives
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              {keywordsUsed?.length
                ? `Matched on: ${keywordsUsed.join(", ")}`
                : "Similar products with a better eco grade"}
            </p>
          </div>
        </div>
        {!loading && alternatives.length > 0 && (
          <ModernBadge variant="success" size="sm">{alternatives.length} found</ModernBadge>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center gap-3 py-6 justify-center text-slate-500">
          <div className="w-5 h-5 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin" />
          <span className="text-sm">Searching dataset…</span>
        </div>
      )}

      {/* Error */}
      {error && <p className="text-sm text-red-400 py-4 text-center">{error}</p>}

      {/* Cards */}
      {!loading && alternatives.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {alternatives.map((alt, i) => (
            <AlternativeCard key={i} alt={alt} index={i} currentCo2={currentCo2} />
          ))}
        </div>
      )}

      {/* Footer */}
      {!loading && alternatives.length > 0 && (
        <p className="mt-4 text-xs text-slate-600 leading-relaxed border-t border-slate-700/50 pt-3">
          Alternatives sourced from our product impact dataset ({">"}50,000 products).
          Each result is one grade level better, giving a realistic improvement pathway.
          CO₂ estimates use the same rule-based methodology; actual emissions vary by retailer and delivery.
        </p>
      )}
    </motion.div>
  );
}
