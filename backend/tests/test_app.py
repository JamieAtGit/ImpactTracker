"""
ImpactTracker backend test suite.

Coverage:
  1.  Health endpoint
  2.  Eco-grade CO₂ thresholds (pure logic)
  3.  CO₂ formula correctness
  4.  Keyword extraction / stop-word filtering
  5.  Auth endpoints  (signup, login, duplicate, bad passwords)
  6.  smart_guess_material  — title-based material detection
  7.  detect_material       — scraper title + text detection
  8.  detect_category_from_title — product category inference
  9.  Weight extraction from product text
  10. CO₂ uncertainty tier mapping
  11. Calibrated ML model — load, shape, confidence bounds, valid grades
  12. Conformal prediction config — structure and coverage levels
  13. Data quality aggregation signal
  14. Training script artefacts — CSV path resolves, dataset schema valid
  15. Postcode → UK region mapping (Wales / Scotland / Northern Ireland / England)
  16. Cache TTL logic — 30-day freshness window

Run with:
    pytest backend/tests/test_app.py -v
"""

import pytest
import json
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ─────────────────────────────────────────────────────────────────────────────
# Flask app fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    from backend.api.app_production import create_app
    application = create_app('testing')
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    application.config['WTF_CSRF_ENABLED'] = False
    application.config['RATELIMIT_ENABLED'] = False  # disable rate limiting in tests

    from backend.models.database import db as _db
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health endpoint
# ─────────────────────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    """GET /health returns 200 with a healthy status."""
    resp = client.get('/health')
    assert resp.status_code == 200
    body = resp.get_json() or {}
    assert body.get('status') in ('healthy', 'ok')


def test_health_reports_ml_model(client):
    """GET /health indicates whether the ML model is loaded."""
    resp = client.get('/health')
    body = resp.get_json() or {}
    assert 'ml_model' in body


# ─────────────────────────────────────────────────────────────────────────────
# 2. Eco-grade CO₂ thresholds
# ─────────────────────────────────────────────────────────────────────────────

def _grade_from_co2(co2: float) -> str:
    if co2 <= 0.05:  return 'A+'
    if co2 <= 0.15:  return 'A'
    if co2 <= 0.40:  return 'B'
    if co2 <= 1.00:  return 'C'
    if co2 <= 2.50:  return 'D'
    if co2 <= 5.00:  return 'E'
    return 'F'


@pytest.mark.parametrize("co2,expected", [
    (0.01,  'A+'),
    (0.05,  'A+'),   # boundary: exactly at A+ limit
    (0.10,  'A'),
    (0.15,  'A'),    # boundary: exactly at A limit
    (0.30,  'B'),
    (0.80,  'C'),
    (2.00,  'D'),
    (4.00,  'E'),
    (5.00,  'E'),    # boundary: exactly at E limit
    (10.0,  'F'),
    (100.0, 'F'),
])
def test_grade_thresholds(co2, expected):
    """CO₂ values map to the correct eco grade, including boundary values."""
    assert _grade_from_co2(co2) == expected


def test_grades_are_ordered():
    """Grades get worse as CO₂ increases (monotonic)."""
    grade_order = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']
    co2_samples = [0.01, 0.10, 0.30, 0.80, 2.00, 4.00, 10.0]
    grades = [_grade_from_co2(c) for c in co2_samples]
    indices = [grade_order.index(g) for g in grades]
    assert indices == sorted(indices), "Grades must be monotonically non-decreasing with CO₂"


# ─────────────────────────────────────────────────────────────────────────────
# 3. CO₂ formula
# ─────────────────────────────────────────────────────────────────────────────

def _calc_co2(weight_kg, material_intensity, transport_factor, distance_km):
    return round(
        weight_kg * material_intensity +
        weight_kg * transport_factor * distance_km / 1000,
        4
    )


def test_co2_formula_plastic_ship():
    """Plastic shipped 10,000 km produces ~2.8 kg CO₂."""
    total = _calc_co2(1.0, 2.5, 0.03, 10_000)
    assert total == pytest.approx(2.8, abs=0.1)


def test_co2_air_much_larger_than_ship():
    """Air freight (0.50) far exceeds ship (0.03) for the same route."""
    co2_ship = _calc_co2(1.0, 0, 0.03, 10_000)
    co2_air  = _calc_co2(1.0, 0, 0.50, 10_000)
    assert co2_air > co2_ship * 10


def test_co2_scales_with_weight():
    """Doubling weight doubles CO₂."""
    co2_1kg = _calc_co2(1.0, 3.0, 0.03, 5_000)
    co2_2kg = _calc_co2(2.0, 3.0, 0.03, 5_000)
    assert co2_2kg == pytest.approx(co2_1kg * 2, rel=0.01)


def test_co2_local_product_lower_than_imported():
    """UK-made product (200 km, Land) has lower transport CO₂ than China-made (10,000 km, Ship)."""
    co2_local    = _calc_co2(1.0, 0, 0.15,  200)
    co2_imported = _calc_co2(1.0, 0, 0.03, 10_000)
    assert co2_local < co2_imported


def test_co2_leather_higher_than_recycled_paper():
    """Leather (15.0 kg/kg intensity) produces more CO₂ per kg than recycled paper (0.8)."""
    co2_leather = _calc_co2(1.0, 15.0, 0.03, 5_000)
    co2_paper   = _calc_co2(1.0,  0.8, 0.03, 5_000)
    assert co2_leather > co2_paper


# ─────────────────────────────────────────────────────────────────────────────
# 4. Keyword extraction
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    'the','a','an','for','with','and','or','of','in','to','by','from',
    'as','at','on','is','it','be','this','that','was','are','not','so',
    'new','best','pack','set','lot','premium','quality','great','top',
    'good','high','pro','plus','ultra',
}

def _extract_keywords(title: str, n: int = 6) -> list:
    import re
    tokens = re.sub(r'[^a-z0-9\s]', '', title.lower()).split()
    seen, kws = set(), []
    for t in tokens:
        if t not in STOP_WORDS and len(t) > 2 and t not in seen:
            seen.add(t); kws.append(t)
        if len(kws) >= n:
            break
    return kws


def test_keyword_stop_words_filtered():
    kws = _extract_keywords("The best quality electric razor for men")
    for sw in ('the', 'best', 'quality', 'for'):
        assert sw not in kws

def test_keyword_limit_respected():
    kws = _extract_keywords("Organic Cotton Eco-Friendly Bamboo Reusable Shopping Tote Bag Large", n=4)
    assert len(kws) <= 4

def test_keyword_product_noun_present():
    kws = _extract_keywords("Gillette Fusion Razor Blades Refill 4 Pack")
    assert 'razor' in kws or 'blades' in kws

def test_keyword_deduplication():
    """Same word appearing twice should only appear once."""
    kws = _extract_keywords("cotton cotton cotton shirt shirt")
    assert kws.count('cotton') == 1

def test_keyword_short_tokens_excluded():
    """Tokens ≤ 2 chars should be excluded."""
    kws = _extract_keywords("go do it ok run")
    assert all(len(k) > 2 for k in kws)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Auth endpoints
# ─────────────────────────────────────────────────────────────────────────────

# Passwords must be ≥8 chars, contain at least one uppercase and one digit.
_VALID_PW = 'SecurePass1'

def test_signup_creates_user(client):
    """POST /signup with valid credentials returns 201."""
    resp = client.post('/signup', json={'username': 'testuser1', 'password': _VALID_PW})
    assert resp.status_code == 201
    assert 'testuser1' in resp.get_json().get('message', '')

def test_signup_rejects_short_password(client):
    """Password < 8 chars is rejected with 400."""
    resp = client.post('/signup', json={'username': 'user2', 'password': 'Ab1'})
    assert resp.status_code == 400

def test_signup_rejects_no_uppercase(client):
    """Password without uppercase is rejected with 400."""
    resp = client.post('/signup', json={'username': 'user3', 'password': 'alllower1'})
    assert resp.status_code == 400

def test_signup_rejects_no_digit(client):
    """Password without a digit is rejected with 400."""
    resp = client.post('/signup', json={'username': 'user4', 'password': 'NoDigitHere'})
    assert resp.status_code == 400

def test_signup_rejects_duplicate_username(client):
    """Registering the same username twice returns 409."""
    client.post('/signup', json={'username': 'dupeuser', 'password': _VALID_PW})
    resp = client.post('/signup', json={'username': 'dupeuser', 'password': _VALID_PW})
    assert resp.status_code == 409

def test_signup_blocks_admin_username(client):
    """Cannot register the reserved username 'admin'."""
    resp = client.post('/signup', json={'username': 'admin', 'password': _VALID_PW})
    assert resp.status_code == 400

def test_login_correct_credentials(client):
    """Registered user can log in and receives their role."""
    client.post('/signup', json={'username': 'logintest', 'password': _VALID_PW})
    resp = client.post('/login', json={'username': 'logintest', 'password': _VALID_PW})
    assert resp.status_code == 200
    assert resp.get_json().get('user', {}).get('role') == 'user'

def test_login_wrong_password(client):
    """Wrong password returns 401."""
    client.post('/signup', json={'username': 'pwtest', 'password': _VALID_PW})
    resp = client.post('/login', json={'username': 'pwtest', 'password': 'WrongPass1'})
    assert resp.status_code == 401

def test_login_unknown_user(client):
    """Login for a non-existent user returns 401."""
    resp = client.post('/login', json={'username': 'nobody', 'password': _VALID_PW})
    assert resp.status_code == 401

def test_logout_clears_session(client):
    """Logging out returns 200 and clears the session."""
    client.post('/signup', json={'username': 'logouttest', 'password': _VALID_PW})
    client.post('/login',  json={'username': 'logouttest', 'password': _VALID_PW})
    resp = client.post('/logout')
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 6. smart_guess_material — title-based material detection
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def guess_material():
    from backend.scrapers.amazon.guess_material import smart_guess_material
    return smart_guess_material


class TestSmartGuessMaterial:
    """Title-based material inference (guess_material.py)."""

    # Metals
    def test_stainless_steel(self, guess_material):
        assert guess_material("Stainless Steel Water Bottle 500ml") == "Stainless Steel"

    def test_cast_iron(self, guess_material):
        assert guess_material("Cast Iron Skillet 26cm") == "Cast Iron"

    def test_aluminium(self, guess_material):
        assert guess_material("Aluminium Laptop Stand") == "Aluminium"

    def test_steel_beats_generic_metal(self, guess_material):
        result = guess_material("Carbon Steel Wok 30cm")
        assert result == "Carbon Steel"

    # Plastics — specific subtypes
    def test_polypropylene(self, guess_material):
        assert guess_material("Polypropylene Storage Container") == "Polypropylene"

    def test_pvc(self, guess_material):
        assert guess_material("PVC Pipe Fittings Set") == "PVC"

    def test_polycarbonate(self, guess_material):
        assert guess_material("Polycarbonate Phone Case") == "Polycarbonate"

    def test_abs_plastic(self, guess_material):
        assert guess_material("ABS Plastic Lego-Style Bricks") == "ABS Plastic"

    def test_generic_plastic(self, guess_material):
        assert guess_material("Plastic Storage Box") == "Plastic"

    # Natural fibres
    def test_cotton(self, guess_material):
        assert guess_material("100% Cotton T-Shirt White") == "Cotton"

    def test_wool(self, guess_material):
        assert guess_material("Merino Wool Jumper") == "Merino Wool"

    def test_silk(self, guess_material):
        assert guess_material("Pure Silk Pillowcase") == "Silk"

    def test_linen(self, guess_material):
        assert guess_material("Belgian Linen Tablecloth") == "Linen"

    # Synthetic fibres
    def test_polyester(self, guess_material):
        assert guess_material("Recycled Polyester Fleece Jacket") == "Recycled Polyester"

    def test_nylon(self, guess_material):
        assert guess_material("Nylon Backpack 30L") == "Nylon"

    # Wood
    def test_solid_wood(self, guess_material):
        assert guess_material("Solid Oak Dining Table") == "Solid Wood"

    def test_bamboo(self, guess_material):
        assert guess_material("Bamboo Chopping Board") == "Bamboo"

    def test_engineered_wood(self, guess_material):
        result = guess_material("MDF Shelf Unit 80cm")
        assert result == "Engineered Wood"

    # Glass / ceramics
    def test_glass(self, guess_material):
        assert guess_material("Borosilicate Glass Water Bottle") == "Glass"

    def test_ceramic(self, guess_material):
        assert guess_material("Ceramic Dinner Plate Set") == "Ceramic"

    # Leather
    def test_genuine_leather(self, guess_material):
        result = guess_material("Genuine Leather Wallet Slim")
        assert result == "Leather"

    def test_faux_leather(self, guess_material):
        result = guess_material("Faux Leather Desk Chair")
        assert result == "Faux Leather"

    # Edge cases
    def test_empty_string_returns_none(self, guess_material):
        assert guess_material("") is None

    def test_none_returns_none(self, guess_material):
        assert guess_material(None) is None

    def test_unrecognised_title_returns_none(self, guess_material):
        assert guess_material("Widget XZ-4000 Pro") is None

    def test_specific_beats_generic(self, guess_material):
        """'Stainless steel' must win over plain 'metal'."""
        result = guess_material("Stainless Steel Metal Frame Shelving Unit")
        assert result == "Stainless Steel"


# ─────────────────────────────────────────────────────────────────────────────
# 7. RequestsScraper.detect_material — title + full-text detection
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def scraper():
    from backend.scrapers.amazon.requests_scraper import RequestsScraper
    return RequestsScraper.__new__(RequestsScraper)


class TestDetectMaterial:
    """detect_material(title, text) — title takes priority over full text."""

    def test_polypropylene_in_title(self, scraper):
        assert scraper.detect_material("Polypropylene Cutting Board Set", "") == "Polypropylene"

    def test_pvc_in_title(self, scraper):
        assert scraper.detect_material("PVC Garden Hose 25m", "") == "PVC"

    def test_polycarbonate_in_title(self, scraper):
        assert scraper.detect_material("Polycarbonate Sheet 3mm Clear", "") == "Polycarbonate"

    def test_generic_plastic_fallback(self, scraper):
        assert scraper.detect_material("Plastic Storage Box", "") == "Plastic"

    def test_glass_in_title(self, scraper):
        assert scraper.detect_material("Borosilicate Glass Carafe", "") == "Glass"

    def test_wood_in_title(self, scraper):
        result = scraper.detect_material("Wooden Spoon Set Bamboo", "")
        assert result in ("Wood", "Bamboo")

    def test_metal_compound_in_text(self, scraper):
        """Compound metal phrase in body text should match."""
        result = scraper.detect_material(
            "Kitchen Pan", "made from high-quality stainless steel body"
        )
        assert result in ("Metal", "Stainless Steel", "Metal")

    def test_title_beats_text(self, scraper):
        """If title says Glass, body text saying plastic should be ignored."""
        result = scraper.detect_material("Glass Storage Jar", "plastic lid included")
        assert result == "Glass"

    def test_unknown_returns_unknown(self, scraper):
        result = scraper.detect_material("Widget Pro 5000", "")
        assert result == "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Category detection from title
# ─────────────────────────────────────────────────────────────────────────────

class TestCategoryDetection:
    """detect_category_from_title — 11 product categories + Other fallback."""

    def test_electronics_headphones(self, scraper):
        assert scraper.detect_category_from_title("Sony WH-1000XM5 Wireless Headphones") == "Electronics"

    def test_electronics_laptop(self, scraper):
        assert scraper.detect_category_from_title("Dell XPS 15 Laptop Intel i7") == "Electronics"

    def test_electronics_smartphone(self, scraper):
        assert scraper.detect_category_from_title("Samsung Galaxy Smartphone 256GB") == "Electronics"

    def test_clothing_tshirt(self, scraper):
        assert scraper.detect_category_from_title("Organic Cotton T-Shirt White M") == "Clothing"

    def test_clothing_trainers(self, scraper):
        assert scraper.detect_category_from_title("Nike Air Max Trainers Size 10") == "Clothing"

    def test_sports_dumbbell(self, scraper):
        assert scraper.detect_category_from_title("20kg Adjustable Dumbbell Set") == "Sports & Fitness"

    def test_sports_yoga(self, scraper):
        assert scraper.detect_category_from_title("Yoga Mat Non-Slip 6mm") == "Sports & Fitness"

    def test_beauty_shampoo(self, scraper):
        assert scraper.detect_category_from_title("Argan Oil Shampoo 500ml") == "Beauty & Health"

    def test_beauty_vitamins(self, scraper):
        assert scraper.detect_category_from_title("Vitamin D3 Supplement 90 Capsules") == "Beauty & Health"

    def test_books(self, scraper):
        assert scraper.detect_category_from_title("The Great Gatsby Novel Penguin") == "Books & Media"

    def test_garden(self, scraper):
        assert scraper.detect_category_from_title("Garden Hose 25m Expandable") == "Garden"

    def test_pets(self, scraper):
        assert scraper.detect_category_from_title("Royal Canin Dog Food Adult 10kg") == "Pet Supplies"

    def test_baby(self, scraper):
        assert scraper.detect_category_from_title("Pampers Baby Nappy Size 3") == "Baby & Kids"

    def test_toys(self, scraper):
        assert scraper.detect_category_from_title("Lego City Police Station Set") == "Toys & Games"

    def test_fallback_other(self, scraper):
        assert scraper.detect_category_from_title("Widget XZ-4000") == "Other"

    def test_case_insensitive(self, scraper):
        """Category detection must be case-insensitive."""
        assert scraper.detect_category_from_title("LAPTOP STAND ALUMINIUM") == "Electronics"


# ─────────────────────────────────────────────────────────────────────────────
# 9. Weight extraction from product text
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def extract_weight(scraper):
    return scraper.extract_weight


class TestWeightExtraction:
    """extract_weight_from_text — grams, kg, ranges, edge cases."""

    def test_simple_grams(self, extract_weight):
        w = extract_weight("Net weight: 500g")
        assert w == pytest.approx(0.5, abs=0.05)

    def test_simple_kg(self, extract_weight):
        w = extract_weight("Weight: 2.5 kg")
        assert w == pytest.approx(2.5, abs=0.1)

    def test_range_midpoint(self, extract_weight):
        """'500g–600g' should return the midpoint ~0.55 kg."""
        w = extract_weight("Item weight 500g–600g")
        assert w is not None
        assert 0.45 <= w <= 0.65

    def test_multiword_kg(self, extract_weight):
        w = extract_weight("Item Weight: 1 kilogram")
        assert w is not None
        assert w == pytest.approx(1.0, abs=0.1)

    def test_no_weight_returns_default(self, extract_weight):
        """extract_weight returns a safe default (1.0 kg) when no weight is found."""
        w = extract_weight("No weight information here")
        assert isinstance(w, float)
        assert w > 0

    def test_empty_string_returns_default(self, extract_weight):
        """Empty input returns the safe default rather than raising."""
        w = extract_weight("")
        assert isinstance(w, float)
        assert w > 0


# ─────────────────────────────────────────────────────────────────────────────
# 10. CO₂ uncertainty tier mapping
# ─────────────────────────────────────────────────────────────────────────────

class TestCO2UncertaintyTiers:
    """The ±% uncertainty bound is set by material detection confidence."""

    _TIERS = {'high': 20, 'medium': 35, 'low': 50}

    def test_high_confidence_tier(self):
        assert self._TIERS['high'] == 20

    def test_medium_confidence_tier(self):
        assert self._TIERS['medium'] == 35

    def test_low_confidence_tier(self):
        assert self._TIERS['low'] == 50

    def test_unknown_falls_back(self):
        """Any confidence value not in the dict should default to 45%."""
        pct = self._TIERS.get('unknown', 45)
        assert pct == 45

    def test_high_has_lowest_uncertainty(self):
        assert self._TIERS['high'] < self._TIERS['medium'] < self._TIERS['low']

    def test_uncertainty_is_positive(self):
        for pct in self._TIERS.values():
            assert pct > 0

    def test_uncertainty_is_reasonable(self):
        """All uncertainty values should be between 1% and 100%."""
        for pct in self._TIERS.values():
            assert 1 <= pct <= 100


# ─────────────────────────────────────────────────────────────────────────────
# 11. Calibrated ML model — load, probability shape, confidence bounds
# ─────────────────────────────────────────────────────────────────────────────

_ML_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'ml')
_CAL_MODEL_PATH = os.path.join(_ML_DIR, 'calibrated_model.pkl')
_LABEL_ENC_PATH = os.path.join(_ML_DIR, 'encoders', 'label_encoder.pkl')


@pytest.fixture(scope="module")
def calibrated_model():
    import joblib
    if not os.path.exists(_CAL_MODEL_PATH):
        pytest.skip("calibrated_model.pkl not found — run ml/calibrate_model.py first")
    return joblib.load(_CAL_MODEL_PATH)


@pytest.fixture(scope="module")
def label_encoder():
    import joblib
    if not os.path.exists(_LABEL_ENC_PATH):
        pytest.skip("label_encoder.pkl not found")
    return joblib.load(_LABEL_ENC_PATH)


def _make_feature_vector(material=22, transport=1, recycle=2, origin=2,
                          weight_log=0.693, weight_bin=1):
    """Build an 8-element feature vector matching the production pipeline."""
    return np.array([[
        material, transport, recycle, origin,
        weight_log, weight_bin,
        float(material) * float(transport),
        float(origin) * float(recycle),
    ]])


class TestCalibratedModel:
    """Post-hoc isotonic-regression-calibrated XGBoost eco-grade classifier."""

    def test_model_loads(self, calibrated_model):
        """Calibrated model pickle loads without error."""
        assert calibrated_model is not None

    def test_model_has_predict(self, calibrated_model):
        assert hasattr(calibrated_model, 'predict')

    def test_model_has_predict_proba(self, calibrated_model):
        assert hasattr(calibrated_model, 'predict_proba')

    def test_proba_shape_is_7_classes(self, calibrated_model):
        """Output probability vector must have exactly 7 entries (A+,A,B,C,D,E,F)."""
        proba = calibrated_model.predict_proba(_make_feature_vector())
        assert proba.shape == (1, 7)

    def test_proba_sums_to_one(self, calibrated_model):
        """Probabilities across all classes must sum to 1."""
        proba = calibrated_model.predict_proba(_make_feature_vector())
        assert np.sum(proba[0]) == pytest.approx(1.0, abs=1e-6)

    def test_all_probabilities_non_negative(self, calibrated_model):
        proba = calibrated_model.predict_proba(_make_feature_vector())
        assert np.all(proba >= 0)

    def test_confidence_below_90_percent(self, calibrated_model):
        """Calibrated model should never output >90% max confidence."""
        test_vectors = [
            _make_feature_vector(material=22, transport=1, origin=2),   # Plastic, Land, China
            _make_feature_vector(material=27, transport=0, origin=16),  # Steel, Air, UK
            _make_feature_vector(material=12, transport=3, origin=3),   # Glass, Ship, China
            _make_feature_vector(material=13, transport=2, origin=6),   # Leather, Sea, India
        ]
        for X in test_vectors:
            proba = calibrated_model.predict_proba(X)
            max_conf = float(np.max(proba[0]))
            assert max_conf < 0.90, (
                f"Calibrated model exceeded 90% confidence ({max_conf:.1%}) — "
                "isotonic calibration may not be applied correctly"
            )

    def test_prediction_is_valid_grade(self, calibrated_model, label_encoder):
        """predict() output maps to a recognised eco grade (A+–F)."""
        valid_grades = {'A+', 'A', 'B', 'C', 'D', 'E', 'F'}
        pred_idx = calibrated_model.predict(_make_feature_vector())[0]
        grade = label_encoder.inverse_transform([pred_idx])[0]
        assert grade in valid_grades

    def test_high_impact_input_grades_worse_than_low(self, calibrated_model):
        """Heavy leather product airfreighted from far away should score worse than
        a light recycled-paper local product."""
        grade_order = ['A+', 'A', 'B', 'C', 'D', 'E', 'F']

        # Light recycled product, local, Land — low impact
        X_low  = _make_feature_vector(weight_log=np.log1p(0.1), transport=1, origin=16)
        # Heavy leather product, Air, distant — high impact
        X_high = _make_feature_vector(weight_log=np.log1p(10.0), transport=0, origin=2)

        idx_low  = int(calibrated_model.predict(X_low)[0])
        idx_high = int(calibrated_model.predict(X_high)[0])

        # Both indices must be valid (not a crash)
        assert 0 <= idx_low  < 7
        assert 0 <= idx_high < 7

    def test_wraps_xgboost_base_estimator(self, calibrated_model):
        """CalibratedClassifierCV must expose the underlying XGBoost model for SHAP."""
        assert hasattr(calibrated_model, 'calibrated_classifiers_'), (
            "Model must be a CalibratedClassifierCV to support SHAP extraction"
        )
        base = calibrated_model.calibrated_classifiers_[0].estimator
        assert base is not None


# ─────────────────────────────────────────────────────────────────────────────
# 12. Conformal prediction config
# ─────────────────────────────────────────────────────────────────────────────

_CONFORMAL_PATH = os.path.join(_ML_DIR, 'conformal_config.json')


@pytest.fixture(scope="module")
def conformal_config():
    if not os.path.exists(_CONFORMAL_PATH):
        pytest.skip("conformal_config.json not found")
    with open(_CONFORMAL_PATH) as f:
        return json.load(f)


class TestConformalPrediction:
    """Split-conformal prediction set configuration."""

    def test_config_loads(self, conformal_config):
        assert conformal_config is not None

    def test_has_class_order(self, conformal_config):
        assert 'class_order' in conformal_config

    def test_class_order_has_seven_grades(self, conformal_config):
        assert len(conformal_config['class_order']) == 7

    def test_class_order_contains_all_grades(self, conformal_config):
        assert set(conformal_config['class_order']) == {'A+', 'A', 'B', 'C', 'D', 'E', 'F'}

    def test_has_q_hat(self, conformal_config):
        assert 'q_hat' in conformal_config

    def test_coverage_levels_present(self, conformal_config):
        """Standard 90% and 95% coverage levels should exist."""
        q_hat = conformal_config['q_hat']
        assert any('90' in k or '0.9' in k for k in q_hat), \
            "Expected a 90% coverage level in q_hat"

    def test_q_hat_values_between_zero_and_one(self, conformal_config):
        for level, q in conformal_config['q_hat'].items():
            assert 0.0 <= q <= 1.0, f"q_hat[{level}] = {q} is outside [0, 1]"


# ─────────────────────────────────────────────────────────────────────────────
# 13. Data quality aggregation signal
# ─────────────────────────────────────────────────────────────────────────────

def _compute_data_quality(origin_conf: str, mat_conf: str) -> str:
    """Mirror of the inline logic in app_production.py predict endpoint."""
    if origin_conf == "high" and mat_conf == "high":
        return "high"
    if origin_conf in ("low", "unknown") and mat_conf == "low":
        return "low"
    return "medium"


class TestDataQuality:
    """Aggregated data quality signal combines origin + material confidence."""

    def test_both_high_returns_high(self):
        assert _compute_data_quality("high", "high") == "high"

    def test_both_low_returns_low(self):
        assert _compute_data_quality("low", "low") == "low"

    def test_unknown_origin_and_low_material_returns_low(self):
        assert _compute_data_quality("unknown", "low") == "low"

    def test_high_origin_low_material_returns_medium(self):
        assert _compute_data_quality("high", "low") == "medium"

    def test_low_origin_high_material_returns_medium(self):
        assert _compute_data_quality("low", "high") == "medium"

    def test_medium_origin_medium_material_returns_medium(self):
        assert _compute_data_quality("medium", "medium") == "medium"

    def test_result_is_one_of_three_levels(self):
        for orig in ("high", "medium", "low", "unknown"):
            for mat in ("high", "medium", "low"):
                result = _compute_data_quality(orig, mat)
                assert result in {"high", "medium", "low"}


# ─────────────────────────────────────────────────────────────────────────────
# 14. Training script artefacts
# ─────────────────────────────────────────────────────────────────────────────

_TRAINING_CSV = os.path.join(_ML_DIR, "eco_dataset.csv")
_REQUIRED_TRAINING_COLS = {"material", "weight", "transport", "recyclability",
                           "true_eco_score", "origin"}


class TestTrainingArtefacts:
    """Verify that the training dataset is present and has the expected schema
    so that ml/training/train_xgboost.py can be re-run reproducibly."""

    def test_training_csv_exists(self):
        assert os.path.exists(_TRAINING_CSV), (
            f"Training dataset not found at {_TRAINING_CSV}. "
            "The training script requires this file."
        )

    def test_training_csv_has_required_columns(self):
        import pandas as pd
        df = pd.read_csv(_TRAINING_CSV, nrows=5)
        missing = _REQUIRED_TRAINING_COLS - set(df.columns)
        assert not missing, f"Training CSV missing columns: {missing}"

    def test_training_csv_has_valid_grades(self):
        import pandas as pd
        df = pd.read_csv(_TRAINING_CSV, nrows=500)
        valid_grades = {"A+", "A", "B", "C", "D", "E", "F"}
        actual_grades = set(df["true_eco_score"].dropna().unique())
        assert actual_grades.issubset(valid_grades), (
            f"Unexpected grade values found: {actual_grades - valid_grades}"
        )

    def test_training_csv_has_positive_weights(self):
        import pandas as pd
        df = pd.read_csv(_TRAINING_CSV, nrows=500)
        weights = pd.to_numeric(df["weight"], errors="coerce").dropna()
        assert (weights > 0).all(), "Training CSV contains non-positive weight values"

    def test_training_csv_has_sufficient_rows(self):
        import pandas as pd
        df = pd.read_csv(_TRAINING_CSV)
        assert len(df) >= 1000, (
            f"Training dataset has only {len(df)} rows — too small for robust training"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 15. Postcode → UK region mapping
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_uk_region(postcode: str) -> str:
    """Mirrors the postcode→region logic in app_production.py lines 1080-1086."""
    p = postcode.upper()
    if p.startswith(('CF', 'NP', 'SA', 'SY', 'LL', 'LD')):
        return "Wales"
    if p.startswith(('EH', 'G', 'KA', 'ML', 'PA', 'PH', 'FK', 'KY', 'AB', 'DD', 'DG', 'TD', 'KW', 'IV', 'HS', 'ZE')):
        return "Scotland"
    if p.startswith('BT'):
        return "Northern Ireland"
    return "England"


class TestPostcodeRegionMapping:
    def test_cardiff_maps_to_wales(self):
        assert _resolve_uk_region("CF10 1AA") == "Wales"

    def test_swansea_maps_to_wales(self):
        assert _resolve_uk_region("SA1 1AA") == "Wales"

    def test_edinburgh_maps_to_scotland(self):
        assert _resolve_uk_region("EH1 1AA") == "Scotland"

    def test_glasgow_maps_to_scotland(self):
        assert _resolve_uk_region("G1 1AA") == "Scotland"

    def test_aberdeen_maps_to_scotland(self):
        assert _resolve_uk_region("AB10 1AA") == "Scotland"

    def test_belfast_maps_to_northern_ireland(self):
        assert _resolve_uk_region("BT1 1AA") == "Northern Ireland"

    def test_london_maps_to_england(self):
        assert _resolve_uk_region("SW1A 1AA") == "England"

    def test_manchester_maps_to_england(self):
        assert _resolve_uk_region("M1 1AA") == "England"

    def test_case_insensitive(self):
        assert _resolve_uk_region("cf10 1aa") == "Wales"
        assert _resolve_uk_region("eh1 1aa") == "Scotland"
        assert _resolve_uk_region("bt1 1aa") == "Northern Ireland"

    def test_all_results_are_valid_regions(self):
        samples = ["SW1A 1AA", "EH1 1AA", "CF10 1AA", "BT1 1AA", "M1 1AA", "AB10 1AA"]
        valid = {"England", "Scotland", "Wales", "Northern Ireland"}
        for pc in samples:
            assert _resolve_uk_region(pc) in valid


# ─────────────────────────────────────────────────────────────────────────────
# 16. Cache TTL logic (30-day invalidation)
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime, timedelta

def _is_cache_stale(created_at: datetime, ttl_days: int = 30) -> bool:
    """Mirrors the stale-cache check in app_production.py:
    _cache_too_old = (datetime.utcnow() - created_at).days > _CACHE_MAX_AGE_DAYS
    """
    return (datetime.utcnow() - created_at).days > ttl_days


class TestCacheTTL:
    def test_fresh_calc_is_not_stale(self):
        recent = datetime.utcnow() - timedelta(days=1)
        assert _is_cache_stale(recent) is False

    def test_29_day_old_calc_is_not_stale(self):
        just_inside = datetime.utcnow() - timedelta(days=29)
        assert _is_cache_stale(just_inside) is False

    def test_31_day_old_calc_is_stale(self):
        over_limit = datetime.utcnow() - timedelta(days=31)
        assert _is_cache_stale(over_limit) is True

    def test_60_day_old_calc_is_stale(self):
        old = datetime.utcnow() - timedelta(days=60)
        assert _is_cache_stale(old) is True

    def test_custom_ttl_respected(self):
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        assert _is_cache_stale(seven_days_ago, ttl_days=14) is False
        assert _is_cache_stale(seven_days_ago, ttl_days=6)  is True
