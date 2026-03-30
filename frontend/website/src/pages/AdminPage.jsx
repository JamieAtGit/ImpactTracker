import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import ModernLayout, { ModernCard, ModernSection, ModernButton, ModernBadge, ModernInput } from "../components/ModernLayout";
import Header from "../components/Header";
import InsightsDashboard from "../components/InsightsDashboard";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const AdminStatCard = ({ title, value, subtitle, icon, color = "blue" }) => {
  const colorMap = {
    blue: "from-blue-500 to-cyan-500",
    purple: "from-purple-500 to-violet-500",
    green: "from-green-500 to-emerald-500",
    amber: "from-amber-500 to-orange-500",
    red: "from-red-500 to-rose-500"
  };

  return (
    <motion.div
      className="glass-card p-6"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-slate-200 mt-1">{value}</p>
          {subtitle && <p className="text-slate-500 text-xs mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorMap[color]} flex items-center justify-center`}>
          <span className="text-white text-lg">{icon}</span>
        </div>
      </div>
    </motion.div>
  );
};

const GRADE_VARIANT = g =>
  g === 'A+' || g === 'A' ? 'success' : g === 'B' || g === 'C' ? 'warning' : 'error';

// Returns the suggested true label and reasoning for a submission
const suggest = (item) => {
  const conf = parseFloat(item.confidence) || 0;
  if (item.predicted_label && item.rule_based_label && item.predicted_label === item.rule_based_label)
    return { grade: item.predicted_label, reason: 'Both methods agree' };
  if (conf >= 80 && item.predicted_label)
    return { grade: item.predicted_label, reason: `ML confidence ${conf.toFixed(0)}% — trust ML` };
  if (conf < 60 && item.rule_based_label)
    return { grade: item.rule_based_label, reason: `ML confidence low (${conf.toFixed(0)}%) — prefer rule` };
  if (item.rule_based_label)
    return { grade: item.rule_based_label, reason: 'Uncertain — rule grade suggested' };
  if (item.predicted_label)
    return { grade: item.predicted_label, reason: 'Rule unavailable — using ML' };
  return { grade: '', reason: 'No suggestion available' };
};

const GRADE_ORDER = { 'A+': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6 };
const gradeGap = (a, b) => {
  if (a == null || b == null || !(a in GRADE_ORDER) || !(b in GRADE_ORDER)) return null;
  return Math.abs(GRADE_ORDER[a] - GRADE_ORDER[b]);
};

// Pill button used in the bulk-actions bar
const ActionPill = ({ onClick, color, dot, children }) => {
  const styles = {
    emerald: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-400/50',
    blue:    'bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20 hover:border-blue-400/50',
    violet:  'bg-violet-500/10 border-violet-500/30 text-violet-400 hover:bg-violet-500/20 hover:border-violet-400/50',
  };
  return (
    <button
      onClick={onClick}
      className={`group inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 ${styles[color]}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full bg-current group-hover:animate-ping`} />}
      {children}
    </button>
  );
};

// Inline action button used inside the table
const InlineBtn = ({ onClick, variant = 'default', children }) => {
  const styles = {
    default: 'border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white',
    save:    'border-emerald-500/60 text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20',
    cancel:  'border-slate-600 text-slate-400 hover:bg-slate-700',
  };
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-md border text-xs font-medium transition-all duration-150 ${styles[variant]}`}
    >
      {children}
    </button>
  );
};

function PredictionManagement({ submissions, selected, updatedLabel, setUpdatedLabel, handleEdit, handleSave, setSelected, handleBulkApprove, handleBulkApproveML, handleBulkApproveRule, handleFixCo2, handleExportCsv }) {
  const [filter, setFilter] = React.useState('all'); // 'all' | 'disagree' | 'close' | 'far'

  const labelledCount = submissions.filter(s => s.true_label).length;
  const labelPct = submissions.length > 0 ? Math.round((labelledCount / submissions.length) * 100) : 0;

  const disagreementCount = submissions.filter(
    s => s.predicted_label && s.rule_based_label && s.predicted_label !== s.rule_based_label && !s.true_label
  ).length;

  const displayed = React.useMemo(() => {
    if (filter === 'all') return submissions;
    return submissions.filter(s => {
      if (s.true_label) return false;
      const gap = gradeGap(s.predicted_label, s.rule_based_label);
      if (filter === 'disagree') return gap != null && gap > 0;
      if (filter === 'close')   return gap != null && gap === 1;
      if (filter === 'far')     return gap != null && gap >= 3;
      return true;
    });
  }, [submissions, filter]);

  const filterBtn = (key, label, activeColor) => (
    <button
      onClick={() => setFilter(key)}
      className={`px-3 py-1 rounded-full text-xs font-medium border transition-all duration-150 ${
        filter === key
          ? activeColor
          : 'bg-slate-700/40 border-slate-600 text-slate-400 hover:text-slate-200'
      }`}
    >
      {label}
    </button>
  );

  return (
    <ModernCard solid>
      <div className="space-y-5">
        {/* Header row */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-lg font-display text-slate-200">Review & Validate Predictions</h3>
          <ModernBadge variant="info" size="sm">{displayed.length} of {submissions.length}</ModernBadge>
        </div>

        {/* Labelling progress bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Labelling progress</span>
            <span className="font-medium text-slate-300">{labelledCount} / {submissions.length} labelled ({labelPct}%)</span>
          </div>
          <div className="h-2 w-full bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
              style={{ width: `${labelPct}%` }}
            />
          </div>
        </div>

        {/* Bulk actions row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-medium">Bulk approve:</span>
          <ActionPill color="emerald" dot onClick={handleBulkApprove}>Matching grades</ActionPill>
          <ActionPill color="blue"    dot onClick={handleBulkApproveML}>ML grades</ActionPill>
          <ActionPill color="violet"  dot onClick={handleBulkApproveRule}>Rule grades</ActionPill>
        </div>

        {/* Maintenance + export row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-medium">Tools:</span>
          <ActionPill color="emerald" onClick={handleFixCo2}>Fix CO₂ units</ActionPill>
          <ActionPill color="blue" onClick={handleExportCsv}>Export CSV</ActionPill>
        </div>

        {/* Filter row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-medium">Filter:</span>
          {filterBtn('all',     'All',                        'bg-slate-600 border-slate-500 text-slate-200')}
          {filterBtn('disagree','⚠ Disagreements' + (disagreementCount ? ` (${disagreementCount})` : ''), 'bg-amber-500/20 border-amber-500/50 text-amber-300')}
          {filterBtn('close',   'Close (1 grade apart)',       'bg-sky-500/20 border-sky-500/50 text-sky-300')}
          {filterBtn('far',     'Far apart (3+ grades)',       'bg-red-500/20 border-red-500/50 text-red-300')}
        </div>

        {/* Guidance panel */}
        <div className="rounded-xl border border-slate-700 bg-slate-800/40 px-4 py-3 text-xs text-slate-400 space-y-1">
          <p><span className="text-slate-300 font-medium">Confidence</span> — ML model certainty. &gt;80%: trust ML grade. &lt;60%: prefer Rule grade (deterministic maths).</p>
          <p><span className="text-slate-300 font-medium">⚠ Grades disagree</span> — click <span className="text-slate-300">Label</span> and the input is pre-filled with the best suggestion. Edit if you disagree.</p>
          <p><span className="text-slate-300 font-medium">CO₂ sense-check</span> — A+ ≈ &lt;0.5 kg · A ≈ 0.5–2 kg · B–C ≈ 2–8 kg · D ≈ 8–15 kg · E–F &gt;15 kg.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-600">
                <th className="text-left p-3 text-slate-300 font-medium">Product Title</th>
                <th className="text-left p-3 text-slate-300 font-medium">Origin</th>
                <th className="text-left p-3 text-slate-300 font-medium">ML Grade</th>
                <th className="text-left p-3 text-slate-300 font-medium">Rule Grade</th>
                <th className="text-left p-3 text-slate-300 font-medium">Confidence</th>
                <th className="text-left p-3 text-slate-300 font-medium">CO₂ (kg)</th>
                <th className="text-left p-3 text-slate-300 font-medium">Suggestion</th>
                <th className="text-left p-3 text-slate-300 font-medium">True Label</th>
                <th className="text-left p-3 text-slate-300 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayed.length > 0 ? (
                displayed.map((item, index) => {
                  const realIndex = submissions.indexOf(item);
                  const { grade: suggestedGrade, reason: suggestedReason } = suggest(item);
                  const disagrees = item.predicted_label && item.rule_based_label && item.predicted_label !== item.rule_based_label;
                  return (
                    <motion.tr
                      key={item.id ?? index}
                      className={`border-b border-slate-700/50 hover:bg-slate-800/30 ${disagrees && !item.true_label ? 'bg-amber-900/5' : ''}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: Math.min(index * 0.03, 0.3) }}
                    >
                      <td className="p-3 text-slate-300">
                        <div className="max-w-[180px] truncate" title={item.title}>{item.title}</div>
                        {item.material && <div className="text-slate-500 text-xs mt-0.5">{item.material}</div>}
                      </td>
                      <td className="p-3 text-slate-400 text-sm">{item.origin || '—'}</td>
                      <td className="p-3">
                        {item.predicted_label ? (
                          <div className="flex items-center gap-1.5">
                            <ModernBadge variant={GRADE_VARIANT(item.predicted_label)} size="sm">
                              {item.predicted_label}
                            </ModernBadge>
                            {disagrees && <span className="text-amber-400 text-xs">⚠</span>}
                          </div>
                        ) : <span className="text-slate-600 text-xs">—</span>}
                      </td>
                      <td className="p-3">
                        {item.rule_based_label
                          ? <ModernBadge variant={GRADE_VARIANT(item.rule_based_label)} size="sm">{item.rule_based_label}</ModernBadge>
                          : <span className="text-slate-600 text-xs">—</span>}
                      </td>
                      <td className="p-3 text-slate-400 text-sm">
                        {item.confidence || <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-3 text-slate-400 text-sm font-mono">
                        {item.co2_kg != null ? item.co2_kg.toFixed(2) : <span className="text-slate-600">—</span>}
                      </td>
                      <td className="p-3">
                        {suggestedGrade ? (
                          <div className="flex flex-col gap-0.5">
                            <ModernBadge variant={GRADE_VARIANT(suggestedGrade)} size="sm">{suggestedGrade}</ModernBadge>
                            <span className="text-slate-500 text-xs leading-tight">{suggestedReason}</span>
                          </div>
                        ) : <span className="text-slate-600 text-xs">—</span>}
                      </td>
                      <td className="p-3">
                        {realIndex === selected ? (
                          <ModernInput
                            type="text"
                            value={updatedLabel}
                            onChange={(e) => setUpdatedLabel(e.target.value.toUpperCase())}
                            placeholder="A+, A, B…"
                            className="w-20"
                          />
                        ) : (
                          <span className={item.true_label ? "text-emerald-400 font-medium" : "text-slate-500"}>
                            {item.true_label || '—'}
                          </span>
                        )}
                      </td>
                      <td className="p-3">
                        {realIndex === selected ? (
                          <div className="flex gap-2">
                            <InlineBtn variant="save" onClick={handleSave}>Save</InlineBtn>
                            <InlineBtn variant="cancel" onClick={() => setSelected(null)}>Cancel</InlineBtn>
                          </div>
                        ) : (
                          <InlineBtn onClick={() => handleEdit(realIndex, suggestedGrade)}>Label</InlineBtn>
                        )}
                      </td>
                    </motion.tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="9" className="text-center p-8 text-slate-400">
                    <div className="space-y-2">
                      <div className="text-3xl">{filter !== 'all' ? '✅' : '📭'}</div>
                      <p>{filter !== 'all' ? 'No items match this filter.' : 'No submissions found or access denied.'}</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </ModernCard>
  );
}

const UserManagement = ({ users, handleDeleteUser, handleRoleChange }) => (
  <ModernCard solid>
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-display text-slate-200">
          User Account Management
        </h3>
        <ModernBadge variant="info" size="sm">
          {users.length} users
        </ModernBadge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-600">
              <th className="text-left p-3 text-slate-300 font-medium">Username</th>
              <th className="text-left p-3 text-slate-300 font-medium">Role</th>
              <th className="text-left p-3 text-slate-300 font-medium">Email</th>
              <th className="text-left p-3 text-slate-300 font-medium">Created</th>
              <th className="text-left p-3 text-slate-300 font-medium">Last Login</th>
              <th className="text-left p-3 text-slate-300 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(users) && users.length > 0 ? (
              users.map((user, index) => (
                <motion.tr 
                  key={user.username} 
                  className="border-b border-slate-700/50 hover:bg-slate-800/30"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <td className="p-3 text-slate-300 font-medium">
                    {user.username}
                  </td>
                  <td className="p-3">
                    <ModernBadge 
                      variant={user.role === 'admin' ? 'warning' : 'info'}
                      size="sm"
                    >
                      {user.role}
                    </ModernBadge>
                  </td>
                  <td className="p-3 text-slate-400">
                    {user.email}
                  </td>
                  <td className="p-3 text-slate-400">
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="p-3 text-slate-400">
                    {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-2">
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user, e.target.value)}
                        className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs border border-slate-600 focus:border-blue-500 focus:outline-none"
                        disabled={user.username === 'admin'}
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                      {user.username !== 'admin' && (
                        <ModernButton
                          variant="error"
                          size="sm"
                          onClick={() => handleDeleteUser(user)}
                        >
                          Delete
                        </ModernButton>
                      )}
                    </div>
                  </td>
                </motion.tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="text-center p-8 text-slate-400">
                  <div className="space-y-2">
                    <div className="text-3xl">👥</div>
                    <p>No users found or access denied.</p>
                    <p className="text-sm text-slate-500">Users will appear here when they register.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  </ModernCard>
);

export default function AdminPage() {
  const [submissions, setSubmissions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [updatedLabel, setUpdatedLabel] = useState("");
  const [metrics, setMetrics] = useState({});
  const [modelMetrics, setModelMetrics] = useState({});
  const [users, setUsers] = useState([]);
  const [activeTab, setActiveTab] = useState("predictions");

  useEffect(() => {
    // Load submissions
    fetch(`${BASE_URL}/admin/submissions`, {
      method: "GET",
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setSubmissions(Array.isArray(data) ? data : []))
      .catch((err) => console.error("Error loading submissions:", err));

    // Load dashboard metrics for admin overview
    fetch(`${BASE_URL}/api/dashboard-metrics`)
      .then((res) => res.json())
      .then((data) => setMetrics(data))
      .catch((err) => console.error("Error loading metrics:", err));

    // Load model performance metrics
    fetch(`${BASE_URL}/model-metrics`)
      .then((res) => res.json())
      .then((data) => setModelMetrics(data))
      .catch((err) => console.error("Error loading model metrics:", err));

    // Load user accounts for admin management
    fetch(`${BASE_URL}/admin/users`, {
      method: "GET",
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setUsers(Array.isArray(data) ? data : []))
      .catch((err) => console.error("Error loading users:", err));
  }, []);

  const handleEdit = (index, suggestedGrade = "") => {
    setSelected(index);
    // Pre-fill with existing true label, or the system suggestion if unlabelled
    setUpdatedLabel(submissions[index].true_label || suggestedGrade);
  };

  const handleSave = () => {
    const item = { ...submissions[selected], true_label: updatedLabel };
    fetch(`${BASE_URL}/admin/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(item),
    })
      .then(() => {
        const updated = [...submissions];
        updated[selected].true_label = updatedLabel;
        setSubmissions(updated);
        setSelected(null);
      })
      .catch((err) => console.error("Update failed:", err));
  };

  const handleDeleteUser = async (user) => {
    if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) return;

    try {
      const res = await fetch(`${BASE_URL}/admin/users/${user.id}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (res.ok) {
        setUsers(users.filter(u => u.id !== user.id));
        alert(`User ${user.username} deleted successfully`);
      } else {
        const data = await res.json();
        alert(`Failed to delete user: ${data.error}`);
      }
    } catch (err) {
      console.error("Delete user failed:", err);
      alert("Failed to delete user");
    }
  };

  const refreshSubmissions = async () => {
    const res = await fetch(`${BASE_URL}/admin/submissions`, { credentials: 'include' });
    setSubmissions(await res.json());
  };

  const bulkAction = async (endpoint, label) => {
    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        alert(`${label}: ${data.approved} approved, ${data.skipped} skipped.`);
        await refreshSubmissions();
      } else {
        alert(`Failed: ${data.error}`);
      }
    } catch (err) {
      alert(`${label} failed`);
    }
  };

  const handleBulkApprove     = () => bulkAction('/admin/bulk-approve-matching', 'Auto-approve matching');
  const handleBulkApproveML   = () => bulkAction('/admin/bulk-approve-ml',       'Approve ML grades');
  const handleBulkApproveRule = () => bulkAction('/admin/bulk-approve-rule',      'Approve rule grades');

  const handleFixCo2 = async () => {
    if (!confirm('Recalculate CO₂ for all records where weight was stored in grams instead of kg?\n\nThis is safe to run multiple times.')) return;
    try {
      const res = await fetch(`${BASE_URL}/api/admin/fix-co2`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        alert(`CO₂ fix complete: ${data.fixed} records corrected, ${data.skipped} skipped.`);
        await refreshSubmissions();
      } else {
        alert(`Failed: ${data.error}`);
      }
    } catch (err) {
      alert('CO₂ fix failed');
    }
  };

  const handleExportCsv = async () => {
    try {
      const res = await fetch(`${BASE_URL}/api/admin/export-labelled-csv`, { credentials: 'include' });
      if (!res.ok) { alert('Export failed: not authorised'); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'labelled_data.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Export failed');
    }
  };

  const handleRoleChange = async (user, newRole) => {
    try {
      const res = await fetch(`${BASE_URL}/admin/users/${user.id}/role`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ role: newRole }),
      });

      if (res.ok) {
        setUsers(users.map(u =>
          u.id === user.id ? { ...u, role: newRole } : u
        ));
        alert(`User ${user.username} role updated to ${newRole}`);
      } else {
        const data = await res.json();
        alert(`Failed to update role: ${data.error}`);
      }
    } catch (err) {
      console.error("Role update failed:", err);
      alert("Failed to update user role");
    }
  };

  // Calculate admin-specific metrics
  const labelledCount = submissions.filter(s => s.true_label).length;
  const needsReview = submissions.length - labelledCount;

  // Use per-submission accuracy only when enough labels exist (>=5).
  // Otherwise fall back to the real XGBoost test-set accuracy from model-metrics.
  const accuracyInfo = (() => {
    if (labelledCount >= 5) {
      const correct = submissions.filter(
        s => s.true_label && s.predicted_label === s.true_label
      ).length;
      return {
        value: (correct / labelledCount * 100).toFixed(1),
        subtitle: `${labelledCount} labelled samples`,
      };
    }
    if (modelMetrics.accuracy) {
      return {
        value: (modelMetrics.accuracy * 100).toFixed(1),
        subtitle: "XGBoost test-set accuracy",
      };
    }
    return { value: "N/A", subtitle: "No labelled data yet" };
  })();

  const recentActivity = submissions.filter(s => {
    if (!s.created_at) return false;
    return new Date(s.created_at) > new Date(Date.now() - 24 * 60 * 60 * 1000);
  }).length;

  const submissionStats = {
    total: submissions.length,
    needsReview,
    accuracyInfo,
    recentActivity,
  };

  return (
    <ModernLayout>
      {{
        nav: <Header />,
        content: (
          <div className="space-y-8">
            {/* Hero Section */}
            <ModernSection className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="space-y-6"
              >
                <h1 className="text-4xl md:text-5xl font-display font-bold leading-tight">
                  <span className="text-slate-100">Admin</span>
                  <br />
                  <span className="bg-gradient-to-r from-purple-400 via-pink-500 to-red-400 bg-clip-text text-transparent">
                    Dashboard
                  </span>
                </h1>
                <motion.p
                  className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.4 }}
                >
                  Monitor system performance, review predictions, and manage model accuracy.
                </motion.p>
              </motion.div>
            </ModernSection>

            {/* Admin Stats Grid */}
            <ModernSection>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <AdminStatCard
                  title="Total Submissions"
                  value={submissionStats.total}
                  subtitle="All predictions"
                  icon="📊"
                  color="blue"
                />
                <AdminStatCard
                  title="Needs Review"
                  value={submissionStats.needsReview}
                  subtitle={`${labelledCount} of ${submissionStats.total} labelled`}
                  icon="⚠️"
                  color="amber"
                />
                <AdminStatCard
                  title="Model Accuracy"
                  value={`${submissionStats.accuracyInfo.value}%`}
                  subtitle={submissionStats.accuracyInfo.subtitle}
                  icon="🎯"
                  color="green"
                />
                <AdminStatCard
                  title="Recent Activity"
                  value={submissionStats.recentActivity}
                  subtitle="Last 24 hours"
                  icon="⚡"
                  color="purple"
                />
              </div>
            </ModernSection>

            {/* System Overview */}
            <ModernSection 
              title="System Analytics" 
              icon={true}
              delay={0.2}
            >
              <InsightsDashboard />
            </ModernSection>

            {/* Admin Tabs */}
            <ModernSection 
              title="Admin Controls" 
              icon={true}
              delay={0.3}
            >
              <div className="space-y-6">
                {/* Tab Navigation */}
                <div className="flex space-x-1 bg-slate-800/50 p-1 rounded-lg">
                  <button
                    onClick={() => setActiveTab("predictions")}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                      activeTab === "predictions"
                        ? "bg-blue-600 text-white shadow-md"
                        : "text-slate-300 hover:text-white hover:bg-slate-700/50"
                    }`}
                  >
                    📊 Prediction Review
                  </button>
                  <button
                    onClick={() => setActiveTab("users")}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                      activeTab === "users"
                        ? "bg-purple-600 text-white shadow-md"
                        : "text-slate-300 hover:text-white hover:bg-slate-700/50"
                    }`}
                  >
                    👥 User Management
                  </button>
                </div>

                {/* Tab Content */}
                {activeTab === "predictions" && (
                  <PredictionManagement
                    submissions={submissions}
                    selected={selected}
                    updatedLabel={updatedLabel}
                    setUpdatedLabel={setUpdatedLabel}
                    handleEdit={handleEdit}
                    handleSave={handleSave}
                    setSelected={setSelected}
                    handleBulkApprove={handleBulkApprove}
                    handleBulkApproveML={handleBulkApproveML}
                    handleBulkApproveRule={handleBulkApproveRule}
                    handleFixCo2={handleFixCo2}
                    handleExportCsv={handleExportCsv}
                  />
                )}

                {activeTab === "users" && (
                  <UserManagement 
                    users={users}
                    handleDeleteUser={handleDeleteUser}
                    handleRoleChange={handleRoleChange}
                  />
                )}
              </div>
            </ModernSection>


            {/* Footer */}
            <motion.footer
              className="text-center py-12 mt-16"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.8 }}
            >
              <ModernCard className="max-w-md mx-auto text-center">
                <div className="space-y-2">
                  <p className="text-slate-300 font-medium">
                    © 2025 Impact Tracker Admin
                  </p>
                  <p className="text-slate-400 text-sm">
                    Monitoring system performance 🔧
                  </p>
                </div>
              </ModernCard>
            </motion.footer>
          </div>
        ),
      }}
    </ModernLayout>
  );
}
