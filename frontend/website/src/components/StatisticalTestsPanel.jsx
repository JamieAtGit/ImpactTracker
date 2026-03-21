import React from "react";
import { motion } from "framer-motion";

function MetricCard({ label, value, sub, color = "text-cyan-400", delay = 0 }) {
  return (
    <motion.div
      className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-5 text-center"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <div className={`text-2xl font-bold font-mono ${color} mb-1`}>{value}</div>
      <div className="text-slate-300 text-sm font-medium">{label}</div>
      {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
    </motion.div>
  );
}

function FoldBar({ folds, color = "#22d3ee" }) {
  const max = Math.max(...folds);
  const min = Math.min(...folds);
  return (
    <div className="space-y-1.5">
      {folds.map((v, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-slate-500 w-12">Fold {i + 1}</span>
          <div className="flex-1 h-4 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ backgroundColor: color }}
              initial={{ width: 0 }}
              animate={{ width: `${((v - min * 0.98) / (max * 1.02 - min * 0.98)) * 100}%` }}
              transition={{ delay: i * 0.08, duration: 0.7, ease: "easeOut" }}
            />
          </div>
          <span className="text-xs font-mono text-slate-300 w-12 text-right">
            {(v * 100).toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  );
}

export default function StatisticalTestsPanel({ evaluationData }) {
  if (!evaluationData) return (
    <div className="flex items-center justify-center h-32 text-slate-500">
      Loading statistical results…
    </div>
  );

  const cv   = evaluationData.cross_validation;
  const mcn  = evaluationData.mcnemar_test;
  const conf = evaluationData.confusion_matrix;

  return (
    <div className="space-y-8">

      {/* Top-level test set metrics */}
      <div>
        <h5 className="text-sm font-semibold text-slate-300 mb-3">Held-Out Test Set (20%, n={mcn?.n_test})</h5>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Test Accuracy" value={`${(conf?.test_accuracy * 100).toFixed(1)}%`}
            sub="20% held-out set" color="text-cyan-400" delay={0}
          />
          <MetricCard
            label="Macro F1" value={conf?.test_f1_macro?.toFixed(3)}
            sub="Unweighted avg" color="text-purple-400" delay={0.05}
          />
          <MetricCard
            label="XGBoost vs RF" value={`+${((cv?.xgboost?.accuracy_mean - cv?.random_forest?.accuracy_mean) * 100).toFixed(2)}%`}
            sub="CV accuracy advantage" color="text-green-400" delay={0.1}
          />
          <MetricCard
            label="Paired t-test" value={cv?.paired_t_test?.p_value < 0.001 ? "p < 0.001" : `p = ${cv?.paired_t_test?.p_value?.toFixed(4)}`}
            sub={cv?.paired_t_test?.significant_at_0_05 ? "XGBoost significantly better" : "No significant difference"}
            color={cv?.paired_t_test?.significant_at_0_05 ? "text-green-400" : "text-yellow-400"} delay={0.15}
          />
        </div>
      </div>

      {/* Cross-validation results */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h5 className="text-sm font-semibold text-slate-300 mb-3">
            5-Fold CV — XGBoost
            <span className="ml-2 text-cyan-400 font-mono">
              {(cv?.xgboost?.accuracy_mean * 100).toFixed(2)}% ± {(cv?.xgboost?.accuracy_std * 100).toFixed(2)}%
            </span>
          </h5>
          <FoldBar folds={cv?.xgboost?.per_fold_acc || []} color="#22d3ee" />
          <div className="mt-3 grid grid-cols-3 gap-2 text-center">
            <div className="bg-slate-800/30 rounded-lg p-2">
              <div className="text-xs text-slate-500">Macro F1</div>
              <div className="text-sm font-mono text-purple-400">{cv?.xgboost?.f1_macro_mean?.toFixed(3)}</div>
            </div>
            <div className="bg-slate-800/30 rounded-lg p-2">
              <div className="text-xs text-slate-500">Log Loss</div>
              <div className="text-sm font-mono text-orange-400">{cv?.xgboost?.log_loss_mean?.toFixed(3)}</div>
            </div>
            <div className="bg-slate-800/30 rounded-lg p-2">
              <div className="text-xs text-slate-500">Brier</div>
              <div className="text-sm font-mono text-amber-400">{cv?.xgboost?.brier_mean?.toFixed(4)}</div>
            </div>
          </div>
        </div>

        <div>
          <h5 className="text-sm font-semibold text-slate-300 mb-3">
            5-Fold CV — Random Forest (baseline)
            <span className="ml-2 text-slate-400 font-mono">
              {(cv?.random_forest?.accuracy_mean * 100).toFixed(2)}% ± {(cv?.random_forest?.accuracy_std * 100).toFixed(2)}%
            </span>
          </h5>
          <FoldBar folds={cv?.random_forest?.per_fold_acc || []} color="#a78bfa" />
          <div className="mt-3 bg-slate-800/30 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Paired t-test (XGBoost vs RF)</div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">t = {cv?.paired_t_test?.t_statistic?.toFixed(3)}</span>
              <span className="text-xs text-slate-500">
                p = {cv?.paired_t_test?.p_value < 0.001 ? "< 0.001" : cv?.paired_t_test?.p_value?.toFixed(4)}
              </span>
              <span className={`text-xs font-medium ${cv?.paired_t_test?.significant_at_0_05 ? "text-green-400" : "text-slate-400"}`}>
                {cv?.paired_t_test?.significant_at_0_05 ? "Significant" : "Not significant"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Label consistency audit */}
      <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl p-5">
        <h5 className="text-sm font-semibold text-slate-300 mb-1">Label Consistency Audit</h5>
        <p className="text-xs text-slate-500 mb-4">
          Verifies that training labels match the DEFRA CO₂ thresholds used in production.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-lg font-bold text-cyan-400">{(mcn?.ml_accuracy * 100).toFixed(1)}%</div>
            <div className="text-xs text-slate-400">ML accuracy (test set)</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-emerald-400">{(mcn?.rule_accuracy * 100).toFixed(1)}%</div>
            <div className="text-xs text-slate-400">Rule-based accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-indigo-400 font-mono">{mcn?.n10_ml_right_rule_wrong + mcn?.n01_ml_wrong_rule_right}</div>
            <div className="text-xs text-slate-400">Discordant predictions</div>
          </div>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-300/80 leading-relaxed">
          <strong className="text-amber-300">Note on rule-based accuracy:</strong> After re-deriving training
          labels directly from the DEFRA CO₂ formula, the rule-based method approaches 100% by construction —
          the labels <em>are</em> the rule-based grades. This confirms label pipeline integrity rather than
          serving as an independent comparison. The meaningful comparison is XGBoost vs Random Forest (paired
          t-test above), which uses the same labels but tests whether the ML model generalises better than a
          simpler classifier.
        </div>
      </div>
    </div>
  );
}
