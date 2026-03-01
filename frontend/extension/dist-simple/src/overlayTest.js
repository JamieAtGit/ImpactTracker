// Simple test to verify script is loading
console.log('🌱 Eco Tracker: Overlay script loaded!');

// Create a simple test div to confirm injection works
const testDiv = document.createElement('div');
testDiv.id = 'eco-tracker-test';
testDiv.style.cssText = `
  position: fixed;
  top: 20px;
  right: 20px;
  background: #00d4ff;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  z-index: 999999;
  font-family: Arial, sans-serif;
  font-size: 14px;
  font-weight: bold;
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
`;
testDiv.textContent = '🌱 Eco Tracker Active';

// Wait for DOM to be ready
if (document.body) {
  document.body.appendChild(testDiv);
  console.log('✅ Test div appended to body');
  
  // Auto-hide after 3 seconds, then load real overlay
  setTimeout(() => {
    testDiv.remove();
    console.log('🚀 Loading full overlay...');
    
    // Now load the full overlay script
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('overlay.js');
    document.head.appendChild(script);
  }, 3000);
} else {
  // Wait for body to be available
  document.addEventListener('DOMContentLoaded', () => {
    document.body.appendChild(testDiv);
    console.log('✅ Test div appended after DOMContentLoaded');
  });
}