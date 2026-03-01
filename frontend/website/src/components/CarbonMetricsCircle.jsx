import React from "react";
import { motion } from "framer-motion";

function normalizeEcoScore(score) {
  const scale = ["F", "E", "D", "C", "B", "A", "A+"];
  const index = scale.indexOf(score?.toUpperCase());
  return index >= 0 ? ((index + 1) / scale.length) * 100 : 0;
}

// Custom Circular Progress Component
const FuturisticCircularProgress = ({ value, text, label, color, icon }) => {
  const circumference = 2 * Math.PI * 45; // radius of 45
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <motion.div 
      className="flex flex-col items-center"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.1 }}
    >
      <div className="relative w-28 h-28">
        {/* Background Circle */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="8"
            fill="none"
            className="opacity-50"
          />
          {/* Progress Circle */}
          <motion.circle
            cx="50"
            cy="50"
            r="45"
            stroke={color}
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
            style={{
              filter: `drop-shadow(0 0 8px ${color})`,
            }}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, delay: 0.5, ease: "easeOut" }}
          />
        </svg>
        
        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg mb-1">{icon}</span>
          <span 
            className="text-xs font-futuristic font-bold text-center leading-tight"
            style={{ color }}
          >
            {text}
          </span>
        </div>
      </div>
      
      {/* Label */}
      <p className="mt-3 text-sm font-futuristic text-gray-300 text-center uppercase tracking-wide">
        {label}
      </p>
    </motion.div>
  );
};

export default function CarbonMetricsCircle({
  carbonKg,
  ecoScore,
  recyclability,
  recyclabilityPercentage,
  treesToOffset,
}) {
  const carbonPct = Math.min((carbonKg / 25) * 100, 100);
  const treePct = Math.min((treesToOffset / 10) * 100, 100);
  
  // Use provided percentage if available, otherwise fallback to hardcoded values
  const recyclePct = recyclabilityPercentage || 
    (typeof recyclability === "number"
      ? recyclability
      : recyclability === "High"
      ? 90
      : recyclability === "Medium"
      ? 60
      : 30);
  
  const ecoPct = normalizeEcoScore(ecoScore);

  const metrics = [
    { 
      label: "CO₂ Emissions", 
      value: carbonPct, 
      text: `${carbonKg?.toFixed(1) ?? "0"} kg`,
      color: "#ff6b6b",
      icon: "💨"
    },
    { 
      label: "Recyclability", 
      value: recyclePct, 
      text: `${recyclePct.toFixed(0)}%`,
      color: "#00ff00",
      icon: "♻️"
    },
    { 
      label: "Eco Score", 
      value: ecoPct, 
      text: ecoScore ?? "N/A",
      color: "#00ffff",
      icon: "🌍"
    },
    { 
      label: "Trees Needed", 
      value: treePct, 
      text: `${treesToOffset ?? 0}`,
      color: "#ffff00",
      icon: "🌳"
    },
  ];

  return (
    <motion.div 
      className="glass-card-solid p-6 rounded-lg"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="status-indicator status-warning"></div>
          <h4 className="text-lg font-display text-slate-200">
            Impact Metrics
          </h4>
        </div>
        
        {/* Info Tooltip */}
        <div className="relative group cursor-pointer">
          <motion.div
            className="w-8 h-8 glass-card rounded-full flex items-center justify-center"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <span className="text-sm text-slate-400">ℹ️</span>
          </motion.div>
          
          <div className="absolute right-0 top-10 w-72 text-xs text-slate-300 glass-card-solid border border-blue-500/30 rounded-lg p-4 hidden group-hover:block z-10">
            <p className="font-medium text-blue-400 mb-2">Metric Analysis:</p>
            <ul className="space-y-1 text-slate-400">
              <li><strong className="text-red-400">CO₂:</strong> Normalized to 25kg cap</li>
              <li><strong className="text-green-400">Recyclability:</strong> High=90%, Medium=60%, Low=30%</li>
              <li><strong className="text-cyan-400">Eco Score:</strong> F(0%) → A+(100%)</li>
              <li><strong className="text-amber-400">Trees:</strong> Carbon offset requirement</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => (
          <FuturisticCircularProgress
            key={index}
            value={metric.value}
            text={metric.text}
            label={metric.label}
            color={metric.color}
            icon={metric.icon}
          />
        ))}
      </div>
      
      {/* Summary Bar */}
      <motion.div
        className="mt-6 p-4 glass-card rounded-lg"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1 }}
      >
        <div className="flex items-center justify-center gap-4 text-sm">
          <span className="text-slate-400">Overall Impact Score:</span>
          <span className="text-cyan-400 font-bold">
            {((carbonPct + recyclePct + ecoPct + treePct) / 4).toFixed(0)}% Efficiency
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}
