// Content script that creates a persistent overlay on Amazon pages
(function() {
  'use strict';

  // Prevent multiple injections
  if (window.ecoTrackerInjected) return;
  window.ecoTrackerInjected = true;

  let overlayVisible = false;
  let overlay = null;

  // Create the overlay HTML
  function createOverlay() {
    const overlayHTML = `
      <div id="eco-tracker-overlay" style="
        position: fixed;
        top: 20px;
        right: 20px;
        width: 420px;
        max-height: 90vh;
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 8px 32px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #ffffff;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow-y: auto;
        display: none;
        animation: slideInFromRight 0.3s ease-out;
      ">
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
          
          @keyframes slideInFromRight {
            from {
              opacity: 0;
              transform: translateX(100%);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }

          @keyframes slideOutToRight {
            from {
              opacity: 1;
              transform: translateX(0);
            }
            to {
              opacity: 0;
              transform: translateX(100%);
            }
          }

          #eco-tracker-overlay.closing {
            animation: slideOutToRight 0.3s ease-in forwards;
          }

          #eco-tracker-overlay::-webkit-scrollbar {
            width: 8px;
          }

          #eco-tracker-overlay::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
          }

          #eco-tracker-overlay::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 255, 0.3);
            border-radius: 4px;
          }

          #eco-tracker-overlay .glass-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            padding: 24px;
            margin: 16px;
            position: relative;
            overflow: hidden;
          }

          #eco-tracker-overlay .glass-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
          }

          #eco-tracker-overlay .close-button {
            position: absolute;
            top: 16px;
            right: 16px;
            width: 32px;
            height: 32px;
            border: none;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            color: #ffffff;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.3s ease;
            z-index: 10;
          }

          #eco-tracker-overlay .close-button:hover {
            background: rgba(255, 0, 0, 0.2);
            transform: scale(1.1);
          }

          #eco-tracker-overlay .title-gradient {
            font-size: 20px;
            font-weight: 700;
            margin: 0 0 20px;
            text-align: center;
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
            padding-right: 40px;
          }

          #eco-tracker-overlay .input-group {
            position: relative;
            margin-bottom: 16px;
          }

          #eco-tracker-overlay .input-field {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-sizing: border-box;
            backdrop-filter: blur(10px);
          }

          #eco-tracker-overlay .input-field::placeholder {
            color: #a1a1aa;
            font-weight: 400;
          }

          #eco-tracker-overlay .input-field:focus {
            outline: none;
            border-color: #00d4ff;
            background: rgba(0, 212, 255, 0.1);
            box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.1);
            transform: translateY(-1px);
          }

          #eco-tracker-overlay .btn-primary {
            width: 100%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 24px;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            min-height: 44px;
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            color: white;
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
          }

          #eco-tracker-overlay .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(0, 212, 255, 0.4);
          }

          #eco-tracker-overlay .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
          }

          #eco-tracker-overlay .spinner {
            position: absolute;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            left: 50%;
            top: 50%;
            margin-left: -10px;
            margin-top: -10px;
          }

          @keyframes spin {
            to { transform: rotate(360deg); }
          }

          #eco-tracker-overlay .result-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            animation: slideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
          }

          @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
          }

          #eco-tracker-overlay .product-title {
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
            line-height: 1.3;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            word-break: break-word;
          }

          #eco-tracker-overlay .metric-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 16px 0;
          }

          #eco-tracker-overlay .metric-item {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            transition: all 0.3s ease;
          }

          #eco-tracker-overlay .metric-item.full-width {
            grid-column: 1 / -1;
          }

          #eco-tracker-overlay .metric-label {
            font-size: 10px;
            color: #a1a1aa;
            font-weight: 500;
            display: block;
            margin-bottom: 6px;
          }

          #eco-tracker-overlay .metric-value {
            font-size: 16px;
            font-weight: 700;
            color: #00d4ff;
          }

          #eco-tracker-overlay .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          #eco-tracker-overlay .status-badge.primary {
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            border: 1px solid rgba(0, 212, 255, 0.3);
          }

          #eco-tracker-overlay .status-badge.success {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
          }

          #eco-tracker-overlay .status-badge.info {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
          }

          #eco-tracker-overlay .status-badge.carbon {
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            color: white;
            border: none;
            font-size: 12px;
          }

          #eco-tracker-overlay .section-divider {
            height: 1px;
            background: rgba(255, 255, 255, 0.1);
            margin: 16px 0;
          }

          #eco-tracker-overlay .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 12px;
            color: #ef4444;
            font-size: 12px;
            margin: 12px 0;
          }

          #eco-tracker-overlay .loading-message {
            color: #a1a1aa;
            font-style: italic;
            text-align: center;
            padding: 16px;
            font-size: 12px;
          }

          /* New Analysis button */
          #eco-tracker-overlay .new-analysis-btn {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 16px;
            width: 100%;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
          }

          #eco-tracker-overlay .new-analysis-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
          }

          /* Auto-fill button */
          #eco-tracker-overlay .auto-fill-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            color: #ffffff;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 12px;
            width: 100%;
          }

          #eco-tracker-overlay .auto-fill-btn:hover {
            background: rgba(255, 255, 255, 0.15);
          }

          /* Fade out animation for form */
          #eco-tracker-overlay .form-fade-out {
            opacity: 0.5;
            transition: opacity 0.3s ease;
          }

          /* Clear notification */
          #eco-tracker-overlay .clear-notification {
            background: rgba(245, 158, 11, 0.2);
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 8px;
            padding: 8px 12px;
            color: #f59e0b;
            font-size: 12px;
            margin-bottom: 12px;
            text-align: center;
            animation: slideIn 0.3s ease;
          }
        </style>

        <button class="close-button" id="eco-close-btn">×</button>
        
        <div class="glass-container">
          <h2 class="title-gradient">Amazon Emissions<br>Estimator</h2>
          
          <div id="new-analysis-section" style="display: none;">
            <button class="new-analysis-btn" id="new-analysis-btn">🆕 Analyze New Product</button>
          </div>
          
          <button class="auto-fill-btn" id="auto-fill-btn">🔗 Use Current Page URL</button>
          
          <form class="estimate-form" id="eco-estimate-form">
            <div class="input-group">
              <input 
                type="text" 
                id="eco-amazon-url" 
                class="input-field" 
                placeholder="Amazon product URL" 
                required
              />
            </div>
            <div class="input-group">
              <input 
                type="text" 
                id="eco-postcode" 
                class="input-field" 
                placeholder="Enter your postcode" 
              />
            </div>
            <button type="submit" id="eco-analyze" class="btn-primary">
              <span id="eco-button-text">Estimate Emissions</span>
              <div class="spinner" id="eco-spinner" style="display: none;"></div>
            </button>
          </form>

          <div id="eco-output"></div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', overlayHTML);
    overlay = document.getElementById('eco-tracker-overlay');
    
    // Add event listeners
    setupEventListeners();
  }

  function setupEventListeners() {
    const closeBtn = document.getElementById('eco-close-btn');
    const autoFillBtn = document.getElementById('auto-fill-btn');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const newAnalysisSection = document.getElementById('new-analysis-section');
    const form = document.getElementById('eco-estimate-form');
    const analyzeButton = document.getElementById('eco-analyze');
    const buttonText = document.getElementById('eco-button-text');
    const spinner = document.getElementById('eco-spinner');
    const output = document.getElementById('eco-output');
    const urlInput = document.getElementById('eco-amazon-url');
    const postcodeInput = document.getElementById('eco-postcode');
    
    let clearTimeout = null;

    // Close button
    closeBtn.addEventListener('click', hideOverlay);

    // Auto-fill current page URL
    autoFillBtn.addEventListener('click', () => {
      urlInput.value = window.location.href;
      // Trigger auto-clear if there are results
      if (output.innerHTML.trim()) {
        scheduleAutoClear();
      }
    });

    // New Analysis button
    newAnalysisBtn.addEventListener('click', () => {
      clearAnalysis();
      urlInput.focus();
    });

    // Auto-clear on URL change
    urlInput.addEventListener('input', () => {
      if (output.innerHTML.trim()) {
        scheduleAutoClear();
      }
    });

    function scheduleAutoClear() {
      // Clear any existing timeout
      if (clearTimeout) {
        clearTimeout(clearTimeout);
      }
      
      // Add fade effect to indicate change is coming
      form.classList.add('form-fade-out');
      
      // Schedule clear after 2 seconds
      clearTimeout = setTimeout(() => {
        clearAnalysis(true);
        form.classList.remove('form-fade-out');
      }, 2000);
    }

    function clearAnalysis(showNotification = false) {
      // Clear results
      output.innerHTML = '';
      
      // Hide new analysis section
      newAnalysisSection.style.display = 'none';
      
      // Reset form if not preserving URL
      if (!showNotification) {
        urlInput.value = '';
        postcodeInput.value = '';
      }
      
      // Show notification if auto-cleared
      if (showNotification) {
        const notification = document.createElement('div');
        notification.className = 'clear-notification';
        notification.textContent = '✨ Previous analysis cleared for new product';
        form.insertBefore(notification, form.firstChild);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
          if (notification.parentNode) {
            notification.remove();
          }
        }, 3000);
      }
      
      // Focus URL input
      setTimeout(() => urlInput.focus(), 100);
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const url = document.getElementById('eco-amazon-url').value.trim();
      const postcode = document.getElementById('eco-postcode').value.trim();

      if (!url) {
        showError("Please enter an Amazon product URL.");
        return;
      }

      // Show loading state
      buttonText.style.display = "none";
      spinner.style.display = "block";
      analyzeButton.disabled = true;
      output.innerHTML = '<div class="loading-message">Analyzing product... This may take a few seconds.</div>';

      const BASE_URL = "https://web-production-a62d7.up.railway.app";

      try {
        // Send message to background script to make the API call
        const response = await new Promise((resolve, reject) => {
          chrome.runtime.sendMessage({
            action: 'makeApiCall',
            url: `${BASE_URL}/estimate_emissions`,
            data: {
              amazon_url: url,
              postcode: postcode || "SW1A 1AA",
              include_packaging: true
            }
          }, (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else if (response.error) {
              reject(new Error(response.error));
            } else {
              resolve(response);
            }
          });
        });

        if (!response.ok) {
          throw new Error(response.error || "Failed to analyze product");
        }

        if (response.data?.data) {
          displayResults(response.data);
          // Show the "New Analysis" button after successful results
          newAnalysisSection.style.display = 'block';
        } else {
          showError("No data received from the server.");
        }
      } catch (err) {
        console.error("❌ Extension API error:", err);
        showError(`Error: ${err.message}. Make sure the backend is running on localhost:5000.`);
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

      const mlScore = attributes.eco_score_ml || "N/A";
      const ruleScore = attributes.eco_score_rule_based || "N/A";

      output.innerHTML = `
        <div class="result-card">
          <div class="product-title">
            📦 ${productTitle}
          </div>

          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">Eco Score (ML)</span>
              <span class="metric-value">${mlScore} ${getEmojiForScore(mlScore)}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Eco Score (Rule)</span>
              <span class="metric-value">${ruleScore} ${getEmojiForScore(ruleScore)}</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Material</span>
              <span class="status-badge info">${attributes.material_type || "Unknown"}</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Transport</span>
              <span class="status-badge success">
                ${attributes.transport_mode || "N/A"} ${getTransportEmoji(attributes.transport_mode)}
              </span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Weight</span>
              <span class="status-badge primary">${attributes.weight_kg || "N/A"} kg</span>
            </div>
            
            <div class="metric-item">
              <span class="metric-label">Origin</span>
              <span class="status-badge info">${attributes.origin || attributes.country_of_origin || "Unknown"}</span>
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
              <span class="status-badge primary">${formatDistance(attributes.distance_from_origin_km)}</span>
            </div>

            <div class="metric-item">
              <span class="metric-label">Distance from UK Hub</span>
              <span class="status-badge primary">${formatDistance(attributes.distance_from_uk_hub_km)}</span>
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

      const trees = Math.round(carbonKg / 21.77);
      const kmDriven = (carbonKg * 4.6).toFixed(1);

      return `
        <div>
          <div class="section-divider"></div>
          <div class="metric-grid">
            <div class="metric-item">
              <span class="metric-label">Trees to Offset</span>
              <span class="metric-value">🌳 ${trees}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Km Driven</span>
              <span class="metric-value">🚗 ${kmDriven}</span>
            </div>
          </div>
        </div>
      `;
    }
  }

  function showOverlay() {
    if (!overlay) {
      createOverlay();
    }
    overlay.style.display = 'block';
    overlayVisible = true;
  }

  function hideOverlay() {
    if (overlay) {
      overlay.classList.add('closing');
      setTimeout(() => {
        overlay.style.display = 'none';
        overlay.classList.remove('closing');
        overlayVisible = false;
      }, 300);
    }
  }

  // Add toggle button to Amazon page
  function addToggleButton() {
    const toggleButton = document.createElement('div');
    toggleButton.innerHTML = `
      <div style="
        position: fixed;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        z-index: 9999;
        background: linear-gradient(135deg, #00d4ff, #7c3aed);
        border-radius: 50%;
        width: 56px;
        height: 56px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        transition: all 0.3s ease;
        font-size: 24px;
        color: white;
        font-weight: bold;
      " id="eco-toggle-btn" title="Check Environmental Impact">
        🌱
      </div>
    `;

    document.body.appendChild(toggleButton);

    // Add hover effect
    const btn = document.getElementById('eco-toggle-btn');
    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'translateY(-50%) scale(1.1)';
      btn.style.boxShadow = '0 12px 35px rgba(0, 212, 255, 0.4)';
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'translateY(-50%) scale(1)';
      btn.style.boxShadow = '0 8px 25px rgba(0, 212, 255, 0.3)';
    });

    btn.addEventListener('click', () => {
      if (overlayVisible) {
        hideOverlay();
      } else {
        showOverlay();
      }
    });
  }

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'toggleOverlay') {
      if (overlayVisible) {
        hideOverlay();
      } else {
        showOverlay();
      }
      sendResponse({ status: 'toggled' });
    }
  });

  // Initialize on Amazon pages
  if (window.location.hostname.includes('amazon')) {
    addToggleButton();
  }

})();