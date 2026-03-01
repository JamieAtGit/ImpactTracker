// tooltip.js — Cursor-following eco tooltip

// ⚠️ LEGACY createFloatingTooltip - DISABLED
function createFloatingTooltip() {
  console.log("⚠️ Legacy createFloatingTooltip() called but DISABLED");
  return null;
}

function guessMaterialFromCategory(title) {
  const lower = title.toLowerCase();
  if (lower.includes("headphones") || lower.includes("earbuds")) return "plastics";
  if (lower.includes("phone case") || lower.includes("cover")) return "plastics";
  if (lower.includes("laptop") || lower.includes("notebook")) return "aluminum";
  if (lower.includes("bottle") || lower.includes("thermos")) return "steel";
  if (lower.includes("jacket") || lower.includes("coat")) return "polyester";
  if (lower.includes("shoes") || lower.includes("trainers")) return "rubber";
  if (lower.includes("backpack") || lower.includes("rucksack") || lower.includes("hiking")) return "nylon";
  if (lower.includes("bag") && !lower.includes("sleeping")) return "nylon";
  return null;
}

// ✅ Enhanced material insights loader
window.loadMaterialInsights = async function () {
  try {
    const getURL = typeof chrome !== "undefined" && chrome.runtime?.getURL
      ? chrome.runtime.getURL
      : (path) => path;
    const res = await fetch(getURL('material_insights.json'));
    const insights = await res.json();
    console.log("📚 Material insights loaded:", Object.keys(insights).length, "materials");
    return insights;
  } catch (e) {
    console.error("❌ Failed to load insights:", e);
    return {};
  }
};

// ⚠️ LEGACY enhanceTooltips function - DISABLED
// This has been moved to /src/components/tooltip.js with major improvements
// Keeping this file only for the ecoLookup function and utilities

async function enhanceTooltips() {
  // DISABLED - Using enhanced tooltip.js implementation instead
  console.log("⚠️ Legacy enhanceTooltips() called but DISABLED - using enhanced tooltip.js instead");
  return;
}

// Enhanced material type detection function with comprehensive families
function detectSpecificMaterialType(materialHint, data) {
  if (!materialHint) return null;
  
  const hint = materialHint.toLowerCase();
  
  // Define comprehensive material families and their specific types
  const materialFamilies = {
    // METALS - Comprehensive metal family
    metals: {
      'precious_metals': ['gold', 'silver', 'platinum', 'palladium'],
      'common_metals': ['aluminum', 'aluminium', 'steel', 'iron', 'copper', 'brass', 'bronze', 'zinc', 'tin', 'lead'],
      'specialty_metals': ['titanium', 'titanium alloys', 'stainless steel', 'carbon steel', 'tool steel', 'low-alloy steel', 'cast iron', 'nickel alloys'],
      'metal_composites': ['metal', 'alloy', 'metallic']
    },
    
    // POLYMERS - Reorganized and expanded polymer family
    polymers: {
      'thermoplastics': ['polyethylene', 'polypropylene', 'polystyrene', 'pvc', 'abs', 'polycarbonate', 'pmma', 'acrylic'],
      'thermosets': ['polyurethane', 'epoxy', 'phenolic', 'ptfe'],
      'bio_polymers': ['pla', 'pha', 'pbat', 'bioplastic'],
      'recycled_polymers': ['recovered plastic', 'recycled plastic', 'plastics'],
      'specialty_polymers': ['kevlar', 'qmonos', 'vinyl']
    },
    
    // ELASTOMERS - Rubber and elastic materials
    elastomers: {
      'natural_rubber': ['rubber', 'natural rubber', 'latex'],
      'synthetic_elastomers': ['silicone', 'neoprene', 'epdm', 'reclaimed rubber'],
      'elastic_fibers': ['elastane', 'spandex', 'lycra']
    },
    
    // CERAMICS - Clay-based and technical ceramics
    ceramics: {
      'traditional_ceramics': ['ceramic', 'ceramics', 'porcelain', 'stoneware', 'earthenware', 'terracotta'],
      'construction_ceramics': ['brick', 'tile', 'clay'],
      'technical_ceramics': ['alumina', 'zirconia', 'silicon carbide']
    },
    
    // GLASSES - Various glass types
    glasses: {
      'common_glass': ['glass', 'tempered glass', 'laminated glass'],
      'specialty_glass': ['borosilicate', 'optical glass', 'crystal'],
      'glass_composites': ['fiberglass', 'glass fiber']
    },
    
    // STONE/MINERAL - Natural and processed stone materials
    stone_mineral: {
      'natural_stone': ['granite', 'marble', 'limestone', 'sandstone', 'slate', 'stone', 'quartz'],
      'processed_stone': ['concrete', 'cement', 'terrazzo', 'plaster']
    },
    
    // TEXTILES - Comprehensive textile families
    textiles: {
      'natural_plant_fibers': ['cotton', 'linen', 'hemp', 'jute', 'ramie', 'sisal', 'abaca', 'nettle fiber', 'coir', 'coconut fiber'],
      'natural_animal_fibers': ['wool', 'silk', 'cashmere', 'alpaca', 'mohair', 'merino wool', 'down', 'angora'],
      'synthetic_fibers': ['polyester', 'nylon', 'acrylic', 'spandex', 'elastane', 'lycra', 'viscose', 'rayon', 'modal', 'lyocell', 'lyocell tencel'],
      'innovative_bio_fibers': ['milk fiber', 'orange fiber', 'rose fiber', 'soy fabric', 'lotus fiber', 'seacell', 'econyl', 's.cafe'],
      'recycled_textiles': ['recycled cotton', 'recycled polyester', 'recycled wool', 'recycled nylon'],
      'fabric_constructions': ['denim', 'canvas', 'velvet', 'satin', 'chiffon', 'georgette', 'organza', 'tulle', 'corduroy', 'flannel', 'fleece', 'jersey', 'crepe', 'seersucker']
    },
    
    // LEATHER - Expanded leather family
    leather: {
      'genuine_leather': ['leather', 'genuine leather', 'real leather', 'full grain leather', 'top grain leather', 'nubuck', 'suede', 'patent leather'],
      'alternative_leather': ['faux leather', 'vegan leather', 'synthetic leather', 'pleather'],
      'innovative_leather': ['mushroom leather', 'mycelium', 'apple leather', 'grape leather', 'cactus leather', 'palm leather', 'piñatex'],
      'recycled_leather': ['recycled leather', 'bonded leather']
    },
    
    // WOOD/PLANT - Wood and plant-based materials
    wood_plant: {
      'solid_wood': ['timber', 'wood', 'lumber', 'hardwood', 'softwood'],
      'engineered_wood': ['plywood', 'mdf', 'chipboard', 'osb', 'oriented strand board'],
      'sustainable_wood': ['bamboo', 'cork', 'reclaimed wood', 'rattan'],
      'plant_materials': ['kapok', 'bagasse', 'rice hulls', 'wheat straw', 'sunflower hulls']
    },
    
    // PAPER/CELLULOSE - Paper-based materials
    paper_cellulose: {
      'paper_products': ['paper', 'cardboard', 'wood pulp'],
      'specialty_paper': ['tapa cloth', 'kraft paper']
    },
    
    // COMPOSITES/HYBRIDS - Advanced composite materials
    composites: {
      'fiber_composites': ['carbon fiber', 'fiberglass', 'kevlar', 'aramid'],
      'bio_composites': ['bananatex', 'hemp composite'],
      'engineered_composites': ['composite', 'hybrid material']
    },
    
    // CONSTRUCTION - Building and construction materials
    construction: {
      'structural': ['concrete', 'cement', 'brick', 'drywall', 'plaster'],
      'finishing': ['paint', 'paints', 'water-based paint', 'roofing', 'siding', 'insulation'],
      'adhesives': ['adhesives', 'glues', 'epoxy']
    },
    
    // CHEMICAL/PROCESSING - Chemical and processing materials
    chemical: {
      'processing_agents': ['dyeing agents', 'tanning agents'],
      'surface_materials': ['linoleum', 'sanding dust']
    }
  };
  
  // Check for specific material types across all families
  for (const [familyName, subcategories] of Object.entries(materialFamilies)) {
    for (const [subcategoryName, types] of Object.entries(subcategories)) {
      for (const type of types) {
        if (hint.includes(type) && data[type]) {
          console.log(`🎯 Found specific ${familyName} (${subcategoryName}):`, type);
          return { 
            material: type, 
            confidence: 95, 
            isSpecific: true, 
            family: familyName,
            subcategory: subcategoryName 
          };
        }
      }
    }
  }
  
  // Enhanced compound material detection with comprehensive patterns
  const compoundPatterns = [
    // Metal compounds
    /(stainless|carbon|tool|low-alloy)\s+steel/,
    /(titanium|nickel|aluminum)\s+(alloy|alloys)/,
    /(cast|wrought)\s+iron/,
    
    // Polymer compounds
    /(recycled|bio|recovered)\s+(plastic|polymer)/,
    /(thermoplastic|thermoset)\s+(\w+)/,
    
    // Textile compounds
    /(organic|recycled|sustainable|premium)\s+(cotton|wool|silk|polyester|nylon)/,
    /(merino|cashmere|alpaca|mohair)\s+wool/,
    /(genuine|real|authentic|full\s+grain|top\s+grain)\s+(leather)/,
    /(vegan|faux|synthetic|artificial)\s+(leather|suede)/,
    /(recycled|organic)\s+(cotton|polyester|wool|nylon)/,
    
    // Glass compounds
    /(tempered|laminated|borosilicate)\s+glass/,
    /(fiber|fibre)\s+glass/,
    
    // Wood compounds
    /(reclaimed|engineered|solid)\s+(wood|timber)/,
    /(oriented\s+strand|particle)\s+board/,
    
    // Stone compounds
    /(natural|artificial|engineered)\s+(stone|marble|granite)/,
    
    // Ceramic compounds
    /(technical|advanced|traditional)\s+(ceramic|ceramics)/,
    
    // General modifiers
    /(premium|high-grade|industrial|medical-grade|food-grade)\s+(\w+)/,
    /(\w+)\s+(fiber|fibre|composite|blend)/
  ];
  
  for (const pattern of compoundPatterns) {
    const match = hint.match(pattern);
    if (match) {
      const compound = match[0].trim();
      const modifier = match[1];
      const base = match[2] || match[1];
      
      // Check if we have the specific compound material
      if (data[compound]) {
        console.log('🧬 Found compound material:', compound);
        return { 
          material: compound, 
          confidence: 90, 
          isSpecific: true,
          compound: true,
          modifier: modifier
        };
      }
      
      // Check for close matches in our database
      const closeMatches = Object.keys(data).filter(key => 
        key.toLowerCase().includes(compound.toLowerCase()) || 
        compound.toLowerCase().includes(key.toLowerCase())
      );
      
      if (closeMatches.length > 0) {
        const bestMatch = closeMatches[0];
        console.log('🔍 Found close compound match:', compound, '→', bestMatch);
        return { 
          material: bestMatch, 
          confidence: 85, 
          isSpecific: true,
          compound: true,
          originalHint: compound
        };
      }
      
      // Fall back to base material
      if (base && data[base]) {
        console.log('🔄 Using base material for compound:', compound, '→', base);
        return { 
          material: base, 
          confidence: 75, 
          isSpecific: false,
          compound: true,
          baseOf: compound
        };
      }
    }
  }
  
  return null;
}

window.ecoLookup = async function (title, materialHint) {
  try {
    // Use cached data if available
    let data = window.materialInsights;
    if (!data) {
      const getURL = typeof chrome !== "undefined" && chrome.runtime?.getURL
        ? chrome.runtime.getURL
        : (path) => path;

      const res = await fetch(getURL("material_insights.json"));
      data = await res.json();
      window.materialInsights = data; // Cache for future use
    }

    // Normalize inputs
    title = (title || "").toLowerCase();
    materialHint = (materialHint || "")
      .replace(/[\u200E\u200F\u202A-\u202E]/g, "") // Strip hidden Unicode chars
      .trim()
      .toLowerCase();

    console.log("🔍 Looking up title:", title.substring(0, 50) + "...");
    if (materialHint) console.log("🧪 Material hint:", materialHint);

    // Priority 1: Try to detect specific material type first
    if (materialHint && materialHint !== "unknown") {
      const specificResult = detectSpecificMaterialType(materialHint, data);
      if (specificResult) {
        return { 
          ...data[specificResult.material], 
          name: specificResult.material, 
          confidence: specificResult.confidence,
          isSpecific: specificResult.isSpecific,
          family: specificResult.family,
          subcategory: specificResult.subcategory,
          compound: specificResult.compound,
          modifier: specificResult.modifier,
          originalHint: specificResult.originalHint,
          baseOf: specificResult.baseOf
        };
      }
      
      // Enhanced exact matching
      for (const key in data) {
        if (materialHint.includes(key.toLowerCase()) || key.toLowerCase().includes(materialHint)) {
          console.log("✅ Matched from material hint:", key);
          return { ...data[key], name: key, confidence: 95 };
        }
      }
      
      // Enhanced fallback mapping for common mismatches
      const materialFallbacks = {
        'polycarbonate': 'plastics',
        'plastic': 'plastics', 
        'pvc': 'pvc',
        'abs': 'abs',
        'polyethylene': 'polyethylene',
        'polypropylene': 'polypropylene',
        'metal': 'steel',
        'metallic': 'aluminum',
        'wood': 'timber',
        'fabric': 'cotton',
        'cloth': 'cotton',
        'synthetic': 'polyester',
        'genuine': 'leather',
        'real leather': 'leather',
        'suede': 'leather'
      };
      
      const fallback = materialFallbacks[materialHint.toLowerCase()];
      if (fallback && data[fallback]) {
        console.log("🔄 Using fallback mapping:", materialHint, "→", fallback);
        return { ...data[fallback], name: fallback, confidence: 85 };
      }
    }

    // Priority 2: Enhanced fuzzy match from title
    let bestMatch = null;
    let highestConfidence = 0;

    for (const key in data) {
      const keyLower = key.toLowerCase();
      
      // Check for exact word boundary matches first
      const exactRegex = new RegExp(`\\b${keyLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, "i");
      if (exactRegex.test(title)) {
        const confidence = 90 + (keyLower.length / title.length) * 10; // Longer matches get higher confidence
        if (confidence > highestConfidence) {
          bestMatch = { ...data[key], name: key, confidence: Math.min(confidence, 100) };
          highestConfidence = confidence;
        }
      }
      
      // Then check for partial matches
      else if (title.includes(keyLower) && keyLower.length > 3) {
        const confidence = 70 + (keyLower.length / title.length) * 20;
        if (confidence > highestConfidence) {
          bestMatch = { ...data[key], name: key, confidence: Math.min(confidence, 85) };
          highestConfidence = confidence;
        }
      }
    }

    if (bestMatch && highestConfidence > 60) {
      console.log("🔍 Fuzzy matched from title:", bestMatch.name, "confidence:", bestMatch.confidence);
      return bestMatch;
    }

    // Priority 3: Enhanced category guessing
    const fallback = guessMaterialFromCategory(title);
    if (fallback && data[fallback]) {
      console.log("🔁 Using fallback category material:", fallback);
      return { ...data[fallback], name: fallback, confidence: 60 };
    }

    // Priority 4: Look for common material descriptors in title with proper mapping
    const commonMaterials = [
      { search: 'plastic', material: 'plastics' },
      { search: 'metal', material: 'steel' },
      { search: 'wood', material: 'timber' },
      { search: 'steel', material: 'steel' },
      { search: 'aluminum', material: 'aluminum' },
      { search: 'glass', material: 'glass' },
      { search: 'ceramic', material: 'ceramic' },
      { search: 'rubber', material: 'rubber' },
      { search: 'leather', material: 'leather' },
      { search: 'cotton', material: 'cotton' },
      { search: 'polyester', material: 'polyester' },
      { search: 'nylon', material: 'nylon' }
    ];
    
    for (const item of commonMaterials) {
      if (title.includes(item.search) && data[item.material]) {
        console.log("🎯 Found common material in title:", item.material);
        return { ...data[item.material], name: item.material, confidence: 50 };
      }
    }

    console.log("❓ No material match found for:", title.substring(0, 30) + "...");
    return null;
    
  } catch (error) {
    console.error("❌ Error in ecoLookup:", error);
    return null;
  }
};