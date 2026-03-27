import os
import secrets
from flask import Flask, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)

CORS(
    app,
    supports_credentials=True,
    origins=[
        'https://impacttracker.netlify.app',
        'https://silly-cuchufli-b154e2.netlify.app',
        r'^https://.*--impacttracker\.netlify\.app$',
        'http://localhost:5173',
        'http://localhost:5174',
    ],
    methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
)


@app.get('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'impacttracker-railway', 'mode': 'stable'}), 200


@app.get('/')
def root():
    return jsonify({'status': 'ok', 'service': 'impacttracker-api', 'mode': 'railway-stable'}), 200


@app.get('/me')
def me():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(user), 200


@app.get('/api/dashboard-metrics')
def dashboard_metrics():
    material_distribution = [
        {'name': 'Plastic', 'value': 11900},
        {'name': 'Steel', 'value': 6712},
        {'name': 'Paper', 'value': 5618},
        {'name': 'Other', 'value': 4945},
        {'name': 'Glass', 'value': 4909},
        {'name': 'Wood', 'value': 4448},
        {'name': 'Aluminum', 'value': 3094},
        {'name': 'Polyester', 'value': 2563},
        {'name': 'Cotton', 'value': 2510},
        {'name': 'Rubber', 'value': 1948},
    ]

    return jsonify({
        'success': True,
        'stats': {
            'total_products': 50000,
            'total_materials': 35,
            'total_predictions': 0,
            'recent_activity': 0,
        },
        'material_distribution': material_distribution,
        'score_distribution': [
            {'name': 'A+', 'value': 3500},
            {'name': 'A', 'value': 8200},
            {'name': 'B', 'value': 12400},
            {'name': 'C', 'value': 11300},
            {'name': 'D', 'value': 8900},
            {'name': 'E', 'value': 4200},
            {'name': 'F', 'value': 1500},
        ],
        'data': {
            'total_products': 50000,
            'total_scraped_products': 0,
            'total_calculations': 0,
            'database_status': 'deferred',
        },
    }), 200


@app.get('/api/eco-data')
def eco_data():
    sample_materials = ['Plastic', 'Steel', 'Paper', 'Glass', 'Wood', 'Aluminum', 'Polyester', 'Cotton', 'Rubber', 'Other']
    sample_origins = ['UK', 'China', 'Germany', 'France', 'USA', 'India', 'Netherlands', 'Poland']
    rows = []
    for idx in range(1, 101):
        material = sample_materials[idx % len(sample_materials)]
        rows.append({
            'id': idx,
            'title': f'Sample Product {idx}',
            'material': material,
            'origin': sample_origins[idx % len(sample_origins)],
            'weight': round(0.2 + (idx % 8) * 0.35, 2),
            'price': round(4.99 + (idx % 20) * 1.5, 2),
            'true_eco_score': ['A+', 'A', 'B', 'C', 'D', 'E', 'F'][idx % 7],
            'ml_prediction': material,
            'confidence': 0.85,
        })
    return jsonify(rows), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
