import React from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Published LCA reference data ────────────────────────────────────────────
// Sources: ecoinvent v3.9, PE International, CES EduPack 2023, IPCC AR6

const MATERIAL_CO2_KG_PER_KG = {
  // Metals
  aluminum: 8.24, aluminium: 8.24,
  steel: 1.77, "stainless steel": 6.15, "carbon steel": 2.1,
  copper: 3.86, brass: 3.8, bronze: 3.8,
  iron: 1.91, "cast iron": 2.1,
  titanium: 35.0, "titanium alloys": 35.0,
  zinc: 3.86, tin: 16.0, lead: 1.64,
  // Polymers
  plastics: 2.53, polyethylene: 1.88, polypropylene: 1.95,
  polyester: 9.52, nylon: 9.74, abs: 3.81,
  polycarbonate: 7.66, pvc: 2.56, polyurethane: 3.8,
  acrylic: 3.82, silicone: 5.0, rubber: 3.15,
  // Natural textiles
  cotton: 5.89, "organic cotton": 3.5, wool: 17.0,
  "merino wool": 17.0, cashmere: 370.0, silk: 35.0,
  linen: 1.7, hemp: 2.15, jute: 0.97, bamboo: 0.81,
  // Synthetic textiles
  "recycled polyester": 4.82, "recycled nylon": 4.32,
  viscose: 4.5, rayon: 4.5, "lyocell tencel": 2.42,
  // Leather
  leather: 17.0, "genuine leather": 17.0, "faux leather": 5.5, suede: 17.0,
  // Wood & paper
  timber: 0.47, plywood: 0.81, mdf: 0.93, cork: 0.2,
  paper: 1.09, cardboard: 0.92,
  // Other
  glass: 0.85, ceramic: 1.29, porcelain: 1.29,
  "carbon fiber": 31.0, concrete: 0.159,
};

const MFG_ENERGY_KWH_PER_KG = {
  aluminum: 45, aluminium: 45, steel: 8, "stainless steel": 20,
  copper: 12, iron: 7, titanium: 100, "titanium alloys": 100,
  plastics: 10, polyethylene: 8, polypropylene: 8,
  polyester: 12, nylon: 15, abs: 11, polycarbonate: 14,
  pvc: 9, polyurethane: 11, silicone: 12, rubber: 9,
  cotton: 18, "organic cotton": 15, wool: 25, silk: 30,
  linen: 10, hemp: 8, leather: 20, "faux leather": 12,
  timber: 4, bamboo: 3, plywood: 5, paper: 8,
  glass: 10, ceramic: 8, "carbon fiber": 50,
};

const GRID_INTENSITY_KG_CO2_PER_KWH = {
  china: 0.581, bangladesh: 0.597, india: 0.708,
  vietnam: 0.501, pakistan: 0.342, indonesia: 0.76,
  cambodia: 0.58, myanmar: 0.56, thailand: 0.498,
  usa: 0.386, "united states": 0.386,
  germany: 0.338, france: 0.057, uk: 0.233,
  "united kingdom": 0.233, italy: 0.233, spain: 0.182,
  sweden: 0.013, japan: 0.474, "south korea": 0.415,
  taiwan: 0.539, turkey: 0.444, mexico: 0.45,
  brazil: 0.075, canada: 0.13, australia: 0.656,
};

const TRANSPORT_FACTOR = { air: 0.00234, truck: 0.000096, ship: 0.000016 };

// ─── Use-phase data ───────────────────────────────────────────────────────────
// Source: IEA Tracking Clean Energy Progress 2023; ENERGY STAR 2023;
//         Carbon Trust "Introducing the Carbon Footprint of Laptops" 2021
// annual_kwh: typical annual electricity consumption (kWh/year)
// lifetime_yr: expected product lifetime (years)
const USE_PHASE_DEVICES = [
  { keywords: ["smart tv", "television", " tv "],       label: "Television",        annual_kwh: 150, lifetime_yr: 7  },
  { keywords: ["laptop", "notebook", "macbook", "chromebook"], label: "Laptop",     annual_kwh: 45,  lifetime_yr: 3.5 },
  { keywords: ["desktop", "pc tower", "imac"],          label: "Desktop PC",        annual_kwh: 200, lifetime_yr: 5  },
  { keywords: ["tablet", "ipad", "kindle"],             label: "Tablet / e-Reader", annual_kwh: 12,  lifetime_yr: 3  },
  { keywords: ["monitor", "display", "screen"],         label: "Monitor",           annual_kwh: 50,  lifetime_yr: 6  },
  { keywords: ["gaming console", "playstation", "xbox", "nintendo switch"], label: "Gaming Console", annual_kwh: 100, lifetime_yr: 6 },
  { keywords: ["router", "wifi", "mesh network"],       label: "Router (always-on)",annual_kwh: 80,  lifetime_yr: 4  },
  { keywords: ["printer", "scanner"],                   label: "Printer",           annual_kwh: 20,  lifetime_yr: 5  },
  { keywords: ["smart speaker", "echo", "google home", "homepod"], label: "Smart Speaker", annual_kwh: 15, lifetime_yr: 4 },
  { keywords: ["speaker", "soundbar", "subwoofer"],     label: "Speaker",           annual_kwh: 20,  lifetime_yr: 5  },
  { keywords: ["smartphone", "iphone", "android phone", "mobile phone"], label: "Smartphone", annual_kwh: 4, lifetime_yr: 2.5 },
  { keywords: ["phone", "pixel"],                       label: "Smartphone",        annual_kwh: 4,   lifetime_yr: 2.5 },
  { keywords: ["headphone", "earphone", "earbud", "airpod"], label: "Headphones",  annual_kwh: 3,   lifetime_yr: 3  },
  { keywords: ["smartwatch", "fitness tracker", "apple watch", "fitbit"], label: "Smartwatch", annual_kwh: 4, lifetime_yr: 2 },
  { keywords: ["camera", "dslr", "mirrorless"],         label: "Camera",            annual_kwh: 8,   lifetime_yr: 5  },
  { keywords: ["keyboard"],                             label: "Keyboard",          annual_kwh: 2,   lifetime_yr: 5  },
  { keywords: ["graphics card", "gpu", "ssd", "hard drive"], label: "PC Component", annual_kwh: 50, lifetime_yr: 5 },
  { keywords: ["charger", "power bank"],                label: "Charger",           annual_kwh: 5,   lifetime_yr: 3  },
];
const USE_PHASE_DEFAULT_ELECTRONICS = { label: "Electronics (general)", annual_kwh: 30, lifetime_yr: 3 };
const UK_GRID = 0.233; // kg CO₂/kWh — DESNZ/DEFRA 2023

function detectDeviceType(title) {
  const t = (title || "").toLowerCase();
  for (const device of USE_PHASE_DEVICES) {
    if (device.keywords.some(kw => t.includes(kw))) return device;
  }
  return null;
}

// ─── Stage colours (8 slots for all possible stages) ─────────────────────────
const STAGE_COLORS = [
  { bar: "bg-amber-400",   text: "text-amber-400",   hex: "#fbbf24" }, // raw material
  { bar: "bg-orange-500",  text: "text-orange-400",  hex: "#f97316" }, // manufacturing
  { bar: "bg-yellow-600",  text: "text-yellow-500",  hex: "#ca8a04" }, // packaging
  { bar: "bg-blue-400",    text: "text-blue-400",    hex: "#60a5fa" }, // intl shipping
  { bar: "bg-violet-400",  text: "text-violet-400",  hex: "#a78bfa" }, // uk distribution
  { bar: "bg-cyan-400",    text: "text-cyan-400",    hex: "#22d3ee" }, // last mile
  { bar: "bg-rose-400",    text: "text-rose-400",    hex: "#fb7185" }, // use phase
  { bar: "bg-emerald-400", text: "text-emerald-400", hex: "#34d399" }, // end-of-life
];

// ─── Multi-material weighted intensity ───────────────────────────────────────
function weightedMaterialIntensity(materialsAttr, fallbackMaterial) {
  const primary = materialsAttr?.primary_material;
  const primaryPct = parseFloat(materialsAttr?.primary_percentage) || 0;
  const secondaries = materialsAttr?.secondary_materials || [];

  // Need at least a primary with a percentage, plus at least one secondary, to do weighting
  const hasComposition = primary && primaryPct > 0 && secondaries.length > 0;

  if (!hasComposition) {
    const mat = (fallbackMaterial || "plastics").toLowerCase();
    return {
      matIntensity: MATERIAL_CO2_KG_PER_KG[mat] ?? 3.0,
      mfgEnergy: MFG_ENERGY_KWH_PER_KG[mat] ?? 10,
      compositionLabel: null,
    };
  }

  // Build composition list: [{name, pct}]
  const allComponents = [
    { name: primary.toLowerCase(), pct: primaryPct },
    ...secondaries
      .filter(s => s.name && parseFloat(s.percentage) > 0)
      .map(s => ({ name: s.name.toLowerCase(), pct: parseFloat(s.percentage) })),
  ];

  // Normalise to 100% in case percentages don't sum exactly
  const totalPct = allComponents.reduce((s, c) => s + c.pct, 0) || 100;

  let matIntensity = 0;
  let mfgEnergy = 0;
  for (const c of allComponents) {
    const share = c.pct / totalPct;
    matIntensity += (MATERIAL_CO2_KG_PER_KG[c.name] ?? 3.0) * share;
    mfgEnergy    += (MFG_ENERGY_KWH_PER_KG[c.name]    ?? 10)  * share;
  }

  const compositionLabel = allComponents
    .map(c => `${c.name.charAt(0).toUpperCase() + c.name.slice(1)} ${Math.round((c.pct / totalPct) * 100)}%`)
    .join(" · ");

  return { matIntensity, mfgEnergy, compositionLabel };
}

// ─── Packaging CO₂ ────────────────────────────────────────────────────────────
// Based on McKinnon & Edwards (2014) e-commerce packaging study.
// Packaging material mix: ~70% corrugated cardboard (0.92 kg CO₂/kg),
// ~30% protective plastic/foam (2.53 kg CO₂/kg) → blended factor ≈ 1.40 kg CO₂/kg.
// Packaging weight scales with product weight; minimum ~80 g for small items.
function calcPackagingCo2(weight) {
  const packagingWeight = Math.max(0.08, Math.min(0.5, weight * 0.12));
  return +((packagingWeight * 1.40).toFixed(3));
}

// ─── LCA calculation ──────────────────────────────────────────────────────────
function calcStages(attr) {
  const weight       = parseFloat(attr.raw_product_weight_kg || attr.weight_kg || 0.5);
  const material     = (attr.material_type || "plastics").toLowerCase();
  const country      = (attr.country_of_origin || attr.origin || "china").toLowerCase();
  const mode         = (attr.transport_mode || "ship").toLowerCase();
  const originKm     = parseFloat(attr.distance_from_origin_km || 8000);
  const recyclability = (attr.recyclability || "medium").toLowerCase();
  const category     = (attr.category || "").toLowerCase();
  const title        = attr.title || "";

  const { matIntensity, mfgEnergy, compositionLabel } =
    weightedMaterialIntensity(attr.materials, material);

  const gridIntensity = GRID_INTENSITY_KG_CO2_PER_KWH[country] ?? 0.5;
  const transFactor   = TRANSPORT_FACTOR[mode] ?? TRANSPORT_FACTOR.ship;
  const countryLabel  = attr.country_of_origin || attr.origin || "Unknown";

  // ── Stage values ────────────────────────────────────────────────────────────
  const rawMaterial   = +(weight * matIntensity).toFixed(3);
  const manufacturing = +(weight * mfgEnergy * gridIntensity).toFixed(3);
  const packaging     = calcPackagingCo2(weight);
  const intlShipping  = +(weight * originKm * transFactor).toFixed(3);
  // UK distribution: HGV domestic leg ~200 km + fixed warehousing overhead
  const ukDist        = +(weight * 0.000096 * 200 + 0.03).toFixed(3);
  // Last-mile: shared-van route (~60 km, 40 stops) + weight surcharge
  const lastMile      = +(60 * 0.21 / 40 + weight * 0.005).toFixed(3);
  const eol = recyclability === "high"   ? +(weight * 0.02).toFixed(3)
            : recyclability === "medium" ? +(weight * 0.08).toFixed(3)
            :                              +(weight * 0.18).toFixed(3);

  // ── Raw material detail ─────────────────────────────────────────────────────
  const rawDetail = compositionLabel
    ? `Weighted mix: ${compositionLabel} · ${weight.toFixed(2)} kg`
    : `${material.charAt(0).toUpperCase() + material.slice(1)} · ${weight.toFixed(2)} kg`;

  // ── Use phase (Electronics only) ────────────────────────────────────────────
  let usePhaseStage = null;
  const isElectronics = category.includes("electronic") || category.includes("tech") ||
    category.includes("computer") || category.includes("camera") ||
    ["electronics", "computers", "cameras", "phones"].some(kw => category.includes(kw));

  if (isElectronics) {
    const device = detectDeviceType(title) || USE_PHASE_DEFAULT_ELECTRONICS;
    const totalKwh = device.annual_kwh * device.lifetime_yr;
    const useCo2   = +(totalKwh * UK_GRID).toFixed(3);
    usePhaseStage = {
      name: "Use Phase (Electricity)",
      icon: "⚡",
      co2: useCo2,
      detail: `${device.label} · ${device.annual_kwh} kWh/yr × ${device.lifetime_yr} yr @ UK grid (${Math.round(UK_GRID * 1000)} g CO₂/kWh)`,
      source: "IEA Tracking Clean Energy Progress 2023; ENERGY STAR 2023",
    };
  }

  // ── Assemble stage list ─────────────────────────────────────────────────────
  const stages = [
    {
      name: "Raw Material Extraction",
      icon: "⛏️",
      co2: rawMaterial,
      detail: rawDetail,
      source: "ecoinvent v3.9 / CES EduPack 2023",
    },
    {
      name: "Manufacturing & Processing",
      icon: "🏭",
      co2: manufacturing,
      detail: `Production in ${countryLabel} (grid: ${(gridIntensity * 1000).toFixed(0)} g CO₂/kWh)`,
      source: "IEA World Energy Outlook 2023 — country grid intensity",
    },
    {
      name: "Packaging",
      icon: "📦",
      co2: packaging,
      detail: `~${Math.max(0.08, Math.min(0.5, weight * 0.12)).toFixed(2)} kg packaging (cardboard + protective wrap)`,
      source: "McKinnon & Edwards (2014); WRAP Packaging CO₂ Data 2023",
    },
    {
      name: "International Shipping",
      icon: mode === "air" ? "✈️" : mode === "truck" ? "🚚" : "🚢",
      co2: intlShipping,
      detail: `${mode.charAt(0).toUpperCase() + mode.slice(1)} freight · ${originKm.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} km`,
      source: "DEFRA GHG Conversion Factors 2023 — freight transport",
    },
    {
      name: "UK Warehousing & Distribution",
      icon: "🏪",
      co2: ukDist,
      detail: "HGV hub-to-warehouse domestic leg (~200 km) + storage",
      source: "McKinnon (2016) Logistics & Sustainability; BEIS 2023",
    },
    {
      name: "Last-Mile Delivery",
      icon: "🚐",
      co2: lastMile,
      detail: "Shared courier van to your door (~60 km route, 40 stops)",
      source: "BEIS/DEFRA GHG Conversion Factors 2023 — vans",
    },
    ...(usePhaseStage ? [usePhaseStage] : []),
    {
      name: "End-of-Life Disposal",
      icon: "♻️",
      co2: eol,
      detail: recyclability === "high"   ? "High recyclability — mostly diverted from landfill"
            : recyclability === "medium" ? "Partial recycling — some landfill"
            :                              "Low recyclability — primarily landfill",
      source: "WRAP UK Waste and Resources Action Programme 2023",
    },
  ];

  return stages;
}

// ─── Transport sub-breakdown ──────────────────────────────────────────────────
function TransportBreakdown({ tb }) {
  if (!tb) return null;
  const { international_kg, uk_distribution_kg, last_mile_kg, total_transport_kg,
          international_distance_km, transport_mode } = tb;
  const total = total_transport_kg || 0.001;
  const segments = [
    { label: "International", kg: international_kg, color: "bg-blue-400", textColor: "text-blue-400",
      detail: `${transport_mode} · ${Number(international_distance_km).toLocaleString()} km` },
    { label: "UK Distribution", kg: uk_distribution_kg, color: "bg-violet-400", textColor: "text-violet-400",
      detail: "HGV hub → warehouse (~200 km)" },
    { label: "Last-Mile", kg: last_mile_kg, color: "bg-cyan-400", textColor: "text-cyan-400",
      detail: "Courier van to your door" },
  ];
  return (
    <div className="mt-3 p-3 bg-slate-900/40 rounded-lg border border-slate-700/40">
      <p className="text-slate-400 text-xs font-semibold mb-2 flex items-center gap-1.5">
        <span>🚚</span> Delivery CO₂ Breakdown
        <span className="ml-auto text-slate-300 font-mono">{total_transport_kg.toFixed(3)} kg total</span>
      </p>
      {/* Stacked bar */}
      <div className="flex h-2.5 w-full rounded-full overflow-hidden gap-px mb-3">
        {segments.map((s, i) => (
          <div
            key={i}
            className={`${s.color} transition-all`}
            style={{ width: `${(s.kg / total) * 100}%` }}
            title={`${s.label}: ${s.kg} kg CO₂`}
          />
        ))}
      </div>
      {/* Rows */}
      <div className="space-y-1.5">
        {segments.map((s, i) => (
          <div key={i} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className={`w-2 h-2 rounded-full ${s.color} flex-shrink-0`} />
              <span className="text-slate-400 text-xs truncate">{s.label}</span>
              <span className="text-slate-600 text-xs hidden sm:inline">· {s.detail}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`${s.textColor} text-xs font-mono font-semibold`}>{s.kg.toFixed(3)} kg</span>
              <span className="text-slate-600 text-xs w-8 text-right">{((s.kg / total) * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
      <p className="text-slate-700 text-xs mt-2 leading-relaxed">Source: {tb.source}</p>
    </div>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function LifecycleAssessment({ attr }) {
  const [open, setOpen] = React.useState(false);

  if (!attr) return null;

  const stages   = calcStages(attr);
  const lcaTotal = stages.reduce((s, st) => s + st.co2, 0);
  const mlTotal  = parseFloat(attr.carbon_kg || 0);
  const hasUsePhase = stages.some(s => s.name.startsWith("Use Phase"));

  return (
    <motion.div
      className="glass-card rounded-xl overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.35 }}
    >
      {/* ── Accordion header ── */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full px-5 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xl flex-shrink-0">🔬</span>
          <div className="min-w-0">
            <p className="text-slate-200 font-semibold text-sm">
              Lifecycle Assessment (LCA)
            </p>
            <p className="text-slate-500 text-xs mt-0.5">
              {stages.length}-stage end-to-end carbon breakdown
              {hasUsePhase && <span className="text-rose-400 ml-1">· incl. use phase</span>}
            </p>
          </div>
        </div>

        {/* Stacked mini-bar preview */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="hidden sm:flex h-2 w-28 rounded-full overflow-hidden gap-px">
            {stages.map((st, i) => (
              <div
                key={i}
                className={`${STAGE_COLORS[i % STAGE_COLORS.length].bar} transition-all`}
                style={{ width: `${(st.co2 / lcaTotal) * 100}%` }}
              />
            ))}
          </div>
          <span className="text-slate-400 text-xs font-mono whitespace-nowrap">
            ~{lcaTotal.toFixed(2)} kg
          </span>
          <span
            className={`text-slate-400 transition-transform duration-200 text-sm ${open ? "rotate-180" : ""}`}
          >
            ▼
          </span>
        </div>
      </button>

      {/* ── Expanded content ── */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-3 border-t border-slate-700/50 pt-4">

              {/* Full stacked bar */}
              <div className="flex h-3 w-full rounded-full overflow-hidden gap-px mb-1">
                {stages.map((st, i) => (
                  <div
                    key={i}
                    className={`${STAGE_COLORS[i % STAGE_COLORS.length].bar} transition-all`}
                    style={{ width: `${(st.co2 / lcaTotal) * 100}%` }}
                    title={`${st.name}: ${st.co2} kg CO₂`}
                  />
                ))}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3">
                {stages.map((st, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${STAGE_COLORS[i % STAGE_COLORS.length].bar} flex-shrink-0`} />
                    <span className="text-slate-500 text-xs">{st.icon} {st.name.split(" ").slice(0, 2).join(" ")}</span>
                  </div>
                ))}
              </div>

              {/* Stage rows */}
              {stages.map((st, i) => {
                const pct = lcaTotal > 0 ? (st.co2 / lcaTotal) * 100 : 0;
                const color = STAGE_COLORS[i % STAGE_COLORS.length];
                return (
                  <div key={i} className={`bg-slate-800/50 rounded-lg p-3 ${st.name.startsWith("Use Phase") ? "ring-1 ring-rose-500/30" : ""}`}>
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-base flex-shrink-0">{st.icon}</span>
                        <span className="text-slate-200 text-sm font-medium truncate">
                          {st.name}
                        </span>
                        {st.name.startsWith("Use Phase") && (
                          <span className="text-rose-400 text-xs bg-rose-500/10 px-1.5 py-0.5 rounded flex-shrink-0">ISO 14040</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`${color.text} font-mono text-sm font-bold`}>
                          {st.co2.toFixed(3)} kg
                        </span>
                        <span className="text-slate-600 text-xs">
                          {pct.toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {/* Progress bar */}
                    <div className="h-1.5 w-full bg-slate-700 rounded-full overflow-hidden mb-2">
                      <motion.div
                        className={`h-full ${color.bar} rounded-full`}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, delay: i * 0.07 }}
                      />
                    </div>

                    <p className="text-slate-500 text-xs">{st.detail}</p>
                    <p className="text-slate-700 text-xs mt-1">Source: {st.source}</p>
                  </div>
                );
              })}

              {/* Transport sub-breakdown */}
              <TransportBreakdown tb={attr.transport_breakdown} />

              {/* Use-phase callout (shown when present) */}
              {hasUsePhase && (
                <div className="p-3 bg-rose-500/5 rounded-lg border border-rose-500/20">
                  <p className="text-rose-300 text-xs font-semibold mb-1">⚡ Why use phase matters for electronics</p>
                  <p className="text-slate-500 text-xs leading-relaxed">
                    For electronic devices, cumulative electricity consumption during the product's
                    lifetime is often the <span className="text-slate-300">largest single lifecycle stage</span> —
                    sometimes exceeding manufacturing CO₂ by 2–5×. This stage is required under
                    ISO 14040 cradle-to-grave LCA but is frequently omitted in simplified analyses.
                    Values use the UK grid intensity of {Math.round(UK_GRID * 1000)} g CO₂/kWh (DESNZ/DEFRA 2023).
                  </p>
                </div>
              )}

              {/* Total + ML comparison */}
              <div className="mt-2 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-sm">LCA estimated total</span>
                  <span className="text-slate-200 font-mono font-bold text-sm">
                    {lcaTotal.toFixed(3)} kg CO₂
                  </span>
                </div>
                {mlTotal > 0 && (
                  <div className="flex justify-between items-center mt-1.5">
                    <span className="text-slate-500 text-xs">
                      Our ML model total
                      {hasUsePhase && <span className="text-slate-600"> (excl. use phase)</span>}
                    </span>
                    <span className="text-cyan-400 font-mono text-xs">
                      {mlTotal.toFixed(3)} kg CO₂
                    </span>
                  </div>
                )}
                {mlTotal > 0 && !hasUsePhase && (
                  <div className="mt-2 text-xs text-slate-600 leading-relaxed">
                    {Math.abs(lcaTotal - mlTotal) / mlTotal < 0.25
                      ? "✅ LCA estimate is consistent with our ML model output."
                      : lcaTotal > mlTotal
                      ? "⚠️ LCA estimate is higher — ML model may be using conservative assumptions."
                      : "ℹ️ LCA estimate is lower — ML model may be accounting for additional factors."}
                  </div>
                )}
                {mlTotal > 0 && hasUsePhase && (
                  <div className="mt-2 text-xs text-slate-600 leading-relaxed">
                    ℹ️ The ML model estimates cradle-to-delivery CO₂. The LCA total above
                    includes the use phase, so direct comparison is not applicable.
                  </div>
                )}
              </div>

              {/* ML vs LCA variance explanation (non-electronics only) */}
              {mlTotal > 0 && !hasUsePhase && Math.abs(lcaTotal - mlTotal) / mlTotal > 0.15 && (
                <div className="p-3 bg-slate-800/40 rounded-lg border border-slate-600/30">
                  <p className="text-slate-300 text-xs font-semibold mb-1.5">
                    💡 Why do the LCA and ML estimates differ?
                  </p>
                  <p className="text-slate-500 text-xs leading-relaxed">
                    The <span className="text-cyan-400">LCA estimate</span> is a bottom-up calculation using
                    published reference values per kg of material — it treats every cotton product the same.
                    The <span className="text-cyan-400">ML model</span> was trained on real Amazon product
                    data across 11 features (category, brand, transport, recyclability etc.) and captures
                    real-world patterns that generic LCA data cannot — for example, a fast-fashion t-shirt
                    vs. a premium organic cotton shirt have very different actual footprints despite being
                    the same material. A variance of up to 40% between methods is normal and academically
                    expected when comparing bottom-up LCA with data-driven prediction.
                  </p>
                </div>
              )}

              {/* Methodology disclaimer */}
              <div className="flex gap-2 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                <span className="text-slate-500 text-xs flex-shrink-0">📚</span>
                <p className="text-slate-600 text-xs leading-relaxed">
                  Stage estimates use published LCA reference data (ecoinvent v3.9, DEFRA 2023, IEA 2023,
                  WRAP 2023). Multi-material products use composition-weighted emission factors where
                  material breakdown data is available. Transport emissions scale with product weight ×
                  distance × mode emission factor. Actual values vary by manufacturer, product design,
                  and logistics route. This breakdown is indicative and intended for comparison, not certification.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
