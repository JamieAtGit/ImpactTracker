import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// Custom Tooltip Component matching design system
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const value = parseFloat(data.value).toFixed(0);
    const grade = data.payload.grade;
    const confidence = data.payload.confidence;
    const isML = label === "AI Prediction";
    
    return (
      <motion.div 
        className="glass-card p-4 border border-slate-600/50 min-w-48"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        <div className="text-center space-y-2">
          <p className="text-sm font-medium text-slate-200">{label}</p>
          <div className="text-2xl font-bold text-cyan-300">
            Grade {grade}
          </div>
          <div className="text-sm text-slate-400">
            Score: {value}/100
          </div>
          <div className="text-xs text-green-400 font-medium">
            Confidence: {confidence}
          </div>
          {data.payload.methodology && (
            <p className="text-xs text-slate-400 leading-tight">
              {data.payload.methodology}
            </p>
          )}
        </div>
      </motion.div>
    );
  }
  return null;
};

const GRADE_ORDER = ['F', 'E', 'D', 'C', 'B', 'A', 'A+'];

function gradeIndex(grade) {
  return GRADE_ORDER.indexOf(grade?.toString().toUpperCase());
}

function gradeDifference(standardGrade, mlGrade) {
  const si = gradeIndex(standardGrade);
  const mi = gradeIndex(mlGrade);
  if (si < 0 || mi < 0) return null;
  return si - mi; // positive = standard is higher (more optimistic)
}

export default function MLvsDEFRAChart({ showML, result }) {
  const [animationKey, setAnimationKey] = useState(0);

  // Extract data from result object
  const attributes = result?.attributes || {};
  const mlScore = attributes.eco_score_ml;
  const defrScore = attributes.eco_score_rule_based;
  const mlConfidence = attributes.eco_score_ml_confidence;
  const methodAgreement = attributes.method_agreement;
  const predictionMethods = attributes.prediction_methods || {};

  // Grade to numeric conversion for chart visualization
  const gradeToNumeric = (grade) => {
    const gradeMap = { 'A+': 100, 'A': 90, 'B': 75, 'C': 60, 'D': 45, 'E': 30, 'F': 15 };
    return gradeMap[grade?.toString().toUpperCase()] ?? 0;
  };
  
  // Color mapping for grades
  const getGradeColor = (grade) => {
    const colorMap = {
      'A+': '#06d6a0', // teal - best
      'A': '#10b981',  // green-500
      'B': '#22c55e',  // green-400
      'C': '#eab308',  // yellow-500
      'D': '#f59e0b',  // amber-500
      'E': '#ef4444',  // red-500
      'F': '#dc2626'   // red-600
    };
    return colorMap[grade?.toString().toUpperCase()] || '#6b7280';
  };

  // Memoized chart data with enhanced validation
  const chartData = useMemo(() => {
    const data = [];
    
    const mlNumeric = gradeToNumeric(mlScore);
    const defrNumeric = gradeToNumeric(defrScore);
    
    if (defrScore && !showML) {
      data.push({ 
        name: "Standard Method", 
        value: defrNumeric,
        grade: defrScore,
        color: getGradeColor(defrScore),
        methodology: "Traditional calculation using government emission factors",
        confidence: "80%"
      });
    }
    
    if (mlScore) {
      data.push({ 
        name: "AI Prediction", 
        value: mlNumeric,
        grade: mlScore,
        color: getGradeColor(mlScore),
        methodology: "XGBoost ML model with 11 features",
        confidence: mlConfidence ? `${mlConfidence}%` : "N/A"
      });
    }
    
    return data;
  }, [mlScore, defrScore, showML, mlConfidence]);

  // Trigger re-animation on data change
  useEffect(() => {
    setAnimationKey(prev => prev + 1);
  }, [mlScore, defrScore, showML]);

  // Error handling for missing data
  if (chartData.length === 0) {
    return (
      <motion.div 
        className="glass-card p-6 mt-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="text-center">
          <div className="text-slate-400 mb-2 text-2xl">⚠️</div>
          <p className="text-slate-400 text-sm">Carbon emission data unavailable</p>
          <p className="text-slate-500 text-xs mt-1">Please check your product analysis</p>
        </div>
      </motion.div>
    );
  }

  // Grade difference between methods (positive = standard more optimistic than AI)
  const diff = !showML ? gradeDifference(defrScore, mlScore) : null;

  return (
    <motion.div 
      className="glass-card p-6 mt-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header with enhanced typography */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <h3 className="text-xl font-display text-slate-200">
            📊 Methodology Comparison
          </h3>
          {diff !== null && diff === 0 && (
            <div className="px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
              ✓ Methods agree
            </div>
          )}
          {diff !== null && diff !== 0 && (
            <div className="px-3 py-1 rounded-full text-xs font-medium bg-slate-700/50 text-slate-300 border border-slate-500/30">
              {Math.abs(diff) === 1 ? "1 grade apart" : `${Math.abs(diff)} grades apart`}
            </div>
          )}
        </div>
        <p className="text-sm text-slate-400">
          Both methods predict an eco <span className="text-slate-300 font-medium">grade (A–F)</span>.
          The CO₂ kg figure shown above is always <span className="text-amber-300 font-medium">formula-based</span> —
          the ML model classifies grade directly from product features without computing a CO₂ value.
        </p>
      </div>

      {/* Enhanced Horizontal Bar Chart */}
      <div className="mb-6" style={{ height: showML ? "140px" : "180px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            key={animationKey}
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 100, left: 10, bottom: 10 }}
            barCategoryGap="25%"
          >
            <XAxis 
              type="number" 
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickFormatter={(value) => `${value}/100`}
              domain={[0, 100]}
            />
            <YAxis 
              type="category" 
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#cbd5e1', fontSize: 14, fontWeight: 500 }}
              width={120}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <Bar 
              dataKey="value" 
              radius={[0, 12, 12, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color}
                  stroke={entry.name === "AI Prediction" ? "#06d6a0" : "#64748b"}
                  strokeWidth={2}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Enhanced insights section */}
      <div className="space-y-4 pt-4 border-t border-slate-600/30">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-slate-400">AI Model Score:</span>
            <span className="text-lg font-bold text-cyan-300">{mlScore || "N/A"}</span>
          </div>

          {!showML && defrScore && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">Standard Method:</span>
              <span className="text-lg font-bold text-blue-300">{defrScore}</span>
            </div>
          )}
        </div>

        {/* Grade comparison insight */}
        {diff !== null && !showML && (
          <motion.div
            className="flex items-center gap-3 p-4 rounded-lg border bg-slate-800/40 border-slate-600/30"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <span style={{ fontSize: "1.2em" }}>
              {diff === 0 ? "✅" : diff > 0 ? "🔍" : "🌱"}
            </span>
            <div>
              {diff === 0 ? (
                <>
                  <p className="text-sm text-slate-300 font-medium">Both methods give the same grade</p>
                  <p className="text-xs text-slate-400 mt-1">The rule-based formula and ML model agree on this product's impact</p>
                </>
              ) : diff > 0 ? (
                <>
                  <p className="text-sm text-slate-300 font-medium">
                    Standard method rates this <span className="font-bold text-blue-300">{Math.abs(diff) === 1 ? "one grade" : `${Math.abs(diff)} grades`} higher</span> than the AI model
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    The rule-based formula is more optimistic — the ML model may account for factors the simple weight × distance formula misses
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm text-slate-300 font-medium">
                    AI model rates this <span className="font-bold text-cyan-300">{Math.abs(diff) === 1 ? "one grade" : `${Math.abs(diff)} grades`} higher</span> than the standard method
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    The ML model is more optimistic — it may be recognising patterns associated with lower-impact products
                  </p>
                </>
              )}
            </div>
          </motion.div>
        )}

        {/* Methodology note for single model view */}
        {showML && (
          <div className="text-sm text-slate-400 text-center p-3 bg-slate-800/30 rounded-lg">
            💡 Toggle comparison mode to see ML grade vs formula-derived grade side by side
          </div>
        )}
      </div>
    </motion.div>
  );
}
