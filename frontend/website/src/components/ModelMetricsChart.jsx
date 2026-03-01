import React, { useEffect, useState } from "react";
const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function ModelMetricsChart() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE_URL}/all-model-metrics`)
      .then((res) => res.json())
      .then((data) => {
        if (
          data.error ||
          !data.random_forest ||
          !data.xgboost
        ) {
          setError(true);
        } else {
          setMetrics(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch model metrics:", err);
        setError(true);
        setLoading(false);
      });
  }, []);

  if (loading) return <p className="text-sm text-slate-400 text-center">Loading model performance...</p>;
  if (error) return <p className="text-red-400 text-sm text-center">❌ Failed to load model metrics.</p>;
  if (!metrics) return <p className="text-sm text-slate-400 text-center">No metrics available.</p>;

  const rf = metrics.random_forest;
  const xgb = metrics.xgboost;

  return (
    <div className="p-6">
      <h3 className="text-2xl font-semibold mb-4 text-slate-200">📈 Model Comparison</h3>

      <table className="table-auto w-full text-sm mb-6 text-slate-300">
        <thead>
          <tr className="border-b border-slate-600">
            <th className="text-left py-2 text-slate-200">Metric</th>
            <th className="text-left py-2 text-slate-200">Random Forest</th>
            <th className="text-left py-2 text-slate-200">XGBoost</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-slate-700">
            <td className="py-2">Accuracy</td>
            <td className="py-2">{(rf.accuracy * 100).toFixed(2)}%</td>
            <td className="py-2">{(xgb.accuracy * 100).toFixed(2)}%</td>
          </tr>
          <tr className="border-b border-slate-700">
            <td className="py-2">F1 Score</td>
            <td className="py-2">{(rf.f1_score * 100).toFixed(2)}%</td>
            <td className="py-2">{(xgb.f1_score * 100).toFixed(2)}%</td>
          </tr>
        </tbody>
      </table>

      <h4 className="text-lg font-medium mb-2 text-slate-200">🧪 Random Forest Confusion Matrix</h4>
      <div className="overflow-x-auto mb-8">
        <table className="table-auto text-sm border border-slate-600 rounded-lg overflow-hidden">
          <thead>
            <tr>
              <th className="p-2 border-r border-slate-600 bg-slate-700 text-slate-200">True ↓ / Pred →</th>
              {rf.labels.map((label, idx) => (
                <th key={idx} className="p-2 border-r border-slate-600 bg-slate-700 text-slate-200">{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rf.confusion_matrix.map((row, i) => (
              <tr key={i}>
                <td className="p-2 border-r border-slate-600 bg-slate-800 text-slate-200 font-medium">{rf.labels[i]}</td>
                {row.map((val, j) => (
                  <td key={j} className="p-2 border-r border-slate-600 text-center text-slate-300">{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h4 className="text-lg font-medium mb-2 text-slate-200">⚡ XGBoost Performance</h4>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-600">
          <h5 className="text-cyan-400 font-medium mb-2">Overall Metrics</h5>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-300">Accuracy:</span>
              <span className="text-slate-200 font-medium">{(xgb.accuracy * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">F1-Score:</span>
              <span className="text-slate-200 font-medium">{(xgb.f1_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-600">
          <h5 className="text-cyan-400 font-medium mb-2">Best Classes</h5>
          <div className="space-y-1 text-sm">
            {Object.entries(xgb.report)
              .filter(([key]) => !['accuracy', 'macro avg', 'weighted avg'].includes(key))
              .sort(([,a], [,b]) => b['f1-score'] - a['f1-score'])
              .slice(0, 3)
              .map(([label, metrics]) => (
                <div key={label} className="flex justify-between">
                  <span className="text-slate-300">{label}:</span>
                  <span className="text-slate-200">{(metrics['f1-score'] * 100).toFixed(0)}%</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
