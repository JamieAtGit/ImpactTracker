#!/usr/bin/env python3
"""
Main deployment entry point.

Purpose:
- Imports and creates the production Flask app via create_app().
- Reads PORT from environment and starts the server.
- Provides startup diagnostics useful in hosted environments (e.g., Railway).
"""
import os
import sys

print("🚀 Starting DSP Eco Tracker backend v3.0 - DEMO MODE...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
print(f"Added to Python path: {project_root}")

try:
    from backend.api.app_production import create_app
    print("✅ Successfully imported create_app")
except ImportError as e:
    print(f"❌ Failed to import create_app: {e}")
    sys.exit(1)

# Create the Flask app
try:
    app = create_app('production')
    print("✅ Flask app created successfully")
except Exception as e:
    print(f"❌ Failed to create Flask app: {e}")
    sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting server on port {port}...")
    
    # Try to use gunicorn if available, otherwise use Flask dev server
    try:
        import gunicorn
        print("✅ Gunicorn available, but using Flask dev server for simplicity")
    except ImportError:
        print("⚠️ Gunicorn not available, using Flask dev server")
    
    # Use Flask development server (should work on Railway)
    app.run(host='0.0.0.0', port=port, debug=False)