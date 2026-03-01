import pandas as pd
import joblib
import os

# Resolve ML assets directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))

# Load model + encoders
model = joblib.load(os.path.join(ML_ASSETS_DIR, "eco_model.pkl"))
material_enc = joblib.load(os.path.join(ML_ASSETS_DIR, "encoders", "material_encoder.pkl"))
transport_enc = joblib.load(os.path.join(ML_ASSETS_DIR, "encoders", "transport_encoder.pkl"))

# Load your dummy data
df = pd.read_csv(os.path.join(ML_ASSETS_DIR, "dummy_data.csv"))

# Encode and predict
df["material_enc"] = material_enc.transform(df["material"])
df["transport_enc"] = transport_enc.transform(df["transport"])

X = df[["material_enc", "weight", "transport_enc"]]
y_pred = model.predict(X)

print("✅ Predictions:")
print(y_pred)
