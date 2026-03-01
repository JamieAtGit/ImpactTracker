// Background script to handle extension icon clicks
chrome.action.onClicked.addListener((tab) => {
  // Check if we're on an Amazon page
  if (tab.url && (tab.url.includes('amazon.co.uk') || tab.url.includes('amazon.com'))) {
    // Send message to content script to toggle overlay
    chrome.tabs.sendMessage(tab.id, { action: 'toggleOverlay' }, (response) => {
      if (chrome.runtime.lastError) {
        console.log('Content script not ready, injecting...');
        // If content script isn't ready, inject it
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content-overlay.js']
        });
      }
    });
  } else {
    // Not on Amazon page, show notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Eco Tracker',
      message: 'This extension only works on Amazon product pages.'
    });
  }
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'ping') {
    sendResponse({ status: 'ok' });
  } else if (request.action === 'makeApiCall') {
    // Make API call from background script to avoid CORS issues
    fetch(request.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data)
    })
    .then(response => {
      const isOk = response.ok;
      return response.json().then(data => ({
        ok: isOk,
        data: data,
        error: isOk ? null : (data.error || 'API request failed')
      }));
    })
    .then(result => {
      sendResponse(result);
    })
    .catch(error => {
      console.error('API call failed:', error);
      sendResponse({
        ok: false,
        error: error.message || 'Network error'
      });
    });
    
    // Return true to indicate we'll respond asynchronously
    return true;
  }
});