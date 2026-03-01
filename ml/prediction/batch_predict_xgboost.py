import pandas as pd
import xgboost as xgb
import joblib
import os

# === Paths
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
ML_ASSETS_DIR = os.environ.get("ML_ASSETS_DIR", os.path.join(project_root, "ml"))
model_dir = ML_ASSETS_DIR
encoders_dir = os.path.join(ML_ASSETS_DIR, "xgb_encoders")

# === Load model and encoders
model = xgb.XGBClassifier()
model.load_model(os.path.join(model_dir, "xgb_model_optimized.json"))

material_enc = joblib.load(os.path.join(encoders_dir, "material_encoder.pkl"))
transport_enc = joblib.load(os.path.join(encoders_dir, "transport_encoder.pkl"))
recycle_enc = joblib.load(os.path.join(encoders_dir, "recyclability_encoder.pkl"))
origin_enc = joblib.load(os.path.join(encoders_dir, "origin_encoder.pkl"))
label_enc = joblib.load(os.path.join(encoders_dir, "label_encoder.pkl"))

# === Load batch input CSV
input_csv = os.path.join(script_dir, "xgbatch_products.csv")
batch_df = pd.read_csv(input_csv)

# === Preprocess input
batch_df["material_encoded"] = material_enc.transform(batch_df["material"].astype(str).str.title().str.strip())
batch_df["weight"] = batch_df["weight"].astype(float)
batch_df["transport_encoded"] = transport_enc.transform(batch_df["transport"].astype(str).str.title().str.strip())
batch_df["recycle_encoded"] = recycle_enc.transform(batch_df["recyclability"].astype(str).str.title().str.strip())
batch_df["origin_encoded"] = origin_enc.transform(batch_df["origin"].astype(str).str.title().str.strip())

X_batch = batch_df[["material_encoded", "weight", "transport_encoded", "recycle_encoded", "origin_encoded"]]

# === Predict
preds_encoded = model.predict(X_batch)
preds_labels = label_enc.inverse_transform(preds_encoded)

# === Add predictions to dataframe
batch_df["predicted_eco_score"] = preds_labels

# === Save output
output_csv = os.path.join(script_dir, "batch_predictions_output.csv")
batch_df.to_csv(output_csv, index=False)

print(f"✅ Batch predictions saved to {output_csv}")
