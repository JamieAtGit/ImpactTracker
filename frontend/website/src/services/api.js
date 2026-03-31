const BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const estimateEmissions = (amazonUrl, postcode, overrideMode = null) =>
  apiFetch("/estimate_emissions", {
    method: "POST",
    body: JSON.stringify({
      amazon_url: amazonUrl,
      postcode: postcode || "SW1A1AA",
      include_packaging: true,
      ...(overrideMode && { override_transport_mode: overrideMode }),
    }),
  });

export const getDashboardMetrics = () =>
  apiFetch("/api/dashboard-metrics");

export const getEcoData = (limit = 1000) =>
  apiFetch(`/api/eco-data?limit=${limit}`);

export const getMaterialAvg = (material) =>
  apiFetch(`/api/material-avg?material=${encodeURIComponent(material)}`);

export const predict = (features) =>
  apiFetch("/predict", { method: "POST", body: JSON.stringify(features) });

export const login = (username, password) =>
  apiFetch("/login", { method: "POST", body: JSON.stringify({ username, password }) });

export const logout = () =>
  apiFetch("/logout", { method: "POST" });

export const getAdminSubmissions = () =>
  apiFetch("/admin/submissions");
