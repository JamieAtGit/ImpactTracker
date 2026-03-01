import { useEffect, useState } from "react";
import "./refined.css";
import MLvsDefraChart from "./MLvsDefraChart";


export default function EstimateForm() {
  const [url, setUrl] = useState("");
  const [postcode, setPostcode] = useState(localStorage.getItem("postcode") || "");
  const [quantity, setQuantity] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [equivalenceView, setEquivalenceView] = useState(0);
  const [materialInsights, setMaterialInsights] = useState({});

  useEffect(() => {
    fetch("/material_insights.json")
      .then((res) => res.json())
      .then(setMaterialInsights)
      .catch((err) => console.warn("Could not load material insights:", err));
  }, []);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentUrl = tabs[0]?.url || "";
      if (currentUrl.includes("amazon.co.uk")) {
        setUrl(currentUrl);
      }
    });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    localStorage.setItem("postcode", postcode);

    try {
      const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
      const res = await fetch(`${BASE_URL}/estimate_emissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: url || "",
          postcode: postcode || "SW1A 1AA",
          include_packaging: true,
        }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText);
      }

      const data = await res.json();
      console.log("Received result:", data);
      setResult(data);
    } catch (err) {
      setError("Failed to fetch product data. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  const attributes = result?.data?.attributes || {};
  const productTitle = result?.data?.title || result?.title || "Untitled Product";

  const materialInsight = materialInsights[attributes.material_type?.toLowerCase()] || {};

  return (
    <div className="glass-container">
      <div className="header-section">
        <button className="btn-secondary theme-toggle" onClick={() => document.body.classList.toggle("dark-mode")}>
          🌃 Toggle Theme
        </button>
      </div>

      <h2 className="title-gradient">Amazon Shipping<br />Emissions Estimator</h2>


      <form onSubmit={handleSubmit} className="estimate-form">
        <div className="input-group">
          <input 
            type="text" 
            className="input-field" 
            placeholder="Amazon product URL" 
            value={url} 
            onChange={(e) => setUrl(e.target.value)} 
          />
        </div>
        <div className="input-group">
          <input 
            type="text" 
            className="input-field" 
            placeholder="Enter your postcode" 
            value={postcode} 
            onChange={(e) => setPostcode(e.target.value)} 
          />
        </div>
        <div className="input-group">
          <input 
            type="number" 
            className="input-field" 
            min="1" 
            value={quantity} 
            onChange={(e) => setQuantity(parseInt(e.target.value))} 
          />
        </div>
        <button type="submit" className={`btn-primary ${loading ? 'loading' : ''}`} disabled={loading}>
          {loading ? (
            <span>
              <span className="spinner"></span>
              Estimating...
            </span>
          ) : (
            "Estimate Emissions"
          )}
        </button>
      </form>

      {error && <div className="status-badge error">{error}</div>}

      {result && (
        <div className="result-card">
          <div className="product-title" title={productTitle}>
            <span role="img" aria-label="package">📦</span>
            {productTitle}
          </div>

          <div className="data-section">
            <h3 className="section-title">🔍 Raw & Parsed Values</h3>
            
            <div className="metric-grid">
              <div className="metric-item">
                <span className="metric-label">Eco Score (ML):</span>
                <span className="status-badge primary">{attributes.eco_score_ml || "N/A"}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Eco Score (Rule-Based):</span>
                <span className="status-badge secondary">{attributes.eco_score_rule_based || "N/A"}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Material Type:</span>
                <span className="status-badge info" title={materialInsight?.description || "No material insight available"}>
                  {attributes.material_type || "Unknown"}
                </span>
              </div>

              <div className="metric-item">
                <span className="metric-label">Selected Transport Mode:</span>
                <span className="status-badge success">
                  {attributes.selected_transport_mode
                    ? `${attributes.selected_transport_mode} ${
                        attributes.selected_transport_mode === "Air"
                          ? "✈️"
                          : attributes.selected_transport_mode === "Ship"
                          ? "🚢"
                          : attributes.selected_transport_mode === "Truck"
                          ? "🚚"
                          : ""
                      }`
                    : "Auto"}
                </span>
              </div>

              <div className="metric-item">
                <span className="metric-label">Default Based on Distance:</span>
                <span className="status-badge info">
                  {attributes.default_transport_mode
                    ? `${attributes.default_transport_mode} ${
                        attributes.default_transport_mode === "Air"
                          ? "✈️"
                          : attributes.default_transport_mode === "Ship"
                          ? "🚢"
                          : attributes.default_transport_mode === "Truck"
                          ? "🚚"
                          : ""
                      }`
                    : "N/A"}
                </span>
              </div>

              {attributes.selected_transport_mode &&
                attributes.selected_transport_mode !== attributes.default_transport_mode && (
                  <div className="metric-item full-width">
                    <div className="status-badge warning">
                      ⚠️ You overrode the suggested mode ({attributes.default_transport_mode}) with{" "}
                      {attributes.selected_transport_mode}.
                    </div>
                  </div>
              )}

              <div className="metric-item">
                <span className="metric-label">Weight (incl. packaging):</span>
                <span className="status-badge primary">{attributes.weight_kg ?? "N/A"} kg</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Recyclability:</span>
                <span className="status-badge success">{attributes.recyclability ?? "N/A"}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Origin:</span>
                <span className="status-badge info">{attributes.origin ?? "N/A"}</span>
              </div>
              
              <div className="metric-item carbon-highlight">
                <span className="metric-label">Carbon Emissions:</span>
                <span className="status-badge carbon">{attributes.carbon_kg ?? "N/A"} kg CO₂</span>
              </div>
            </div>

            <MLvsDefraChart result={result} />

            <div className="section-divider"></div>
            
            <div className="metric-grid">
              <div className="metric-item">
                <span className="metric-label">Distance from Origin:</span>
                <span className="status-badge secondary">
                  {Number.isFinite(parseFloat(attributes?.distance_from_origin_km))
                    ? `${parseFloat(attributes.distance_from_origin_km).toFixed(1)} km`
                    : "N/A"}
                </span>
              </div>

              <div className="metric-item">
                <span className="metric-label">Distance from UK Hub:</span>
                <span className="status-badge secondary">
                  {Number.isFinite(parseFloat(attributes?.distance_from_uk_hub_km))
                    ? `${parseFloat(attributes.distance_from_uk_hub_km).toFixed(1)} km`
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>

          <div className="equivalence-section">
            <button className="btn-secondary rotate-btn" onClick={() => setEquivalenceView((prev) => (prev + 1) % 3)}>
              <span role="img" aria-label="rotate">🔁</span>
              Show another comparison
            </button>
            <div className="equivalence-display">
              {equivalenceView === 0 && result.data?.attributes?.trees_to_offset && (
                <span>≈ {result.data.attributes.trees_to_offset} trees to offset</span>
              )}
              {equivalenceView === 1 && result.data?.attributes?.carbon_kg && (
                <span>≈ {(result.data.attributes.carbon_kg * 4.6).toFixed(1)} km driven</span>
              )}
              {equivalenceView === 2 && result.data?.attributes?.carbon_kg && (
                <span>≈ {Math.round(result.data.attributes.carbon_kg / 0.011)} kettles boiled</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
