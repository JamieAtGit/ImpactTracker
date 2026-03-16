import React, { useState } from "react";
import { motion } from "framer-motion";

const steps = [
  {
    id: "input",
    icon: "🔗",
    label: "User Input",
    sublabel: "Amazon URL + UK Postcode",
    color: "from-cyan-500 to-blue-500",
    border: "border-cyan-500/40",
    bg: "bg-cyan-500/10",
    detail: "User submits an Amazon product URL and optional delivery postcode via the React frontend.",
  },
  {
    id: "scraper",
    icon: "🕷️",
    label: "Requests Scraper",
    sublabel: "Python + BeautifulSoup",
    color: "from-blue-500 to-indigo-500",
    border: "border-blue-500/40",
    bg: "bg-blue-500/10",
    detail: "Amazon product page scraped using rotating user-agents. Extracts title, weight, dimensions, country of origin (Unicode-aware), material type from title-first detection, and brand.",
  },
  {
    id: "features",
    icon: "⚙️",
    label: "Feature Extraction",
    sublabel: "11-dimensional vector",
    color: "from-indigo-500 to-purple-500",
    border: "border-indigo-500/40",
    bg: "bg-indigo-500/10",
    detail: "Builds feature vector: material, transport_mode, recyclability, origin_country, weight_log, weight_bin, packaging_type, size_category, quality_level, pack_size, material_confidence. Origin-to-UK distance calculated via Haversine formula.",
  },
  {
    id: "models",
    icon: "🧠",
    label: "Dual Calculation",
    sublabel: "ML + Rule-Based",
    color: "from-purple-500 to-pink-500",
    border: "border-purple-500/40",
    bg: "bg-purple-500/10",
    detail: "XGBoost model predicts eco grade from the feature vector. Rule-based DEFRA calculation independently computes CO₂: (weight × emission_factor × distance) ÷ 1000 + (weight × material_intensity). Both grades are returned for comparison.",
  },
  {
    id: "api",
    icon: "🚀",
    label: "Flask REST API",
    sublabel: "Railway / Gunicorn",
    color: "from-pink-500 to-rose-500",
    border: "border-pink-500/40",
    bg: "bg-pink-500/10",
    detail: "Flask app served via Gunicorn gthread workers on Railway. Returns structured JSON with 30+ fields: eco scores, CO₂ kg, recyclability %, transport details, confidence levels, and methodology comparison.",
  },
  {
    id: "frontend",
    icon: "🖥️",
    label: "React Dashboard",
    sublabel: "Netlify / Vite + Tailwind",
    color: "from-rose-500 to-orange-500",
    border: "border-rose-500/40",
    bg: "bg-rose-500/10",
    detail: "React frontend renders impact metrics, CO₂ visualisations, methodology comparison chart, and recyclability data. Deployed on Netlify with Vite build tooling.",
  },
  {
    id: "db",
    icon: "🗄️",
    label: "PostgreSQL Database",
    sublabel: "50,000+ products",
    color: "from-orange-500 to-amber-500",
    border: "border-orange-500/40",
    bg: "bg-orange-500/10",
    detail: "Every analysed product is persisted to PostgreSQL on Railway. Tables: Products (50K seed + live), ScrapedProducts, EmissionCalculations. Powers the analytics dashboard and model training data.",
  },
];

const Arrow = () => (
  <div className="hidden md:flex items-center justify-center px-1 flex-shrink-0">
    <motion.div
      className="text-slate-500 text-xl"
      animate={{ x: [0, 4, 0] }}
      transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
    >
      →
    </motion.div>
  </div>
);

export default function SystemArchitectureDiagram() {
  const [activeStep, setActiveStep] = useState(null);

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-400 text-center">
        Click any component to see implementation details
      </p>

      {/* Pipeline Flow */}
      <div className="flex flex-col md:flex-row items-stretch gap-0 md:gap-0 overflow-x-auto pb-2">
        {steps.map((step, i) => (
          <React.Fragment key={step.id}>
            <motion.div
              className={`flex-1 min-w-[120px] cursor-pointer rounded-xl border p-4 text-center transition-all ${step.border} ${step.bg} ${
                activeStep === step.id ? "ring-2 ring-cyan-400/60 scale-105" : "hover:scale-102"
              }`}
              onClick={() => setActiveStep(activeStep === step.id ? null : step.id)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
            >
              <div className="text-2xl mb-2">{step.icon}</div>
              <div className={`text-xs font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent leading-tight`}>
                {step.label}
              </div>
              <div className="text-xs text-slate-500 mt-1 leading-tight">{step.sublabel}</div>
            </motion.div>
            {i < steps.length - 1 && <Arrow />}
          </React.Fragment>
        ))}
      </div>

      {/* Detail Panel */}
      {activeStep && (() => {
        const step = steps.find(s => s.id === activeStep);
        return (
          <motion.div
            className={`rounded-xl border p-5 ${step.border} ${step.bg}`}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{step.icon}</span>
              <div>
                <h5 className={`font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                  {step.label}
                </h5>
                <span className="text-xs text-slate-500">{step.sublabel}</span>
              </div>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{step.detail}</p>
          </motion.div>
        );
      })()}

      {/* Data flow summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-2">Scraping Layer</p>
          <ul className="text-xs text-slate-300 space-y-1">
            <li>→ Rotating user-agents (anti-block)</li>
            <li>→ Unicode \u200e origin parsing</li>
            <li>→ Title-first material detection</li>
            <li>→ Brand → country lookup (10K+ brands)</li>
          </ul>
        </div>
        <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-2">ML Layer</p>
          <ul className="text-xs text-slate-300 space-y-1">
            <li>→ XGBoost classifier (11 features)</li>
            <li>→ Label encoders per categorical</li>
            <li>→ predict_proba for confidence</li>
            <li>→ Fallback to rule-based if model absent</li>
          </ul>
        </div>
        <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/50">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-2">Data Layer</p>
          <ul className="text-xs text-slate-300 space-y-1">
            <li>→ PostgreSQL via SQLAlchemy ORM</li>
            <li>→ 50,000 product seed dataset</li>
            <li>→ Live appends on each prediction</li>
            <li>→ Analytics dashboard aggregations</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
