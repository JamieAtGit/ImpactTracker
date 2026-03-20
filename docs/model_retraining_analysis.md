# Training Data Quality Analysis and Model Retraining: A Comparative Study

**ImpactTracker — Environmental Impact Prediction System**
University of the West of England · Computer Science Department
Environmental Data Science Research · Machine Learning Applications

---

## Abstract

This document provides a comparative analysis of the ImpactTracker XGBoost classification model before and after a critical data quality intervention identified during development. A systematic audit of the training dataset revealed that only 26.1% of grade labels were consistent with the DEFRA CO₂ thresholds used in the production rule-based system. Following re-labelling using the correct thresholds and expansion to a 50,000-row training corpus, cross-validation accuracy improved from 77.4% ± 1.5% to 99.2% ± 0.1%, and macro-average AUC increased from 0.947 to 0.9998. This document records the discovery, the intervention, and an honest evaluation of both the improvements and the new limitations introduced.

---

## 1. Background

The ImpactTracker system assigns eco grades (A+ through F) to Amazon products using two parallel methods: a deterministic rule-based calculator derived from DEFRA greenhouse gas conversion factors, and an XGBoost classifier trained on historical product data. The rule-based method computes CO₂ from product weight, material type, country of origin, and transport mode using the formula:

```
CO₂ (kg) = (weight × transport_factor × distance ÷ 1000) + (weight × material_intensity)
```

where transport factors and material intensities are sourced from UK DEFRA 2023 greenhouse gas conversion factors. Grades are then assigned by threshold:

| Grade | CO₂ threshold |
|-------|--------------|
| A+    | ≤ 0.05 kg    |
| A     | ≤ 0.15 kg    |
| B     | ≤ 0.40 kg    |
| C     | ≤ 1.00 kg    |
| D     | ≤ 2.50 kg    |
| E     | ≤ 5.00 kg    |
| F     | > 5.00 kg    |

The XGBoost model uses an 8-dimensional feature vector: `[material_enc, transport_enc, recyclability_enc, origin_enc, weight_log, weight_bin, material × transport, origin × recyclability]`, trained using SMOTE-balanced data to counteract class imbalance in the raw dataset.

---

## 2. The Pre-Intervention State

### 2.1 Training Data

Prior to the data quality audit, the model was trained on `ml/eco_dataset.csv`, a dataset of 4,699 rows with 8 columns. The grade distribution was highly skewed:

| Grade | Count | % of dataset |
|-------|-------|-------------|
| F     | 1,696 | 36.1%       |
| D     | 1,433 | 30.5%       |
| C     | 685   | 14.6%       |
| B     | 334   | 7.1%        |
| A     | 258   | 5.5%        |
| E     | 250   | 5.3%        |
| A+    | 42    | 0.9%        |

SMOTE (Synthetic Minority Over-sampling Technique) was applied to balance these classes before training, expanding the effective training set to approximately 11,872 samples.

### 2.2 Performance Metrics (Pre-Intervention)

Evaluation was conducted using 5-fold stratified cross-validation with out-of-fold (OOF) probability estimates to eliminate data leakage.

| Metric | Value |
|--------|-------|
| CV Accuracy (mean ± std) | 77.37% ± 1.47% |
| CV Macro F1 | 0.629 |
| CV Log-Loss | 0.615 |
| CV Brier Score | 0.039 |
| Held-out Test Accuracy | 83.83% |
| Held-out Macro F1 | 0.704 |
| Macro ROC AUC (OOF) | 0.947 |

**Per-class AUC (OOF, one-vs-rest):**

| Grade | AUC   |
|-------|-------|
| A+    | 0.998 |
| A     | 0.899 |
| B     | 0.922 |
| C     | 0.956 |
| D     | 0.975 |
| E     | 0.902 |
| F     | 0.976 |
| **Macro** | **0.947** |

**McNemar's test (ML vs rule-based, test set):**

| | Correct | Incorrect |
|--|--|--|
| ML correct, rule-based wrong | 559 | — |
| ML wrong, rule-based correct | 28  | — |

McNemar statistic: χ² = 491.5 · p < 0.0001. This was interpreted as statistically significant evidence that the ML model outperformed the rule-based system.

---

## 3. Discovery of the Labelling Inconsistency

During a data quality audit, the `true_eco_score` labels in the training dataset were compared against grades that would be assigned by applying the production DEFRA thresholds directly to the `co2_emissions` column in the same rows.

```python
def co2_to_grade(co2):
    if co2 <= 0.05: return "A+"
    if co2 <= 0.15: return "A"
    ...
```

The results were alarming:

**Consistency of labels vs DEFRA thresholds:**

| Dataset | Label–threshold consistency |
|---------|---------------------------|
| `ml/eco_dataset.csv` (4.7k, training) | **26.1%** |
| `expanded_eco_dataset.csv` (50k, unused) | **11.8%** |

This means that for approximately 74% of the rows in the training dataset, the grade label did not correspond to the CO₂ value in the same row when evaluated against the DEFRA thresholds used in production.

### 3.1 Illustrative Examples

| Material | Weight | Transport | Origin | CO₂ (csv) | CSV label | Correct DEFRA label |
|----------|--------|-----------|--------|-----------|-----------|---------------------|
| Bamboo   | 1.81 kg | Air     | Singapore | 2.44 kg | F | D (≤2.50) |
| Paper    | 0.20 kg | Land    | UK        | 0.09 kg | B | A (≤0.15) |
| Steel    | 1.85 kg | Air     | Brazil    | 5.83 kg | F | F (>5.00) ✓ |

In the first example, a product with CO₂ of 2.44 kg was labelled F (which requires CO₂ > 5.0 kg). In the second, a product with CO₂ of 0.09 kg — which unambiguously falls in the A band — was labelled B.

### 3.2 Root Cause

The training datasets were generated in earlier pipeline versions where different CO₂ thresholds or labelling logic were applied. When the production system was subsequently updated to use the standardised DEFRA thresholds, the training data was never re-labelled to match. The model therefore learned a different, internally inconsistent grade-assignment function from the one used in production.

This explains a persistent behavioural anomaly observed in the deployed system: the `eco_score_ml` and `eco_score_rule_based` fields shown to users frequently disagreed, even on products where both methods had all the information needed to reach the same conclusion.

---

## 4. The Intervention

### 4.1 Label Correction

All grade labels in the training data were re-derived from the `co2_emissions` column using the production DEFRA thresholds. This is a principled correction: the CO₂ values in the dataset were generated by applying physical emissions factors to product features; the grades should follow deterministically from those CO₂ values. The mismatch was purely an artefact of historical pipeline drift.

### 4.2 Dataset Expansion

Training was moved from `ml/eco_dataset.csv` (4,699 rows) to `expanded_eco_dataset.csv` (49,999 rows) — a 10× increase. The larger dataset was available in the codebase but had not been used for training. After applying DEFRA re-labelling and SMOTE balancing, the effective training corpus expanded to 148,827 samples.

Grade distribution after re-labelling (50k dataset):

| Grade | Raw count | % of dataset |
|-------|-----------|-------------|
| F     | 21,261    | 42.5%       |
| C     | 8,921     | 17.8%       |
| D     | 8,072     | 16.1%       |
| E     | 6,451     | 12.9%       |
| B     | 3,814     | 7.6%        |
| A     | 1,323     | 2.6%        |
| A+    | 157       | 0.3%        |

The class imbalance — particularly the very low frequency of A+ (0.3%) — is an honest reflection of real-world Amazon product data: very few products have sufficiently low CO₂ to qualify for the top grade. SMOTE was applied to balance all classes to 21,261 samples each.

### 4.3 Model Configuration

The XGBoost hyperparameters were kept identical to ensure a fair comparison:

```
n_estimators=300, max_depth=7, learning_rate=0.08,
subsample=0.85, colsample_bytree=0.85, eval_metric='mlogloss'
```

The 8-feature vector was unchanged to maintain full backward compatibility with the production inference pipeline. Encoders were refit on the larger dataset, expanding material coverage from an estimated 15–20 values to 34 unique materials, and origin coverage to 21 countries.

---

## 5. Post-Intervention Results

### 5.1 Performance Metrics

| Metric | Pre-intervention | Post-intervention | Change |
|--------|-----------------|-------------------|--------|
| CV Accuracy (mean ± std) | 77.37% ± 1.47% | **99.17% ± 0.07%** | +21.8pp |
| CV Macro F1 | 0.629 | **0.992** | +0.363 |
| CV Log-Loss | 0.615 | *not reported* | — |
| Held-out Test Accuracy | 83.83% | **99.28%** | +15.5pp |
| Held-out Macro F1 | 0.704 | **0.993** | +0.289 |
| Macro ROC AUC | 0.947 | **0.9998** | +0.053 |
| Random Forest baseline (CV) | ~73% | **97.85%** | — |

**Per-class AUC (post-intervention):**

| Grade | AUC    |
|-------|--------|
| A+    | 1.0000 |
| A     | 1.0000 |
| B     | 0.9999 |
| C     | 0.9996 |
| D     | 0.9996 |
| E     | 0.9998 |
| F     | 0.9999 |
| **Macro** | **0.9998** |

### 5.2 Cross-Validation Fold Stability

One of the most notable improvements is the reduction in variance across folds:

| Fold | Pre-intervention | Post-intervention |
|------|-----------------|-------------------|
| 1    | 75.53%          | 99.14%            |
| 2    | 78.83%          | 99.30%            |
| 3    | 79.15%          | 99.16%            |
| 4    | 75.93%          | 99.14%            |
| 5    | 77.42%          | 99.10%            |
| Std  | ±1.47%          | **±0.07%**        |

The near-elimination of fold variance (from ±1.47% to ±0.07%) is consistent with the model now learning a well-defined, deterministic function rather than trying to fit noisy, inconsistently labelled data.

---

## 6. Critical Analysis and Limitations

### 6.1 Why 99.3% Accuracy is Expected (Not Suspicious)

The near-perfect accuracy requires explicit justification. The DEFRA grading formula is **deterministic** given the four input features: material, transport mode, origin country, and weight. For any specific combination of these values, there is exactly one correct CO₂ value and therefore exactly one correct grade. The XGBoost model, trained on 148,827 SMOTE-balanced samples that all follow this deterministic rule, is therefore learning a fixed mathematical function — not a probabilistic classification problem. Achieving >99% accuracy in this context is not only unsurprising but is the *expected* outcome of a well-trained model on a deterministic labelling scheme.

The residual 0.7% error rate arises from two sources:
1. **Boundary effects**: products whose CO₂ values fall within 5% of a grade boundary may be encoded to features that the model places on the wrong side
2. **Encoding approximation**: LabelEncoder assigns integer codes to categorical values; the integer relationships (e.g., "China"=3, "Germany"=7) carry no ordinal meaning, so some origin–grade relationships require the model to learn non-linear patterns

### 6.2 What the McNemar Test Now Measures

The pre-intervention McNemar test result (p < 0.0001, ML 83.8% vs rule-based 27.3%) was genuinely interesting: it showed that a model trained on imperfect data could still outperform a rule-based system. However, this result was partly an artefact — the rule-based system scored only 27.3% because it was being evaluated against the *wrong* labels.

Post-intervention, the McNemar comparison (ML 99.3% vs rule-based 100%) is a tautology: the rule-based system achieves 100% because the test labels *are* the rule-based grades. The ML model achieves 99.3% because it nearly perfectly replicates that formula. **This comparison is no longer a meaningful model evaluation metric** and should not be interpreted as evidence of ML superiority. It instead confirms label consistency.

### 6.3 The Persistent Fundamental Ceiling

Both before and after the intervention, the labels are derived from approximated CO₂ estimates, not ground-truth environmental impact measurements. The DEFRA formula accounts for transport emissions and a simplified material manufacturing intensity, but excludes:

- Manufacturing energy consumption at the factory level
- End-of-life processing (landfill, recycling infrastructure)
- Packaging materials and their transport
- Supply chain tiers beyond the point of origin

A product graded "A+" by this system may still carry significant lifecycle emissions not captured in the model. The 99.3% accuracy measures alignment with an approximation of environmental impact, not accuracy against a true ground truth. This is an inherent limitation of any system trained on data derived from a simplified formula rather than full lifecycle assessment (LCA) data.

---

## 7. The Data Flywheel

As a consequence of this analysis, a real-time data collection pipeline was implemented. Every product successfully scraped from Amazon is now appended to `ml/live_scraped.csv` with:
- The 8 production features (material, weight, transport, recyclability, origin, CO₂, grade)
- Grade labels derived using the correct DEFRA thresholds at write time

When the live dataset grows by approximately 10% (approximately 5,000 additional rows), `ml/retrain.py` can be executed to:
1. Load the 50k base dataset and merge with all live-scraped rows
2. Re-derive labels (ensuring new rows are consistently labelled)
3. Refit all encoders on the combined data (incorporating new materials and origins seen in the wild)
4. Retrain XGBoost with identical hyperparameters
5. Regenerate `evaluation_results.json` and update all performance charts on the Learn page

This pipeline is deliberately manual-trigger rather than automatic. Automatic retraining carries a risk of silent degradation if the live-scraped data contains scraping errors or outliers. A human review step before retraining is appropriate given the academic context.

---

## 8. Summary Table

| Dimension | Pre-intervention | Post-intervention |
|-----------|-----------------|-------------------|
| Training rows (raw) | 4,699 | 49,999 |
| Training rows (post-SMOTE) | ~11,872 | ~148,827 |
| Label–threshold consistency | 26.1% | **100%** |
| CV accuracy | 77.4% ± 1.5% | **99.2% ± 0.1%** |
| Macro F1 | 0.629 | **0.992** |
| Macro AUC | 0.947 | **0.9998** |
| ML/rule-based agreement | Frequently divergent | Near-identical |
| Encoder material coverage | ~15 values | **34 values** |
| Encoder origin coverage | ~10 values | **21 countries** |
| McNemar test (ML vs rule) | Meaningful (p<0.001) | Tautological (not applicable) |
| Real-world data pipeline | None | **Live CSV append per scrape** |

---

## 9. Conclusion

The primary contribution of this intervention was not a hyperparameter change or architectural improvement, but the identification and correction of a data quality defect that had been silently undermining the model since its initial training. The 26.1% label consistency finding illustrates a general principle in applied machine learning: a model is only as good as its labels, and label quality auditing — comparing assigned labels against the ground truth definition they are supposed to represent — is an essential step that is frequently omitted in practice.

The resulting model correctly learns the DEFRA grading function with near-perfect accuracy, is internally consistent with the rule-based production system, and is connected to a growing corpus of real Amazon product data. The primary remaining limitation — that the labels themselves derive from an approximation rather than ground-truth lifecycle assessment data — is acknowledged as a scope boundary of the project rather than a correctable defect.

---

*Generated as part of ImpactTracker dissertation documentation, March 2026.*
*All metrics computed using 5-fold stratified cross-validation with out-of-fold probability estimates.*
*DEFRA emission factors sourced from: UK Department for Environment, Food & Rural Affairs, Greenhouse Gas Conversion Factors 2023.*
