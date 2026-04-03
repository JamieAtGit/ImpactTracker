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
import threading
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BASE_DIR)

# ── Transport emission factors ─────────────────────────────────────────────────
# Units: kg CO₂e per kg-product per 1000 km (i.e. the formula is
#   transport_co2 = weight_kg × FACTOR × distance_km / 1000)
#
# Sources:
#   Truck: 0.15 kg CO₂/kg/1000km  ≈ DEFRA 2023 HGV average (0.165 kg CO₂e/tonne-km)
#          after rounding. Ref: DEFRA/BEIS GHG Conversion Factors 2023, "Freighting goods".
#   Ship:  0.03 kg CO₂/kg/1000km  ≈ IMO/ECTA Ro-Ro ferry / general cargo average.
#          DEFRA gives 0.011 kg CO₂e/tonne-km for container ships; 0.03 is a conservative
#          estimate covering larger-volume consumer goods vessels.
#   Air:   0.50 kg CO₂/kg/1000km  ≈ DEFRA 2023 air freight average including RFI
#          (0.602 kg CO₂e/tonne-km economy, 0.500 rounded for simplicity).
TRANSPORT_CO2_FACTOR = {
    "Truck": 0.15,
    "Land":  0.15,
    "Ship":  0.03,
    "Air":   0.50,
}

# ── Material CO₂ intensities ────────────────────────────────────────────────────
# Single source of truth for material CO₂ intensities (kg CO₂ per kg of material).
# Used in both the main rule-based calculation and counterfactual explanations.
# Update here and both places stay in sync automatically.
MATERIAL_CO2_INTENSITY = {
    # Generic categories
    "Plastic":          2.5,
    "Steel":            3.0,
    "Metal":            3.0,
    "Paper":            1.2,
    "Glass":            1.5,
    "Wood":             0.8,
    "Fabric":           1.8,
    "Ceramic":          1.5,
    "Rubber":           2.2,
    "Other":            2.0,
    # Specific plastics (kg CO2e / kg, cradle-to-gate, ECOINVENT 3.9)
    "Polypropylene":    1.9,
    "Polyethylene":     2.0,
    "HDPE":             1.9,
    "LDPE":             2.0,
    "PET":              3.4,
    "PVC":              2.4,
    "Polycarbonate":    3.1,
    "Polystyrene":      3.3,
    "ABS Plastic":      3.5,
    "Nylon":            7.9,
    "Acrylic":          3.2,
    "TPE":              2.8,
    "TPU":              4.2,
    "EVA Foam":         2.5,
    "PU":               3.5,
    # Specific metals
    "Stainless Steel":  6.2,
    "Cast Iron":        2.2,   # Primary: ~2.2 kg CO2e/kg (EAF route, ECOINVENT 3.9)
    "Iron":             2.5,
    "Aluminium":        8.2,
    "Aluminum":         8.2,
    "Copper":           3.8,
    "Zinc":             3.5,
    "Brass":            3.2,
    "Bronze":           3.0,
    "Titanium":        35.0,   # Highly energy-intensive to smelt
    # Specific fabrics
    "Cotton":           3.8,
    "Polyester":        5.5,
    "Wool":             5.0,
    "Silk":             20.0,
    "Linen":            1.5,
    "Bamboo":           1.5,
    # Wood
    "MDF":              0.6,
    "Plywood":          0.7,
    # Other
    "Silicone":         2.5,
    "Natural Rubber":   2.0,
    "Memory Foam":      3.0,
    "Leather":          15.0,
    "Faux Leather":     3.5,
}

# Recyclability rates (%) by country, sourced from national recycling data.
# 'UK' uses WRAP 2022/23 figures. 'global' is a world-average fallback.
# To add a new country: add a new key with the same material keys below.
# Default used everywhere is 'UK'. Change DEFAULT_RECYCLABILITY_COUNTRY to
# switch the whole app to a different region.
RECYCLABILITY_RATES = {
    'UK': {
        # Source: WRAP 2022/23, DEFRA statistics, RECOUP reports
        'Glass':           76,   # Bottle banks + kerbside
        'Aluminum':        52,   # Kerbside widely accepted; drinks cans ~75% but foil drags average
        'Steel':           70,   # Cans, tins well-collected
        'Metal':           70,
        'Stainless Steel': 67,
        'Paper':           74,   # Strong UK paper recycling infrastructure
        'Cardboard':       80,   # Highest-performing UK stream
        'Wood':            35,   # Limited kerbside; some commercial routes
        'Bamboo':          25,   # Niche; rarely collected
        'Fabric':          15,   # UK textile recycling is poor (WRAP 2023)
        'Cotton':          15,
        'Polyester':       10,
        'Nylon':           10,
        'Plastic':         12,   # UK plastic recycling rate 2022 (RECOUP)
        'Mixed':           10,   # Hard to separate
        'Electronic':      17,   # WEEE collection ~40% but actual recycling lower
        'Leather':         10,
        'Rubber':          25,   # Tyre recycling routes exist; other rubber low
        'Silicone':        10,
        'Ceramic':         20,
        'Foam':             5,
    },
    'global': {
        # World-average fallback (pre-existing values)
        'Glass':           90,
        'Aluminum':        85,
        'Steel':           85,
        'Metal':           85,
        'Stainless Steel': 88,
        'Paper':           80,
        'Cardboard':       80,
        'Wood':            70,
        'Bamboo':          70,
        'Fabric':          40,
        'Cotton':          40,
        'Polyester':       15,
        'Nylon':           20,
        'Plastic':         20,
        'Mixed':           15,
        'Electronic':      15,
        'Leather':         10,
        'Rubber':          30,
        'Silicone':        20,
        'Ceramic':         30,
        'Foam':            10,
    },
}

DEFAULT_RECYCLABILITY_COUNTRY = 'UK'


def get_recyclability_pct(material: str, country: str = DEFAULT_RECYCLABILITY_COUNTRY) -> int:
    """Return recyclability % for a material in the given country. Falls back to global, then 50."""
    rates = RECYCLABILITY_RATES.get(country) or RECYCLABILITY_RATES.get('global', {})
    return rates.get(material) or RECYCLABILITY_RATES['global'].get(material, 50)


# Lock for ML model lazy-loading — prevents a race condition where two
# simultaneous requests both attempt to load the model from disk.
_MODEL_LOAD_LOCK = threading.Lock()


def estimate_default_weight(title: str, category: str) -> float:
    """
    Return a sensible default weight (kg) when scraping fails to extract one.
    Checks the product title first (most specific), then the category string.
    Falls back to 0.5 kg only for truly unrecognised products.
    """
    t = (title or '').lower()
    c = (category or '').lower()

    # ── Title-based rules (ordered heavy → light) ────────────────────────────
    title_rules = [
        (["washing machine", "washer dryer", "tumble dryer", "dishwasher"], 65.0),
        (["fridge", "refrigerator", "freezer", "chest freezer"],            55.0),
        (["sofa", "couch", "sectional sofa", "corner sofa"],                45.0),
        (["bed frame", "bedframe", "divan bed", "ottoman bed"],             40.0),
        (["wardrobe", "chest of drawers", "bookcase", "bookshelf",
          "shelving unit"],                                                  30.0),
        (["desk", "dining table", "coffee table", "side table"],            20.0),
        (["television", "smart tv", "qled", "oled tv", "led tv"],           12.0),
        (["office chair", "gaming chair", "armchair", "recliner"],          12.0),
        (["mattress"],                                                       10.0),
        (["bicycle", " bike ", "ebike", "e-bike"],                          10.0),
        (["vacuum cleaner", "hoover", "robot vacuum", "cordless vacuum"],    4.0),
        (["air purifier", "air fryer", "microwave"],                         4.0),
        (["coffee maker", "coffee machine", "espresso machine"],             3.0),
        (["printer", "laser printer", "inkjet printer"],                     5.0),
        (["gaming console", "playstation", "xbox", "nintendo switch"],       3.0),
        (["soundbar", "bluetooth speaker", "smart speaker"],                 2.0),
        (["laptop", "notebook computer", "chromebook", "ultrabook"],         2.0),
        (["blender", "food processor", "kettle", "toaster", "air fryer"],    1.5),
        (["hair dryer", "hair straightener", "curling iron"],                0.6),
        (["tablet", "ipad", "kindle"],                                       0.5),
        (["smartphone", "iphone", "android phone"],                          0.2),
        (["book", "paperback", "hardback", "novel"],                         0.4),
        (["t-shirt", "tshirt", "shirt", "blouse", "top"],                    0.2),
        (["jeans", "trousers", "dress", "skirt", "leggings"],                0.4),
        (["jacket", "coat", "hoodie", "jumper", "sweatshirt"],               0.7),
        (["shoes", "trainers", "sneakers", "boots"],                         0.8),
        (["backpack", "rucksack", "handbag"],                                0.7),
    ]
    for keywords, weight in title_rules:
        if any(kw in t for kw in keywords):
            return weight

    # ── Category-based fallbacks ──────────────────────────────────────────────
    category_rules = [
        (["large appliance", "washing", "fridge", "freezer"], 50.0),
        (["furniture", "sofa", "bed", "wardrobe"],            15.0),
        (["small appliance", "kitchen appliance"],             2.0),
        (["electronics", "computers", "laptop", "pc"],         1.5),
        (["tv", "television", "monitor"],                     10.0),
        (["clothing", "fashion", "apparel"],                   0.3),
        (["shoes", "footwear"],                                0.8),
        (["books", "stationery"],                              0.4),
        (["toys", "games"],                                    0.5),
        (["sports", "fitness", "outdoors"],                    1.0),
        (["kitchen", "cookware", "dining"],                    1.0),
        (["garden", "outdoor", "tools"],                       2.0),
    ]
    for keywords, weight in category_rules:
        if any(kw in c for kw in keywords):
            return weight

    return 0.5  # fallback for genuinely unknown products


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
        from backend.routes.api import calculate_eco_score, co2_to_grade
        from backend.services.materials_service_enhanced import EnhancedMaterialsIntelligenceService
        from backend.scrapers.amazon.requests_scraper import RequestsScraper as _RequestsScraper

        _scraper_instance = _RequestsScraper()
        _ESTIMATION_DEPS = {
            'materials_service': EnhancedMaterialsIntelligenceService(),
            'detect_category': _scraper_instance.detect_category_from_title,
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
            'co2_to_grade': co2_to_grade,
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


def _build_transport_breakdown(weight_kg: float, origin_km: float, uk_hub_km: float, mode: str) -> dict:
    """Compute CO₂ for each delivery leg using DEFRA 2023 freight factors.

    Returns a dict with per-leg kg CO₂ and distances, ready to surface in the API.
    Mode factors (kg CO₂ per tonne-km → convert: ÷ 1000 for kg CO₂ per kg per km):
        Air   = 0.234  kg CO₂/tonne-km  → 0.000234 per kg per km  (conservative mid-haul)
        Ship  = 0.016  kg CO₂/tonne-km  → 0.000016 per kg per km
        Truck = 0.096  kg CO₂/tonne-km  → 0.000096 per kg per km
    UK distribution: HGV leg ~200 km domestic route at truck factor.
    Last-mile: courier van (0.21 kg CO₂/km) shared across ~40 stops over ~60 km route.
    """
    _FACTORS = {'Air': 0.000234, 'Ship': 0.000016, 'Truck': 0.000096}
    factor = _FACTORS.get(mode, _FACTORS['Ship'])

    intl_kg      = round(weight_kg * origin_km * factor, 3)
    uk_dist_kg   = round(weight_kg * 0.000096 * 200 + 0.03, 3)   # HGV 200 km + fixed warehouse
    last_mile_kg = round(60 * 0.21 / 40 + weight_kg * 0.005, 3)   # van shared route + weight premium
    total_kg     = round(intl_kg + uk_dist_kg + last_mile_kg, 3)

    return {
        "international_kg":      intl_kg,
        "uk_distribution_kg":    uk_dist_kg,
        "last_mile_kg":          last_mile_kg,
        "total_transport_kg":    total_kg,
        "international_distance_km": round(origin_km, 0),
        "uk_hub_distance_km":    round(uk_hub_km, 0),
        "transport_mode":        mode,
        "mode_factor_per_kg_km": factor,
        "source":                "DEFRA 2023 freight emission factors",
    }


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
            import sys as _sys
            _sys.stderr.write(
                "\n🚨  FLASK_SECRET_KEY is not set.\n"
                "    All user sessions will be invalidated on every restart.\n"
                "    Set this environment variable in your deployment dashboard.\n\n"
            )
            import secrets
            _secret = secrets.token_hex(32)
        app.config['SECRET_KEY'] = _secret
        app.config['DEBUG'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit
    else:
        # Development configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'dev-key-change-in-production'
        app.config['DEBUG'] = True
    
    # Initialize extensions
    db.init_app(app)
    _rate_limit_enabled = config_name == 'production'
    app.limiter = Limiter(
        get_remote_address, app=app, default_limits=[],
        storage_uri="memory://", enabled=_rate_limit_enabled,
    )
    limiter = app.limiter
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
            # Chrome extension — requests come from Amazon page origin
            'https://www.amazon.co.uk',
            'https://www.amazon.com',
            'https://amazon.co.uk',
            'https://amazon.com',
        ],
        methods=['GET', 'POST', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
    )

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Deny all resource loading from API responses (pure JSON API — no HTML assets served)
        response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
        if config_name == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

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
                    ("ALTER TABLE emission_calculations ADD COLUMN data_quality VARCHAR(10)", "emission_calculations.data_quality"),
                    ("ALTER TABLE admin_reviews ADD COLUMN corrected_grade VARCHAR(5)", "admin_reviews.corrected_grade"),
                    ("ALTER TABLE scraped_products ADD COLUMN materials_json TEXT", "scraped_products.materials_json"),
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

            # Load calibrated XGBoost model (preferred) or fall back to raw
            _cal_path = os.path.join(model_dir, "calibrated_model.pkl")
            _xgb_path = os.path.join(model_dir, "xgb_model.json")
            if os.path.exists(_cal_path):
                app.xgb_model = joblib.load(_cal_path)
                print("✅ Calibrated XGBoost model loaded successfully")
            elif os.path.exists(_xgb_path):
                import xgboost as xgb
                xgb_model = xgb.XGBClassifier()
                xgb_model.load_model(_xgb_path)
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

            # Alias: estimation endpoint uses 'recycle_encoder' key; file is named
            # 'recyclability_encoder.pkl'.  Register under both names so both paths work.
            if 'recyclability_encoder' in encoders and 'recycle_encoder' not in encoders:
                encoders['recycle_encoder'] = encoders['recyclability_encoder']

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
    
    @app.route('/estimate_emissions', methods=['POST'])
    @limiter.limit("10 per minute")
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
        co2_to_grade = deps['co2_to_grade']

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

            import re as _re
            _postcode_clean = postcode.replace(" ", "").upper()
            if not _re.match(r'^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$', _postcode_clean):
                return jsonify({"error": "Please enter a valid UK postcode (e.g. SW1A 1AA)"}), 400

            if 'amazon.' not in url.lower():
                return jsonify({"error": "Please enter a valid Amazon product URL (e.g. amazon.co.uk or amazon.com)"}), 400

            asin_key = extract_asin_from_amazon_url(url)
            cached_calc = find_cached_emission_calculation(asin=asin_key, amazon_url=url, postcode=postcode)
            _BAD_TITLES = {'amazon product', 'unknown product', 'unknown', '', 'consumer product'}
            _POOR_MATERIALS = {'mixed', 'unknown', 'other', 'n/a', '', 'not found'}
            # Cache is only usable when we have good material data. If materials_json
            # is NULL and the stored material string is vague (Mixed/Unknown), bypass
            # the cache and re-scrape so the product silently upgrades itself.
            _cached_material_ok = (
                cached_calc
                and cached_calc.scraped_product
                # Require materials_json so cache hits always show full multi-material data.
                # Products without it (scraped before this column existed) are re-scraped
                # exactly once; after that they have materials_json and hit the cache normally.
                and cached_calc.scraped_product.materials_json is not None
                and (cached_calc.scraped_product.material or '').strip().lower() not in _POOR_MATERIALS
            )
            # Cached results older than this are re-scraped so improvements to the
            # material / origin detection pipeline are automatically applied.
            _CACHE_MAX_AGE_DAYS = 30
            _cache_too_old = bool(
                cached_calc
                and cached_calc.created_at
                and (datetime.utcnow() - cached_calc.created_at).days > _CACHE_MAX_AGE_DAYS
            )
            _cache_usable = (
                cached_calc
                and cached_calc.scraped_product
                and (cached_calc.scraped_product.title or '').strip().lower() not in _BAD_TITLES
                and float(cached_calc.final_emission or 0) > 0
                and _cached_material_ok
                and not _cache_too_old
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
                cached_weight   = float(cached_product.weight) if cached_product.weight else estimate_default_weight(cached_product.title, cached_product.category)
                # Sanity-check: if stored weight >150 kg it was likely saved in
                # grams by an older scraper — auto-correct.
                # ScrapedProduct has no category column, so infer from the title.
                _HEAVY_TITLE_WORDS = {
                    'sofa', 'wardrobe', 'cabinet', 'fridge', 'freezer', 'washer',
                    'dryer', 'dishwasher', 'oven', 'cooker', 'barbecue', 'bbq',
                    'treadmill', 'rowing machine', 'elliptical', 'weight bench',
                    'squat rack', 'barbell', 'dumbbell rack', 'weight rack',
                    'lawnmower', 'generator', 'compressor', 'workbench',
                }
                _cached_title_lower = (cached_product.title or '').lower()
                _cached_legitimately_heavy = any(w in _cached_title_lower for w in _HEAVY_TITLE_WORDS)
                if cached_weight > 150 and not _cached_legitimately_heavy:
                    cached_weight /= 1000
                cached_raw_wt   = round(cached_weight / 1.05, 3)
                cached_transport = cached_calc.transport_mode or 'Ship'
                cached_material  = cached_product.material or 'Mixed'

                rec_pct   = get_recyclability_pct(cached_material)
                rec_label = 'High' if rec_pct >= 70 else ('Medium' if rec_pct >= 40 else 'Low')

                cached_grade_ml   = co2_to_grade(cached_ml_co2)
                cached_grade_rule = co2_to_grade(cached_rule_co2)
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
                    "image_url":    None,
                    "manufacturer": cached_product.brand or "Not found",
                    "category":     deps['detect_category'](cached_product.title or ''),
                    "certifications": [],
                    "transport_breakdown": _build_transport_breakdown(
                        weight_kg=cached_weight,
                        origin_km=cached_distance,
                        uk_hub_km=3.2,
                        mode=cached_transport,
                    ),
                    "co2_source": "rule_based_formula",
                }
                cached_attributes = standardize_attributes(cached_attributes, [
                    "origin", "country_of_origin", "facility_origin",
                    "origin_source", "origin_confidence",
                    "material_type", "brand", "price", "asin",
                    "image_url", "manufacturer", "category",
                ])

                # Restore full structured material data if available (saved on
                # the original scrape), so Tier 1/2 detection runs on cache hits
                # just as it would for a fresh scrape — critical for multi-material
                # products (shoes, clothing) where each component has its own row.
                _cached_amazon_mats = None
                if cached_product.materials_json:
                    try:
                        _cached_amazon_mats = json.loads(cached_product.materials_json)
                    except Exception:
                        pass

                # When materials_json is present but contains an empty list (sentinel
                # written for products whose spec table had no material rows), try to
                # reconstruct multi-material data from the stored material field.
                # The material field sometimes holds a comma-separated string like
                # "Sintered Stone, Metal, Engineered Wood" that the scraper extracted
                # from the spec table primary key before single-material normalisation.
                if not (_cached_amazon_mats and _cached_amazon_mats.get('materials')):
                    _mat_str = (cached_product.material or '').strip()
                    if _mat_str and _mat_str.lower() not in _POOR_MATERIALS:
                        _mat_parts = [
                            p.strip() for p in re.split(r'[,;/]', _mat_str)
                            if p.strip() and 2 <= len(p.strip()) <= 60
                        ]
                        if _mat_parts:
                            _cached_amazon_mats = {
                                'materials': [
                                    {'name': p, 'confidence_score': 0.7}
                                    for p in _mat_parts
                                ]
                            }

                try:
                    _cached_materials = deps['materials_service'].detect_materials(
                        {
                            'title': cached_product.title or '',
                            'material_type': cached_material or 'Unknown',
                            'description': cached_material or '',
                            'category': cached_product.category or '',
                            'price': float(cached_product.price) if cached_product.price else None,
                            'brand': cached_product.brand or '',
                        },
                        amazon_extracted_materials=_cached_amazon_mats,
                    )
                except Exception:
                    _cached_materials = None

                cached_attributes['materials'] = _cached_materials

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
            import concurrent.futures as _cf
            try:
                with _cf.ThreadPoolExecutor(max_workers=1) as _pool:
                    _future = _pool.submit(scrape_amazon_product_page, url)
                    product = _future.result(timeout=30)
            except _cf.TimeoutError:
                return jsonify({"error": "Scraping timed out — Amazon may be slow or blocking. Please try again."}), 504
            
            _BAD_SCRAPE_TITLES = {'unknown product', 'amazon product', 'unknown', '', 'consumer product'}
            _scraped_title = (product.get('title') or '').strip().lower()
            if not product or _scraped_title in _BAD_SCRAPE_TITLES:
                return jsonify({"error": "Failed to scrape product data"}), 400
            if _scraped_title == 'blocked':
                return jsonify({"error": "Amazon is blocking requests from this server. The SCRAPERAPI_KEY environment variable may be missing or expired."}), 503
                
            print(f"✅ Scraper success: {product.get('title', '')[:50]}...")

            # Material detection priority:
            # 1. Title-based guess (smart_guess_material on title) — most reliable for naming
            #    the primary product material (e.g. "Velvet Footstool" → Velvet)
            # 2. smart_guess_material on the spec table raw string (e.g. "100% Cotton, Polyester")
            #    — high confidence when title has no material keywords
            # 3. Raw scraped spec table value as-is (e.g. product details field says "Velvet")
            # 4. Full-page detect_material fallback
            title_material = smart_guess_material(product.get("title", ""))
            scraped_material = product.get("material_type") or product.get("material") or ""
            spec_table_material = smart_guess_material(scraped_material) if scraped_material else None

            if title_material:
                material = title_material
                print(f"🧠 Title-based material: {material}")
            elif spec_table_material:
                material = spec_table_material
                print(f"🧵 Spec-table-based material: {material} (raw: '{scraped_material}')")
            elif scraped_material and scraped_material.lower() not in ["unknown", "other", "", "not found", "n/a", "mixed"]:
                material = scraped_material
                print(f"📋 Scraped material (raw): {material}")
            else:
                material = "Mixed"
                print("⚠️ No material detected — defaulting to Mixed")

            product["material_type"] = material

            normalized_material = apply_material_title_consistency(product)
            if normalized_material and str(normalized_material).strip().lower() != str(material or '').strip().lower():
                print(f"🧬 Consistency override material: {material} -> {normalized_material}")
                material = normalized_material
            else:
                material = product.get("material_type") or material

            # Multi-material detection (primary / secondary / tertiary)
            try:
                materials_service = deps['materials_service']
                materials_result = materials_service.detect_materials(
                    {
                        'title': product.get('title', ''),
                        'material_type': material or 'Unknown',
                        'category': product.get('category') or '',
                        'price': product.get('price'),
                        'brand': product.get('brand') or '',
                    },
                    amazon_extracted_materials=product.get('amazon_materials_extracted'),
                )
            except Exception as _mat_err:
                print(f"⚠️ Materials detection failed: {_mat_err}")
                materials_result = None

            # CO₂ uncertainty — ±% based on material detection confidence tier.
            # High = spec table extraction; medium = title inference; low = fallback.
            _mat_conf_tier = (materials_result or {}).get('confidence', 'low')
            co2_uncertainty_pct = {'high': 20, 'medium': 35, 'low': 50}.get(_mat_conf_tier, 45)

            # Sync the material used for CO₂ calculation with what detect_materials
            # determined from the spec table (tiers 1–2 = high confidence spec data).
            # Tier 3+ are heuristics and may be wrong, so we keep the original material.
            if materials_result and materials_result.get('tier', 5) <= 2:
                _detected = (materials_result.get('primary_material') or '').strip()
                if _detected and _detected.lower() not in ('unknown', 'mixed', ''):
                    material = _detected
                    product['material_type'] = material
                    print(f"🧱 CO₂ material synced from spec table: {material}")

            # Get weight
            raw_weight = product.get("weight_kg") or product.get("raw_product_weight_kg")
            weight = float(raw_weight) if raw_weight else estimate_default_weight(
                product.get("title", ""), product.get("category", "")
            )
            # Sanity-check: if weight >150 kg it almost certainly means the scraper
            # returned grams instead of kilograms — auto-correct.
            # Guard: skip the correction for categories where genuinely heavy
            # items exist (furniture, appliances, garden, industrial, etc.) to
            # avoid silently breaking legitimate heavy-product estimates.
            _HEAVY_CATEGORIES = {
                'furniture', 'appliance', 'appliances', 'garden', 'outdoor',
                'industrial', 'sports equipment', 'gym', 'fitness', 'tools',
                'power tools', 'home improvement', 'plumbing', 'heating',
            }
            _cat_lower = (product.get('category') or '').lower()
            _is_legitimately_heavy = any(hc in _cat_lower for hc in _HEAVY_CATEGORIES)
            if weight > 150 and not _is_legitimately_heavy:
                weight /= 1000
                print(f"⚠️ Weight auto-corrected from grams: {weight} kg")
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
                _f = TRANSPORT_CO2_FACTOR
                if origin_country in water_crossing_countries:
                    if distance_km < 500:
                        return "Truck", _f["Truck"]
                    elif distance_km < 3000:
                        return "Ship",  _f["Ship"]
                    else:
                        return "Air",   _f["Air"]

                if distance_km < 1500:
                    return "Truck", _f["Truck"]
                elif distance_km < 20000:
                    return "Ship",  _f["Ship"]
                else:
                    return "Air",   _f["Air"]

            # Determine transport mode
            mode_name, mode_factor = determine_transport_mode(origin_distance_km, origin_country)
            if override_mode:
                mode_name   = override_mode
                mode_factor = TRANSPORT_CO2_FACTOR.get(override_mode, mode_factor)
            
            print(f"🚚 Transport: {mode_name} (factor: {mode_factor})")
            
            # === Rule-based CO2 calculation ===
            import numpy as np
            transport_co2 = weight * mode_factor * origin_distance_km / 1000
            material_intensity = MATERIAL_CO2_INTENSITY.get(material, 2.0)
            material_co2 = weight * material_intensity
            rule_co2 = transport_co2 + material_co2
            total_co2 = rule_co2

            # Rule-based eco grade from CO2 — DEFRA 2023 thresholds (must match ML training labels)
            if rule_co2 <= 0.05:
                eco_score_rule_based = "A+"
            elif rule_co2 <= 0.15:
                eco_score_rule_based = "A"
            elif rule_co2 <= 0.40:
                eco_score_rule_based = "B"
            elif rule_co2 <= 1.00:
                eco_score_rule_based = "C"
            elif rule_co2 <= 2.50:
                eco_score_rule_based = "D"
            elif rule_co2 <= 5.00:
                eco_score_rule_based = "E"
            else:
                eco_score_rule_based = "F"

            # === ML prediction using XGBoost (lazy-load on first request) ===
            import joblib

            if not (hasattr(app, 'xgb_model') and app.xgb_model):
                with _MODEL_LOAD_LOCK:
                    if not (hasattr(app, 'xgb_model') and app.xgb_model):  # double-check inside lock
                        try:
                            _cal_path = os.path.join(model_dir, "calibrated_model.pkl")
                            if os.path.exists(_cal_path):
                                app.xgb_model = joblib.load(_cal_path)
                                print("✅ Lazy-loaded calibrated_model.pkl")
                            else:
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
                    ('recycle_encoder', 'recyclability_encoder.pkl'),
                    ('origin_encoder', 'origin_encoder.pkl'),
                ]:
                    try:
                        app.encoders[_enc_name] = joblib.load(os.path.join(encoders_dir, _filename))
                    except Exception:
                        pass

            def _safe_enc(val, enc, default):
                if enc is None:
                    return 0
                # Normalise to title-case to match training data encoding
                normalised = str(val).strip().title() if val is not None else default
                try:
                    return enc.transform([normalised])[0]
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

                    # Origin is one of the primary model features.  When the
                    # origin was inferred from a weak heuristic (brand default,
                    # title keywords, etc.) rather than from an explicit spec
                    # table entry, the feature value fed to the model may be
                    # wrong.  We penalise the reported confidence accordingly so
                    # the UI can surface an honest uncertainty signal without
                    # requiring a model retrain.
                    if final_origin_confidence == "low":
                        confidence = max(5.0, round(confidence * 0.82, 1))
                    elif final_origin_confidence in ("unknown", None, ""):
                        confidence = max(5.0, round(confidence * 0.90, 1))

                    print(f"✅ ML prediction: {eco_score_ml} ({confidence}%)")

                    # SHAP per-prediction explanation
                    try:
                        import shap as shap_lib
                        # CalibratedClassifierCV wraps the base estimator — SHAP
                        # needs the underlying tree model, not the sklearn wrapper.
                        _shap_model = (
                            app.xgb_model.calibrated_classifiers_[0].estimator
                            if hasattr(app.xgb_model, 'calibrated_classifiers_')
                            else app.xgb_model
                        )
                        explainer = shap_lib.TreeExplainer(_shap_model)
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
                    _mat_intensities = MATERIAL_CO2_INTENSITY  # same source as main calc
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

            recyclability_pct = get_recyclability_pct(material)
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
                "material_type": product.get("material_type", "Not found"),
                "materials": materials_result,
                "recyclability": recyclability_label,
                "recyclability_percentage": recyclability_pct,
                "recyclability_description": f"{recyclability_pct}% of {material} is recycled globally",

                # Transport details
                "transport_mode": mode_name,
                "default_transport_mode": mode_name,
                "selected_transport_mode": override_mode or None,
                "emission_factors": {
                    m: {"factor": TRANSPORT_CO2_FACTOR[m], "co2_kg": transport_co2 if mode_name == m else 0}
                    for m in ("Truck", "Ship", "Air")
                },

                # Scoring - BOTH Methods for Comparison
                "eco_score_ml": eco_score_ml,
                "eco_score_ml_confidence": confidence,
                "eco_score_rule_based": eco_score_rule_based,
                "eco_score_rule_based_local_only": eco_score_rule_based,

                # Method Comparison
                # Note: both methods predict eco GRADES (A–F), not CO₂ kg.
                # The CO₂ kg value shown to users is always rule-based (formula).
                # ML predicts the grade directly from features; rule-based
                # calculates CO₂ then maps it to a grade via fixed thresholds.
                "method_agreement": "Yes" if eco_score_ml == eco_score_rule_based else "No",
                "co2_source": "rule_based_formula",
                "prediction_methods": {
                    "ml_prediction": {
                        "score": eco_score_ml,
                        "confidence": f"{confidence}%",
                        "method": "XGBoost grade classifier (11 features)",
                        "description": "Predicts eco grade (A–F) directly from product features using a trained model. Does not produce a CO₂ kg value.",
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
                        "method": "Formula: (weight × material intensity) + (weight × transport factor × distance)",
                        "description": "Calculates CO₂ kg from emission factors, then maps to grade via fixed thresholds. This value is shown as the CO₂ estimate."
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

                # CO₂ uncertainty range (±%) based on material detection confidence
                "co2_uncertainty_pct": co2_uncertainty_pct,

                # Aggregated data quality signal.
                # "high"   — spec table origin + spec table material (both tier ≤ 2)
                # "medium" — at least one input inferred from title/brand heuristics
                # "low"    — both origin and material are fallback guesses
                "data_quality": (
                    "high"   if final_origin_confidence == "high"   and _mat_conf_tier == "high"
                    else "low" if final_origin_confidence in ("low", "unknown") and _mat_conf_tier == "low"
                    else "medium"
                ),

                # Additional product info
                "brand": product.get("brand"),
                "price": product.get("price"),
                "asin": product.get("asin"),
                "image_url": product.get("image_url"),
                "gallery_images": product.get("gallery_images") or [],
                "manufacturer": product.get("manufacturer"),
                "category": product.get("category"),
                "climate_pledge_friendly": product.get("climate_pledge_friendly", False),
                "certifications": product.get("certifications") or [],
                "sold_by": product.get("sold_by"),
                "dispatched_from": product.get("dispatched_from"),

                # Transport CO₂ breakdown (international + UK hub + last-mile)
                "transport_breakdown": _build_transport_breakdown(
                    weight_kg=weight,
                    origin_km=origin_distance_km,
                    uk_hub_km=uk_distance_km,
                    mode=mode_name,
                ),
            }

            attributes = standardize_attributes(attributes, [
                "origin",
                "country_of_origin",
                "facility_origin",
                "origin_source",
                "origin_confidence",
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
                        "efficiency": None,
                        "efficiency_label": None,
                        "efficiency_description": (
                            None
                        ),
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
                # Serialise full multi-material spec data so cache hits can
                # restore Tier 1/2 detection without re-scraping.
                _amazon_mats = product.get('amazon_materials_extracted')
                # Always persist something (sentinel or real data) so the cache
                # bypass logic (materials_json IS NULL → re-scrape) only fires once
                # per product.  An empty list signals "spec table had no materials"
                # and falls through to title/category keyword detection on cache hits.
                _materials_json = json.dumps(_amazon_mats) if _amazon_mats else json.dumps({'materials': []})

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
                    'scraping_status': 'success',
                    'materials_json': _materials_json,
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
                    'data_quality': (
                        "high"   if final_origin_confidence == "high"   and _mat_conf_tier == "high"
                        else "low" if final_origin_confidence in ("low", "unknown") and _mat_conf_tier == "low"
                        else "medium"
                    ),
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
                    import fcntl as _fcntl
                    with open(_live_csv, 'a', newline='', encoding='utf-8') as _f:
                        _fcntl.flock(_f, _fcntl.LOCK_EX)
                        try:
                            _w = _csv.DictWriter(_f, fieldnames=list(_row.keys()))
                            if _write_header:
                                _w.writeheader()
                            _w.writerow(_row)
                        finally:
                            _fcntl.flock(_f, _fcntl.LOCK_UN)
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
    
    @app.route('/api/material-avg', methods=['GET'])
    def material_avg_co2():
        """Return average CO2 for products with the same material type."""
        from sqlalchemy import func as sql_func
        material_q = request.args.get('material', 'Mixed')
        try:
            row = db.session.query(
                sql_func.avg(EmissionCalculation.final_emission).label('avg_co2'),
                sql_func.count(EmissionCalculation.id).label('n')
            ).join(
                ScrapedProduct, EmissionCalculation.scraped_product_id == ScrapedProduct.id
            ).filter(
                ScrapedProduct.material.ilike(f'%{material_q}%'),
                EmissionCalculation.final_emission > 0,
                EmissionCalculation.final_emission < 500
            ).first()
            avg_val = float(row.avg_co2) if row and row.avg_co2 else None
            sample  = int(row.n)         if row and row.n      else 0
            return jsonify({
                "material": material_q,
                "avg_co2_kg": round(avg_val, 2) if avg_val else None,
                "sample_size": sample
            })
        except Exception as e:
            return jsonify({"material": material_q, "avg_co2_kg": None, "sample_size": 0})

    @app.route('/predict', methods=['POST'])
    def predict_ml():
        """Direct ML prediction endpoint"""
        try:
            import numpy as np
            import joblib

            # === Lazy load model if not already loaded ===
            # Priority: calibrated_model.pkl > xgb_model.json > eco_model.pkl (RF fallback)
            # This matches the startup loading order so both endpoints use the same model.
            if not (hasattr(app, 'xgb_model') and app.xgb_model):
                _loaded = False
                for _path, _label in [
                    (os.path.join(model_dir, "calibrated_model.pkl"), "calibrated_model.pkl"),
                    (os.path.join(model_dir, "eco_model.pkl"),        "eco_model.pkl"),
                ]:
                    if os.path.exists(_path):
                        try:
                            app.xgb_model = joblib.load(_path)
                            print(f"✅ Lazy-loaded {_label} for /predict")
                            _loaded = True
                            break
                        except Exception:
                            pass
                if not _loaded:
                    try:
                        import xgboost as xgb
                        _m = xgb.XGBClassifier()
                        _m.load_model(os.path.join(model_dir, "xgb_model.json"))
                        app.xgb_model = _m
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
                    ('recycle_encoder', 'recyclability_encoder.pkl'),
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
                # Normalise to title-case to match training data encoding
                normalised = str(value).strip().title() if value is not None else default
                try:
                    return encoder.transform([normalised])[0]
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
            proba_distribution = []
            if hasattr(app.xgb_model, 'predict_proba'):
                proba = app.xgb_model.predict_proba(X)
                confidence = round(float(np.max(proba[0])) * 100, 1)
                try:
                    classes = app.label_encoder.classes_
                    proba_distribution = [
                        {"grade": str(g), "probability": round(float(p) * 100, 1)}
                        for g, p in zip(classes, proba[0])
                    ]
                except Exception:
                    pass

            print(f"🧠 Predicted: {decoded_score} ({confidence}%)")

            return jsonify({
                'predicted_label': decoded_score,
                'confidence': f'{confidence}%',
                'proba_distribution': proba_distribution,
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
            return jsonify({"error": str(e)}), 500

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
                # Shape / geometry (e.g. "round wall clock", "square storage box")
                'round','square','oval','rectangular','circular','flat','curved',
                'shaped','slim','thin','thick','long','short','tall',
                # Motion / mechanism descriptors
                'rolling','sliding','folding','collapsible','retractable','extendable',
                # Salon / spa / wellness context (not product types)
                'massage','salon','spa','beauty','hydraulic','pneumatic','padded',
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
                # When the product type is confidently inferred, use ONLY those
                # terms as specific keywords.  Mixing in title-derived extras like
                # "round", "rolling", or "massage" causes unrelated products to be
                # returned when no exact match exists.
                specific_kws = inferred
                print(f"🔍 Product type inferred: {inferred} (category={category!r})")

            # Map Amazon's verbose category breadcrumb to one of the 6 DB categories.
            # The DB training dataset uses these exact strings: health_beauty, books_media,
            # sports_outdoors, electronics, home_kitchen, clothing.
            _AMAZON_CAT_MAP = [
                (['health', 'beauty', 'personal care', 'massage', 'medical', 'pharmacy',
                  'nutrition', 'supplement', 'vitamin', 'baby', 'hygiene', 'wellbeing',
                  'wellness', 'dental', 'skincare', 'haircare'],       'health_beauty'),
                (['book', 'kindle', 'music', 'cd', 'dvd', 'blu-ray', 'film', 'movie',
                  'video', 'magazine', 'newspaper', 'audio', 'podcast'],  'books_media'),
                (['sport', 'outdoor', 'fitness', 'gym', 'exercise', 'cycling', 'running',
                  'hiking', 'camping', 'football', 'tennis', 'golf', 'swimming',
                  'yoga', 'garden', 'gardening', 'patio', 'automotive', 'car', 'diy',
                  'tools', 'hardware'],                                   'sports_outdoors'),
                (['electronic', 'computer', 'laptop', 'phone', 'camera', 'tv',
                  'television', 'audio', 'speaker', 'headphone', 'tablet', 'printer',
                  'monitor', 'keyboard', 'gaming', 'console', 'software'],  'electronics'),
                (['home', 'kitchen', 'furniture', 'lamp', 'lighting', 'bedding',
                  'bathroom', 'storage', 'cleaning', 'pet', 'office', 'stationery',
                  'craft', 'art', 'food', 'drink', 'grocery'],            'home_kitchen'),
                (['clothing', 'fashion', 'apparel', 'shoe', 'boot', 'trainer',
                  'jacket', 'coat', 'dress', 'shirt', 'trouser', 'underwear',
                  'accessory', 'jewellery', 'watch', 'bag', 'luggage', 'handbag'],
                                                                           'clothing'),
            ]

            def _resolve_db_category(amazon_cat_raw: str) -> str:
                """Map an Amazon category breadcrumb to one of the 6 DB category values."""
                c = (amazon_cat_raw or '').lower()
                for keywords, db_cat in _AMAZON_CAT_MAP:
                    if any(kw in c for kw in keywords):
                        return db_cat
                return ''

            db_category = _resolve_db_category(category)

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

                # 5. DB category (mapped from Amazon's verbose breadcrumb to one of
                #    the 6 coarse training-data categories: home_kitchen, electronics, etc.)
                if db_category:
                    p = _run(Product.category.ilike(f'%{db_category}%'))
                    if p: return p, 'category'

                # 6. Any product of this grade — suppressed (returns irrelevant products)
                return (None, None)

            results       = []
            seen_ids      = set()
            seen_prefixes = set()

            for grade in better_grades[:4]:
                product, matched_by = _query_for_grade(grade, specific_kws, modifier_kws, category)
                if not product or product.id in seen_ids or matched_by == 'fallback':
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
            deps = _load_estimation_dependencies()
            _co2_to_grade = deps['co2_to_grade']

            submissions = ScrapedProduct.query.order_by(ScrapedProduct.id.desc()).limit(100).all()
            sub_ids = [s.id for s in submissions]
            # Bulk-fetch calculations and reviews in 2 queries instead of 2N
            _all_calcs = EmissionCalculation.query.filter(
                EmissionCalculation.scraped_product_id.in_(sub_ids)
            ).order_by(EmissionCalculation.id.desc()).all()
            _all_reviews = AdminReview.query.filter(
                AdminReview.scraped_product_id.in_(sub_ids)
            ).order_by(AdminReview.id.desc()).all()
            calc_map   = {c.scraped_product_id: c for c in reversed(_all_calcs)}
            review_map = {r.scraped_product_id: r for r in reversed(_all_reviews)}

            result = []
            for sub in submissions:
                calc   = calc_map.get(sub.id)
                review = review_map.get(sub.id)

                dist   = float(calc.transport_distance or 0) if calc else 0
                weight = float(sub.weight or 0.5)

                # Derive rule-based grade from stored rule_based_prediction
                rule_grade = None
                if calc and calc.rule_based_prediction:
                    try:
                        rule_grade = _co2_to_grade(float(calc.rule_based_prediction))
                    except Exception:
                        pass

                # eco_grade_ml is NULL for products scraped before the column existed.
                # Fall back to deriving it from ml_prediction so the column is never blank.
                ml_grade = calc.eco_grade_ml if calc and calc.eco_grade_ml else None
                if not ml_grade and calc and calc.ml_prediction:
                    try:
                        ml_grade = _co2_to_grade(float(calc.ml_prediction))
                    except Exception:
                        pass

                result.append({
                    'id': sub.id,
                    'url': sub.amazon_url,
                    'title': sub.title or 'Unknown product',
                    'material': sub.material,
                    'origin': sub.origin_country,
                    'brand': sub.brand,
                    'predicted_label': ml_grade,
                    'rule_based_label': rule_grade,
                    'confidence': f"{float(calc.ml_confidence):.1f}%" if calc and calc.ml_confidence else None,
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

    @app.route('/admin/bulk-approve-matching', methods=['POST'])
    def admin_bulk_approve_matching():
        """
        Auto-approve all submissions where the derived ML grade and rule-based
        grade agree, and no true label has been set yet. When two independent
        methods (ML model + deterministic rule calculation) reach the same
        conclusion, confidence is high enough to treat it as ground truth.
        Requires admin auth.
        """
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        try:
            deps = _load_estimation_dependencies()
            _co2_to_grade = deps['co2_to_grade']

            submissions = ScrapedProduct.query.order_by(ScrapedProduct.id.desc()).limit(100).all()
            sub_ids = [s.id for s in submissions]
            _all_calcs   = EmissionCalculation.query.filter(EmissionCalculation.scraped_product_id.in_(sub_ids)).order_by(EmissionCalculation.id.desc()).all()
            _all_reviews = AdminReview.query.filter(AdminReview.scraped_product_id.in_(sub_ids)).order_by(AdminReview.id.desc()).all()
            calc_map   = {c.scraped_product_id: c for c in reversed(_all_calcs)}
            review_map = {r.scraped_product_id: r for r in reversed(_all_reviews)}

            approved = 0
            skipped = 0
            admin_user_id = user.get('id')

            for sub in submissions:
                calc   = calc_map.get(sub.id)
                review = review_map.get(sub.id)

                # Skip already-labelled products
                if review and review.corrected_grade:
                    skipped += 1
                    continue

                if not calc:
                    skipped += 1
                    continue

                # Derive ML grade (stored or calculated from ml_prediction)
                ml_grade = calc.eco_grade_ml or None
                if not ml_grade and calc.ml_prediction:
                    try:
                        ml_grade = _co2_to_grade(float(calc.ml_prediction))
                    except Exception:
                        pass

                # Derive rule grade
                rule_grade = None
                if calc.rule_based_prediction:
                    try:
                        rule_grade = _co2_to_grade(float(calc.rule_based_prediction))
                    except Exception:
                        pass

                # Only approve when both methods agree
                if not ml_grade or not rule_grade or ml_grade != rule_grade:
                    skipped += 1
                    continue

                if review:
                    review.corrected_grade = ml_grade
                    review.review_status = 'approved'
                    review.reviewed_by = admin_user_id
                    review.reviewed_at = datetime.utcnow()
                    review.admin_notes = 'Auto-approved: ML and rule-based grades agree'
                else:
                    db.session.add(AdminReview(
                        scraped_product_id=sub.id,
                        corrected_grade=ml_grade,
                        review_status='approved',
                        reviewed_by=admin_user_id,
                        reviewed_at=datetime.utcnow(),
                        admin_notes='Auto-approved: ML and rule-based grades agree',
                    ))
                approved += 1

            db.session.commit()
            return jsonify({
                'success': True,
                'approved': approved,
                'skipped': skipped,
                'message': f'{approved} submissions auto-approved, {skipped} skipped (already labelled or grades disagree)',
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def _bulk_approve_by_source(source: str):
        """
        Shared logic for bulk-approve-ml and bulk-approve-rule.
        source='ml'   → set true_label = derived ML grade for all unlabelled rows
        source='rule' → set true_label = derived rule grade for all unlabelled rows
        """
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        try:
            deps = _load_estimation_dependencies()
            _co2_to_grade = deps['co2_to_grade']
            submissions = ScrapedProduct.query.order_by(ScrapedProduct.id.desc()).limit(100).all()
            sub_ids = [s.id for s in submissions]
            _all_calcs   = EmissionCalculation.query.filter(EmissionCalculation.scraped_product_id.in_(sub_ids)).order_by(EmissionCalculation.id.desc()).all()
            _all_reviews = AdminReview.query.filter(AdminReview.scraped_product_id.in_(sub_ids)).order_by(AdminReview.id.desc()).all()
            calc_map   = {c.scraped_product_id: c for c in reversed(_all_calcs)}
            review_map = {r.scraped_product_id: r for r in reversed(_all_reviews)}

            approved = 0
            skipped = 0
            admin_user_id = user.get('id')

            for sub in submissions:
                calc   = calc_map.get(sub.id)
                review = review_map.get(sub.id)

                if review and review.corrected_grade:
                    skipped += 1
                    continue
                if not calc:
                    skipped += 1
                    continue

                grade = None
                if source == 'ml':
                    grade = calc.eco_grade_ml or None
                    if not grade and calc.ml_prediction:
                        try:
                            grade = _co2_to_grade(float(calc.ml_prediction))
                        except Exception:
                            pass
                else:  # rule
                    if calc.rule_based_prediction:
                        try:
                            grade = _co2_to_grade(float(calc.rule_based_prediction))
                        except Exception:
                            pass

                if not grade:
                    skipped += 1
                    continue

                note = f'Auto-approved: using {"ML" if source == "ml" else "rule-based"} grade'
                if review:
                    review.corrected_grade = grade
                    review.review_status = 'approved'
                    review.reviewed_by = admin_user_id
                    review.reviewed_at = datetime.utcnow()
                    review.admin_notes = note
                else:
                    db.session.add(AdminReview(
                        scraped_product_id=sub.id,
                        corrected_grade=grade,
                        review_status='approved',
                        reviewed_by=admin_user_id,
                        reviewed_at=datetime.utcnow(),
                        admin_notes=note,
                    ))
                approved += 1

            db.session.commit()
            return jsonify({'success': True, 'approved': approved, 'skipped': skipped})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/bulk-approve-ml', methods=['POST'])
    def admin_bulk_approve_ml():
        """Bulk-approve all unlabelled submissions using the derived ML grade."""
        return _bulk_approve_by_source('ml')

    @app.route('/admin/bulk-approve-rule', methods=['POST'])
    def admin_bulk_approve_rule():
        """Bulk-approve all unlabelled submissions using the derived rule-based grade."""
        return _bulk_approve_by_source('rule')

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
    
    @app.route('/api/admin/backfill-materials', methods=['POST'])
    def admin_backfill_materials():
        """
        One-time maintenance endpoint: populate materials_json for existing
        ScrapedProduct rows that were saved before the column existed.

        Parses each row's `material` field (already normalised by the scraper)
        into a synthetic amazon_extracted_materials dict so future cache hits
        use Tier 1/2 detection instead of falling back to Tier 3 guessing.

        Skips rows that already have materials_json or have material='Mixed'/
        'Unknown'.  Safe to call multiple times (idempotent).

        Requires admin session.
        """
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        import re as _re

        # Very simple percentage parser: "95% Cotton, 5% Elastane" or
        # "Cotton 95%, Elastane 5%"
        _PCT_FIRST = _re.compile(
            r'(\d+(?:\.\d+)?)\s*%\s*([A-Za-z][A-Za-z\s\-]{1,30}?)(?=[,;/+]|\d|$)'
        )
        _PCT_LAST = _re.compile(
            r'([A-Za-z][A-Za-z\s\-]{1,30}?)\s+(\d+(?:\.\d+)?)\s*%(?=[,;/+]|$)'
        )

        _SKIP = {'mixed', 'unknown', 'other', 'n/a', '', 'not found'}

        def _build_materials_json(material_str: str):
            if not material_str or material_str.strip().lower() in _SKIP:
                return None
            raw = material_str.strip()

            # Try percentage composition first
            matches = _PCT_FIRST.findall(raw)
            if not matches:
                matches = [(pct, nm) for nm, pct in _PCT_LAST.findall(raw)]
            if matches:
                total = sum(float(p) for p, _ in matches)
                if 85 <= total <= 105:
                    items = [
                        {'name': nm.strip().title(), 'confidence_score': 0.9,
                         'weight': round(float(p) / 100, 4)}
                        for p, nm in matches if nm.strip()
                    ]
                    if items:
                        return json.dumps({'materials': items})

            # Fallback: split on separators, treat each token as a material
            parts = [p.strip() for p in _re.split(r'[,;/\+&]', raw) if p.strip()]
            if not parts:
                return None
            items = [{'name': p.title(), 'confidence_score': 0.75} for p in parts]
            return json.dumps({'materials': items})

        try:
            rows = ScrapedProduct.query.filter(
                ScrapedProduct.materials_json.is_(None),
                ScrapedProduct.material.isnot(None),
            ).all()

            updated = 0
            skipped = 0
            for row in rows:
                mj = _build_materials_json(row.material)
                if mj:
                    row.materials_json = mj
                    updated += 1
                else:
                    skipped += 1

            db.session.commit()
            return jsonify({
                'success': True,
                'updated': updated,
                'skipped_no_useful_material': skipped,
                'total_processed': len(rows),
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/fix-co2', methods=['POST'])
    def admin_fix_co2():
        """
        Maintenance endpoint: recalculate rule_based_prediction for emission records
        where weight was historically stored in grams instead of kg, causing CO₂
        values that are ~1000× too high.

        Detection: if stored weight > 150 kg (impossible for an Amazon product) it
        was stored in grams.  We divide by 1000, recalculate rule CO₂, and update
        both the scraped_product.weight and emission_calculation.rule_based_prediction.

        Safe to call multiple times (idempotent — only updates records that changed).
        """
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        _material_intensity = MATERIAL_CO2_INTENSITY  # single source of truth
        _mode_factor = {
            "Truck": 0.15, "Ship": 0.03, "Air": 0.5,
            "Land": 0.15, "Sea": 0.03,
        }

        fixed = 0
        skipped = 0

        try:
            all_calcs = EmissionCalculation.query.join(ScrapedProduct).all()
            for calc in all_calcs:
                sp = calc.scraped_product
                if not sp:
                    skipped += 1
                    continue

                raw_w = float(sp.weight or 0)
                if raw_w <= 0:
                    skipped += 1
                    continue

                # Detect grams-stored-as-kg: threshold 150 kg
                if raw_w <= 150:
                    skipped += 1
                    continue

                # Convert to kg
                weight_kg = raw_w / 1000
                material = sp.material or 'Other'
                intensity = _material_intensity.get(material, 2.0)
                mode = calc.transport_mode or 'Ship'
                factor = _mode_factor.get(mode, 0.03)
                distance = float(calc.transport_distance or 9000)

                new_rule_co2 = round(weight_kg * intensity + weight_kg * factor * distance / 1000, 2)

                # Update emission record
                calc.rule_based_prediction = new_rule_co2
                if calc.ml_prediction and float(calc.ml_prediction) > 0:
                    # Keep ML as-is but fix final emission to rule average
                    calc.final_emission = round((new_rule_co2 + float(calc.ml_prediction)) / 2, 2)
                else:
                    calc.final_emission = new_rule_co2

                # Fix weight in scraped_products too
                sp.weight = weight_kg
                fixed += 1

            db.session.commit()
            return jsonify({'success': True, 'fixed': fixed, 'skipped': skipped})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/export-labelled-csv', methods=['GET'])
    def admin_export_labelled_csv():
        """Export approved labelled submissions as CSV for ML retraining"""
        user = session.get('user')
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        import csv
        import io as _io

        reviews = (
            AdminReview.query
            .filter(
                AdminReview.review_status == 'approved',
                AdminReview.corrected_grade.isnot(None),
            )
            .all()
        )

        output = _io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'title', 'material', 'weight_kg', 'transport_mode',
            'transport_distance_km', 'origin_country',
            'true_label', 'ml_grade', 'rule_co2_kg', 'ml_co2_kg',
        ])

        for review in reviews:
            sp = review.scraped_product
            if not sp:
                continue
            calc = (
                EmissionCalculation.query
                .filter_by(scraped_product_id=sp.id)
                .order_by(EmissionCalculation.id.desc())
                .first()
            )
            writer.writerow([
                sp.title or '',
                sp.material or '',
                float(sp.weight) if sp.weight else '',
                calc.transport_mode if calc else '',
                float(calc.transport_distance) if calc and calc.transport_distance else '',
                sp.origin_country or '',
                review.corrected_grade,
                calc.eco_grade_ml if calc else '',
                float(calc.rule_based_prediction) if calc and calc.rule_based_prediction else '',
                float(calc.ml_prediction) if calc and calc.ml_prediction else '',
            ])

        output.seek(0)
        from flask import Response as _Response
        return _Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=labelled_data.csv'},
        )

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
    @limiter.limit("5 per minute")
    def signup():
        """User registration — saves to DB with hashed password."""
        import re as _re
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
            if not _re.search(r'[A-Z]', password) or not _re.search(r'[0-9]', password):
                return jsonify({'error': 'Password must contain at least one uppercase letter and one number'}), 400
            if email and not _re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                return jsonify({'error': 'Invalid email address'}), 400
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
                    'data_quality': calc.data_quality if calc else None,
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

    @app.route('/api/my/carbon-timeline', methods=['GET'])
    def my_carbon_timeline():
        """Monthly CO₂ totals for the logged-in user — drives the carbon timeline chart."""
        user_info = session.get('user')
        if not user_info:
            return jsonify({'error': 'Login required'}), 401
        uid = user_info['id']
        try:
            products = (
                ScrapedProduct.query
                .filter_by(user_id=uid)
                .order_by(ScrapedProduct.created_at.asc())
                .all()
            )
            monthly: dict = {}
            for p in products:
                if not p.created_at:
                    continue
                calc = EmissionCalculation.query.filter_by(
                    scraped_product_id=p.id
                ).order_by(EmissionCalculation.id.desc()).first()
                co2 = float(calc.final_emission) if calc and calc.final_emission else 0.0
                month_key = p.created_at.strftime('%Y-%m')
                if month_key not in monthly:
                    monthly[month_key] = {'month': month_key, 'co2_kg': 0.0, 'scans': 0}
                monthly[month_key]['co2_kg'] += co2
                monthly[month_key]['scans'] += 1

            timeline = sorted(monthly.values(), key=lambda x: x['month'])
            for entry in timeline:
                entry['co2_kg'] = round(entry['co2_kg'], 2)

            return jsonify({'timeline': timeline})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ── Enterprise dashboard blueprint ───────────────────────────────────────
    try:
        from backend.routes.enterprise_dashboard import enterprise_bp
        app.register_blueprint(enterprise_bp)
        print("✅ Enterprise dashboard blueprint registered")
    except Exception as _e:
        print(f"⚠️  Enterprise blueprint not loaded: {_e}")

    # ── AI Visual Material Analysis ───────────────────────────────────────────
    # ── Category hints injected into the vision prompt ───────────────────────
    _IMAGE_CATEGORY_HINTS = {
        'guitar': (
            "GUITAR — typical composition by WEIGHT:\n"
            "• Body (alder/mahogany/ash/basswood solid wood): 45–55%\n"
            "• Neck (maple or mahogany): 12–18%\n"
            "• Fretboard (rosewood/ebony/maple): 5–8%\n"
            "• Hardware — bridge, tuning pegs, strap buttons (zinc alloy or steel): 8–14%\n"
            "• Strings (steel/nickel wound): 1–2%\n"
            "• Electronics — pickups, pots, switch (copper coil + ABS plastic): 3–6%\n"
            "• Polyester finish/lacquer: 2–4%\n"
            "Acoustic guitars have no electronics; identify body wood from grain/colour if possible."
        ),
        'bass guitar': (
            "BASS GUITAR — similar to electric guitar but heavier hardware and thicker neck.\n"
            "• Body (alder/ash): 40–50%  • Neck (maple): 14–20%  • Fretboard: 5–8%\n"
            "• Heavy bridge + tuning machines (zinc/steel): 12–18%  • Electronics: 4–7%"
        ),
        'acoustic guitar': (
            "ACOUSTIC GUITAR — no pickups/electronics:\n"
            "• Top (spruce or cedar): 12–18%  • Back & sides (mahogany/rosewood/maple): 28–38%\n"
            "• Neck (mahogany/maple): 12–16%  • Fretboard (rosewood/ebony): 5–8%\n"
            "• Bridge + tuning machines (rosewood + nickel/chrome): 8–12%\n"
            "• Bracing + linings (spruce/basswood): 8–12%"
        ),
        'laptop': (
            "LAPTOP — typical composition by WEIGHT:\n"
            "• Battery pack (lithium-ion cells + aluminium casing): 22–30%\n"
            "• Display assembly (aluminosilicate glass + LCD + aluminium frame): 18–25%\n"
            "• Chassis lid + base (aluminium alloy or ABS plastic): 20–28%\n"
            "• Motherboard (FR4 fibreglass PCB + copper + silicon): 10–15%\n"
            "• Keyboard assembly (ABS plastic keys + steel plate): 6–10%\n"
            "• Thermal system (copper heat pipes + aluminium heatsink + fan): 4–8%\n"
            "Premium models use aluminium throughout; budget models use ABS plastic chassis."
        ),
        'smartphone': (
            "SMARTPHONE — typical composition by WEIGHT:\n"
            "• Battery (lithium-ion polymer): 25–35%\n"
            "• PCB + SoC + memory chips (FR4 + copper + silicon + solder): 15–22%\n"
            "• Aluminium or stainless steel frame: 15–22%\n"
            "• Front glass (Gorilla Glass or ceramic): 10–15%\n"
            "• Rear glass or polycarbonate back: 8–14%\n"
            "• Camera module (glass lenses + copper actuator + plastic): 3–6%\n"
            "• Display panel (OLED/LCD layers): 4–7%"
        ),
        'office chair': (
            "OFFICE / GAMING CHAIR — IMPORTANT: metal is much denser than foam.\n"
            "• Steel frame + recline mechanism: 35–50%\n"
            "• Polyurethane foam padding (VERY low density ~0.04 g/cm³ — large but light): 8–16%\n"
            "• Fabric/mesh/leather upholstery: 8–14%\n"
            "• Nylon or ABS plastic seat shell, back shell, armrests: 14–22%\n"
            "• Aluminium or steel gas-lift cylinder: 6–10%\n"
            "• Nylon star base + polyurethane castor wheels: 5–9%"
        ),
        'dining chair': (
            "DINING CHAIR:\n"
            "• Solid wood or steel frame legs: 50–65%\n"
            "• Seat & back padding (foam): 8–15%\n"
            "• Upholstery (fabric/leather/velvet): 10–18%\n"
            "• Hardware (screws, brackets — steel): 3–6%"
        ),
        'sofa': (
            "SOFA / COUCH:\n"
            "• Steel frame + spring system: 35–48%\n"
            "• Polyurethane foam cushioning (bulky but light): 10–18%\n"
            "• Fabric/leather/velvet upholstery: 12–20%\n"
            "• Solid wood or engineered wood base/legs: 12–18%\n"
            "• Sinuous spring wire (steel): 5–8%"
        ),
        'desk': (
            "DESK / TABLE:\n"
            "• Tabletop (MDF, solid wood, or particle board): 50–65%\n"
            "• Legs/frame (steel tube, solid wood, or powder-coated steel): 28–42%\n"
            "• Hardware (brackets, bolts, levelling feet — steel): 4–8%\n"
            "• Veneer or laminate surface coating (if visible): 2–5%"
        ),
        'water bottle': (
            "INSULATED WATER BOTTLE / FLASK:\n"
            "• Main body double-wall (stainless steel 18/8): 78–86%\n"
            "• Lid / cap (polypropylene plastic): 10–16%\n"
            "• Silicone seal ring + base bumper: 3–6%"
        ),
        'cookware': (
            "COOKWARE (pan/pot/wok) — density dominates weight estimate:\n"
            "• Cast iron body: ~7.2 g/cm³ — very heavy for size → 80–90% if cast iron\n"
            "• Stainless steel body: ~8.0 g/cm³ → 72–82%\n"
            "• Aluminium body: ~2.7 g/cm³ → 65–75%\n"
            "• Phenolic/bakelite handle: 12–20%\n"
            "• PTFE or ceramic non-stick coating: 1–3%\n"
            "• Steel rivets: 1–2%"
        ),
        'backpack': (
            "BACKPACK / BAG:\n"
            "• Main body fabric (nylon 420D/600D or polyester): 40–52%\n"
            "• Zippers + pulls (nylon coil + zinc alloy): 8–14%\n"
            "• Webbing straps (nylon/polyester): 10–15%\n"
            "• Polypropylene or ABS frame/stiffener: 8–12%\n"
            "• EVA foam back-panel + shoulder-pad padding: 5–10%\n"
            "• Acetal or aluminium buckles: 3–6%"
        ),
        'jacket': (
            "JACKET / COAT:\n"
            "• Outer shell (polyester, nylon, or cotton): 32–44%\n"
            "• Insulation (down feathers, polyester fiberfill, or fleece): 22–35%\n"
            "• Lining (polyester or nylon): 14–22%\n"
            "• Zips (nylon coil + metal pulls): 4–7%\n"
            "• Buttons/snaps (plastic or metal): 1–3%"
        ),
        'shoe': (
            "FOOTWEAR / TRAINER / BOOT:\n"
            "• Upper (leather, suede, mesh, or synthetic): 32–45%\n"
            "• EVA foam midsole: 20–32%\n"
            "• Carbon rubber outsole: 16–24%\n"
            "• Polyurethane foam insole: 5–10%\n"
            "• Polyester laces: 1–3%"
        ),
        'headphones': (
            "HEADPHONES / EARPHONES:\n"
            "• ABS plastic headband + ear-cup housings: 28–38%\n"
            "• Driver units (copper voice coil + neodymium magnet + plastic housing): 16–24%\n"
            "• Polyurethane + protein-leather ear pads: 10–18%\n"
            "• Steel headband spring: 8–14%\n"
            "• PCB + battery (if wireless): 8–14%\n"
            "• Copper cable or charging cable + PVC sheath: 6–12%"
        ),
        'bicycle': (
            "BICYCLE:\n"
            "• Frame (aluminium alloy 6061 or carbon fibre or steel): 28–40%\n"
            "• Wheels — rims + spokes + tyres (aluminium + steel + rubber): 25–35%\n"
            "• Drivetrain — chain, cassette, cranks (steel + aluminium): 12–18%\n"
            "• Brakes + cables (aluminium + steel): 5–9%\n"
            "• Handlebar + stem (aluminium): 5–8%\n"
            "• Saddle (steel rails + foam + synthetic leather): 3–6%"
        ),
    }

    def _get_category_hint(title: str) -> str:
        """Match product title to a category and return composition hint."""
        t = title.lower()
        # Order matters — more specific first
        checks = [
            (['acoustic guitar'],                   'acoustic guitar'),
            (['bass guitar'],                        'bass guitar'),
            (['electric guitar', 'guitar'],          'guitar'),
            (['laptop', 'macbook', 'notebook'],      'laptop'),
            (['iphone', 'samsung galaxy', 'pixel phone', 'smartphone'], 'smartphone'),
            (['office chair', 'gaming chair', 'desk chair', 'task chair'], 'office chair'),
            (['dining chair', 'kitchen chair'],      'dining chair'),
            (['sofa', 'couch', 'settee', 'loveseat'], 'sofa'),
            (['desk', 'standing desk', 'workstation', 'coffee table', 'side table', 'dining table'], 'desk'),
            (['water bottle', 'flask', 'tumbler', 'thermos', 'insulated bottle'], 'water bottle'),
            (['frying pan', 'saucepan', 'wok', 'skillet', 'cookware', 'casserole'], 'cookware'),
            (['backpack', 'rucksack', 'bag', 'satchel', 'tote'],  'backpack'),
            (['jacket', 'coat', 'hoodie', 'gilet', 'puffer'],     'jacket'),
            (['shoe', 'trainer', 'sneaker', 'boot', 'sandal'],    'shoe'),
            (['headphone', 'earphone', 'earbud', 'airpod', 'headset'], 'headphones'),
            (['bicycle', 'bike', 'mountain bike', 'road bike'],   'bicycle'),
        ]
        for keywords, key in checks:
            if any(kw in t for kw in keywords):
                return _IMAGE_CATEGORY_HINTS.get(key, '')
        return ''

    @app.route('/api/analyse-image', methods=['POST', 'OPTIONS'])
    def analyse_image():
        """Use Claude vision + category-aware reasoning to identify materials from a product image."""
        if request.method == 'OPTIONS':
            return '', 204

        data = request.get_json() or {}
        image_url = (data.get('image_url') or '').strip()
        product_title = (data.get('title') or '')
        gallery_images = [u for u in (data.get('gallery_images') or []) if u and u != image_url]
        spec_materials = data.get('spec_materials') or {}

        if not image_url:
            return jsonify({'error': 'image_url required'}), 400

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'Vision analysis not configured — ANTHROPIC_API_KEY missing'}), 503

        try:
            import anthropic as _anthropic
            import base64

            _http = __import__('requests')
            _headers = {'User-Agent': 'Mozilla/5.0 (compatible; ImpactTracker/1.0)'}

            def _fetch_image(url):
                """Fetch image and return (base64_str, media_type) or None on failure."""
                try:
                    r = _http.get(url, timeout=12, headers=_headers)
                    r.raise_for_status()
                    ct = r.headers.get('content-type', 'image/jpeg')
                    if 'png' in ct:   mt = 'image/png'
                    elif 'webp' in ct: mt = 'image/webp'
                    elif 'gif' in ct:  mt = 'image/gif'
                    else:              mt = 'image/jpeg'
                    return base64.standard_b64encode(r.content).decode('utf-8'), mt
                except Exception:
                    return None

            # Collect up to 3 images: main + up to 2 gallery angles
            images_to_send = []
            main = _fetch_image(image_url)
            if main:
                images_to_send.append(main)
            for gurl in gallery_images[:4]:   # try up to 4, take first 2 that load
                if len(images_to_send) >= 3:
                    break
                img = _fetch_image(gurl)
                if img:
                    images_to_send.append(img)

            if not images_to_send:
                return jsonify({'error': 'Could not fetch product image'}), 502

            client = _anthropic.Anthropic(api_key=api_key)

            # Build spec-table hint if we already know the materials
            spec_hint = ''
            if spec_materials:
                _sp = (spec_materials.get('primary_material') or '').strip()
                _ss = [m.get('name', '') for m in (spec_materials.get('secondary_materials') or []) if m.get('name')]
                if _sp and _sp.lower() not in ('unknown', 'mixed', ''):
                    spec_hint = (
                        f"\nSPEC TABLE EVIDENCE: Amazon's spec table identifies the primary material as "
                        f"'{_sp}'"
                        + (f" with secondary: {', '.join(_ss)}" if _ss else "")
                        + ". Treat this as strong prior evidence — confirm visually or explain any discrepancy.\n"
                    )

            category_hint = _get_category_hint(product_title)
            category_block = f"\nCATEGORY-SPECIFIC GUIDE:\n{category_hint}\n" if category_hint else ""
            n_images = len(images_to_send)
            multi_note = (
                f"\nYou have been provided with {n_images} product images showing different angles. "
                "Use ALL images together for the most accurate assessment — different angles reveal different components.\n"
            ) if n_images > 1 else ""

            system_prompt = (
                "You are a senior materials scientist specialising in consumer product composition analysis. "
                "You combine visual evidence from product images with deep knowledge of manufacturing conventions "
                "to produce accurate material breakdowns with weight-percentage estimates. "
                "You never guess generically — you reason from what you can see and what you know about how products are made."
            )

            user_prompt = f"""PRODUCT TITLE: {product_title}
{multi_note}{spec_hint}{category_block}
IMPORTANT: Images may contain backgrounds, packaging, Amazon badges (Prime, Climate Pledge), certification logos, or lifestyle props. Analyse ONLY the physical product itself.

TASK: Produce a precise material composition breakdown by weight.

REASONING METHOD:
1. Identify the product type and every distinct component — visible AND implied/hidden (e.g. battery inside a phone, steel mechanism inside a chair).
2. Assign the most specific material name using visual cues (colour, texture, sheen, transparency, grain) and manufacturing knowledge.
3. Estimate weight % using MATERIAL DENSITY — a small metal part outweighs a large foam cushion:

   DENSITY (g/cm³):
   Steel/Cast Iron: 7.6–8.1 | Stainless Steel: 7.9–8.1 | Copper: 8.9 | Zinc alloy: 6.5
   Aluminium: 2.7 | Glass: 2.5 | Ceramic: 2.4
   ABS Plastic: 1.04 | Polypropylene: 0.91 | Polycarbonate: 1.2 | Nylon: 1.15 | PVC: 1.4
   Solid Wood: 0.65–0.85 | MDF: 0.75 | Bamboo: 0.7
   Silicone: 1.1 | Natural Rubber: 0.93 | Neoprene: 1.25
   EVA Foam: 0.05–0.15 | Polyurethane Foam: 0.03–0.06 ← VERY LIGHT
   Cotton: 0.15 | Leather: 0.86 | Down: 0.03
   Lithium-Ion Battery: 2.8 | FR4 PCB: 1.9 | Carbon Fibre: 1.55

4. Multi-part products (instruments, furniture, electronics): list ALL major components separately.

OUTPUT — return ONLY this JSON, no markdown:
{{"components":[{{"part":"name","material":"Specific Name","percentage":45,"reasoning":"visual evidence + density logic"}}],"confidence":"high","notes":"caveats if any"}}

RULES:
- 3–8 components (more for guitars, laptops, bicycles)
- Percentages = integers summing to exactly 100
- Specific names: "Stainless Steel 18/8" not "Metal"; "ABS Plastic" not "Plastic"; "EVA Foam" not "Foam"
- confidence: "high"=clearly visible, "medium"=some uncertainty, "low"=obscured/packaged"""

            # Build multi-image content block
            content = []
            for b64, mt in images_to_send:
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mt, "data": b64},
                })
            content.append({"type": "text", "text": user_prompt})

            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
            )

            response_text = message.content[0].text.strip()
            if '```' in response_text:
                response_text = re.sub(r'```(?:json)?\s*|\s*```', '', response_text).strip()

            result = json.loads(response_text)
            components = result.get('components', [])
            if not components:
                return jsonify({'error': 'No components detected in image'}), 422

            # Normalise percentages to sum to exactly 100
            total = sum(c.get('percentage', 0) for c in components)
            if total > 0 and total != 100:
                # Adjust largest component to absorb rounding error
                for c in components:
                    c['percentage'] = round(c.get('percentage', 0) * 100 / total)
                diff = 100 - sum(c['percentage'] for c in components)
                if diff != 0:
                    largest = max(components, key=lambda c: c['percentage'])
                    largest['percentage'] += diff

            print(f"🔬 Image analysis: {len(components)} components detected for '{product_title[:40]}'")
            return jsonify({
                'components': components,
                'confidence': result.get('confidence', 'medium'),
                'category_detected': result.get('category_detected', ''),
                'notes': result.get('notes', ''),
            })

        except json.JSONDecodeError as e:
            print(f"⚠️ Image analysis JSON parse error: {e}")
            return jsonify({'error': 'Could not parse AI response as JSON'}), 500
        except Exception as e:
            print(f"⚠️ Image analysis error: {e}")
            return jsonify({'error': str(e)}), 500

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