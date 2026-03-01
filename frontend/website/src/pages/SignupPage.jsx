import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton, ModernInput } from "../components/ModernLayout";
import Header from "../components/Header";
import Footer from "../components/Footer";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function SignupPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    
    try {
      const res = await fetch(`${BASE_URL}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Signup failed");

      navigate("/login");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="flex items-center justify-center min-h-[70vh]">
            <ModernCard className="max-w-md w-full" solid hover>
              <ModernSection title="Create Account" className="text-center">
                <motion.form 
                  onSubmit={handleSignup} 
                  className="space-y-6"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                >
                  <div className="text-center mb-6">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-lg">
                      <span className="text-2xl">🆕</span>
                    </div>
                    <p className="text-slate-400 text-sm">
                      Join Impact Tracker to access your personalized sustainability dashboard
                    </p>
                  </div>

                  <ModernInput
                    label="Username"
                    type="text"
                    placeholder="Choose a unique username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    icon="👤"
                    required
                  />
                  
                  <ModernInput
                    label="Password"
                    type="password"
                    placeholder="Create a secure password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    icon="🔑"
                    required
                  />

                  <ModernInput
                    label="Confirm Password"
                    type="password"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    icon="🔒"
                    required
                    error={error}
                  />
                  
                  <ModernButton 
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="w-full"
                    icon="🚀"
                  >
                    Create Account
                  </ModernButton>
                </motion.form>
                
                <motion.div
                  className="mt-6 text-center"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  <p className="text-sm text-slate-400">
                    Already have an account?{" "}
                    <a 
                      href="/login" 
                      className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium"
                    >
                      Sign in here
                    </a>
                  </p>
                </motion.div>
              </ModernSection>
            </ModernCard>
            
            <Footer />
          </div>
        ),
      }}
    </ModernLayout>
  );
}
