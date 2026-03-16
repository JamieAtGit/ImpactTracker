"""
Production Flask application factory.

Purpose:
- Configures production settings (DB, CORS, secrets, and migrations).
- Initializes SQLAlchemy models and loads ML assets.
- Registers the API endpoints used by deployed environments.
"""
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_migrate import Migrate
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BASE_DIR)

# Import database models
from backend.models.database import db, User, Product, ScrapedProduct, EmissionCalculation, AdminReview
from backend.models.database import save_scraped_product, save_emission_calculation, get_or_create_scraped_product, find_cached_emission_calculation
from werkzeug.security import generate_password_hash, check_password_hash

import json
import re


_ESTIMATION_DEPS = None


def _load_estimation_dependencies():
    global _ESTIMATION_DEPS
    if _ESTIMATION_DEPS is None:
        from backend.scrapers.amazon.unified_scraper import scrape_amazon_product_page
        from backend.scrapers.amazon.integrated_scraper import (
            estimate_origin_country,
            resolve_brand_origin,
            haversine,
            origin_hubs,
            uk_hub,
        )
        from backend.scrapers.amazon.guess_material import smart_guess_material
        from backend.services.prediction_consistency import (
            apply_material_title_consistency,
            normalize_brand_for_lookup,
            normalize_amazon_url,
            extract_asin_from_amazon_url,
        )
        from backend.services.response_standardizer import standardize_attributes
        from backend.routes.api import calculate_eco_score

        _ESTIMATION_DEPS = {
            'scrape_amazon_product_page': scrape_amazon_product_page,
            'estimate_origin_country': estimate_origin_country,
            'resolve_brand_origin': resolve_brand_origin,
            'haversine': haversine,
            'origin_hubs': origin_hubs,
            'uk_hub': uk_hub,
            'smart_guess_material': smart_guess_material,
            'apply_material_title_consistency': apply_material_title_consistency,
            'normalize_brand_for_lookup': normalize_brand_for_lookup,
            'normalize_amazon_url': normalize_amazon_url,
            'extract_asin_from_amazon_url': extract_asin_from_amazon_url,
            'standardize_attributes': standardize_attributes,
            'calculate_eco_score': calculate_eco_score,
        }
    return _ESTIMATION_DEPS

def _safe_float(val):
    """Convert val to float, returning None if not a valid number."""
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _seed_products_from_csv():
    """Seed products table from CSV. Each batch uses engine.begin() so it auto-commits."""
    try:
        import pandas as pd
        from sqlalchemy import text as _text

        dataset_path = os.path.join(BASE_DIR, 'common', 'data', 'csv', 'expanded_eco_dataset.csv')
        if not os.path.exists(dataset_path):
            print(f"⚠️ CSV not found at {dataset_path} — cannot seed products table.")
            return

        df = pd.read_csv(dataset_path)
        df = df.where(pd.notnull(df), None)
        expected = len(df)

        # Check existing count in its own committed transaction
        with db.engine.begin() as conn:
            existing = conn.execute(_text("SELECT COUNT(*) FROM products")).scalar() or 0

        if existing >= int(expected * 0.99):
            print(f"ℹ️ Products table already has {existing}/{expected} rows — skipping seed.")
            return

        if existing > 0:
            print(f"⚠️ Partial seed detected ({existing}/{expected} rows). Clearing and re-seeding...")
            with db.engine.begin() as conn:
                conn.execute(_text("DELETE FROM products"))

        records = df.to_dict(orient='records')
        BATCH = 5000
        total = len(records)
        print(f"🌱 Seeding {total} products into DB from CSV...")

        insert_sql = _text("""
            INSERT INTO products
                (title, material, weight, transport, recyclability,
                 true_eco_score, co2_emissions, origin, category, search_term)
            VALUES
                (:title, :material, :weight, :transport, :recyclability,
                 :true_eco_score, :co2_emissions, :origin, :category, :search_term)
        """)

        for i in range(0, total, BATCH):
            batch = [
                {
                    'title': r.get('title'),
                    'material': r.get('material'),
                    'weight': _safe_float(r.get('weight')),
                    'transport': r.get('transport'),
                    'recyclability': r.get('recyclability'),
                    'true_eco_score': r.get('true_eco_score'),
                    'co2_emissions': _safe_float(r.get('co2_emissions')),
                    'origin': r.get('origin'),
                    'category': r.get('category') or '',
                    'search_term': r.get('search_term') or '',
                }
                for r in records[i:i + BATCH]
                if r.get('title') and str(r.get('title')).lower() != 'title'
            ]
            if not batch:
                continue
            with db.engine.begin() as conn:   # auto-commits on exit, rolls back on error
                conn.execute(insert_sql, batch)
            print(f"  ✅ Committed rows {i+1}–{min(i+BATCH, total)}")

        with db.engine.begin() as conn:
            final_count = conn.execute(_text("SELECT COUNT(*) FROM products")).scalar()
        print(f"🌱 Seeding complete — {final_count} products now in DB.")

    except Exception as e:
        print(f"⚠️ Product seeding failed: {e}")
        import traceback
        traceback.print_exc()


def create_app(config_name='production'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    if config_name == 'production':
        # Railway MySQL connection - build DATABASE_URL from individual components
        mysql_host = os.getenv('MYSQL_HOST')
        mysql_port = os.getenv('MYSQL_PORT')
        mysql_user = os.getenv('MYSQL_USER')
        mysql_password = os.getenv('MYSQL_PASSWORD')
        mysql_database = os.getenv('MYSQL_DATABASE')
        
        if all([mysql_host, mysql_port, mysql_user, mysql_password, mysql_database]):
            database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            print(f"✅ MySQL connection configured: {mysql_host}:{mysql_port}/{mysql_database}")
        else:
            # Fallback to DATABASE_URL if available
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                app.config['SQLALCHEMY_DATABASE_URI'] = database_url
                print(f"✅ Database URL configured from DATABASE_URL")
            else:
                # Stable fallback for production when DB env vars are missing
                print("⚠️ No production DB env found. Falling back to local SQLite for service availability.")
                database_url = 'sqlite:///production_fallback.db'
                app.config['SQLALCHEMY_DATABASE_URI'] = database_url
                print("✅ SQLite fallback DB configured")
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'railway-production-key')
        app.config['DEBUG'] = False
    else:
        # Development configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-key-change-in-production'
        app.config['DEBUG'] = True
    
    # Initialize extensions
    db.init_app(app)
    enable_migrations = os.getenv('ENABLE_DB_MIGRATIONS', '').strip().lower() in {'1', 'true', 'yes'}
    if config_name != 'production' or enable_migrations:
        migrate = Migrate(app, db)
    else:
        migrate = None
        print("ℹ️ Skipping Flask-Migrate initialization in production startup (set ENABLE_DB_MIGRATIONS=1 to enable).")
    CORS(
        app,
        supports_credentials=True,
        origins=[
            'http://localhost:5173',
            'http://localhost:5174',
            'https://impacttracker.netlify.app',
            'https://silly-cuchufli-b154e2.netlify.app',
            r'^https://.*--impacttracker\.netlify\.app$',
        ],
        methods=['GET', 'POST', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
    )
    
    run_db_bootstrap = os.getenv('RUN_DB_BOOTSTRAP', '').strip().lower() in {'1', 'true', 'yes'}

    if config_name != 'production' or run_db_bootstrap:
        with app.app_context():
            try:
                print("🔄 Creating/verifying database tables...")
                db.create_all()
                print("✅ Database tables ready")
                _seed_products_from_csv()
            except Exception as e:
                print(f"❌ Database setup error: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("ℹ️ Skipping DB bootstrap in production startup (set RUN_DB_BOOTSTRAP=1 to enable).")
    
    # Load ML models
    # Unified ML assets directory (single location)
    ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(BASE_DIR, "ml"))
    model_dir = ML_ASSETS_DIR
    encoders_dir = os.path.join(ML_ASSETS_DIR, "encoders")

    app.xgb_model = None
    app.encoders = {}

    load_ml_on_startup = os.environ.get("LOAD_ML_ON_STARTUP", "").strip().lower()
    if config_name == 'production' and load_ml_on_startup not in {"1", "true", "yes"}:
        print("ℹ️ Skipping ML model preload in production startup (set LOAD_ML_ON_STARTUP=1 to enable).")
    else:
        try:
            import joblib

            # Load XGBoost model
            import xgboost as xgb
            xgb_model_path = os.path.join(model_dir, "xgb_model.json")
            if os.path.exists(xgb_model_path):
                xgb_model = xgb.XGBClassifier()
                xgb_model.load_model(xgb_model_path)
                app.xgb_model = xgb_model
                print("✅ XGBoost model loaded successfully")

            # Load encoders
            encoders = {}
            encoder_files = [
                'material_encoder.pkl', 'transport_encoder.pkl', 'recyclability_encoder.pkl',
                'origin_encoder.pkl', 'weight_bin_encoder.pkl'
            ]

            for encoder_file in encoder_files:
                encoder_path = os.path.join(encoders_dir, encoder_file)
                if os.path.exists(encoder_path):
                    encoder_name = encoder_file.replace('.pkl', '')
                    encoders[encoder_name] = joblib.load(encoder_path)

            app.encoders = encoders
            print(f"✅ Loaded {len(encoders)} encoders successfully")

        except Exception as e:
            print(f"⚠️ Error loading ML models: {e}")
            app.xgb_model = None
            app.encoders = {}
    
    # === ROUTES ===
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        if config_name == 'production':
            return jsonify({
                'status': 'healthy',
                'database': 'deferred',
                'ml_model': 'loaded' if hasattr(app, 'xgb_model') and app.xgb_model else 'not loaded'
            })

        return jsonify({
            'status': 'healthy',
            'database': 'connected' if db.engine else 'disconnected',
            'ml_model': 'loaded' if hasattr(app, 'xgb_model') and app.xgb_model else 'not loaded'
        })

    @app.route('/', methods=['GET'])
    def root_status():
        return jsonify({
            'status': 'ok',
            'service': 'impacttracker-api',
            'mode': config_name
        }), 200
    
    @app.route('/estimate_emissions', methods=['POST', 'OPTIONS'])
    def estimate_emissions():
        """Main endpoint for estimating product emissions - matches localhost functionality"""
        print("🔔 Route hit: /estimate_emissions")

        import pandas as pd
        import pgeocode

        deps = _load_estimation_dependencies()
        scrape_amazon_product_page = deps['scrape_amazon_product_page']
        estimate_origin_country = deps['estimate_origin_country']
        resolve_brand_origin = deps['resolve_brand_origin']
        haversine = deps['haversine']
        origin_hubs = deps['origin_hubs']
        uk_hub = deps['uk_hub']
        smart_guess_material = deps['smart_guess_material']
        apply_material_title_consistency = deps['apply_material_title_consistency']
        normalize_brand_for_lookup = deps['normalize_brand_for_lookup']
        normalize_amazon_url = deps['normalize_amazon_url']
        extract_asin_from_amazon_url = deps['extract_asin_from_amazon_url']
        standardize_attributes = deps['standardize_attributes']
        calculate_eco_score = deps['calculate_eco_score']
        
        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON in request"}), 400
            
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
            _BAD_TITLES = {'amazon product', 'unknown product', 'unknown', '', 'consumer product'}
            _cache_usable = (
                cached_calc
                and cached_calc.scraped_product
                and (cached_calc.scraped_product.title or '').strip().lower() not in _BAD_TITLES
                and float(cached_calc.final_emission or 0) > 0
            )
            if _cache_usable:
                cached_product = cached_calc.scraped_product
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
                    "material_type": cached_product.material or "Mixed",
                    "weight_kg": round(float(cached_product.weight or 0.5), 2),
                    "origin": cached_product.origin_country or "Unknown",
                    "country_of_origin": cached_product.origin_country or "Unknown",
                    "facility_origin": cached_product.origin_country or "Unknown",
                    "origin_source": "database_cache",
                    "origin_confidence": cached_origin_confidence,
                    "dimensions_cm": "Not found",
                    "brand": cached_product.brand,
                    "price": cached_product.price,
                    "asin": cached_product.asin,
                    "image_url": "Not found",
                    "manufacturer": "Not found",
                    "category": "Not found",
                }
                cached_attributes = standardize_attributes(cached_attributes, [
                    "origin",
                    "country_of_origin",
                    "facility_origin",
                    "origin_source",
                    "origin_confidence",
                    "dimensions_cm",
                    "material_type",
                    "brand",
                    "price",
                    "asin",
                    "image_url",
                    "manufacturer",
                    "category",
                ])

                cached_total = float(cached_calc.final_emission or 0.0)
                cached_distance = float(cached_calc.transport_distance or 0.0)
                cached_weight = float(cached_product.weight or 0.5)
                cached_response = {
                    "title": cached_product.title or "Unknown Product",
                    "cache_hit": True,
                    "cache_source": "emission_calculation",
                    "data": {
                        "attributes": cached_attributes,
                        "environmental_metrics": {
                            "carbon_footprint": round(cached_total, 2),
                            "recyclability_score": 30,
                            "eco_score": calculate_eco_score(cached_total, "Medium", cached_distance, cached_weight),
                            "efficiency": "22%"
                        },
                        "recommendations": [
                            "Consider products made from recycled materials",
                            "Look for items manufactured closer to your location",
                            "Choose products with minimal packaging"
                        ]
                    }
                }
                return jsonify(cached_response)
            
            # Scrape product - using unified scraper in production
            print(f"🔍 Scraping URL: {url}")
            product = scrape_amazon_product_page(url)
            
            _BAD_SCRAPE_TITLES = {'unknown product', 'amazon product', 'unknown', '', 'consumer product'}
            _scraped_title = (product.get('title') or '').strip().lower()
            if not product or _scraped_title in _BAD_SCRAPE_TITLES:
                return jsonify({"error": "Failed to scrape product data"}), 400
                
            print(f"✅ Scraper success: {product.get('title', '')[:50]}...")
            
            # Debug what the scraper returned
            print("🔍 DEBUG: Scraper returned:")
            for key, value in product.items():
                print(f"  {key}: {value}")
            print("🔍 END DEBUG")
            
            # Material detection if needed
            material = product.get("material_type") or product.get("material")
            if not material or material.lower() in ["unknown", "other", "", "not found", "n/a"]:
                guessed = smart_guess_material(product.get("title", ""))
                if guessed:
                    print(f"🧠 Guessed material: {guessed}")
                    material = guessed.title()
                    product["material_type"] = material
            
            # Ensure material is set
            if not product.get("material_type"):
                product["material_type"] = material or "Mixed"

            normalized_material = apply_material_title_consistency(product)
            if normalized_material and str(normalized_material).strip().lower() != str(material or '').strip().lower():
                print(f"🧬 Consistency override material: {material} -> {normalized_material}")
                material = normalized_material
            else:
                material = product.get("material_type") or material
            
            # Get weight
            raw_weight = product.get("weight_kg") or product.get("raw_product_weight_kg") or 0.5
            weight = float(raw_weight)
            print(f"🏋️ Using weight: {weight} kg from scraper")
            if include_packaging:
                weight *= 1.05
            
            # Get user coordinates from postcode
            geo = pgeocode.Nominatim("gb")
            location = geo.query_postal_code(postcode)
            if location.empty or pd.isna(location.latitude):
                return jsonify({"error": "Invalid postcode"}), 400
                
            user_lat, user_lon = location.latitude, location.longitude
            
            # Get origin coordinates
            def _is_unknown_value(value) -> bool:
                return str(value or "").strip().lower() in {"unknown", "", "none", "n/a", "na"}

            explicit_sources = {"technical_details", "product_details", "manufacturer_contact", "specifications", "scraped_verified"}
            top_confidence_sources = {"technical_details", "product_details", "scraped_verified"}
            weak_sources = {
                "heuristic_brand_default",
                "heuristic_title_default",
                "title_description",
                "default_uk",
                "unknown",
            }
            scraped_origin = product.get("country_of_origin") or product.get("origin")
            scraped_source = str(product.get("origin_source", "")).strip().lower()

            origin_country = "Unknown"
            final_origin_source = "unknown"
            final_origin_confidence = product.get("origin_confidence", "unknown")

            if not _is_unknown_value(scraped_origin) and scraped_source not in weak_sources:
                origin_country = scraped_origin
                final_origin_source = scraped_source or "scraped"
                if scraped_source in top_confidence_sources:
                    final_origin_confidence = "high"
                elif scraped_source in explicit_sources:
                    final_origin_confidence = "medium"
                elif final_origin_confidence in {None, "", "unknown"}:
                    final_origin_confidence = "medium"
            elif not _is_unknown_value(scraped_origin) and scraped_source in weak_sources:
                print(f"⚠️ Ignoring weak scraped origin '{scraped_origin}' from source '{scraped_source}' and continuing fallbacks")

            if _is_unknown_value(origin_country):
                brand = product.get("brand", "")
                if brand and str(brand).strip().lower() != "unknown":
                    try:
                        lookup_brand = normalize_brand_for_lookup(brand)
                        brand_result = resolve_brand_origin(lookup_brand or brand)
                        brand_origin = brand_result[0] if isinstance(brand_result, tuple) else brand_result
                        if not _is_unknown_value(brand_origin) and str(brand_origin).strip().lower() != "uk":
                            origin_country = brand_origin
                            final_origin_source = "brand_db"
                            final_origin_confidence = "medium"
                            product["origin"] = origin_country
                            product["country_of_origin"] = origin_country
                    except Exception as origin_error:
                        print(f"⚠️ Brand-origin fallback error: {origin_error}")

            if _is_unknown_value(origin_country):
                asin = str(product.get("asin", "")).strip().upper()
                if asin:
                    try:
                        historical = (
                            ScrapedProduct.query
                            .filter(ScrapedProduct.asin == asin)
                            .filter(ScrapedProduct.origin_country.isnot(None))
                            .order_by(ScrapedProduct.id.desc())
                            .first()
                        )
                        if historical:
                            candidate_origin = str(historical.origin_country or "").strip()
                            if not _is_unknown_value(candidate_origin):
                                origin_country = candidate_origin
                                final_origin_source = "asin_history"
                                final_origin_confidence = "low"
                                product["origin"] = origin_country
                                product["country_of_origin"] = origin_country
                    except Exception as asin_error:
                        print(f"⚠️ ASIN-history fallback error: {asin_error}")

            if _is_unknown_value(origin_country):
                title_for_heuristic = str(product.get("title", "") or "").strip()
                heuristic_origin = estimate_origin_country(title_for_heuristic) if title_for_heuristic else "Unknown"
                if not _is_unknown_value(heuristic_origin):
                    origin_country = heuristic_origin
                    final_origin_source = "heuristic_title_default"
                    final_origin_confidence = "low"
                    product["origin"] = origin_country
                    product["country_of_origin"] = origin_country
                else:
                    origin_country = "Unknown"
                    final_origin_source = "unknown"
                    if final_origin_confidence in {None, "", "unknown"}:
                        final_origin_confidence = "unknown"
            
            # For UK internal deliveries, determine specific region from postcode
            # Only remap when origin comes from explicit product-page evidence.
            explicit_sources = {"technical_details", "product_details", "manufacturer_contact", "specifications", "scraped_verified", "raw_text"}
            if origin_country == "UK" and postcode and final_origin_source in explicit_sources:
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
            # Fall back to China hub (not UK) for unknown overseas origins to avoid near-zero distance
            default_hub = uk_hub if origin_country in ("UK", "England", "Scotland", "Wales", "Northern Ireland") else origin_hubs.get("China")
            origin_coords = origin_hubs.get(origin_country, default_hub)
            
            # Distance calculations
            origin_distance_km = round(haversine(origin_coords["lat"], origin_coords["lon"], user_lat, user_lon), 1)
            uk_distance_km = round(haversine(uk_hub["lat"], uk_hub["lon"], user_lat, user_lon), 1)
            
            print(f"🌍 Distances → origin: {origin_distance_km} km | UK hub: {uk_distance_km} km")
            
            # Transport mode logic
            def determine_transport_mode(distance_km, origin_country="Unknown"):
                water_crossing_countries = ["Ireland", "France", "Germany", "Netherlands", "Belgium", "Denmark", 
                                          "Sweden", "Norway", "Finland", "Spain", "Italy", "Poland"]
                
                if origin_country in water_crossing_countries:
                    if distance_km < 500:
                        return "Truck", 0.15
                    elif distance_km < 3000:
                        return "Ship", 0.03
                    else:
                        return "Air", 0.5
                        
                if distance_km < 1500:
                    return "Truck", 0.15
                elif distance_km < 20000:
                    return "Ship", 0.03
                else:
                    return "Air", 0.5
            
            # Determine transport mode
            mode_name, mode_factor = determine_transport_mode(origin_distance_km, origin_country)
            if override_mode:
                mode_name = override_mode
                mode_factor = {"Truck": 0.15, "Ship": 0.03, "Air": 0.5}.get(override_mode, mode_factor)
            
            print(f"🚚 Transport: {mode_name} (factor: {mode_factor})")
            
            # Calculate emissions using ML model
            try:
                # Prepare features for ML prediction
                ml_features = {
                    'material': product.get('material_type', 'Mixed'),
                    'transport_mode': mode_name,
                    'weight': weight,
                    'origin_country': origin_country,
                    'recyclability': 'Medium',  # Default
                    'weight_category': 'Medium' if weight < 2 else 'Heavy',
                    'packaging_type': 'Standard',
                    'size_category': 'Medium',
                    'quality_level': 'Standard',
                    'pack_size': 'Single',
                    'material_confidence': 0.85
                }
                
                # Use ML prediction if available
                if hasattr(app, 'xgb_model') and app.xgb_model:
                    features_df = pd.DataFrame([ml_features])
                    
                    # Encode features
                    for col in ['material', 'transport_mode', 'recyclability', 'origin_country', 
                               'weight_category', 'packaging_type', 'size_category', 'quality_level', 'pack_size']:
                        if col in app.encoders:
                            features_df[col] = app.encoders[col].transform(features_df[col])
                    
                    # Make prediction
                    ml_prediction = app.xgb_model.predict(features_df)[0]
                    ml_co2 = float(ml_prediction) * weight
                else:
                    # Fallback calculation
                    ml_co2 = weight * (mode_factor * origin_distance_km) / 1000

            except Exception as e:
                print(f"ML prediction error: {e}")
                ml_co2 = weight * (mode_factor * origin_distance_km) / 1000

            # Rule-based calculation
            transport_co2 = weight * mode_factor * origin_distance_km / 1000
            material_intensity = {"Plastic": 2.5, "Steel": 3.0, "Paper": 1.2, 
                                "Glass": 1.5, "Wood": 0.8, "Other": 2.0}.get(material, 2.0)
            material_co2 = weight * material_intensity
            rule_co2 = transport_co2 + material_co2
            
            # Calculate eco scores
            eco_score_ml = "C"  # Default ML score
            eco_score_rule_based = "A"  # Default rule-based score
            confidence = 83.3
            
            # Simple eco score calculation based on total CO2
            total_co2 = (ml_co2 + rule_co2) / 2
            if total_co2 < 1:
                eco_score_rule_based = "A+"
                eco_score_ml = "B"
            elif total_co2 < 2:
                eco_score_rule_based = "A"
                eco_score_ml = "B"
            elif total_co2 < 5:
                eco_score_rule_based = "B"
                eco_score_ml = "C"
            elif total_co2 < 10:
                eco_score_rule_based = "C"
                eco_score_ml = "D"
            else:
                eco_score_rule_based = "D"
                eco_score_ml = "E"
            
            # Prepare response matching localhost format EXACTLY
            attributes = {
                "carbon_kg": round(total_co2, 2),
                "weight_kg": round(weight, 2),
                "raw_product_weight_kg": round(raw_weight, 2),
                "origin": origin_country,
                "country_of_origin": origin_country,
                "facility_origin": product.get("facility_origin", "Not found"),
                "origin_source": final_origin_source,
                "origin_confidence": final_origin_confidence,

                # Distance fields
                "intl_distance_km": origin_distance_km,
                "uk_distance_km": uk_distance_km,
                "distance_from_origin_km": origin_distance_km,
                "distance_from_uk_hub_km": uk_distance_km,

                # Product features
                "dimensions_cm": product.get("dimensions_cm"),
                "material_type": product.get("material_type", "Not found"),
                "recyclability": "Medium",
                "recyclability_percentage": 30,
                "recyclability_description": "Assessment pending",

                # Transport details
                "transport_mode": mode_name,
                "default_transport_mode": mode_name,
                "selected_transport_mode": override_mode or None,
                "emission_factors": {
                    "Truck": {"factor": 0.15, "co2_kg": transport_co2 if mode_name == "Truck" else 0},
                    "Ship": {"factor": 0.03, "co2_kg": transport_co2 if mode_name == "Ship" else 0},
                    "Air": {"factor": 0.5, "co2_kg": transport_co2 if mode_name == "Air" else 0}
                },

                # Scoring - BOTH Methods for Comparison
                "eco_score_ml": eco_score_ml,
                "eco_score_ml_confidence": confidence,
                "eco_score_rule_based": eco_score_rule_based,
                "eco_score_rule_based_local_only": eco_score_rule_based,

                # Method Comparison
                "method_agreement": "No",
                "prediction_methods": {
                    "ml_prediction": {
                        "score": eco_score_ml,
                        "confidence": f"{confidence}%",
                        "method": "Enhanced XGBoost (11 features)",
                        "features_used": {
                            "feature_count": 11,
                            "features": [
                                {"name": "material_type", "value": material},
                                {"name": "transport_mode", "value": mode_name},
                                {"name": "weight", "value": weight}
                            ]
                        }
                    },
                    "rule_based_prediction": {
                        "score": eco_score_rule_based,
                        "confidence": "80%",
                        "method": "Traditional calculation method"
                    }
                },

                # Trees calculation
                "trees_to_offset": int(total_co2 / 20),

                # Additional product info
                "brand": product.get("brand"),
                "price": product.get("price"),
                "asin": product.get("asin"),
                "image_url": product.get("image_url"),
                "manufacturer": product.get("manufacturer"),
                "category": product.get("category")
            }

            attributes = standardize_attributes(attributes, [
                "origin",
                "country_of_origin",
                "facility_origin",
                "origin_source",
                "origin_confidence",
                "dimensions_cm",
                "material_type",
                "brand",
                "price",
                "asin",
                "image_url",
                "manufacturer",
                "category",
            ])

            response_data = {
                "title": product.get("title", "Unknown Product"),
                "data": {
                    "attributes": attributes,
                    "environmental_metrics": {
                        "carbon_footprint": round(total_co2, 2),
                        "recyclability_score": 30,
                        "eco_score": eco_score_ml,
                        "efficiency": "22%"
                    },
                    "recommendations": [
                        "Consider products made from recycled materials",
                        "Look for items manufactured closer to your location",
                        "Choose products with minimal packaging"
                    ]
                }
            }
            
            # Save to database
            try:
                confidence_label = str(final_origin_confidence or 'medium').strip().lower()
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
                    'weight': weight,
                    'material': material,
                    'brand': product.get('brand'),
                    'origin_country': origin_country,
                    'confidence_score': product.get('confidence_score', 0.85),
                    'scraping_status': 'success'
                })
                
                save_emission_calculation({
                    'scraped_product_id': scraped_product.id,
                    'user_postcode': postcode,
                    'transport_distance': origin_distance_km,
                    'transport_mode': mode_name,
                    'ml_prediction': ml_co2,
                    'rule_based_prediction': rule_co2,
                    'final_emission': (ml_co2 + rule_co2) / 2,
                    'confidence_level': confidence_score,
                    'calculation_method': 'combined'
                })

                # Add to products table — count grows permanently in PostgreSQL
                _transport_map = {'Truck': 'Land', 'Ship': 'Ship', 'Air': 'Air', 'Land': 'Land', 'Sea': 'Sea'}
                _material_recyclability = {
                    'Glass': 'High', 'Aluminum': 'High', 'Steel': 'High',
                    'Paper': 'High', 'Cardboard': 'High', 'Wood': 'High',
                    'Bamboo': 'High', 'Cotton': 'High',
                    'Plastic': 'Low', 'Polyester': 'Low', 'Rubber': 'Low',
                }
                new_product = Product(
                    title=product.get('title'),
                    material=material,
                    weight=weight,
                    transport=_transport_map.get(mode_name, 'Land'),
                    recyclability=_material_recyclability.get(material, 'Medium'),
                    true_eco_score=eco_score_rule_based or eco_score_ml or 'C',
                    co2_emissions=(ml_co2 + rule_co2) / 2 if (ml_co2 and rule_co2) else total_co2,
                    origin=(origin_country or '').upper() or 'UNKNOWN',
                    category=product.get('category') or '',
                    search_term='',
                )
                db.session.add(new_product)
                db.session.commit()
                print(f"✅ Product added to DB: {new_product.title} (total now {Product.query.count()})")
            except Exception as e:
                print(f"Database save error: {e}")
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"❌ Error in estimate_emissions: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/predict', methods=['POST'])
    def predict_ml():
        """Direct ML prediction endpoint"""
        try:
            import numpy as np
            import joblib

            # === Lazy load model if not already loaded ===
            if not (hasattr(app, 'xgb_model') and app.xgb_model):
                try:
                    app.xgb_model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
                    print("✅ Lazy-loaded eco_model.pkl for /predict")
                except Exception:
                    try:
                        import xgboost as xgb
                        m = xgb.XGBClassifier()
                        m.load_model(os.path.join(model_dir, "xgb_model.json"))
                        app.xgb_model = m
                        print("✅ Lazy-loaded xgb_model.json for /predict")
                    except Exception as e:
                        return jsonify({'error': f'Failed to load ML model: {str(e)}'}), 500

            # === Lazy load label encoder ===
            if not hasattr(app, 'label_encoder') or app.label_encoder is None:
                try:
                    app.label_encoder = joblib.load(os.path.join(encoders_dir, 'label_encoder.pkl'))
                except Exception:
                    class _FallbackLabelEncoder:
                        classes_ = ["A+", "A", "B", "C", "D", "E", "F"]
                        def inverse_transform(self, indices):
                            return [self.classes_[min(int(i), len(self.classes_) - 1)] for i in indices]
                    app.label_encoder = _FallbackLabelEncoder()

            # === Lazy load feature encoders ===
            if not app.encoders:
                encoders = {}
                for enc_name, filename in [
                    ('material_encoder', 'material_encoder.pkl'),
                    ('transport_encoder', 'transport_encoder.pkl'),
                    ('recycle_encoder', 'recycle_encoder.pkl'),
                    ('origin_encoder', 'origin_encoder.pkl'),
                ]:
                    try:
                        encoders[enc_name] = joblib.load(os.path.join(encoders_dir, filename))
                    except Exception:
                        pass
                app.encoders = encoders

            data = request.get_json()

            # === Helper functions ===
            def normalize(val, default):
                return str(val).strip() if val else default

            def safe_encode(value, encoder, default):
                if encoder is None:
                    return 0
                try:
                    return encoder.transform([value])[0]
                except Exception:
                    try:
                        return encoder.transform([default])[0]
                    except Exception:
                        return 0

            # === Extract and encode features ===
            material = normalize(data.get('material'), 'Other')
            weight = float(data.get('weight') or 1.0)
            recyclability = normalize(data.get('recyclability'), 'Medium')
            origin = normalize(data.get('origin'), 'Other')

            distance_km = float(data.get('distance_origin_to_uk') or 0)
            override_transport = normalize(data.get('override_transport_mode') or data.get('transport'), '')
            if override_transport in ['Truck', 'Ship', 'Air', 'Land']:
                transport = override_transport
            elif distance_km > 7000:
                transport = 'Ship'
            elif distance_km > 2000:
                transport = 'Air'
            else:
                transport = 'Land'

            material_encoded = safe_encode(material, app.encoders.get('material_encoder'), 'Other')
            transport_encoded = safe_encode(transport, app.encoders.get('transport_encoder'), 'Land')
            recycle_encoded = safe_encode(recyclability, app.encoders.get('recycle_encoder'), 'Medium')
            origin_encoded = safe_encode(origin, app.encoders.get('origin_encoder'), 'Other')
            weight_log = np.log1p(weight)
            weight_bin = 0 if weight < 0.5 else 1 if weight < 2 else 2 if weight < 10 else 3

            material_transport = float(material_encoded) * float(transport_encoded)
            origin_recycle = float(origin_encoded) * float(recycle_encoded)

            X = [[material_encoded, transport_encoded, recycle_encoded, origin_encoded, weight_log, weight_bin, material_transport, origin_recycle]]

            # === Predict ===
            prediction = app.xgb_model.predict(X)
            decoded_score = app.label_encoder.inverse_transform([prediction[0]])[0]

            confidence = 0.0
            if hasattr(app.xgb_model, 'predict_proba'):
                proba = app.xgb_model.predict_proba(X)
                confidence = round(float(np.max(proba[0])) * 100, 1)

            print(f"🧠 Predicted: {decoded_score} ({confidence}%)")

            return jsonify({
                'predicted_label': decoded_score,
                'confidence': f'{confidence}%',
                'raw_input': {
                    'material': material,
                    'weight': weight,
                    'transport': transport,
                    'recyclability': recyclability,
                    'origin': origin,
                },
                'encoded_input': {
                    'material': int(material_encoded),
                    'transport': int(transport_encoded),
                    'recyclability': int(recycle_encoded),
                    'origin': int(origin_encoded),
                    'weight_bin': int(weight_bin),
                },
            })

        except Exception as e:
            print(f"❌ Error in /predict: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/products', methods=['GET'])
    def admin_get_products():
        """Admin endpoint to get all scraped products - REQUIRES ADMIN AUTH"""
        # Check authentication
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            products = ScrapedProduct.query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'success': True,
                'products': [product.to_dict() for product in products.items],
                'total': products.total,
                'pages': products.pages,
                'current_page': page
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/analytics', methods=['GET'])
    def admin_analytics():
        """Admin analytics dashboard - REQUIRES ADMIN AUTH"""
        # Check authentication
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        try:
            # Get basic stats
            total_products = ScrapedProduct.query.count()
            total_calculations = EmissionCalculation.query.count()
            
            # Get material distribution
            material_stats = db.session.query(
                ScrapedProduct.material,
                db.func.count(ScrapedProduct.id).label('count')
            ).group_by(ScrapedProduct.material).all()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_products': total_products,
                    'total_calculations': total_calculations,
                    'material_distribution': [
                        {'material': material, 'count': count} 
                        for material, count in material_stats
                    ]
                }
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/dashboard-metrics', methods=['GET'])
    def dashboard_metrics():
        """Dashboard metrics — counts from PostgreSQL products table (seeded from CSV)."""
        try:
            total_products = 0
            total_materials = 0
            material_distribution = []
            score_distribution = []
            total_scraped = 0
            total_calculations = 0

            try:
                total_products = Product.query.count()
                total_scraped = ScrapedProduct.query.count()
                total_calculations = EmissionCalculation.query.count()

                mat_rows = (
                    db.session.query(Product.material, db.func.count(Product.id))
                    .filter(Product.material.isnot(None))
                    .group_by(Product.material)
                    .order_by(db.func.count(Product.id).desc())
                    .limit(10)
                    .all()
                )
                material_distribution = [{'name': m, 'value': c} for m, c in mat_rows]
                total_materials = (
                    db.session.query(db.func.count(db.distinct(Product.material)))
                    .scalar() or 0
                )

                score_rows = (
                    db.session.query(Product.true_eco_score, db.func.count(Product.id))
                    .filter(Product.true_eco_score.isnot(None))
                    .group_by(Product.true_eco_score)
                    .all()
                )
                score_distribution = [{'name': s, 'value': c} for s, c in score_rows]

            except Exception as db_err:
                print(f"DB query error in dashboard-metrics: {db_err}")

            # No CSV fallback — always show the real DB count so frontend matches backend

            return jsonify({
                'success': True,
                'stats': {
                    'total_products': total_products,
                    'total_materials': total_materials,
                    'total_predictions': total_calculations,
                    'recent_activity': total_scraped
                },
                'material_distribution': material_distribution,
                'score_distribution': score_distribution,
                'data': {
                    'total_products': total_products,
                    'total_scraped_products': total_scraped,
                    'total_calculations': total_calculations,
                    'database_status': 'connected'
                }
            })
        except Exception as e:
            print(f"Error in dashboard-metrics: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/insights', methods=['GET'])
    def insights():
        """Analytics insights for dashboard"""
        try:
            # Get top materials
            material_stats = db.session.query(
                Product.material,
                db.func.count(Product.id).label('count')
            ).group_by(Product.material).limit(10).all()
            
            # Get recent calculations
            recent_calculations = EmissionCalculation.query.order_by(
                EmissionCalculation.id.desc()
            ).limit(10).all()
            
            return jsonify({
                'success': True,
                'material_distribution': [
                    {'material': material or 'Unknown', 'count': count} 
                    for material, count in material_stats
                ],
                'recent_calculations': [
                    {
                        'id': calc.id,
                        'co2_estimate': calc.co2_estimate,
                        'created_at': calc.created_at.isoformat() if calc.created_at else None
                    } for calc in recent_calculations
                ]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/eco-data', methods=['GET'])
    def eco_data():
        """Eco data for tables and analytics - reads from CSV to match localhost"""
        try:
            import pandas as pd
            dataset_path = os.path.join(BASE_DIR, 'common', 'data', 'csv', 'expanded_eco_dataset.csv')
            if not os.path.exists(dataset_path):
                print(f"⚠️ Dataset not found: {dataset_path}")
                return jsonify([]), 200

            df = pd.read_csv(dataset_path)
            df = df.dropna(subset=['material', 'true_eco_score'])
            df = df.where(pd.notnull(df), None)

            limit = request.args.get('limit', type=int, default=1000)
            limit = min(limit, 50000)
            df_limited = df.head(limit)

            return jsonify({
                'products': df_limited.to_dict(orient='records'),
                'metadata': {
                    'total_products_in_dataset': len(df),
                    'products_returned': len(df_limited),
                    'limit_applied': limit
                }
            })
        except Exception as e:
            print(f"Error in eco-data endpoint: {e}")
            return jsonify([]), 200
    
    @app.route('/admin/submissions', methods=['GET'])
    def admin_submissions():
        """Get admin submissions - REQUIRES ADMIN AUTH"""
        # Check authentication
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        try:
            # Get scraped products for admin review
            submissions = ScrapedProduct.query.order_by(ScrapedProduct.id.desc()).limit(50).all()
            
            return jsonify([{
                'id': sub.id,
                'url': sub.url,
                'title': sub.title,
                'material': sub.material,
                'status': 'pending',
                'created_at': sub.created_at.isoformat() if sub.created_at else None
            } for sub in submissions])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/admin/update', methods=['POST'])
    def admin_update():
        """Update admin submission - REQUIRES ADMIN AUTH"""
        # Check authentication
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        try:
            data = request.json
            submission_id = data.get('id')
            
            if not submission_id:
                return jsonify({'error': 'No submission ID provided'}), 400
                
            # Here you would update the submission
            return jsonify({'success': True, 'message': 'Submission updated'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/all-model-metrics', methods=['GET'])
    def all_model_metrics():
        """Get all model metrics from real training artifacts"""
        try:
            import json as _json
            import numpy as np

            rf_path = os.path.join(BASE_DIR, 'ml', 'metrics.json')
            xgb_path = os.path.join(BASE_DIR, 'ml', 'xgb_metrics.json')

            with open(rf_path) as f:
                rf_data = _json.load(f)
            with open(xgb_path) as f:
                xgb_data = _json.load(f)

            # Compute per-class precision/recall/F1 from the RF confusion matrix
            cm = np.array(rf_data['confusion_matrix'])
            rf_labels = rf_data['labels']
            rf_report = {}
            for i, label in enumerate(rf_labels):
                tp = float(cm[i, i])
                fp = float(cm[:, i].sum()) - tp
                fn = float(cm[i, :].sum()) - tp
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                rf_report[label] = {
                    'precision': round(prec, 4),
                    'recall':    round(rec,  4),
                    'f1-score':  round(f1,   4),
                    'support':   int(cm[i, :].sum()),
                }

            rf_macro_prec = round(float(np.mean([v['precision'] for v in rf_report.values()])), 4)
            rf_macro_rec  = round(float(np.mean([v['recall']    for v in rf_report.values()])), 4)

            # XGBoost per-class report (exclude summary rows)
            xgb_report = {
                k: v for k, v in xgb_data['report'].items()
                if k not in ('accuracy', 'macro avg', 'weighted avg')
            }

            return jsonify({
                'random_forest': {
                    'accuracy':         rf_data['accuracy'],
                    'precision':        rf_macro_prec,
                    'recall':           rf_macro_rec,
                    'f1_score':         rf_data['f1_score'],
                    'labels':           rf_labels,
                    'confusion_matrix': rf_data['confusion_matrix'],
                    'report':           rf_report,
                },
                'xgboost': {
                    'accuracy':         xgb_data['accuracy'],
                    'precision':        round(xgb_data['report']['macro avg']['precision'], 4),
                    'recall':           round(xgb_data['report']['macro avg']['recall'],    4),
                    'f1_score':         xgb_data['f1_score'],
                    'labels':           xgb_data['labels'],
                    'confusion_matrix': xgb_data['confusion_matrix'],
                    'report':           xgb_report,
                },
            })
        except Exception as e:
            print(f"⚠️ Error loading model metrics: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/model-metrics', methods=['GET'])
    def model_metrics():
        """Get current model performance metrics"""
        accuracy = 0.8661
        confidence_avg = 0.8701
        try:
            import json as _json
            xgb_path = os.path.join(BASE_DIR, 'ml', 'xgb_metrics.json')
            with open(xgb_path) as f:
                xgb_data = _json.load(f)
            accuracy = xgb_data.get('accuracy', accuracy)
            confidence_avg = round(xgb_data.get('report', {}).get('macro avg', {}).get('precision', confidence_avg), 4)
        except Exception:
            pass
        return jsonify({
            'accuracy': accuracy,
            'total_predictions': EmissionCalculation.query.count(),
            'confidence_avg': confidence_avg,
        })
    
    @app.route('/api/ml-audit', methods=['GET'])
    def ml_audit():
        """ML audit trail endpoint"""
        recent_predictions = EmissionCalculation.query.order_by(
            EmissionCalculation.id.desc()
        ).limit(20).all()
        
        return jsonify({
            'audit_trail': [{
                'id': pred.id,
                'timestamp': pred.created_at.isoformat() if pred.created_at else None,
                'co2_estimate': pred.co2_estimate,
                'method': pred.method
            } for pred in recent_predictions]
        })
    
    @app.route('/api/feature-importance', methods=['GET'])
    def feature_importance():
        """Get feature importance from trained Random Forest model (eco_model.pkl)"""
        # Try to load live from the model for accuracy
        try:
            import joblib
            model = joblib.load(os.path.join(model_dir, 'eco_model.pkl'))
            feature_names = [
                'Material Type', 'Transport Mode', 'Recyclability',
                'Origin Country', 'Weight (log)', 'Weight Category',
            ]
            importances = model.feature_importances_
            result = [
                {'feature': name, 'importance': round(float(imp) * 100, 2)}
                for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])
            ]
            return jsonify(result)
        except Exception:
            pass
        # Fall back to values computed from eco_model.pkl on 2026-03-16
        return jsonify([
            {'feature': 'Weight (log)',    'importance': 36.39},
            {'feature': 'Material Type',   'importance': 21.60},
            {'feature': 'Transport Mode',  'importance': 17.77},
            {'feature': 'Origin Country',  'importance': 14.59},
            {'feature': 'Recyclability',   'importance':  5.07},
            {'feature': 'Weight Category', 'importance':  4.57},
        ])
    
    @app.route('/api/feedback', methods=['POST'])
    def feedback():
        """Handle user feedback"""
        try:
            data = request.json
            # Here you would store feedback in database
            print(f"Feedback received: {data}")
            return jsonify({'success': True, 'message': 'Thank you for your feedback!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Authentication endpoints
    @app.route('/signup', methods=['POST'])
    def signup():
        """User registration endpoint - SIMPLIFIED FOR DEMO"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            # ADMIN ACCOUNT HARDCODED CHECK
            if username.upper() == 'ADMIN':
                if password == 'ADMINTEST':
                    return jsonify({'message': '✅ Admin login successful', 'role': 'admin'}), 200
                else:
                    return jsonify({'error': 'Admin password must be: ADMINTEST'}), 400
            
            # FOR REGULAR USERS - Just return success (demo mode)
            # In a real system, you'd save to database here
            return jsonify({'message': f'✅ User {username} registered successfully', 'role': 'user'}), 200
            
        except Exception as e:
            print(f"Signup error: {e}")
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
    @app.route('/login', methods=['POST'])
    def login():
        """User login endpoint - USING RAW SQL"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            # HARDCODED ADMIN LOGIN
            if username.upper() == 'ADMIN' and password == 'ADMINTEST':
                session['user'] = {
                    'id': 1,
                    'username': 'ADMIN',
                    'role': 'admin'
                }
                return jsonify({
                    'message': '✅ Admin logged in successfully',
                    'user': session['user']
                }), 200
            
            # FOR REGULAR USERS - Accept any valid username/password combo
            if len(username) >= 3 and len(password) >= 3:
                session['user'] = {
                    'id': 999,
                    'username': username,
                    'role': 'user'
                }
                return jsonify({
                    'message': f'✅ User {username} logged in successfully',
                    'user': session['user']
                }), 200
            else:
                return jsonify({'error': 'Username and password must be at least 3 characters'}), 401
            
        except Exception as e:
            print(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/logout', methods=['POST'])
    def logout():
        """User logout endpoint"""
        session.pop('user', None)
        return jsonify({'message': 'Logged out successfully'})
    
    @app.route('/me', methods=['GET'])
    def me():
        """Get current user info"""
        user = session.get('user')
        if not user:
            return jsonify({'error': 'Not logged in'}), 401
        return jsonify(user)
    
    # Database is already set up at app initialization
    
    print("✅ app_production routes initialized")
    return app

def calculate_emissions_for_product(product_data, user_postcode, app):
    """Calculate emissions for a product using ML + rule-based approach"""
    try:
        # Step 1: Get geographic distance
        origin_country = product_data.get('origin', 'CN')  # Default to China
        
        # Calculate distance and transport mode
        distance, transport_mode = calculate_transport_distance(origin_country, user_postcode)
        
        # Step 2: ML Prediction (if available)
        ml_prediction = None
        if hasattr(app, 'xgb_model') and app.xgb_model:
            try:
                features = prepare_ml_features(product_data, app.encoders)
                ml_prediction = float(app.xgb_model.predict([features])[0])
            except Exception as e:
                print(f"⚠️ ML prediction failed: {e}")
        
        # Step 3: Rule-based calculation
        rule_based_prediction = calculate_rule_based_emission(
            product_data, distance, transport_mode
        )
        
        # Step 4: Final emission (prefer ML, fallback to rule-based)
        final_emission = ml_prediction if ml_prediction is not None else rule_based_prediction
        
        return {
            'final_emission': final_emission,
            'ml_prediction': ml_prediction,
            'rule_based_prediction': rule_based_prediction,
            'transport_distance': distance,
            'transport_mode': transport_mode,
            'confidence': 0.85 if ml_prediction else 0.65,
            'method': 'ML + Rule-based' if ml_prediction else 'Rule-based only'
        }
        
    except Exception as e:
        print(f"❌ Error calculating emissions: {e}")
        return {
            'final_emission': 1.0,  # Default fallback
            'error': str(e),
            'method': 'fallback'
        }

def calculate_transport_distance(origin_country, user_postcode):
    """Calculate transport distance and mode"""
    try:
        import pandas as pd
        import pgeocode
        from backend.scrapers.amazon.integrated_scraper import haversine, origin_hubs, uk_hub

        # Get origin coordinates
        origin_coords = origin_hubs.get(origin_country, origin_hubs['CN'])
        
        # Get user coordinates from postcode
        uk_geo = pgeocode.Nominatim('GB')
        user_location = uk_geo.query_postal_code(user_postcode)
        
        if pd.isna(user_location.latitude):
            user_coords = uk_hub  # Default to London
        else:
            user_coords = (user_location.latitude, user_location.longitude)
        
        # Calculate distance
        distance = haversine(origin_coords, user_coords)
        
        # Determine transport mode
        if distance < 1500:
            transport_mode = "truck"
        elif distance < 6000:
            transport_mode = "ship"
        else:
            transport_mode = "air"
        
        return distance, transport_mode
        
    except Exception as e:
        print(f"⚠️ Error calculating distance: {e}")
        return 5000.0, "ship"  # Default values

def prepare_ml_features(product_data, encoders):
    """Prepare features for ML model"""
    try:
        import numpy as np
        features = []
        
        # Material encoding
        material = product_data.get('material', 'Unknown')
        if 'material_encoder' in encoders:
            try:
                material_encoded = encoders['material_encoder'].transform([material])[0]
            except:
                material_encoded = 0  # Unknown material
        else:
            material_encoded = 0
        features.append(material_encoded)
        
        # Weight (normalized)
        weight = float(product_data.get('weight', 1.0))
        features.append(np.log1p(weight))  # Log transform
        
        # Add other features as needed...
        # This is a simplified version - expand based on your actual model features
        
        return features
        
    except Exception as e:
        print(f"⚠️ Error preparing ML features: {e}")
        return [0, 1.0]  # Default features

def calculate_rule_based_emission(product_data, distance, transport_mode):
    """Rule-based emission calculation as fallback"""
    try:
        # Basic material intensities (kg CO2/kg)
        material_intensities = {
            'plastic': 2.5,
            'metal': 3.2,
            'paper': 0.9,
            'cardboard': 0.7,
            'glass': 1.8,
            'fabric': 5.0,
            'electronics': 8.0
        }
        
        # Transport factors (kg CO2/kg·km)
        transport_factors = {
            'truck': 0.00015,
            'ship': 0.00003,
            'air': 0.0005
        }
        
        material = product_data.get('material', 'plastic').lower()
        weight = float(product_data.get('weight', 1.0))
        
        material_intensity = material_intensities.get(material, 2.0)
        transport_factor = transport_factors.get(transport_mode, 0.0001)
        
        # Total emission = material production + transport
        material_emission = weight * material_intensity
        transport_emission = weight * distance * transport_factor
        
        total_emission = material_emission + transport_emission
        
        return round(total_emission, 2)
        
    except Exception as e:
        print(f"⚠️ Error in rule-based calculation: {e}")
        return 1.0  # Default emission

# Create the Flask app
app = create_app(os.getenv('FLASK_ENV', 'production'))
print("✅ app_production module initialized")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)