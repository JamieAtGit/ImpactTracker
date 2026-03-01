#!/usr/bin/env python3
"""
🎓 Advanced ML Module
====================

Professional-grade machine learning components for research-level
model validation, uncertainty quantification, and bias detection.

This module implements academic-standard ML practices:
- Statistical significance testing
- Cross-validation with confidence intervals  
- Model uncertainty quantification
- Bias detection and fairness analysis
- Ensemble methods and voting classifiers
- Performance monitoring and drift detection

Components:
- model_validator.py: Statistical validation framework
- uncertainty.py: Prediction uncertainty quantification
- bias_detector.py: Fairness and bias analysis
- ensemble.py: Multi-model ensemble methods
- performance_monitor.py: Model drift and performance tracking
"""

__version__ = "1.0.0"
__author__ = "DSP Eco Tracker Research Team"

from .model_validator import ModelValidator
from .uncertainty import UncertaintyQuantifier
from .bias_detector import BiasDetector

__all__ = [
    "ModelValidator",
    "UncertaintyQuantifier", 
    "BiasDetector"
]