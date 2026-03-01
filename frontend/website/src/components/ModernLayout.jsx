import React from "react";
import { motion } from "framer-motion";

// Ambient Background Component
const AmbientBackground = () => {
  return <div className="ambient-bg" />;
};

// Modern Navigation Component
const ModernNav = ({ children }) => {
  return (
    <motion.header 
      className="fixed top-0 left-0 right-0 z-50 p-4"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="glass-card p-4">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          {children}
        </div>
      </div>
    </motion.header>
  );
};

// Modern Container Component
const ModernContainer = ({ children, className = "" }) => {
  return (
    <motion.div
      className={`relative z-10 min-h-screen pt-24 pb-8 px-4 ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <div className="max-w-7xl mx-auto">
        {children}
      </div>
    </motion.div>
  );
};

// Modern Card Component
const ModernCard = ({ children, className = "", hover = false, solid = false, ...props }) => {
  const cardClass = solid ? "glass-card-solid" : "glass-card";
  const hoverClass = hover ? "card-hover" : "";
  
  return (
    <motion.div
      className={`${cardClass} ${hoverClass} p-6 ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Modern Section Component
const ModernSection = ({ children, title, icon, className = "", delay = 0 }) => {
  return (
    <motion.section
      className={`mb-12 ${className}`}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: "easeOut" }}
    >
      {title && (
        <motion.div
          className="flex items-center gap-3 mb-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: delay + 0.2 }}
        >
          {icon && (
            <span className="status-indicator status-success"></span>
          )}
          <h2 className="text-2xl font-display text-slate-200">
            {title}
          </h2>
        </motion.div>
      )}
      {children}
    </motion.section>
  );
};

// Modern Button Component
const ModernButton = ({ 
  children, 
  variant = "primary", 
  size = "md", 
  loading = false, 
  icon,
  className = "",
  ...props 
}) => {
  const sizeClasses = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3",
    lg: "px-8 py-4 text-lg"
  };

  const buttonClass = `btn-${variant} ${sizeClasses[size]} ${className}`;

  return (
    <motion.button
      className={buttonClass}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      disabled={loading}
      {...props}
    >
      <span className="flex items-center justify-center gap-2">
        {loading ? (
          <div className="loading-spinner"></div>
        ) : (
          icon && <span className="text-sm">{icon}</span>
        )}
        <span>{children}</span>
      </span>
    </motion.button>
  );
};

// Modern Input Component
const ModernInput = ({ 
  label, 
  icon, 
  error, 
  className = "", 
  ...props 
}) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-slate-300">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400">
            {icon}
          </div>
        )}
        <motion.input
          className={`input-modern ${icon ? 'pl-10' : ''} ${error ? 'border-red-500' : ''}`}
          whileFocus={{ scale: 1.01 }}
          transition={{ duration: 0.2 }}
          {...props}
        />
      </div>
      {error && (
        <motion.p 
          className="text-sm text-red-400"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {error}
        </motion.p>
      )}
    </div>
  );
};

// Modern Badge Component
const ModernBadge = ({ children, variant = "default", size = "sm" }) => {
  const variants = {
    default: "bg-slate-700 text-slate-300",
    success: "bg-green-900/50 text-green-400 border border-green-500/30",
    warning: "bg-amber-900/50 text-amber-400 border border-amber-500/30",
    error: "bg-red-900/50 text-red-400 border border-red-500/30",
    info: "bg-blue-900/50 text-blue-400 border border-blue-500/30"
  };

  const sizes = {
    sm: "px-2 py-1 text-xs",
    md: "px-3 py-1.5 text-sm"
  };

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  );
};

// Main Layout Component
export default function ModernLayout({ children, showNav = true }) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <AmbientBackground />
      {showNav && (
        <ModernNav>
          {children?.nav}
        </ModernNav>
      )}
      <ModernContainer>
        {children?.content || children}
      </ModernContainer>
    </div>
  );
}

export { 
  ModernNav, 
  ModernContainer, 
  ModernCard, 
  ModernSection, 
  ModernButton, 
  ModernInput, 
  ModernBadge 
};