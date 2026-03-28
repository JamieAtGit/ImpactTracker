import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const MATERIAL_COLORS = [
  "bg-cyan-500/60",
  "bg-amber-500/60",
  "bg-purple-500/60",
  "bg-green-500/60",
  "bg-rose-500/60",
  "bg-sky-500/60",
];

const MATERIAL_COLOR_MAP = {
  glass: "bg-sky-400/70",
  aluminium: "bg-slate-400/70",
  aluminum: "bg-slate-400/70",
  steel: "bg-slate-500/70",
  "stainless steel": "bg-slate-400/70",
  plastic: "bg-amber-500/70",
  "abs plastic": "bg-amber-500/70",
  polycarbonate: "bg-amber-400/70",
  polypropylene: "bg-yellow-500/70",
  fabric: "bg-purple-500/70",
  cotton: "bg-purple-400/70",
  linen: "bg-purple-300/70",
  wood: "bg-orange-600/70",
  timber: "bg-orange-600/70",
  rubber: "bg-gray-600/70",
  silicone: "bg-teal-500/70",
  leather: "bg-amber-700/70",
  ceramic: "bg-red-400/70",
  copper: "bg-orange-500/70",
  foam: "bg-yellow-400/70",
  "memory foam": "bg-yellow-400/70",
};

function getColor(material, index) {
  const key = (material || "").toLowerCase();
  for (const [k, v] of Object.entries(MATERIAL_COLOR_MAP)) {
    if (key.includes(k)) return v;
  }
  return MATERIAL_COLORS[index % MATERIAL_COLORS.length];
}

export default function ImageMaterialAnalysis({ imageUrl, title, galleryImages, specMaterials }) {
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  if (!imageUrl || imageUrl === "Not found" || imageUrl === "") return null;

  async function handleAnalyse() {
    setStatus("loading");
    setResult(null);
    setErrorMsg("");
    try {
      const res = await fetch(`${BASE_URL}/api/analyse-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_url: imageUrl,
          title,
          gallery_images: galleryImages || [],
          spec_materials: specMaterials || {},
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Analysis failed");
      setResult(data);
      setStatus("done");
    } catch (e) {
      setErrorMsg(e.message || "Unexpected error");
      setStatus("error");
    }
  }

  const cornerClass = "absolute w-5 h-5 border-green-400";
  const isActive = status === "loading" || status === "done";

  return (
    <div className="glass-card rounded-xl p-4">
      <h4 className="text-slate-300 font-semibold text-sm mb-3 flex items-center gap-2">
        🔍 AI Visual Material Analysis
        <span className="text-xs text-slate-500 font-normal">(Beta)</span>
      </h4>

      {/* Product image with capture animation */}
      <div className="flex justify-center mb-4">
        <motion.div
          className="relative rounded-xl overflow-hidden inline-block"
          animate={
            status === "loading"
              ? {
                  boxShadow: [
                    "0 0 0 0px rgba(34,197,94,0)",
                    "0 0 0 4px rgba(34,197,94,0.65)",
                    "0 0 0 0px rgba(34,197,94,0)",
                  ],
                }
              : status === "done"
              ? { boxShadow: "0 0 0 2px rgba(34,197,94,0.45)" }
              : { boxShadow: "0 0 0 0px rgba(34,197,94,0)" }
          }
          transition={{ duration: 1.3, repeat: status === "loading" ? Infinity : 0 }}
        >
          <img
            src={imageUrl}
            alt={title || "Product"}
            className="max-h-56 max-w-full rounded-xl object-contain bg-slate-800/80"
            onError={(e) => {
              e.target.style.display = "none";
            }}
          />

          {/* Scanning line */}
          {status === "loading" && (
            <motion.div
              className="absolute inset-x-0 h-0.5 bg-green-400/80 shadow-[0_0_6px_rgba(34,197,94,0.8)] pointer-events-none"
              initial={{ top: "0%" }}
              animate={{ top: "100%" }}
              transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
            />
          )}

          {/* Corner markers */}
          {isActive && (
            <>
              <div className={`${cornerClass} top-1.5 left-1.5 border-t-2 border-l-2 rounded-tl`} />
              <div className={`${cornerClass} top-1.5 right-1.5 border-t-2 border-r-2 rounded-tr`} />
              <div className={`${cornerClass} bottom-1.5 left-1.5 border-b-2 border-l-2 rounded-bl`} />
              <div className={`${cornerClass} bottom-1.5 right-1.5 border-b-2 border-r-2 rounded-br`} />
            </>
          )}
        </motion.div>
      </div>

      {/* Idle — CTA button */}
      {status === "idle" && (
        <button
          onClick={handleAnalyse}
          className="w-full py-2.5 px-4 rounded-lg text-sm font-medium bg-green-500/15 text-green-300 border border-green-500/35 hover:bg-green-500/25 transition-all duration-200 flex items-center justify-center gap-2"
        >
          <span>🔬</span> Analyse Materials from Image
        </button>
      )}

      {/* Loading */}
      {status === "loading" && (
        <div className="flex flex-col items-center gap-1.5 py-1">
          <motion.p
            className="text-green-400 text-sm font-medium"
            animate={{ opacity: [1, 0.45, 1] }}
            transition={{ duration: 1.3, repeat: Infinity }}
          >
            Scanning image for materials…
          </motion.p>
          <p className="text-slate-500 text-xs">Claude is examining each component</p>
        </div>
      )}

      {/* Error */}
      {status === "error" && (
        <div className="text-center py-1 space-y-1.5">
          <p className="text-red-400 text-xs">{errorMsg}</p>
          <button
            onClick={() => setStatus("idle")}
            className="text-slate-400 text-xs hover:text-slate-200 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {status === "done" && result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.28 }}
            className="space-y-3"
          >
            {/* Header row */}
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-400 font-medium">Detected components</p>
              <span
                className={`text-xs px-2 py-0.5 rounded-full border ${
                  result.confidence === "high"
                    ? "text-green-300 border-green-500/40 bg-green-500/10"
                    : result.confidence === "medium"
                    ? "text-amber-300 border-amber-500/40 bg-amber-500/10"
                    : "text-red-300 border-red-500/40 bg-red-500/10"
                }`}
              >
                {result.confidence} confidence
              </span>
            </div>

            {/* Component bars */}
            {result.components.map((c, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium capitalize">{c.part}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">{c.material}</span>
                    <span className="text-slate-100 font-mono font-semibold w-9 text-right">
                      {c.percentage}%
                    </span>
                  </div>
                </div>
                <div className="w-full h-2 bg-slate-700/60 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${getColor(c.material, i)}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${c.percentage}%` }}
                    transition={{ delay: i * 0.07 + 0.18, duration: 0.55, ease: "easeOut" }}
                  />
                </div>
                {c.reasoning && (
                  <p className="text-slate-600 text-xs italic pl-0.5">{c.reasoning}</p>
                )}
              </motion.div>
            ))}

            {/* Notes */}
            {result.notes && (
              <p className="text-slate-500 text-xs italic border-t border-slate-700/40 pt-2 mt-1">
                {result.notes}
              </p>
            )}

            <button
              onClick={() => setStatus("idle")}
              className="text-slate-500 text-xs hover:text-slate-300 transition-colors"
            >
              Re-analyse
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
