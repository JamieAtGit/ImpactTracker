import { useState } from "react";
import "./refined.css";

/**
 * 🎯 ML vs DEFRA Comparison Chart - Extension Popup Optimized
 * 
 * Lightweight horizontal bar chart designed for extension popup constraints:
 * - Width: ~400px max
 * - Height: ~150px max  
 * - No external dependencies (no Recharts)
 * - Clean, accessible design
 * - Handles edge cases gracefully
 */

const MLvsDefraChart = ({ result }) => {
  const [showDetails, setShowDetails] = useState(false);
  
  // Extract data from API response
  const attributes = result?.data?.attributes || {};
  const mlScore = attributes.eco_score_ml;
  const defrScore = attributes.eco_score_rule_based;
  const mlConfidence = attributes.eco_score_ml_confidence;
  const methodAgreement = attributes.method_agreement;
  const predictionMethods = attributes.prediction_methods || {};
  
  // Grade to numeric conversion for chart visualization
  const gradeToNumeric = (grade) => {
    const gradeMap = { 'A': 90, 'B': 75, 'C': 60, 'D': 45, 'E': 30, 'F': 15 };
    return gradeMap[grade?.toString().toUpperCase()] || 0;
  };
  
  // Color mapping for grades
  const getGradeColor = (grade) => {
    const colorMap = {
      'A': '#10b981', // green-500
      'B': '#22c55e', // green-400  
      'C': '#eab308', // yellow-500
      'D': '#f59e0b', // amber-500
      'E': '#ef4444', // red-500
      'F': '#dc2626'  // red-600
    };
    return colorMap[grade?.toString().toUpperCase()] || '#6b7280';
  };
  
  const mlNumeric = gradeToNumeric(mlScore);
  const defrNumeric = gradeToNumeric(defrScore);
  const maxValue = Math.max(mlNumeric, defrNumeric, 50); // Ensure minimum chart width
  
  // Handle edge cases
  if (!mlScore && !defrScore) {
    return (
      <div className="ml-defra-chart" style={{ 
        padding: '12px', 
        backgroundColor: '#f9fafb', 
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
          ⚠️ Prediction data not available
        </p>
      </div>
    );
  }
  
  return (
    <div className="ml-defra-chart" style={{ 
      padding: '16px', 
      backgroundColor: '#f9fafb', 
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      marginTop: '16px'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '16px', 
          fontWeight: '600',
          color: '#1f2937'
        }}>
          🤖 AI vs Government Comparison
        </h3>
        
        {/* Agreement indicator */}
        <span style={{
          fontSize: '12px',
          padding: '4px 8px',
          borderRadius: '12px',
          backgroundColor: methodAgreement === 'Yes' ? '#dcfce7' : '#fef3c7',
          color: methodAgreement === 'Yes' ? '#166534' : '#92400e',
          fontWeight: '500'
        }}>
          {methodAgreement === 'Yes' ? '✅ Match' : '⚡ Different'}
        </span>
      </div>
      
      {/* Chart bars */}
      <div style={{ marginBottom: '16px' }}>
        
        {/* ML Prediction Bar */}
        {mlScore && (
          <div style={{ marginBottom: '12px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '4px'
            }}>
              <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                🧠 AI Model
              </span>
              <span style={{ 
                fontSize: '14px', 
                fontWeight: '600',
                color: getGradeColor(mlScore)
              }}>
                Grade {mlScore} {mlConfidence ? `(${mlConfidence}%)` : ''}
              </span>
            </div>
            
            {/* Bar visualization */}
            <div style={{
              width: '100%',
              height: '20px',
              backgroundColor: '#e5e7eb',
              borderRadius: '10px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${(mlNumeric / maxValue) * 100}%`,
                height: '100%',
                backgroundColor: getGradeColor(mlScore),
                borderRadius: '10px',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        )}
        
        {/* DEFRA/Rule-based Bar */}
        {defrScore && (
          <div style={{ marginBottom: '8px' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '4px'
            }}>
              <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                📊 Government Baseline
              </span>
              <span style={{ 
                fontSize: '14px', 
                fontWeight: '600',
                color: getGradeColor(defrScore)
              }}>
                Grade {defrScore} (80%)
              </span>
            </div>
            
            {/* Bar visualization */}
            <div style={{
              width: '100%',
              height: '20px',
              backgroundColor: '#e5e7eb',
              borderRadius: '10px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${(defrNumeric / maxValue) * 100}%`,
                height: '100%',
                backgroundColor: getGradeColor(defrScore),
                borderRadius: '10px',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        )}
      </div>
      
      {/* Toggle details button */}
      <button 
        onClick={() => setShowDetails(!showDetails)}
        style={{
          width: '100%',
          padding: '8px',
          fontSize: '13px',
          backgroundColor: 'transparent',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          cursor: 'pointer',
          color: '#6b7280',
          transition: 'all 0.2s ease'
        }}
        onMouseOver={(e) => {
          e.target.style.backgroundColor = '#f3f4f6';
          e.target.style.color = '#374151';
        }}
        onMouseOut={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.color = '#6b7280';
        }}
      >
        {showDetails ? '▲ Hide Details' : '▼ Show Methodology Details'}
      </button>
      
      {/* Detailed breakdown */}
      {showDetails && (
        <div style={{ 
          marginTop: '12px', 
          padding: '12px',
          backgroundColor: '#ffffff',
          borderRadius: '6px',
          border: '1px solid #e5e7eb',
          fontSize: '12px',
          lineHeight: '1.4'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#374151' }}>🧠 AI Model:</strong>
            <div style={{ color: '#6b7280', marginTop: '2px' }}>
              {predictionMethods.ml_prediction?.method || 'Enhanced XGBoost'}
            </div>
          </div>
          
          <div>
            <strong style={{ color: '#374151' }}>📊 Government Baseline:</strong>
            <div style={{ color: '#6b7280', marginTop: '2px' }}>
              {predictionMethods.rule_based_prediction?.method || 'DEFRA emission factors + heuristic rules'}
            </div>
          </div>
          
          {methodAgreement === 'No' && (
            <div style={{ 
              marginTop: '8px', 
              padding: '8px',
              backgroundColor: '#fef3c7',
              borderRadius: '4px',
              color: '#92400e'
            }}>
              <strong>⚡ Different Results:</strong> AI considers additional factors like brand patterns and material complexity
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MLvsDefraChart;