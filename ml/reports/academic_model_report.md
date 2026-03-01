# Enhanced XGBoost Model Report
## Academic-Level Statistical Analysis

### Model Enhancement Summary
- **Enhanced Features**: 16 features (vs 6 baseline)
- **Dataset**: 4561 samples with 36 total columns
- **Model Type**: XGBoost with academic validation

### Cross-Validation Results (5-fold Stratified)
- **Accuracy**: 0.8446 ± 0.0036 [CI: 0.8391 - 0.8492]
- **F1 Macro**: 0.8462 ± 0.0037 [CI: 0.8405 - 0.8510]
- **F1 Weighted**: 0.8462 ± 0.0037 [CI: 0.8406 - 0.8510]

### Final Model Performance
- **Test Accuracy**: 0.8707
- **Test F1 Score**: 0.8721

### Statistical Significance
- **P-value vs Baseline**: 0.057668
- **Statistically Significant**: False

### Top 5 Most Important Features
1. **pack_size**: 0.1848
2. **transport_encoded**: 0.1409
3. **weight_confidence**: 0.1299
4. **material_encoded**: 0.0911
5. **weight_bin_encoded**: 0.0785


### Academic Rigor Improvements
1. **Enhanced Feature Engineering**: 16 features vs 6 baseline (+167% increase)
2. **Statistical Validation**: Proper stratified k-fold CV with confidence intervals
3. **Significance Testing**: Statistical comparison with baseline performance
4. **Feature Analysis**: Importance ranking with quantitative measures
5. **Reproducibility**: Fixed random seeds and comprehensive logging

### Model Files Generated
- Enhanced XGBoost model: `enhanced_xgb_model.json`
- Backward compatible model: `eco_model.pkl` 
- Feature encoders: `encoders/` directory
- Comprehensive results: `enhanced_model_report.json`
