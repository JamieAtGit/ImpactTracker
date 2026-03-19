import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STORAGE_KEY = "impact_basket";

function loadBasket() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); }
  catch { return []; }
}

function saveBasket(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

const GRADE_COLOURS = {
  "A+": "text-emerald-400", "A": "text-green-400", "B": "text-cyan-400",
  "C": "text-yellow-400",   "D": "text-amber-400", "E": "text-orange-400", "F": "text-red-400",
};

export default function CarbonBasket() {
  const [open, setOpen]   = useState(false);
  const [items, setItems] = useState(loadBasket);

  useEffect(() => {
    function handler(e) {
      setItems(prev => {
        const next = [...prev, { ...e.detail, id: Date.now() }];
        saveBasket(next);
        return next;
      });
    }
    window.addEventListener("basket:add", handler);
    return () => window.removeEventListener("basket:add", handler);
  }, []);

  function remove(id) {
    setItems(prev => {
      const next = prev.filter(i => i.id !== id);
      saveBasket(next);
      return next;
    });
  }

  function clear() {
    setItems([]);
    saveBasket([]);
  }

  const totalCo2 = items.reduce((s, i) => s + (parseFloat(i.co2) || 0), 0);

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-emerald-600 hover:bg-emerald-500 shadow-xl flex items-center justify-center transition-colors"
        title="Carbon Basket"
      >
        <span className="text-2xl">🧺</span>
        {items.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
            {items.length}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 bg-black/60 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />

            {/* Drawer */}
            <motion.div
              className="fixed right-0 top-0 h-full w-full max-w-sm bg-slate-900 border-l border-slate-700 z-50 flex flex-col"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 260 }}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-slate-700">
                <div>
                  <h3 className="text-lg font-display font-semibold text-slate-200">Carbon Basket</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {items.length} product{items.length !== 1 ? "s" : ""} tracked
                  </p>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-800 text-slate-400 text-lg"
                >
                  ✕
                </button>
              </div>

              {/* Item list */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {items.length === 0 ? (
                  <div className="text-center text-slate-500 py-16">
                    <p className="text-5xl mb-4">🧺</p>
                    <p className="text-sm">No products tracked yet.</p>
                    <p className="text-xs mt-1 text-slate-600">
                      Analyse a product and click "Add to Basket".
                    </p>
                  </div>
                ) : (
                  items.map(item => (
                    <motion.div
                      key={item.id}
                      className="p-3 rounded-lg bg-slate-800/60 border border-slate-700 flex items-start gap-3"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-200 leading-snug line-clamp-2">
                          {item.title || "Unknown product"}
                        </p>
                        <div className="flex items-center gap-3 mt-1.5">
                          <span className={`text-xs font-bold ${GRADE_COLOURS[item.grade] || "text-slate-400"}`}>
                            Grade {item.grade}
                          </span>
                          <span className="text-xs text-red-400">
                            {parseFloat(item.co2).toFixed(3)} kg CO₂
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => remove(item.id)}
                        className="text-slate-600 hover:text-red-400 text-xl flex-shrink-0 leading-none"
                      >
                        ×
                      </button>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Footer totals */}
              {items.length > 0 && (
                <div className="p-5 border-t border-slate-700 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Total carbon footprint</span>
                    <span className="text-lg font-bold text-red-400">{totalCo2.toFixed(3)} kg CO₂</span>
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div>≈ {(totalCo2 / 0.21).toFixed(1)} km driven (average car)</div>
                    <div>≈ {(totalCo2 * 50).toFixed(0)} smartphone charges</div>
                  </div>
                  <button
                    onClick={clear}
                    className="w-full py-2 rounded-lg text-xs text-slate-500 hover:text-red-400 border border-slate-700 hover:border-red-500/50 transition-colors"
                  >
                    Clear basket
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
