// Persistent overlay that stays on page until manually closed
(function() {
  'use strict';
  
  let overlayVisible = false;
  let lastAnalysisData = null;
  let savedPostcode = '';
  
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
          <h3 class="eco-overlay-title">🌱 Amazon Emissions Calculator</h3>
          <button class="eco-close-btn" title="Close">×</button>
        </div>
        
        <div class="eco-overlay-content">
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
    
    const BASE_URL = 'https://web-production-a62d7.up.railway.app';
    
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
    if (!isFinite(carbonKg)) return '';
    
    const trees = attributes.trees_to_offset || Math.round(carbonKg / 21.77);
    
    return `
      <div class="eco-equivalence">
        🌳 ${trees} trees needed to offset this carbon footprint
      </div>
    `;
  }
  
  // Global function for new analysis
  window.startNewEcoAnalysis = function() {
    document.getElementById('eco_amazon_url').value = window.location.href;
    document.getElementById('ecoOutput').innerHTML = '';
    chrome.storage.local.remove('lastAnalysisData');
    lastAnalysisData = null;
  };
})();