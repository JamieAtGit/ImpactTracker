// Handle extension icon clicks
chrome.action.onClicked.addListener((tab) => {
  // Only inject overlay on Amazon pages
  if (tab.url.includes('amazon.co.uk') || tab.url.includes('amazon.com')) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'TOGGLE_OVERLAY',
      url: tab.url
    });
  } else {
    // Show notification for non-Amazon pages
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icon48.png',
      title: 'Eco Tracker',
      message: 'Please visit an Amazon product page to use the Eco Tracker.'
    });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "OPEN_OVERLAY") {
      // Send message to content script to show overlay
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {
          type: 'TOGGLE_OVERLAY',
          url: request.url
        });
      });
      
      sendResponse({ success: true });
    }
    
    if (request.type === "FETCH_ECO_INSIGHT") {
      const { href } = request.payload;
      const API_BASE = "https://impacttracker-production.up.railway.app";

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      fetch(`${API_BASE}/estimate_emissions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amazon_url: href,
          include_packaging: true
        }),
        signal: controller.signal
      })
        .then((res) => res.json())
        .then((json) => {
          clearTimeout(timeoutId);
          const a = json.data?.attributes || {};
          sendResponse({
            impact: a.eco_score_ml || "Unknown",
            summary: `CO₂: ${a.carbon_kg ?? "?"}kg, Material: ${a.material_type || "N/A"}`,
            recyclable: a.recyclability === "High"
              ? true
              : a.recyclability === "Low"
              ? false
              : null
          });
        })
        .catch((err) => {
          clearTimeout(timeoutId);
          const isTimeout = err.name === "AbortError";
          console.error(isTimeout ? "API request timed out" : "API fetch error:", err);
          sendResponse({
            impact: "Unknown",
            summary: isTimeout ? "Request timed out — API may be busy." : "Could not reach the API.",
            recyclable: null
          });
        });

      return true; // keep message channel open for async reply
    }
  });
  