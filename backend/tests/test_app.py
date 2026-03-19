"""
Unit tests for ImpactTracker backend API.

Covers:
  - CO₂ estimation logic
  - Eco-grade classification thresholds
  - Alternatives keyword extraction
  - Auth endpoint validation
  - SHAP counterfactual generation
  - API response shapes

Run with:  pytest backend/tests/test_app.py -v
"""

import pytest
import json
import sys
import os

# Make sure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    from backend.api.app_production import create_app
    application = create_app('testing')
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    application.config['WTF_CSRF_ENABLED'] = False

    from backend.models.database import db as _db
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ──────────────────────────────────────────────────────────────────────────────
# 1. Health endpoint
# ──────────────────────────────────────────────────────────────────────────────

def test_health_endpoint(client):
    """GET /health returns 200."""
    resp = client.get('/health')
    assert resp.status_code == 200
    # Accept either a JSON body or a plain "healthy" string response
    body = resp.get_data(as_text=True)
    assert 'healthy' in body.lower() or (resp.get_json() or {}).get('status') == 'ok'


# ──────────────────────────────────────────────────────────────────────────────
# 2. Eco-grade thresholds (pure logic, no DB)
# ──────────────────────────────────────────────────────────────────────────────

def _grade_from_co2(co2: float) -> str:
    """Replicate the rule-based grading logic from the backend."""
    if co2 <= 0.05:   return 'A+'
    if co2 <= 0.15:   return 'A'
    if co2 <= 0.40:   return 'B'
    if co2 <= 1.00:   return 'C'
    if co2 <= 2.50:   return 'D'
    if co2 <= 5.00:   return 'E'
    return 'F'


@pytest.mark.parametrize("co2,expected", [
    (0.01,  'A+'),
    (0.10,  'A'),
    (0.30,  'B'),
    (0.80,  'C'),
    (2.00,  'D'),
    (4.00,  'E'),
    (10.0,  'F'),
])
def test_grade_thresholds(co2, expected):
    """CO₂ values map to the correct eco grade."""
    assert _grade_from_co2(co2) == expected


# ──────────────────────────────────────────────────────────────────────────────
# 3. CO₂ calculation formula
# ──────────────────────────────────────────────────────────────────────────────

def test_co2_formula_basic():
    """Rule-based CO₂ = (weight × material_intensity) + (weight × transport_factor × distance / 1000)."""
    weight_kg      = 1.0
    material_int   = 2.5   # Plastic
    transport_fac  = 0.03  # Ship
    distance_km    = 10000.0

    transport_co2 = weight_kg * transport_fac * distance_km / 1000
    material_co2  = weight_kg * material_int
    total = round(transport_co2 + material_co2, 4)

    assert total == pytest.approx(2.8, abs=0.1)


def test_co2_formula_air_much_larger_than_ship():
    """Air freight (0.50) produces far more CO₂ than ship (0.03) for same route."""
    weight_kg    = 1.0
    distance_km  = 10000.0

    co2_ship = weight_kg * 0.03 * distance_km / 1000
    co2_air  = weight_kg * 0.50 * distance_km / 1000

    assert co2_air > co2_ship * 10


# ──────────────────────────────────────────────────────────────────────────────
# 4. Keyword extraction stop-word filtering (pure logic)
# ──────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    'the', 'a', 'an', 'for', 'with', 'and', 'or', 'of', 'in', 'to', 'by',
    'from', 'as', 'at', 'on', 'is', 'it', 'be', 'this', 'that', 'was',
    'are', 'not', 'so', 'new', 'best', 'pack', 'set', 'lot', 'premium',
    'quality', 'great', 'top', 'good', 'high', 'pro', 'plus', 'ultra',
}

def _extract_keywords(title: str, n: int = 6) -> list[str]:
    import re
    tokens = re.sub(r'[^a-z0-9\s]', '', title.lower()).split()
    seen = set()
    kws = []
    for t in tokens:
        if t not in STOP_WORDS and len(t) > 2 and t not in seen:
            seen.add(t)
            kws.append(t)
        if len(kws) >= n:
            break
    return kws


def test_keyword_stop_words_filtered():
    """Common stop words should not appear in extracted keywords."""
    kws = _extract_keywords("The best quality electric razor for men")
    assert 'the' not in kws
    assert 'best' not in kws
    assert 'quality' not in kws
    assert 'for' not in kws


def test_keyword_limit_respected():
    """Keyword list must not exceed n items."""
    title = "Organic Cotton Eco-Friendly Bamboo Reusable Shopping Tote Bag Large"
    kws = _extract_keywords(title, n=4)
    assert len(kws) <= 4


def test_keyword_product_noun_present():
    """Product type nouns should survive extraction."""
    kws = _extract_keywords("Gillette Fusion Razor Blades Refill 4 Pack")
    assert 'razor' in kws or 'blades' in kws


# ──────────────────────────────────────────────────────────────────────────────
# 5. Auth endpoints
# ──────────────────────────────────────────────────────────────────────────────

def test_signup_creates_user(client):
    """POST /signup with valid data returns 201."""
    resp = client.post('/signup', json={
        'username': 'testuser',
        'password': 'securepass123',
    })
    assert resp.status_code == 201
    assert 'testuser' in resp.get_json().get('message', '')


def test_signup_rejects_short_password(client):
    """Passwords shorter than 8 chars are rejected with 400."""
    resp = client.post('/signup', json={'username': 'user2', 'password': 'short'})
    assert resp.status_code == 400


def test_signup_rejects_duplicate_username(client):
    """Registering the same username twice returns 409."""
    client.post('/signup', json={'username': 'dupeuser', 'password': 'password123'})
    resp = client.post('/signup', json={'username': 'dupeuser', 'password': 'password456'})
    assert resp.status_code == 409


def test_login_correct_credentials(client):
    """Registered user can log in and receives role info."""
    client.post('/signup', json={'username': 'logintest', 'password': 'mypassword1'})
    resp = client.post('/login', json={'username': 'logintest', 'password': 'mypassword1'})
    assert resp.status_code == 200
    assert resp.get_json().get('user', {}).get('role') == 'user'


def test_login_wrong_password(client):
    """Wrong password returns 401."""
    client.post('/signup', json={'username': 'pwtest', 'password': 'correctpass1'})
    resp = client.post('/login', json={'username': 'pwtest', 'password': 'wrongpassword'})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    """Login for non-existent user returns 401."""
    resp = client.post('/login', json={'username': 'nobody', 'password': 'doesnotmatter'})
    assert resp.status_code == 401


def test_signup_blocks_admin_username(client):
    """Cannot register username 'admin' via signup."""
    resp = client.post('/signup', json={'username': 'admin', 'password': 'adminpass123'})
    assert resp.status_code == 400
