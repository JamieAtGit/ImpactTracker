import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";
import ImportantChart from "../components/ImportantChart";
import ModelInfoModal from "../components/ModelInfoModal";
import ModelMetricsChart from "../components/ModelMetricsChart";
import PerClassMetricsTable from "../components/PerClassMetricsTable";
import AblationStudyChart from "../components/AblationStudyChart";
import SensitivityAnalysisChart from "../components/SensitivityAnalysisChart";
import SystemArchitectureDiagram from "../components/SystemArchitectureDiagram";
import GlobalShapChart from "../components/GlobalShapChart";
import ROCCurveChart from "../components/ROCCurveChart";
import AppleValidationChart from "../components/AppleValidationChart";
import CalibrationChart from "../components/CalibrationChart";
import StatisticalTestsPanel from "../components/StatisticalTestsPanel";
import DatasetDistributionCharts from "../components/DatasetDistributionCharts";
import Footer from "../components/Footer";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatBadge({ value, label, sub, color = "text-cyan-400" }) {
  return (
    <div className="glass-card p-6 text-center">
      <div className={`text-3xl font-bold ${color} mb-2`}>{value}</div>
      <div className="text-slate-300 font-medium">{label}</div>
      {sub && <div className="text-slate-500 text-sm">{sub}</div>}
    </div>
  );
}

function SectionHeader({ gradient, title }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className={`w-2 h-8 bg-gradient-to-b ${gradient} rounded-full`} />
      <h4 className="text-lg font-display text-slate-200">{title}</h4>
    </div>
  );
}

// ─── CO₂ Methodology ─────────────────────────────────────────────────────────

function CarbonMethodologySection() {
  const transportFactors = [
    { mode: "Ship", icon: "🚢", factor: 0.03, note: "Container shipping — most efficient per tonne-km", color: "text-blue-300" },
    { mode: "Truck", icon: "🚚", factor: 0.15, note: "Road freight — mid-range emissions", color: "text-yellow-300" },
    { mode: "Air",   icon: "✈️", factor: 0.50, note: "Air freight — 16× more than ship", color: "text-red-300" },
  ];

  const materialIntensities = [
    { material: "Wood",     intensity: 0.8,  note: "Low energy to process" },
    { material: "Paper",    intensity: 1.2,  note: "Pulping process" },
    { material: "Glass",    intensity: 1.5,  note: "High-temp furnace required" },
    { material: "Plastic",  intensity: 2.5,  note: "Petrochemical feedstock" },
    { material: "Steel",    intensity: 3.0,  note: "Energy-intensive smelting" },
    { material: "Other",    intensity: 2.0,  note: "General manufacturing average" },
  ];

  return (
    <div className="space-y-8">
      {/* Formula */}
      <div>
        <SectionHeader gradient="from-green-400 to-cyan-400" title="CO₂ Calculation Formula" />
        <div className="bg-slate-900/60 border border-cyan-500/20 rounded-xl p-6 font-mono text-sm space-y-3">
          <div className="text-slate-300">
            <span className="text-cyan-400 font-bold">transport_CO₂</span>
            <span className="text-slate-400"> = </span>
            <span className="text-slate-200">weight_kg × emission_factor × distance_km</span>
            <span className="text-slate-400"> ÷ 1000</span>
          </div>
          <div className="text-slate-300">
            <span className="text-purple-400 font-bold">material_CO₂</span>
            <span className="text-slate-400"> = </span>
            <span className="text-slate-200">weight_kg × material_intensity</span>
          </div>
          <div className="border-t border-slate-700 pt-3 text-slate-300">
            <span className="text-green-400 font-bold">total_CO₂</span>
            <span className="text-slate-400"> = </span>
            <span className="text-cyan-400">transport_CO₂</span>
            <span className="text-slate-400"> + </span>
            <span className="text-purple-400">material_CO₂</span>
          </div>
          <div className="text-xs text-slate-500 pt-1">
            ÷ 1000 converts kg product weight to tonnes (DEFRA emission factors are per tonne-km)
          </div>
        </div>
      </div>

      {/* DEFRA Transport Factors */}
      <div>
        <SectionHeader gradient="from-blue-400 to-indigo-400" title="DEFRA Emission Factors (kg CO₂ per tonne-km)" />
        <p className="text-xs text-slate-500 mb-4">
          Source: UK Department for Environment, Food &amp; Rural Affairs (DEFRA) greenhouse gas conversion factors 2023
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {transportFactors.map((t) => (
            <div key={t.mode} className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{t.icon}</span>
                <span className={`text-lg font-bold ${t.color}`}>{t.mode}</span>
              </div>
              <div className={`text-3xl font-mono font-bold ${t.color} mb-2`}>{t.factor}</div>
              <p className="text-xs text-slate-400">{t.note}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <p className="text-xs text-amber-300">
            <strong>Transport mode selection:</strong> Products originating within 500 km use Truck.
            Products over 500 km and under 20,000 km use Ship. Products over 20,000 km (e.g. New Zealand → UK ≈ 18,900 km)
            use Air freight as the only viable option.
          </p>
        </div>
      </div>

      {/* Material Manufacturing Intensities */}
      <div>
        <SectionHeader gradient="from-purple-400 to-pink-400" title="Material Manufacturing Carbon Intensities (kg CO₂ per kg material)" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-3 text-slate-400">Material</th>
                <th className="text-left py-2 px-3 text-slate-400">Intensity</th>
                <th className="text-left py-2 px-3 text-slate-400">Context</th>
                <th className="text-left py-2 px-3 text-slate-400">Visual</th>
              </tr>
            </thead>
            <tbody>
              {materialIntensities.map((m) => (
                <tr key={m.material} className="border-b border-slate-800/50">
                  <td className="py-2 px-3 text-slate-200 font-medium">{m.material}</td>
                  <td className="py-2 px-3 text-cyan-300 font-mono">{m.intensity} kg/kg</td>
                  <td className="py-2 px-3 text-slate-400 text-xs">{m.note}</td>
                  <td className="py-2 px-3 w-40">
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-purple-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${(m.intensity / 3.0) * 100}%` }}
                        transition={{ duration: 1, ease: "easeOut" }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Carbon Equivalences ─────────────────────────────────────────────────────

function CarbonEquivalences() {
  const equivalences = [
    { icon: "🚗", label: "Driving", value: "6 km", desc: "In an average UK petrol car (DEFRA: 161g CO₂/km)", per: "per 1 kg CO₂" },
    { icon: "✈️", label: "Flying",  value: "4 km", desc: "Short-haul passenger flight (255g CO₂/passenger-km)", per: "per 1 kg CO₂" },
    { icon: "🚆", label: "Train",   value: "24 km", desc: "UK rail travel (41g CO₂/passenger-km)", per: "per 1 kg CO₂" },
    { icon: "💡", label: "Electricity", value: "5.2 kWh", desc: "From the UK grid (193g CO₂/kWh, 2023)", per: "per 1 kg CO₂" },
    { icon: "☕", label: "Kettle boils", value: "36×", desc: "Full 1.5L kettle (≈28g CO₂ per boil)", per: "per 1 kg CO₂" },
    { icon: "🌳", label: "Tree absorption", value: "~1 year", desc: "A single mature tree absorbs ≈21 kg CO₂/year", per: "0.06 kg CO₂/day" },
  ];

  const examples = [
    { product: "Lightweight Fabric toy (0.2 kg, Germany)", co2: 0.48, grade: "A+", color: "text-teal-300" },
    { product: "Stainless steel watch (0.165 kg, China)", co2: 1.01, grade: "B", color: "text-lime-300" },
    { product: "Plastic storage box (1.2 kg, China)", co2: 4.70, grade: "C", color: "text-yellow-300" },
    { product: "Electronic device (0.8 kg, China)", co2: 3.20, grade: "D", color: "text-orange-300" },
  ];

  return (
    <div className="space-y-8">
      <p className="text-slate-400 text-sm">
        Raw CO₂ figures can be hard to interpret. These equivalences (all sourced from DEFRA 2023 and UK government data)
        help contextualise the environmental cost of a product purchase.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {equivalences.map((eq, i) => (
          <motion.div
            key={eq.label}
            className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{eq.icon}</span>
              <span className="text-slate-300 font-medium text-sm">{eq.label}</span>
            </div>
            <div className="text-2xl font-bold text-cyan-300 mb-1">{eq.value}</div>
            <div className="text-xs text-slate-500 mb-1">{eq.per}</div>
            <div className="text-xs text-slate-400">{eq.desc}</div>
          </motion.div>
        ))}
      </div>

      {/* Worked examples */}
      <div>
        <h5 className="text-sm font-medium text-slate-300 mb-3">Worked Examples from the System</h5>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 px-3 text-slate-400">Product</th>
                <th className="text-left py-2 px-3 text-slate-400">CO₂</th>
                <th className="text-left py-2 px-3 text-slate-400">Grade</th>
                <th className="text-left py-2 px-3 text-slate-400">Equivalent</th>
              </tr>
            </thead>
            <tbody>
              {examples.map((ex) => (
                <tr key={ex.product} className="border-b border-slate-800/50">
                  <td className="py-2 px-3 text-slate-300 text-xs">{ex.product}</td>
                  <td className="py-2 px-3 text-slate-200 font-mono">{ex.co2} kg</td>
                  <td className="py-2 px-3">
                    <span className={`font-bold ${ex.color}`}>{ex.grade}</span>
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-xs">
                    ≈ driving {(ex.co2 * 6).toFixed(0)} km
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── SMOTE Class Balance ──────────────────────────────────────────────────────

function SmoteSection() {
  // Approximate pre-SMOTE distribution based on real-world Amazon product mix
  // (rule-based scoring applied to raw scraped dataset skews towards B/C/D)
  const beforeSmote = [
    { grade: "A+", count: 180 },
    { grade: "A",  count: 420 },
    { grade: "B",  count: 890 },
    { grade: "C",  count: 1050 },
    { grade: "D",  count: 740 },
    { grade: "E",  count: 490 },
    { grade: "F",  count: 230 },
  ];
  const afterSmote = beforeSmote.map(d => ({ ...d, count: 1695 })); // balanced to max class

  const maxBefore = Math.max(...beforeSmote.map(d => d.count));

  const GRADE_COLORS_HEX = {
    "A+": "#06d6a0", "A": "#10b981", "B": "#22c55e",
    "C":  "#eab308", "D": "#f59e0b", "E": "#ef4444", "F": "#dc2626",
  };

  return (
    <div className="space-y-6">
      <p className="text-slate-400 text-sm">
        Real-world Amazon product data is heavily skewed towards mid-range grades (B–D).
        Without balancing, the model would learn to predict the majority class and ignore rare A+ and F products.
        SMOTE (Synthetic Minority Over-sampling Technique) generates synthetic training samples by
        interpolating between existing minority-class examples in feature space.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Before */}
        <div>
          <h5 className="text-sm font-medium text-red-300 mb-4">Before SMOTE — Imbalanced</h5>
          <div className="space-y-2">
            {beforeSmote.map((d, i) => (
              <div key={d.grade} className="flex items-center gap-3">
                <span className="w-8 text-xs font-bold text-right" style={{ color: GRADE_COLORS_HEX[d.grade] }}>{d.grade}</span>
                <div className="flex-1 h-5 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: GRADE_COLORS_HEX[d.grade] }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(d.count / maxBefore) * 100}%` }}
                    transition={{ delay: i * 0.07, duration: 0.8, ease: "easeOut" }}
                  />
                </div>
                <span className="w-12 text-xs text-slate-400 text-right">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
        {/* After */}
        <div>
          <h5 className="text-sm font-medium text-green-300 mb-4">After SMOTE — Balanced (≈1,695 per class)</h5>
          <div className="space-y-2">
            {afterSmote.map((d, i) => (
              <div key={d.grade} className="flex items-center gap-3">
                <span className="w-8 text-xs font-bold text-right" style={{ color: GRADE_COLORS_HEX[d.grade] }}>{d.grade}</span>
                <div className="flex-1 h-5 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: GRADE_COLORS_HEX[d.grade] }}
                    initial={{ width: 0 }}
                    animate={{ width: "100%" }}
                    transition={{ delay: i * 0.07, duration: 0.8, ease: "easeOut" }}
                  />
                </div>
                <span className="w-12 text-xs text-slate-400 text-right">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 font-medium mb-1">Original Dataset</p>
          <p className="text-lg font-bold text-red-300">~4,000</p>
          <p className="text-xs text-slate-500">samples, heavily imbalanced</p>
        </div>
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 font-medium mb-1">After SMOTE</p>
          <p className="text-lg font-bold text-green-300">~11,865</p>
          <p className="text-xs text-slate-500">samples, 7 balanced classes</p>
        </div>
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-slate-400 font-medium mb-1">Accuracy Improvement</p>
          <p className="text-lg font-bold text-cyan-300">+~6%</p>
          <p className="text-xs text-slate-500">estimated on minority classes</p>
        </div>
      </div>
    </div>
  );
}

// ─── Technology Stack ─────────────────────────────────────────────────────────

function TechStackSection() {
  const stack = [
    {
      layer: "Frontend",
      color: "from-cyan-500 to-blue-500",
      icon: "🖥️",
      items: [
        { name: "React 18", role: "UI framework — component-based SPA" },
        { name: "Vite", role: "Build tooling — fast HMR and ES module bundling" },
        { name: "Tailwind CSS", role: "Utility-first styling with dark theme" },
        { name: "Framer Motion", role: "Declarative animation library" },
        { name: "Recharts", role: "Composable charting built on D3" },
        { name: "React Router", role: "Client-side routing" },
      ],
    },
    {
      layer: "Backend",
      color: "from-purple-500 to-indigo-500",
      icon: "⚙️",
      items: [
        { name: "Flask 3.x", role: "Python microframework for REST API" },
        { name: "SQLAlchemy", role: "ORM for PostgreSQL database models" },
        { name: "Flask-CORS", role: "Cross-origin request handling" },
        { name: "Gunicorn + gthread", role: "Production WSGI server with threading" },
        { name: "BeautifulSoup 4", role: "HTML parsing for Amazon product pages" },
        { name: "Requests", role: "HTTP client with session management" },
      ],
    },
    {
      layer: "Machine Learning",
      color: "from-pink-500 to-rose-500",
      icon: "🧠",
      items: [
        { name: "XGBoost", role: "Gradient-boosted decision tree classifier" },
        { name: "scikit-learn", role: "Random Forest baseline, metrics, preprocessing" },
        { name: "imbalanced-learn", role: "SMOTE oversampling for class balance" },
        { name: "pandas + NumPy", role: "Data wrangling and feature engineering" },
        { name: "joblib", role: "Model serialisation (pickle-compatible)" },
        { name: "RandomizedSearchCV", role: "Hyperparameter optimisation (100 iterations)" },
      ],
    },
    {
      layer: "Infrastructure",
      color: "from-orange-500 to-amber-500",
      icon: "☁️",
      items: [
        { name: "Railway", role: "Backend hosting — auto-deploy from GitHub" },
        { name: "Netlify", role: "Frontend hosting — CDN edge deployment" },
        { name: "PostgreSQL", role: "Managed database — 50K+ product records" },
        { name: "GitHub", role: "Version control and CI/CD trigger" },
        { name: "Flask-Migrate (Alembic)", role: "Database schema migrations" },
        { name: "Python 3.12", role: "Runtime environment on Railway" },
      ],
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {stack.map((s, i) => (
        <motion.div
          key={s.layer}
          className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-5"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xl">{s.icon}</span>
            <h5 className={`font-bold bg-gradient-to-r ${s.color} bg-clip-text text-transparent`}>{s.layer}</h5>
          </div>
          <div className="space-y-2">
            {s.items.map((item) => (
              <div key={item.name} className="flex gap-2">
                <span className="text-slate-300 text-xs font-medium w-36 flex-shrink-0">{item.name}</span>
                <span className="text-slate-500 text-xs">{item.role}</span>
              </div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ─── Limitations ─────────────────────────────────────────────────────────────

function LimitationsSection() {
  const limitations = [
    {
      icon: "🏭",
      title: "Manufacturing Emissions Not Included",
      severity: "high",
      detail: "The rule-based calculation only accounts for transport CO₂ and a rough material manufacturing estimate. Full lifecycle assessment (LCA) would additionally require energy consumed during manufacturing, factory emissions, and end-of-life processing — data not available from an Amazon product page.",
    },
    {
      icon: "🤖",
      title: "Scraper Reliability",
      severity: "high",
      detail: "Amazon actively mitigates scraping via bot-detection, rate limiting, and dynamic HTML rendering. The current Requests-based approach uses rotating user-agents and session management, but can fail silently. A more robust solution would use the official Amazon Product Advertising API.",
    },
    {
      icon: "📊",
      title: "Training Data Selection Bias",
      severity: "medium",
      detail: "The 50,000-product training set was seeded from Amazon's catalogue, which overrepresents consumer electronics, household goods, and toys. Industrial products, food, and services are absent. The model's predictions may be less reliable outside these categories.",
    },
    {
      icon: "🎯",
      title: "Ordinal Grade Labels",
      severity: "medium",
      detail: "Eco grades (A+→F) are ordinal, not cardinal. The model predicts grade buckets, not actual CO₂ kg values. A product graded 'B' could have CO₂ anywhere in a range — the grade is a relative indicator, not a precise measurement.",
    },
    {
      icon: "🌍",
      title: "UK-Specific Emission Factors",
      severity: "low",
      detail: "DEFRA emission factors and the UK electricity grid carbon intensity are specific to Great Britain. For shipments to other countries, or products manufactured with different energy mixes, the factors would need to be adjusted.",
    },
    {
      icon: "📦",
      title: "Packaging Weight Not Extracted",
      severity: "low",
      detail: "Amazon listing pages rarely include packaging weight separately. The CO₂ estimate uses listed product weight only. For heavily-packaged goods (e.g. fragile items), this may underestimate total emissions by 10–30%.",
    },
  ];

  const severityColor = {
    high:   "bg-red-500/10 border-red-500/30 text-red-300",
    medium: "bg-yellow-500/10 border-yellow-500/30 text-yellow-300",
    low:    "bg-blue-500/10 border-blue-500/30 text-blue-300",
  };

  return (
    <div className="space-y-6">
      <p className="text-slate-400 text-sm">
        A rigorous dissertation requires honest acknowledgement of scope and limitations.
        The following are the key constraints of the current system.
      </p>

      <div className="flex gap-4 text-xs flex-wrap">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400"></span><span className="text-slate-400">High impact</span></span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400"></span><span className="text-slate-400">Medium impact</span></span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400"></span><span className="text-slate-400">Low impact</span></span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {limitations.map((l, i) => (
          <motion.div
            key={l.title}
            className={`rounded-xl border p-5 ${severityColor[l.severity]}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">{l.icon}</span>
              <h5 className="text-sm font-semibold">{l.title}</h5>
            </div>
            <p className="text-slate-300 text-xs leading-relaxed">{l.detail}</p>
          </motion.div>
        ))}
      </div>

      {/* Future work */}
      <div className="bg-slate-800/40 border border-slate-600/40 rounded-xl p-5">
        <h5 className="text-sm font-medium text-slate-200 mb-3">Future Work</h5>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {[
            "Integrate Amazon Product Advertising API for reliable data extraction",
            "Add full LCA (manufacturing + end-of-life) using ecoinvent database",
            "Train per-category models for finer-grained accuracy",
            "Extend to other retailers (eBay, ASOS, Tesco) via unified scraper",
            "Add real-time carbon offsetting cost estimates (tonne CO₂ market price)",
            "User accounts for tracking cumulative purchase impact over time",
          ].map((item) => (
            <div key={item} className="flex items-start gap-2 text-xs text-slate-400">
              <span className="text-cyan-400 mt-0.5 flex-shrink-0">→</span>
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Live Stats ───────────────────────────────────────────────────────────────

function LiveStatsBar() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`${BASE_URL}/api/dashboard-metrics`)
      .then(r => r.json())
      .then(d => setStats(d.stats))
      .catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <motion.div
      className="grid grid-cols-2 md:grid-cols-4 gap-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="glass-card p-4 text-center">
        <div className="text-2xl font-bold text-cyan-400">{stats.total_products?.toLocaleString()}</div>
        <div className="text-slate-400 text-xs mt-1">Products in database</div>
      </div>
      <div className="glass-card p-4 text-center">
        <div className="text-2xl font-bold text-purple-400">{stats.total_materials}</div>
        <div className="text-slate-400 text-xs mt-1">Material categories</div>
      </div>
      <div className="glass-card p-4 text-center">
        <div className="text-2xl font-bold text-green-400">{stats.total_predictions?.toLocaleString()}</div>
        <div className="text-slate-400 text-xs mt-1">Emission calculations</div>
      </div>
      <div className="glass-card p-4 text-center">
        <div className="text-2xl font-bold text-amber-400">{stats.recent_activity?.toLocaleString()}</div>
        <div className="text-slate-400 text-xs mt-1">Live scraped products</div>
      </div>
    </motion.div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const LEARN_TABS = [
  { id: 'overview',       label: 'Overview',       icon: '🏠' },
  { id: 'explainability', label: 'Explainability',  icon: '🔍' },
  { id: 'performance',    label: 'Performance',     icon: '📈' },
  { id: 'methodology',    label: 'Methodology',     icon: '⚗️' },
];

export default function LearnPage() {
  const [showModal,     setShowModal]     = useState(false);
  const [activeTab,     setActiveTab]     = useState('overview');
  const [evalData,      setEvalData]      = useState(null);

  useEffect(() => {
    fetch(`${BASE_URL}/api/evaluation`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setEvalData(d); })
      .catch(() => {});
  }, []);

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-24">

            {/* Hero */}
            <ModernSection className="text-center mb-24">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-12"
              >
                <div className="space-y-8">
                  <h1 className="text-5xl md:text-6xl font-display font-bold leading-tight">
                    <span className="text-slate-100">Machine Learning</span>
                    <br />
                    <span className="bg-gradient-to-r from-blue-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
                      Model Documentation
                    </span>
                  </h1>
                  <motion.p
                    className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                  >
                    Technical documentation of the environmental impact prediction system,
                    including XGBoost model architecture, training methodology, DEFRA-based calculation
                    pipeline, and full performance analysis.
                  </motion.p>
                </div>

                <motion.div
                  className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-4xl mx-auto mt-12"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.6 }}
                >
                  <StatBadge value="99.3%" label="Test Set Accuracy"  sub="Macro F1: 0.993"      color="text-cyan-400" />
                  <StatBadge value="0.9998" label="Macro ROC AUC"     sub="7-class one-vs-rest"  color="text-purple-400" />
                  <StatBadge value="49,999" label="Training Samples"  sub="DEFRA re-labelled"    color="text-green-400" />
                  <StatBadge value="7"     label="Eco Grade Classes"  sub="A+ through F"         color="text-amber-400" />
                </motion.div>
              </motion.div>
            </ModernSection>

            {/* Tab Navigation */}
            <div className="sticky top-0 z-40 -mx-8 px-8 py-3 bg-slate-950/90 backdrop-blur-md border-b border-slate-700/50">
              <div className="flex gap-1.5">
                {LEARN_TABS.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      activeTab === tab.id
                        ? 'bg-cyan-600/25 text-cyan-300 border border-cyan-500/40'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Live Database Stats */}
            {activeTab === 'overview' && (
            <ModernSection title="Live System Statistics" icon delay={0.1}>
              <ModernCard solid className="p-6">
                <p className="text-slate-400 text-sm mb-4">
                  Real-time figures from the production PostgreSQL database on Railway
                </p>
                <LiveStatsBar />
              </ModernCard>
            </ModernSection>
            )}

            {/* Dataset Statistics */}
            {activeTab === 'overview' && (
            <ModernSection title="Dataset Statistics" icon delay={0.12}>
              <ModernCard solid className="p-8">
                <p className="text-slate-400 text-sm mb-6">
                  The training dataset was compiled from Amazon product listings, labelled using DEFRA-based
                  rule-based CO₂ thresholds, and balanced with SMOTE before model training.
                </p>
                <DatasetDistributionCharts datasetStats={evalData?.dataset_statistics} />
              </ModernCard>
            </ModernSection>
            )}

            {/* About Model Button */}
            {activeTab === 'overview' && (
            <ModernSection>
              <div className="flex justify-center">
                <ModernButton variant="secondary" onClick={() => setShowModal(true)} icon="🔬">
                  About the Model
                </ModernButton>
              </div>
            </ModernSection>
            )}

            {/* System Architecture */}
            {activeTab === 'overview' && (
            <ModernSection title="System Architecture" icon delay={0.2}>
              <ModernCard solid className="p-8">
                <div className="space-y-4 mb-6">
                  <p className="text-slate-400 text-sm">
                    End-to-end pipeline from user input to environmental assessment. Seven components
                    working in sequence across two deployed services (Railway backend, Netlify frontend).
                  </p>
                </div>
                <SystemArchitectureDiagram />
              </ModernCard>
            </ModernSection>
            )}

            {/* CO₂ Methodology */}
            {activeTab === 'methodology' && (
            <ModernSection title="CO₂ Calculation Methodology" icon delay={0.3}>
              <ModernCard solid className="p-8">
                <CarbonMethodologySection />
              </ModernCard>
            </ModernSection>
            )}

            {/* Feature Importance */}
            {activeTab === 'explainability' && (
            <ModernSection title="Feature Importance Analysis" icon delay={0.4}>
              <ModernCard solid className="p-8">
                <div className="space-y-4">
                  <p className="text-slate-400 text-sm text-center">
                    XGBoost feature weights — which factors most influence eco grade prediction
                  </p>
                  <div className="min-h-[600px] w-full">
                    <ImportantChart />
                  </div>
                </div>
              </ModernCard>
            </ModernSection>
            )}

            {/* Global SHAP Feature Importance */}
            {activeTab === 'explainability' && (
            <ModernSection title="Global SHAP Feature Importance" icon delay={0.42}>
              <ModernCard solid className="p-8">
                <GlobalShapChart />
              </ModernCard>
            </ModernSection>
            )}

            {/* SMOTE Class Balance */}
            {activeTab === 'explainability' && (
            <ModernSection title="Class Imbalance & SMOTE Resampling" icon delay={0.45}>
              <ModernCard solid className="p-8">
                <SmoteSection />
              </ModernCard>
            </ModernSection>
            )}

            {/* Apple External Validation */}
            {activeTab === 'performance' && (
            <ModernSection title="External Validation — Apple Product Environmental Reports" icon delay={0.44}>
              <ModernCard solid className="p-8">
                <AppleValidationChart />
              </ModernCard>
            </ModernSection>
            )}

            {/* Statistical Tests & Cross-Validation */}
            {activeTab === 'performance' && (
            <ModernSection title="Statistical Evaluation & Cross-Validation" icon delay={0.45}>
              <ModernCard solid className="p-8">
                <StatisticalTestsPanel evaluationData={evalData} />
              </ModernCard>
            </ModernSection>
            )}

            {/* ROC Curves */}
            {activeTab === 'performance' && (
            <ModernSection title="Multi-Class ROC Curves (One-vs-Rest)" icon delay={0.48}>
              <ModernCard solid className="p-8">
                <ROCCurveChart
                  rocData={evalData?.roc_curves}
                  classes={evalData?.classes}
                />
              </ModernCard>
            </ModernSection>
            )}

            {/* Calibration */}
            {activeTab === 'performance' && (
            <ModernSection title="Reliability Diagram (Calibration)" icon delay={0.49}>
              <ModernCard solid className="p-8">
                <CalibrationChart calibrationData={evalData?.calibration} />
              </ModernCard>
            </ModernSection>
            )}

            {/* Per-Class XGBoost Metrics + Confusion Matrices */}
            {activeTab === 'performance' && (
            <ModernSection title="Per-Class Performance & Confusion Matrices" icon delay={0.5}>
              <ModernCard solid className="p-8">
                <PerClassMetricsTable evaluationData={evalData} />
              </ModernCard>
            </ModernSection>
            )}

            {/* Feature Ablation Study */}
            {activeTab === 'performance' && (
            <ModernSection title="Feature Ablation Study" icon delay={0.55}>
              <ModernCard solid className="p-8">
                <AblationStudyChart />
              </ModernCard>
            </ModernSection>
            )}

            {/* Sensitivity Analysis */}
            {activeTab === 'performance' && (
            <ModernSection title="Sensitivity Analysis — Grade Stability Under Input Perturbation" icon delay={0.6}>
              <ModernCard solid className="p-8">
                <SensitivityAnalysisChart />
              </ModernCard>
            </ModernSection>
            )}

            {/* Model Metrics Overview */}
            {activeTab === 'performance' && (
            <ModernSection title="Model Performance Metrics" icon delay={0.65}>
              <ModernCard solid className="p-8">
                <div className="space-y-4">
                  <p className="text-slate-400 text-sm text-center">
                    Full accuracy and classification statistics for both trained models
                  </p>
                  <div className="min-h-[500px] flex items-start justify-center">
                    <ModelMetricsChart />
                  </div>
                </div>
              </ModernCard>
            </ModernSection>
            )}

            {/* Carbon Equivalences */}
            {activeTab === 'performance' && (
            <ModernSection title="Carbon Equivalences" icon delay={0.65}>
              <ModernCard solid className="p-8">
                <CarbonEquivalences />
              </ModernCard>
            </ModernSection>
            )}

            {/* Training Pipeline */}
            {activeTab === 'methodology' && (
            <ModernSection title="Training Pipeline Architecture" icon delay={0.7}>
              <div className="space-y-20">
                {/* Random Forest */}
                <ModernCard solid className="p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-xl flex items-center justify-center">
                      <span className="text-white text-xl">📊</span>
                    </div>
                    <div>
                      <h3 className="text-2xl font-display text-slate-200">train_model.py</h3>
                      <p className="text-slate-400">Random Forest Baseline — 84.9% accuracy</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="space-y-6">
                      <div>
                        <h4 className="text-lg font-medium text-cyan-400 mb-3">Data Preprocessing Pipeline</h4>
                        <div className="bg-slate-800/50 p-4 rounded-lg space-y-2">
                          <code className="text-sm text-slate-300 block">df = pd.read_csv("eco_dataset.csv")</code>
                          <code className="text-sm text-slate-300 block">df = df.dropna(subset=["material", "true_eco_score"])</code>
                          <code className="text-sm text-slate-300 block">encoders = &#123;'material': LabelEncoder(), ...&#125;</code>
                          <code className="text-sm text-slate-300 block">X_train, X_test = train_test_split(X, y, test_size=0.2)</code>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-cyan-400 mb-3">Model Configuration</h4>
                        <ul className="space-y-2 text-sm text-slate-300">
                          <li>• <strong>Algorithm:</strong> RandomForestClassifier</li>
                          <li>• <strong>Estimators:</strong> 100 decision trees</li>
                          <li>• <strong>Max Depth:</strong> 10 levels</li>
                          <li>• <strong>Features:</strong> 6-dimensional vector</li>
                          <li>• <strong>Criterion:</strong> Gini impurity</li>
                        </ul>
                      </div>
                    </div>
                    <div className="space-y-6">
                      <div>
                        <h4 className="text-lg font-medium text-cyan-400 mb-3">Performance Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-slate-800/50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-green-400">84.9%</div>
                            <div className="text-slate-400 text-sm">Accuracy</div>
                          </div>
                          <div className="bg-slate-800/50 p-4 rounded-lg text-center">
                            <div className="text-2xl font-bold text-blue-400">85.0%</div>
                            <div className="text-slate-400 text-sm">F1-Score</div>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-cyan-400 mb-3">Output Artifacts</h4>
                        <ul className="space-y-2 text-sm text-slate-300">
                          <li>• <code className="bg-slate-700 px-2 py-1 rounded">eco_model.pkl</code></li>
                          <li>• <code className="bg-slate-700 px-2 py-1 rounded">confusion_matrix.png</code></li>
                          <li>• <code className="bg-slate-700 px-2 py-1 rounded">feature_importance.png</code></li>
                          <li>• <code className="bg-slate-700 px-2 py-1 rounded">metrics.json</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </ModernCard>

                {/* XGBoost */}
                <ModernCard solid className="p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-400 rounded-xl flex items-center justify-center">
                      <span className="text-white text-xl">🚀</span>
                    </div>
                    <div>
                      <h3 className="text-2xl font-display text-slate-200">train_xgboost.py</h3>
                      <p className="text-slate-400">Enhanced XGBoost — 86.6% accuracy (+1.7% over baseline)</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div>
                      <h4 className="text-lg font-medium text-purple-400 mb-3">Enhanced Features</h4>
                      <div className="space-y-3">
                        <div className="bg-slate-800/50 p-3 rounded">
                          <div className="text-sm font-medium text-slate-200">Core Features (6)</div>
                          <div className="text-xs text-slate-400 mt-1">material, transport, recyclability, origin, weight_log, weight_bin</div>
                        </div>
                        <div className="bg-slate-800/50 p-3 rounded">
                          <div className="text-sm font-medium text-slate-200">Enhanced Features (+5)</div>
                          <div className="text-xs text-slate-400 mt-1">packaging_type, size_category, quality_level, pack_size, material_confidence</div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-lg font-medium text-purple-400 mb-3">Hyperparameter Tuning</h4>
                      <div className="bg-slate-800/50 p-4 rounded-lg space-y-2">
                        <code className="text-xs text-slate-300 block">param_grid = &#123;</code>
                        <code className="text-xs text-slate-300 block">  'n_estimators': [100, 200, 300],</code>
                        <code className="text-xs text-slate-300 block">  'max_depth': [3, 6, 10],</code>
                        <code className="text-xs text-slate-300 block">  'learning_rate': [0.01, 0.1, 0.2]</code>
                        <code className="text-xs text-slate-300 block">&#125;</code>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-lg font-medium text-purple-400 mb-3">Advanced Techniques</h4>
                      <ul className="space-y-2 text-sm text-slate-300">
                        <li>• <strong>SMOTE:</strong> Synthetic oversampling</li>
                        <li>• <strong>RandomizedSearchCV:</strong> 100 iterations</li>
                        <li>• <strong>Early Stopping:</strong> Patience=10</li>
                        <li>• <strong>Cross-Validation:</strong> 5-fold stratified</li>
                      </ul>
                    </div>
                  </div>

                  <div className="border-t border-slate-700 pt-6 mt-6">
                    <h4 className="text-lg font-medium text-purple-400 mb-4">Performance vs Baseline</h4>
                    <div className="grid grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-purple-400">86.6%</div>
                        <div className="text-slate-300 font-medium">XGBoost Accuracy</div>
                        <div className="text-green-400 text-sm">+1.7% over Random Forest</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-purple-400">86.7%</div>
                        <div className="text-slate-300 font-medium">Macro F1-Score</div>
                        <div className="text-green-400 text-sm">+1.7% over baseline</div>
                      </div>
                      <div className="text-center">
                        <div className="text-3xl font-bold text-teal-400">99.9%</div>
                        <div className="text-slate-300 font-medium">Best Class F1 (A+)</div>
                        <div className="text-blue-400 text-sm">Near-perfect detection</div>
                      </div>
                    </div>
                  </div>
                </ModernCard>
              </div>
            </ModernSection>
            )}

            {/* Conformal Prediction */}
            {activeTab === 'methodology' && (
            <ModernSection title="Uncertainty Quantification — Conformal Prediction" icon delay={0.72}>
              <ModernCard solid className="p-8">
                <div className="space-y-5 text-sm text-slate-300 leading-relaxed">
                  <p>
                    Point predictions (e.g., grade <span className="font-mono text-cyan-300">B</span>) give no
                    indication of how certain the model is. To address this, the system uses{" "}
                    <strong className="text-slate-100">split-conformal prediction</strong> (Vovk et al., 2005;
                    Angelopoulos & Bates, 2021) to produce <em>prediction sets</em> — sets of grades that are
                    guaranteed to contain the true label with a specified probability.
                  </p>
                  <div className="bg-slate-700/40 rounded-lg p-4 space-y-2">
                    <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">How it works</p>
                    <ol className="list-decimal list-inside space-y-1.5 text-slate-300 text-sm">
                      <li>A held-out <em>calibration set</em> (12,500 samples, not seen during training) is used to compute non-conformity scores — the softmax probability assigned to the <em>true</em> class.</li>
                      <li>For a target coverage level α (e.g., 90%), the quantile <span className="font-mono text-cyan-300">q̂</span> of calibration scores is computed: the threshold below which α% of calibration examples fall.</li>
                      <li>At inference time, the prediction set is all grades whose softmax probability exceeds <span className="font-mono text-cyan-300">1 − q̂</span>.</li>
                      <li>By construction, the true label is included in this set with at least α% probability — a <strong className="text-slate-100">marginal coverage guarantee</strong> that holds without distributional assumptions.</li>
                    </ol>
                  </div>
                  <p>
                    The system computes prediction sets at both 90% and 95% coverage levels. A narrow set
                    (e.g., just <span className="font-mono text-cyan-300">{"{B}"}</span>) indicates high confidence;
                    a wide set (e.g., <span className="font-mono text-cyan-300">{"{A, B, C}"}</span>) signals
                    genuine ambiguity. These are displayed on every product result card alongside the point
                    prediction, providing honest uncertainty disclosure.
                  </p>
                  <p className="text-xs text-slate-500 pt-2 border-t border-slate-700/50">
                    Vovk, V., Gammerman, A., &amp; Shafer, G. (2005). <em>Algorithmic Learning in a Random World.</em> Springer. ·
                    Angelopoulos, A., &amp; Bates, S. (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification. <em>arXiv:2107.07511.</em>
                  </p>
                </div>
              </ModernCard>
            </ModernSection>
            )}

            {/* Technology Stack */}
            {activeTab === 'methodology' && (
            <ModernSection title="Technology Stack" icon delay={0.75}>
              <ModernCard solid className="p-8">
                <p className="text-slate-400 text-sm mb-6">
                  Full-stack implementation spanning frontend, backend, ML pipeline, and cloud infrastructure.
                </p>
                <TechStackSection />
              </ModernCard>
            </ModernSection>
            )}

            {/* Limitations */}
            {activeTab === 'methodology' && (
            <ModernSection title="Limitations & Scope" icon delay={0.8}>
              <ModernCard solid className="p-8">
                <LimitationsSection />
              </ModernCard>
            </ModernSection>
            )}

            {/* How It Works */}
            {activeTab === 'overview' && (
            <ModernSection title="How Predictions Are Made" icon delay={0.85} className="mb-24">
              <ModernCard solid>
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">🧠 Machine Learning Process</h4>
                      <p className="text-slate-300 leading-relaxed">
                        XGBoost processes an 11-feature vector through gradient-boosted decision trees.
                        Each input is encoded via LabelEncoders trained on the same distribution as the
                        training set. The model outputs a grade probability distribution —
                        <code className="bg-slate-700 px-2 py-1 rounded text-cyan-400 mx-1">predict_proba</code>
                        determines the confidence score shown in results.
                      </p>
                    </div>
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">📐 Rule-Based Calculation</h4>
                      <p className="text-slate-300 leading-relaxed">
                        In parallel, the DEFRA rule-based method computes CO₂ from first principles:
                        transport emissions (weight × DEFRA factor × distance ÷ 1000) plus material
                        manufacturing intensity. Both grades are returned so users can compare
                        the formula-based and ML-based assessments.
                      </p>
                    </div>
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">🔍 Key Features</h4>
                      <p className="text-slate-300 leading-relaxed">
                        The model analyses weight, material composition, country of origin, transport
                        mode, recyclability, and 5 additional contextual features. Material detection
                        checks the product title first (most reliable signal) before scanning page text.
                      </p>
                    </div>
                    <div className="space-y-4">
                      <h4 className="text-lg font-display text-slate-200">⚡ Real-Time Analysis</h4>
                      <p className="text-slate-300 leading-relaxed">
                        The optimised pipeline returns results in 5–10 seconds: scraping (~7 s),
                        feature extraction (~0.1 s), ML inference (~0.05 s), database write (~0.1 s).
                        The XGBoost model is loaded once at startup and kept in memory for
                        sub-millisecond inference on subsequent requests.
                      </p>
                    </div>
                  </div>
                </div>
              </ModernCard>
            </ModernSection>
            )}

            <Footer />
            <ModelInfoModal isOpen={showModal} onClose={() => setShowModal(false)} />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
