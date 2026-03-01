// Overlay injection script - creates persistent eco tracker widget
(function() {
  // Check if overlay already exists
  if (document.getElementById('eco-tracker-overlay')) {
    return;
  }

  // Create overlay container
  const overlay = document.createElement('div');
  overlay.id = 'eco-tracker-overlay';
  overlay.className = 'eco-tracker-overlay';
  
  // Initial HTML structure
  overlay.innerHTML = `
    <div class="eco-overlay-container">
      <div class="eco-overlay-header">
        <h3 class="eco-overlay-title">🌱 Eco Tracker</h3>
        <div class="eco-overlay-controls">
          <button class="eco-minimize-btn" title="Minimize">_</button>
          <button class="eco-close-btn" title="Close">×</button>
        </div>
      </div>
      
      <div class="eco-overlay-content">
        <form class="eco-estimate-form" id="ecoEstimateForm">
          <div class="eco-input-group">
            <input 
              type="text" 
              id="eco_amazon_url" 
              class="eco-input-field" 
              placeholder="Amazon product URL" 
              required
            />
            <button type="button" class="eco-use-current-btn" id="useCurrentUrl" title="Use current page URL">
              📍
            </button>
          </div>
          <div class="eco-input-group">
            <input 
              type="text" 
              id="eco_postcode" 
              class="eco-input-field" 
              placeholder="Enter your postcode" 
            />
          </div>
          <button type="submit" id="ecoAnalyze" class="eco-btn-primary">
            <span id="ecoButtonText">Estimate Emissions</span>
            <div class="eco-spinner" id="ecoSpinner" style="display: none;"></div>
          </button>
        </form>
        
        <div id="ecoOutput" class="eco-output"></div>
      </div>
      
      <div class="eco-overlay-minimized" style="display: none;">
        <span class="eco-minimized-text">🌱 Eco Tracker</span>
      </div>
    </div>
  `;
  
  // Append to body
  document.body.appendChild(overlay);
  
  // Load saved state
  chrome.storage.local.get(['ecoTrackerState', 'lastAnalysis'], (data) => {
    if (data.ecoTrackerState) {
      restoreState(data.ecoTrackerState);
    }
    if (data.lastAnalysis && data.lastAnalysis.url === window.location.href) {
      displayResults(data.lastAnalysis.results);
    }
  });
  
  // Event listeners
  setupEventListeners();
  
  function setupEventListeners() {
    // Close button
    document.querySelector('.eco-close-btn').addEventListener('click', () => {
      overlay.style.display = 'none';
      chrome.storage.local.set({ ecoTrackerState: { visible: false } });
    });
    
    // Minimize/Maximize
    const minimizeBtn = document.querySelector('.eco-minimize-btn');
    const content = document.querySelector('.eco-overlay-content');
    const minimizedView = document.querySelector('.eco-overlay-minimized');
    const container = document.querySelector('.eco-overlay-container');
    
    minimizeBtn.addEventListener('click', () => {
      const isMinimized = content.style.display === 'none';
      if (isMinimized) {
        // Maximize
        content.style.display = 'block';
        minimizedView.style.display = 'none';
        container.classList.remove('minimized');
        minimizeBtn.textContent = '_';
      } else {
        // Minimize
        content.style.display = 'none';
        minimizedView.style.display = 'flex';
        container.classList.add('minimized');
        minimizeBtn.textContent = '□';
      }
      saveState();
    });
    
    // Click on minimized view to expand
    minimizedView.addEventListener('click', () => {
      content.style.display = 'block';
      minimizedView.style.display = 'none';
      container.classList.remove('minimized');
      minimizeBtn.textContent = '_';
      saveState();
    });
    
    // Use current URL button
    document.getElementById('useCurrentUrl').addEventListener('click', () => {
      document.getElementById('eco_amazon_url').value = window.location.href;
    });
    
    // Form submission
    const form = document.getElementById('ecoEstimateForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Make draggable
    makeDraggable(overlay);
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
    
    // Use production API
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
        displayResults(json);
        // Save results
        chrome.storage.local.set({
          lastAnalysis: {
            url: url,
            results: json,
            timestamp: Date.now()
          }
        });
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
            ✨ New
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
    
    // Save state
    saveState();
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
        <span class="eco-equiv-item">🌳 ${trees} trees to offset</span>
      </div>
    `;
  }
  
  // Make widget draggable
  function makeDraggable(element) {
    const header = element.querySelector('.eco-overlay-header');
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;
    
    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    
    function dragStart(e) {
      if (e.target.classList.contains('eco-minimize-btn') || 
          e.target.classList.contains('eco-close-btn')) {
        return;
      }
      
      initialX = e.clientX - xOffset;
      initialY = e.clientY - yOffset;
      
      if (e.target === header || header.contains(e.target)) {
        isDragging = true;
        header.style.cursor = 'grabbing';
      }
    }
    
    function drag(e) {
      if (isDragging) {
        e.preventDefault();
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;
        
        xOffset = currentX;
        yOffset = currentY;
        
        element.style.transform = `translate(${currentX}px, ${currentY}px)`;
      }
    }
    
    function dragEnd(e) {
      initialX = currentX;
      initialY = currentY;
      isDragging = false;
      header.style.cursor = 'grab';
      saveState();
    }
  }
  
  // State management
  function saveState() {
    const overlay = document.getElementById('eco-tracker-overlay');
    const content = document.querySelector('.eco-overlay-content');
    const container = document.querySelector('.eco-overlay-container');
    
    const state = {
      visible: overlay.style.display !== 'none',
      minimized: content.style.display === 'none',
      position: overlay.style.transform,
      postcode: document.getElementById('eco_postcode').value
    };
    
    chrome.storage.local.set({ ecoTrackerState: state });
  }
  
  function restoreState(state) {
    const overlay = document.getElementById('eco-tracker-overlay');
    const content = document.querySelector('.eco-overlay-content');
    const minimizedView = document.querySelector('.eco-overlay-minimized');
    const container = document.querySelector('.eco-overlay-container');
    const minimizeBtn = document.querySelector('.eco-minimize-btn');
    
    if (!state.visible) {
      overlay.style.display = 'none';
    }
    
    if (state.minimized) {
      content.style.display = 'none';
      minimizedView.style.display = 'flex';
      container.classList.add('minimized');
      minimizeBtn.textContent = '□';
    }
    
    if (state.position) {
      overlay.style.transform = state.position;
    }
    
    if (state.postcode) {
      document.getElementById('eco_postcode').value = state.postcode;
    }
  }
  
  // Global function for new analysis
  window.startNewEcoAnalysis = function() {
    document.getElementById('eco_amazon_url').value = '';
    document.getElementById('eco_postcode').value = '';
    document.getElementById('ecoOutput').innerHTML = '';
    document.getElementById('eco_amazon_url').focus();
    chrome.storage.local.remove('lastAnalysis');
  };
})();