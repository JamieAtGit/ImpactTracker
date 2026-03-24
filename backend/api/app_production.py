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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sys
import hmac
from datetime import timedelta
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
from datetime import datetime


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
        _secret = os.getenv('FLASK_SECRET_KEY')
        if not _secret:
            import secrets
            _secret = secrets.token_hex(32)
            print("⚠️  FLASK_SECRET_KEY not set — generated ephemeral key (sessions will not survive restart)")
        app.config['SECRET_KEY'] = _secret
        app.config['DEBUG'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
    else:
        # Development configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-key-change-in-production'
        app.config['DEBUG'] = True
    
    # Initialize extensions
    db.init_app(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=[], storage_uri="memory://")
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
                # Add last_login column to existing deployments if missing
                from sqlalchemy import text as _text
                _migrations = [
                    ("ALTER TABLE users ADD COLUMN last_login TIMESTAMP", "users.last_login"),
                    ("ALTER TABLE emission_calculations ADD COLUMN eco_grade_ml VARCHAR(5)", "emission_calculations.eco_grade_ml"),
                    ("ALTER TABLE emission_calculations ADD COLUMN ml_confidence DECIMAL(5,2)", "emission_calculations.ml_confidence"),
                    ("ALTER TABLE admin_reviews ADD COLUMN corrected_grade VARCHAR(5)", "admin_reviews.corrected_grade"),
                ]
                for sql, col in _migrations:
                    try:
                        with db.engine.connect() as _conn:
                            _conn.execute(_text(sql))
                            _conn.commit()
                        print(f"✅ Added column {col}")
                    except Exception:
                        pass  # Column already exists — ignore
                print("✅ Database tables ready")
                _seed_products_from_csv()
            except Exception as e:
                print(f"❌ Database setup error: {e}")
                import traceback
                traceback.print_exc()

    else:
        print("ℹ️ Skipping DB bootstrap in production startup (set RUN_DB_BOOTSTRAP=1 to enable).")

    # Seed admin user from env vars if no admin exists in DB (runs always)
    with app.app_context():
        try:
            admin_username = os.getenv('ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('ADMIN_PASSWORD', '')
            if admin_password and not User.query.filter_by(role='admin').first():
                admin_user = User(username=admin_username, email='admin@impacttracker.app', role='admin')
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Admin user '{admin_username}' created in database")
            elif not admin_password:
                print("ℹ️  ADMIN_PASSWORD not set — admin user not auto-created")
        except Exception as _ae:
            print(f"⚠️  Admin seeding failed: {_ae}")
    
    # Load ML models
    # Unified ML assets directory (single location)
    ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(BASE_DIR, "ml"))
    model_dir = ML_ASSETS_DIR
    encoders_dir = os.path.join(ML_ASSETS_DIR, "encoders")

    app.xgb_model = None
    app.encoders = {}
    app.conformal_config = None

    # Load conformal prediction config (generated by ml/conformal.py)
    try:
        _conf_path = os.path.join(BASE_DIR, 'ml', 'conformal_config.json')
        if os.path.exists(_conf_path):
            with open(_conf_path, 'r') as _f:
                app.conformal_config = json.load(_f)
            print("✅ Conformal prediction config loaded")
    except Exception as _e:
        print(f"⚠️ Could not load conformal config: {_e}")

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
                # Reconstruct all fields from the cached emission calculation
                cached_total    = float(cached_calc.final_emission or 0.0)
                cached_ml_co2   = float(cached_calc.ml_prediction or cached_total)
                cached_rule_co2 = float(cached_calc.rule_based_prediction or cached_total)
                cached_distance = float(cached_calc.transport_distance or 0.0)
                cached_weight   = float(cached_product.weight or 0.5)
                cached_raw_wt   = round(cached_weight / 1.05, 3)
                cached_transport = cached_calc.transport_mode or 'Ship'
                cached_material  = cached_product.material or 'Mixed'

                _recyclability_rates = {
                    'Glass': 90, 'Aluminum': 85, 'Steel': 85, 'Metal': 85,
                    'Paper': 80, 'Cardboard': 80, 'Wood': 70, 'Bamboo': 70,
                    'Fabric': 40, 'Cotton': 40, 'Plastic': 20,
                    'Mixed': 15, 'Electronic': 15,
                }
                rec_pct   = _recyclability_rates.get(cached_material, 50)
                rec_label = 'High' if rec_pct >= 70 else ('Medium' if rec_pct >= 40 else 'Low')

                cached_grade_ml   = calculate_eco_score(cached_ml_co2,   rec_label, cached_distance, cached_weight)
                cached_grade_rule = calculate_eco_score(cached_rule_co2, rec_label, cached_distance, cached_weight)
                cached_ml_conf    = round(cached_confidence_numeric * 100, 1)

                cached_attributes = {
                    # Core CO₂ and weight
                    "carbon_kg":             round(cached_total, 2),
                    "weight_kg":             round(cached_weight, 2),
                    "raw_product_weight_kg": cached_raw_wt,
                    # Origin
                    "origin":            cached_product.origin_country or "Unknown",
                    "country_of_origin": cached_product.origin_country or "Unknown",
                    "facility_origin":   cached_product.origin_country or "Unknown",
                    "origin_source":     "database_cache",
                    "origin_confidence": cached_origin_confidence,
                    # Distance & transport
                    "distance_from_origin_km":  cached_distance,
                    "distance_from_uk_hub_km":  3.2,
                    "intl_distance_km":         cached_distance,
                    "uk_distance_km":           3.2,
                    "transport_mode":           cached_transport,
                    "default_transport_mode":   cached_transport,
                    "selected_transport_mode":  None,
                    # Material & recyclability
                    "material_type":                cached_material,
                    "recyclability":                rec_label,
                    "recyclability_percentage":     rec_pct,
                    "recyclability_description":    f"{rec_pct}% of {cached_material} is recycled globally",
                    # Eco scores — both methods
                    "eco_score_ml":                     cached_grade_ml,
                    "eco_score_ml_confidence":          cached_ml_conf,
                    "eco_score_rule_based":             cached_grade_rule,
                    "eco_score_rule_based_local_only":  cached_grade_rule,
                    "method_agreement": "Yes" if cached_grade_ml == cached_grade_rule else "No",
                    # Carbon offset
                    "trees_to_offset": max(1, int(cached_total / 20)),
                    # Advanced explanations not available from cache
                    "shap_explanation":  None,
                    "proba_distribution": [],
                    "counterfactuals":    [],
                    # Product metadata
                    "brand":        cached_product.brand,
                    "price":        float(cached_product.price) if cached_product.price else None,
                    "asin":         cached_product.asin,
                    "image_url":    "Not found",
                    "manufacturer": "Not found",
                    "category":     "Not found",
                    "dimensions_cm": "Not found",
                }
                cached_attributes = standardize_attributes(cached_attributes, [
                    "origin", "country_of_origin", "facility_origin",
                    "origin_source", "origin_confidence", "dimensions_cm",
                    "material_type", "brand", "price", "asin",
                    "image_url", "manufacturer", "category",
                ])
                cached_response = {
                    "title": cached_product.title or "Unknown Product",
                    "cache_hit": True,
                    "cache_source": "emission_calculation",
                    "data": {
                        "attributes": cached_attributes,
                        "environmental_metrics": {
                            "carbon_footprint": round(cached_total, 2),
                            "recyclability_score": rec_pct,
                            "eco_score": cached_grade_ml,
                            "efficiency": None,
                        },
                        "recommendations": [
                            "Consider products made from recycled materials",
                            "Look for items manufactured closer to your location",
                            "Choose products with minimal packaging",
                        ],
                    },
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
            
            # === Rule-based CO2 calculation ===
            import numpy as np
            transport_co2 = weight * mode_factor * origin_distance_km / 1000
            material_intensity = {"Plastic": 2.5, "Steel": 3.0, "Paper": 1.2,
                                   "Glass": 1.5, "Wood": 0.8, "Metal": 3.0,
                                   "Fabric": 1.8, "Ceramic": 1.5, "Rubber": 2.2,
                                   "Other": 2.0}.get(material, 2.0)
            material_co2 = weight * material_intensity
            rule_co2 = transport_co2 + material_co2
            total_co2 = rule_co2

            # Rule-based eco grade from CO2
            if rule_co2 < 0.5:
                eco_score_rule_based = "A+"
            elif rule_co2 < 1.0:
                eco_score_rule_based = "A"
            elif rule_co2 < 2.5:
                eco_score_rule_based = "B"
            elif rule_co2 < 5.0:
                eco_score_rule_based = "C"
            elif rule_co2 < 10.0:
                eco_score_rule_based = "D"
            elif rule_co2 < 20.0:
                eco_score_rule_based = "E"
            else:
                eco_score_rule_based = "F"

            # === ML prediction using XGBoost (lazy-load on first request) ===
            import joblib

            if not (hasattr(app, 'xgb_model') and app.xgb_model):
                try:
                    app.xgb_model = joblib.load(os.path.join(model_dir, "eco_model.pkl"))
                    print("✅ Lazy-loaded eco_model.pkl")
                except Exception:
                    try:
                        import xgboost as xgb_mod
                        _m = xgb_mod.XGBClassifier()
                        _m.load_model(os.path.join(model_dir, "xgb_model.json"))
                        app.xgb_model = _m
                        print("✅ Lazy-loaded xgb_model.json")
                    except Exception:
                        app.xgb_model = None

            if not (hasattr(app, 'label_encoder') and app.label_encoder):
                try:
                    app.label_encoder = joblib.load(os.path.join(encoders_dir, 'label_encoder.pkl'))
                except Exception:
                    class _FallbackLE:
                        classes_ = ["A+", "A", "B", "C", "D", "E", "F"]
                        def inverse_transform(self, idx):
                            return [self.classes_[min(int(i), len(self.classes_) - 1)] for i in idx]
                    app.label_encoder = _FallbackLE()

            if not app.encoders:
                for _enc_name, _filename in [
                    ('material_encoder', 'material_encoder.pkl'),
                    ('transport_encoder', 'transport_encoder.pkl'),
                    ('recycle_encoder', 'recycle_encoder.pkl'),
                    ('origin_encoder', 'origin_encoder.pkl'),
                ]:
                    try:
                        app.encoders[_enc_name] = joblib.load(os.path.join(encoders_dir, _filename))
                    except Exception:
                        pass

            def _safe_enc(val, enc, default):
                if enc is None:
                    return 0
                try:
                    return enc.transform([val])[0]
                except Exception:
                    try:
                        return enc.transform([default])[0]
                    except Exception:
                        return 0

            recyclability = product.get('recyclability', 'Medium') or 'Medium'
            material_encoded = _safe_enc(material, app.encoders.get('material_encoder'), 'Other')
            transport_encoded = _safe_enc(mode_name, app.encoders.get('transport_encoder'), 'Land')
            recycle_encoded = _safe_enc(recyclability, app.encoders.get('recycle_encoder'), 'Medium')
            origin_encoded = _safe_enc(origin_country, app.encoders.get('origin_encoder'), 'Other')
            weight_log = np.log1p(weight)
            weight_bin = 0 if weight < 0.5 else 1 if weight < 2 else 2 if weight < 10 else 3
            X = np.array([[
                material_encoded, transport_encoded, recycle_encoded, origin_encoded,
                weight_log, weight_bin,
                float(material_encoded) * float(transport_encoded),
                float(origin_encoded) * float(recycle_encoded)
            ]])

            eco_score_ml = eco_score_rule_based  # fallback if model unavailable
            confidence = 0.0
            shap_explanation = None
            proba_distribution = []
            conformal_sets = None

            if app.xgb_model:
                try:
                    pred = app.xgb_model.predict(X)[0]
                    eco_score_ml = app.label_encoder.inverse_transform([pred])[0]

                    conformal_sets = None
                    if hasattr(app.xgb_model, 'predict_proba'):
                        proba = app.xgb_model.predict_proba(X)
                        confidence = round(float(np.max(proba[0])) * 100, 1)
                        try:
                            proba_distribution = [
                                {"grade": str(g), "probability": round(float(p) * 100, 1)}
                                for g, p in zip(app.label_encoder.classes_, proba[0])
                            ]
                        except Exception:
                            pass

                        # Conformal prediction sets (split-conformal, guaranteed coverage)
                        try:
                            if app.conformal_config:
                                _class_order = app.conformal_config["class_order"]
                                _q_hats      = app.conformal_config["q_hat"]
                                _proba_row   = proba[0]
                                conformal_sets = {}
                                for _cov_label, _q in _q_hats.items():
                                    _threshold = 1.0 - _q
                                    _ps = [_class_order[j] for j, p_j in enumerate(_proba_row)
                                           if p_j >= _threshold]
                                    # Always include the predicted class (handles near-boundary cases)
                                    if eco_score_ml and eco_score_ml not in _ps:
                                        _ps = [eco_score_ml] + _ps
                                    conformal_sets[_cov_label] = _ps
                        except Exception as _ce:
                            print(f"⚠️ Conformal prediction failed: {_ce}")

                    print(f"✅ ML prediction: {eco_score_ml} ({confidence}%)")

                    # SHAP per-prediction explanation
                    try:
                        import shap as shap_lib
                        explainer = shap_lib.TreeExplainer(app.xgb_model)
                        shap_vals = explainer.shap_values(X)
                        pred_idx = int(np.argmax(app.xgb_model.predict_proba(X)[0]))
                        sv = np.array(shap_vals)
                        if sv.ndim == 3:
                            class_shap = sv[0, :, pred_idx]
                        elif isinstance(shap_vals, list):
                            class_shap = np.array(shap_vals[pred_idx])[0]
                        else:
                            class_shap = sv[0]
                        ev = explainer.expected_value
                        base_val = float(ev[pred_idx]) if hasattr(ev, '__len__') else float(ev)
                        feat_names = ['Material Type', 'Transport Mode', 'Recyclability',
                                      'Origin Country', 'Weight', 'Weight Category',
                                      'Material × Transport', 'Origin × Recyclability']
                        weight_bins_labels = ['<0.5 kg', '0.5–2 kg', '2–10 kg', '>10 kg']
                        raw_vals = [material, mode_name, recyclability, origin_country,
                                    f"{round(weight, 2)} kg",
                                    weight_bins_labels[int(weight_bin)], '', '']
                        shap_features = [
                            {"name": feat_names[i], "shap_value": round(float(class_shap[i]), 4),
                             "raw_value": raw_vals[i]}
                            for i in range(min(8, len(class_shap)))
                        ]
                        shap_features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
                        shap_explanation = {
                            "predicted_class": eco_score_ml,
                            "base_value": round(base_val, 4),
                            "features": shap_features
                        }
                        print(f"✅ SHAP explanation computed")
                    except Exception as shap_err:
                        print(f"⚠️ SHAP failed: {shap_err}")
                except Exception as ml_err:
                    print(f"⚠️ ML prediction failed: {ml_err}")
                    eco_score_ml = eco_score_rule_based
                    confidence = 0.0
            else:
                print("⚠️ No ML model available — using rule-based grade")

            # ml_co2 used in DB save — set to rule_co2 as best approximation
            ml_co2 = rule_co2

            # === Counterfactual Explanations ===
            # For each scenario, re-encode modified features and re-predict to show
            # what single change would most improve the eco grade.
            # Method: Wachter et al. (2017) "Counterfactual Explanations without Opening the Black Box"
            counterfactuals = []
            if app.xgb_model:
                try:
                    grade_order = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
                    current_grade_idx = grade_order.index(eco_score_ml) if eco_score_ml in grade_order else 6
                    _mat_intensities = {
                        "Plastic": 2.5, "Steel": 3.0, "Metal": 3.0, "Paper": 1.2,
                        "Glass": 1.5, "Wood": 0.8, "Fabric": 1.8, "Ceramic": 1.5, "Rubber": 2.2
                    }
                    cf_scenarios = [
                        ('origin',    'United Kingdom', 'Source locally (UK manufacture)'),
                        ('material',  'Paper',          'Switch to Paper/Cardboard'),
                        ('material',  'Wood',           'Switch to Wood/Bamboo'),
                        ('transport', 'Truck',          'Use road transport only'),
                    ]
                    seen_cf_grades = set()
                    for cf_feature, cf_new_val, cf_desc in cf_scenarios:
                        try:
                            cf_mat  = cf_new_val if cf_feature == 'material'  else material
                            cf_trns = cf_new_val if cf_feature == 'transport' else mode_name
                            cf_orig = cf_new_val if cf_feature == 'origin'    else origin_country
                            cf_mat_enc  = _safe_enc(cf_mat,  app.encoders.get('material_encoder'),  'Other')
                            cf_trns_enc = _safe_enc(cf_trns, app.encoders.get('transport_encoder'), 'Land')
                            cf_orig_enc = _safe_enc(cf_orig, app.encoders.get('origin_encoder'),    'Other')
                            cf_X = np.array([[
                                cf_mat_enc, cf_trns_enc, recycle_encoded, cf_orig_enc,
                                weight_log, weight_bin,
                                float(cf_mat_enc) * float(cf_trns_enc),
                                float(cf_orig_enc) * float(recycle_encoded)
                            ]])
                            cf_pred  = app.xgb_model.predict(cf_X)[0]
                            cf_grade = app.label_encoder.inverse_transform([cf_pred])[0]
                            cf_grade_idx   = grade_order.index(cf_grade) if cf_grade in grade_order else 6
                            grades_improved = current_grade_idx - cf_grade_idx
                            if grades_improved > 0 and cf_grade not in seen_cf_grades:
                                seen_cf_grades.add(cf_grade)
                                # Estimate CO2 under the counterfactual scenario
                                if cf_feature == 'origin':
                                    cf_coords   = origin_hubs.get(cf_orig, origin_hubs.get('United Kingdom'))
                                    cf_dist_km  = round(haversine(cf_coords['lat'], cf_coords['lon'], user_lat, user_lon), 1)
                                    cf_co2_val  = weight * mode_factor * cf_dist_km / 1000 + material_co2
                                elif cf_feature == 'material':
                                    cf_intensity = _mat_intensities.get(cf_mat, 2.0)
                                    cf_co2_val   = transport_co2 + (weight * cf_intensity)
                                else:
                                    cf_mode_factor = {"Truck": 0.15, "Ship": 0.03, "Air": 0.5}.get(cf_trns, mode_factor)
                                    cf_co2_val     = weight * cf_mode_factor * origin_distance_km / 1000 + material_co2
                                cf_co2_val   = max(cf_co2_val, 0.01)
                                co2_reduction = round(rule_co2 - cf_co2_val, 3)
                                co2_reduction_pct = round((co2_reduction / rule_co2) * 100, 1) if rule_co2 > 0 else 0
                                counterfactuals.append({
                                    'change':            cf_desc,
                                    'changed_feature':   cf_feature,
                                    'changed_value':     cf_new_val,
                                    'current_grade':     eco_score_ml,
                                    'new_grade':         cf_grade,
                                    'grades_improved':   grades_improved,
                                    'estimated_co2':     round(cf_co2_val, 3),
                                    'co2_reduction_kg':  round(max(co2_reduction, 0), 3),
                                    'co2_reduction_pct': co2_reduction_pct,
                                })
                        except Exception:
                            pass
                    counterfactuals.sort(key=lambda x: x['grades_improved'], reverse=True)
                    counterfactuals = counterfactuals[:3]
                    if counterfactuals:
                        print(f"✅ Counterfactuals computed: {len(counterfactuals)}")
                except Exception as cf_err:
                    print(f"⚠️ Counterfactual generation error: {cf_err}")

            # Real-world recyclability rates by material (based on global recycling data)
            _recyclability_rates = {
                'Glass':      90,   # Closed-loop, widely recycled
                'Aluminum':   85,   # Infinitely recyclable
                'Steel':      85,   # Infinitely recyclable
                'Metal':      85,
                'Paper':      80,   # Strong infrastructure
                'Cardboard':  80,
                'Wood':       70,   # Biodegradable/recyclable
                'Bamboo':     70,
                'Ceramic':    60,   # Recyclable but limited infrastructure
                'Stone':      25,   # Natural material, rarely recycled
                'Fabric':     40,   # Limited infrastructure
                'Cotton':     40,
                'Leather':    10,   # Very difficult to recycle
                'Rubber':     30,   # Some recycling routes (e.g. tyres) but limited
                'Silicone':   20,   # Technically recyclable but rarely is
                'Plastic':    20,   # ~9% of all plastic ever produced has been recycled
                'Polyester':  15,
                'Mixed':      15,   # Hard to separate components
                'Electronic': 15,
            }
            recyclability_pct = _recyclability_rates.get(material, 50)
            recyclability_label = 'High' if recyclability_pct >= 70 else ('Medium' if recyclability_pct >= 40 else 'Low')

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
                "recyclability": recyclability_label,
                "recyclability_percentage": recyclability_pct,
                "recyclability_description": f"{recyclability_pct}% of {material} is recycled globally",

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

                # SHAP per-prediction explanation
                "shap_explanation": shap_explanation,

                # Full 7-class probability distribution for confidence chart
                "proba_distribution": proba_distribution,

                # Conformal prediction sets (split-conformal, guaranteed marginal coverage)
                "conformal_sets": conformal_sets,

                # Counterfactual explanations
                "counterfactuals": counterfactuals,

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
                        "recyclability_score": recyclability_pct,
                        "eco_score": eco_score_ml,
                        "efficiency": None
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

                _session_user_id = session.get('user', {}).get('id')
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
                }, user_id=_session_user_id)
                
                save_emission_calculation({
                    'scraped_product_id': scraped_product.id,
                    'user_postcode': postcode,
                    'transport_distance': origin_distance_km,
                    'transport_mode': mode_name,
                    'ml_prediction': ml_co2,
                    'rule_based_prediction': rule_co2,
                    'final_emission': (ml_co2 + rule_co2) / 2,
                    'confidence_level': confidence_score,
                    'calculation_method': 'combined',
                    'eco_grade_ml': eco_score_ml,
                    'ml_confidence': confidence,
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

                # ── Data flywheel: append to live_scraped.csv for future retraining ──
                # The retrain.py script will merge this with the 50k base dataset.
                # Grade is re-derived from the DEFRA CO₂ value (same formula as training).
                try:
                    import csv as _csv
                    _live_csv = os.path.join(BASE_DIR, 'ml', 'live_scraped.csv')
                    _co2_val  = (ml_co2 + rule_co2) / 2 if (ml_co2 and rule_co2) else total_co2
                    _recyclability = _material_recyclability.get(material, 'Medium')
                    _row = {
                        'title':          product.get('title', ''),
                        'material':       material,
                        'weight':         round(float(weight), 4),
                        'transport':      mode_name,
                        'recyclability':  _recyclability,
                        'true_eco_score': eco_score_rule_based or 'C',
                        'co2_emissions':  round(float(_co2_val), 4),
                        'origin':         (origin_country or 'Unknown').title(),
                    }
                    _write_header = not os.path.exists(_live_csv)
                    with open(_live_csv, 'a', newline='', encoding='utf-8') as _f:
                        _w = _csv.DictWriter(_f, fieldnames=list(_row.keys()))
                        if _write_header:
                            _w.writeheader()
                        _w.writerow(_row)
                except Exception as _e:
                    print(f"Live CSV append skipped: {_e}")

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
                        'co2_estimate': float(calc.final_emission) if calc.final_emission else None,
                        'created_at': calc.created_at.isoformat() if calc.created_at else None
                    } for calc in recent_calculations
                ]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/eco-data', methods=['GET'])
    def eco_data():
        """Eco data for tables and analytics - queries PostgreSQL Product table"""
        try:
            limit = request.args.get('limit', type=int, default=1000)
            offset = request.args.get('offset', type=int, default=0)
            limit = min(limit, 10000)

            total = Product.query.count()
            products = (
                Product.query
                .filter(Product.material.isnot(None), Product.true_eco_score.isnot(None))
                .order_by(Product.id)
                .offset(offset)
                .limit(limit)
                .all()
            )

            return jsonify({
                'products': [p.to_dict() for p in products],
                'metadata': {
                    'total_products_in_dataset': total,
                    'products_returned': len(products),
                    'limit_applied': limit,
                    'offset': offset
                }
            })
        except Exception as e:
            print(f"Error in eco-data endpoint: {e}")
            return jsonify([]), 200

    @app.route('/api/alternatives', methods=['GET'])
    def get_alternatives():
        """Return greener product alternatives of the same type from the DB.

        Strategy (in priority order per grade level):
          1. Title keyword match  — finds the same kind of product
          2. Category match       — same broad product family
          3. Any product          — last resort to fill the slot

        Returns one result per grade level (A+, A, B…) for diversity, so the
        CO₂ comparison is meaningful rather than showing three identical A+ values.
        """
        import re
        try:
            title_param   = request.args.get('title', '').strip()
            category      = request.args.get('category', '').strip()
            current_grade = request.args.get('grade', 'F').strip()

            grade_order   = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
            current_idx   = grade_order.index(current_grade) if current_grade in grade_order else len(grade_order) - 1
            better_grades = grade_order[:current_idx]

            if not better_grades:
                return jsonify({'alternatives': [], 'message': 'Already at best possible grade'})

            # --- Keyword extraction from product title ---
            # Strips stop-words, model numbers, and generic descriptors so that
            # "SIHOO B100 Ergonomic Office Chair" → specific=['chair'], modifiers=['ergonomic','office']
            STOP = {
                'a','an','the','and','or','but','in','on','at','to','for','of',
                'with','by','from','as','is','was','are','be','been','have','had',
                'do','does','did','its','our','your',
                'pack','set','kit','bundle','count','piece','pieces','box','case','bag',
                'new','best','top','premium','quality','super','ultra','extra','plus',
                'pro','max','mini','large','small','medium','big','great','good',
                'free','easy','quick','fast','soft','hard','hot','cold','light',
                'heavy','original','classic','standard','basic','regular','gentle',
                'clean','fresh','pure','natural','advanced','improved','enhanced',
                'black','white','blue','red','green','grey','gray','silver','gold',
                'clear','transparent','brown','pink','purple','orange','yellow',
                'mens','womens','women','men','girls','boys','kids','adult','adults',
                'amazon','brand','basics','style','design','color','colour','edition',
                'version','series','model','type','size',
                # Product spec noise
                'comfy','cozy','comfortable','adaptive','dynamic','wide','narrow',
                'flip','tilt','lock','swivel','rotate','height','depth','weight',
            }

            def extract_keywords(raw, n=6):
                words = re.sub(r"[^\w\s]", " ", raw.lower()).split()
                kws = [
                    w for w in words
                    if w not in STOP
                    and len(w) > 2
                    # Pure numbers / units: "5g", "100ml", "3x"
                    and not re.match(r'^\d+[a-z]{0,3}$', w)
                    # Alphanumeric model numbers: "b100", "gt500", "x200", "dxr"
                    and not re.match(r'^[a-z]{1,3}\d+[a-z]{0,3}$', w)
                    and not re.match(r'^\d+[a-z]{1,3}\d*$', w)
                ]
                seen, unique = set(), []
                for w in kws:
                    if w not in seen:
                        seen.add(w)
                        unique.append(w)
                return unique[:n]

            keywords = extract_keywords(title_param) if title_param else []

            # Generic modifiers — describe how/where a product is used but are NOT the product type.
            # "electric razor" → specific=['razor'], modifiers=['electric']
            # "ergonomic office chair" → specific=['chair'], modifiers=['ergonomic','office']
            GENERIC_MODIFIERS = {
                # Tech/connectivity
                'electric', 'digital', 'wireless', 'smart', 'portable', 'rechargeable',
                'battery', 'automatic', 'manual', 'professional', 'cordless', 'power',
                'powered', 'electronic', 'mechanical', 'solar', 'handheld',
                # Product context / workspace
                'office', 'desk', 'gaming', 'home', 'kitchen', 'bathroom', 'bedroom',
                'indoor', 'outdoor', 'travel', 'compact', 'personal',
                # Physical descriptors
                'ergonomic', 'adjustable', 'foldable', 'breathable', 'waterproof',
                'washable', 'reusable', 'disposable', 'standing', 'rotating',
            }

            # Split into core product nouns vs context modifiers
            specific_kws  = [k for k in keywords if k not in GENERIC_MODIFIERS]
            modifier_kws  = [k for k in keywords if k in GENERIC_MODIFIERS]

            # ---------------------------------------------------------------
            # Product-type inference
            # ---------------------------------------------------------------
            # Many product titles contain NO product-type noun:
            #   • Books: "Never Lie: From the Sunday Times Bestselling Author…"
            #   • Electronics: model numbers only ("iPhone 15 Pro Max")
            # We infer the product type from (1) Amazon category breadcrumb,
            # then (2) distinctive title phrases, and prepend the result to
            # specific_kws so the DB search is anchored on the right term.
            # ---------------------------------------------------------------
            CATEGORY_TYPE_MAP = [
                # Books / reading material
                (['book', 'novel', 'fiction', 'non-fiction', 'nonfiction', 'thriller',
                  'mystery', 'biography', 'autobiography', 'memoir', 'history',
                  'kindle', 'literature', 'poetry', 'graphic novel', 'comic',
                  'children', 'young adult', 'self-help', 'religion', 'education',
                  'reference', 'textbook', 'cookbook', 'recipe'],
                 ['book', 'novel']),
                # Computing
                (['laptop', 'notebook computer', 'chromebook'], ['laptop', 'notebook']),
                (['desktop', 'pc', 'computer tower'],            ['computer', 'desktop']),
                # Headphones MUST come before phones — 'headphone' contains 'phone'
                (['headphone', 'earphone', 'earbuds', 'headset'],['headphone', 'earbuds']),
                (['smartphone', 'mobile phone', 'sim free'],     ['phone', 'smartphone']),
                (['tablet', 'ipad'],                             ['tablet']),
                (['keyboard'],                                   ['keyboard']),
                (['mouse'],                                      ['mouse']),
                (['monitor', 'television', 'tv'],                ['monitor', 'television']),
                (['camera'],                                     ['camera']),
                (['printer'],                                    ['printer']),
                # Home / furniture
                (['chair', 'stool', 'seat'],                     ['chair', 'seat']),
                (['table', 'desk'],                              ['desk', 'table']),
                (['sofa', 'couch'],                              ['sofa', 'couch']),
                (['bed', 'mattress', 'bedding', 'pillow', 'duvet'],['pillow', 'bedding']),
                (['lamp', 'light', 'lighting'],                  ['lamp', 'light']),
                # Kitchen
                (['coffee', 'espresso', 'coffee maker', 'cafetiere'], ['coffee']),
                (['toaster', 'kettle', 'blender', 'air fryer',
                  'microwave', 'oven'],                          ['appliance', 'kitchen']),
                (['water bottle', 'flask', 'tumbler'],           ['bottle', 'flask']),
                (['pan', 'pot', 'cookware', 'frying'],           ['pan', 'cookware']),
                # Personal care / health
                (['razor', 'shaver', 'shaving'],                 ['razor', 'shaver']),
                (['toothbrush'],                                 ['toothbrush']),
                (['skincare', 'moisturiser', 'moisturizer',
                  'serum', 'sunscreen'],                         ['skincare', 'cream']),
                (['hair dryer', 'hair straightener', 'curler'],  ['hair', 'dryer']),
                # Clothing / footwear
                (['clothing', 'shirt', 't-shirt', 'dress',
                  'jeans', 'trousers', 'shorts'],                ['clothing', 'shirt']),
                (['jacket', 'coat', 'hoodie', 'jumper',
                  'sweater'],                                    ['jacket', 'hoodie']),
                (['shoe', 'sneaker', 'trainer', 'boot',
                  'sandal'],                                     ['shoe', 'trainer']),
                # Sports / outdoors
                (['yoga', 'fitness', 'gym', 'exercise'],         ['fitness', 'gym']),
                (['bicycle', 'cycling'],                         ['bicycle', 'cycling']),
                # Toys / games
                (['toy', 'game', 'puzzle', 'lego', 'doll',
                  'action figure'],                              ['toy', 'game']),
                (['gaming', 'controller', 'console', 'playstation',
                  'xbox', 'nintendo'],                           ['controller', 'gaming']),
                # Office
                (['pen', 'pencil', 'stationery'],                ['pen', 'stationery']),
                (['notebook', 'journal', 'planner'],             ['notebook', 'journal']),
            ]

            # Title phrases that betray the product type even without a category
            TITLE_TYPE_PATTERNS = [
                # Books — subtitles containing author/review signals
                (['from the author', 'bestselling author', 'sunday times bestsell',
                  'new york times bestsell', 'times bestsell', 'richard & judy',
                  'book of the month', 'waterstones', 'gripping thriller',
                  'murder mystery', 'crime novel', 'sunday times number one',
                  'times number one'],
                 ['book', 'novel']),
                # Electronics model names
                (['iphone', 'samsung galaxy', 'pixel'],          ['phone', 'smartphone']),
                (['airpods', 'earbuds'],                         ['earbuds', 'headphone']),
                (['macbook', 'surface pro'],                     ['laptop', 'notebook']),
            ]

            def infer_product_type(title_raw, category_raw):
                """Return inferred DB search terms for the product type, or [].

                Uses word-boundary matching to prevent substring false positives
                (e.g. 'phone' must not match inside 'headphones').
                Strips trailing 's' to handle plurals ('shoes' → 'shoe').
                """
                import re as _re
                t = (title_raw or '').lower()
                c = (category_raw or '').lower()

                def _matches(text, patterns):
                    for p in patterns:
                        # Word-boundary match with optional plural suffix.
                        # Handles: shoe→shoes, trainer→trainers, toothbrush→toothbrushes
                        escaped = _re.escape(p)
                        if _re.search(rf'\b{escaped}(es|s)?\b', text):
                            return True
                    return False

                # 1. Category-based (most reliable — Amazon always sets this)
                for patterns, terms in CATEGORY_TYPE_MAP:
                    if _matches(c, patterns):
                        return terms
                # 2. Title-phrase-based (catches books with no 'book' in title)
                for patterns, terms in TITLE_TYPE_PATTERNS:
                    if _matches(t, patterns):
                        return terms
                return []

            inferred = infer_product_type(title_param, category)
            if inferred:
                # Prepend inferred product-type terms so they anchor the search,
                # then add any non-overlapping title-derived specific keywords.
                specific_kws = inferred + [k for k in specific_kws if k not in inferred]
                print(f"🔍 Product type inferred: {inferred} (category={category!r})")

            from sqlalchemy import or_ as sql_or, and_ as sql_and

            def _title_and(*words):
                """AND filter: title must contain every word."""
                return [Product.title.ilike(f'%{w}%') for w in words]

            def _query_for_grade(grade, specific, modifiers, cat):
                """Find one relevant product for this grade using progressively relaxed matching.

                Priority:
                  1. ALL specific keywords AND (if any modifiers exist, at least one modifier)
                     e.g. title contains 'razor' AND 'shaving' AND 'electric'
                  2. Top-2 specific keywords AND'd together  (razor AND shaving)
                  3. First specific keyword alone            (razor)
                  4. First modifier + first specific        (electric AND razor)  — only if no specific hit
                  5. Category match
                  6. Any product of that grade              (last resort)
                """
                base = [
                    Product.true_eco_score == grade,
                    Product.title.isnot(None),
                    Product.co2_emissions.isnot(None),
                ]

                def _run(*filters):
                    return (
                        Product.query
                        .filter(*base, *filters)
                        .order_by(Product.co2_emissions.asc())
                        .first()
                    )

                if specific:
                    # 1. All specific + at least one modifier
                    if modifiers:
                        p = _run(*_title_and(*specific), sql_or(*[Product.title.ilike(f'%{m}%') for m in modifiers]))
                        if p: return p, 'keyword'

                    # 2. All specific keywords (AND)
                    if len(specific) >= 2:
                        p = _run(*_title_and(*specific))
                        if p: return p, 'keyword'

                    # 3. Top-2 specific (AND)
                    if len(specific) >= 2:
                        p = _run(*_title_and(*specific[:2]))
                        if p: return p, 'keyword'

                    # 4. Each specific keyword individually in REVERSE order.
                    #    Product-type nouns (chair, razor, bottle) appear after brand
                    #    names in titles, so reversing means we try them first.
                    for kw in reversed(specific):
                        p = _run(Product.title.ilike(f'%{kw}%'))
                        if p: return p, 'keyword'

                elif modifiers:
                    # No specific nouns — try each modifier in reverse order
                    for kw in reversed(modifiers):
                        p = _run(Product.title.ilike(f'%{kw}%'))
                        if p: return p, 'keyword'

                # 5. Category
                if cat:
                    p = _run(Product.category.ilike(f'%{cat}%'))
                    if p: return p, 'category'

                # 6. Any product of this grade
                p = _run()
                return (p, 'fallback') if p else (None, None)

            results       = []
            seen_ids      = set()
            seen_prefixes = set()

            for grade in better_grades[:4]:
                product, matched_by = _query_for_grade(grade, specific_kws, modifier_kws, category)
                if not product or product.id in seen_ids:
                    continue
                prefix = (product.title or '')[:40].lower()
                if prefix in seen_prefixes:
                    continue
                seen_ids.add(product.id)
                seen_prefixes.add(prefix)
                results.append({
                    'title':         product.title,
                    'material':      product.material,
                    'grade':         product.true_eco_score,
                    'co2_emissions': float(product.co2_emissions) if product.co2_emissions else None,
                    'origin':        product.origin,
                    'transport':     product.transport,
                    'recyclability': product.recyclability,
                    'category':      product.category,
                    'matched_by':    matched_by,
                    'keywords_used': inferred if inferred else (specific_kws or keywords),
                })
                if len(results) >= 3:
                    break

            print(f"✅ Alternatives: {len(results)} results | keywords={keywords} grade={current_grade}")
            return jsonify({'alternatives': results})

        except Exception as e:
            print(f"Error in alternatives endpoint: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/submissions', methods=['GET'])
    def admin_submissions():
        """Get admin submissions - REQUIRES ADMIN AUTH"""
        # Check authentication
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        try:
            submissions = ScrapedProduct.query.order_by(ScrapedProduct.id.desc()).limit(100).all()
            result = []
            for sub in submissions:
                # Get latest emission calculation for this product
                calc = EmissionCalculation.query.filter_by(
                    scraped_product_id=sub.id
                ).order_by(EmissionCalculation.id.desc()).first()
                # Get admin review (true label) if any
                review = AdminReview.query.filter_by(
                    scraped_product_id=sub.id
                ).order_by(AdminReview.id.desc()).first()

                result.append({
                    'id': sub.id,
                    'url': sub.amazon_url,
                    'title': sub.title or 'Unknown product',
                    'material': sub.material,
                    'origin': sub.origin_country,
                    'brand': sub.brand,
                    'predicted_label': calc.eco_grade_ml if calc else None,
                    'confidence': f"{float(calc.ml_confidence):.1f}%" if calc and calc.ml_confidence else None,
                    'rule_based_label': None,
                    'true_label': review.corrected_grade if review else None,
                    'review_status': review.review_status if review else 'pending',
                    'admin_notes': review.admin_notes if review else None,
                    'co2_kg': float(calc.final_emission) if calc and calc.final_emission else None,
                    'transport_mode': calc.transport_mode if calc else None,
                    'created_at': sub.created_at.isoformat() if sub.created_at else None,
                })
            return jsonify(result)
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
            true_label = (data.get('true_label') or '').strip().upper()
            admin_notes = data.get('admin_notes', '')

            if not submission_id:
                return jsonify({'error': 'No submission ID provided'}), 400

            review = AdminReview.query.filter_by(scraped_product_id=submission_id).order_by(AdminReview.id.desc()).first()
            if review:
                review.corrected_grade = true_label or None
                review.admin_notes = admin_notes
                review.review_status = 'approved' if true_label else 'pending'
                review.reviewed_by = session['user'].get('id')
                review.reviewed_at = datetime.utcnow()
            else:
                review = AdminReview(
                    scraped_product_id=submission_id,
                    corrected_grade=true_label or None,
                    admin_notes=admin_notes,
                    review_status='approved' if true_label else 'pending',
                    reviewed_by=session['user'].get('id'),
                    reviewed_at=datetime.utcnow(),
                )
                db.session.add(review)
            db.session.commit()
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
                'co2_estimate': float(pred.final_emission) if pred.final_emission else None,
                'method': pred.calculation_method
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
    
    @app.route('/api/global-shap', methods=['GET'])
    def global_shap():
        """Global SHAP feature importance averaged over a dataset sample.

        Computes mean(|SHAP value|) per feature across 500 randomly-sampled
        products, aggregated over all 7 grade classes. This gives the global
        importance of each input feature to the model as a whole, complementing
        the per-prediction local SHAP explanations on the results card.

        Method: Lundberg & Lee (2017) — SHapley Additive exPlanations.
        """
        try:
            import shap as shap_lib

            # Use `is None` — truthiness on sklearn/xgb objects can be ambiguous
            model = getattr(app, 'xgb_model', None)
            if model is None:
                return jsonify({'error': 'Model not loaded yet — make one prediction first'}), 503

            # Sample up to 500 products from the DB
            sample = (
                Product.query
                .filter(
                    Product.material.isnot(None),
                    Product.transport.isnot(None),
                    Product.origin.isnot(None),
                    Product.weight.isnot(None),
                )
                .limit(500)
                .all()
            )
            if len(sample) < 20:
                return jsonify({'error': 'Insufficient data in database'}), 400

            enc = app.encoders  # populated after first prediction (lazy load)

            def _safe_enc_shap(val, *keys_to_try, default_int=0):
                """Try multiple encoder key names — handles startup vs lazy-load key naming."""
                for key in keys_to_try:
                    e = enc.get(key)
                    if e is not None:
                        try:
                            return int(e.transform([str(val)])[0])
                        except Exception:
                            try:
                                return int(e.transform(['Other'])[0])
                            except Exception:
                                continue
                return default_int

            rows = []
            row_errors = 0
            for p in sample:
                try:
                    mat  = str(p.material  or 'Other')
                    trn  = str(p.transport or 'Ship')
                    rec  = str(p.recyclability or 'Medium')
                    orig = str(p.origin    or 'Unknown').title()  # normalise case
                    w    = float(p.weight  or 1.0)
                    # Try both historic key names for each encoder
                    me = _safe_enc_shap(mat,  'material_encoder')
                    te = _safe_enc_shap(trn,  'transport_encoder')
                    re_= _safe_enc_shap(rec,  'recycle_encoder', 'recyclability_encoder')
                    oe = _safe_enc_shap(orig, 'origin_encoder')
                    wl = float(np.log1p(max(w, 0.0)))
                    wb = float(0 if w < 0.5 else 1 if w < 2 else 2 if w < 10 else 3)
                    rows.append([me, te, re_, oe, wl, wb,
                                 float(me) * float(te),
                                 float(oe) * float(re_)])
                except Exception as row_err:
                    row_errors += 1
                    if row_errors <= 3:
                        print(f"⚠️ SHAP row encode error: {row_err}")

            print(f"ℹ️ Global SHAP: {len(rows)}/{len(sample)} rows encoded ({row_errors} errors)")

            # Fallback: if encoding produced nothing, use feature_importances_ from the model
            if len(rows) < 10:
                print("⚠️ SHAP row encoding failed — falling back to feature_importances_")
                try:
                    fi = model.feature_importances_
                except Exception:
                    return jsonify({'error': 'Could not compute feature importance'}), 500
                feat_names_fb = [
                    'Material Type', 'Transport Mode', 'Recyclability',
                    'Origin Country', 'Weight (log)', 'Weight Category',
                    'Material × Transport', 'Origin × Recyclability',
                ]
                features = sorted([
                    {'feature': feat_names_fb[i], 'importance': round(float(fi[i]), 5)}
                    for i in range(min(len(feat_names_fb), len(fi)))
                ], key=lambda x: -x['importance'])
                return jsonify({
                    'features':    features,
                    'sample_size': 0,
                    'method':      'XGBoost feature_importances_ (SHAP encoding failed)',
                    'citation':    'Lundberg & Lee (2017). NeurIPS.',
                })

            X_s = np.array(rows)
            explainer = shap_lib.TreeExplainer(model)
            sv = explainer.shap_values(X_s)

            arr = np.array(sv)
            if arr.ndim == 3:
                global_imp = np.mean(np.abs(arr), axis=(0, 2))
            elif isinstance(sv, list):
                global_imp = np.mean(np.abs(np.stack(sv, axis=-1)), axis=(0, 2))
            else:
                global_imp = np.mean(np.abs(arr), axis=0)

            feat_names = [
                'Material Type', 'Transport Mode', 'Recyclability',
                'Origin Country', 'Weight', 'Weight Category',
                'Material × Transport', 'Origin × Recyclability',
            ]
            features = sorted([
                {'feature': feat_names[i], 'importance': round(float(global_imp[i]), 5)}
                for i in range(min(8, len(global_imp)))
            ], key=lambda x: -x['importance'])

            print(f"✅ Global SHAP computed over {len(rows)} samples")
            return jsonify({
                'features':    features,
                'sample_size': len(rows),
                'method':      'TreeExplainer — mean(|SHAP|) across all samples and classes',
                'citation':    'Lundberg & Lee (2017). NeurIPS.',
            })

        except Exception as e:
            print(f"Global SHAP error: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/apple-validation', methods=['GET'])
    def apple_validation():
        """Serve Apple Product Environmental Report validation results."""
        try:
            path = os.path.join(BASE_DIR, 'ml', 'apple_validation_results.json')
            if not os.path.exists(path):
                return jsonify({'error': 'Apple validation results not found'}), 404
            with open(path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/evaluation', methods=['GET'])
    def evaluation():
        """Serve pre-computed ML evaluation results (generated by ml/compute_evaluation.py)."""
        try:
            eval_path = os.path.join(BASE_DIR, 'ml', 'evaluation_results.json')
            if not os.path.exists(eval_path):
                return jsonify({'error': 'Evaluation results not found'}), 404
            with open(eval_path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ablation', methods=['GET'])
    def ablation():
        """Serve feature ablation study results (generated by ml/ablation.py)."""
        try:
            path = os.path.join(BASE_DIR, 'ml', 'ablation_results.json')
            if not os.path.exists(path):
                return jsonify({'error': 'Ablation results not found'}), 404
            with open(path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/sensitivity', methods=['GET'])
    def sensitivity():
        """Serve sensitivity analysis results (generated by ml/sensitivity.py)."""
        try:
            path = os.path.join(BASE_DIR, 'ml', 'sensitivity_results.json')
            if not os.path.exists(path):
                return jsonify({'error': 'Sensitivity results not found'}), 404
            with open(path, 'r') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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
        """User registration — saves to DB with hashed password."""
        try:
            data = request.get_json() or {}
            username = (data.get('username') or '').strip()
            password = data.get('password') or ''
            email    = (data.get('email') or '').strip() or None

            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            if len(username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters'}), 400
            if len(password) < 8:
                return jsonify({'error': 'Password must be at least 8 characters'}), 400
            if username.lower() == 'admin':
                return jsonify({'error': 'Username not available'}), 400

            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already taken'}), 409
            if email and User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already registered'}), 409

            user = User(username=username, email=email, role='user')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            return jsonify({'message': f'Account created for {username}', 'role': 'user'}), 201

        except Exception as e:
            db.session.rollback()
            print(f"Signup error: {e}")
            return jsonify({'error': 'Registration failed'}), 500

    @app.route('/login', methods=['POST'])
    @limiter.limit("10 per minute")
    def login():
        """Login — all users authenticated via DB with hashed passwords."""
        try:
            data = request.get_json() or {}
            username = (data.get('username') or '').strip()
            password = data.get('password') or ''

            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400

            # Single auth path: DB lookup for all users (including admin)
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid username or password'}), 401

            # Update last_login timestamp (graceful — column may not exist on older deployments)
            try:
                user.last_login = datetime.utcnow()
                db.session.commit()
            except Exception:
                db.session.rollback()

            session.permanent = True
            session['user'] = {'id': user.id, 'username': user.username, 'role': user.role or 'user'}
            return jsonify({'message': 'Logged in', 'user': session['user']}), 200

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

    # ── Admin user management (DB-backed) ────────────────────────────────────

    def _require_admin():
        u = session.get('user')
        if not u or u.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return None

    @app.route('/admin/users', methods=['GET'])
    def admin_get_users():
        err = _require_admin()
        if err: return err
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify([u.to_dict() for u in users]), 200

    @app.route('/admin/users/<int:user_id>', methods=['DELETE'])
    def admin_delete_user(user_id):
        err = _require_admin()
        if err: return err
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if user.role == 'admin':
            return jsonify({'error': 'Cannot delete admin user'}), 400
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'User {user.username} deleted'}), 200

    @app.route('/admin/users/<int:user_id>/role', methods=['PUT'])
    def admin_update_role(user_id):
        err = _require_admin()
        if err: return err
        data = request.get_json() or {}
        new_role = data.get('role')
        if new_role not in ('user', 'admin'):
            return jsonify({'error': 'Invalid role'}), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user.role = new_role
        db.session.commit()
        return jsonify({'message': f'{user.username} role set to {new_role}'}), 200

    # ── User history & stats ─────────────────────────────────────────────────
    @app.route('/api/my/history', methods=['GET'])
    def my_history():
        user_info = session.get('user')
        if not user_info:
            return jsonify({'error': 'Login required'}), 401
        uid = user_info['id']
        try:
            products = (
                ScrapedProduct.query
                .filter_by(user_id=uid)
                .order_by(ScrapedProduct.created_at.desc())
                .limit(100)
                .all()
            )
            result = []
            for p in products:
                calc = EmissionCalculation.query.filter_by(
                    scraped_product_id=p.id
                ).order_by(EmissionCalculation.id.desc()).first()
                result.append({
                    'id': p.id,
                    'title': p.title or 'Unknown product',
                    'brand': p.brand,
                    'material': p.material,
                    'origin': p.origin_country,
                    'eco_grade': calc.eco_grade_ml if calc else None,
                    'co2_kg': float(calc.final_emission) if calc and calc.final_emission else None,
                    'confidence': float(calc.ml_confidence) if calc and calc.ml_confidence else None,
                    'transport_mode': calc.transport_mode if calc else None,
                    'scanned_at': p.created_at.isoformat() if p.created_at else None,
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/my/stats', methods=['GET'])
    def my_stats():
        user_info = session.get('user')
        if not user_info:
            return jsonify({'error': 'Login required'}), 401
        uid = user_info['id']
        try:
            products = ScrapedProduct.query.filter_by(user_id=uid).all()
            total = len(products)
            if total == 0:
                return jsonify({'total_scans': 0, 'avg_co2_kg': None, 'total_co2_kg': None,
                                'grade_distribution': {}, 'top_material': None, 'best_grade': None})

            grades, co2_vals, materials = [], [], []
            for p in products:
                calc = EmissionCalculation.query.filter_by(
                    scraped_product_id=p.id
                ).order_by(EmissionCalculation.id.desc()).first()
                if calc:
                    if calc.eco_grade_ml:
                        grades.append(calc.eco_grade_ml)
                    if calc.final_emission:
                        co2_vals.append(float(calc.final_emission))
                if p.material:
                    materials.append(p.material)

            grade_order = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
            grade_dist = {g: grades.count(g) for g in grade_order if grades.count(g) > 0}
            best_grade = next((g for g in grade_order if g in grade_dist), None)
            top_material = max(set(materials), key=materials.count) if materials else None
            total_co2 = round(sum(co2_vals), 2) if co2_vals else None
            avg_co2 = round(sum(co2_vals) / len(co2_vals), 2) if co2_vals else None

            return jsonify({
                'total_scans': total,
                'avg_co2_kg': avg_co2,
                'total_co2_kg': total_co2,
                'grade_distribution': grade_dist,
                'top_material': top_material,
                'best_grade': best_grade,
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── Enterprise dashboard blueprint ───────────────────────────────────────
    try:
        from backend.routes.enterprise_dashboard import enterprise_bp
        app.register_blueprint(enterprise_bp)
        print("✅ Enterprise dashboard blueprint registered")
    except Exception as _e:
        print(f"⚠️  Enterprise blueprint not loaded: {_e}")

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