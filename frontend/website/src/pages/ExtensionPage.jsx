import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";
import Footer from "../components/Footer";

const FAQ = [
  {
    q: "Which browser does the extension support?",
    a: "Currently Chrome and Chromium-based browsers (Edge, Brave). Because it's a research prototype it requires manual installation via Developer Mode — it isn't on the Chrome Web Store yet.",
  },
  {
    q: "Why do I need Developer Mode?",
    a: "Publishing to the Chrome Web Store requires a Google developer account. For this research prototype, loading unpacked is the quickest way to try it. The process takes under 60 seconds and doesn't affect your other extensions.",
  },
  {
    q: "What data does the extension send?",
    a: "When you view an Amazon product page, the extension sends the product title, detected material, and weight to the Impact Tracker API. No personal data, browsing history, or Amazon account information is ever transmitted.",
  },
  {
    q: "Does it work on every Amazon product?",
    a: "It works best on products with clear material and weight information in the listing. The AI makes its best prediction from the available data — confidence scores tell you how certain the model is.",
  },
];

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-slate-700/50 last:border-0">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between py-4 text-left text-slate-200 hover:text-slate-100 transition-colors"
      >
        <span className="text-sm font-medium pr-4">{q}</span>
        <motion.span
          animate={{ rotate: open ? 45 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-slate-500 text-lg flex-shrink-0"
        >
          +
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <p className="text-slate-400 text-sm leading-relaxed pb-4">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ExtensionPage() {
  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-12">

            {/* ── Hero ── */}
            <ModernSection className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7 }}
                className="space-y-5"
              >
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-2xl mb-2 shadow-lg shadow-cyan-500/20">
                  <span className="text-3xl">🧩</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight">
                  <span className="text-slate-100">Shop smarter with the</span>
                  <br />
                  <span className="bg-gradient-to-r from-green-400 via-cyan-500 to-blue-400 bg-clip-text text-transparent">
                    Impact Tracker Extension
                  </span>
                </h1>
                <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
                  The extension overlays an environmental grade directly onto Amazon product pages —
                  so you can see a product's eco impact before you add it to your cart.
                </p>

                <div className="flex flex-wrap justify-center gap-3 pt-2">
                  <span className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-full px-3 py-1">Chrome</span>
                  <span className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-full px-3 py-1">Edge</span>
                  <span className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-full px-3 py-1">Brave</span>
                  <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs rounded-full px-3 py-1">Free</span>
                </div>
              </motion.div>
            </ModernSection>

            {/* ── Download + install ── */}
            <div className="grid md:grid-cols-2 gap-8">
              <ModernCard solid>
                <div className="space-y-5">
                  <h2 className="text-xl font-display text-slate-200 flex items-center gap-2">
                    ⬇️ Download & Install
                  </h2>
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <ModernButton
                      variant="accent"
                      size="lg"
                      icon="⬇️"
                      className="w-full mb-5"
                      onClick={() => window.open(`${import.meta.env.VITE_API_BASE_URL}/static/my-extension.zip`, "_blank")}
                    >
                      Download Extension (.zip)
                    </ModernButton>
                  </motion.div>

                  <ol className="space-y-3">
                    {[
                      { step: 1, text: <>Unzip the downloaded file to a folder on your computer.</> },
                      { step: 2, text: <>Open Chrome and go to <code className="bg-slate-700 px-1.5 py-0.5 rounded text-cyan-400 text-xs">chrome://extensions</code>.</> },
                      { step: 3, text: <>Toggle <strong className="text-slate-200">Developer mode</strong> on (top-right switch).</> },
                      { step: 4, text: <>Click <strong className="text-slate-200">Load unpacked</strong> and select the unzipped folder.</> },
                      { step: 5, text: <>Visit any Amazon product page — the impact badge appears automatically. ✅</> },
                    ].map(({ step, text }) => (
                      <li key={step} className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-slate-900 text-xs font-bold rounded-full flex items-center justify-center mt-0.5">
                          {step}
                        </span>
                        <span className="text-slate-300 text-sm leading-relaxed">{text}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </ModernCard>

              <ModernCard solid>
                <div className="space-y-5">
                  <h2 className="text-xl font-display text-slate-200 flex items-center gap-2">
                    ✨ What it does
                  </h2>
                  <ul className="space-y-3">
                    {[
                      { icon: "🏷️", text: "Overlays an A–F eco grade badge on every Amazon product page you visit" },
                      { icon: "🧠", text: "Grade is predicted live by the same XGBoost model powering the main site" },
                      { icon: "📦", text: "Detects material, weight and origin from the product listing automatically" },
                      { icon: "📊", text: "Shows confidence level so you know how certain the prediction is" },
                      { icon: "🔒", text: "No account required — works instantly after installation" },
                      { icon: "⚡", text: "Lightweight: only activates on amazon.co.uk product pages" },
                    ].map(({ icon, text }) => (
                      <li key={text} className="flex items-start gap-3">
                        <span className="text-lg flex-shrink-0">{icon}</span>
                        <span className="text-slate-300 text-sm leading-relaxed">{text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </ModernCard>
            </div>

            {/* ── Live mockup ── */}
            <ModernSection title="See it in action" icon delay={0.3}>
              <ModernCard solid className="p-6 md:p-8">
                {/* Fake browser chrome */}
                <div className="rounded-xl overflow-hidden border border-slate-600/60 shadow-2xl">
                  {/* Browser bar */}
                  <div className="bg-slate-800 px-4 py-2.5 flex items-center gap-3 border-b border-slate-700">
                    <div className="flex gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-red-500/70" />
                      <div className="w-3 h-3 rounded-full bg-amber-500/70" />
                      <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
                    </div>
                    <div className="flex-1 bg-slate-700/60 rounded px-3 py-1 text-slate-400 text-xs font-mono truncate">
                      amazon.co.uk/dp/B09XS7JWHH
                    </div>
                    <div className="flex items-center gap-1.5 text-cyan-400 text-xs font-medium">
                      <div className="w-5 h-5 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-[9px] font-bold">IT</span>
                      </div>
                      Active
                    </div>
                  </div>

                  {/* Page content */}
                  <div className="bg-white p-5 md:p-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                      {/* Product image + overlay badge */}
                      <div className="relative">
                        <div className="bg-slate-100 rounded-xl flex items-center justify-center h-56">
                          <div className="text-center">
                            <div className="w-28 h-28 bg-slate-200 rounded-xl mx-auto mb-3 flex items-center justify-center">
                              <span className="text-5xl">🎧</span>
                            </div>
                            <p className="text-slate-500 text-xs">Sony WH-1000XM5</p>
                          </div>
                        </div>

                        {/* Extension overlay — matches real output format */}
                        <motion.div
                          initial={{ opacity: 0, scale: 0.88, y: 8 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          transition={{ duration: 0.5, delay: 1.2 }}
                          className="absolute top-3 right-3 bg-slate-900 rounded-xl p-4 shadow-2xl border border-cyan-500/25 w-52"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-cyan-400 text-xs font-semibold">Impact Tracker</span>
                            <span className="text-slate-500 text-xs">🌍</span>
                          </div>
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-amber-500/15 border border-amber-500/40 flex items-center justify-center">
                              <span className="text-amber-400 font-black text-lg">C</span>
                            </div>
                            <div>
                              <p className="text-slate-200 text-xs font-medium">Eco Grade</p>
                              <p className="text-slate-500 text-xs">74% confidence</p>
                            </div>
                          </div>
                          <div className="space-y-1.5 text-xs border-t border-slate-700/60 pt-2.5">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Material</span>
                              <span className="text-slate-300">Mixed Plastic</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Est. CO₂</span>
                              <span className="text-orange-400 font-mono">4.1 kg</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Origin</span>
                              <span className="text-slate-300">China</span>
                            </div>
                          </div>
                        </motion.div>
                      </div>

                      {/* Product details */}
                      <div className="space-y-3">
                        <h3 className="text-lg font-bold text-slate-900 leading-snug">
                          Sony WH-1000XM5 Wireless Noise Cancelling Headphones
                        </h3>
                        <div className="flex items-center gap-2">
                          <span className="text-orange-400 text-sm">★★★★☆</span>
                          <span className="text-blue-600 text-xs">34,291 ratings</span>
                        </div>
                        <p className="text-2xl font-bold text-slate-900">£329.00</p>
                        <div className="space-y-1.5 text-sm text-slate-700">
                          <div className="flex gap-2">
                            <span className="text-slate-500">Colour:</span>
                            <span>Black</span>
                          </div>
                          <div className="flex gap-2 items-center">
                            <span className="text-slate-500">Material:</span>
                            <span>Mixed Plastic</span>
                            <motion.span
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: 1.8 }}
                              className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full border border-amber-200"
                            >
                              Grade C
                            </motion.span>
                          </div>
                          <div className="flex gap-2">
                            <span className="text-slate-500">Weight:</span>
                            <span>250 g</span>
                          </div>
                        </div>
                        <button className="mt-2 bg-orange-400 text-white px-6 py-2.5 rounded-lg text-sm font-medium">
                          Add to Basket
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <p className="text-slate-500 text-xs text-center mt-4">
                  Simulated mockup — illustrates how the extension overlay appears on a real Amazon product page.
                  Grades, CO₂ and confidence values are predicted live by the ML model.
                </p>
              </ModernCard>
            </ModernSection>

            {/* ── How it works (light) ── */}
            <ModernSection title="How it works" icon delay={0.2}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    icon: "🔍",
                    step: "1",
                    title: "Detects the product",
                    desc: "When you open an Amazon product page, the extension reads the title, listed material, and weight from the page.",
                  },
                  {
                    icon: "🧠",
                    step: "2",
                    title: "Calls the AI model",
                    desc: "That data is sent to the Impact Tracker API, which runs it through the XGBoost classifier — the same model used on this website.",
                  },
                  {
                    icon: "🏷️",
                    step: "3",
                    title: "Displays the grade",
                    desc: "An A–F badge appears directly on the page with a confidence score, estimated CO₂, and origin country — no extra clicks needed.",
                  },
                ].map((s, i) => (
                  <motion.div
                    key={s.step}
                    initial={{ opacity: 0, y: 14 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="glass-card p-5 rounded-xl relative"
                  >
                    <div className="absolute top-4 right-4 text-slate-700 font-black text-3xl font-mono select-none">
                      {s.step}
                    </div>
                    <div className="text-2xl mb-3">{s.icon}</div>
                    <h3 className="text-slate-200 font-semibold mb-1.5">{s.title}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed">{s.desc}</p>
                  </motion.div>
                ))}
              </div>
            </ModernSection>

            {/* ── FAQ ── */}
            <ModernSection title="Common questions" icon delay={0.3}>
              <ModernCard solid>
                {FAQ.map(item => (
                  <FaqItem key={item.q} {...item} />
                ))}
              </ModernCard>
            </ModernSection>

            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
