import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import ModernLayout, { ModernCard, ModernSection, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function LogOnPage() {
  const [username, setUsername]   = useState("");
  const [password, setPassword]   = useState("");
  const [showPass, setShowPass]   = useState(false);
  const [error, setError]         = useState("");
  const [loading, setLoading]     = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed");

      localStorage.setItem("user", JSON.stringify(data.user));
      toast.success(`Welcome back, ${data.user.username}!`);

      if (data.user.role === "admin") navigate("/admin");
      else navigate("/");
    } catch (err) {
      setError(err.message || "Incorrect username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="flex items-center justify-center min-h-[70vh]">
            <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8 items-center">

              {/* ── Left: value prop ── */}
              <motion.div
                initial={{ opacity: 0, x: -24 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                className="hidden md:block space-y-6"
              >
                <div>
                  <h1 className="text-3xl font-display font-bold text-slate-100 mb-2">
                    Your sustainability<br />
                    <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                      dashboard awaits
                    </span>
                  </h1>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    Sign in to unlock your personal scan history, stats, and more.
                  </p>
                </div>

                <div className="space-y-3">
                  {[
                    { icon: "📜", title: "Scan history",     desc: "Every product you've checked, in one place" },
                    { icon: "📊", title: "Personal stats",   desc: "Your CO₂ tracked, grade distribution, top materials" },
                    { icon: "🔬", title: "Impact Explorer",  desc: "Full access to the what-if prediction tool" },
                  ].map(f => (
                    <div key={f.title} className="flex items-start gap-3 p-3 glass-card rounded-xl">
                      <span className="text-xl flex-shrink-0">{f.icon}</span>
                      <div>
                        <p className="text-slate-200 text-sm font-medium">{f.title}</p>
                        <p className="text-slate-500 text-xs mt-0.5">{f.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* ── Right: form ── */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <ModernCard solid>
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg">
                        <span className="text-2xl">🌿</span>
                      </div>
                      <h2 className="text-xl font-display font-semibold text-slate-200">Welcome back</h2>
                      <p className="text-slate-500 text-sm mt-1">Sign in to your Impact Tracker account</p>
                    </div>

                    {/* Inline error */}
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm"
                      >
                        <span>⚠️</span> {error}
                      </motion.div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-4">
                      {/* Username */}
                      <div className="space-y-1.5">
                        <label className="block text-sm font-medium text-slate-300">Username</label>
                        <input
                          type="text"
                          value={username}
                          onChange={e => setUsername(e.target.value)}
                          placeholder="Enter your username"
                          required
                          autoComplete="username"
                          className="w-full px-4 py-2.5 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500/60 transition-colors"
                        />
                      </div>

                      {/* Password */}
                      <div className="space-y-1.5">
                        <label className="block text-sm font-medium text-slate-300">Password</label>
                        <div className="relative">
                          <input
                            type={showPass ? "text" : "password"}
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                            autoComplete="current-password"
                            className="w-full px-4 py-2.5 pr-10 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500/60 transition-colors"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPass(s => !s)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors text-sm"
                            tabIndex={-1}
                          >
                            {showPass ? "🙈" : "👁️"}
                          </button>
                        </div>
                      </div>

                      <ModernButton
                        type="submit"
                        variant="primary"
                        size="lg"
                        className="w-full"
                        loading={loading}
                      >
                        {loading ? "Signing in…" : "Sign In"}
                      </ModernButton>
                    </form>

                    <p className="text-center text-sm text-slate-500">
                      Don't have an account?{" "}
                      <Link to="/signup" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
                        Sign up free
                      </Link>
                    </p>
                  </div>
                </ModernCard>
              </motion.div>
            </div>
          </div>
        ),
      }}
    </ModernLayout>
  );
}
