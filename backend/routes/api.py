"""
Core emissions estimation helper functions.

NOTE: The standalone Flask `app` and `/estimate_emissions` route defined in
this file are legacy and are NOT served in production.  The live endpoint is
registered inside `backend/api/app_production.py::create_app()`.

Only the following helper functions are imported and used by `app_production.py`:
  - calculate_eco_score()  — converts CO₂ kg to an A–F eco grade
  - calculate_eco_score_local_only()  — variant without transport distance
  - map_score_to_grade()  — maps numeric score to letter grade

Do NOT remove this file — its imports and helper functions are still active.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.scrapers.amazon.unified_scraper import scrape_amazon_product_page
from backend.scrapers.amazon.integrated_scraper import haversine, origin_hubs, uk_hub
import pgeocode
from backend.scrapers.amazon.guess_material import smart_guess_material
import sys
import os

# Add services directory for manufacturing complexity (project-relative)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICES_DIR = os.path.join(PROJECT_ROOT, 'backend', 'services')
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)
from manufacturing_complexity_multipliers import ManufacturingComplexityCalculator
from enhanced_materials_database import EnhancedMaterialsDatabase


app = Flask(__name__)
CORS(app)

# Initialize manufacturing complexity system for realistic CO2 calculations
complexity_calculator = ManufacturingComplexityCalculator()
materials_db = EnhancedMaterialsDatabase()
print("✅ API now using realistic CO2 calculations with manufacturing complexity")

# Helper function to determine transport mode based on distance
def determine_transport_mode(distance_km):
    if distance_km < 1500:
        return "Truck", 0.12  # 120g per tonne-km
    elif distance_km < 6000:
        return "Ship", 0.02   # 20g per tonne-km
    else:
        return "Air", 0.5     # 500g per tonne-km
   
    
def co2_to_grade(co2_kg: float) -> str:
    """Convert a CO₂ value (kg CO₂e) to an eco grade using DEFRA 2023 thresholds.
    These must match the labels used to train the ML model (ml/retrain.py::co2_to_grade).
    """
    if co2_kg <= 0.05:  return "A+"
    if co2_kg <= 0.15:  return "A"
    if co2_kg <= 0.40:  return "B"
    if co2_kg <= 1.00:  return "C"
    if co2_kg <= 2.50:  return "D"
    if co2_kg <= 5.00:  return "E"
    return "F"


def calculate_eco_score(carbon_kg, recyclability, distance_km, weight_kg):
    carbon_score = max(0, 10 - carbon_kg * 5)
    weight_score = max(0, 10 - weight_kg * 2)
    distance_score = max(0, 10 - distance_km / 1000)
    recycle_score = {
        "Low": 2,
        "Medium": 6,
        "High": 10
    }.get(recyclability or "Medium", 5)

    total_score = (carbon_score + weight_score + distance_score + recycle_score) / 4

    if total_score >= 9:
        return "A+"
    elif total_score >= 8:
        return "A"
    elif total_score >= 6.5:
        return "B"
    elif total_score >= 5:
        return "C"
    elif total_score >= 3.5:
        return "D"
    else:
        return "F"
    
  
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
  

@app.route("/estimate_emissions", methods=["POST"])
def estimate():
    data = request.get_json()
    print("🔍 Incoming data:", data)
    url = data.get("amazon_url")
    postcode = data.get("postcode")
    include_packaging = data.get("include_packaging", True)
    override_mode = data.get("override_transport_mode")

    print(f"🌍 Request received: {url}")
    print(f"📍 Postcode: {postcode} | Packaging included? {include_packaging} | Override mode: {override_mode}")

    if not url or not postcode:
        return jsonify({'error': 'Missing URL or postcode'}), 400

    # Get lat/lon from postcode
    geo = pgeocode.Nominatim('gb')
    location = geo.query_postal_code(postcode)
    if location.empty or location.latitude is None:
        return jsonify({'error': 'Invalid postcode'}), 400

    user_lat, user_lon = location.latitude, location.longitude

    # Scrape product
    product = scrape_amazon_product_page(url)
    # Fallback guess for material type
    material = product.get("material_type")
    if not material or material.lower() in ["unknown", "other", ""]:
        guessed = smart_guess_material(product.get("title", ""))
        if guessed:
            print(f"🧠 Fallback guessed material: {guessed}")
            material = guessed.title()
    product["material_type"] = material

    if not product:
        return jsonify({'error': 'Could not fetch product'}), 500

    print(f"🔍 Scraped product: {product.get('title', 'N/A')}")

    origin = origin_hubs.get(product['brand_estimated_origin'], uk_hub)

    # Distance from origin to user
    distance = haversine(origin['lat'], origin['lon'], user_lat, user_lon)
    origin_distance = round(distance, 1)

    # Distance from UK hub to user
    uk_distance = round(haversine(uk_hub['lat'], uk_hub['lon'], user_lat, user_lon), 1)

    # Raw + final weight
    raw_weight = product['estimated_weight_kg']
    final_weight = raw_weight * 1.05 if include_packaging else raw_weight

    modes = {
    "Air": 0.5,
    "Ship": 0.03,
    "Truck": 0.15
    }
    
    # ✅ Get the default mode based on distance
    default_mode, default_emission_factor = determine_transport_mode(distance)

    
    # Use user override if valid
    if override_mode in modes:
        transport_mode = override_mode
        emission_factor = modes[override_mode]
        print(f"🚚 Override transport mode used: {transport_mode}")
    else:
        transport_mode = default_mode
        emission_factor = default_emission_factor
        print(f"📦 Auto-detected transport mode used: {transport_mode}")

    # ✅ Calculate realistic CO2 using manufacturing complexity (same as fixed dataset)
    # Get material CO2 intensity from enhanced database
    material_co2_per_kg = materials_db.get_material_impact_score(product.get("material", "").lower())
    if not material_co2_per_kg:
        # Use fallback for unknown materials
        material_variants = {
            'textile': 'cotton',
            'metal': 'steel', 
            'electronic': 'aluminum',
            'mixed': 'plastic'
        }
        material_name = product.get("material", "").lower()
        alt_material = material_variants.get(material_name, 'plastic')
        material_co2_per_kg = materials_db.get_material_impact_score(alt_material) or 2.0
    
    # Get transport multiplier
    transport_multipliers = {"air": 2.5, "ship": 1.0, "truck": 1.2, "land": 1.2}
    transport_multiplier = transport_multipliers.get(transport_mode.lower(), 1.0)
    
    # Get category for manufacturing complexity
    category = product.get("category", "general").lower().replace(' ', '_').replace('&', '_')
    
    # Calculate realistic CO2 with manufacturing complexity (same method as dataset fix)
    enhanced_result = complexity_calculator.calculate_enhanced_co2(
        weight_kg=final_weight,
        material_co2_per_kg=material_co2_per_kg,
        transport_multiplier=transport_multiplier,
        category=category
    )
    
    carbon_kg = round(enhanced_result["enhanced_total_co2"], 2)

    # Eco Score
    eco_score = calculate_eco_score(
        carbon_kg,
        product.get("recyclability"),
        origin_distance,
        final_weight
    )
    
    eco_score_rule_local = calculate_eco_score_local_only(
        carbon_kg,
        product.get("recyclability", "Medium"),
        final_weight
    )



    # Metadata
    origin_source = product.get("origin_source", "brand_db")
    confidence = product.get("confidence", "Estimated")


    print("✅ Final values:", {
    "transport_mode": transport_mode,
    "default": default_mode,
    "override": override_mode,
    "emission_factor": emission_factor
})

    eco_score_rule = calculate_eco_score(
        carbon_kg,
        product.get("recyclability"),
        origin_distance,
        final_weight
    )
    

    # Response
    # === Final Response ===
    response = {
        "title": product.get("title"),
        "data": {
            "attributes": {
                "carbon_kg": carbon_kg,
                "weight_kg": round(final_weight, 2),
                "raw_product_weight_kg": round(raw_weight, 2),
                "origin": product.get("brand_estimated_origin"),

                # Distance fields
                "intl_distance_km": origin_distance,
                "uk_distance_km": uk_distance,
                "distance_from_origin_km": origin_distance,
                "distance_from_uk_hub_km": uk_distance,

                # Product features
                "dimensions_cm": product.get("dimensions_cm"),
                "material_type": product.get("material_type"),
                "recyclability": product.get("recyclability"),

                # Transport details
                "transport_mode": transport_mode,
                "default_transport_mode": default_mode,
                "selected_transport_mode": override_mode or None,

                # Emission & scoring
                "emission_factors": modes,
                # Scoring
                "eco_score_ml": eco_score,
                "eco_score_confidence": confidence,
                "eco_score_rule_based": eco_score_rule,
                "eco_score_rule_based_local_only": eco_score_rule_local,

                # Metadata
                "confidence": confidence,
                "origin_source": origin_source,
                "trees_to_offset": round(carbon_kg / 20, 1),
            }
        }
    }

    return jsonify(response)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)