// Persistent overlay that stays on page until manually closed
(function() {
  'use strict';

  let overlayVisible = false;
  let lastAnalysisData = null;
  let savedPostcode = '';
  let activeOverlayTab = 'calculator'; // 'calculator' | 'history'
  let ecoSettings = { showBadges: true, showTooltips: true, showAutoCard: true, showAiImaging: true };

  // ── Product image highlight ─────────────────────────────────────────────────
  // Applies a red (searching) or green (found) glow-border to the main product
  // image on Amazon product detail pages without affecting page layout.
  function _ensureEcoAnimStyles() {
    if (document.getElementById('eco-img-anim-styles')) return;
    const s = document.createElement('style');
    s.id = 'eco-img-anim-styles';
    s.textContent = `
      @keyframes ecoRedPulse {
        0%,100% { box-shadow: 0 0 0 3px rgba(239,68,68,0.88), 0 0 16px rgba(239,68,68,0.28); }
        50%      { box-shadow: 0 0 0 3px rgba(239,68,68,0.36), 0 0 28px rgba(239,68,68,0.10); }
      }
    `;
    document.head.appendChild(s);
  }

  function setProductImageHighlight(state) {
    const img =
      document.querySelector('#landingImage') ||
      document.querySelector('#imgTagWrapperId img') ||
      document.querySelector('#main-image') ||
      document.querySelector('.a-dynamic-image[data-old-hires]');
    if (!img) return;

    _ensureEcoAnimStyles();
    img.style.transition    = 'box-shadow 0.35s ease, border-radius 0.25s ease';
    img.style.borderRadius  = '8px';

    if (state === 'searching') {
      img.style.animation  = 'ecoRedPulse 1.4s ease-in-out infinite';
      img.style.boxShadow  = '0 0 0 3px rgba(239,68,68,0.88), 0 0 16px rgba(239,68,68,0.28)';
    } else if (state === 'found') {
      img.style.animation  = 'none';
      img.style.boxShadow  = '0 0 0 3px rgba(16,185,129,0.92), 0 0 22px rgba(16,185,129,0.38)';
    } else {
      img.style.animation     = 'none';
      img.style.boxShadow     = '';
      img.style.borderRadius  = '';
      img.style.transition    = '';
    }
  }

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TOGGLE_OVERLAY') {
      toggleOverlay(message.url);
      sendResponse({ success: true });
    }
  });
  
  // Load saved state
  chrome.storage.local.get(['lastAnalysisData', 'savedPostcode', 'overlayVisible', 'ecoSettings'], (data) => {
    if (data.lastAnalysisData) lastAnalysisData = data.lastAnalysisData;
    if (data.savedPostcode) savedPostcode = data.savedPostcode;
    if (data.ecoSettings) ecoSettings = { ...ecoSettings, ...data.ecoSettings };
    if (data.overlayVisible) {
      showOverlay(data.lastAnalysisData?.url || window.location.href);
    }
  });

  // Auto-analyse product detail pages — wait for DOM if needed
  function maybeAutoAnalyze() {
    if (document.querySelector('#productTitle')) {
      autoAnalyzeProductPage();
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', maybeAutoAnalyze);
  } else {
    maybeAutoAnalyze();
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
          <div style="display:flex;gap:6px;align-items:center;">
            <button class="eco-settings-btn" id="ecoSettingsBtn" title="Settings">⚙️</button>
            <button class="eco-close-btn" title="Close">×</button>
          </div>
        </div>

        <!-- Settings panel (hidden by default) -->
        <div id="eco-settings-panel" style="display:none;padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.03);">
          <div style="font-size:12px;font-weight:700;color:#94a3b8;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Settings</div>
          <div class="eco-setting-row" id="ecoSettingBadges">
            <span class="eco-setting-label">Show eco badges on products</span>
            <button class="eco-toggle-btn" data-setting="showBadges">ON</button>
          </div>
          <div class="eco-setting-row" id="ecoSettingTooltips">
            <span class="eco-setting-label">Show material tooltip on hover</span>
            <button class="eco-toggle-btn" data-setting="showTooltips">ON</button>
          </div>
          <div class="eco-setting-row" id="ecoSettingAutoCard">
            <span class="eco-setting-label">Auto-analyse product pages</span>
            <button class="eco-toggle-btn" data-setting="showAutoCard">ON</button>
          </div>
          <div class="eco-setting-row" id="ecoSettingAiImaging">
            <span class="eco-setting-label">AI image material analysis</span>
            <button class="eco-toggle-btn" data-setting="showAiImaging">ON</button>
          </div>
        </div>

        <div class="eco-tab-bar">
          <button class="eco-tab-btn eco-tab-active" id="ecoTabCalculator">🔍 Calculator</button>
          <button class="eco-tab-btn" id="ecoTabHistory">📋 History</button>
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
        width: 100% !important;
        padding: 14px 16px !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        box-sizing: border-box !important;
        -webkit-text-fill-color: #ffffff !important;
        outline: none !important;
      }

      .eco-input-field::placeholder {
        color: rgba(200, 200, 220, 0.7) !important;
        -webkit-text-fill-color: rgba(200, 200, 220, 0.7) !important;
      }

      .eco-input-field:focus {
        outline: none !important;
        border-color: #00d4ff !important;
        background: rgba(0, 50, 80, 0.95) !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.15) !important;
        -webkit-text-fill-color: #ffffff !important;
        color: #ffffff !important;
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
      
      /* ── Result card ── */
      .eco-result-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 18px;
        margin-top: 14px;
        animation: eco-slideIn 0.3s ease;
      }

      @keyframes eco-slideIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0);   }
      }

      .eco-product-name {
        font-size: 12px;
        font-weight: 500;
        color: #94a3b8;
        line-height: 1.4;
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
      }

      /* Carbon hero */
      .eco-carbon-hero {
        text-align: center;
        margin-bottom: 16px;
      }
      .eco-carbon-number {
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg,#00d4ff,#7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1px;
      }
      .eco-carbon-unit {
        font-size: 13px;
        color: #64748b;
        margin-left: 4px;
        font-weight: 500;
      }

      /* Score badges */
      .eco-scores-row {
        display: flex;
        align-items: stretch;
        gap: 0;
        margin-bottom: 14px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        overflow: hidden;
      }
      .eco-score-badge {
        flex: 1;
        padding: 10px 8px;
        text-align: center;
      }
      .eco-scores-divider {
        width: 1px;
        background: rgba(255,255,255,0.08);
      }
      .eco-score-method {
        font-size: 10px;
        color: #64748b;
        font-weight: 600;
        letter-spacing: 0.3px;
        margin-bottom: 5px;
        text-transform: uppercase;
      }
      .eco-score-value {
        display: inline-block;
        font-size: 16px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 6px;
      }

      /* Stats rows */
      .eco-stats-block {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 14px;
      }
      .eco-stat-row {
        display: flex;
        align-items: center;
        padding: 9px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        gap: 8px;
      }
      .eco-stat-row:last-child { border-bottom: none; }
      .eco-stat-icon { font-size: 13px; width: 18px; text-align: center; flex-shrink: 0; }
      .eco-stat-label { font-size: 11px; color: #64748b; font-weight: 500; flex: 1; }
      .eco-stat-value { font-size: 12px; color: #e2e8f0; font-weight: 600; text-align: right; }

      .eco-new-analysis-btn {
        display: block;
        width: 100%;
        padding: 11px;
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 10px;
        color: #a78bfa;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        margin-top: 4px;
      }
      .eco-new-analysis-btn:hover {
        background: rgba(124,58,237,0.25);
        border-color: rgba(124,58,237,0.5);
        color: #c4b5fd;
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

      .eco-settings-btn {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: #94a3b8 !important;
        width: 30px !important; height: 30px !important;
        border-radius: 8px !important;
        font-size: 14px !important; cursor: pointer !important;
        transition: all 0.2s !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
      }
      .eco-settings-btn:hover { background: rgba(255,255,255,0.15) !important; color: #e2e8f0 !important; }

      .eco-setting-row {
        display: flex !important; justify-content: space-between !important;
        align-items: center !important; padding: 7px 0 !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
      }
      .eco-setting-row:last-child { border-bottom: none !important; }
      .eco-setting-label { font-size: 12px !important; color: #cbd5e1 !important; }
      .eco-toggle-btn {
        padding: 3px 10px !important; border-radius: 9999px !important;
        font-size: 11px !important; font-weight: 700 !important;
        cursor: pointer !important; border: none !important;
        transition: all 0.2s !important; min-width: 38px !important;
      }
      .eco-toggle-on  { background: #10b981 !important; color: #fff !important; }
      .eco-toggle-off { background: rgba(255,255,255,0.1) !important; color: #64748b !important; }

      /* Cart summary */
      #eco-cart-summary {
        margin-top: 10px !important;
        padding: 10px 12px !important;
        background: rgba(0,212,255,0.06) !important;
        border: 1px solid rgba(0,212,255,0.15) !important;
        border-radius: 10px !important;
        font-size: 12px !important; color: #94a3b8 !important;
        display: flex !important; justify-content: space-between !important; align-items: center !important;
      }
      #eco-cart-summary .eco-cart-total { color: #00d4ff !important; font-weight: 700 !important; }
      #eco-cart-clear {
        padding: 2px 8px !important; border-radius: 6px !important;
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        color: #ef4444 !important; font-size: 10px !important;
        cursor: pointer !important; font-weight: 600 !important;
      }

      /* Export CSV button */
      #eco-export-csv {
        display: block !important; width: 100% !important;
        padding: 9px !important; margin-top: 12px !important;
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important; color: #94a3b8 !important;
        font-size: 12px !important; font-weight: 600 !important;
        cursor: pointer !important; transition: all 0.2s !important;
        text-align: center !important;
      }
      #eco-export-csv:hover { background: rgba(255,255,255,0.1) !important; color: #e2e8f0 !important; }

      /* In-page eco card (injected into Amazon product page) */
      #eco-inline-card {
        background: linear-gradient(135deg, rgba(15,15,35,0.95), rgba(22,33,62,0.95)) !important;
        border: 1px solid rgba(0,212,255,0.25) !important;
        border-radius: 12px !important;
        padding: 14px 16px !important;
        margin-bottom: 14px !important;
        font-family: 'Inter',-apple-system,BlinkMacSystemFont,sans-serif !important;
        font-size: 13px !important; color: #e2e8f0 !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
        position: relative !important; z-index: 100 !important;
      }
      .eco-card-header {
        display: flex !important; justify-content: space-between !important;
        align-items: center !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        margin-bottom: 10px !important;
      }
      .eco-card-title { font-size: 13px !important; font-weight: 700 !important; color: #00d4ff !important; }
      .eco-card-score {
        font-size: 13px !important; font-weight: 800 !important;
        padding: 2px 10px !important; border-radius: 6px !important;
      }
      .eco-card-row {
        display: flex !important; justify-content: space-between !important;
        align-items: center !important; padding: 5px 0 !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        font-size: 12px !important;
      }
      .eco-card-row:last-child { border-bottom: none !important; }
      .eco-card-key { color: #64748b !important; font-weight: 500 !important; }
      .eco-card-val { color: #e2e8f0 !important; font-weight: 600 !important; text-align: right !important; }
      .eco-card-carbon { color: #00d4ff !important; font-size: 15px !important; font-weight: 800 !important; }
      .eco-card-footer {
        margin-top: 10px !important; padding-top: 8px !important;
        border-top: 1px solid rgba(255,255,255,0.06) !important;
        display: flex !important; justify-content: space-between !important; align-items: center !important;
      }
      .eco-card-equiv { font-size: 11px !important; color: #10b981 !important; font-weight: 500 !important; }
      .eco-card-open-btn {
        font-size: 11px !important; color: #00d4ff !important;
        background: none !important; border: none !important;
        cursor: pointer !important; font-weight: 600 !important;
        padding: 0 !important;
      }
      .eco-card-open-btn:hover { text-decoration: underline !important; }

      /* AI imaging section — overlay */
      #eco-ai-imaging-section {
        margin-top: 12px !important;
        padding: 12px 14px !important;
        background: rgba(16,185,129,0.05) !important;
        border: 1px solid rgba(16,185,129,0.2) !important;
        border-radius: 10px !important;
      }
      .eco-ai-header {
        font-size: 11px !important; font-weight: 700 !important;
        color: #10b981 !important; text-transform: uppercase !important;
        letter-spacing: 0.5px !important; margin-bottom: 8px !important;
        display: flex !important; align-items: center !important; gap: 6px !important;
      }
      .eco-ai-badge {
        font-size: 9px !important; font-weight: 600 !important;
        padding: 1px 6px !important; border-radius: 9999px !important;
        background: rgba(16,185,129,0.15) !important;
        border: 1px solid rgba(16,185,129,0.3) !important;
        color: #6ee7b7 !important; text-transform: uppercase !important;
      }
      .eco-ai-loading {
        display: flex !important; align-items: center !important; gap: 8px !important;
        font-size: 11px !important; color: #64748b !important;
      }
      .eco-ai-spinner {
        width: 12px !important; height: 12px !important;
        border: 2px solid rgba(16,185,129,0.2) !important;
        border-top-color: #10b981 !important;
        border-radius: 50% !important;
        animation: eco-spin 0.8s linear infinite !important;
        flex-shrink: 0 !important;
      }
      @keyframes eco-spin { to { transform: rotate(360deg); } }
      .eco-ai-conf {
        font-size: 10px !important; font-weight: 600 !important;
        text-align: right !important; margin-bottom: 6px !important;
        text-transform: capitalize !important;
      }
      .eco-ai-component { margin-bottom: 6px !important; }
      .eco-ai-comp-row {
        display: flex !important; align-items: center !important;
        justify-content: space-between !important;
        font-size: 11px !important; margin-bottom: 3px !important;
      }
      .eco-ai-part { color: #e2e8f0 !important; font-weight: 600 !important; text-transform: capitalize !important; }
      .eco-ai-material { color: #94a3b8 !important; flex: 1 !important; text-align: center !important; }
      .eco-ai-pct { color: #e2e8f0 !important; font-weight: 700 !important; font-family: monospace !important; min-width: 32px !important; text-align: right !important; }
      .eco-ai-bar-track {
        width: 100% !important; height: 5px !important;
        background: rgba(255,255,255,0.08) !important;
        border-radius: 9999px !important; overflow: hidden !important;
      }
      .eco-ai-bar-fill {
        height: 100% !important;
        background: linear-gradient(90deg, #10b981, #06b6d4) !important;
        border-radius: 9999px !important;
        transition: width 0.5s ease !important;
      }
      .eco-ai-reasoning {
        font-size: 10px !important; color: #475569 !important;
        font-style: italic !important; margin-top: 2px !important;
      }
      .eco-ai-notes {
        font-size: 10px !important; color: #475569 !important;
        font-style: italic !important;
        border-top: 1px solid rgba(255,255,255,0.06) !important;
        padding-top: 6px !important; margin-top: 6px !important;
      }
      .eco-ai-error {
        font-size: 10px !important; color: #64748b !important; font-style: italic !important;
      }

      /* AI imaging — inline card compact section */
      #eco-inline-ai {
        margin-top: 10px !important;
        padding-top: 8px !important;
        border-top: 1px solid rgba(255,255,255,0.06) !important;
      }
      .eco-inline-ai-header {
        font-size: 10px !important; font-weight: 700 !important;
        color: #10b981 !important; text-transform: uppercase !important;
        letter-spacing: 0.4px !important; margin-bottom: 6px !important;
      }
      .eco-inline-ai-loading {
        font-size: 10px !important; color: #475569 !important;
        display: flex !important; align-items: center !important; gap: 5px !important;
      }
      .eco-inline-ai-spinner {
        width: 9px !important; height: 9px !important;
        border: 1.5px solid rgba(16,185,129,0.2) !important;
        border-top-color: #10b981 !important;
        border-radius: 50% !important;
        animation: eco-spin 0.8s linear infinite !important;
        flex-shrink: 0 !important;
      }
      .eco-inline-ai-row {
        display: flex !important; align-items: center !important;
        gap: 6px !important; margin-bottom: 4px !important; font-size: 10px !important;
      }
      .eco-inline-ai-label { color: #94a3b8 !important; min-width: 60px !important; font-weight: 500 !important; text-transform: capitalize !important; }
      .eco-inline-ai-track {
        flex: 1 !important; height: 4px !important;
        background: rgba(255,255,255,0.08) !important;
        border-radius: 9999px !important; overflow: hidden !important;
      }
      .eco-inline-ai-fill {
        height: 100% !important;
        background: linear-gradient(90deg, #10b981, #06b6d4) !important;
        border-radius: 9999px !important;
      }
      .eco-inline-ai-pct { color: #e2e8f0 !important; font-weight: 700 !important; font-family: monospace !important; min-width: 28px !important; text-align: right !important; }
    `;
    
    document.head.appendChild(style);
    // Dismiss any existing auto-banner when overlay opens
    const existingBanner = document.getElementById('eco-auto-banner');
    if (existingBanner) existingBanner.remove();

    document.body.appendChild(overlay);

    // Setup event listeners
    setupEventListeners();
    
    // Restore last analysis if available
    if (lastAnalysisData) {
      displayResults(lastAnalysisData);
    }
    renderCartSummary();
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

    // Tab buttons
    document.getElementById('ecoTabCalculator').addEventListener('click', () => switchTab('calculator'));
    document.getElementById('ecoTabHistory').addEventListener('click', () => switchTab('history'));

    // Form submission
    const form = document.getElementById('ecoEstimateForm');
    form.addEventListener('submit', handleFormSubmit);

    // Save postcode as user types
    const postcodeInput = document.getElementById('eco_postcode');
    postcodeInput.addEventListener('input', () => {
      const postcode = postcodeInput.value.trim();
      chrome.storage.local.set({ savedPostcode: postcode });
    });

    // Settings panel toggle
    const settingsBtn = document.getElementById('ecoSettingsBtn');
    if (settingsBtn) {
      settingsBtn.addEventListener('click', () => {
        const panel = document.getElementById('eco-settings-panel');
        if (panel) panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      });
    }

    // Settings toggles — read fresh from storage to avoid race with storage callback
    chrome.storage.local.get(['ecoSettings'], (data) => {
      if (data.ecoSettings) ecoSettings = { ...ecoSettings, ...data.ecoSettings };
      document.querySelectorAll('.eco-toggle-btn').forEach(btn => {
        const key = btn.dataset.setting;
        const isOn = ecoSettings[key] !== false;
        btn.textContent = isOn ? 'ON' : 'OFF';
        btn.className = 'eco-toggle-btn ' + (isOn ? 'eco-toggle-on' : 'eco-toggle-off');

        btn.addEventListener('click', () => {
          ecoSettings[key] = !ecoSettings[key];
          btn.textContent = ecoSettings[key] ? 'ON' : 'OFF';
          btn.className = 'eco-toggle-btn ' + (ecoSettings[key] ? 'eco-toggle-on' : 'eco-toggle-off');
          chrome.storage.local.set({ ecoSettings });
        });
      });
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
    setProductImageHighlight('searching');

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
        setProductImageHighlight('found');
        displayResults(analysisData);

        // AI image material analysis (if enabled)
        if (ecoSettings.showAiImaging) {
          const attr = json.data?.attributes || {};
          const imgUrl = attr.image_url;
          if (imgUrl && imgUrl !== 'Not found') {
            _appendAiImagingToOverlay(imgUrl, json.title || '', attr.gallery_images || [], attr.materials || {});
          }
        }
      } else {
        setProductImageHighlight('idle');
        showError('No data received from the server.');
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setProductImageHighlight('idle');
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
    const attr = data.attributes || {};
    const productTitle = response.title || data.title || 'Unknown Product';

    const mlScore   = attr.eco_score_ml || 'N/A';
    const ruleScore = attr.eco_score_rule_based || 'N/A';
    const carbonKg  = attr.carbon_kg;
    const confidence = attr.eco_score_ml_confidence;
    const origin    = attr.country_of_origin || attr.origin || null;
    const material  = attr.material_type || 'Unknown';
    const transport = attr.transport_mode || null;
    const weightKg  = attr.weight_kg || attr.estimated_weight_kg || attr.product_weight_kg || null;

    const scoreColor = s => ({ 'A+':'#10b981','A':'#10b981','B':'#84cc16','C':'#f59e0b','D':'#f97316','E':'#ef4444','F':'#dc2626' }[s] || '#6b7280');
    const scoreBg    = s => scoreColor(s) + '22';

    const scoreBadge = (label, score, icon) => `
      <div class="eco-score-badge">
        <div class="eco-score-method">${label}</div>
        <div class="eco-score-value" style="color:${scoreColor(score)};background:${scoreBg(score)};">
          ${icon} ${score}
        </div>
      </div>`;

    const statRow = (icon, label, value) => value ? `
      <div class="eco-stat-row">
        <span class="eco-stat-icon">${icon}</span>
        <span class="eco-stat-label">${label}</span>
        <span class="eco-stat-value">${value}</span>
      </div>` : '';

    output.innerHTML = `
      <div class="eco-result-card">

        <div class="eco-product-name">
          ${productTitle.length > 72 ? productTitle.substring(0,70)+'…' : productTitle}
        </div>

        <div class="eco-carbon-hero">
          <span class="eco-carbon-number">${carbonKg != null ? carbonKg : '—'}</span>
          <span class="eco-carbon-unit">kg CO₂e</span>
        </div>

        <div class="eco-scores-row">
          ${scoreBadge('🧠 ML Model', mlScore, getEmojiForScore(mlScore))}
          <div class="eco-scores-divider"></div>
          ${scoreBadge('📊 Rule-Based', ruleScore, getEmojiForScore(ruleScore))}
        </div>

        <div class="eco-stats-block">
          ${statRow('🧱', 'Material',   material)}
          ${statRow('⚖️', 'Est. Weight', weightKg ? `${weightKg} kg` : null)}
          ${statRow('🚢', 'Transport',  transport ? `${getTransportEmoji(transport)} ${transport}` : null)}
          ${statRow('🌐', 'Origin',     origin)}
          ${statRow('🎯', 'Confidence', confidence ? `${confidence}%` : null)}
        </div>

        ${getCompactEquivalence(attr)}

        <button class="eco-new-analysis-btn" id="ecoNewAnalysisBtn">
          🔄 Analyse Another Product
        </button>
      </div>
    `;

    const newAnalysisBtn = document.getElementById('ecoNewAnalysisBtn');
    if (newAnalysisBtn) {
      newAnalysisBtn.addEventListener('click', startNewEcoAnalysis);
    }
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
  function switchTab(tab) {
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
      renderCartSummary();
    } else {
      calcPane.style.display = 'none';
      histPane.style.display = 'block';
      calcBtn.classList.remove('eco-tab-active');
      histBtn.classList.add('eco-tab-active');
      renderHistory();
    }
  }

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

  // ── Cart carbon tracker ────────────────────────────────────────────────────
  function renderCartSummary() {
    const container = document.getElementById('eco-cart-summary');
    chrome.storage.local.get(['cartItems'], (data) => {
      const items = (data.cartItems || []).filter(i => i.carbonKg != null);
      if (items.length === 0) {
        if (container) container.style.display = 'none';
        return;
      }
      const total = items.reduce((s, i) => s + parseFloat(i.carbonKg || 0), 0);
      // Inject cart summary div if it doesn't exist
      let el = document.getElementById('eco-cart-summary');
      if (!el) {
        el = document.createElement('div');
        el.id = 'eco-cart-summary';
        const pane = document.getElementById('ecoTabPaneCalculator');
        if (pane) pane.appendChild(el);
      }
      el.style.display = 'flex';
      el.innerHTML = `
        <span>🛒 Cart: <span class="eco-cart-total">${total.toFixed(2)} kg CO₂</span> &nbsp;(${items.length} item${items.length > 1 ? 's' : ''})</span>
        <button id="eco-cart-clear">Clear</button>
      `;
      document.getElementById('eco-cart-clear')?.addEventListener('click', () => {
        chrome.storage.local.remove('cartItems');
        el.style.display = 'none';
      });
    });
  }

  // ── Export history as CSV ──────────────────────────────────────────────────
  function exportHistoryCSV() {
    chrome.storage.local.get(['analysisHistory'], (data) => {
      const history = data.analysisHistory || [];
      if (history.length === 0) return;
      const headers = ['Title', 'Carbon kg CO2', 'ML Score', 'Date', 'URL'];
      const rows = history.map(h => [
        '"' + (h.title || '').replace(/"/g, '""').substring(0, 100) + '"',
        h.carbonKg != null ? h.carbonKg : '',
        h.mlScore || '',
        new Date(h.timestamp).toLocaleString('en-GB'),
        '"' + (h.url || '') + '"',
      ]);
      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\r\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `eco-impact-${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  function renderHistory() {
    const container = document.getElementById('ecoHistoryList');
    if (!container) return;
    chrome.storage.local.get(['analysisHistory'], (data) => {
      const history = data.analysisHistory || [];
      if (history.length === 0) {
        container.innerHTML = '<div class="eco-history-empty">No analyses yet.<br>Calculate emissions for a product to see history here.</div>';
        renderCartSummary();
        return;
      }
      container.innerHTML = history.map((item, i) => {
        const date = new Date(item.timestamp).toLocaleDateString('en-GB', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' });
        return `
          <div class="eco-history-item" data-history-index="${i}">
            <div class="eco-history-title">📦 ${item.title}</div>
            <div class="eco-history-meta">
              <span class="eco-history-carbon">${item.carbonKg ? item.carbonKg + ' kg CO₂' : 'N/A'}</span>
              <span>${item.mlScore || ''} &bull; ${date}</span>
            </div>
          </div>`;
      }).join('');

      container.querySelectorAll('.eco-history-item').forEach((item, i) => {
        item.addEventListener('click', () => loadHistoryItem(i));
      });

      // Export CSV button
      const exportBtn = document.createElement('button');
      exportBtn.id = 'eco-export-csv';
      exportBtn.textContent = '📥 Export History as CSV';
      container.appendChild(exportBtn);
      exportBtn.addEventListener('click', exportHistoryCSV);

      renderCartSummary();
    });
  }

  function loadHistoryItem(index) {
    chrome.storage.local.get(['analysisHistory'], (data) => {
      const item = (data.analysisHistory || [])[index];
      if (!item) return;
      // Re-fill URL and switch to calculator
      switchTab('calculator');
      const urlInput = document.getElementById('eco_amazon_url');
      if (urlInput) urlInput.value = item.url;
    });
  }

  // ── Auto-analyse on product detail pages ──────────────────────────────────
  function autoAnalyzeProductPage() {
    if (document.getElementById('eco-persistent-overlay')) return; // overlay already open
    if (!ecoSettings.showAutoCard) return;

    const url = window.location.href;
    const asinMatch = url.match(/\/dp\/([A-Z0-9]{10})/);
    if (!asinMatch) return;
    const asin = asinMatch[1];

    // ── Detect material from title immediately (no API needed) ─────────────
    const titleEl = document.querySelector('#productTitle');
    const productTitle = titleEl?.textContent?.trim() || '';

    // ── Inject inline eco card into the product page buy-box area ──────────
    const rightCol = document.querySelector('#rightCol') || document.querySelector('#desktop_buybox') || document.querySelector('#buybox');
    let inlineCard = null;

    if (rightCol) {
      inlineCard = document.createElement('div');
      inlineCard.id = 'eco-inline-card';
      inlineCard.innerHTML = `
        <div class="eco-card-header">
          <span class="eco-card-title">🌱 Eco Impact</span>
          <span class="eco-card-score" id="eco-card-score-badge" style="background:rgba(100,116,139,0.2);color:#64748b;">Calculating…</span>
        </div>
        <div id="eco-card-rows">
          <div class="eco-card-row"><span class="eco-card-key">Carbon footprint</span><span class="eco-card-val eco-card-carbon" id="eco-card-carbon">—</span></div>
          <div class="eco-card-row"><span class="eco-card-key">Material</span><span class="eco-card-val" id="eco-card-material">Detecting…</span></div>
          <div class="eco-card-row"><span class="eco-card-key">Origin</span><span class="eco-card-val" id="eco-card-origin">—</span></div>
          <div class="eco-card-row"><span class="eco-card-key">Transport</span><span class="eco-card-val" id="eco-card-transport">—</span></div>
        </div>
        <div class="eco-card-footer">
          <span class="eco-card-equiv" id="eco-card-equiv"></span>
          <button class="eco-card-open-btn" id="eco-card-open-btn">Full analysis →</button>
        </div>
      `;
      rightCol.insertBefore(inlineCard, rightCol.firstChild);

      // "Full analysis" opens the main overlay
      document.getElementById('eco-card-open-btn')?.addEventListener('click', () => {
        if (!document.getElementById('eco-persistent-overlay')) {
          showOverlay(url);
        }
      });
    }

    // ── Inject minimal CSS for inline card (if not already in page) ─────────
    if (!document.getElementById('eco-inline-card-style')) {
      const s = document.createElement('style');
      s.id = 'eco-inline-card-style';
      s.textContent = `
        #eco-inline-card { background:linear-gradient(135deg,rgba(15,15,35,0.95),rgba(22,33,62,0.95)) !important; border:1px solid rgba(0,212,255,0.25) !important; border-radius:12px !important; padding:14px 16px !important; margin-bottom:14px !important; font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif !important; font-size:13px !important; color:#e2e8f0 !important; box-shadow:0 4px 20px rgba(0,0,0,0.25) !important; }
        .eco-card-header { display:flex !important; justify-content:space-between !important; align-items:center !important; padding-bottom:10px !important; border-bottom:1px solid rgba(255,255,255,0.08) !important; margin-bottom:10px !important; }
        .eco-card-title { font-size:13px !important; font-weight:700 !important; color:#00d4ff !important; }
        .eco-card-score { font-size:12px !important; font-weight:800 !important; padding:2px 10px !important; border-radius:6px !important; }
        .eco-card-row { display:flex !important; justify-content:space-between !important; align-items:center !important; padding:5px 0 !important; border-bottom:1px solid rgba(255,255,255,0.04) !important; font-size:12px !important; }
        .eco-card-row:last-child { border-bottom:none !important; }
        .eco-card-key { color:#64748b !important; font-weight:500 !important; }
        .eco-card-val { color:#e2e8f0 !important; font-weight:600 !important; text-align:right !important; }
        .eco-card-carbon { color:#00d4ff !important; font-size:15px !important; font-weight:800 !important; }
        .eco-card-footer { margin-top:10px !important; padding-top:8px !important; border-top:1px solid rgba(255,255,255,0.06) !important; display:flex !important; justify-content:space-between !important; align-items:center !important; }
        .eco-card-equiv { font-size:11px !important; color:#10b981 !important; font-weight:500 !important; }
        .eco-card-open-btn { font-size:11px !important; color:#00d4ff !important; background:none !important; border:none !important; cursor:pointer !important; font-weight:600 !important; padding:0 !important; }
      `;
      document.head.appendChild(s);
    }

    // ── Cart tracker: listen for add-to-cart click ────────────────────────
    let pendingCarbon = null;
    const cartBtn = document.getElementById('add-to-cart-button');
    if (cartBtn && !cartBtn.dataset.ecoCartListenerAttached) {
      cartBtn.dataset.ecoCartListenerAttached = 'true';
      cartBtn.addEventListener('click', () => {
        const entry = {
          asin,
          title: productTitle.substring(0, 80),
          carbonKg: pendingCarbon,
          timestamp: Date.now(),
        };
        chrome.storage.local.get(['cartItems'], (d) => {
          let items = d.cartItems || [];
          items = items.filter(i => i.asin !== asin); // deduplicate
          items.unshift(entry);
          items = items.slice(0, 10);
          chrome.storage.local.set({ cartItems: items });
        });
      });
    }

    // ── Fetch full emissions data ─────────────────────────────────────────
    chrome.storage.local.get(['analysisHistory', 'savedPostcode'], async (data) => {
      const pc = data.savedPostcode || 'SW1A 1AA';

      // Check cache first (6 hour window)
      const history = data.analysisHistory || [];
      const cached = history.find(h => h.url && h.url.includes(asin) && Date.now() - h.timestamp < 21600000);

      if (cached) {
        updateInlineCard(inlineCard, cached.title, cached.carbonKg, cached.mlScore, cached.material, null, null, true);
        pendingCarbon = cached.carbonKg;
        return;
      }

      const BASE_URL = 'https://impacttracker-production.up.railway.app';
      setProductImageHighlight('searching');
      try {
        const res = await fetch(`${BASE_URL}/estimate_emissions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amazon_url: url, postcode: pc, include_packaging: true })
        });
        const json = await res.json();
        if (json?.data?.attributes) {
          const attr = json.data.attributes;
          pendingCarbon = attr.carbon_kg;
          setProductImageHighlight('found');
          updateInlineCard(
            inlineCard,
            json.title,
            attr.carbon_kg,
            attr.eco_score_ml,
            attr.material_type,
            attr.country_of_origin || attr.origin,
            attr.transport_mode,
            false
          );
          saveToHistory({ url, title: json.title, data: json.data, timestamp: Date.now() });

          // AI image material analysis (if enabled)
          if (ecoSettings.showAiImaging && inlineCard) {
            const imgUrl = attr.image_url;
            if (imgUrl && imgUrl !== 'Not found') {
              _appendAiImagingToInlineCard(inlineCard, imgUrl, json.title || '', attr.gallery_images || [], attr.materials || {});
            }
          }
        } else {
          setProductImageHighlight('idle');
        }
      } catch {
        setProductImageHighlight('idle');
        if (inlineCard) {
          const carbonEl = document.getElementById('eco-card-carbon');
          if (carbonEl) carbonEl.textContent = 'Unavailable';
        }
      }
    });
  }

  function updateInlineCard(card, title, carbonKg, mlScore, material, origin, transport, fromCache) {
    if (!card) return;

    const scoreColors = { 'A+':'#10b981','A':'#10b981','B':'#84cc16','C':'#f59e0b','D':'#f97316','E':'#ef4444','F':'#dc2626' };
    const scoreColor = scoreColors[mlScore] || '#6b7280';

    const scoreBadge = document.getElementById('eco-card-score-badge');
    if (scoreBadge) {
      scoreBadge.textContent = mlScore || '?';
      scoreBadge.style.background = scoreColor + '33';
      scoreBadge.style.color = scoreColor;
    }

    const carbonEl = document.getElementById('eco-card-carbon');
    if (carbonEl) carbonEl.textContent = carbonKg != null ? `${carbonKg} kg CO₂e` : '—';

    const matEl = document.getElementById('eco-card-material');
    if (matEl) matEl.textContent = material || '—';

    const origEl = document.getElementById('eco-card-origin');
    if (origEl) origEl.textContent = origin || '—';

    const transEl = document.getElementById('eco-card-transport');
    if (transEl) transEl.textContent = transport || '—';

    // Equivalence line
    const equivEl = document.getElementById('eco-card-equiv');
    if (equivEl && carbonKg) {
      const kg = parseFloat(carbonKg);
      const trees = kg / 21;
      equivEl.textContent = trees < 1
        ? `≈ ${Math.round(trees * 365)} days of tree absorption`
        : `≈ ${Math.ceil(trees)} tree${Math.ceil(trees) > 1 ? 's' : ''} to offset`;
    }

    if (fromCache && card) {
      const cacheNote = document.createElement('div');
      cacheNote.style.cssText = 'font-size:10px;color:#475569;text-align:right;margin-top:4px;';
      cacheNote.textContent = 'cached result';
      card.appendChild(cacheNote);
    }
  }

  // ── AI image material analysis ────────────────────────────────────────────────

  async function _fetchAiMaterialAnalysis(imageUrl, title, galleryImages, specMaterials) {
    const BASE_URL = 'https://impacttracker-production.up.railway.app';
    const res = await fetch(`${BASE_URL}/api/analyse-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_url: imageUrl,
        title: title,
        gallery_images: galleryImages,
        spec_materials: specMaterials
      })
    });
    if (!res.ok) throw new Error('AI analysis failed');
    return res.json();
  }

  function _appendAiImagingToOverlay(imageUrl, title, galleryImages, specMaterials) {
    const output = document.getElementById('ecoOutput');
    if (!output) return;

    const section = document.createElement('div');
    section.id = 'eco-ai-imaging-section';
    section.innerHTML = `
      <div class="eco-ai-header">🔍 AI Material Analysis <span class="eco-ai-badge">Beta</span></div>
      <div id="eco-ai-loading" class="eco-ai-loading">
        <div class="eco-ai-spinner"></div>
        <span>Scanning product image…</span>
      </div>
      <div id="eco-ai-results" style="display:none;"></div>
    `;
    output.appendChild(section);

    _fetchAiMaterialAnalysis(imageUrl, title, galleryImages, specMaterials)
      .then(data => {
        const loadingEl = document.getElementById('eco-ai-loading');
        const resultsEl = document.getElementById('eco-ai-results');
        if (loadingEl) loadingEl.style.display = 'none';
        if (!resultsEl || !data?.components?.length) return;

        const confColor = data.confidence === 'high' ? '#10b981' : data.confidence === 'medium' ? '#f59e0b' : '#ef4444';
        const barsHtml = data.components.map(c => `
          <div class="eco-ai-component">
            <div class="eco-ai-comp-row">
              <span class="eco-ai-part">${c.part}</span>
              <span class="eco-ai-material">${c.material}</span>
              <span class="eco-ai-pct">${c.percentage}%</span>
            </div>
            <div class="eco-ai-bar-track">
              <div class="eco-ai-bar-fill" style="width:${c.percentage}%"></div>
            </div>
            ${c.reasoning ? `<div class="eco-ai-reasoning">${c.reasoning}</div>` : ''}
          </div>
        `).join('');

        resultsEl.innerHTML = `
          <div class="eco-ai-conf" style="color:${confColor};">${data.confidence} confidence</div>
          ${barsHtml}
          ${data.notes ? `<div class="eco-ai-notes">${data.notes}</div>` : ''}
        `;
        resultsEl.style.display = 'block';
      })
      .catch(() => {
        const loadingEl = document.getElementById('eco-ai-loading');
        if (loadingEl) {
          loadingEl.innerHTML = '<span class="eco-ai-error">AI analysis unavailable</span>';
        }
      });
  }

  function _appendAiImagingToInlineCard(card, imageUrl, title, galleryImages, specMaterials) {
    const aiSection = document.createElement('div');
    aiSection.id = 'eco-inline-ai';
    aiSection.innerHTML = `
      <div class="eco-inline-ai-header">🔍 AI Materials</div>
      <div id="eco-inline-ai-loading" class="eco-inline-ai-loading">
        <div class="eco-inline-ai-spinner"></div>
        <span>Scanning…</span>
      </div>
      <div id="eco-inline-ai-results" style="display:none;"></div>
    `;
    card.appendChild(aiSection);

    _fetchAiMaterialAnalysis(imageUrl, title, galleryImages, specMaterials)
      .then(data => {
        const loadingEl = document.getElementById('eco-inline-ai-loading');
        const resultsEl = document.getElementById('eco-inline-ai-results');
        if (loadingEl) loadingEl.style.display = 'none';
        if (!resultsEl || !data?.components?.length) return;

        // Show top 3 components only for compact card
        const top = data.components.slice(0, 3);
        resultsEl.innerHTML = top.map(c => `
          <div class="eco-inline-ai-row">
            <span class="eco-inline-ai-label">${c.part}</span>
            <div class="eco-inline-ai-track">
              <div class="eco-inline-ai-fill" style="width:${c.percentage}%"></div>
            </div>
            <span class="eco-inline-ai-pct">${c.percentage}%</span>
          </div>
        `).join('');
        resultsEl.style.display = 'block';
      })
      .catch(() => {
        const loadingEl = document.getElementById('eco-inline-ai-loading');
        if (loadingEl) loadingEl.style.display = 'none';
      });
  }

  // Local function for new analysis
  function startNewEcoAnalysis() {
    switchTab('calculator');
    const urlInput = document.getElementById('eco_amazon_url');
    if (urlInput) {
      urlInput.value = window.location.href;
      urlInput.focus();
    }
    const output = document.getElementById('ecoOutput');
    if (output) output.innerHTML = '';
    chrome.storage.local.remove('lastAnalysisData');
    lastAnalysisData = null;
  }
})();