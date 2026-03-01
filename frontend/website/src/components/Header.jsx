import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import useAuth from "../hooks/useAuth";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  // Dynamic navigation based on authentication
  const getNavItems = () => {
    const baseItems = [
      { path: "/", label: "Home", icon: "🏠" },
      { path: "/learn", label: "Learn", icon: "📖" },
      { path: "/predict", label: "Predict", icon: "📊" },
      { path: "/extension", label: "Extension", icon: "🔗" },
    ];

    if (user) {
      // Add admin link for admin users
      if (user.role === "admin") {
        baseItems.push({ path: "/admin", label: "Admin", icon: "⚙️" });
      }
      return baseItems;
    } else {
      // Add login for non-authenticated users
      baseItems.push({ path: "/login", label: "Login", icon: "👤" });
      return baseItems;
    }
  };

  const navItems = getNavItems();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <>
      {/* Logo/Brand */}
      <motion.div
        className="flex items-center gap-3"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg">
          <span className="text-xl">🌿</span>
        </div>
        <h1 className="text-xl font-display font-bold">
          <span className="text-slate-200">Impact</span>{" "}
          <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Tracker</span>
        </h1>
      </motion.div>

      {/* User Greeting & Desktop Navigation */}
      <div className="hidden md:flex items-center gap-6">
        {/* User Greeting */}
        {user && (
          <motion.div
            className="flex items-center gap-3 px-4 py-2 glass-card rounded-lg"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
              <span className="text-white text-sm font-bold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-slate-400">Hello,</span>
              <span className="text-sm font-medium text-slate-200">
                {user.username}
              </span>
            </div>
            {user.role === "admin" && (
              <div className="w-5 h-5 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                <span className="text-white text-xs">👑</span>
              </div>
            )}
          </motion.div>
        )}

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          {navItems.map((item, index) => (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
            >
              <Link
                to={item.path}
                className={`nav-link flex items-center gap-2 ${
                  location.pathname === item.path ? "active" : ""
                }`}
              >
                <span className="text-sm">{item.icon}</span>
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            </motion.div>
          ))}
          
          {/* Logout Button */}
          {user && (
            <motion.button
              onClick={handleLogout}
              className="nav-link flex items-center gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: navItems.length * 0.1 }}
            >
              <span className="text-sm">🚪</span>
              <span className="text-sm font-medium">Logout</span>
            </motion.button>
          )}
        </nav>
      </div>

      {/* Mobile Menu Button */}
      <motion.button
        className="md:hidden w-10 h-10 glass-card flex items-center justify-center rounded-lg"
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="flex flex-col gap-1.5">
          <motion.div
            className="w-5 h-0.5 bg-slate-300 rounded-full"
            animate={{ 
              rotate: isMenuOpen ? 45 : 0, 
              y: isMenuOpen ? 3 : 0,
              originX: 0.5,
              originY: 0.5 
            }}
            transition={{ duration: 0.3 }}
          />
          <motion.div
            className="w-5 h-0.5 bg-slate-300 rounded-full"
            animate={{ opacity: isMenuOpen ? 0 : 1 }}
            transition={{ duration: 0.2 }}
          />
          <motion.div
            className="w-5 h-0.5 bg-slate-300 rounded-full"
            animate={{ 
              rotate: isMenuOpen ? -45 : 0, 
              y: isMenuOpen ? -3 : 0,
              originX: 0.5,
              originY: 0.5 
            }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </motion.button>

      {/* Mobile Navigation Menu */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            className="md:hidden absolute top-full left-0 right-0 mt-2 glass-card p-4"
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.3 }}
          >
            {/* Mobile User Greeting */}
            {user && (
              <motion.div
                className="flex items-center gap-3 p-3 mb-4 bg-slate-800/50 rounded-lg"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
                  <span className="text-white font-bold">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex flex-col flex-1">
                  <span className="text-xs text-slate-400">Hello,</span>
                  <span className="text-sm font-medium text-slate-200">
                    {user.username}
                  </span>
                </div>
                {user.role === "admin" && (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                    <span className="text-white text-sm">👑</span>
                  </div>
                )}
              </motion.div>
            )}

            <nav className="flex flex-col gap-1">
              {navItems.map((item, index) => (
                <motion.div
                  key={item.path}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <Link
                    to={item.path}
                    className={`nav-link flex items-center gap-3 w-full ${
                      location.pathname === item.path ? "active" : ""
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <span>{item.icon}</span>
                    <span className="font-medium">{item.label}</span>
                  </Link>
                </motion.div>
              ))}
              
              {/* Mobile Logout Button */}
              {user && (
                <motion.button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="nav-link flex items-center gap-3 w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: navItems.length * 0.05 }}
                >
                  <span>🚪</span>
                  <span className="font-medium">Logout</span>
                </motion.button>
              )}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
