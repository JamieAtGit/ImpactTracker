import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import ModernLayout, { ModernCard, ModernButton } from "../components/ModernLayout";
import Header from "../components/Header";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

function getPasswordStrength(pwd) {
  if (!pwd) return null;
  if (pwd.length < 8) return { label: "Too short", width: "15%", bar: "bg-red-500",    text: "text-red-400"     };
  const checks = [pwd.length >= 10, /[A-Z]/.test(pwd), /[0-9]/.test(pwd), /[^a-zA-Z0-9]/.test(pwd)];
  const score = checks.filter(Boolean).length;
  if (score <= 1) return { label: "Weak",   width: "30%",  bar: "bg-red-400",     text: "text-red-400"     };
  if (score === 2) return { label: "Fair",   width: "55%",  bar: "bg-amber-400",   text: "text-amber-400"   };
  if (score === 3) return { label: "Good",   width: "78%",  bar: "bg-cyan-400",    text: "text-cyan-400"    };
  return              { label: "Strong", width: "100%", bar: "bg-emerald-400",  text: "text-emerald-400" };
}

export default function SignupPage() {
  const [username,        setUsername]        = useState("");
  const [email,           setEmail]           = useState("");
  const [password,        setPassword]        = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass,        setShowPass]        = useState(false);
  const [error,           setError]           = useState("");
  const [loading,         setLoading]         = useState(false);
  const navigate = useNavigate();

  const strength = getPasswordStrength(password);
  const passwordsMatch = confirmPassword === "" || password === confirmPassword;

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (!/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
      setError("Password must contain at least one uppercase letter and one number.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email: email || undefined, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Signup failed");

      toast.success("Account created! Please sign in.");
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="flex items-center justify-center min-h-[70vh] py-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="w-full max-w-md"
            >
              <ModernCard solid>
                <div className="space-y-6">
                  <div className="text-center">
                    <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-lg">
                      <span className="text-2xl">🌿</span>
                    </div>
                    <h2 className="text-xl font-display font-semibold text-slate-200">Create your account</h2>
                    <p className="text-slate-500 text-sm mt-1">Track your environmental impact for free</p>
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

                  <form onSubmit={handleSignup} className="space-y-4">
                    {/* Username */}
                    <div className="space-y-1.5">
                      <label className="block text-sm font-medium text-slate-300">Username</label>
                      <input
                        type="text"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        placeholder="Choose a username"
                        required
                        autoComplete="username"
                        className="w-full px-4 py-2.5 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500/60 transition-colors"
                      />
                    </div>

                    {/* Email (optional) */}
                    <div className="space-y-1.5">
                      <label className="block text-sm font-medium text-slate-300">
                        Email <span className="text-slate-600 font-normal">(optional)</span>
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        autoComplete="email"
                        className="w-full px-4 py-2.5 bg-slate-800/60 border border-slate-600/50 rounded-lg text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500/60 transition-colors"
                      />
                      <p className="text-slate-600 text-xs">Used only for account recovery</p>
                    </div>

                    {/* Password */}
                    <div className="space-y-1.5">
                      <label className="block text-sm font-medium text-slate-300">Password</label>
                      <div className="relative">
                        <input
                          type={showPass ? "text" : "password"}
                          value={password}
                          onChange={e => setPassword(e.target.value)}
                          placeholder="Create a password"
                          required
                          autoComplete="new-password"
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

                      {/* Password strength meter */}
                      {strength && (
                        <div className="space-y-1 mt-1.5">
                          <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
                            <motion.div
                              className={`h-full rounded-full ${strength.bar}`}
                              initial={{ width: 0 }}
                              animate={{ width: strength.width }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          <p className={`text-xs ${strength.text}`}>{strength.label}</p>
                        </div>
                      )}
                    </div>

                    {/* Confirm password */}
                    <div className="space-y-1.5">
                      <label className="block text-sm font-medium text-slate-300">Confirm Password</label>
                      <input
                        type={showPass ? "text" : "password"}
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        placeholder="Repeat your password"
                        required
                        autoComplete="new-password"
                        className={`w-full px-4 py-2.5 bg-slate-800/60 border rounded-lg text-slate-200 placeholder-slate-500 text-sm focus:outline-none transition-colors ${
                          !passwordsMatch
                            ? "border-red-500/60 focus:border-red-500/60"
                            : confirmPassword && "border-emerald-500/50 focus:border-emerald-500/60"
                              || "border-slate-600/50 focus:border-cyan-500/60"
                        }`}
                      />
                      {!passwordsMatch && (
                        <p className="text-red-400 text-xs">Passwords don't match</p>
                      )}
                    </div>

                    <ModernButton
                      type="submit"
                      variant="primary"
                      size="lg"
                      className="w-full"
                      loading={loading}
                      disabled={!passwordsMatch || loading}
                    >
                      {loading ? "Creating account…" : "Create Account"}
                    </ModernButton>
                  </form>

                  <p className="text-center text-sm text-slate-500">
                    Already have an account?{" "}
                    <Link to="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
                      Sign in
                    </Link>
                  </p>
                </div>
              </ModernCard>
            </motion.div>
          </div>
        ),
      }}
    </ModernLayout>
  );
}
