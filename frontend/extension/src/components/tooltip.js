// ── Extension settings (loaded from storage, gating badge + tooltip display) ─
let ecoSettings = { showBadges: true, showTooltips: true };
chrome.storage.local.get(['ecoSettings'], (data) => {
  if (data.ecoSettings) ecoSettings = { ...ecoSettings, ...data.ecoSettings };
});
// Keep settings in sync when user changes them in the overlay
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes.ecoSettings) {
    ecoSettings = { ...ecoSettings, ...changes.ecoSettings.newValue };
  }
});

// Active filter state persists across enhanceTooltips re-runs
let activeEcoFilter = 'all'; // 'all' | 'Low' | 'Low-Moderate' | 'Moderate' | 'High'

// Smart cleanup function - only cleans up broken/orphaned tooltips
function cleanupBrokenTooltips() {
  console.log("🧹 Cleaning up broken tooltips");
  
  // Find and clean up elements that have the flag but no working handlers
  const enhancedElements = document.querySelectorAll('[data-enhanced-tooltip-attached="true"]');
  enhancedElements.forEach(el => {
    // Check if element still exists in DOM and has working handlers
    if (!document.contains(el) || (!el._ecoTooltip && !el._ecoTooltipHandlers)) {
      // Element is orphaned or broken - clean it up
      if (el._ecoTooltip) {
        el._ecoTooltip.remove();
        el._ecoTooltip = null;
      }
      if (el._ecoTooltipHandlers) {
        el.removeEventListener("mouseenter", el._ecoTooltipHandlers.mouseEnterHandler);
        el.removeEventListener("mouseleave", el._ecoTooltipHandlers.mouseLeaveHandler);
        if (el._ecoTooltipHandlers.mouseMoveHandler) {
          el.removeEventListener("mousemove", el._ecoTooltipHandlers.mouseMoveHandler);
        }
        el._ecoTooltipHandlers = null;
      }
      el.style.borderBottom = '';
      el.dataset.enhancedTooltipAttached = "false";
    }
  });
  
  // Remove orphaned tooltip elements
  const orphanedTooltips = document.querySelectorAll('.eco-tooltip');
  orphanedTooltips.forEach(tooltip => {
    let isAttached = false;
    enhancedElements.forEach(el => {
      if (el._ecoTooltip === tooltip) {
        isAttached = true;
      }
    });
    if (!isAttached) {
      tooltip.remove();
    }
  });
}

function createTooltip(html) {
  const tooltip = document.createElement("div");
  tooltip.className = "eco-tooltip";
  tooltip.innerHTML = html;
  
  // Enhanced CSS styles to ensure visibility
  tooltip.style.cssText = `
    position: absolute !important;
    z-index: 10000 !important;
    background: rgba(0, 0, 0, 0.9) !important;
    color: white !important;
    padding: 12px !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-family: Arial, sans-serif !important;
    line-height: 1.4 !important;
    max-width: 300px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    opacity: 0 !important;
    transition: opacity 0.2s ease !important;
    pointer-events: none !important;
    word-wrap: break-word !important;
  `;
  
  document.body.appendChild(tooltip);
  console.log("🔧 Created tooltip element:", tooltip);
  return tooltip;
}

function attachTooltipEvents(target, html) {
  // Check if tooltip is already properly attached and working
  if (target.dataset.enhancedTooltipAttached === "true" && target._ecoTooltip && target._ecoTooltipHandlers) {
    console.log("✅ Tooltip already working on element, skipping");
    return;
  }
  
  // Clean up any existing broken tooltip and handlers first
  if (target._ecoTooltip) {
    target._ecoTooltip.remove();
    target._ecoTooltip = null;
  }
  if (target._ecoTooltipHandlers) {
    target.removeEventListener("mouseenter", target._ecoTooltipHandlers.mouseEnterHandler);
    target.removeEventListener("mouseleave", target._ecoTooltipHandlers.mouseLeaveHandler);
    if (target._ecoTooltipHandlers.mouseMoveHandler) {
      target.removeEventListener("mousemove", target._ecoTooltipHandlers.mouseMoveHandler);
    }
    target._ecoTooltipHandlers = null;
  }
  
  target.dataset.enhancedTooltipAttached = "true";
  
  const tooltip = createTooltip(html);
  target.style.borderBottom = "2px dotted #10b981"; // Better green color
  
  // Store tooltip reference on the target for cleanup
  target._ecoTooltip = tooltip;
  
  const mouseEnterHandler = () => {
    console.log("🟢 Mouse entered tooltip target");
    
    // Hide other visible tooltips (but don't affect their event handlers)
    document.querySelectorAll('.eco-tooltip').forEach(t => {
      if (t !== tooltip && t.style.opacity === '1') {
        t.style.opacity = '0';
        setTimeout(() => {
          if (t.style.opacity === '0') {
            t.style.display = 'none';
          }
        }, 150);
      }
    });
    
    const rect = target.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    
    // Better positioning with bounds checking
    let top = rect.bottom + scrollTop + 10;
    let left = rect.left + scrollLeft;
    
    // Keep tooltip within viewport
    if (left + 300 > window.innerWidth) {
      left = window.innerWidth - 320;
    }
    if (left < 10) {
      left = 10;
    }
    
    // Ensure tooltip is positioned and visible
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
    tooltip.style.display = 'block';
    tooltip.style.opacity = '1';
    tooltip.style.pointerEvents = 'none';
    
    console.log("🟢 Enhanced tooltip showing at:", { top, left });
  };

  const mouseLeaveHandler = () => {
    console.log("🔴 Mouse left tooltip target");
    tooltip.style.opacity = '0';
    // Small delay before hiding to prevent flicker
    setTimeout(() => {
      if (tooltip.style.opacity === '0') {
        tooltip.style.display = 'none';
      }
    }, 150);
  };
  
  // Add event listeners with proper cleanup
  target.addEventListener("mouseenter", mouseEnterHandler, { passive: true });
  target.addEventListener("mouseleave", mouseLeaveHandler, { passive: true });
  
  // Also handle mouse movement for better responsiveness
  const mouseMoveHandler = (e) => {
    if (tooltip.style.opacity === '1') {
      const rect = target.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
      
      let top = rect.bottom + scrollTop + 10;
      let left = rect.left + scrollLeft;
      
      if (left + 300 > window.innerWidth) {
        left = window.innerWidth - 320;
      }
      if (left < 10) {
        left = 10;
      }
      
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
    }
  };
  
  target.addEventListener("mousemove", mouseMoveHandler, { passive: true });
  
  // Store handlers for potential cleanup
  target._ecoTooltipHandlers = { mouseEnterHandler, mouseLeaveHandler, mouseMoveHandler };
  
  console.log("✅ Tooltip events attached to element:", target.textContent.substring(0, 30) + "...");
}

function extractMaterialFromDetailPage() {
  // Enhanced selectors for Amazon's product detail pages
  const selectors = [
    "th, span.a-text-bold",
    ".a-section .a-row span.a-text-bold",
    "#feature-bullets ul span.a-text-bold",
    "#productDetails_techSpec_section_1 th",
    "#productDetails_detailBullets_sections1 th",
    ".pdTab span.a-text-bold"
  ];
  
  let foundMaterials = [];
  
  for (const selector of selectors) {
    const labels = document.querySelectorAll(selector);
    for (const label of labels) {
      const text = label.innerText.trim().toLowerCase();
      if (text.includes("material") || text.includes("fabric") || text.includes("construction") || text.includes("composition")) {
        const valueEl = label.closest("tr")?.querySelector("td") ||
                        label.parentElement?.nextElementSibling ||
                        label.nextElementSibling;
        if (valueEl) {
          const val = valueEl.innerText.trim().toLowerCase();
          if (val && val !== "material" && val.length > 2) {
            console.log("✅ Found material in product page:", val);
            foundMaterials.push(val);
          }
        }
      }
    }
  }
  
  // Enhanced extraction from feature bullets and descriptions
  const contentSelectors = [
    "#feature-bullets ul li span",
    "#productDescription p",
    ".a-section .a-spacing-medium span",
    "[data-feature-name='featurebullets'] span"
  ];
  
  for (const selector of contentSelectors) {
    const elements = document.querySelectorAll(selector);
    for (const element of elements) {
      const text = element.innerText.toLowerCase();
      
      // Look for detailed material descriptions
      const materialPatterns = [
        /(?:made (?:of|from)|material:?\s*|fabric:?\s*|composition:?\s*)([a-z\s,&%-]+)/i,
        /(?:genuine|real|authentic)\s+(leather|suede|silk|wool|cotton|linen)/i,
        /(\w+)\s+leather/i,
        /(\w+)\s+cotton/i,
        /(recycled|organic|sustainable)\s+(\w+)/i,
        /(?:upper|outer|shell):?\s*([a-z\s,&%-]+)/i
      ];
      
      for (const pattern of materialPatterns) {
        const match = text.match(pattern);
        if (match) {
          const material = match[1] || match[2] || match[0];
          if (material && material.length > 2) {
            console.log("✅ Found detailed material:", material.trim());
            foundMaterials.push(material.trim());
          }
        }
      }
    }
  }
  
  // Return the most detailed/specific material found
  if (foundMaterials.length > 0) {
    // Sort by length (longer = more specific) and return the most specific
    foundMaterials.sort((a, b) => b.length - a.length);
    return foundMaterials[0];
  }
  
  console.warn("⚠️ No material found in detail page.");
  return null;
}


function extractMaterialFromTile(tile) {
  // Look in the tile and its parent containers for material info
  const containers = [
    tile.closest("div"),
    tile.closest("div")?.parentElement,
    tile.closest("[data-component-type='s-search-result']")
  ].filter(Boolean);
  
  let foundMaterials = [];
  
  for (const container of containers) {
    const text = container.innerText || "";
    
    // Enhanced material patterns for more specific detection
    const materialPatterns = [
      /Material Type[:\s]*([A-Za-z,\s&%-]+)/i,
      /Material[:\s]*([A-Za-z,\s&%-]+)/i,
      /Made (?:of|from)[:\s]*([A-Za-z,\s&%-]+)/i,
      /Fabric[:\s]*([A-Za-z,\s&%-]+)/i,
      /(?:genuine|real|authentic)\s+(leather|suede|silk|wool|cotton|linen)/i,
      /(\w+)\s+leather/i,
      /(recycled|organic|sustainable|premium)\s+(\w+)/i,
      /(?:upper|outer|shell)[:\s]*([A-Za-z,\s&%-]+)/i,
      /(vegan|faux|synthetic)\s+(leather|suede)/i
    ];
    
    for (const pattern of materialPatterns) {
      const match = text.match(pattern);
      if (match) {
        const material = (match[1] || match[2] || match[0]).trim().toLowerCase();
        if (material.length > 2 && !material.includes('material')) {
          console.log("✅ Found material in tile:", material);
          foundMaterials.push(material);
        }
      }
    }
  }
  
  // Return most specific material found
  if (foundMaterials.length > 0) {
    foundMaterials.sort((a, b) => b.length - a.length);
    return foundMaterials[0];
  }
  
  return null;
}

async function smartGuessMaterialFromTitle(title) {
  const titleLower = title.toLowerCase();

  // ── STEP 0: Explicit material words in the title (highest confidence) ──────
  // Check BEFORE any category guessing. Longer/more specific phrases first.
  const EXPLICIT_MATERIALS = [
    // Wood — specific species and types first
    { words: ['solid oak','solid pine','solid walnut','solid wood','solid timber','solid beech'], material: 'timber' },
    { words: ['oak','pine','walnut','birch','teak','mahogany','maple','beech','ash wood','acacia'], material: 'timber' },
    { words: ['engineered wood','mdf board','mdf','particleboard','chipboard','plywood','fibreboard','fibreboard','fsc-certified wood','fsc certified'], material: 'timber' },
    { words: ['wooden','reclaimed wood','bamboo board','bamboo shelf','bamboo table','bamboo desk'], material: 'timber' },
    // Metals — specific alloys first
    { words: ['stainless steel','surgical steel','304 steel','316 steel'], material: 'stainless steel' },
    { words: ['cast iron'], material: 'cast iron' },
    { words: ['carbon steel'], material: 'carbon steel' },
    { words: ['titanium'], material: 'titanium alloys' },
    { words: ['aluminium frame','aluminum frame','aluminium body','anodised aluminium','anodized aluminum','aluminium alloy','aluminum alloy'], material: 'aluminum' },
    { words: ['aluminium','aluminum'], material: 'aluminum' },
    { words: ['copper','brass','bronze'], material: 'brass' },
    // Glass
    { words: ['borosilicate','tempered glass','toughened glass','safety glass','frosted glass'], material: 'glass' },
    // Upholstery / soft furnishings — must appear before generic "metal"
    { words: ['velvet','velour'], material: 'polyester' },
    { words: ['boucle','bouclé','chenille'], material: 'wool' },
    { words: ['upholstered','upholstery'], material: 'polyester' },
    { words: ['foam mattress','memory foam'], material: 'polyurethane' },
    { words: ['cushion cover','cushion insert'], material: 'cotton' },
    // Natural fibres — specific first
    { words: ['100% cotton','organic cotton','pure cotton'], material: 'cotton' },
    { words: ['merino wool','pure wool','100% wool'], material: 'merino wool' },
    { words: ['genuine leather','real leather','full grain','top grain','full-grain','top-grain'], material: 'leather' },
    { words: ['vegan leather','faux leather','pu leather','synthetic leather','pu coated'], material: 'faux leather' },
    { words: ['recycled polyester','rpet'], material: 'recycled polyester' },
    { words: ['recycled plastic'], material: 'recovered plastic' },
    // Ceramics
    { words: ['porcelain','stoneware','earthenware'], material: 'ceramic' },
    // Rubber / silicone
    { words: ['natural rubber','vulcanised rubber'], material: 'rubber' },
    { words: ['food grade silicone','medical grade silicone'], material: 'silicone' },
  ];

  for (const entry of EXPLICIT_MATERIALS) {
    if (entry.words.some(w => titleLower.includes(w))) {
      console.log(`🎯 Explicit material match: "${entry.material}" from title`);
      return entry.material;
    }
  }

  // ── STEP 0b: Generic single material words (still beats category guessing) ─
  const GENERIC_WORDS = [
    { words: ['velvet','velour','boucle','chenille','upholstered'], material: 'polyester' },
    { words: ['wooden','timber','wood'], material: 'timber' },
    { words: ['metal','steel','iron','metallic','alloy steel'], material: 'steel' },
    { words: ['glass'], material: 'glass' },
    { words: ['plastic','polypropylene','polyethylene','pvc','acrylic'], material: 'plastics' },
    { words: ['leather'], material: 'leather' },
    { words: ['cotton','denim'], material: 'cotton' },
    { words: ['polyester','fleece'], material: 'polyester' },
    { words: ['nylon'], material: 'nylon' },
    { words: ['rubber'], material: 'rubber' },
    { words: ['silicone'], material: 'silicone' },
    { words: ['ceramic'], material: 'ceramic' },
    { words: ['bamboo'], material: 'bamboo' },
    { words: ['canvas','fabric','textile','linen'], material: 'cotton' },
    { words: ['paper','cardboard'], material: 'paper' },
    { words: ['concrete','cement'], material: 'concrete' },
    { words: ['marble','granite'], material: 'marble' },
    { words: ['carbon fibre','carbon fiber'], material: 'carbon fiber' },
  ];

  for (const entry of GENERIC_WORDS) {
    if (entry.words.some(w => titleLower.includes(w))) {
      console.log(`🔤 Generic material word: "${entry.material}" from title`);
      return entry.material;
    }
  }

  // ── STEP 1: Category-pattern guessing (fallback when no material words present) ─
  // Load material insights to get comprehensive list
  const insights = window.materialInsights || await window.loadMaterialInsights?.() || {};

  // Enhanced category-based guessing with comprehensive material families
  const categoryPatterns = [
    // LEATHER PRODUCTS (Comprehensive leather detection)
    { patterns: ['genuine leather', 'real leather', 'full grain leather', 'top grain leather'], material: 'leather', priority: 22 },
    { patterns: ['suede', 'nubuck', 'patent leather'], material: 'leather', priority: 21 },
    { patterns: ['vegan leather', 'faux leather', 'synthetic leather', 'pleather'], material: 'faux leather', priority: 20 },
    { patterns: ['mushroom leather', 'mycelium leather'], material: 'mushroom leather', priority: 20 },
    { patterns: ['apple leather', 'grape leather', 'cactus leather'], material: 'apple leather', priority: 20 },
    { patterns: ['recycled leather', 'bonded leather'], material: 'recycled leather', priority: 19 },
    
    // METALS (Comprehensive metal detection)
    { patterns: ['stainless steel', 'surgical steel'], material: 'stainless steel', priority: 22 },
    { patterns: ['carbon steel', 'high carbon steel'], material: 'carbon steel', priority: 21 },
    { patterns: ['titanium alloy', 'titanium'], material: 'titanium alloys', priority: 21 },
    { patterns: ['cast iron', 'wrought iron'], material: 'cast iron', priority: 20 },
    { patterns: ['brass', 'bronze', 'copper'], material: 'brass', priority: 19 },
    
    // BAGS & BACKPACKS (High Priority - prioritize nylon over aluminum)
    { patterns: ['backpack', 'rucksack', 'hiking backpack', 'travel backpack', 'daypack'], material: 'nylon', priority: 18 },
    { patterns: ['gym bag', 'sports bag', 'duffel bag', 'duffle bag'], material: 'nylon', priority: 17 },
    { patterns: ['laptop bag', 'briefcase', 'computer bag'], material: 'nylon', priority: 16 },
    { patterns: ['hiking pack', 'climbing pack', 'outdoor pack'], material: 'nylon', priority: 17 },
    { patterns: ['leather bag', 'leather handbag', 'leather purse'], material: 'leather', priority: 15 },
    { patterns: ['canvas bag', 'canvas backpack'], material: 'canvas', priority: 14 },
    { patterns: ['bag', 'handbag', 'shoulder bag', 'tote bag'], material: 'leather', priority: 9 },
    
    // TEXTILES & CLOTHING (Comprehensive textile detection)
    // Natural Plant Fibers
    { patterns: ['organic cotton', '100% cotton', 'pure cotton'], material: 'cotton', priority: 18 },
    { patterns: ['recycled cotton', 'sustainable cotton'], material: 'recycled cotton', priority: 17 },
    { patterns: ['linen', 'flax', 'irish linen'], material: 'linen', priority: 17 },
    { patterns: ['hemp', 'hemp fiber', 'industrial hemp'], material: 'hemp', priority: 17 },
    { patterns: ['jute', 'burlap', 'hessian'], material: 'jute', priority: 16 },
    { patterns: ['bamboo fiber', 'bamboo fabric'], material: 'bamboo', priority: 16 },
    
    // Animal Fibers  
    { patterns: ['merino wool', 'pure wool', 'virgin wool'], material: 'merino wool', priority: 18 },
    { patterns: ['cashmere', 'kashmir wool'], material: 'cashmere', priority: 18 },
    { patterns: ['alpaca', 'alpaca wool'], material: 'alpaca', priority: 17 },
    { patterns: ['mohair', 'angora mohair'], material: 'mohair', priority: 17 },
    { patterns: ['silk', 'mulberry silk', 'pure silk'], material: 'silk', priority: 17 },
    { patterns: ['down', 'goose down', 'duck down'], material: 'down', priority: 16 },
    
    // Synthetic Fibers
    { patterns: ['recycled polyester', 'eco polyester', 'rPET'], material: 'recycled polyester', priority: 17 },
    { patterns: ['recycled nylon', 'econyl'], material: 'recycled nylon', priority: 17 },
    { patterns: ['lyocell', 'tencel', 'modal'], material: 'lyocell tencel', priority: 16 },
    { patterns: ['viscose', 'rayon'], material: 'viscose', priority: 15 },
    
    // Clothing Items
    { patterns: ['denim jeans', 'denim jacket'], material: 'denim', priority: 15 },
    { patterns: ['canvas shoes', 'canvas sneakers'], material: 'canvas', priority: 14 },
    { patterns: ['t-shirt', 'shirt', 'tee', 'top'], material: 'cotton', priority: 10 },
    { patterns: ['jeans', 'denim'], material: 'denim', priority: 10 },
    { patterns: ['jacket', 'coat', 'hoodie', 'sweater'], material: 'polyester', priority: 9 },
    { patterns: ['pants', 'trousers', 'leggings'], material: 'cotton', priority: 8 },
    { patterns: ['dress', 'skirt'], material: 'polyester', priority: 8 },
    { patterns: ['socks', 'underwear'], material: 'cotton', priority: 9 },
    { patterns: ['leather shoes', 'leather boots'], material: 'leather', priority: 12 },
    { patterns: ['shoes', 'sneakers', 'trainers', 'boots'], material: 'leather', priority: 8 },
    
    // ELECTRONICS & TECH (Comprehensive tech material detection)
    // Phone Cases & Accessories
    { patterns: ['silicone case', 'silicone cover', 'silicone protector'], material: 'silicone', priority: 16 },
    { patterns: ['tpu case', 'thermoplastic polyurethane'], material: 'polyurethane', priority: 16 },
    { patterns: ['polycarbonate case', 'pc case'], material: 'polycarbonate', priority: 16 },
    { patterns: ['abs case', 'abs plastic case'], material: 'abs', priority: 16 },
    { patterns: ['leather case', 'leather phone case'], material: 'leather', priority: 15 },
    { patterns: ['aluminum case', 'metal case'], material: 'aluminum', priority: 15 },
    
    // Devices
    { patterns: ['titanium watch', 'titanium phone'], material: 'titanium alloys', priority: 16 },
    { patterns: ['stainless steel watch', 'steel watch'], material: 'stainless steel', priority: 15 },
    { patterns: ['carbon fiber case', 'carbon fiber phone'], material: 'carbon fiber', priority: 15 },
    { patterns: ['ceramic watch', 'ceramic phone'], material: 'ceramic', priority: 14 },
    { patterns: ['headphones', 'earbuds', 'earphones'], material: 'plastics', priority: 8 },
    { patterns: ['phone case', 'case', 'cover', 'protector'], material: 'plastics', priority: 9 },
    { patterns: ['laptop', 'macbook', 'ultrabook', 'notebook computer'], material: 'aluminum', priority: 7 },
    { patterns: ['charger', 'cable', 'adapter', 'cord'], material: 'plastics', priority: 8 },
    { patterns: ['speaker', 'soundbar'], material: 'plastics', priority: 7 },
    { patterns: ['tablet', 'ipad'], material: 'aluminum', priority: 7 },
    
    // HOME & KITCHEN (Comprehensive home goods detection)
    // Drinkware
    { patterns: ['stainless steel bottle', 'steel water bottle', 'insulated steel'], material: 'stainless steel', priority: 17 },
    { patterns: ['glass bottle', 'borosilicate glass', 'tempered glass'], material: 'glass', priority: 16 },
    { patterns: ['ceramic mug', 'porcelain mug', 'stoneware mug'], material: 'ceramic', priority: 16 },
    { patterns: ['bamboo tumbler', 'bamboo cup'], material: 'bamboo', priority: 15 },
    { patterns: ['silicone bottle', 'collapsible bottle'], material: 'silicone', priority: 14 },
    
    // Cookware  
    { patterns: ['cast iron pan', 'cast iron skillet'], material: 'cast iron', priority: 17 },
    { patterns: ['stainless steel pan', 'steel cookware'], material: 'stainless steel', priority: 16 },
    { patterns: ['carbon steel pan', 'carbon steel wok'], material: 'carbon steel', priority: 16 },
    { patterns: ['ceramic cookware', 'ceramic pan'], material: 'ceramic', priority: 15 },
    { patterns: ['copper cookware', 'copper pan'], material: 'copper', priority: 15 },
    
    // Cutting Boards
    { patterns: ['bamboo cutting board', 'bamboo chopping board'], material: 'bamboo', priority: 16 },
    { patterns: ['wooden cutting board', 'wood chopping board'], material: 'timber', priority: 15 },
    { patterns: ['plastic cutting board', 'polyethylene board'], material: 'polyethylene', priority: 14 },
    
    // General Items
    { patterns: ['water bottle', 'bottle', 'flask', 'tumbler'], material: 'stainless steel', priority: 8 },
    { patterns: ['mug', 'cup'], material: 'ceramic', priority: 8 },
    { patterns: ['pan', 'pot', 'cookware', 'frying pan'], material: 'aluminum', priority: 8 },
    { patterns: ['cutting board', 'chopping board'], material: 'timber', priority: 9 },
    { patterns: ['plate', 'bowl', 'dish'], material: 'ceramic', priority: 8 },
    { patterns: ['curtain', 'drapes'], material: 'polyester', priority: 7 },
    { patterns: ['towel', 'washcloth'], material: 'cotton', priority: 8 },
    { patterns: ['pillow', 'cushion'], material: 'polyester', priority: 7 },
    { patterns: ['blanket', 'throw'], material: 'cotton', priority: 7 },
    
    // Sports & Outdoors
    { patterns: ['yoga mat', 'exercise mat', 'gym mat'], material: 'rubber', priority: 9 },
    { patterns: ['tent', 'camping'], material: 'nylon', priority: 8 },
    { patterns: ['sleeping bag'], material: 'nylon', priority: 8 },
    
    // Tools & Hardware
    { patterns: ['screwdriver', 'wrench', 'hammer', 'tool'], material: 'steel', priority: 8 },
    { patterns: ['drill', 'power tool'], material: 'plastics', priority: 7 },
    
    // Accessories
    { patterns: ['watch', 'smartwatch'], material: 'steel', priority: 7 },
    { patterns: ['sunglasses', 'glasses'], material: 'plastics', priority: 8 },
    { patterns: ['wallet', 'purse'], material: 'leather', priority: 8 },
    { patterns: ['belt'], material: 'leather', priority: 8 },
    
    // Books & Media
    { patterns: ['book', 'paperback', 'hardcover'], material: 'paper', priority: 9 },
    { patterns: ['notebook', 'journal', 'diary'], material: 'paper', priority: 8 },
    
    // Beauty & Personal Care
    { patterns: ['brush', 'comb'], material: 'plastics', priority: 7 },
    { patterns: ['mirror'], material: 'glass', priority: 8 }
  ];
  
  // Check category patterns with priority (highest priority first)
  let bestMatch = null;
  let highestPriority = 0;
  
  for (const category of categoryPatterns) {
    const matchedPattern = category.patterns.find(pattern => titleLower.includes(pattern));
    if (matchedPattern && category.priority > highestPriority) {
      bestMatch = {
        material: category.material,
        pattern: matchedPattern,
        priority: category.priority
      };
      highestPriority = category.priority;
    }
  }
  
  if (bestMatch) {
    console.log("🎯 Category-based material guess:", bestMatch.material, `(priority: ${bestMatch.priority}, pattern: "${bestMatch.pattern}")`);
    return bestMatch.material;
  }
  
  // Check for direct material mentions in title
  const materialKeywords = Object.keys(insights);
  for (const material of materialKeywords) {
    if (titleLower.includes(material.toLowerCase())) {
      console.log("🔍 Direct material found in title:", material);
      return material;
    }
  }
  
  // Check for common material descriptors
  const materialDescriptors = [
    { patterns: ['wooden', 'wood'], material: 'timber' },
    { patterns: ['metal', 'metallic'], material: 'steel' },
    { patterns: ['plastic'], material: 'plastics' },
    { patterns: ['glass'], material: 'glass' },
    { patterns: ['ceramic'], material: 'ceramic' },
    { patterns: ['rubber'], material: 'rubber' },
    { patterns: ['leather'], material: 'leather' },
    { patterns: ['fabric', 'cloth', 'textile'], material: 'cotton' },
    { patterns: ['carbon fiber', 'carbon fibre'], material: 'carbon fiber' },
    { patterns: ['bamboo'], material: 'bamboo' },
    { patterns: ['silicone'], material: 'silicone' }
  ];
  
  for (const descriptor of materialDescriptors) {
    if (descriptor.patterns.some(pattern => titleLower.includes(pattern))) {
      console.log("📝 Descriptor-based material guess:", descriptor.material);
      return descriptor.material;
    }
  }
  
  console.log("❓ No material guess found for:", title);
  return null;
}

// Returns {primary, secondary} by scanning the full title for up to 2 distinct materials.
// Primary = first match; secondary = second distinct match or inferred from category.
async function detectMaterials(title) {
  const titleLower = title.toLowerCase();

  // Flat ordered rule list — same priority order as the explicit/generic checks
  // but traversed fully so we can collect a second material
  const ALL_RULES = [
    { words: ['velvet','velour'],                                           material: 'polyester' },
    { words: ['boucle','bouclé','chenille'],                                material: 'wool' },
    { words: ['upholstered','upholstery'],                                  material: 'polyester' },
    { words: ['foam mattress','memory foam'],                               material: 'polyurethane' },
    { words: ['solid oak','solid pine','solid walnut','solid wood','solid timber','solid beech'], material: 'timber' },
    { words: ['oak','pine','walnut','birch','teak','mahogany','maple','beech','acacia'],          material: 'timber' },
    { words: ['engineered wood','mdf','particleboard','chipboard','plywood','fibreboard','fsc-certified wood'], material: 'timber' },
    { words: ['stainless steel','surgical steel'],                          material: 'stainless steel' },
    { words: ['cast iron'],                                                 material: 'cast iron' },
    { words: ['carbon steel'],                                              material: 'carbon steel' },
    { words: ['titanium'],                                                  material: 'titanium alloys' },
    { words: ['aluminium alloy','aluminum alloy','anodised aluminium','anodized aluminum','aluminium frame','aluminum frame'], material: 'aluminum' },
    { words: ['aluminium','aluminum'],                                      material: 'aluminum' },
    { words: ['copper','brass','bronze'],                                   material: 'brass' },
    { words: ['borosilicate','tempered glass','toughened glass','safety glass'], material: 'glass' },
    { words: ['100% cotton','organic cotton','pure cotton'],                material: 'cotton' },
    { words: ['merino wool','pure wool','100% wool'],                       material: 'merino wool' },
    { words: ['genuine leather','real leather','full grain','top grain'],   material: 'leather' },
    { words: ['vegan leather','faux leather','pu leather','synthetic leather','pu coated'], material: 'faux leather' },
    { words: ['recycled polyester','rpet'],                                 material: 'recycled polyester' },
    { words: ['recycled plastic'],                                          material: 'recovered plastic' },
    { words: ['porcelain','stoneware','earthenware'],                       material: 'ceramic' },
    { words: ['food grade silicone','medical grade silicone'],              material: 'silicone' },
    // Generic single-word fallbacks
    { words: ['wooden','timber','wood'],                                    material: 'timber' },
    { words: ['metal frame','metal leg','metal base','alloy steel','metallic'], material: 'steel' },
    { words: ['glass'],                                                     material: 'glass' },
    { words: ['plastic','polypropylene','polyethylene','pvc','acrylic'],    material: 'plastics' },
    { words: ['leather'],                                                   material: 'leather' },
    { words: ['cotton','denim'],                                            material: 'cotton' },
    { words: ['polyester','fleece'],                                        material: 'polyester' },
    { words: ['nylon'],                                                     material: 'nylon' },
    { words: ['rubber'],                                                    material: 'rubber' },
    { words: ['silicone'],                                                  material: 'silicone' },
    { words: ['ceramic'],                                                   material: 'ceramic' },
    { words: ['bamboo'],                                                    material: 'bamboo' },
    { words: ['canvas','fabric','textile','linen'],                         material: 'cotton' },
    { words: ['paper','cardboard'],                                         material: 'paper' },
    { words: ['carbon fibre','carbon fiber'],                               material: 'carbon fiber' },
    { words: ['marble','granite'],                                          material: 'marble' },
    // Generic metal last — only fires when no specific material found
    { words: ['metal','steel','iron'],                                      material: 'steel' },
  ];

  const found = [];
  for (const entry of ALL_RULES) {
    if (found.length >= 2) break;
    if (entry.words.some(w => titleLower.includes(w))) {
      const mat = entry.material;
      if (!found.includes(mat)) found.push(mat);
    }
  }

  // Infer secondary from product category if still only one material found
  if (found.length === 1) {
    const sec = inferSecondaryMaterial(titleLower, found[0]);
    if (sec) found.push(sec);
  }

  // Fall back to category-pattern guessing if title has no material signal at all
  if (found.length === 0) {
    const guessed = await smartGuessMaterialFromTitle(title);
    if (guessed) found.push(guessed);
  }

  return { primary: found[0] || null, secondary: found[1] || null };
}

// Infers a likely secondary material based on product category + primary material.
function inferSecondaryMaterial(titleLower, primaryMaterial) {
  const p = (primaryMaterial || '').toLowerCase();

  // Soft-upholstered furniture → structural frame as secondary
  const SOFT = ['polyester','cotton','wool','velvet','linen','silk','leather','faux leather',
                'merino wool','recycled polyester','down','boucle','chenille'];
  if (SOFT.some(m => p.includes(m))) {
    if (/\b(stool|chair|sofa|bench|ottoman|footrest|seat|armchair|couch|loveseat|settee|pouf|pouffe)\b/.test(titleLower)) {
      if (/\b(wood|oak|pine|walnut|beech|bamboo|wooden)\b/.test(titleLower)) return 'timber';
      return 'steel'; // default: metal legs
    }
    if (/\b(mattress|bed frame|divan)\b/.test(titleLower)) return 'timber';
  }

  // Wood furniture → metal hardware/legs as secondary
  const WOOD = ['timber','engineered wood','bamboo','solid wood'];
  if (WOOD.some(m => p.includes(m))) {
    if (/\b(desk|table|shelf|shelving|unit|cabinet|drawer|wardrobe|bookcase|storage|frame|stand)\b/.test(titleLower)) {
      return 'steel';
    }
  }

  // Electronics: glass or metal primary → plastic secondary, and vice-versa
  if (/\b(phone|laptop|tablet|computer|monitor|tv|television|camera|speaker|headphone|earbuds|charger|router|keyboard|mouse)\b/.test(titleLower)) {
    if (p === 'aluminum' || p === 'glass') return 'plastics';
    if (p === 'plastics') return 'aluminum';
  }

  // Cookware: often steel + another material
  if (/\b(pan|pot|wok|skillet|saucepan|casserole)\b/.test(titleLower)) {
    if (p === 'stainless steel' || p === 'cast iron' || p === 'carbon steel') return 'plastics'; // handle
    if (p === 'aluminum') return 'steel';
  }

  return null;
}

function getLcaBreakdown(info) {
  const impact = info.impact || 'Unknown';
  const recyclable = info.recyclable;
  const materialName = (info.name || '').toLowerCase();

  // Production = overall material impact
  const productionLevel = impact;

  // Transport heuristic
  const lowTransportMaterials = ['timber', 'bamboo', 'cork', 'stone', 'brick', 'concrete', 'clay', 'sand', 'gravel'];
  const highTransportMaterials = ['platinum', 'palladium', 'titanium', 'rare earth', 'lithium'];
  let transportLevel = 'Moderate';
  if (lowTransportMaterials.some(m => materialName.includes(m))) transportLevel = 'Low';
  if (highTransportMaterials.some(m => materialName.includes(m))) transportLevel = 'High';

  // Use phase — electronics/energy-dependent materials are higher
  const highUseMaterials = ['battery', 'lithium', 'led', 'electronics', 'copper', 'tungsten'];
  const lowUseMaterials = ['timber', 'stone', 'ceramic', 'glass', 'cotton', 'wool', 'leather', 'paper', 'bamboo'];
  let useLevel = 'Low';
  if (highUseMaterials.some(m => materialName.includes(m))) useLevel = 'Moderate';
  if (lowUseMaterials.some(m => materialName.includes(m))) useLevel = 'Low';

  // End-of-life
  const eolLevel = recyclable === true ? 'Low' : recyclable === false ? 'High' : 'Moderate';
  const eolLabel = recyclable === true ? 'Low ♻️' : recyclable === false ? 'High 🚯' : 'Unknown';

  const levelColor = {
    'Low': '#10b981', 'Low-Moderate': '#84cc16',
    'Moderate': '#f59e0b', 'High': '#ef4444', 'Unknown': '#6b7280'
  };
  const levelBar = {
    'Low': '██░░░', 'Low-Moderate': '███░░',
    'Moderate': '████░', 'High': '█████', 'Unknown': '░░░░░'
  };

  const row = (icon, label, level, display) =>
    `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
      <span style="color:#cbd5e1;">${icon} ${label}</span>
      <span style="color:${levelColor[level]||'#6b7280'};font-family:monospace;font-size:10px;">${levelBar[level]||'░░░░░'} ${display||level}</span>
    </div>`;

  return `
    <div style="margin-top:8px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.15);font-size:11px;">
      <div style="font-weight:600;margin-bottom:5px;color:#e2e8f0;font-size:11px;">🔄 Lifecycle Assessment</div>
      ${row('🏭','Manufacturing', productionLevel, productionLevel)}
      ${row('🚢','Transport', transportLevel, transportLevel)}
      ${row('💡','Use Phase', useLevel, useLevel)}
      ${row('🗑️','End-of-Life', eolLevel, eolLabel)}
    </div>`;
}

function showTooltipFor(target, info, secondaryMaterial) {
  if (!ecoSettings.showTooltips) return;
  if (!info || typeof info !== "object" || !info.name || info.name === "unknown") {
    console.warn("⚠️ Skipping tooltip — no valid info provided.");
    return;
  }

  // Only show tooltips with reasonable confidence (lowered threshold for better coverage)
  const confidence = info.confidence || 70;
  if (confidence < 25) {
    console.warn("⚠️ Skipping tooltip — confidence too low:", confidence);
    return;
  }

  const emoji = info.impact === "High" ? "🔥"
              : info.impact === "Moderate" ? "⚠️"
              : info.impact === "Low" ? "🌱"
              : info.impact === "Low-Moderate" ? "🌿"
              : "❓";

  // Enhanced tooltip with confidence indicator and material specificity
  const confidenceColor = confidence >= 80 ? "#10b981"
                         : confidence >= 60 ? "#f59e0b"
                         : "#ef4444";

  // Enhanced material name display with family information
  const materialName = info.name;
  const isSpecificMaterial = info.isSpecific || materialName.includes(' ') ||
                           ['faux leather', 'recycled', 'organic', 'vegan', 'genuine', 'stainless', 'carbon'].some(prefix =>
                           materialName.toLowerCase().includes(prefix));

  const familyInfo = info.family ? ` (${info.family.replace('_', ' ')})` : '';

  // Material type icons based on family
  const familyIcons = {
    metals: '🔩', polymers: '🧪', elastomers: '🔄', ceramics: '🏺',
    glasses: '🔍', stone_mineral: '🪨', textiles: '🧵', leather: '💼',
    wood_plant: '🌳', paper_cellulose: '📄', composites: '⚙️',
    construction: '🏠', chemical: '⚗️'
  };

  const materialIcon = info.family && familyIcons[info.family] ? familyIcons[info.family] :
                      (isSpecificMaterial ? "🎯" : "🧬");

  const specificityNote = isSpecificMaterial ?
    `<div style="font-size: 10px; color: #10b981; margin-top: 2px;">✨ Specific material detected${familyInfo}</div>` :
    `<div style="font-size: 10px; color: #888; margin-top: 2px;">📈 General material category${familyInfo}</div>`;

  const compoundInfo = info.compound && info.originalHint ?
    `<div style="font-size: 10px; color: #a78bfa; margin-top: 2px;">🧬 Detected from: "${info.originalHint}"</div>` : '';

  const relatedMaterials = findRelatedMaterials(materialName);
  const relatedSection = relatedMaterials.length > 0 ?
    `<div style="font-size: 11px; color: #94a3b8; margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1);">
      <strong>🔗 Related materials:</strong> ${relatedMaterials.slice(0, 3).join(', ')}
    </div>` : '';

  const lcaSection = getLcaBreakdown(info);

  const secondaryLine = secondaryMaterial
    ? `<div style="font-size:11px;color:#a8b8cc;margin-top:4px;font-weight:500;">+ ${capitalizeFirst(secondaryMaterial)} <span style="color:#7a8a9a;font-weight:400;">(secondary material)</span></div>`
    : '';

  const html = `
    <div style="border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 8px; margin-bottom: 8px;">
      <strong>${materialIcon} Material: ${capitalizeFirst(materialName)}</strong>
      ${secondaryLine}
      ${specificityNote}
      ${compoundInfo}
      <div style="margin-top: 4px; font-size: 11px; color: #888;">
        Confidence: <span style="color: ${confidenceColor};">${Math.round(confidence)}%</span>
      </div>
    </div>
    <div style="margin-bottom: 8px;">
      <strong>${emoji} ${info.impact || "Unknown"} Environmental Impact</strong>
    </div>
    <div style="font-size: 12px; line-height: 1.4; margin-bottom: 6px; color: #e2e8f0;">
      ${info.summary || "No summary available."}
    </div>
    ${lcaSection}
    ${relatedSection}
    <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 10px; color: #64748b; text-align: center;">
      ℹ️ Material estimate from title &bull; Click <strong style="color:#10b981;">🌱 Eco</strong> for full carbon analysis
    </div>
  `;

  attachTooltipEvents(target, html);
}

// Enhanced helper function to find related materials using comprehensive families
function findRelatedMaterials(materialName) {
  const insights = window.materialInsights || {};
  const baseName = materialName.toLowerCase();
  const related = [];
  
  // Define comprehensive material families for related materials
  const materialFamilies = {
    // METALS
    metals: ['aluminum', 'steel', 'stainless steel', 'carbon steel', 'titanium alloys', 'brass', 'copper', 'iron', 'zinc', 'tin'],
    
    // LEATHER FAMILY
    leather: ['leather', 'suede', 'faux leather', 'vegan leather', 'mushroom leather', 'apple leather', 'grape leather', 'cactus leather', 'palm leather', 'recycled leather'],
    
    // POLYMERS/PLASTICS
    polymers: ['plastics', 'polyethylene', 'polypropylene', 'polystyrene', 'pvc', 'abs', 'polycarbonate', 'polyurethane', 'bioplastic', 'recovered plastic', 'acrylic'],
    
    // NATURAL PLANT FIBERS
    plant_fibers: ['cotton', 'linen', 'hemp', 'jute', 'ramie', 'sisal', 'organic cotton', 'recycled cotton'],
    
    // ANIMAL FIBERS
    animal_fibers: ['wool', 'silk', 'cashmere', 'alpaca', 'mohair', 'merino wool', 'down'],
    
    // SYNTHETIC FIBERS
    synthetic_fibers: ['polyester', 'nylon', 'acrylic', 'spandex', 'viscose', 'rayon', 'recycled polyester', 'recycled nylon'],
    
    // ELASTOMERS
    elastomers: ['rubber', 'silicone', 'elastane', 'spandex', 'reclaimed rubber'],
    
    // WOOD/PLANT MATERIALS
    wood_materials: ['timber', 'bamboo', 'cork', 'plywood', 'reclaimed wood', 'wood'],
    
    // CERAMICS
    ceramics: ['ceramic', 'ceramics', 'porcelain', 'stoneware', 'brick'],
    
    // GLASS
    glass_materials: ['glass', 'fiberglass'],
    
    // STONE/MINERAL
    stone_materials: ['granite', 'marble', 'limestone', 'concrete', 'cement', 'stone'],
    
    // PAPER/CELLULOSE
    paper_materials: ['paper', 'cardboard', 'wood pulp'],
    
    // COMPOSITES
    composites: ['carbon fiber', 'fiberglass', 'kevlar']
  };
  
  // Find which family the current material belongs to
  for (const [familyName, materials] of Object.entries(materialFamilies)) {
    const materialMatch = materials.find(m => {
      return baseName.includes(m) || m.includes(baseName) || 
             // Handle compound materials
             (baseName.includes(' ') && m.includes(baseName.split(' ')[0])) ||
             (m.includes(' ') && baseName.includes(m.split(' ')[0]));
    });
    
    if (materialMatch) {
      // Add other materials from the same family
      for (const material of materials) {
        if (material !== materialMatch && 
            material !== baseName && 
            insights[material] && 
            !related.includes(material)) {
          related.push(material);
        }
      }
      
      // Also look for variations with prefixes (recycled, organic, etc.)
      const baseMaterial = baseName.replace(/(recycled|organic|sustainable|premium|eco|bio)\s+/, '');
      const prefixes = ['recycled', 'organic', 'sustainable', 'eco', 'bio'];
      
      for (const prefix of prefixes) {
        const variation = `${prefix} ${baseMaterial}`;
        if (insights[variation] && !related.includes(variation) && variation !== baseName) {
          related.push(variation);
        }
      }
      
      break;
    }
  }
  
  // If no family match, look for direct variations
  if (related.length === 0) {
    const allMaterials = Object.keys(insights);
    const baseMaterial = baseName.replace(/(recycled|organic|sustainable|premium|eco|bio)\s+/, '');
    
    for (const material of allMaterials) {
      const materialLower = material.toLowerCase();
      if ((materialLower.includes(baseMaterial) || baseMaterial.includes(materialLower)) &&
          materialLower !== baseName &&
          related.length < 5) {
        related.push(material);
      }
    }
  }
  
  return related.slice(0, 4); // Limit to 4 related materials
}

// Helper function to capitalize first letter
function capitalizeFirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

async function enhanceTooltips() {
  console.log("✅ Enhanced tooltip script running");
  
  // Only clean up orphaned tooltips (not attached to any element)
  const allTooltips = document.querySelectorAll('.eco-tooltip');
  const attachedTooltips = new Set();
  
  // Find tooltips that are still attached to elements
  document.querySelectorAll('[data-enhanced-tooltip-attached="true"]').forEach(el => {
    if (el._ecoTooltip) {
      attachedTooltips.add(el._ecoTooltip);
    }
  });
  
  // Remove only orphaned tooltips
  allTooltips.forEach(tooltip => {
    if (!attachedTooltips.has(tooltip)) {
      tooltip.remove();
    }
  });
  
  // Don't clean up working tooltips - only fix broken ones in attachTooltipEvents
  
  // Ensure material insights are loaded
  if (!window.materialInsights) {
    try {
      const getURL = typeof chrome !== "undefined" && chrome.runtime?.getURL
        ? chrome.runtime.getURL
        : (path) => path;
      const res = await fetch(getURL("material_insights.json"));
      window.materialInsights = await res.json();
      console.log("📚 Loaded material insights:", Object.keys(window.materialInsights).length, "materials");
    } catch (e) {
      console.error("❌ Failed to load material insights:", e);
      window.materialInsights = {};
    }
  }

  const isProductDetail = document.querySelector("#productTitle") !== null;

  if (isProductDetail) {
    const titleEl = document.querySelector("#productTitle");
    if (!titleEl || titleEl.dataset.tooltipAttached) return;
    titleEl.dataset.tooltipAttached = "true";
    const title = titleEl.textContent.trim();

    // PRIMARY: title-based detection (title names what product IS)
    const { primary: titlePrimary, secondary: titleSecondary } = await detectMaterials(title);
    let materialHint = titlePrimary;

    // SUPPLEMENT: if title gave no signal at all, try DOM extraction
    if (!materialHint) {
      const domMaterial = extractMaterialFromDetailPage();
      if (domMaterial) {
        materialHint = domMaterial;
        console.log("📋 Supplemental DOM material:", domMaterial);
      }
    }

    if (!materialHint) materialHint = "unknown";
    console.log("🧪 Final Material Hint (product page):", materialHint, "| secondary:", titleSecondary);

    const info = await window.ecoLookup(title, materialHint);
    showTooltipFor(titleEl, info || { impact: "Unknown", summary: "No insight found.", recyclable: null }, titleSecondary);
    return;

  } else {
    // ── PASS 1: Quick class-based selectors (catches obvious cases fast) ──────
    const QUICK_SELECTORS = [
      "h2 span.a-text-normal",
      "h2 span.a-color-base",
      "h2 span.a-size-base-plus",
      "span.a-text-normal",
      "div[data-component-type='s-search-result'] h2 span",
      "div.puisg-title span",
      ".p13n-sc-truncated",
      ".p13n-sc-truncated-desktop-type2",
      "[data-cy='title-recipe'] span",
      ".a-carousel-card h2 span",
      ".a-carousel-card span.a-text-normal",
      "li[data-asin] span.a-text-normal",
      "li[data-asin] h2 span",
      "._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y",
      "._cDEzb_p13n-sc-css-line-clamp-3_g3dy1",
    ];

    let tiles = [];
    for (const sel of QUICK_SELECTORS) {
      Array.from(document.querySelectorAll(sel)).forEach(el => tiles.push(el));
    }

    // ── PASS 2: Universal ASIN sweep — layout-agnostic, catches everything ────
    document.querySelectorAll('[data-asin]').forEach(container => {
      const asin = container.getAttribute('data-asin');
      if (!asin || container.dataset.asinScanned) return;
      container.dataset.asinScanned = "true";

      if (container.querySelector('[data-tooltip-attached="true"], [data-enhanced-tooltip-attached="true"]')) return;

      // Priority 1: heading span
      let titleEl =
        container.querySelector('h2 span:not([class*="offscreen"]):not([class*="hidden"])') ||
        container.querySelector('h3 span:not([class*="offscreen"]):not([class*="hidden"])') ||
        container.querySelector('h2') ||
        container.querySelector('h3');

      // Priority 2: explicit title class
      if (!titleEl) {
        titleEl =
          container.querySelector('[class*="product-title"]') ||
          container.querySelector('[class*="item-title"]') ||
          container.querySelector('[class*="s-line-clamp"]') ||
          container.querySelector('[data-cy="title-recipe"]');
      }

      // Priority 3: longest plausible text node — removed children<4 constraint
      // which was incorrectly excluding many valid title spans
      if (!titleEl) {
        let best = null, bestLen = 0;
        container.querySelectorAll('span, a').forEach(el => {
          const text = (el.textContent || '').trim();
          if (
            text.length > 15 && text.length < 250 &&
            text.length > bestLen &&
            !text.match(/^[\£\$\€\d]/) &&
            !text.match(/\d+\s*star/i) &&
            !/^(see more|add to|buy now|in stock|free delivery|sponsored|results|filter|sort|back to top)/i.test(text) &&
            el.nodeName !== 'DIV'
          ) {
            best = el;
            bestLen = text.length;
          }
        });
        titleEl = best;
      }

      if (titleEl && !titleEl.dataset.tooltipAttached && !tiles.includes(titleEl)) {
        tiles.push(titleEl);
      }
    });

    // ── PASS 3: Product link sweep — catches anything ASIN sweep missed ───────
    // Anchors linking to /dp/ or /gp/product/ are product page links.
    const PRODUCT_LINK_SELECTOR = 'a[href*="/dp/"], a[href*="/gp/product/"]';
    document.querySelectorAll(PRODUCT_LINK_SELECTOR).forEach(anchor => {
      if (anchor.dataset.tooltipAttached || anchor.dataset.enhancedTooltipAttached) return;
      // Prefer an inner visible span, but fall back to the anchor itself
      const titleSpan =
        anchor.querySelector('span:not([class*="offscreen"]):not([class*="sr-only"]):not([class*="hidden"]):not([class*="aok-offscreen"])') ||
        anchor;
      const text = (titleSpan.textContent || '').trim();
      if (text.length < 10 || text.length > 250) return;
      if (/^(see more|view|shop|browse|sponsored|click|visit|back|deals|all|sign in|your|cart|list|registry|orders|account)/i.test(text)) return;
      if (/^\d/.test(text)) return; // skip price-like strings
      if (tiles.some(t => t.textContent.trim() === text)) return;
      if (!titleSpan.dataset.tooltipAttached) tiles.push(titleSpan);
    });

    // ── Deduplicate and validate ───────────────────────────────────────────────
    tiles = tiles.filter((el, index, arr) => {
      const text = el.textContent.trim();
      return text.length >= 10 &&
             text.length < 250 &&
             !el.dataset.tooltipAttached &&
             el.dataset.enhancedTooltipAttached !== "true" &&
             arr.findIndex(other => other.textContent.trim() === text) === index &&
             !/^\d/.test(text) && // skip price strings
             !/^(see more|view details|add to cart|check each product page|back to results|sign in|your orders|cart|wishlist)/i.test(text);
    });
    
    console.log("✅ Product tiles found:", tiles.length);

    for (const tile of tiles) {
      tile.dataset.tooltipAttached = "true";
      const title = tile.textContent.trim();

      // Try extracting primary from tile DOM context first
      let tileContextMaterial = extractMaterialFromTile(tile);

      // Always run full title scan to get both primary and secondary
      const { primary: titlePrimary, secondary } = await detectMaterials(title);

      // Prefer tile-context material for primary (more specific), fall back to title scan
      const materialHint = tileContextMaterial || titlePrimary;

      const info = await window.ecoLookup(title, materialHint);

      // Synthesise a minimal badge-info when ecoLookup has no data.
      // This ensures every detected product gets a coloured pill — even when
      // the exact material isn't in material_insights.json.
      let badgeInfo = info;
      if (!badgeInfo || !badgeInfo.impact || badgeInfo.impact === 'Unknown') {
        const estimatedImpact = estimateImpactFromTitle(materialHint || titlePrimary, title);
        if (estimatedImpact) {
          badgeInfo = { impact: estimatedImpact, name: materialHint || titlePrimary || 'unknown', estimated: true };
        }
      }

      showTooltipFor(tile, info, secondary);   // tooltip uses real lookup (may be null → no tooltip)
      addImpactBadge(tile, badgeInfo);          // badge uses best available info
    }

    // Update summary bar and filter buttons after processing all tiles
    injectOrUpdateSummaryBar();
    injectOrUpdateFilterBar();
  }
}

// Fast title/material-based impact estimator — used as final badge fallback
// when ecoLookup has no data for the detected material.
function estimateImpactFromTitle(materialHint, title) {
  const s = ((materialHint || '') + ' ' + (title || '')).toLowerCase();

  // Low — renewables, recycled, natural bio materials
  if (/\b(bamboo|cork|hemp|organic cotton|recycled cotton|recycled polyester|recycled nylon|recycled plastic|reclaimed wood|linen|paper|cardboard|beeswax|rattan|jute|sisal)\b/.test(s)) return 'Low';

  // Low-Moderate — natural, long-lasting materials
  if (/\b(cotton|wool|merino|cashmere|silk|down|timber|oak|pine|walnut|birch|teak|mahogany|maple|beech|acacia|leather|rubber|silicone|ceramic|porcelain|stoneware|glass|bamboo board)\b/.test(s)) return 'Low-Moderate';

  // Moderate — common industrially produced materials
  if (/\b(steel|iron|aluminium|aluminum|metal|polyester|nylon|plastic|polypropylene|polyethylene|pvc|acrylic|velvet|upholster|foam|memory foam|fleece|viscose|rayon|faux leather|vegan leather)\b/.test(s)) return 'Moderate';

  // High — energy/mining-intensive materials
  if (/\b(carbon fibre|carbon fiber|carbon steel|stainless steel|cast iron|titanium|lithium|battery|circuit|pcb|electronic)\b/.test(s)) return 'High';

  // Category-based fallbacks on title alone
  const t = (title || '').toLowerCase();
  if (/\b(book|paperback|hardcover|notebook|journal|diary|puzzle|board game|card game)\b/.test(t)) return 'Low';
  if (/\b(t-shirt|shirt|tee|socks|underwear|hoodie|jumper|sweater|dress|skirt|jeans|trousers|leggings|hat|scarf|gloves|trainers|sneakers|shoes|boots)\b/.test(t)) return 'Low-Moderate';
  if (/\b(sofa|couch|chair|stool|table|desk|shelf|cabinet|bed|mattress|wardrobe|bookcase|ottoman|footrest|pouffe)\b/.test(t)) return 'Moderate';
  if (/\b(bag|backpack|luggage|suitcase|wallet|purse|belt|handbag|tote)\b/.test(t)) return 'Moderate';
  if (/\b(mug|cup|plate|bowl|bottle|flask|tumbler|pan|pot|wok|cookware|cutlery|utensil|chopping board)\b/.test(t)) return 'Moderate';
  if (/\b(toy|game|lego|playset|doll|action figure|puzzle|fidget)\b/.test(t)) return 'Moderate';
  if (/\b(phone|laptop|tablet|computer|monitor|tv|television|camera|headphones|earbuds|charger|speaker|router|keyboard|mouse|smartwatch|console|gaming)\b/.test(t)) return 'High';

  return null; // Give up only if truly nothing matches
}

// Inject a small coloured impact badge inline after the product title text
function addImpactBadge(target, badgeInfo) {
  if (!ecoSettings.showBadges) return;
  if (!badgeInfo || !badgeInfo.impact || badgeInfo.impact === "Unknown") return;
  if (target.dataset.ecoBadgeAdded) return;
  target.dataset.ecoBadgeAdded = "true";

  const colorMap = {
    "Low":          { bg: "#10b981", text: "🌱 Low" },
    "Low-Moderate": { bg: "#84cc16", text: "🌿 Low-Med" },
    "Moderate":     { bg: "#f59e0b", text: "⚠️ Med" },
    "High":         { bg: "#ef4444", text: "🔥 High" },
  };
  const style = colorMap[badgeInfo.impact] || { bg: "#6b7280", text: "❓" };

  // ~ prefix when impact was estimated from title keywords, not from material_insights.json
  const prefix = badgeInfo.estimated === true ? '~' : '';

  const badge = document.createElement("span");
  badge.className = "eco-impact-badge";
  badge.style.cssText = [
    "display:inline-block",
    "margin-left:6px",
    "padding:1px 7px",
    "border-radius:9999px",
    "font-size:10px",
    "font-weight:700",
    "color:#fff",
    `background:${style.bg}`,
    "vertical-align:middle",
    "line-height:1.6",
    "white-space:nowrap",
    "pointer-events:none",
    "font-family:system-ui,-apple-system,sans-serif",
    "opacity:0.95",
  ].join(";");
  badge.textContent = prefix + style.text;

  // Insert after the target span, or append inside it if no next sibling
  if (target.nextSibling) {
    target.parentNode.insertBefore(badge, target.nextSibling);
  } else {
    target.parentNode?.appendChild(badge);
  }

  // Mark the nearest [data-asin] container for eco filter targeting
  const container = target.closest('[data-asin]');
  if (container) {
    container.dataset.ecoImpact = badgeInfo.impact;
  }
}

// ── Eco summary bar: shows count of products analysed by impact level ─────────
function injectOrUpdateSummaryBar() {
  // Only on listing/search pages, not product detail
  if (document.querySelector('#productTitle')) return;

  const counts = { Low: 0, 'Low-Moderate': 0, Moderate: 0, High: 0 };
  let total = 0;
  document.querySelectorAll('[data-asin][data-eco-impact]').forEach(el => {
    const impact = el.dataset.ecoImpact;
    if (counts[impact] !== undefined) { counts[impact]++; total++; }
  });
  if (total === 0) return;

  // Find the results container
  const anchor =
    document.querySelector('.s-main-slot') ||
    document.querySelector('[data-component-type="s-search-result"]')?.parentElement ||
    document.querySelector('#search');
  if (!anchor) return;

  let bar = document.getElementById('eco-summary-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'eco-summary-bar';
    bar.style.cssText = [
      'width:100%','box-sizing:border-box',
      'padding:8px 16px','margin-bottom:8px',
      'background:linear-gradient(135deg,rgba(15,15,35,0.92),rgba(22,33,62,0.92))',
      'border:1px solid rgba(0,212,255,0.2)','border-radius:10px',
      'font-family:system-ui,-apple-system,sans-serif',
      'font-size:13px','color:#e2e8f0',
      'display:flex','align-items:center','gap:14px','flex-wrap:wrap',
      'position:relative','z-index:9000',
    ].join(';');
    anchor.insertBefore(bar, anchor.firstChild);
  }

  bar.innerHTML = `
    <span style="font-weight:700;color:#00d4ff;white-space:nowrap;">🌍 Eco: ${total} analysed</span>
    ${counts['Low']        ? `<span style="color:#10b981;font-weight:600;">🌱 Low: ${counts['Low']}</span>` : ''}
    ${counts['Low-Moderate'] ? `<span style="color:#84cc16;font-weight:600;">🌿 Low-Med: ${counts['Low-Moderate']}</span>` : ''}
    ${counts['Moderate']   ? `<span style="color:#f59e0b;font-weight:600;">⚠️ Med: ${counts['Moderate']}</span>` : ''}
    ${counts['High']       ? `<span style="color:#ef4444;font-weight:600;">🔥 High: ${counts['High']}</span>` : ''}
    <span style="margin-left:auto;font-size:11px;color:#475569;">Scroll for more →</span>
  `;
}

// ── Eco filter buttons: hide/show result tiles by impact level ────────────────
function injectOrUpdateFilterBar() {
  if (document.querySelector('#productTitle')) return;
  if (document.querySelectorAll('[data-asin][data-eco-impact]').length === 0) return;

  const anchor =
    document.querySelector('.s-main-slot') ||
    document.querySelector('[data-component-type="s-search-result"]')?.parentElement ||
    document.querySelector('#search');
  if (!anchor) return;

  let filterBar = document.getElementById('eco-filter-bar');
  if (!filterBar) {
    filterBar = document.createElement('div');
    filterBar.id = 'eco-filter-bar';
    filterBar.style.cssText = [
      'width:100%','box-sizing:border-box',
      'padding:6px 16px','margin-bottom:10px',
      'display:flex','align-items:center','gap:8px','flex-wrap:wrap',
      'font-family:system-ui,-apple-system,sans-serif',
    ].join(';');

    const summaryBar = document.getElementById('eco-summary-bar');
    if (summaryBar) {
      anchor.insertBefore(filterBar, summaryBar.nextSibling);
    } else {
      anchor.insertBefore(filterBar, anchor.firstChild);
    }

    // Build filter button set
    const filters = [
      { key: 'all',          label: '🔍 All',        active_col: '#00d4ff', border: 'rgba(0,212,255,0.4)' },
      { key: 'Low',          label: '🌱 Low',         active_col: '#10b981', border: 'rgba(16,185,129,0.4)' },
      { key: 'Low-Moderate', label: '🌿 Low-Med',     active_col: '#84cc16', border: 'rgba(132,204,22,0.4)'  },
      { key: 'Moderate',     label: '⚠️ Med',         active_col: '#f59e0b', border: 'rgba(245,158,11,0.4)'  },
      { key: 'High',         label: '🔥 High',        active_col: '#ef4444', border: 'rgba(239,68,68,0.4)'   },
    ];

    const label = document.createElement('span');
    label.style.cssText = 'font-size:12px;font-weight:600;color:#94a3b8;margin-right:4px;';
    label.textContent = 'Eco Filter:';
    filterBar.appendChild(label);

    filters.forEach(f => {
      const btn = document.createElement('button');
      btn.dataset.ecoFilterKey = f.key;
      btn.style.cssText = [
        'padding:3px 10px','border-radius:9999px',
        'border:1px solid rgba(255,255,255,0.15)',
        'background:rgba(255,255,255,0.06)',
        'color:#94a3b8','font-size:11px','font-weight:600',
        'cursor:pointer','transition:all 0.15s',
        'font-family:system-ui,-apple-system,sans-serif',
        'white-space:nowrap',
      ].join(';');
      btn.textContent = f.label;
      btn.addEventListener('click', () => {
        activeEcoFilter = f.key;
        // Update button styles
        filterBar.querySelectorAll('button[data-eco-filter-key]').forEach(b => {
          const bf = filters.find(x => x.key === b.dataset.ecoFilterKey);
          if (b.dataset.ecoFilterKey === activeEcoFilter) {
            b.style.background = bf ? bf.active_col + '33' : 'rgba(0,212,255,0.15)';
            b.style.borderColor = bf ? bf.border : 'rgba(0,212,255,0.4)';
            b.style.color = bf ? bf.active_col : '#00d4ff';
          } else {
            b.style.background = 'rgba(255,255,255,0.06)';
            b.style.borderColor = 'rgba(255,255,255,0.15)';
            b.style.color = '#94a3b8';
          }
        });
        applyEcoFilter();
      });
      filterBar.appendChild(btn);
    });
  }

  // Re-apply current filter whenever new products have loaded
  applyEcoFilter();
  // Highlight active filter button
  filterBar.querySelectorAll('button[data-eco-filter-key]').forEach(btn => {
    const isActive = btn.dataset.ecoFilterKey === activeEcoFilter;
    btn.style.background = isActive ? 'rgba(0,212,255,0.15)' : 'rgba(255,255,255,0.06)';
    btn.style.borderColor = isActive ? 'rgba(0,212,255,0.4)' : 'rgba(255,255,255,0.15)';
    btn.style.color = isActive ? '#00d4ff' : '#94a3b8';
  });
}

function applyEcoFilter() {
  // Only target actual product result tiles, not nav/breadcrumbs/carousels
  const productTiles = document.querySelectorAll(
    '[data-component-type="s-search-result"][data-asin]'
  );
  if (productTiles.length === 0) {
    // Fallback: li[data-asin] tiles (some Amazon layouts)
    document.querySelectorAll('li[data-asin][data-eco-impact]').forEach(container => {
      if (activeEcoFilter === 'all') {
        container.style.display = '';
      } else {
        container.style.display = (container.dataset.ecoImpact === activeEcoFilter) ? '' : 'none';
      }
    });
    return;
  }
  productTiles.forEach(container => {
    if (activeEcoFilter === 'all') {
      container.style.display = '';
    } else {
      const impact = container.dataset.ecoImpact;
      container.style.display = (impact === activeEcoFilter) ? '' : 'none';
    }
  });
}




// ⏱️ Improved debounced observer to prevent overload
let lastEnhanceRun = 0;
let enhanceTimeout = null;
let isEnhancing = false;
const DEBOUNCE_MS = 1500; // Reduced for more responsiveness
const MIN_INTERVAL_MS = 500; // Minimum time between enhancements

function debouncedEnhanceTooltips() {
  const now = Date.now();
  
  // Don't run if already enhancing
  if (isEnhancing) {
    console.log("⏳ Enhancement already in progress, skipping");
    return;
  }
  
  // Don't run too frequently
  if (now - lastEnhanceRun < MIN_INTERVAL_MS) {
    if (enhanceTimeout) {
      clearTimeout(enhanceTimeout);
    }
    enhanceTimeout = setTimeout(() => {
      debouncedEnhanceTooltips();
    }, MIN_INTERVAL_MS - (now - lastEnhanceRun));
    return;
  }
  
  if (now - lastEnhanceRun > DEBOUNCE_MS) {
    lastEnhanceRun = now;
    isEnhancing = true;
    enhanceTooltips().catch(console.error).finally(() => {
      isEnhancing = false;
    });
  } else {
    // Clear existing timeout and set a new one
    if (enhanceTimeout) {
      clearTimeout(enhanceTimeout);
    }
    enhanceTimeout = setTimeout(() => {
      lastEnhanceRun = Date.now();
      isEnhancing = true;
      enhanceTooltips().catch(console.error).finally(() => {
        isEnhancing = false;
      });
    }, DEBOUNCE_MS);
  }
}

// Smart initialization without aggressive cleanup
let pageInitialized = false;

// Cleanup broken tooltips on page unload
window.addEventListener("beforeunload", cleanupBrokenTooltips);

// Initialize on page load
window.addEventListener("load", () => {
  if (!pageInitialized) {
    pageInitialized = true;
    cleanupBrokenTooltips();
    setTimeout(debouncedEnhanceTooltips, 1000);
  }
});

// Also initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (!pageInitialized) {
      pageInitialized = true;
      cleanupBrokenTooltips();
      setTimeout(debouncedEnhanceTooltips, 500);
    }
  });
} else if (!pageInitialized) {
  pageInitialized = true;
  cleanupBrokenTooltips();
  debouncedEnhanceTooltips();
}

// Monitor for dynamic content changes (common on Amazon)
const observer = new MutationObserver((mutations) => {
  // Only trigger if meaningful changes occurred
  const hasRelevantChanges = mutations.some(mutation =>
    mutation.type === 'childList' &&
    mutation.addedNodes.length > 0 &&
    Array.from(mutation.addedNodes).some(node =>
      node.nodeType === Node.ELEMENT_NODE
    )
  );
  
  if (hasRelevantChanges) {
    debouncedEnhanceTooltips();
  }
});

observer.observe(document.body, { 
  childList: true, 
  subtree: true,
  attributeFilter: ['class', 'data-component-type'] // Only watch for relevant attribute changes
});

// Also run when URL changes (for SPA navigation)
let currentUrl = window.location.href;
setInterval(() => {
  if (window.location.href !== currentUrl) {
    currentUrl = window.location.href;
    setTimeout(debouncedEnhanceTooltips, 500);
  }
}, 1000);

// Also trigger on scroll to catch lazy-loaded products
window.addEventListener('scroll', debouncedEnhanceTooltips, { passive: true });
