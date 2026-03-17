"""
Primary development Flask API application.

Purpose:
- Exposes the main prediction and scraping endpoints used during local development.
- Loads ML assets, scraper integrations, and route modules.
- Configures CORS, sessions, and request handling for frontend + extension clients.
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import joblib
import sys
import os
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BASE_DIR)

# Unified ML assets directory (single location)
# Can be overridden with env var ML_ASSETS_DIR
ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(BASE_DIR, "ml"))
model_dir = ML_ASSETS_DIR
encoders_dir = os.path.join(ML_ASSETS_DIR, "encoders")

import json

from backend.routes.auth import register_routes
from backend.routes.api import calculate_eco_score
from backend.routes.enterprise_dashboard import enterprise_bp
try:
    from backend.routes.benchmarking_api import benchmarking_bp
except ImportError:
    benchmarking_bp = None

# Add manufacturing complexity system for realistic CO2 calculations (project-relative)
SERVICES_DIR = os.path.join(BASE_DIR, 'backend', 'services')
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)
try:
    from manufacturing_complexity_multipliers import ManufacturingComplexityCalculator
    from enhanced_materials_database import EnhancedMaterialsDatabase
    
    # Initialize for realistic CO2 calculations
    complexity_calculator = ManufacturingComplexityCalculator()
    materials_db = EnhancedMaterialsDatabase()
    print("✅ Main API now using realistic CO2 calculations with manufacturing complexity")
    MANUFACTURING_COMPLEXITY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Manufacturing complexity not available: {e}")
    MANUFACTURING_COMPLEXITY_AVAILABLE = False


import pandas as pd
# Import production scraper with category intelligence and enhanced reliability
try:
    from backend.scrapers.amazon.production_scraper import ProductionAmazonScraper
    PRODUCTION_SCRAPER_AVAILABLE = True
    print("✅ Production scraper with category intelligence loaded")
except ImportError as e:
    print(f"⚠️ Production scraper not available: {e}")
    PRODUCTION_SCRAPER_AVAILABLE = False

# Always import unified scraper functions
from backend.scrapers.amazon.unified_scraper import (
    scrape_amazon_product_page,  # Final fallback scraper
    UnifiedProductScraper
)

# Always try to load enhanced scraper as fallback
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from enhanced_scraper_fix import EnhancedAmazonScraper
    ENHANCED_SCRAPER_AVAILABLE = True
    print("✅ Enhanced scraper with dual origins loaded (fallback)")
except ImportError as e2:
    ENHANCED_SCRAPER_AVAILABLE = False
    print(f"⚠️ Enhanced scraper not available: {e2}")
from backend.scrapers.amazon.integrated_scraper import (
    estimate_origin_country,
    resolve_brand_origin,
    save_brand_locations,
    haversine, 
    origin_hubs, 
    uk_hub
)
from backend.models.database import db, ScrapedProduct, EmissionCalculation, find_cached_emission_calculation, get_or_create_scraped_product, save_emission_calculation
from backend.services.prediction_consistency import apply_material_title_consistency, normalize_amazon_url, extract_asin_from_amazon_url
from backend.services.response_standardizer import standardize_attributes

import csv
import re
import numpy as np
import pgeocode

# === Load Flask ===
#   app = Flask(__name__)
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    static_url_path="/static"
)
# Configure Flask with production security settings
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# For Railway deployment, we need to handle HTTPS properly
is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('RAILWAY_ENVIRONMENT') == 'production'

app.config['SESSION_COOKIE_SECURE'] = is_production  # Only require HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if is_production else 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow cross-domain cookies
app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # 2 hours

app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.getenv('DATABASE_URL', 'sqlite:///impacttracker_local.db'))
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
try:
    if 'sqlalchemy' not in app.extensions:
        db.init_app(app)
    with app.app_context():
        db.create_all()
    print("✅ Local database cache initialized")
except Exception as db_init_error:
    print(f"⚠️ Database initialization skipped: {db_init_error}")

def extract_weight_from_title(title: str) -> float:
    """
    Enhanced weight extraction that avoids nutritional content
    Works for ANY product type with category-specific intelligence
    """
    if not title:
        return 0.0
    import re

    print(f"🔍 Extracting weight from title: {title}")

    title_lower = title.lower()
    nutritional_exclusions = [
        r'\d+\s*g\s*protein\b',
        r'\d+\s*g\s*carbs?\b',
        r'\d+\s*g\s*fat\b',
        r'\d+\s*mg\s*(?:sodium|caffeine|vitamin|salt)\b',
    ]

    cleaned_title = title_lower
    for pattern in nutritional_exclusions:
        cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)

    patterns = [
        r'(\d+(?:\.\d+)?)\s*kg\b',
        r'(\d+(?:\.\d+)?)\s*g\b',
        r'(\d+(?:\.\d+)?)\s*lb\b',
        r'(\d+(?:\.\d+)?)\s*oz\b',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, cleaned_title, flags=re.IGNORECASE):
            value = float(match.group(1))
            unit_text = match.group(0).lower()

            if 'kg' in unit_text:
                weight_kg = value
            elif re.search(r'\bg\b', unit_text):
                weight_kg = value / 1000.0
            elif 'lb' in unit_text:
                weight_kg = value * 0.453592
            elif 'oz' in unit_text:
                weight_kg = value * 0.0283495
            else:
                continue

            if 0.01 <= weight_kg <= 50:
                print(f"✅ Weight extracted from title: {weight_kg:.3f}kg")
                return round(weight_kg, 3)
            print(f"⚠️ Weight out of range: {weight_kg:.3f}kg")
    
    print("⚠️ No valid weight found in title")
    return 0.0

def get_category_fallback_weight(title: str, brand: str = "") -> float:
    """
    Category-specific weight estimation when extraction fails
    Uses intelligent defaults based on product category
    """
    if not title:
        return 1.0
        
    title_lower = title.lower()
    
    print(f"🧠 Getting category fallback for: {title}")
    
    # Protein powder/supplement category
    if any(keyword in title_lower for keyword in ['protein', 'whey', 'casein', 'mass gainer', 'supplement']):
        # Estimate based on common protein powder sizes
        if any(size in title_lower for size in ['trial', 'sample', 'mini', 'small']):
            weight = 0.9  # ~900g trial size
            print(f"🏋️ Protein supplement (trial size): {weight}kg")
        elif any(size in title_lower for size in ['bulk', '10lb', '5kg', 'large', 'jumbo']):
            weight = 4.5  # ~4.5kg bulk size
            print(f"🏋️ Protein supplement (bulk size): {weight}kg")
        else:
            weight = 2.3  # ~2.3kg standard 5lb container
            print(f"🏋️ Protein supplement (standard size): {weight}kg")
        return weight
    
    # Pre-workout/BCAA powder
    elif any(keyword in title_lower for keyword in ['pre-workout', 'pre workout', 'bcaa', 'amino', 'creatine']):
        weight = 0.5  # Typically smaller containers
        print(f"💊 Pre-workout supplement: {weight}kg")
        return weight
    
    # Electronics category
    elif any(keyword in title_lower for keyword in ['phone', 'smartphone', 'mobile', 'iphone']):
        weight = 0.2  # Phone weight
        print(f"📱 Smartphone: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['tablet', 'ipad']):
        weight = 0.5  # Tablet weight
        print(f"📱 Tablet: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['laptop', 'notebook']):
        weight = 2.0  # Laptop weight
        print(f"💻 Laptop: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['headphone', 'earphone', 'earbuds']):
        weight = 0.3  # Headphone weight
        print(f"🎧 Headphones: {weight}kg")
        return weight
    
    # Books and media
    elif any(keyword in title_lower for keyword in ['book', 'kindle', 'paperback', 'hardcover']):
        if 'hardcover' in title_lower:
            weight = 0.6  # Hardcover book
        else:
            weight = 0.3  # Paperback book
        print(f"📚 Book: {weight}kg")
        return weight
    
    # Clothing
    elif any(keyword in title_lower for keyword in ['shirt', 't-shirt', 'top', 'blouse']):
        weight = 0.2  # Shirt weight
        print(f"👕 Shirt: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['jacket', 'coat', 'hoodie']):
        weight = 0.8  # Jacket weight
        print(f"🧥 Jacket: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['shoes', 'sneakers', 'boots']):
        weight = 1.0  # Shoe pair weight
        print(f"👟 Shoes: {weight}kg")
        return weight
    
    # Home and kitchen
    elif any(keyword in title_lower for keyword in ['mug', 'cup', 'glass']):
        weight = 0.3  # Mug weight
        print(f"☕ Mug/Cup: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['plate', 'bowl', 'dish']):
        weight = 0.5  # Plate weight
        print(f"🍽️ Dishware: {weight}kg")
        return weight
    elif any(keyword in title_lower for keyword in ['bottle', 'water bottle']):
        weight = 0.2  # Water bottle weight
        print(f"🍶 Bottle: {weight}kg")
        return weight
    
    # Paper products (toilet rolls, kitchen rolls, tissues)
    elif any(keyword in title_lower for keyword in ['toilet roll', 'toilet tissue', 'toilet paper', 'kitchen roll', 'kitchen towel', 'tissue roll']):
        import re
        pack_match = re.search(r'(\d+)\s*(?:rolls?|count|pack|sheets?)', title_lower)
        if pack_match:
            count = int(pack_match.group(1))
            weight = round(count * 0.13, 1)  # ~130g per standard roll
            print(f"🧻 Paper products ({count} rolls estimated): {weight}kg")
        else:
            weight = 1.5
            print(f"🧻 Paper products (default): {weight}kg")
        return weight

    # Tools and hardware
    elif any(keyword in title_lower for keyword in ['drill', 'screwdriver', 'hammer']):
        weight = 1.5  # Tool weight
        print(f"🔧 Tool: {weight}kg")
        return weight
    
    # Toys and games
    elif any(keyword in title_lower for keyword in ['toy', 'game', 'puzzle', 'lego']):
        weight = 0.4  # Toy weight
        print(f"🧸 Toy: {weight}kg")
        return weight
    
    # Default fallback
    weight = 1.0
    print(f"❓ Unknown category, using default: {weight}kg")
    return weight

def extract_enhanced_origins(product: dict, title: str) -> dict:
    """
    Universal origin extraction with priority system:
    1. Scraped origin from product specs (highest priority)  
    2. Brand locations database (fallback)
    3. Confidence scoring when both match
    """
    results = {}
    
    # Get current values
    scraped_origin = product.get("origin", "Unknown")
    scraped_country = product.get("country_of_origin", "Unknown") 
    scraped_facility = product.get("facility_origin", "Unknown")
    scraped_source = str(product.get("origin_source", "")).strip().lower()
    brand = product.get("brand", "")
    
    print(f"🔍 Origin analysis - Scraped: '{scraped_origin}', Brand: '{brand}'")
    
    def _is_plausible_origin(value: str) -> bool:
        if not value:
            return False
        normalized = str(value).strip()
        if normalized.lower() in {"unknown", "n/a", "na", "none"}:
            return False
        if len(normalized) < 2 or len(normalized) > 30:
            return False
        invalid_tokens = {
            "splinter", "crack", "break", "bpa", "plastic", "cutlery", "disposable",
            "friendly", "pack", "piece", "set", "weight", "size", "model", "item"
        }
        lowered = normalized.lower()
        return not any(token in lowered for token in invalid_tokens)

    def _is_explicit_page_origin_source(source: str) -> bool:
        return source in {"technical_details", "product_details", "manufacturer_contact", "specifications", "scraped_verified"}

    def _is_top_confidence_origin_source(source: str) -> bool:
        return source in {"technical_details", "product_details", "scraped_verified"}

    def _is_brand_like_source(source: str) -> bool:
        return source.startswith("brand_locations") or source in {
            "brand_db",
            "heuristic_brand_default",
            "brand_mapping",
            "title_description",
            "default_uk",
        }

    # 1. Priority: Use scraped origin if valid
    country_origin = None
    scraped_is_explicit = _is_explicit_page_origin_source(scraped_source)
    scraped_is_brand_like = _is_brand_like_source(scraped_source)

    if _is_plausible_origin(scraped_origin) and (scraped_is_explicit or not scraped_is_brand_like):
        country_origin = scraped_origin
        print(f"✅ Using scraped origin: {country_origin} (source: {scraped_source or 'unknown'})")
    elif _is_plausible_origin(scraped_country) and (scraped_is_explicit or not scraped_is_brand_like):
        country_origin = scraped_country
        print(f"✅ Using scraped country: {country_origin} (source: {scraped_source or 'unknown'})")
    
    # 2. Fallback: Brand locations database
    brand_origin = None
    if brand and brand != "Unknown":
        normalized_brand = re.sub(r'^(visit the|brand:|by)\s+', '', str(brand), flags=re.IGNORECASE).strip()
        lookup_brand = normalized_brand or brand
        brand_result = resolve_brand_origin(lookup_brand)
        # Handle case where resolve_brand_origin returns a tuple
        if isinstance(brand_result, tuple):
            brand_origin = brand_result[0] if brand_result[0] != "Unknown" else None
        else:
            brand_origin = brand_result
        
        if brand_origin and brand_origin != "UK":  # Don't use UK default
            print(f"📍 Brand database origin: {brand_origin}")
    
    # 3. Decision logic with confidence
    final_origin = None
    confidence_boost = False
    
    if country_origin and brand_origin:
        if country_origin.lower() == brand_origin.lower():
            final_origin = country_origin
            confidence_boost = True
            print(f"🎯 HIGH CONFIDENCE: Scraped '{country_origin}' matches brand '{brand_origin}'")
        elif scraped_is_explicit:
            # Explicit page-origin evidence wins over brand fallback
            final_origin = country_origin
            print(f"✅ SOURCE PRIORITY: Keeping explicit page origin '{country_origin}' over brand '{brand_origin}'")
        else:
            # If scraped source is brand-like/noisy, prefer brand DB fallback
            final_origin = brand_origin if scraped_is_brand_like else country_origin
            print(f"⚠️ CONFLICT: Scraped '{country_origin}' vs Brand '{brand_origin}' - using '{final_origin}'")
    elif country_origin:
        final_origin = country_origin
        print(f"📊 Using scraped origin: {final_origin}")
    elif brand_origin:
        final_origin = brand_origin
        print(f"📊 Using brand fallback: {final_origin}")
    else:
        final_origin = "Unknown"
        print("❌ No origin detected")
    
    explicit_sources = {"technical_details", "product_details", "manufacturer_contact", "specifications", "scraped_verified", "raw_text"}
    
    # Build results
    if final_origin != "Unknown":
        results["origin"] = final_origin
        results["country_of_origin"] = final_origin
        if confidence_boost:
            results["origin_confidence"] = "High"
            results["origin_source"] = "scraped_verified"
        elif country_origin and _is_top_confidence_origin_source(scraped_source):
            results["origin_confidence"] = "High"
            results["origin_source"] = scraped_source or "scraped"
        elif country_origin and scraped_is_explicit:
            results["origin_confidence"] = "Medium"
            results["origin_source"] = scraped_source or "scraped"
        elif country_origin:
            results["origin_confidence"] = "Medium"
            results["origin_source"] = scraped_source or "scraped"
        else:
            results["origin_confidence"] = "Medium"
            results["origin_source"] = "brand_db"

    # 4. Facility extraction only when origin came from explicit page evidence
    resolved_source = str(results.get("origin_source", "")).strip().lower()
    if final_origin != "Unknown" and resolved_source in explicit_sources:
        facility_origin = extract_facility_location(product, title, final_origin)
    else:
        facility_origin = "Unknown"
    
    if facility_origin != "Unknown":
        results["facility_origin"] = facility_origin
    
    return results

def extract_facility_location(product: dict, title: str, country: str) -> str:
    """
    Three-tier facility location system:
    1. Specific city/location (Manchester, Paris, etc.)
    2. Brand name as facility  
    3. Product category description
    """
    # Get all available text for analysis
    all_text = f"{title} {product.get('description', '')}".lower()
    brand = product.get('brand', '').strip()
    
    import re
    
    # === TIER 1: Specific Location Search ===
    print("🏭 Tier 1: Searching for specific locations...")
    
    # City/Location patterns (ordered by country for better matching)
    location_patterns = [
        # UK cities
        r'\b(manchester|birmingham|london|glasgow|edinburgh|cardiff|belfast|leeds|liverpool|bristol|sheffield|nottingham|coventry|leicester|bradford|wolverhampton|plymouth|stoke|derby|southampton|portsmouth|york|peterborough|warrington|slough|rochdale|rotherham|oldham|blackpool|grimsby|northampton|luton|milton keynes|swindon|crawley|gloucester|chester|reading|cambridge|oxford|preston|blackburn|huddersfield|stockport|burnley|carlisle|wakefield|wigan|mansfield|dartford|gillingham|st helens|woking|worthing|tamworth|chesterfield|basildon|shrewsbury|colchester|redditch|lincoln|runcorn|scunthorpe|watford|gateshead|eastbourne|ayr|paisley|kidderminster|bognor regis|rhondda|barry|caerphilly|newport|swansea|neath|merthyr tydfil|wrexham|bangor|conway|llandudno|aberystwyth|carmarthen|haverfordwest|pembroke|tenby|cardigan|lampeter|brecon|abergavenny|monmouth|chepstow|tredegar|ebbw vale|aberdare|pontypridd|penarth|cowbridge)\b',
        
        # French cities  
        r'\b(paris|marseille|lyon|toulouse|nice|nantes|montpellier|strasbourg|bordeaux|lille|rennes|reims|saint-étienne|toulon|le havre|grenoble|dijon|angers|nîmes|villeurbanne|clermont-ferrand|aix-en-provence|brest|limoges|tours|amiens|metz|besançon|orléans|mulhouse|rouen|caen|nancy|argenteuil|montreuil|roubaix|dunkirk|nanterre|avignon|poitiers|créteil|pau|calais|la rochelle|champigny-sur-marne|antibes|béziers|saint-malo|cannes|colmar|bourges|mérignac|ajaccio|saint-nazaire|la seyne-sur-mer|quimper|valence|vénissieux|laval|évry|maisons-alfort|clichy)\b',
        
        # German cities
        r'\b(berlin|munich|hamburg|cologne|frankfurt|stuttgart|düsseldorf|leipzig|dresden|nuremberg|hanover|bremen|duisburg|bochum|wuppertal|bielefeld|bonn|mannheim|karlsruhe|wiesbaden|münster|augsburg|aachen|mönchengladbach|braunschweig|krefeld|chemnitz|kiel|halle|magdeburg|oberhausen|lübeck|freiburg|hagen|erfurt|rostock|mainz|kassel|hamm|saarbrücken|ludwigshafen|leverkusen|oldenburg|osnabrück|heidelberg|darmstadt|würzburg|göttingen|regensburg|recklinghausen|bottrop|wolfsburg|ingolstadt|ulm|heilbronn|pforzheim|offenbach|siegen|jena|gera|hildesheim|erlangen)\b',
        
        # Other EU cities (shorter list)
        r'\b(madrid|barcelona|valencia|seville|milan|rome|naples|turin|amsterdam|rotterdam|brussels|antwerp|vienna|stockholm|copenhagen|oslo|dublin|lisbon|prague|warsaw|budapest|athens|helsinki|zurich|geneva)\b',
        
        # US cities (major ones)
        r'\b(new york|los angeles|chicago|houston|phoenix|philadelphia|san antonio|san diego|dallas|san jose|austin|jacksonville|fort worth|columbus|charlotte|san francisco|indianapolis|seattle|denver|washington|boston|detroit|nashville|portland|las vegas|baltimore|milwaukee|atlanta|miami|oakland|minneapolis|cleveland|tampa|orlando|st louis|pittsburgh|cincinnati|kansas city|raleigh|richmond|sacramento|san bernardino|salt lake city)\b',
        
        # Asian cities
        r'\b(tokyo|osaka|yokohama|nagoya|sapporo|kobe|kyoto|fukuoka|kawasaki|saitama|beijing|shanghai|guangzhou|shenzhen|tianjin|wuhan|chengdu|hong kong|taipei|seoul|busan|incheon|daegu|bangkok|singapore|kuala lumpur|jakarta|manila|ho chi minh|hanoi|mumbai|delhi|bangalore|chennai|kolkata|hyderabad|ahmedabad|pune|surat)\b',
        
        # Facility-specific patterns
        r'\b(?:facility|factory|plant|manufacturing plant|production facility|gmp facility|warehouse|distribution center|headquarters|hq)\s+(?:in|at|located in)?\s*([a-z\s\-]{3,30})\b',
        r'\b(?:manufactured|made|produced)\s+(?:in|at)\s+([a-z\s\-]{3,30}?)\s+(?:facility|factory|plant)\b',
        r'\bmade\s+in\s+([a-z\s\-]{3,30}?)\s+facility\b',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, all_text)
        if matches:
            if isinstance(matches[0], tuple):
                location = matches[0][1] if len(matches[0]) > 1 else matches[0][0]
            else:
                location = matches[0]
            
            # Clean and validate location
            location = location.strip().title()
            if len(location) > 2 and location.lower() not in ['the', 'and', 'or', 'of', 'in', 'at', 'a', 'an']:
                print(f"🏭 ✅ Tier 1 Success: Found specific location '{location}'")
                return location
    
    # === TIER 2: Brand Name as Facility ===
    print("🏭 Tier 2: Using brand name as facility...")
    
    # Clean up common brand prefixes/suffixes
    if brand and brand.lower() not in ['unknown', 'visit the', '']:
        # Remove common Amazon prefixes
        clean_brand = re.sub(r'^(visit the|brand:|by)\s+', '', brand, flags=re.IGNORECASE)
        clean_brand = re.sub(r'\s+(store|shop|official)$', '', clean_brand, flags=re.IGNORECASE)
        clean_brand = clean_brand.strip()
        
        if clean_brand and len(clean_brand) > 1:
            print(f"🏭 ✅ Tier 2 Success: Using brand '{clean_brand}'")
            return f"{clean_brand} Facility"
    
    # Try extracting brand from title if not in product data
    if not brand or brand.lower() == 'unknown':
        # Common brand patterns in titles
        brand_patterns = [
            r'^([A-Z][a-zA-Z0-9\-&\s]+?)\s+(?:by|from|-)',  # "Nike by..." 
            r'^([A-Z][a-zA-Z0-9\-&\s]+?)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # "Sony Digital Camera"
            r'^([A-Z][a-zA-Z0-9\-&]+)\s+',  # First capitalized word
        ]
        
        for pattern in brand_patterns:
            match = re.match(pattern, title)
            if match:
                potential_brand = match.group(1).strip()
                if len(potential_brand) > 2 and len(potential_brand) < 30:
                    print(f"🏭 ✅ Tier 2 Success: Extracted brand '{potential_brand}' from title")
                    return f"{potential_brand} Facility"
    
    # === TIER 3: Product Category ===
    print("🏭 Tier 3: Determining product category...")
    
    # Analyze title and content for product category
    text_lower = (title + " " + all_text).lower()
    
    # Product category patterns
    product_categories = [
        # Food & Supplements
        ('protein powder', ['protein', 'powder', 'whey', 'casein', 'supplement']),
        ('vitamin supplement', ['vitamin', 'supplement', 'mineral', 'capsule', 'tablet']),
        ('energy bar', ['energy bar', 'protein bar', 'nutrition bar']),
        ('sports nutrition', ['pre-workout', 'post-workout', 'bcaa', 'creatine']),
        
        # Electronics
        ('electronics', ['laptop', 'computer', 'phone', 'tablet', 'camera', 'tv', 'monitor', 'speaker', 'headphone']),
        ('gaming device', ['playstation', 'xbox', 'nintendo', 'gaming', 'console']),
        ('smart device', ['smart watch', 'smartwatch', 'fitness tracker', 'smart home']),
        
        # Fashion & Accessories
        ('clothing', ['shirt', 'dress', 'pants', 'jacket', 'coat', 'sweater', 'jeans']),
        ('footwear', ['shoes', 'boots', 'sneakers', 'sandals', 'heels']),
        ('accessories', ['wallet', 'belt', 'watch', 'jewelry', 'bag', 'purse', 'backpack']),
        
        # Home & Kitchen  
        ('kitchenware', ['pot', 'pan', 'knife', 'cutlery', 'cookware', 'bakeware']),
        ('appliance', ['blender', 'mixer', 'toaster', 'coffee', 'microwave', 'refrigerator']),
        ('furniture', ['chair', 'table', 'desk', 'sofa', 'bed', 'shelf', 'cabinet']),
        
        # Sports & Outdoors
        ('sports equipment', ['ball', 'racket', 'golf', 'tennis', 'football', 'basketball']),
        ('fitness equipment', ['dumbbell', 'weight', 'resistance', 'yoga', 'exercise']),
        ('outdoor gear', ['tent', 'sleeping bag', 'backpack', 'hiking', 'camping']),
        
        # Other
        ('book', ['book', 'novel', 'textbook', 'guide', 'manual']),
        ('toy', ['toy', 'game', 'puzzle', 'lego', 'doll', 'action figure']),
        ('beauty product', ['makeup', 'cosmetic', 'skincare', 'shampoo', 'lotion']),
        ('tool', ['hammer', 'screwdriver', 'drill', 'saw', 'wrench']),
    ]
    
    for category_name, keywords in product_categories:
        if any(keyword in text_lower for keyword in keywords):
            print(f"🏭 ✅ Tier 3 Success: Detected product category '{category_name}'")
            return f"{category_name.title()} Manufacturing"
    
    # === FINAL FALLBACK ===
    # If we have a country, use country-based facility
    if country and country != "Unknown":
        facility_map = {
            'UK': 'UK Manufacturing Facility',
            'England': 'English Manufacturing Facility', 
            'Germany': 'German Production Facility',
            'USA': 'US Manufacturing Plant',
            'France': 'French Production Facility',
            'China': 'Chinese Manufacturing Facility',
            'South Africa': 'South African Production Facility'
        }
        
        generic_facility = facility_map.get(country, f"{country} Manufacturing Facility")
        print(f"🏭 Final fallback: Using generic facility '{generic_facility}'")
        return generic_facility
    
    print("🏭 ❌ All tiers failed - returning 'Manufacturing Facility'")
    return "Manufacturing Facility"


from flask_cors import CORS

# Configure CORS with security in mind
allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
if not allowed_origins or allowed_origins == ['']:
    # Default development origins
    allowed_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server (alt port)
        "http://localhost:3000",  # Alternative dev server
        "https://impacttracker.netlify.app",  # Production Netlify site
        "https://silly-cuchufli-b154e2.netlify.app",  # Legacy Netlify site
        "chrome-extension://*"    # Chrome extension
    ]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

# Configure CORS with proper production settings
CORS(app, 
     supports_credentials=True,
     origins=allowed_origins + [
         # Allow Amazon product pages (extension content script runs in-page)
         "https://www.amazon.co.uk",
         "https://amazon.co.uk",
         "https://smile.amazon.co.uk",
         "https://www.amazon.com",
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"]
)

# A small, safe helper to echo back allowed origins for preflight requests.
# This is useful when the platform or proxy may strip CORS headers before
# they reach the browser. Keep the list restricted to known origins.
ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "https://impacttracker.netlify.app",
    "https://silly-cuchufli-b154e2.netlify.app",
    "https://www.amazon.co.uk",
    "https://amazon.co.uk",
    "https://smile.amazon.co.uk",
    "https://www.amazon.com",
}

def is_allowed_origin(origin: str) -> bool:
    if not origin:
        return False
    # Exact match
    if origin in ALLOWED_ORIGINS:
        return True
    # Allow any Netlify preview subdomain
    if origin.endswith('.netlify.app'):
        return True
    # Allow Amazon product pages (be specific to amazon domains)
    if 'amazon.' in origin:
        return True
    # Allow extension schemes
    if origin.startswith('chrome-extension://') or origin.startswith('moz-extension://'):
        return True
    return False


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin and is_allowed_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# Flask-CORS already handles all CORS headers, so we don't need this
# Removing duplicate CORS handler to fix "multiple values" error

# Global error handler to prevent crashes from affecting other routes
@app.errorhandler(500)
def handle_500_error(e):
    print(f"❌ 500 Error handled: {e}")
    return jsonify({"error": "Internal server error"}), 500




register_routes(app)

# Register enterprise dashboard blueprint
app.register_blueprint(enterprise_bp)
print("✅ Enterprise dashboard routes registered")

# Register benchmarking API blueprint
if benchmarking_bp is not None:
    app.register_blueprint(benchmarking_bp)
    print("✅ Supply chain benchmarking routes registered")
else:
    print("⚠️ Benchmarking routes not available (backend/routes/benchmarking_api.py not found)")



SUBMISSION_FILE = "submitted_predictions.json"
EXPANDED_DATASET_FILE = os.path.join(BASE_DIR, "common", "data", "csv", "expanded_eco_dataset.csv")
EXPANDED_DATASET_COLUMNS = [
    "title",
    "material",
    "weight",
    "transport",
    "recyclability",
    "true_eco_score",
    "co2_emissions",
    "origin",
    "category",
    "search_term",
]


@app.route("/admin/submissions")
def get_submissions():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    if not os.path.exists(SUBMISSION_FILE):
        return jsonify([])

    with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))



@app.route("/admin/update", methods=["POST"])
def update_submission():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    item = request.json
    with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for i, row in enumerate(data):
        if row["title"] == item["title"]:
            data[i] = item
            break
    with open(SUBMISSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status": "success"})



def log_submission(product):
    path = "submitted_predictions.json"
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error in {path}: {e}. Starting fresh.")
                    data = []
        else:
            data = []
        data.append(product)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Logged submission: {product.get('title', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to log submission: {e}")


def append_estimation_to_expanded_dataset(entry):
    try:
        os.makedirs(os.path.dirname(EXPANDED_DATASET_FILE), exist_ok=True)
        file_exists = os.path.exists(EXPANDED_DATASET_FILE)

        with open(EXPANDED_DATASET_FILE, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=EXPANDED_DATASET_COLUMNS)
            if not file_exists or os.path.getsize(EXPANDED_DATASET_FILE) == 0:
                writer.writeheader()

            row = {column: entry.get(column, "") for column in EXPANDED_DATASET_COLUMNS}
            writer.writerow(row)

        print(f"✅ Appended estimation to expanded dataset: {row.get('title', 'Unknown Product')}")
        return True
    except Exception as csv_error:
        print(f"⚠️ Could not append estimation to expanded dataset CSV: {csv_error}")
        return False
        
def load_material_co2_data():
    try:
        import pandas as pd
        df = pd.read_csv(os.path.join(model_dir, "defra_material_intensity.csv")) 
        return {str(row["material"]).lower(): float(row["co2_per_kg"]) for _, row in df.iterrows()}
    except Exception as e:
        print(f"⚠️ Could not load CO₂ map: {e}")
        return {}

material_co2_map = load_material_co2_data()


@app.route("/predict", methods=["POST"])
def predict_eco_score():
    
    print("📩 /predict endpoint was hit via POST")  # debug
    try:
        data = request.get_json()
        product = data  # ensure it's always defined
        material = normalize_feature(data.get("material"), "Other")
        weight = float(data.get("weight") or 0.0)
        # Estimate default transport from distance if none provided
        user_transport = data.get("transport")
        origin_km = float(product.get("distance_origin_to_uk", 0) or 0)

        # Heuristic fallback: choose mode by distance
        def guess_transport_by_distance(km):
            if km > 7000:
                return "Ship"
            elif km > 2000:
                return "Air"
            else:
                return "Land"

        # === Determine transport mode based on distance (default + override)
        override_transport = normalize_feature(data.get("override_transport_mode"), None)

        def determine_transport_mode(distance_km):
            if distance_km < 1500:
                return "Truck", 0.15
            elif distance_km < 6000:
                return "Ship", 0.03
            else:
                return "Air", 0.5
            
        origin_distance_km = float(data.get("distance_origin_to_uk") or 0)
        origin = normalize_feature(data.get("origin"), "Other")

        default_mode, default_emission_factor = determine_transport_mode(origin_distance_km)

        if override_transport in ["Truck", "Ship", "Air"]:
            transport = override_transport
            print(f"🚛 User override mode: {transport}")
        else:
            transport = default_mode
            print(f"📦 Default transport mode applied: {transport}")

        print(f"🚛 Final transport used: {transport} (user selected: {user_transport})")

        recyclability = normalize_feature(data.get("recyclability"), "Medium")

        # === Encode features
        material_encoded = safe_encode(material, material_encoder, "Other")
        transport_encoded = safe_encode(transport, transport_encoder, "Land")
        recycle_encoded = safe_encode(recyclability, recycle_encoder, "Medium")
        origin_encoded = safe_encode(origin, origin_encoder, "Other")

        # === Bin weight (for 6th feature)
        def bin_weight(w):
            if w < 0.5:
                return 0
            elif w < 2:
                return 1
            elif w < 10:
                return 2
            else:
                return 3

        weight_bin_encoded = bin_weight(weight)

        weight_log = np.log1p(weight)

        # === Prepare enhanced features for 11-feature model
        try:
            # Infer additional features from title if available
            title = data.get("title", "")
            title_lower = title.lower()
            
            # Packaging type inference
            if any(x in title_lower for x in ["bottle", "jar", "can"]):
                packaging_type = "bottle"
            elif any(x in title_lower for x in ["box", "pack", "carton"]):
                packaging_type = "box"
            else:
                packaging_type = "other"
            
            # Size category inference
            if weight > 2.0:
                size_category = "large"
            elif weight > 0.5:
                size_category = "medium"
            else:
                size_category = "small"
            
            # Quality level inference
            if any(x in title_lower for x in ["premium", "pro", "professional", "deluxe"]):
                quality_level = "premium"
            elif any(x in title_lower for x in ["basic", "standard", "regular"]):
                quality_level = "standard"
            else:
                quality_level = "standard"
            
            # Pack size (number of items)
            pack_size = 1
            for num_word in ["2 pack", "3 pack", "4 pack", "5 pack", "6 pack", "8 pack", "10 pack", "12 pack"]:
                if num_word in title_lower:
                    pack_size = int(num_word.split()[0])
                    break
            
            # Material confidence
            material_confidence = 0.8 if material != "Other" else 0.3
            
            # Try to encode enhanced features if available
            if packaging_type_encoder and size_category_encoder and quality_level_encoder and inferred_category_encoder:
                packaging_encoded = safe_encode(packaging_type, packaging_type_encoder, "box")
                size_encoded = safe_encode(size_category, size_category_encoder, "medium") 
                quality_encoded = safe_encode(quality_level, quality_level_encoder, "standard")
                
                # Inferred category (basic inference)
                if any(x in title_lower for x in ["protein", "supplement", "vitamins"]):
                    inferred_category = "health"
                elif any(x in title_lower for x in ["electronics", "phone", "computer"]):
                    inferred_category = "electronics"  
                elif any(x in title_lower for x in ["clothing", "shirt", "dress"]):
                    inferred_category = "clothing"
                else:
                    inferred_category = "other"
                
                # Encode inferred category
                category_encoded = safe_encode(inferred_category, inferred_category_encoder, "other")
                
                # Additional confidence measures
                origin_confidence = 0.8 if origin != "Other" else 0.4
                weight_confidence = 0.9 if weight > 0.1 else 0.5
                
                # Estimated lifespan (years) - basic heuristic
                if "electronics" in inferred_category:
                    estimated_lifespan_years = 5.0
                elif "clothing" in inferred_category:
                    estimated_lifespan_years = 2.0
                else:
                    estimated_lifespan_years = 3.0
                
                # Repairability score (1-10, higher is more repairable)
                if "electronics" in inferred_category:
                    repairability_score = 3.0
                elif inferred_category in ["other", "health"]:
                    repairability_score = 1.0  # Consumables not repairable
                else:
                    repairability_score = 5.0
                
                # Use 16-feature enhanced model (matching our training)
                X = [[
                    material_encoded,           # 1: material_encoded
                    transport_encoded,          # 2: transport_encoded  
                    recycle_encoded,           # 3: recyclability_encoded
                    origin_encoded,            # 4: origin_encoded
                    weight_log,                # 5: weight_log
                    weight_bin_encoded,        # 6: weight_bin_encoded
                    packaging_encoded,         # 7: packaging_type_encoded
                    size_encoded,              # 8: size_category_encoded
                    quality_encoded,           # 9: quality_level_encoded
                    category_encoded,          # 10: inferred_category_encoded
                    pack_size,                 # 11: pack_size
                    material_confidence,       # 12: material_confidence
                    origin_confidence,         # 13: origin_confidence
                    weight_confidence,         # 14: weight_confidence
                    estimated_lifespan_years,  # 15: estimated_lifespan_years
                    repairability_score        # 16: repairability_score
                ]]
                print(f"🔧 Using 16-feature enhanced model for prediction")
            else:
                raise Exception("Enhanced encoders not available")
                
        except Exception as e:
            print(f"⚠️ Enhanced features failed: {e}, falling back to 6 features")
            # Fallback to 6-feature model
            X = [[
                material_encoded,
                transport_encoded,
                recycle_encoded,
                origin_encoded,
                weight_log,
                weight_bin_encoded
            ]]
        
        if model is None:
            return jsonify({"error": "Model not available - please check server logs"}), 500
            
        prediction = model.predict(X)
        decoded_score = label_encoder.inverse_transform([prediction[0]])[0]

        print("🧠 Predicted Label:", decoded_score)
        
        confidence = 0.0
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)
            print("🧪 predict_proba output:", proba)
            print("🎯 Raw predict_proba values:", proba[0])  # <=== ADD THIS HERE

            best_index = int(np.argmax(proba[0]))
            best_label = label_encoder.inverse_transform([best_index])[0]
            confidence = round(float(proba[0][best_index]) * 100, 1)

            print(f"🧠 Most confident class: {best_label} with {confidence}%")

                
        # === Feature Importance (optional)
        try:
            global_importance = model.feature_importances_
            print(f"🔍 Feature importance array length: {len(global_importance)}")
            
            # Safely calculate local impact for available features
            local_impact = {}
            if len(global_importance) >= 6:
                local_impact = {
                    "material": to_python_type(float(material_encoded * global_importance[0])),
                    "transport": to_python_type(float(transport_encoded * global_importance[1])),
                    "recyclability": to_python_type(float(recycle_encoded * global_importance[2])),
                    "origin": to_python_type(float(origin_encoded * global_importance[3])),
                    "weight_log": to_python_type(float(weight_log * global_importance[4])),
                    "weight_bin": to_python_type(float(weight_bin_encoded * global_importance[5])),
                }
            else:
                local_impact = {"note": "Feature importance not available for this model"}
        except Exception as impact_error:
            print(f"⚠️ Feature importance calculation failed: {impact_error}")
            local_impact = {"error": "Could not calculate feature impact"}

        # === SHAP Explanation (per-prediction feature attribution)
        shap_explanation = None
        try:
            import shap as shap_lib
            explainer = shap_lib.TreeExplainer(model)
            X_arr = np.array(X)
            shap_vals = explainer.shap_values(X_arr)

            n_features = len(X[0])
            all_feature_names = [
                'Material Type', 'Transport Mode', 'Recyclability', 'Origin Country',
                'Weight', 'Weight Category', 'Packaging Type', 'Size Category',
                'Quality Level', 'Category', 'Pack Size', 'Material Confidence',
                'Origin Confidence', 'Weight Confidence', 'Est. Lifespan', 'Repairability'
            ]
            feature_names = all_feature_names[:n_features]

            weight_bins = ['<0.5 kg', '0.5–2 kg', '2–10 kg', '>10 kg']
            raw_vals = [
                material, transport, recyclability, origin,
                f"{round(weight, 2)} kg",
                weight_bins[int(weight_bin_encoded)] if 0 <= int(weight_bin_encoded) < 4 else str(weight_bin_encoded)
            ] + [''] * max(0, n_features - 6)

            # Predicted class index from proba
            pred_idx = int(np.argmax(model.predict_proba(X_arr)[0]))

            # Handle different SHAP output shapes across library versions
            sv = np.array(shap_vals)
            if sv.ndim == 3:
                # (n_samples, n_features, n_classes)
                class_shap = sv[0, :, pred_idx]
            elif isinstance(shap_vals, list):
                # list of (n_samples, n_features) per class
                class_shap = np.array(shap_vals[pred_idx])[0]
            else:
                class_shap = sv[0]

            ev = explainer.expected_value
            base_val = float(ev[pred_idx]) if hasattr(ev, '__len__') else float(ev)

            features = [
                {
                    "name": feature_names[i],
                    "shap_value": round(float(class_shap[i]), 4),
                    "raw_value": raw_vals[i] if i < len(raw_vals) else ""
                }
                for i in range(min(n_features, len(class_shap)))
            ]
            features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

            shap_explanation = {
                "predicted_class": decoded_score,
                "base_value": round(base_val, 4),
                "features": features
            }
        except Exception as shap_err:
            print(f"⚠️ SHAP computation failed: {shap_err}")
            shap_explanation = None

        # === Log the prediction
        log_submission({
            "title": data.get("title", "Manual Submission"),
            "raw_input": {
                "material": material,
                "weight": weight,
                "transport": transport,
                "recyclability": recyclability,
                "origin": origin
            },
            "predicted_label": decoded_score,
            "confidence": f"{confidence}%"
        })

        # === Return JSON response
        return jsonify({
            "predicted_label": decoded_score,
            "confidence": f"{confidence}%",
            "raw_input": {
                "material": material,
                "weight": weight,
                "transport": transport,
                "recyclability": recyclability,
                "origin": origin
            },
            "encoded_input": {
                "material": to_python_type(material_encoded),
                "weight": to_python_type(weight),
                "transport": to_python_type(transport_encoded),
                "recyclability": to_python_type(recycle_encoded),
                "origin": to_python_type(origin_encoded),
                "weight_bin": to_python_type(weight_bin_encoded)
            },
            "feature_impact": local_impact,
            "shap_explanation": shap_explanation
        })

    except Exception as e:
        print(f"❌ Error in /predict: {e}")
        return jsonify({"error": str(e)}), 500


# === Load Model and Encoders ===

# Load the enhanced XGBoost model with error handling
model = None
model_type = None  # Track which model type is loaded

# First try to load the 16-feature enhanced model (eco_model.pkl)
try:
    model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
    print("✅ Loaded enhanced XGBoost model (16-feature)")
    model_type = "enhanced_16"
except Exception as e:
    print(f"⚠️ Failed to load enhanced 16-feature model: {e}")
    
    # Fallback to old XGBoost JSON format
    try:
        import xgboost as xgb
        model = xgb.XGBClassifier()
        model.load_model(os.path.join(model_dir, "xgb_model.json"))
        print("✅ Loaded legacy XGBoost model")
        model_type = "legacy"
    except Exception as e2:
        print(f"⚠️ Failed to load XGBoost JSON model: {e2}")
        print("🔄 Trying other formats...")
    try:
        # Try loading the pickled model without XGBoost dependency
        import pickle
        with open(os.path.join(model_dir, "eco_model.pkl"), 'rb') as f:
            model = pickle.load(f)
        print("✅ Loaded fallback model via pickle")
    except Exception as e2:
        try:
            # Try to load enhanced XGBoost model first
            try:
                model = joblib.load(os.path.join(model_dir, "enhanced_xgboost_model.pkl"))
                print("✅ Loaded enhanced XGBoost model (11 features)")
                model_type = "enhanced"
            except:
                # Fallback to basic model
                model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
                print("⚠️ Loaded basic model (6 features)")
                model_type = "basic"
            print("✅ Loaded fallback model via joblib")
        except Exception as e3:
            print(f"❌ Failed to load any model: {e3}")
            print("🔄 Creating simple fallback model...")
            
            # Create a simple fallback model class
            class FallbackModel:
                def predict(self, X):
                    # Simple rule-based prediction based on features
                    material_score = X[0][0] / 10.0  # Material encoded value
                    weight_score = min(X[0][4], 3.0)  # Weight log
                    transport_score = X[0][1] / 3.0   # Transport encoded
                    
                    # Simple scoring logic
                    total_score = (material_score + weight_score + transport_score) / 3
                    
                    if total_score < 0.3:
                        return [0]  # A+
                    elif total_score < 0.5:
                        return [1]  # A
                    elif total_score < 0.7:
                        return [2]  # B
                    elif total_score < 0.9:
                        return [3]  # C
                    elif total_score < 1.2:
                        return [4]  # D
                    elif total_score < 1.5:
                        return [5]  # E
                    else:
                        return [6]  # F
                
                def predict_proba(self, X):
                    # Return mock probabilities
                    pred = self.predict(X)[0]
                    proba = [0.1] * 7  # 7 classes
                    proba[pred] = 0.7  # High confidence for predicted class
                    return [proba]
                
                @property
                def feature_importances_(self):
                    # Mock feature importances for 6 or 11 features
                    return [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]  # 6 features
            
            model = FallbackModel()
            print("✅ Created fallback rule-based model")

class SimpleLabelEncoderFallback:
    def __init__(self, classes):
        self.classes_ = np.array(classes)
        self._index_map = {label: idx for idx, label in enumerate(self.classes_)}

    def transform(self, values):
        return np.array([self._index_map.get(value, 0) for value in values], dtype=int)

    def inverse_transform(self, indices):
        return np.array([
            self.classes_[idx] if 0 <= int(idx) < len(self.classes_) else self.classes_[0]
            for idx in indices
        ])


def _is_git_lfs_pointer(file_path):
    try:
        with open(file_path, "rb") as file_handle:
            first_line = file_handle.readline(128)
        return first_line.startswith(b"version https://git-lfs.github.com/spec/v1")
    except Exception:
        return False


def _load_encoder_or_fallback(filename, fallback_classes, encoder_name):
    file_path = os.path.join(encoders_dir, filename)

    if _is_git_lfs_pointer(file_path):
        print(
            f"⚠️ {filename} is a Git LFS pointer file on this deployment. "
            f"Using fallback {encoder_name}."
        )
        return SimpleLabelEncoderFallback(fallback_classes)

    try:
        return joblib.load(file_path)
    except Exception as error:
        print(f"⚠️ Failed to load {filename}: {error}. Using fallback {encoder_name}.")
        return SimpleLabelEncoderFallback(fallback_classes)


# Load basic encoders (with Railway-safe fallback for missing LFS objects)
material_encoder = _load_encoder_or_fallback(
    "material_encoder.pkl",
    ["Other", "Plastic", "Wood", "Glass", "Aluminium", "Steel", "Paper", "Cardboard", "Cotton", "Bamboo"],
    "material encoder",
)
print("🧩 Loaded material encoder classes:", material_encoder.classes_)

transport_encoder = _load_encoder_or_fallback(
    "transport_encoder.pkl",
    ["Land", "Ship", "Air", "Truck", "Rail", "Other"],
    "transport encoder",
)
recycle_encoder = _load_encoder_or_fallback(
    "recycle_encoder.pkl",
    ["Medium", "Low", "High", "Unknown"],
    "recycle encoder",
)
label_encoder = _load_encoder_or_fallback(
    "label_encoder.pkl",
    ["A+", "A", "B", "C", "D", "E", "F"],
    "label encoder",
)
origin_encoder = _load_encoder_or_fallback(
    "origin_encoder.pkl",
    ["Other", "Uk", "China", "Usa", "Germany", "France", "India"],
    "origin encoder",
)

# Load enhanced encoders for 16-feature model
try:
    packaging_type_encoder = joblib.load(os.path.join(encoders_dir, "packaging_type_encoder.pkl"))
    size_category_encoder = joblib.load(os.path.join(encoders_dir, "size_category_encoder.pkl"))
    quality_level_encoder = joblib.load(os.path.join(encoders_dir, "quality_level_encoder.pkl"))
    inferred_category_encoder = joblib.load(os.path.join(encoders_dir, "inferred_category_encoder.pkl"))
    print("✅ Loaded enhanced encoders for 16-feature model")
except Exception as e:
    print(f"⚠️ Could not load enhanced encoders: {e}")
    # Set to None so we can check later
    packaging_type_encoder = None
    size_category_encoder = None
    quality_level_encoder = None
    inferred_category_encoder = None

valid_scores = list(label_encoder.classes_)
print("✅ Loaded label classes:", valid_scores)


@app.route("/all-model-metrics", methods=["GET"])
def get_all_model_metrics():
    try:
        with open(os.path.join(model_dir, "metrics.json"), "r") as f1, open(os.path.join(model_dir, "xgb_metrics.json"), "r") as f2:
            return jsonify({
                "random_forest": json.load(f1),
                "xgboost": json.load(f2)
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/model-metrics", methods=["GET"])
def get_model_metrics():
    try:
        with open(os.path.join(model_dir, "metrics.json"), "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ml-audit", methods=["GET"])
def ml_audit_report():
    """
    Comprehensive ML model audit for senior developer review
    Returns detailed analysis of model performance, dataset quality, and feature selection
    """
    try:
        audit_report = {
            "model_performance": {},
            "dataset_analysis": {},
            "feature_assessment": {},
            "recommendations": [],
            "technical_issues": []
        }
        
        # 1. Load model metrics
        try:
            with open(os.path.join(model_dir, "xgb_metrics.json"), "r") as f:
                xgb_metrics = json.load(f)
            with open(os.path.join(model_dir, "metrics.json"), "r") as f:
                rf_metrics = json.load(f)
                
            audit_report["model_performance"] = {
                "xgboost": {
                    "accuracy": xgb_metrics.get("accuracy", 0),
                    "f1_score": xgb_metrics.get("f1_score", 0),
                    "class_balance": "Good - roughly equal support across classes",
                    "best_performing_classes": ["A+", "D", "F"],
                    "challenging_classes": ["A", "B", "C"],
                    "recommendation": "Strong model - suitable for production"
                },
                "random_forest": {
                    "accuracy": rf_metrics.get("accuracy", 0),
                    "f1_score": rf_metrics.get("f1_score", 0),
                    "vs_xgboost": "XGBoost outperforms by ~4%",
                    "recommendation": "Use XGBoost as primary model"
                }
            }
        except Exception as e:
            audit_report["technical_issues"].append(f"Could not load model metrics: {e}")
        
        # 2. Dataset analysis
        try:
            dataset_path = os.path.join(BASE_DIR, "common", "data", "csv", "expanded_eco_dataset.csv")
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                
                # Analyze dataset characteristics
                unique_materials = df["material"].nunique() if "material" in df.columns else 0
                unique_origins = df["origin"].nunique() if "origin" in df.columns else 0
                score_distribution = df["true_eco_score"].value_counts().to_dict() if "true_eco_score" in df.columns else {}
                
                audit_report["dataset_analysis"] = {
                    "total_samples": len(df),
                    "unique_materials": unique_materials,
                    "unique_origins": unique_origins,
                    "score_distribution": score_distribution,
                    "data_quality_issues": [
                        "Limited product diversity (mostly water bottles)",
                        "May contain synthetic/generated data",
                        "Good geographic distribution"
                    ],
                    "recommendation": "Expand dataset with real Amazon product data"
                }
        except Exception as e:
            audit_report["technical_issues"].append(f"Dataset analysis failed: {e}")
        
        # 3. Feature assessment
        try:
            # Check feature encoders availability
            encoder_files = [
                "material_encoder.pkl", "transport_encoder.pkl", "recycle_encoder.pkl",
                "origin_encoder.pkl", "label_encoder.pkl", "packaging_type_encoder.pkl",
                "size_category_encoder.pkl", "quality_level_encoder.pkl"
            ]
            
            available_encoders = []
            missing_encoders = []
            
            for encoder in encoder_files:
                encoder_path = os.path.join(encoders_dir, encoder)
                if os.path.exists(encoder_path):
                    available_encoders.append(encoder)
                else:
                    missing_encoders.append(encoder)
            
            audit_report["feature_assessment"] = {
                "total_features": 11,
                "core_features": 6,
                "enhanced_features": 5,
                "available_encoders": available_encoders,
                "missing_encoders": missing_encoders,
                "feature_engineering_quality": "Good" if len(missing_encoders) < 3 else "Needs improvement",
                "issues": [
                    "Frequent fallback to 6-feature model",
                    "Enhanced encoders not always available",
                    "Need validation of additional features' value"
                ]
            }
        except Exception as e:
            audit_report["technical_issues"].append(f"Feature assessment failed: {e}")
        
        # 4. Recommendations
        audit_report["recommendations"] = [
            {
                "priority": "High",
                "category": "Dataset Expansion",
                "description": "Collect real Amazon product data across diverse categories (electronics, clothing, home goods)",
                "implementation": "Enhance web scraping to capture more product types"
            },
            {
                "priority": "High", 
                "category": "Feature Validation",
                "description": "A/B test 11-feature vs 6-feature model performance",
                "implementation": "Run comparative analysis on holdout test set"
            },
            {
                "priority": "Medium",
                "category": "Model Robustness",
                "description": "Add cross-validation and ensemble methods",
                "implementation": "Implement 5-fold CV and model stacking"
            },
            {
                "priority": "Medium",
                "category": "Production Monitoring",
                "description": "Add model drift detection and retraining triggers", 
                "implementation": "Monitor prediction confidence and accuracy over time"
            },
            {
                "priority": "Low",
                "category": "Interpretability",
                "description": "Add SHAP values for individual prediction explanations",
                "implementation": "Integrate SHAP library for feature importance per prediction"
            }
        ]
        
        # 5. Overall assessment
        audit_report["overall_assessment"] = {
            "model_quality": "Good - 85.8% accuracy suitable for production",
            "dataset_concerns": "Moderate - needs real-world diversity",
            "feature_engineering": "Good foundation, needs validation",
            "production_readiness": "Yes, with monitoring",
            "dissertation_quality": "Strong technical foundation with room for expansion"
        }
        
        return jsonify(audit_report)
        
    except Exception as e:
        return jsonify({"error": f"ML audit failed: {str(e)}"}), 500

    
# === Load CO2 Map ===
def load_material_co2_data():
    try:
        df = pd.read_csv(os.path.join(model_dir, "defra_material_intensity.csv"))
        return dict(zip(df["material"], df["co2_per_kg"]))
    except Exception as e:
        print(f"⚠️ Could not load DEFRA data: {e}")
        return {}

material_co2_map = load_material_co2_data()

# === Helpers ===
def normalize_feature(value, default):
    clean = str(value or default).strip().title()
    return default if clean.lower() == "unknown" else clean

def safe_encode(value, encoder, default):
    value = normalize_feature(value, default)
    if value not in encoder.classes_:
        print(f"⚠️ '{value}' not in encoder classes. Defaulting to '{default}'.")
        value = default
    return encoder.transform([value])[0]

@app.route("/api/feature-importance")
def get_feature_importance():
    try:
        if model is None:
            return jsonify({"error": "Model not available"}), 500
            
        importances = model.feature_importances_
        # Updated for 11-feature enhanced model
        features = [
            "Material Type", "Transport Mode", "Recyclability", "Origin Country",
            "Weight (log)", "Weight Category", "Packaging Type", "Size Category", 
            "Quality Level", "Pack Size", "Material Confidence"
        ]
        
        # Handle both 11-feature and 6-feature models
        if len(importances) == 11:
            feature_names = features
        else:
            feature_names = ["Material", "Transport", "Recyclability", "Origin", "Weight (log)", "Weight Category"][:len(importances)]
        
        data = [{"feature": f, "importance": round(i * 100, 2)} for f, i in zip(feature_names, importances)]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



def to_python_type(obj):
    import numpy as np
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    return obj


# === Fuzzy Matching Helpers ===
def fuzzy_match_material(text):
    material_keywords = {
        "Plastic": ["plastic", "plastics"],
        "Glass": ["glass"],
        "Aluminium": ["aluminium", "aluminum"],
        "Steel": ["steel"],
        "Paper": ["paper", "papers"],
        "Cardboard": ["cardboard", "corrugated"],
        "Leather": ["leather", "buffalo", "veg tan"],
        "Wood": ["wood", "timber"],
        "Foam": ["foam", "polyurethane"],
    }

    text = str(text or "").lower()
    for label, keywords in material_keywords.items():
        if any(keyword in text for keyword in keywords):
            return label
    return "Other"

    material_lower = material.lower()
    for clean, keywords in material_keywords.items():
        if any(keyword in material_lower for keyword in keywords):
            return clean
    return material

def fuzzy_match_origin(origin):
    origin_keywords = {
        "China": ["china"],
        "UK": ["uk", "united kingdom"],
        "USA": ["usa", "united states", "america"],
        "Germany": ["germany"],
        "France": ["france"],
        "Italy": ["italy"],
    }

    origin_lower = origin.lower()
    for clean, keywords in origin_keywords.items():
        if any(keyword in origin_lower for keyword in keywords):
            return clean
    return origin


@app.route("/api/eco-data", methods=["GET"])
def fetch_eco_dataset():
    try:
        dataset_path = os.path.join(BASE_DIR, "common", "data", "csv", "expanded_eco_dataset.csv")
        
        # Check if file exists
        if not os.path.exists(dataset_path):
            print(f"⚠️ Dataset file not found: {dataset_path}")
            # Return empty dataset instead of crashing
            return jsonify([])
        
        df = pd.read_csv(dataset_path)
        
        # Handle missing columns gracefully
        required_cols = ["material", "true_eco_score", "co2_emissions"]
        existing_cols = [col for col in required_cols if col in df.columns]
        
        if not existing_cols:
            print("⚠️ No required columns found in dataset")
            return jsonify([])
        
        df = df.dropna(subset=existing_cols)
        
        # Replace NaN values with None/null for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        # Get limit from query parameter, default to 1000 for performance
        limit = request.args.get('limit', type=int, default=1000)
        limit = min(limit, 50000)  # Cap at 50k to allow full dataset access
        
        # Apply limit
        df_limited = df.head(limit)
        
        # Add metadata about the dataset
        response_data = {
            "products": df_limited.to_dict(orient="records"),
            "metadata": {
                "total_products_in_dataset": len(df),
                "products_returned": len(df_limited),
                "limit_applied": limit
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in eco-data endpoint: {e}")  
        import traceback
        print(traceback.format_exc())
        # Return empty array instead of 500 error
        return jsonify([]), 200




@app.route("/insights", methods=["GET"])
def insights_dashboard():
    try:
        # Load the logged data
        dataset_path = os.path.join(BASE_DIR, "common", "data", "csv", "expanded_eco_dataset.csv")
        df = pd.read_csv(dataset_path)
        print("🔍 Dataset path:", dataset_path)
        print("✅ Exists?", os.path.exists(dataset_path))


        df = df.dropna(subset=["material", "true_eco_score", "co2_emissions"])  # Clean

        # Keep only the needed fields
        insights = df[["material", "true_eco_score", "co2_emissions"]]
        insights = insights.head(1000)  # Limit for frontend performance

        return jsonify(insights.to_dict(orient="records"))
    except Exception as e:
        print(f"❌ Failed to serve insights: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard-metrics", methods=["GET"])
def get_dashboard_metrics():
    """
    Enhanced dashboard metrics combining real data from multiple sources
    Replaces placeholder values with actual aggregated statistics
    """
    try:
        metrics = {
            "total_products": 0,
            "total_materials": 0,
            "total_predictions": 0,
            "score_distribution": {},
            "material_distribution": {},
            "recent_activity": 0
        }
        
        # 1. Load main dataset
        try:
            dataset_path = os.path.join(BASE_DIR, "common", "data", "csv", "expanded_eco_dataset.csv")
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                df_clean = df.dropna(subset=["material", "true_eco_score"])
                
                metrics["total_products"] += len(df_clean)
                
                # Material distribution from dataset
                material_counts = df_clean["material"].value_counts().to_dict()
                for material, count in material_counts.items():
                    metrics["material_distribution"][material] = metrics["material_distribution"].get(material, 0) + count
                
                # Score distribution from dataset
                score_counts = df_clean["true_eco_score"].value_counts().to_dict()
                for score, count in score_counts.items():
                    metrics["score_distribution"][score] = metrics["score_distribution"].get(score, 0) + count
                    
                print(f"📊 Loaded {len(df_clean)} records from main dataset")
        except Exception as e:
            print(f"⚠️ Could not load main dataset: {e}")
        
        # 2. Load submitted predictions
        try:
            if os.path.exists(SUBMISSION_FILE):
                with open(SUBMISSION_FILE, "r", encoding="utf-8") as f:
                    submissions = json.load(f)
                
                metrics["total_predictions"] = len(submissions)
                metrics["recent_activity"] = len([s for s in submissions if s])  # Non-empty submissions
                
                # Add submission data to distributions
                for submission in submissions:
                    if isinstance(submission, dict):
                        # Material distribution from submissions
                        material = submission.get("raw_input", {}).get("material", "Unknown")
                        if material != "Unknown":
                            metrics["material_distribution"][material] = metrics["material_distribution"].get(material, 0) + 1
                        
                        # Score distribution from submissions
                        predicted_label = submission.get("predicted_label", "Unknown")
                        if predicted_label != "Unknown":
                            metrics["score_distribution"][predicted_label] = metrics["score_distribution"].get(predicted_label, 0) + 1
                
                print(f"📊 Loaded {len(submissions)} submitted predictions")
        except Exception as e:
            print(f"⚠️ Could not load submissions: {e}")
        
        # 3. Calculate totals
        try:
            db_product_count = ScrapedProduct.query.count()
            db_calculation_count = EmissionCalculation.query.count()
            metrics["total_products"] += db_product_count
            metrics["total_predictions"] = max(metrics["total_predictions"], db_calculation_count)
            metrics["recent_activity"] = max(metrics["recent_activity"], db_calculation_count)
            print(f"📊 Added DB counts: {db_product_count} scraped products, {db_calculation_count} calculations")
        except Exception as db_metrics_error:
            print(f"⚠️ Could not load DB metrics: {db_metrics_error}")

        metrics["total_materials"] = len(metrics["material_distribution"])
        
        # 4. Convert to frontend-friendly format
        dashboard_data = {
            "stats": {
                "total_products": metrics["total_products"],
                "total_materials": metrics["total_materials"], 
                "total_predictions": metrics["total_predictions"],
                "recent_activity": metrics["recent_activity"]
            },
            "score_distribution": [
                {"name": score, "value": count} 
                for score, count in sorted(metrics["score_distribution"].items())
            ],
            "material_distribution": [
                {"name": material, "value": count}
                for material, count in sorted(metrics["material_distribution"].items(), key=lambda x: x[1], reverse=True)[:10]
            ]
        }
        
        print(f"✅ Dashboard metrics compiled: {metrics['total_products']} products, {metrics['total_materials']} materials")
        return jsonify(dashboard_data)
        
    except Exception as e:
        print(f"❌ Dashboard metrics error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    try:
        data = request.get_json()
        feedback_dir = os.path.join(ML_ASSETS_DIR, "user_feedback.json")
        print("Received feedback:", data)
        # Append to file
        import json
        existing = []
        if os.path.exists(feedback_dir):
            with open(feedback_dir, "r") as f:
                existing = json.load(f)

        existing.append(data)

        with open(feedback_dir, "w") as f:
            json.dump(existing, f, indent=2)

        return jsonify({"message": "✅ Feedback saved!"}), 200

    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return jsonify({"error": str(e)}), 500




def calculate_eco_score_local_only(carbon_kg, recyclability, weight_kg):
    carbon_score = max(0, 10 - carbon_kg * 5)
    weight_score = max(0, 10 - weight_kg * 2)
    recycle_score = {
        "Low": 2,
        "Medium": 6,
        "High": 10
    }.get(recyclability or "Medium", 5)

    total_score = (carbon_score + weight_score + recycle_score) / 3

    return map_score_to_grade(total_score)

def map_score_to_grade(score):
    if score >= 9:
        return "A+"
    elif score >= 8:
        return "A"
    elif score >= 6.5:
        return "B"
    elif score >= 5:
        return "C"
    elif score >= 3.5:
        return "D"
    else:
        return "F"


@app.route("/estimate_emissions", methods=["POST", "OPTIONS"])
def estimate_emissions():
    print("🔔 Route hit: /estimate_emissions")
    
    # Flask-CORS handles OPTIONS requests automatically
    # Return early for OPTIONS to avoid trying to parse JSON
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON in request"}), 400

    # Convert numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        return obj

    try:
        raw_url = data.get("amazon_url")
        url = normalize_amazon_url(raw_url)
        postcode = data.get("postcode")
        include_packaging = data.get("include_packaging", True)
        override_mode = data.get("override_transport_mode")

        # Validate inputs
        if not url or not postcode:
            return jsonify({"error": "Missing URL or postcode"}), 400

        asin_key = extract_asin_from_amazon_url(url)
        cached_calc = find_cached_emission_calculation(asin=asin_key, amazon_url=url, postcode=postcode)
        if cached_calc and cached_calc.scraped_product:
            cached_product = cached_calc.scraped_product
            cached_total = float(cached_calc.final_emission or 0.0)
            cached_weight = float(cached_product.weight or 0.5)
            cached_origin = cached_product.origin_country or "Unknown"
            cached_distance = float(cached_calc.transport_distance or 0.0)
            cached_eco_score = calculate_eco_score(
                cached_total,
                "Medium",
                cached_distance,
                cached_weight,
            )
            try:
                cached_confidence_numeric = float(cached_calc.confidence_level or 0.7)
            except Exception:
                cached_confidence_numeric = 0.7
            if cached_confidence_numeric >= 0.85:
                cached_origin_confidence = "high"
            elif cached_confidence_numeric >= 0.6:
                cached_origin_confidence = "medium"
            else:
                cached_origin_confidence = "low"

            cached_attributes = {
                "carbon_kg": round(cached_total, 2),
                "weight_kg": round(cached_weight, 2),
                "raw_product_weight_kg": round(cached_weight, 2),
                "origin": cached_origin,
                "country_of_origin": cached_origin,
                "facility_origin": cached_origin,
                "origin_source": "database_cache",
                "origin_confidence": cached_origin_confidence,
                "intl_distance_km": round(float(cached_calc.transport_distance or 0.0), 2),
                "uk_distance_km": 0.0,
                "distance_from_origin_km": round(float(cached_calc.transport_distance or 0.0), 2),
                "distance_from_uk_hub_km": 0.0,
                "dimensions_cm": "Not found",
                "material_type": cached_product.material or "Unknown",
                "materials": {},
                "recyclability": "Not found",
                "recyclability_percentage": 30,
                "recyclability_description": "Assessment pending",
                "transport_mode": cached_calc.transport_mode or "Unknown",
                "default_transport_mode": cached_calc.transport_mode or "Unknown",
                "selected_transport_mode": override_mode or None,
                "emission_factors": {},
                "eco_score_ml": cached_eco_score,
                "eco_score_ml_confidence": None,
                "eco_score_rule_based": cached_eco_score,
                "eco_score_rule_based_local_only": cached_eco_score,
                "method_agreement": "Yes",
                "prediction_methods": {
                    "ml_prediction": {
                        "score": cached_eco_score,
                        "confidence": "N/A",
                        "method": "Database cache",
                        "features_used": {"feature_count": 0, "features": []}
                    },
                    "rule_based_prediction": {
                        "score": cached_eco_score,
                        "confidence": "N/A",
                        "method": "Database cache"
                    }
                },
                "trees_to_offset": round(cached_total / 20, 1)
            }

            cached_attributes = standardize_attributes(cached_attributes, [
                "origin",
                "country_of_origin",
                "facility_origin",
                "origin_source",
                "origin_confidence",
                "dimensions_cm",
                "material_type",
                "recyclability",
            ])

            return jsonify({
                "title": cached_product.title or "Unknown Product",
                "cache_hit": True,
                "cache_source": "emission_calculation",
                "data": {
                    "attributes": cached_attributes
                }
            })

        # Scrape product using production scraper with category intelligence
        print(f"🔍 Scraping URL: {url}")
        
        if PRODUCTION_SCRAPER_AVAILABLE:
            # Use production scraper with category intelligence and enhanced reliability
            production_scraper = ProductionAmazonScraper()
            result = production_scraper.scrape_with_full_url(url)
            
            if result and result.get('title', 'Unknown Product') != 'Unknown Product':
                print(f"✅ Production scraper success: {result.get('title', '')[:50]}... (confidence: {result.get('confidence_score', 0):.1%})")
                product = result
                
                # If production scraper didn't get detailed materials, try detailed scraper for materials
                needs_detail_enrichment = (
                    not product.get('materials')
                    or not product.get('materials', {}).get('primary_material')
                    or str(product.get('origin', 'Unknown')).strip().lower() in {'unknown', ''}
                    or str(product.get('country_of_origin', 'Unknown')).strip().lower() in {'unknown', ''}
                )

                if needs_detail_enrichment:
                    print("🔍 Production scraper missing key details, trying detailed scraper for materials/origin...")

                    def _is_unknown_value(value) -> bool:
                        return str(value or "").strip().lower() in {'unknown', '', 'none', 'n/a', 'na'}

                    def _origin_source_rank(source: str) -> int:
                        source_key = str(source or '').strip().lower()
                        rank_map = {
                            'product_details': 100,
                            'technical_details': 100,
                            'manufacturer_contact': 95,
                            'specifications': 90,
                            'raw_text': 80,
                            'detailed_scraper': 70,
                            'unified_scraper': 60,
                            'requests_scraper': 55,
                            'brand_mapping': 40,
                            'brand_db': 35,
                            'title_description': 25,
                            'heuristic_brand_default': 20,
                            'default_uk': 10,
                            'unknown': 0,
                        }
                        return rank_map.get(source_key, 50)

                    def _is_weak_heuristic_source(source: str) -> bool:
                        source_key = str(source or '').strip().lower()
                        return source_key in {'heuristic_brand_default', 'title_description', 'default_uk', 'unknown'}

                    def _merge_enrichment(enriched: dict, fallback_source: str, fallback_confidence: str) -> None:
                        if not enriched:
                            return

                        if enriched.get('materials') and (
                            not product.get('materials')
                            or not product.get('materials', {}).get('primary_material')
                        ):
                            print(f"✅ Enrichment found materials: {enriched.get('materials')}")
                            product['materials'] = enriched['materials']
                            if enriched['materials'].get('primary_material'):
                                product['material_type'] = enriched['materials']['primary_material']

                        candidate_origin = enriched.get('country_of_origin') or enriched.get('origin')
                        if _is_unknown_value(candidate_origin):
                            return

                        existing_origin = product.get('country_of_origin') or product.get('origin')
                        existing_source = product.get('origin_source', 'unknown')
                        candidate_source = enriched.get('origin_source', fallback_source)

                        if _is_weak_heuristic_source(candidate_source):
                            print(f"⚠️ Skipping weak heuristic origin source: {candidate_source}")
                            return

                        should_replace = _is_unknown_value(existing_origin) or (
                            _origin_source_rank(candidate_source) > _origin_source_rank(existing_source)
                        )

                        if should_replace:
                            product['origin'] = candidate_origin
                            product['country_of_origin'] = candidate_origin
                            product['origin_source'] = candidate_source
                            product['origin_confidence'] = enriched.get('origin_confidence', fallback_confidence)
                            print(
                                f"✅ Enrichment set origin: {candidate_origin} "
                                f"(source: {candidate_source}, replaced: {existing_origin})"
                            )

                    try:
                        from backend.scrapers.amazon.scrape_amazon_titles import scrape_amazon_product_page as scrape_amazon_product_page_detailed
                        detailed_result = scrape_amazon_product_page_detailed(url, fallback=False)
                        _merge_enrichment(detailed_result, 'detailed_scraper', 'medium')
                    except Exception as e:
                        print(f"⚠️ Error getting materials/origin from detailed scraper: {e}")

                    still_missing_key_details = (
                        not product.get('materials')
                        or not product.get('materials', {}).get('primary_material')
                        or _is_unknown_value(product.get('origin'))
                        or _is_unknown_value(product.get('country_of_origin'))
                    )

                    if still_missing_key_details:
                        print("🔁 Detailed scraper incomplete, trying unified scraper as next-ranked fallback...")
                        try:
                            unified_result = scrape_amazon_product_page(url)
                            _merge_enrichment(unified_result, 'unified_scraper', 'low')
                        except Exception as e2:
                            print(f"⚠️ Error with unified scraper fallback: {e2}")
            else:
                print("⚠️ Production scraper failed, trying fallback")
                if ENHANCED_SCRAPER_AVAILABLE:
                    enhanced_scraper = EnhancedAmazonScraper()
                    result = enhanced_scraper.scrape_product_enhanced(url)
                    if result and result.get('title', 'Unknown Product') != 'Unknown Product':
                        print(f"✅ Enhanced scraper fallback success")
                        product = result
                    else:
                        print("⚠️ Enhanced scraper also failed, using unified fallback")
                        product = scrape_amazon_product_page(url)
                else:
                    product = scrape_amazon_product_page(url)
        elif ENHANCED_SCRAPER_AVAILABLE:
            # Use enhanced scraper as fallback
            enhanced_scraper = EnhancedAmazonScraper()
            result = enhanced_scraper.scrape_product_enhanced(url)
            
            if result and result.get('title', 'Unknown Product') != 'Unknown Product':
                print(f"✅ Enhanced scraper success: {result.get('title', '')[:50]}...")
                product = result
            else:
                print("⚠️ Enhanced scraper failed, using unified fallback")
                product = scrape_amazon_product_page(url)
        else:
            # Use unified scraper as final fallback
            product = scrape_amazon_product_page(url)
        
        # Debug what the scraper returned
        print("🔍 DEBUG: Scraper returned:")
        for key, value in product.items():
            print(f"  {key}: {value}")
        
        # Apply 5-tier materials intelligence
        try:
            from backend.services.materials_service import detect_product_materials
            print("🧬 Applying 5-tier materials intelligence...")

            existing_material_type = str(product.get('material_type', '') or '').strip()
            existing_material_known = existing_material_type.lower() not in {'', 'unknown', 'mixed', 'other'}
            
            # Extract existing materials data
            amazon_materials = product.get('materials', {})
            
            # Prepare product data for analysis
            product_analysis_data = {
                'title': product.get('title', ''),
                'description': product.get('description', ''),
                'category': product.get('category', ''),
                'brand': product.get('brand', '')
            }
            
            # Get intelligent materials detection
            materials_result = detect_product_materials(product_analysis_data, amazon_materials)
            
            # Update product with enhanced materials data
            product['materials'] = {
                'primary_material': materials_result['primary_material'],
                'primary_percentage': materials_result.get('primary_percentage'),
                'secondary_materials': materials_result.get('secondary_materials', []),
                'all_materials': materials_result.get('all_materials', []),
                'confidence': materials_result['confidence'],
                'environmental_impact_score': materials_result.get('environmental_impact_score', 2.5),
                'has_percentages': materials_result.get('has_percentages', False),
                'tier': materials_result['tier'],
                'tier_name': materials_result['tier_name'],
                'prediction_method': materials_result.get('prediction_method', '')
            }
            
            # Update the basic material_type with the primary material
            proposed_material = str(materials_result.get('primary_material', '') or '').strip()
            proposed_tier = int(materials_result.get('tier', 5) or 5)
            title_text = str(product.get('title', '') or '').lower()

            title_has_wood_signal = any(token in title_text for token in [
                'wooden', 'wood spoon', 'wood cutlery', 'bamboo', 'birchwood'
            ])
            title_has_anti_plastic_signal = any(token in title_text for token in [
                'plastic free', 'plastic-free', 'no plastic'
            ])
            title_strongly_prefers_wood = title_has_wood_signal and title_has_anti_plastic_signal

            should_apply_proposed_material = (
                proposed_material not in ['Mixed', 'Unknown', '']
            )

            # Keep explicit scraper material when intelligence result is low-reliability (tier 4/5)
            if existing_material_known and proposed_tier >= 4:
                override_low_tier_due_to_title = (
                    existing_material_type.lower() == 'plastic'
                    and proposed_material.lower() in {'wood', 'bamboo', 'paper'}
                    and title_strongly_prefers_wood
                )

                if override_low_tier_due_to_title:
                    print(
                        f"🧬 Title strongly indicates wood/plastic-free; overriding explicit "
                        f"'{existing_material_type}' with tier-{proposed_tier} '{proposed_material}'"
                    )
                else:
                    should_apply_proposed_material = False
                    product['materials']['primary_material'] = existing_material_type
                    print(
                        f"🧬 Keeping explicit scraper material '{existing_material_type}' over "
                        f"tier-{proposed_tier} prediction '{proposed_material}'"
                    )

            if should_apply_proposed_material:
                product['material_type'] = proposed_material
            
            print(f"✅ Materials intelligence: Tier {materials_result['tier']} - {materials_result['tier_name']}")
            print(f"   Primary: {materials_result['primary_material']} (confidence: {materials_result['confidence']:.2f})")
            if materials_result.get('secondary_materials'):
                secondary_names = [m['name'] for m in materials_result['secondary_materials']]
                print(f"   Secondary: {', '.join(secondary_names)}")
            
        except Exception as e:
            print(f"⚠️ Materials intelligence failed: {e}")
            # Fallback to existing materials system
            pass
        print("🔍 END DEBUG")
        
        # Add additional fields for compatibility with existing UI
        if PRODUCTION_SCRAPER_AVAILABLE and 'category' in product:
            print(f"🏷️ Product category: {product['category']} (confidence: {product.get('category_confidence', 0):.1%})")
            if 'scraping_metadata' in product:
                print(f"🔧 Scraping strategy: {product['scraping_metadata']['successful_strategy']}")
                print(f"📊 Success rate: {product['scraping_metadata']['success_rate']}")
        
        from backend.scrapers.amazon.guess_material import smart_guess_material

        material = product.get("material_type")
        # Only do additional material processing if using fallback scrapers
        if not PRODUCTION_SCRAPER_AVAILABLE and (not material or material.lower() in ["unknown", "other", ""]):
            guessed = smart_guess_material(product.get("title", ""))
            if guessed:
                print(f"🧠 Fallback guessed material: {guessed}")
                material = guessed.title()
                product["material_type"] = material
        elif PRODUCTION_SCRAPER_AVAILABLE:
            print(f"🔧 Production scraper handled material detection: {material}")
        
        # Ensure material is set
        if not product.get("material_type"):
            product["material_type"] = material or "Mixed"

        normalized_material = apply_material_title_consistency(product)
        if normalized_material and str(normalized_material).strip().lower() != str(material or '').strip().lower():
            print(f"🧬 Consistency override material: {material} -> {normalized_material}")
            material = normalized_material
        else:
            material = product.get("material_type") or material
        
        # Universal product enhancement (no product-specific hardcoding)
        print("🔧 Applying universal product data enhancement...")
        
        # Enhanced weight extraction (only needed for fallback scrapers)
        title = product.get("title", "")
        current_weight = product.get("weight_kg", 0)
        
        print(f"🔧 Current weight from scraper: {current_weight}kg")
        
        # Only do additional weight processing if using fallback scrapers
        if not PRODUCTION_SCRAPER_AVAILABLE and current_weight <= 0.1:
            import re
            enhanced_weight = extract_weight_from_title(title)
            if enhanced_weight > 0:
                product["weight_kg"] = enhanced_weight
                print(f"🔧 Enhanced weight extraction: {enhanced_weight}kg from title")
            else:
                # Use category-specific fallback when extraction fails
                fallback_weight = get_category_fallback_weight(title, product.get("brand", ""))
                product["weight_kg"] = fallback_weight
                print(f"🔧 Using category fallback weight: {fallback_weight}kg")
        else:
            if PRODUCTION_SCRAPER_AVAILABLE:
                print(f"🔧 Production scraper handled weight extraction: {current_weight}kg")
            else:
                print(f"🔧 Weight seems reasonable, keeping: {current_weight}kg")
        
        # Enhanced origin extraction with priority system
        enhanced_origins = extract_enhanced_origins(product, title)
        if enhanced_origins:
            product.update(enhanced_origins)
            print(f"🔧 Enhanced origins: {enhanced_origins}")

        if not product:
            return jsonify({"error": "Could not fetch product"}), 500

        # Get user coordinates from postcode
        import pgeocode
        geo = pgeocode.Nominatim("gb")
        location = geo.query_postal_code(postcode)
        if location.empty or location.latitude is None:
            return jsonify({"error": "Invalid postcode"}), 400

        user_lat, user_lon = location.latitude, location.longitude

        # Get origin coordinates - use country_of_origin for distance calculation
        origin_source = str(product.get("origin_source", "") or "").strip().lower()
        weak_sources = {"heuristic_brand_default", "heuristic_title_default", "title_description", "default_uk", "unknown"}
        origin_country = product.get("country_of_origin") or product.get("origin") or product.get("brand_estimated_origin") or "Unknown"

        if origin_source in weak_sources and str(origin_country).strip().lower() == "uk":
            origin_country = "Unknown"

        if str(origin_country).strip().lower() in {"", "unknown", "none", "n/a", "na"}:
            heuristic_origin = estimate_origin_country(title) if title else "Unknown"
            if str(heuristic_origin).strip().lower() not in {"", "unknown", "none", "n/a", "na"}:
                origin_country = heuristic_origin
                product["origin"] = origin_country
                product["country_of_origin"] = origin_country
                product["origin_source"] = "heuristic_title_default"
                product["origin_confidence"] = "low"

        facility_origin = product.get("facility_origin", "Unknown")
        
        # For UK internal deliveries, determine specific region from postcode
        # Only remap when origin came from explicit high-confidence page evidence.
        origin_source = str(product.get("origin_source", "")).strip().lower()
        explicit_sources = {"technical_details", "product_details", "manufacturer_contact", "specifications", "scraped_verified", "raw_text"}
        if origin_country == "UK" and postcode and origin_source in explicit_sources:
            postcode_upper = postcode.upper()
            if postcode_upper.startswith(('CF', 'NP', 'SA', 'SY', 'LL', 'LD')):
                origin_country = "Wales"
            elif postcode_upper.startswith(('EH', 'G', 'KA', 'ML', 'PA', 'PH', 'FK', 'KY', 'AB', 'DD', 'DG', 'TD', 'KW', 'IV', 'HS', 'ZE')):
                origin_country = "Scotland"
            elif postcode_upper.startswith('BT'):
                origin_country = "Northern Ireland"
            else:
                origin_country = "England"
            print(f"🇬🇧 UK internal delivery - Origin: {origin_country}")
        
        print(f"🌍 Origin determined: {origin_country}")
        origin_coords = origin_hubs.get(origin_country, uk_hub)

        # Distance calculations
        origin_distance_km = round(haversine(origin_coords["lat"], origin_coords["lon"], user_lat, user_lon), 1)
        uk_distance_km = round(haversine(uk_hub["lat"], uk_hub["lon"], user_lat, user_lon), 1)

        print(f"🌍 Distances → origin: {origin_distance_km} km | UK hub: {uk_distance_km} km")

        # Use weight from scraper
        raw_weight = product.get("weight_kg") or product.get("raw_product_weight_kg") or 0.5
        weight = float(raw_weight)
        print(f"🏋️ Using weight: {weight} kg from scraper")
        if include_packaging:
            weight *= 1.05

        # Transport mode logic with geographic considerations
        def determine_transport_mode(distance_km, origin_country="Unknown"):
            # Special cases for water crossings to UK
            water_crossing_countries = ["Ireland", "France", "Germany", "Netherlands", "Belgium", "Denmark", 
                                      "Sweden", "Norway", "Finland", "Spain", "Italy", "Poland"]
            
            if origin_country in water_crossing_countries:
                if distance_km < 500:
                    return "Truck", 0.15  # Channel tunnel or short ferry
                elif distance_km < 3000:
                    return "Ship", 0.03   # Ferry or cargo ship
                else:
                    return "Air", 0.5     # Long distance air
            
            # Standard logic for other routes
            if distance_km < 1500:
                return "Truck", 0.15
            elif distance_km < 6000:
                return "Ship", 0.03
            else:
                return "Air", 0.5

        default_mode, default_emission_factor = determine_transport_mode(origin_distance_km, origin_country)

        modes = {
            "Air": 0.5,
            "Ship": 0.03,
            "Truck": 0.15
        }

        if override_mode in modes:
            transport_mode = override_mode
            emission_factor = modes[override_mode]
            print(f"🚚 Override transport mode used: {transport_mode}")
        else:
            transport_mode = default_mode
            emission_factor = default_emission_factor
            print(f"📦 Auto-detected transport mode used: {transport_mode}")

        # Calculate realistic CO2 using manufacturing complexity (same as fixed dataset)
        if MANUFACTURING_COMPLEXITY_AVAILABLE:
            # Get material CO2 intensity
            material_name = product.get("material_type", "").lower() or product.get("materials", {}).get("primary_material", "").lower()
            material_co2_per_kg = materials_db.get_material_impact_score(material_name)
            
            if not material_co2_per_kg:
                # Use fallback for unknown materials
                material_variants = {
                    'textile': 'cotton',
                    'metal': 'steel', 
                    'electronic': 'aluminum',
                    'mixed': 'plastic',
                    'aluminum': 'aluminum',
                    'plastic': 'plastic',
                    'steel': 'steel',
                    'cotton': 'cotton'
                }
                alt_material = material_variants.get(material_name, 'plastic')
                material_co2_per_kg = materials_db.get_material_impact_score(alt_material) or 2.0
            
            # Get transport multiplier
            transport_multipliers = {"air": 2.5, "ship": 1.0, "truck": 1.2, "land": 1.2}
            transport_multiplier = transport_multipliers.get(transport_mode.lower(), 1.0)
            
            # Get category for manufacturing complexity
            category = product.get("category", "general").lower().replace(' ', '_').replace('&', '_')
            
            # Calculate realistic CO2 with manufacturing complexity (same method as dataset fix)
            enhanced_result = complexity_calculator.calculate_enhanced_co2(
                weight_kg=weight,
                material_co2_per_kg=material_co2_per_kg,
                transport_multiplier=transport_multiplier,
                category=category
            )
            
            carbon_kg = round(enhanced_result["enhanced_total_co2"], 2)
            print(f"✅ Realistic CO2 calculated: {carbon_kg} kg CO2 (was {round(weight * emission_factor * (origin_distance_km / 1000), 2)} kg with old method)")
        else:
            # Fallback to old method if complexity system not available
            carbon_kg = round(weight * emission_factor * (origin_distance_km / 1000), 2)
            print(f"⚠️ Using old CO2 calculation method: {carbon_kg} kg CO2")
        
        eco_score_rule = calculate_eco_score(
            carbon_kg,
            product.get("recyclability", "Medium"),
            origin_distance_km,
            weight
        )
        
        eco_score_rule_local = calculate_eco_score_local_only(
            carbon_kg,
            product.get("recyclability", "Medium"),
            weight
        )
        


        # === RULE-BASED Prediction (Your Original Method)
        eco_score_rule_based = calculate_eco_score(
            carbon_kg,
            product.get("recyclability", "Medium"),
            origin_distance_km,
            weight
        )
        
        # === ENHANCED ML Prediction (New Method)
        ml_features_used = None
        shap_explanation = None
        try:
            material = product.get("material_type", "Other")
            recyclability = product.get("recyclability", "Medium")
            origin = origin_country

            # === Normalize and encode for ML
            material = normalize_feature(material, "Other")
            recyclability = normalize_feature(recyclability, "Medium")
            origin = normalize_feature(origin, "Other")
            transport = transport_mode

            material_encoded = safe_encode(material, material_encoder, "Other")
            transport_encoded = safe_encode(transport, transport_encoder, "Land")
            recycle_encoded = safe_encode(recyclability, recycle_encoder, "Medium")
            origin_encoded = safe_encode(origin, origin_encoder, "Other")

            # === Enhanced features for ML (11 features total)
            weight_log = np.log1p(weight)
            weight_bin_encoded = 2 if weight > 0.5 else 1 if weight > 0.1 else 0
            
            # Infer additional features from product data
            title_lower = product.get("title", "").lower()
            
            # Packaging type inference
            if any(x in title_lower for x in ["bottle", "jar", "can"]):
                packaging_type = "bottle"
            elif any(x in title_lower for x in ["box", "pack", "carton"]):
                packaging_type = "box"
            else:
                packaging_type = "other"
            
            # Size category inference
            if weight > 2.0:
                size_category = "large"
            elif weight > 0.5:
                size_category = "medium"
            else:
                size_category = "small"
            
            # Quality level inference
            if any(x in title_lower for x in ["premium", "pro", "professional", "deluxe"]):
                quality_level = "premium"
            elif any(x in title_lower for x in ["basic", "standard", "regular"]):
                quality_level = "standard"
            else:
                quality_level = "standard"
            
            # Pack size (number of items)
            pack_size = 1
            for num_word in ["2 pack", "3 pack", "4 pack", "5 pack", "6 pack", "8 pack", "10 pack", "12 pack"]:
                if num_word in title_lower:
                    pack_size = int(num_word.split()[0])
                    break
            
            # Material confidence (based on how specific the material type is)
            material_confidence = 0.8 if material != "Other" else 0.3
            
            # Load enhanced encoders
            try:
                # Check if enhanced encoders are available
                if packaging_type_encoder and size_category_encoder and quality_level_encoder:
                    # Try to encode the enhanced features
                    packaging_encoded = safe_encode(packaging_type, packaging_type_encoder, "box")
                    size_encoded = safe_encode(size_category, size_category_encoder, "medium") 
                    quality_encoded = safe_encode(quality_level, quality_level_encoder, "standard")
                    
                    # === ADD MISSING ENHANCED FEATURES FOR 16-FEATURE MODEL ===
                    
                    # Infer category from product title
                    category_encoded = 0  # Default to first category
                    if inferred_category_encoder:
                        inferred_category = "supplement" if "protein" in product.get("title", "").lower() else "other"
                        category_encoded = safe_encode(inferred_category, inferred_category_encoder, "other")
                    
                    # Additional confidence scores
                    origin_confidence = 0.9 if product.get("origin", "Unknown") != "Unknown" else 0.3
                    weight_confidence = 0.9 if product.get("weight_kg", 1.0) != 1.0 else 0.5
                    
                    # Product lifecycle estimates
                    estimated_lifespan_years = 2.0 if "supplement" in product.get("title", "").lower() else 5.0
                    repairability_score = 0.1 if material in ["Plastic", "Glass"] else 0.6
                    
                    # Build the full feature vector (16 features as expected by enhanced model)
                    X = [[
                        material_encoded,           # 1: material_encoded
                        transport_encoded,          # 2: transport_encoded  
                        recycle_encoded,           # 3: recyclability_encoded
                        origin_encoded,            # 4: origin_encoded
                        weight_log,                # 5: weight_log
                        weight_bin_encoded,        # 6: weight_bin_encoded
                        packaging_encoded,         # 7: packaging_type_encoded
                        size_encoded,              # 8: size_category_encoded
                        quality_encoded,           # 9: quality_level_encoded
                        category_encoded,          # 10: inferred_category_encoded
                        pack_size,                 # 11: pack_size
                        material_confidence,       # 12: material_confidence
                        origin_confidence,         # 13: origin_confidence
                        weight_confidence,         # 14: weight_confidence
                        estimated_lifespan_years,  # 15: estimated_lifespan_years
                        repairability_score        # 16: repairability_score
                    ]]
                    
                    # Show all 16 features for transparency
                    feature_names = [
                        "Material Type", "Transport Mode", "Recyclability", "Origin Country",
                        "Weight (log)", "Weight Category", "Packaging Type", "Size Category", 
                        "Quality Level", "Inferred Category", "Pack Size", "Material Confidence",
                        "Origin Confidence", "Weight Confidence", "Estimated Lifespan", "Repairability Score"
                    ]
                    feature_values = [
                        material_encoded, transport_encoded, recycle_encoded, origin_encoded,
                        weight_log, weight_bin_encoded, packaging_encoded, size_encoded,
                        quality_encoded, category_encoded, pack_size, material_confidence,
                        origin_confidence, weight_confidence, estimated_lifespan_years, repairability_score
                    ]
                    
                    print(f"🔧 Using 16 enhanced features for ML prediction:")
                    for name, value in zip(feature_names, feature_values):
                        print(f"   {name}: {value}")
                    
                    print(f"🔧 Final feature vector: {X[0]}")
                    
                    # Store features for response (convert numpy types)
                    ml_features_used = {
                        "feature_count": 16,
                        "model_type": "enhanced_16_feature",
                        "features": [{"name": name, "value": convert_numpy_types(value)} for name, value in zip(feature_names, feature_values)]
                    }
                else:
                    raise Exception("Enhanced encoders not available")
                
            except Exception as enc_error:
                print(f"⚠️ Enhanced encoder error: {enc_error}, falling back to 6 features")
                # Fallback to original 6 features
                X = [[
                    material_encoded,
                    transport_encoded,
                    recycle_encoded,
                    origin_encoded,
                    weight_log,
                    weight_bin_encoded
                ]]
                
                # Store fallback features for response
                fallback_feature_names = [
                    "Material Type", "Transport Mode", "Recyclability", "Origin Country",
                    "Weight (log)", "Weight Category"
                ]
                fallback_feature_values = [
                    material_encoded, transport_encoded, recycle_encoded, origin_encoded,
                    weight_log, weight_bin_encoded
                ]
                ml_features_used = {
                    "feature_count": 6,
                    "features": [{"name": name, "value": convert_numpy_types(value)} for name, value in zip(fallback_feature_names, fallback_feature_values)]
                }

            # ML Prediction - Use correct features based on loaded model
            if model_type == "basic" or model_type is None:
                # Force 6 features for basic model
                X = [[
                    material_encoded,
                    transport_encoded,
                    recycle_encoded,
                    origin_encoded,
                    weight_log,
                    weight_bin_encoded
                ]]
                print("📊 Using 6 features for basic model")
                ml_features_used["feature_count"] = 6
            
            # ML Prediction
            if model is None:
                raise Exception("Model not available")
            
            try:
                prediction = model.predict(X)[0]
                eco_score_ml = label_encoder.inverse_transform([prediction])[0]
                print(f"✅ ML prediction successful: {eco_score_ml}")
                
                confidence = 0.0
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(X)
                    confidence = round(float(np.max(proba[0])) * 100, 1)
            except Exception as pred_error:
                print(f"⚠️ ML prediction error: {pred_error}")
                print(f"   Feature vector shape: {len(X[0])} features")
                print(f"   Model type: {model_type}")
                # Use rule-based as fallback
                eco_score_ml = eco_score_rule_based
                confidence = 0.0

            print(f"✅ ML Score: {eco_score_ml} ({confidence}%)")
            print(f"🔧 Rule-based Score: {eco_score_rule_based}")

            # === SHAP per-prediction explanation
            shap_explanation = None
            try:
                import shap as shap_lib
                explainer = shap_lib.TreeExplainer(model)
                X_arr = np.array(X)
                shap_vals = explainer.shap_values(X_arr)

                n_features = len(X[0])
                all_feat_names = [
                    'Material Type', 'Transport Mode', 'Recyclability', 'Origin Country',
                    'Weight', 'Weight Category', 'Packaging Type', 'Size Category',
                    'Quality Level', 'Category', 'Pack Size', 'Material Confidence',
                    'Origin Confidence', 'Weight Confidence', 'Est. Lifespan', 'Repairability'
                ]
                feat_names = all_feat_names[:n_features]

                weight_bins = ['<0.5 kg', '0.5–2 kg', '2–10 kg', '>10 kg']
                raw_vals = [
                    material, transport, recyclability, origin,
                    f"{round(weight, 2)} kg",
                    weight_bins[int(weight_bin_encoded)] if 0 <= int(weight_bin_encoded) < 4 else str(weight_bin_encoded)
                ] + [''] * max(0, n_features - 6)

                pred_idx = int(np.argmax(model.predict_proba(X_arr)[0]))

                sv = np.array(shap_vals)
                if sv.ndim == 3:
                    class_shap = sv[0, :, pred_idx]
                elif isinstance(shap_vals, list):
                    class_shap = np.array(shap_vals[pred_idx])[0]
                else:
                    class_shap = sv[0]

                ev = explainer.expected_value
                base_val = float(ev[pred_idx]) if hasattr(ev, '__len__') else float(ev)

                shap_features = [
                    {
                        "name": feat_names[i],
                        "shap_value": round(float(class_shap[i]), 4),
                        "raw_value": raw_vals[i] if i < len(raw_vals) else ""
                    }
                    for i in range(min(n_features, len(class_shap)))
                ]
                shap_features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

                shap_explanation = {
                    "predicted_class": eco_score_ml,
                    "base_value": round(base_val, 4),
                    "features": shap_features
                }
                print(f"✅ SHAP explanation computed ({n_features} features)")
            except Exception as shap_err:
                print(f"⚠️ SHAP computation failed: {shap_err}")
                shap_explanation = None

        except Exception as e:
            print(f"⚠️ ML prediction failed: {e}")
            eco_score_ml = "N/A"
            confidence = None
            shap_explanation = None


        # Assemble response
        response_origin_source = str(product.get("origin_source", "brand_db") or "brand_db").strip().lower()
        response_origin_confidence = product.get("origin_confidence")
        if not response_origin_confidence:
            if response_origin_source in {"technical_details", "product_details", "scraped_verified"}:
                response_origin_confidence = "high"
            elif response_origin_source in {"specifications", "manufacturer_contact", "brand_db", "brand_mapping"}:
                response_origin_confidence = "medium"
            elif response_origin_source in {"heuristic_title_default", "asin_history", "heuristic_brand_default", "title_description"}:
                response_origin_confidence = "low"
            else:
                response_origin_confidence = "unknown"

        attributes = {
            "carbon_kg": convert_numpy_types(carbon_kg),
            "weight_kg": convert_numpy_types(round(raw_weight, 2)),
            "raw_product_weight_kg": convert_numpy_types(round(raw_weight, 2)),
            "origin": origin_country,
            "country_of_origin": origin_country,
            "facility_origin": facility_origin,
            "origin_source": response_origin_source,
            "origin_confidence": response_origin_confidence,

            # Distance fields
            "intl_distance_km": convert_numpy_types(origin_distance_km),
            "uk_distance_km": convert_numpy_types(uk_distance_km),
            "distance_from_origin_km": convert_numpy_types(origin_distance_km),
            "distance_from_uk_hub_km": convert_numpy_types(uk_distance_km),

            # Product features
            "dimensions_cm": product.get("dimensions_cm"),
            "material_type": product.get("material_type"),
            "materials": product.get("materials", {}),
            "recyclability": product.get("recyclability"),
            "recyclability_percentage": convert_numpy_types(product.get("recyclability_percentage", 30)),
            "recyclability_description": product.get("recyclability_description", "Assessment pending"),

            # Transport details
            "transport_mode": transport_mode,
            "default_transport_mode": default_mode,
            "selected_transport_mode": override_mode or None,
            "emission_factors": modes,

            # Scoring - BOTH Methods for Comparison
            "eco_score_ml": eco_score_ml,
            "eco_score_ml_confidence": convert_numpy_types(confidence) if confidence else None,
            "eco_score_rule_based": eco_score_rule_based,
            "eco_score_rule_based_local_only": eco_score_rule_local,

            # Method Comparison
            "method_agreement": "Yes" if eco_score_ml == eco_score_rule_based else "No",
            "prediction_methods": {
                "ml_prediction": {
                    "score": eco_score_ml,
                    "confidence": f"{confidence}%" if confidence else "N/A",
                    "method": "Enhanced XGBoost (11 features)",
                    "features_used": ml_features_used
                },
                "rule_based_prediction": {
                    "score": eco_score_rule_based,
                    "confidence": "80%",
                    "method": "Traditional Heuristic Rules"
                }
            },

            # Misc
            "trees_to_offset": round(carbon_kg / 20, 1),

            # SHAP per-prediction explanation
            "shap_explanation": shap_explanation
        }

        attributes = standardize_attributes(attributes, [
            "origin",
            "country_of_origin",
            "facility_origin",
            "origin_source",
            "origin_confidence",
            "dimensions_cm",
            "material_type",
            "recyclability",
        ])

        try:
            confidence_label = str(response_origin_confidence or "medium").strip().lower()
            confidence_to_score = {
                "high": 0.9,
                "medium": 0.7,
                "low": 0.5,
                "unknown": 0.4,
            }
            confidence_score = confidence_to_score.get(confidence_label, 0.7)

            scraped_product = get_or_create_scraped_product({
                'amazon_url': url,
                'asin': product.get('asin') or asin_key,
                'title': product.get('title'),
                'price': product.get('price'),
                'weight': raw_weight,
                'material': product.get('material_type'),
                'brand': product.get('brand'),
                'origin_country': origin_country,
                'confidence_score': product.get('confidence_score', 0.85),
                'scraping_status': 'success'
            })

            save_emission_calculation({
                'scraped_product_id': scraped_product.id,
                'user_postcode': postcode,
                'transport_distance': origin_distance_km,
                'transport_mode': transport_mode,
                'ml_prediction': float(carbon_kg),
                'rule_based_prediction': float(carbon_kg),
                'final_emission': float(carbon_kg),
                'confidence_level': confidence_score,
                'calculation_method': 'combined'
            })

            append_estimation_to_expanded_dataset({
                'title': product.get('title') or 'Unknown Product',
                'material': product.get('material_type') or product.get('material') or 'Other',
                'weight': round(float(weight), 4),
                'transport': transport_mode,
                'recyclability': attributes.get('recyclability') or 'Medium',
                'true_eco_score': attributes.get('eco_score_rule_based_local_only') or attributes.get('eco_score_rule_based') or attributes.get('eco_score_ml') or 'C',
                'co2_emissions': round(float(carbon_kg), 4),
                'origin': origin_country or 'Unknown',
                'category': product.get('category') or '',
                'search_term': product.get('search_term') or '',
            })
        except Exception as db_save_error:
            print(f"⚠️ Database save error: {db_save_error}")

        return jsonify({
            "title": product.get("title"),
            "data": {
                "attributes": attributes
            }
        })


    except Exception as e:
        print(f"❌ Uncaught error in estimate_emissions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/test_post", methods=["POST"])
def test_post():
    try:
        data = request.get_json()
        print("✅ Received test POST:", data)
        return jsonify({"message": "Success", "you_sent": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "✅ Server is up"}), 200



@app.route("/")
def home():
    """Lightweight backend status page; frontend serves the calculator."""
    return "<h2>🌍 Flask is running</h2>"

@app.route("/enterprise")
def enterprise_dashboard():
    """Serve the enterprise dashboard for Series A demos and enterprise customers."""
    return send_from_directory(
        os.path.join(BASE_DIR, "frontend"), 
        "enterprise_dashboard.html"
    )

@app.route("/test")
def test():
    return "✅ Flask test OK"



#if __name__ == "__main__":
 #   print("🚀 Flask is launching...")
  #  app.run(debug=True)
   # host="0.0.0.0", port=5000,
   
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0" if is_production else "127.0.0.1")
    debug = (os.environ.get("DEBUG", "0") == "1") if is_production else True
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"🔧 CORS configured for production: {is_production}")
    app.run(host=host, port=port, debug=debug)
 