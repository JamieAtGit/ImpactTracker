document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("estimateForm");
  const analyzeButton = document.getElementById("analyze");
  const buttonText = document.getElementById("buttonText");
  const spinner = document.getElementById("spinner");
  const themeToggle = document.getElementById("themeToggle");
  const output = document.getElementById("output");
  const urlInput = document.getElementById("amazon_url");
  const postcodeInput = document.getElementById("postcode");
  
  let currentUrl = "";
  let urlChangeTimeout = null;

  // Theme toggle
  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
  });

  // Load saved data first, then auto-fill URL
  chrome.storage.local.get(['lastAnalysisData', 'savedPostcode', 'currentPageUrl'], (data) => {
    // Restore saved postcode
    if (data.savedPostcode) {
      postcodeInput.value = data.savedPostcode;
    }
    
    // Restore last analysis if exists
    if (data.lastAnalysisData) {
      displayResults(data.lastAnalysisData);
      urlInput.value = data.lastAnalysisData.url || '';
      currentUrl = data.lastAnalysisData.url || '';
    } else {
      // Check if opened from leaf indicator first
      const leafUrl = data.currentPageUrl;
      if (leafUrl && (leafUrl.includes("amazon.co.uk") || leafUrl.includes("amazon.com"))) {
        urlInput.value = leafUrl;
        currentUrl = leafUrl;
        // Clear the stored URL
        chrome.storage.local.remove('currentPageUrl');
      } else {
        // Auto-fill current URL if no saved data
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          const tabUrl = tabs[0]?.url || "";
          if (tabUrl.includes("amazon.co.uk") || tabUrl.includes("amazon.com")) {
            urlInput.value = tabUrl;
            currentUrl = tabUrl;
          }
        });
      }
    }
  });
  
  // Auto-clear when URL changes (with delay to prevent constant clearing while typing)
  urlInput.addEventListener("input", () => {
    const newUrl = urlInput.value.trim();
    
    // Clear any existing timeout
    if (urlChangeTimeout) {
      clearTimeout(urlChangeTimeout);
    }
    
    // If URL has actually changed from the last analyzed URL
    if (newUrl !== currentUrl && newUrl.length > 0) {
      urlChangeTimeout = setTimeout(() => {
        clearResults();
        showNotification("Ready for new analysis! 🔄");
      }, 2000); // 2 second delay
    }
  });

  // Form submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const url = document.getElementById("amazon_url").value.trim();
    const postcode = document.getElementById("postcode").value.trim();

    if (!url) {
      showError("Please enter an Amazon product URL.");
      return;
    }

    // Show loading state
    buttonText.style.display = "none";
    spinner.style.display = "block";
    analyzeButton.disabled = true;
    output.innerHTML = '<div class="loading-message">Analyzing product... This may take a few seconds.</div>';

    // Use production API to match website results
    const BASE_URL = "https://web-production-a62d7.up.railway.app";

    try {
      const res = await fetch(`${BASE_URL}/estimate_emissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: url,
          postcode: postcode || "SW1A 1AA",
          include_packaging: true
        })
      });

      const json = await res.json();
      console.log("🔍 EXTENSION API Response:", json);
      console.log("🔍 Response data:", json.data);
      console.log("🔍 Response attributes:", json.data?.attributes);

      if (!res.ok) {
        throw new Error(json.error || "Failed to analyze product");
      }

      if (json?.data) {
        currentUrl = url; // Update the current URL after successful analysis
        const analysisData = {
          ...json,
          url: url,
          postcode: postcode || 'SW1A 1AA',
          timestamp: Date.now()
        };
        
        // Save analysis data for persistence
        chrome.storage.local.set({ 
          lastAnalysisData: analysisData,
          savedPostcode: postcode || 'SW1A 1AA'
        });
        
        displayResults(analysisData);
      } else {
        showError("No data received from the server.");
      }
    } catch (err) {
      console.error("❌ Fetch error:", err);
      showError("Error contacting API. Make sure the backend is running.");
    } finally {
      buttonText.style.display = "inline";
      spinner.style.display = "none";
      analyzeButton.disabled = false;
    }
  });

  function showError(message) {
    output.innerHTML = `<div class="error-message">${message}</div>`;
  }

  function displayResults(response) {
    const data = response.data;
    const attributes = data.attributes || {};
    const productTitle = response.title || data.title || "Unknown Product";

    // Emoji map for eco scores
    const emoji = {
      "A+": "🌍", "A": "🌿", "B": "🍃",
      "C": "🌱", "D": "⚠️", "E": "❌", "F": "💀"
    };

    const mlScore = attributes.eco_score_ml || "N/A";
    const ruleScore = attributes.eco_score_rule_based || "N/A";

    output.innerHTML = `
      <div class="result-card visible">
        <div class="result-header">
          <div class="product-title">
            📦 ${productTitle}
          </div>
          <button class="new-analysis-btn" onclick="startNewAnalysis()">
            🔄 Try Another Product
          </button>
        </div>

        <div class="data-section">
          <h3 class="section-title">🔍 Environmental Impact Analysis</h3>
          
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">Eco Score (ML)</span>
              <span class="metric-value eco-score">${mlScore} ${getEmojiForScore(mlScore)}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Eco Score (Rule-Based)</span>
              <span class="metric-value eco-score">${ruleScore} ${getEmojiForScore(ruleScore)}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Material Type</span>
              <span class="status-badge info">${attributes.material_type || "Unknown"}</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Transport Mode</span>
              <span class="status-badge success">
                ${attributes.transport_mode || "N/A"} ${getTransportEmoji(attributes.transport_mode)}
              </span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Weight (incl. packaging)</span>
              <span class="status-badge primary">${attributes.weight_kg || "N/A"} kg</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Recyclability</span>
              <span class="status-badge success">${attributes.recyclability || "N/A"}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Origin</span>
              <span class="status-badge info">${attributes.origin || attributes.country_of_origin || "Unknown"}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Confidence</span>
              <span class="status-badge ${getConfidenceBadgeClass(attributes.eco_score_ml_confidence)}">
                ${attributes.eco_score_ml_confidence ? attributes.eco_score_ml_confidence.toFixed(1) : "N/A"}%
              </span>
            </div>
            
            <div class="metric-item full-width">
              <span class="metric-label">Carbon Emissions</span>
              <span class="status-badge carbon">${attributes.carbon_kg || "N/A"} kg CO₂</span>
            </div>
          </div>

          <div class="section-divider"></div>
          
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">Distance from Origin</span>
              <span class="status-badge secondary">
                ${formatDistance(attributes.distance_from_origin_km)}
              </span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Distance from UK Hub</span>
              <span class="status-badge secondary">
                ${formatDistance(attributes.distance_from_uk_hub_km)}
              </span>
            </div>
          </div>
        </div>

        ${getEquivalenceSection(attributes)}
      </div>
    `;
  }

  function getEmojiForScore(score) {
    const emoji = {
      "A+": "🌍", "A": "🌿", "B": "🍃",
      "C": "🌱", "D": "⚠️", "E": "❌", "F": "💀"
    };
    return emoji[score] || "";
  }

  function getTransportEmoji(transport) {
    if (!transport) return "";
    const mode = transport.toLowerCase();
    if (mode === "air") return "✈️";
    if (mode === "ship") return "🚢";
    if (mode === "truck") return "🚚";
    return "";
  }

  function getConfidenceBadgeClass(confidence) {
    if (!confidence) return "secondary";
    if (confidence >= 80) return "success";
    if (confidence >= 60) return "warning";
    return "error";
  }

  function formatDistance(distance) {
    if (!distance && distance !== 0) return "N/A";
    const numDistance = parseFloat(distance);
    if (!isFinite(numDistance)) return "N/A";
    return `${numDistance.toFixed(1)} km`;
  }

  function getEquivalenceSection(attributes) {
    if (!attributes.carbon_kg) return "";

    const carbonKg = parseFloat(attributes.carbon_kg);
    if (!isFinite(carbonKg)) return "";

    const trees = attributes.trees_to_offset || Math.round(carbonKg / 21.77);
    const kmDriven = (carbonKg * 4.6).toFixed(1);
    const kettlesBoiled = Math.round(carbonKg / 0.011);

    return `
      <div class="equivalence-section">
        <div class="section-divider"></div>
        <h4 style="color: var(--text-secondary); font-size: 14px; margin-bottom: 12px;">
          Environmental Equivalents:
        </h4>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="metric-label">Trees to Offset</span>
            <span class="metric-value">🌳 ${trees}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Km Driven</span>
            <span class="metric-value">🚗 ${kmDriven}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Kettles Boiled</span>
            <span class="metric-value">☕ ${kettlesBoiled}</span>
          </div>
        </div>
      </div>
    `;
  }

  // Helper functions for new analysis workflow
  function startNewAnalysis() {
    clearResults();
    urlInput.value = "";
    currentUrl = "";
    urlInput.focus(); // Auto-focus for better UX
    
    // Clear saved analysis but keep postcode
    chrome.storage.local.remove('lastAnalysisData');
    
    // Auto-fill current URL if on Amazon
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabUrl = tabs[0]?.url || "";
      if (tabUrl.includes("amazon.co.uk") || tabUrl.includes("amazon.com")) {
        urlInput.value = tabUrl;
        currentUrl = tabUrl;
      }
    });
    
    showNotification("Enter a new product URL to analyze! 🚀");
  }

  function clearResults() {
    output.innerHTML = "";
  }
  
  // Save postcode when user types
  postcodeInput.addEventListener('input', () => {
    const postcode = postcodeInput.value.trim();
    if (postcode) {
      chrome.storage.local.set({ savedPostcode: postcode });
    }
  });

  function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification-toast';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  // Make startNewAnalysis globally accessible for onclick
  window.startNewAnalysis = startNewAnalysis;
});