# ML Folder (Consolidated)

This folder now contains all ML code and assets for ImpactTracker.

Structure:
- inference/: Real-time eco scoring utilities
- prediction/: CLI and batch prediction scripts
- training/: Model training pipelines and reports
- evaluation/: Comparison and validation tools
- encoders/, xgb_encoders/: Saved label encoders
- *.json, *.pkl: Models and metrics

Notes:
- The environment variable ML_ASSETS_DIR can override the default path (this folder).
- Legacy imports from `backend.ml` will work temporarily via a shim, but please update to use `ml`.
