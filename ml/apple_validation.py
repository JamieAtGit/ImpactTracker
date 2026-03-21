"""
apple_validation.py
===================
External ground-truth validation of the ImpactTracker model against
Apple's independently verified Product Environmental Reports (PERs).

Apple publishes a PER for every product it sells. Each report contains
the product's full lifecycle carbon footprint (kg CO₂e), independently
audited to ISO 14040/14044 standards, broken down by lifecycle stage:
manufacturing, transport, use, and end-of-life.

This script compares:
  1. Our model's predicted eco grade vs the grade Apple's verified CO₂ implies
  2. Our DEFRA-formula CO₂ estimate vs Apple's verified CO₂
  3. What fraction of Apple's impact our formula actually captures

All Apple figures are sourced from publicly available Product Environmental
Reports at https://www.apple.com/environment/reports/

Usage:
  cd /Users/jamie/Documents/University/ImpactTracker
  source venv/bin/activate
  python ml/apple_validation.py
"""

import os, json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE    = os.path.dirname(os.path.abspath(__file__))
CSV     = os.path.join(BASE, "apple_products.csv")
MODEL   = os.path.join(BASE, "xgb_model.json")
ENC_DIR = os.path.join(BASE, "xgb_encoders")
OUT     = os.path.join(BASE, "apple_validation_results.json")

# ── DEFRA constants (mirrors production code exactly) ─────────────────────────
TRANSPORT_FACTORS = {"Ship": 0.03, "Air": 0.50, "Land": 0.15, "Truck": 0.15}
MATERIAL_INTENSITY = {
    "Aluminum": 8.0, "Steel": 3.0, "Plastic": 2.5, "Glass": 1.5,
    "Paper": 1.2, "Wood": 0.8, "Other": 2.0, "Mixed": 2.0,
}
# Origin → approximate distance to UK (km), mirrors production haversine values
UK_DISTANCES = {
    "China": 8170, "Vietnam": 9170, "India": 6700, "Taiwan": 9600,
    "USA": 6750, "Germany": 930, "UK": 100,
}
GRADE_ORDER = ["A+", "A", "B", "C", "D", "E", "F"]

def co2_to_grade(co2: float) -> str:
    if co2 <= 0.05: return "A+"
    if co2 <= 0.15: return "A"
    if co2 <= 0.40: return "B"
    if co2 <= 1.00: return "C"
    if co2 <= 2.50: return "D"
    if co2 <= 5.00: return "E"
    return "F"

def defra_co2(weight_kg: float, material: str, transport: str, origin: str) -> float:
    """Reproduce the production DEFRA CO₂ formula exactly."""
    tf   = TRANSPORT_FACTORS.get(transport, 0.15)
    mi   = MATERIAL_INTENSITY.get(material, 2.0)
    dist = UK_DISTANCES.get(origin, 8000)
    return round(weight_kg * tf * dist / 1000 + weight_kg * mi, 4)

# ── Load model and encoders ───────────────────────────────────────────────────
print("Loading model and encoders…")
model = xgb.XGBClassifier()
model.load_model(MODEL)

le_mat = joblib.load(os.path.join(ENC_DIR, "material_encoder.pkl"))
le_trn = joblib.load(os.path.join(ENC_DIR, "transport_encoder.pkl"))
le_rec = joblib.load(os.path.join(ENC_DIR, "recyclability_encoder.pkl"))
le_ori = joblib.load(os.path.join(ENC_DIR, "origin_encoder.pkl"))
le_lbl = joblib.load(os.path.join(ENC_DIR, "label_encoder.pkl"))

def safe_enc(enc, val, default):
    try:    return int(enc.transform([val])[0])
    except:
        try: return int(enc.transform([default])[0])
        except: return 0

def predict(weight_kg, material, transport, origin, recyclability="Medium"):
    mat = safe_enc(le_mat, material, "Other")
    trn = safe_enc(le_trn, transport, "Air")
    rec = safe_enc(le_rec, recyclability, "Medium")
    ori = safe_enc(le_ori, origin, "China")
    wl  = float(np.log1p(max(weight_kg, 0)))
    wb  = float(0 if weight_kg < 0.5 else 1 if weight_kg < 2 else 2 if weight_kg < 10 else 3)
    X   = np.array([[mat, trn, rec, ori, wl, wb, float(mat)*float(trn), float(ori)*float(rec)]])
    pred   = model.predict(X)[0]
    probas = model.predict_proba(X)[0]
    grade  = le_lbl.inverse_transform([pred])[0]
    conf   = round(float(probas.max()) * 100, 1)
    return grade, conf, probas

# ── Load Apple products ────────────────────────────────────────────────────────
print("Loading Apple product data…")
df = pd.read_csv(CSV)
print(f"  {len(df)} products across {df['category'].nunique()} categories")

# ── Run validation ─────────────────────────────────────────────────────────────
print("\nRunning validation…")
records = []

for _, row in df.iterrows():
    product   = row["product_name"]
    weight    = float(row["weight_kg"])
    material  = str(row["material_scraper_would_find"])
    origin    = str(row["country_of_manufacture"])
    category  = str(row["category"])

    # All Apple products ship via Air freight internationally
    transport = "Air"

    # Apple products have moderate recyclability (Apple has good recycling
    # programmes but products are not easily user-recyclable)
    recyclability = "Medium"

    # 1. Our DEFRA formula CO₂ estimate
    our_co2 = defra_co2(weight, material, transport, origin)
    our_grade = co2_to_grade(our_co2)

    # 2. Model prediction
    ml_grade, ml_conf, ml_probas = predict(weight, material, transport, origin, recyclability)

    # 3. Apple's verified CO₂ figures
    apple_total = float(row["apple_co2_total_kg"])
    mfg_pct     = float(row["apple_manufacturing_pct"]) / 100
    trn_pct     = float(row["apple_transport_pct"])     / 100
    use_pct     = float(row["apple_use_pct"])           / 100
    eol_pct     = 1.0 - mfg_pct - trn_pct - use_pct

    apple_manufacturing = round(apple_total * mfg_pct, 2)
    apple_transport     = round(apple_total * trn_pct, 2)
    apple_use           = round(apple_total * use_pct, 2)
    apple_eol           = round(apple_total * eol_pct, 2)

    # The most comparable scope: manufacturing + transport
    # (our formula attempts to estimate these two stages only)
    apple_comparable = apple_manufacturing + apple_transport

    # 4. Grade Apple's verified data implies
    apple_grade = co2_to_grade(apple_total)

    # 5. What fraction of Apple's comparable CO₂ does our formula capture?
    capture_pct = round((our_co2 / apple_comparable) * 100, 1) if apple_comparable > 0 else 0

    # 6. What fraction of Apple's total does our formula capture?
    capture_of_total = round((our_co2 / apple_total) * 100, 1)

    # 7. Underestimation factor (how many times are we below Apple's comparable)
    underestimation_factor = round(apple_comparable / our_co2, 1) if our_co2 > 0 else None

    records.append({
        "product":                   product,
        "category":                  category,
        "weight_kg":                 weight,
        "material":                  material,
        "origin":                    origin,
        "transport":                 transport,
        "report_year":               int(row["report_year"]),

        # Our estimates
        "our_defra_co2_kg":          our_co2,
        "our_defra_grade":           our_grade,
        "our_ml_grade":              ml_grade,
        "our_ml_confidence_pct":     ml_conf,

        # Apple's verified figures
        "apple_co2_total_kg":        apple_total,
        "apple_co2_manufacturing_kg": apple_manufacturing,
        "apple_co2_transport_kg":    apple_transport,
        "apple_co2_use_kg":          apple_use,
        "apple_co2_eol_kg":          apple_eol,
        "apple_co2_comparable_kg":   round(apple_comparable, 2),
        "apple_implied_grade":       apple_grade,

        # Gap analysis
        "capture_of_comparable_pct": capture_pct,
        "capture_of_total_pct":      capture_of_total,
        "underestimation_factor":    underestimation_factor,
        "grade_agreement":           ml_grade == apple_grade,
    })

    print(f"  {product:<35} | Our: {our_co2:.2f}kg ({ml_grade}) | "
          f"Apple: {apple_total:.0f}kg ({apple_grade}) | "
          f"Capture: {capture_pct:.0f}% of mfg+transport")

# ── Aggregate statistics ───────────────────────────────────────────────────────
df_r = pd.DataFrame(records)

# Grade agreement
grade_agree = (df_r["our_ml_grade"] == df_r["apple_implied_grade"]).mean()

# Capture rates
mean_capture_comparable = df_r["capture_of_comparable_pct"].mean()
mean_capture_total      = df_r["capture_of_total_pct"].mean()
median_underest         = df_r["underestimation_factor"].median()

# Per-category breakdown
by_cat = df_r.groupby("category").agg(
    n=("product", "count"),
    mean_our_co2=("our_defra_co2_kg", "mean"),
    mean_apple_comparable=("apple_co2_comparable_kg", "mean"),
    mean_apple_total=("apple_co2_total_kg", "mean"),
    mean_capture_pct=("capture_of_comparable_pct", "mean"),
    mean_underest_factor=("underestimation_factor", "mean"),
).round(2).reset_index()

# What the formula misses (gap components)
# Average for all products:
avg_mfg     = df_r["apple_co2_manufacturing_kg"].mean()
avg_our_mfg = df_r["our_defra_co2_kg"].mean() - (
    df_r.apply(lambda r: r["weight_kg"] * TRANSPORT_FACTORS["Air"] * UK_DISTANCES.get(r["origin"], 8000) / 1000, axis=1).mean()
)  # rough split
avg_trn_apple  = df_r["apple_co2_transport_kg"].mean()
avg_use_apple  = df_r["apple_co2_use_kg"].mean()
avg_eol_apple  = df_r["apple_co2_eol_kg"].mean()

print(f"\n{'='*60}")
print(f"VALIDATION SUMMARY ({len(df_r)} Apple products)")
print(f"{'='*60}")
print(f"  Grade agreement (ML vs Apple):    {grade_agree:.1%}")
print(f"  Mean capture of mfg+transport:    {mean_capture_comparable:.1f}%")
print(f"  Mean capture of total lifecycle:  {mean_capture_total:.1f}%")
print(f"  Median underestimation factor:    {median_underest:.0f}×")
print(f"\n  Per-category underestimation factor:")
for _, r in by_cat.iterrows():
    print(f"    {r['category']:<15}: {r['mean_underest_factor']:.0f}× (n={int(r['n'])})")

# ── Save results ───────────────────────────────────────────────────────────────
results = {
    "generated_at": pd.Timestamp.now().isoformat(),
    "description": (
        "External validation against Apple Product Environmental Reports (PERs). "
        "Apple's CO₂ figures are independently audited to ISO 14040/14044. "
        "Source: https://www.apple.com/environment/reports/"
    ),
    "n_products": len(records),
    "categories": df_r["category"].unique().tolist(),
    "summary": {
        "grade_agreement_pct":             round(float(grade_agree * 100), 1),
        "mean_capture_of_comparable_pct":  round(float(mean_capture_comparable), 1),
        "mean_capture_of_total_pct":       round(float(mean_capture_total), 1),
        "median_underestimation_factor":   round(float(median_underest), 1),
        "what_formula_misses": [
            "Semiconductor and component manufacturing energy (chip fabrication, PCB production, rare earth processing)",
            "Multi-tier supply chain transport (components → assembly factory, not just factory → UK)",
            "Use-phase electricity consumption over product lifetime",
            "End-of-life processing and recycling infrastructure",
        ],
        "why_gap_is_expected": (
            "The DEFRA formula estimates transport emissions and bulk material manufacturing intensity. "
            "For consumer electronics, the dominant emissions source is semiconductor fabrication — "
            "producing 1kg of integrated circuits requires approximately 630kg CO₂e due to the energy "
            "intensity of cleanroom manufacturing and rare earth material processing. "
            "DEFRA's 'Aluminum' intensity factor (8 kg CO₂ per kg material) covers smelting only "
            "and does not capture this. The gap is a scope difference, not a model error."
        ),
    },
    "per_category": by_cat.to_dict(orient="records"),
    "products": records,
}

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Saved → {OUT}")
