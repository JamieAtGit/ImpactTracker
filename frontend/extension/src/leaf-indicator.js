// Floating leaf indicator for Amazon pages
(function() {
  'use strict';
  
  // Check if indicator already exists
  if (document.getElementById('eco-leaf-indicator')) {
    return;
  }
  
  // Only run on Amazon product pages
  if (!window.location.href.includes('amazon.co.uk') && !window.location.href.includes('amazon.com')) {
    return;
  }
  
  // Create floating leaf indicator
  const leafIndicator = document.createElement('div');
  leafIndicator.id = 'eco-leaf-indicator';
  leafIndicator.innerHTML = `
    <div class="leaf-circle">
      <span class="leaf-emoji">🌱</span>
      <span class="leaf-text">Eco</span>
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    #eco-leaf-indicator {
      position: fixed;
      top: 50%;
      right: 20px;
      transform: translateY(-50%);
      z-index: 999998;
      cursor: pointer;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .leaf-circle {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #00d4ff, #7c3aed);
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
      transition: all 0.3s ease;
    }
    
    .leaf-circle:hover {
      transform: scale(1.1);
      box-shadow: 0 12px 35px rgba(0, 212, 255, 0.6);
    }
    
    .leaf-emoji {
      font-size: 20px;
      line-height: 1;
      margin-bottom: 2px;
    }
    
    .leaf-text {
      font-size: 10px;
      font-weight: 600;
      color: white;
      line-height: 1;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    #eco-leaf-indicator.pulse {
      animation: leafPulse 2s infinite;
    }
    
    @keyframes leafPulse {
      0%, 100% { transform: translateY(-50%) scale(1); }
      50% { transform: translateY(-50%) scale(1.05); }
    }
  `;
  
  document.head.appendChild(style);
  document.body.appendChild(leafIndicator);
  
  // Add pulse animation initially
  leafIndicator.classList.add('pulse');
  
  // Remove pulse after 5 seconds
  setTimeout(() => {
    leafIndicator.classList.remove('pulse');
  }, 5000);
  
  // Click handler to open overlay
  leafIndicator.addEventListener('click', () => {
    // Send message to show overlay
    chrome.runtime.sendMessage({
      type: 'OPEN_OVERLAY',
      url: window.location.href
    });
    
    // Visual feedback
    leafIndicator.style.transform = 'translateY(-50%) scale(0.95)';
    setTimeout(() => {
      leafIndicator.style.transform = 'translateY(-50%) scale(1)';
    }, 150);
  });
  
  // Update indicator based on page changes
  let lastUrl = window.location.href;
  const observer = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      // Re-add pulse when URL changes
      leafIndicator.classList.add('pulse');
      setTimeout(() => {
        leafIndicator.classList.remove('pulse');
      }, 3000);
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
})();