import React from "react";
import { motion, AnimatePresence } from "framer-motion";

// ─── Published LCA reference data ────────────────────────────────────────────
// Sources: ecoinvent v3, PE International, CES EduPack, IPCC AR6

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

// ─── Stage colours ────────────────────────────────────────────────────────────
const STAGE_COLORS = [
  { bar: "bg-amber-400",   text: "text-amber-400",   hex: "#fbbf24" },
  { bar: "bg-orange-500",  text: "text-orange-400",  hex: "#f97316" },
  { bar: "bg-blue-400",    text: "text-blue-400",    hex: "#60a5fa" },
  { bar: "bg-violet-400",  text: "text-violet-400",  hex: "#a78bfa" },
  { bar: "bg-cyan-400",    text: "text-cyan-400",    hex: "#22d3ee" },
  { bar: "bg-emerald-400", text: "text-emerald-400", hex: "#34d399" },
];

// ─── LCA calculation ──────────────────────────────────────────────────────────
function calcStages(attr) {
  const weight     = parseFloat(attr.raw_product_weight_kg || attr.weight_kg || 0.5);
  const material   = (attr.material_type || "plastics").toLowerCase();
  const country    = (attr.country_of_origin || attr.origin || "china").toLowerCase();
  const mode       = (attr.transport_mode || "ship").toLowerCase();
  const originKm   = parseFloat(attr.distance_from_origin_km || 8000);
  const ukHubKm    = parseFloat(attr.distance_from_uk_hub_km || 50);
  const recyclability = (attr.recyclability || "medium").toLowerCase();

  const matIntensity = MATERIAL_CO2_KG_PER_KG[material] ?? 3.0;
  const mfgEnergy    = MFG_ENERGY_KWH_PER_KG[material] ?? 10;
  const gridIntensity = GRID_INTENSITY_KG_CO2_PER_KWH[country] ?? 0.5;
  const transFactor  = TRANSPORT_FACTOR[mode] ?? TRANSPORT_FACTOR.ship;

  const rawMaterial   = +(weight * matIntensity).toFixed(3);
  const manufacturing = +(weight * mfgEnergy * gridIntensity).toFixed(3);
  const intlShipping  = +(weight * originKm * transFactor).toFixed(3);
  const ukDist        = 0.05;
  const lastMile      = +(Math.max(ukHubKm, 10) * 0.00021 * (1 / 40)).toFixed(3);
  const eol = recyclability === "high"  ? +(weight * 0.02).toFixed(3)
            : recyclability === "medium" ? +(weight * 0.08).toFixed(3)
            :                              +(weight * 0.18).toFixed(3);

  const countryLabel = attr.country_of_origin || attr.origin || "Unknown";

  return [
    {
      name: "Raw Material Extraction",
      icon: "⛏️",
      co2: rawMaterial,
      detail: `${material.charAt(0).toUpperCase() + material.slice(1)} · ${weight.toFixed(2)} kg product`,
      source: "ecoinvent v3 / CES EduPack",
    },
    {
      name: "Manufacturing & Processing",
      icon: "🏭",
      co2: manufacturing,
      detail: `Production in ${countryLabel} (grid: ${(gridIntensity * 1000).toFixed(0)} g CO₂/kWh)`,
      source: "IEA 2023 grid intensity data",
    },
    {
      name: "International Shipping",
      icon: mode === "air" ? "✈️" : mode === "truck" ? "🚚" : "🚢",
      co2: intlShipping,
      detail: `${mode.charAt(0).toUpperCase() + mode.slice(1)} freight · ${originKm.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} km`,
      source: "DEFRA 2023 transport factors",
    },
    {
      name: "UK Warehousing & Distribution",
      icon: "🏪",
      co2: ukDist,
      detail: "Storage, sorting & domestic freight",
      source: "Amazon UK logistics estimate",
    },
    {
      name: "Last-Mile Delivery",
      icon: "🚐",
      co2: lastMile,
      detail: "Van delivery to your door",
      source: "BEIS delivery emissions estimate",
    },
    {
      name: "End-of-Life Disposal",
      icon: "♻️",
      co2: eol,
      detail: recyclability === "high" ? "High recyclability — mostly diverted from landfill"
            : recyclability === "medium" ? "Partial recycling — some landfill"
            : "Low recyclability — primarily landfill",
      source: "WRAP UK waste data",
    },
  ];
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function LifecycleAssessment({ attr }) {
  const [open, setOpen] = React.useState(false);

  if (!attr) return null;

  const stages  = calcStages(attr);
  const lcaTotal = stages.reduce((s, st) => s + st.co2, 0);
  const mlTotal  = parseFloat(attr.carbon_kg || 0);

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
              6-stage end-to-end carbon breakdown
            </p>
          </div>
        </div>

        {/* Stacked mini-bar preview */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="hidden sm:flex h-2 w-28 rounded-full overflow-hidden gap-px">
            {stages.map((st, i) => (
              <div
                key={i}
                className={`${STAGE_COLORS[i].bar} transition-all`}
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
                    className={`${STAGE_COLORS[i].bar} transition-all`}
                    style={{ width: `${(st.co2 / lcaTotal) * 100}%` }}
                    title={`${st.name}: ${st.co2} kg CO₂`}
                  />
                ))}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3">
                {stages.map((st, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${STAGE_COLORS[i].bar} flex-shrink-0`} />
                    <span className="text-slate-500 text-xs">{st.name.split(" ")[0]} {st.name.split(" ")[1] || ""}</span>
                  </div>
                ))}
              </div>

              {/* Stage rows */}
              {stages.map((st, i) => {
                const pct = lcaTotal > 0 ? (st.co2 / lcaTotal) * 100 : 0;
                return (
                  <div key={i} className="bg-slate-800/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2 gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-base flex-shrink-0">{st.icon}</span>
                        <span className="text-slate-200 text-sm font-medium truncate">
                          {st.name}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`${STAGE_COLORS[i].text} font-mono text-sm font-bold`}>
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
                        className={`h-full ${STAGE_COLORS[i].bar} rounded-full`}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.6, delay: i * 0.08 }}
                      />
                    </div>

                    <p className="text-slate-500 text-xs">{st.detail}</p>
                  </div>
                );
              })}

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
                    <span className="text-slate-500 text-xs">Our ML model total</span>
                    <span className="text-cyan-400 font-mono text-xs">
                      {mlTotal.toFixed(3)} kg CO₂
                    </span>
                  </div>
                )}
                {mlTotal > 0 && (
                  <div className="mt-2 text-xs text-slate-600 leading-relaxed">
                    {Math.abs(lcaTotal - mlTotal) / mlTotal < 0.25
                      ? "✅ LCA estimate is consistent with our ML model output."
                      : lcaTotal > mlTotal
                      ? "⚠️ LCA estimate is higher — ML model may be using conservative assumptions."
                      : "ℹ️ LCA estimate is lower — ML model may be accounting for additional factors."}
                  </div>
                )}
              </div>

              {/* Methodology disclaimer */}
              <div className="flex gap-2 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                <span className="text-slate-500 text-xs flex-shrink-0">📚</span>
                <p className="text-slate-600 text-xs leading-relaxed">
                  Stage estimates use published LCA reference data (ecoinvent v3, DEFRA 2023, IEA 2023).
                  Actual values vary by manufacturer, product design, and logistics route.
                  This breakdown is indicative and intended for comparison, not certification.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
