// Persistent overlay that stays on page until manually closed
(function() {
  'use strict';
  
  let overlayVisible = false;
  let lastAnalysisData = null;
  let savedPostcode = '';
  let activeOverlayTab = 'calculator'; // 'calculator' | 'history'
  
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TOGGLE_OVERLAY') {
      toggleOverlay(message.url);
      sendResponse({ success: true });
    }
  });
  
  // Load saved state
  chrome.storage.local.get(['lastAnalysisData', 'savedPostcode', 'overlayVisible'], (data) => {
    if (data.lastAnalysisData) {
      lastAnalysisData = data.lastAnalysisData;
    }
    if (data.savedPostcode) {
      savedPostcode = data.savedPostcode;
    }
    if (data.overlayVisible) {
      showOverlay(data.lastAnalysisData?.url || window.location.href);
    }
  });

  // Auto-analyse product detail pages
  if (document.querySelector('#productTitle')) {
    autoAnalyzeProductPage();
  }
  
  function toggleOverlay(url) {
    if (overlayVisible) {
      hideOverlay();
    } else {
      showOverlay(url);
    }
  }
  
  function showOverlay(url) {
    if (document.getElementById('eco-persistent-overlay')) {
      return; // Already exists
    }
    
    overlayVisible = true;
    chrome.storage.local.set({ overlayVisible: true });
    
    // Create overlay HTML
    const overlay = document.createElement('div');
    overlay.id = 'eco-persistent-overlay';
    overlay.innerHTML = `
      <div class="eco-overlay-container">
        <div class="eco-overlay-header">
          <h3 class="eco-overlay-title">🌱 Eco Emissions</h3>
          <button class="eco-close-btn" title="Close">×</button>
        </div>

        <div class="eco-tab-bar">
          <button class="eco-tab-btn eco-tab-active" id="ecoTabCalculator" onclick="window.ecoSwitchTab('calculator')">🔍 Calculator</button>
          <button class="eco-tab-btn" id="ecoTabHistory" onclick="window.ecoSwitchTab('history')">📋 History</button>
        </div>

        <div class="eco-overlay-content">
          <!-- Calculator tab -->
          <div id="ecoTabPaneCalculator">
            <form class="eco-estimate-form" id="ecoEstimateForm">
              <div class="eco-input-group">
                <input
                  type="text"
                  id="eco_amazon_url"
                  class="eco-input-field"
                  placeholder="Amazon product URL"
                  value="${url || ''}"
                  required
                />
              </div>
              <div class="eco-input-group">
                <input
                  type="text"
                  id="eco_postcode"
                  class="eco-input-field"
                  placeholder="Enter your postcode (e.g., SW1A 1AA)"
                  value="${savedPostcode}"
                />
              </div>
              <button type="submit" id="ecoAnalyze" class="eco-btn-primary">
                <span id="ecoButtonText">Calculate Emissions</span>
                <div class="eco-spinner" id="ecoSpinner" style="display: none;"></div>
              </button>
            </form>
            <div id="ecoOutput" class="eco-output"></div>
          </div>

          <!-- History tab -->
          <div id="ecoTabPaneHistory" style="display:none;">
            <div id="ecoHistoryList"></div>
          </div>
        </div>
      </div>
    `;
    
    // Add CSS
    const style = document.createElement('style');
    style.textContent = `
      #eco-persistent-overlay {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 400px;
        z-index: 999999;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px;
        color: #ffffff;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
      }
      
      .eco-overlay-container {
        background: linear-gradient(135deg, rgba(15, 15, 35, 0.95) 0%, rgba(26, 26, 46, 0.95) 50%, rgba(22, 33, 62, 0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        overflow: hidden;
      }
      
      .eco-overlay-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }

      .eco-tab-bar {
        display: flex;
        gap: 6px;
        padding: 10px 14px 0;
        background: rgba(255,255,255,0.03);
        border-bottom: 1px solid rgba(255,255,255,0.08);
      }

      .eco-tab-btn {
        flex: 1;
        padding: 7px 0;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px 8px 0 0;
        background: transparent;
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        border-bottom: none;
      }

      .eco-tab-btn:hover { color: #e2e8f0; background: rgba(255,255,255,0.05); }

      .eco-tab-active {
        background: rgba(0,212,255,0.1) !important;
        color: #00d4ff !important;
        border-color: rgba(0,212,255,0.3) !important;
      }
      
      .eco-overlay-title {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      
      .eco-close-btn {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #ef4444;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .eco-close-btn:hover {
        background: rgba(239, 68, 68, 0.4);
        transform: scale(1.05);
      }
      
      .eco-overlay-content {
        padding: 20px;
      }
      
      .eco-estimate-form {
        margin-bottom: 20px;
      }
      
      .eco-input-group {
        margin-bottom: 16px;
      }
      
      .eco-input-field {
        width: 100%;
        padding: 14px 16px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-sizing: border-box;
      }
      
      .eco-input-field::placeholder {
        color: #a1a1aa;
      }
      
      .eco-input-field:focus {
        outline: none;
        border-color: #00d4ff;
        background: rgba(0, 212, 255, 0.1);
        box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
      }
      
      .eco-btn-primary {
        width: 100%;
        padding: 16px 24px;
        border: none;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        color: white;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
      }
      
      .eco-btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(0, 212, 255, 0.4);
      }
      
      .eco-btn-primary:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      .eco-spinner {
        position: absolute;
        width: 18px;
        height: 18px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: eco-spin 1s ease-in-out infinite;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
      }
      
      @keyframes eco-spin {
        to { transform: translate(-50%, -50%) rotate(360deg); }
      }
      
      .eco-result-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-top: 16px;
        animation: eco-slideIn 0.3s ease;
      }
      
      @keyframes eco-slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .eco-result-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
        gap: 12px;
      }
      
      .eco-product-title {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.3;
        flex: 1;
      }
      
      .eco-new-analysis-btn {
        background: linear-gradient(135deg, #7c3aed, #00d4ff);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
      }
      
      .eco-new-analysis-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
      }
      
      .eco-metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 12px;
      }
      
      .eco-metric-item {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
      }
      
      .eco-metric-item.full-width {
        grid-column: 1 / -1;
      }
      
      .eco-metric-label {
        font-size: 11px;
        color: #a1a1aa;
        font-weight: 500;
        margin-bottom: 4px;
        display: block;
      }
      
      .eco-metric-value {
        font-size: 14px;
        font-weight: 700;
        color: #00d4ff;
      }
      
      .eco-metric-value.eco-carbon {
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 16px;
      }
      
      .eco-equivalence {
        text-align: center;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 12px;
        color: #10b981;
        font-weight: 600;
        line-height: 1.8;
      }
      
      .eco-loading-message, .eco-error-message {
        text-align: center;
        padding: 16px;
        margin: 12px 0;
        border-radius: 8px;
      }
      
      .eco-loading-message {
        color: #a1a1aa;
        background: rgba(255, 255, 255, 0.05);
      }
      
      .eco-error-message {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #ef4444;
      }

      .eco-history-item {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: background 0.2s;
      }
      .eco-history-item:hover { background: rgba(255,255,255,0.08); }
      .eco-history-title {
        font-size: 12px;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 4px;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .eco-history-meta {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: #64748b;
      }
      .eco-history-carbon { color: #00d4ff; font-weight: 700; }
      .eco-history-empty {
        text-align: center;
        color: #475569;
        font-size: 13px;
        padding: 30px 0;
      }

      /* Auto-analyse banner */
      #eco-auto-banner {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 340px;
        z-index: 999998;
        background: linear-gradient(135deg,rgba(15,15,35,0.97),rgba(22,33,62,0.97));
        border: 1px solid rgba(0,212,255,0.3);
        border-radius: 14px;
        padding: 14px 16px;
        font-family: 'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
        font-size: 13px;
        color: #fff;
        box-shadow: 0 12px 40px rgba(0,0,0,0.35);
        animation: eco-slideIn 0.3s ease;
      }
      .eco-banner-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .eco-banner-title { font-size: 13px; font-weight: 700; color: #00d4ff; }
      .eco-banner-close {
        background: none; border: none; color: #64748b;
        font-size: 16px; cursor: pointer; padding: 0 2px;
      }
      .eco-banner-close:hover { color: #ef4444; }
      .eco-banner-row { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 12px; }
      .eco-banner-label { color: #94a3b8; }
      .eco-banner-value { font-weight: 600; color: #e2e8f0; }
      .eco-banner-carbon { color: #00d4ff; font-size: 18px; font-weight: 800; }
      .eco-banner-loading { color: #94a3b8; font-size: 12px; text-align: center; padding: 8px 0; }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(overlay);
    
    // Setup event listeners
    setupEventListeners();
    
    // Restore last analysis if available
    if (lastAnalysisData) {
      displayResults(lastAnalysisData);
    }
  }
  
  function hideOverlay() {
    const overlay = document.getElementById('eco-persistent-overlay');
    if (overlay) {
      overlay.remove();
    }
    overlayVisible = false;
    chrome.storage.local.set({ overlayVisible: false });
  }
  
  function setupEventListeners() {
    // Close button
    document.querySelector('.eco-close-btn').addEventListener('click', hideOverlay);
    
    // Form submission
    const form = document.getElementById('ecoEstimateForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Save postcode as user types
    const postcodeInput = document.getElementById('eco_postcode');
    postcodeInput.addEventListener('input', () => {
      const postcode = postcodeInput.value.trim();
      chrome.storage.local.set({ savedPostcode: postcode });
    });
  }
  
  async function handleFormSubmit(e) {
    e.preventDefault();
    
    const url = document.getElementById('eco_amazon_url').value.trim();
    const postcode = document.getElementById('eco_postcode').value.trim();
    const buttonText = document.getElementById('ecoButtonText');
    const spinner = document.getElementById('ecoSpinner');
    const analyzeButton = document.getElementById('ecoAnalyze');
    const output = document.getElementById('ecoOutput');
    
    if (!url) {
      showError('Please enter an Amazon product URL.');
      return;
    }
    
    // Show loading state
    buttonText.style.display = 'none';
    spinner.style.display = 'block';
    analyzeButton.disabled = true;
    output.innerHTML = '<div class="eco-loading-message">Analyzing product... This may take a few seconds.</div>';
    
    const BASE_URL = 'https://impacttracker-production.up.railway.app';
    
    try {
      const res = await fetch(`${BASE_URL}/estimate_emissions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amazon_url: url,
          postcode: postcode || 'SW1A 1AA',
          include_packaging: true
        })
      });
      
      const json = await res.json();
      
      if (!res.ok) {
        throw new Error(json.error || 'Failed to analyze product');
      }
      
      if (json?.data) {
        const analysisData = {
          ...json,
          url: url,
          postcode: postcode || 'SW1A 1AA',
          timestamp: Date.now()
        };
        
        lastAnalysisData = analysisData;
        chrome.storage.local.set({
          lastAnalysisData: analysisData,
          savedPostcode: postcode || 'SW1A 1AA'
        });
        saveToHistory(analysisData);

        displayResults(analysisData);
      } else {
        showError('No data received from the server.');
      }
    } catch (err) {
      console.error('Fetch error:', err);
      showError('Error contacting API. Please try again.');
    } finally {
      buttonText.style.display = 'inline';
      spinner.style.display = 'none';
      analyzeButton.disabled = false;
    }
  }
  
  function displayResults(response) {
    const output = document.getElementById('ecoOutput');
    const data = response.data;
    const attributes = data.attributes || {};
    const productTitle = response.title || data.title || 'Unknown Product';
    
    const mlScore = attributes.eco_score_ml || 'N/A';
    const ruleScore = attributes.eco_score_rule_based || 'N/A';
    
    output.innerHTML = `
      <div class="eco-result-card">
        <div class="eco-result-header">
          <div class="eco-product-title">📦 ${productTitle}</div>
          <button class="eco-new-analysis-btn" onclick="window.startNewEcoAnalysis()">
            🔄 Try Another Product
          </button>
        </div>
        
        <div class="eco-metric-grid">
          <div class="eco-metric-item">
            <span class="eco-metric-label">ML Score</span>
            <span class="eco-metric-value">${mlScore} ${getEmojiForScore(mlScore)}</span>
          </div>
          
          <div class="eco-metric-item">
            <span class="eco-metric-label">Rule Score</span>
            <span class="eco-metric-value">${ruleScore} ${getEmojiForScore(ruleScore)}</span>
          </div>
          
          <div class="eco-metric-item full-width">
            <span class="eco-metric-label">Carbon Emissions</span>
            <span class="eco-metric-value eco-carbon">${attributes.carbon_kg || 'N/A'} kg CO₂</span>
          </div>
          
          <div class="eco-metric-item">
            <span class="eco-metric-label">Material</span>
            <span class="eco-metric-value">${attributes.material_type || 'Unknown'}</span>
          </div>

          <div class="eco-metric-item">
            <span class="eco-metric-label">Transport</span>
            <span class="eco-metric-value">${attributes.transport_mode || 'N/A'} ${getTransportEmoji(attributes.transport_mode)}</span>
          </div>

          ${attributes.country_of_origin || attributes.origin ? `
          <div class="eco-metric-item">
            <span class="eco-metric-label">Origin</span>
            <span class="eco-metric-value">${attributes.country_of_origin || attributes.origin}</span>
          </div>` : ''}

          ${attributes.eco_score_ml_confidence ? `
          <div class="eco-metric-item">
            <span class="eco-metric-label">Confidence</span>
            <span class="eco-metric-value">${attributes.eco_score_ml_confidence}%</span>
          </div>` : ''}
        </div>

        ${getCompactEquivalence(attributes)}
      </div>
    `;
  }
  
  function showError(message) {
    const output = document.getElementById('ecoOutput');
    output.innerHTML = `<div class="eco-error-message">${message}</div>`;
  }
  
  function getEmojiForScore(score) {
    const emoji = {
      'A+': '🌍', 'A': '🌿', 'B': '🍃',
      'C': '🌱', 'D': '⚠️', 'E': '❌', 'F': '💀'
    };
    return emoji[score] || '';
  }
  
  function getTransportEmoji(transport) {
    if (!transport) return '';
    const mode = transport.toLowerCase();
    if (mode === 'air') return '✈️';
    if (mode === 'ship') return '🚢';
    if (mode === 'truck') return '🚚';
    return '';
  }
  
  function getCompactEquivalence(attributes) {
    if (!attributes.carbon_kg) return '';
    const carbonKg = parseFloat(attributes.carbon_kg);
    if (!isFinite(carbonKg) || carbonKg <= 0) return '';

    const treesExact = carbonKg / 21;
    const treesDisplay = treesExact < 1
      ? `${Math.round(treesExact * 365)} days of tree absorption`
      : `${Math.ceil(treesExact)} tree${Math.ceil(treesExact) > 1 ? 's' : ''} to offset`;

    const kmDriven = Math.round(carbonKg / 0.21);
    const phoneCharges = Math.round(carbonKg / 0.005);
    const laptopHours = Math.round(carbonKg / 0.05);

    const climateLine = attributes.climate_pledge_friendly
      ? `<div style="color:#10b981;margin-top:4px;">🌿 Amazon Climate Pledge Friendly ✅</div>` : '';

    return `
      <div class="eco-equivalence" style="font-size:12px;line-height:1.8;">
        <div>🌳 ${treesDisplay}</div>
        <div>🚗 ${kmDriven} km driven</div>
        <div>📱 ${phoneCharges} phone charges</div>
        <div>💻 ${laptopHours} hrs laptop use</div>
        ${climateLine}
      </div>
    `;
  }
  
  // ── Tab switching ──────────────────────────────────────────────────────────
  window.ecoSwitchTab = function(tab) {
    activeOverlayTab = tab;
    const calcPane = document.getElementById('ecoTabPaneCalculator');
    const histPane = document.getElementById('ecoTabPaneHistory');
    const calcBtn  = document.getElementById('ecoTabCalculator');
    const histBtn  = document.getElementById('ecoTabHistory');
    if (!calcPane) return;

    if (tab === 'calculator') {
      calcPane.style.display = 'block';
      histPane.style.display = 'none';
      calcBtn.classList.add('eco-tab-active');
      histBtn.classList.remove('eco-tab-active');
    } else {
      calcPane.style.display = 'none';
      histPane.style.display = 'block';
      calcBtn.classList.remove('eco-tab-active');
      histBtn.classList.add('eco-tab-active');
      renderHistory();
    }
  };

  // ── History helpers ────────────────────────────────────────────────────────
  function saveToHistory(analysisData) {
    chrome.storage.local.get(['analysisHistory'], (data) => {
      let history = data.analysisHistory || [];
      // Remove existing entry for same URL to avoid duplicates
      history = history.filter(h => h.url !== analysisData.url);
      history.unshift({
        url:       analysisData.url,
        title:     analysisData.title || 'Unknown Product',
        carbonKg:  analysisData.data?.attributes?.carbon_kg,
        mlScore:   analysisData.data?.attributes?.eco_score_ml,
        timestamp: Date.now(),
      });
      // Keep last 20 entries
      history = history.slice(0, 20);
      chrome.storage.local.set({ analysisHistory: history });
    });
  }

  function renderHistory() {
    const container = document.getElementById('ecoHistoryList');
    if (!container) return;
    chrome.storage.local.get(['analysisHistory'], (data) => {
      const history = data.analysisHistory || [];
      if (history.length === 0) {
        container.innerHTML = '<div class="eco-history-empty">No analyses yet.<br>Calculate emissions for a product to see history here.</div>';
        return;
      }
      container.innerHTML = history.map((item, i) => {
        const date = new Date(item.timestamp).toLocaleDateString('en-GB', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' });
        return `
          <div class="eco-history-item" onclick="window.ecoLoadHistoryItem(${i})">
            <div class="eco-history-title">📦 ${item.title}</div>
            <div class="eco-history-meta">
              <span class="eco-history-carbon">${item.carbonKg ? item.carbonKg + ' kg CO₂' : 'N/A'}</span>
              <span>${item.mlScore || ''} &bull; ${date}</span>
            </div>
          </div>`;
      }).join('');
    });
  }

  window.ecoLoadHistoryItem = function(index) {
    chrome.storage.local.get(['analysisHistory'], (data) => {
      const item = (data.analysisHistory || [])[index];
      if (!item) return;
      // Re-fill URL and switch to calculator
      window.ecoSwitchTab('calculator');
      const urlInput = document.getElementById('eco_amazon_url');
      if (urlInput) urlInput.value = item.url;
    });
  };

  // ── Auto-analyse on product detail pages ──────────────────────────────────
  function autoAnalyzeProductPage() {
    const url = window.location.href;
    const asinMatch = url.match(/\/dp\/([A-Z0-9]{10})/);
    if (!asinMatch) return;
    const asin = asinMatch[1];

    // Show loading banner immediately
    const banner = createAutoBanner();
    banner.querySelector('#eco-banner-body').innerHTML = '<div class="eco-banner-loading">🔍 Analysing product emissions…</div>';

    chrome.storage.local.get(['analysisHistory', 'savedPostcode'], async (data) => {
      const pc = data.savedPostcode || 'SW1A 1AA';
      // Check cache — reuse if analysed within 6 hours
      const history = data.analysisHistory || [];
      const cached = history.find(h => h.url && h.url.includes(asin) && Date.now() - h.timestamp < 21600000);
      if (cached) {
        showBannerResult(banner, cached.title, cached.carbonKg, cached.mlScore, true);
        return;
      }

      const BASE_URL = 'https://impacttracker-production.up.railway.app';
      try {
        const res = await fetch(`${BASE_URL}/estimate_emissions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amazon_url: url, postcode: pc, include_packaging: true })
        });
        const json = await res.json();
        if (json?.data?.attributes) {
          const attr = json.data.attributes;
          showBannerResult(banner, json.title, attr.carbon_kg, attr.eco_score_ml, false);
          saveToHistory({ url, title: json.title, data: json.data, timestamp: Date.now() });
        } else {
          banner.remove();
        }
      } catch {
        banner.remove();
      }
    });
  }

  function createAutoBanner() {
    const existing = document.getElementById('eco-auto-banner');
    if (existing) existing.remove();
    const el = document.createElement('div');
    el.id = 'eco-auto-banner';
    el.innerHTML = `
      <div class="eco-banner-header">
        <span class="eco-banner-title">🌱 Eco Impact</span>
        <button class="eco-banner-close" onclick="document.getElementById('eco-auto-banner').remove()">×</button>
      </div>
      <div id="eco-banner-body"></div>
    `;
    document.body.appendChild(el);
    return el;
  }

  function showBannerResult(banner, title, carbonKg, mlScore, fromCache) {
    const scoreEmoji = { 'A+':'🌍','A':'🌿','B':'🍃','C':'🌱','D':'⚠️','E':'❌','F':'💀' }[mlScore] || '🔍';
    const treesExact = carbonKg ? carbonKg / 21 : 0;
    const treesLine = treesExact < 1
      ? `${Math.round(treesExact * 365)} days of tree absorption`
      : `${Math.ceil(treesExact)} tree${Math.ceil(treesExact) > 1 ? 's' : ''} to offset`;

    banner.querySelector('#eco-banner-body').innerHTML = `
      <div class="eco-banner-row" style="margin-bottom:8px;">
        <span style="font-size:12px;color:#94a3b8;font-style:italic;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:280px;">${(title||'').substring(0,60)}${(title||'').length>60?'…':''}</span>
      </div>
      <div class="eco-banner-row">
        <span class="eco-banner-label">Carbon footprint</span>
        <span class="eco-banner-carbon">${carbonKg ? carbonKg + ' kg CO₂' : 'N/A'}</span>
      </div>
      <div class="eco-banner-row">
        <span class="eco-banner-label">Eco score</span>
        <span class="eco-banner-value">${scoreEmoji} ${mlScore || 'N/A'}</span>
      </div>
      <div class="eco-banner-row">
        <span class="eco-banner-label">Offset</span>
        <span class="eco-banner-value" style="color:#10b981;">🌳 ${treesLine}</span>
      </div>
      ${fromCache ? '<div style="text-align:right;font-size:10px;color:#475569;margin-top:4px;">cached result</div>' : ''}
    `;
    // Auto-dismiss after 12 seconds
    setTimeout(() => {
      const el = document.getElementById('eco-auto-banner');
      if (el) el.style.opacity = '0', el.style.transition = 'opacity 0.5s', setTimeout(() => el?.remove(), 500);
    }, 12000);
  }

  // Global function for new analysis
  window.startNewEcoAnalysis = function() {
    document.getElementById('eco_amazon_url').value = window.location.href;
    document.getElementById('ecoOutput').innerHTML = '';
    chrome.storage.local.remove('lastAnalysisData');
    lastAnalysisData = null;
  };
})();