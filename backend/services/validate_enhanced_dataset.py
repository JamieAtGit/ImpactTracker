#!/usr/bin/env python3
"""
Enhanced Dataset Validation Script
Validates data integrity, column structure, and quality of the enhanced dataset
"""

import csv
import json
from typing import Dict, List, Any, Set
from collections import Counter
import os

class DatasetValidator:
    """
    Comprehensive validation for the enhanced eco dataset
    """
    
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.required_columns = [
            'title', 'material', 'weight', 'transport', 'recyclability', 
            'true_eco_score', 'co2_emissions', 'origin', 'material_confidence',
            'secondary_materials', 'packaging_type', 'packaging_materials',
            'packaging_weight_ratio', 'inferred_category', 'origin_confidence',
            'estimated_lifespan_years', 'repairability_score', 'size_category',
            'quality_level', 'is_eco_labeled', 'is_amazon_choice', 'pack_size',
            'estimated_volume_l', 'weight_confidence'
        ]
        self.validation_results = {}
    
    def validate_column_structure(self) -> Dict[str, Any]:
        """Validate that all required columns are present"""
        print("🔍 Validating column structure...")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actual_columns = reader.fieldnames
        
        missing_columns = set(self.required_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(self.required_columns)
        
        result = {
            'total_required': len(self.required_columns),
            'total_actual': len(actual_columns),
            'missing_columns': list(missing_columns),
            'extra_columns': list(extra_columns),
            'valid_structure': len(missing_columns) == 0
        }
        
        if result['valid_structure']:
            print("✅ Column structure is valid")
        else:
            print(f"❌ Missing columns: {missing_columns}")
            print(f"❌ Extra columns: {extra_columns}")
        
        return result
    
    def validate_data_types_and_ranges(self) -> Dict[str, Any]:
        """Validate data types and reasonable value ranges"""
        print("🔍 Validating data types and ranges...")
        
        errors = []
        warnings = []
        stats = {
            'total_rows': 0,
            'numeric_fields': {},
            'categorical_fields': {},
            'text_fields': {}
        }
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                stats['total_rows'] = row_num
                
                # Skip header row in error reporting
                if row_num == 1:
                    continue
                
                # Validate numeric fields
                try:
                    weight = float(row['weight'])
                    if weight <= 0 or weight > 1000:
                        warnings.append(f"Row {row_num}: Unusual weight {weight}kg")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid weight '{row['weight']}'")
                
                try:
                    co2 = float(row['co2_emissions'])
                    if co2 <= 0 or co2 > 100000:
                        warnings.append(f"Row {row_num}: Unusual CO2 {co2}kg")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid CO2 '{row['co2_emissions']}'")
                
                try:
                    confidence = float(row['material_confidence'])
                    if confidence < 0 or confidence > 1:
                        errors.append(f"Row {row_num}: Material confidence out of range: {confidence}")
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid material confidence '{row['material_confidence']}'")
                
                # Validate categorical fields
                valid_transports = {'Air', 'Ship', 'Land'}
                if row['transport'] not in valid_transports:
                    errors.append(f"Row {row_num}: Invalid transport '{row['transport']}'")
                
                valid_recyclability = {'Low', 'Medium', 'High', 'Very High'}
                if row['recyclability'] not in valid_recyclability:
                    errors.append(f"Row {row_num}: Invalid recyclability '{row['recyclability']}'")
                
                valid_eco_scores = {'A', 'B', 'C', 'D', 'E', 'F', 'G'}
                if row['true_eco_score'] not in valid_eco_scores:
                    errors.append(f"Row {row_num}: Invalid eco score '{row['true_eco_score']}'")
                
                # Validate boolean fields
                if row['is_eco_labeled'] not in ['True', 'False']:
                    errors.append(f"Row {row_num}: Invalid is_eco_labeled '{row['is_eco_labeled']}'")
                
                # Validate text fields are not empty
                if not row['title'].strip():
                    errors.append(f"Row {row_num}: Empty title")
                
                if not row['material'].strip():
                    errors.append(f"Row {row_num}: Empty material")
                
                # Stop after checking 10,000 rows to avoid excessive processing
                if row_num > 10000:
                    break
        
        result = {
            'total_errors': len(errors),
            'total_warnings': len(warnings),
            'errors': errors[:20],  # Show first 20 errors
            'warnings': warnings[:20],  # Show first 20 warnings
            'rows_checked': min(stats['total_rows'], 10000)
        }
        
        print(f"✅ Checked {result['rows_checked']} rows")
        print(f"📊 Found {result['total_errors']} errors, {result['total_warnings']} warnings")
        
        return result
    
    def analyze_data_distribution(self) -> Dict[str, Any]:
        """Analyze the distribution of key fields"""
        print("🔍 Analyzing data distribution...")
        
        categories = Counter()
        materials = Counter()
        origins = Counter()
        transports = Counter()
        eco_scores = Counter()
        quality_levels = Counter()
        
        weight_ranges = {'0-0.5kg': 0, '0.5-2kg': 0, '2-10kg': 0, '10kg+': 0}
        co2_ranges = {'0-50': 0, '50-200': 0, '200-1000': 0, '1000+': 0}
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                categories[row['inferred_category']] += 1
                materials[row['material']] += 1
                origins[row['origin']] += 1
                transports[row['transport']] += 1
                eco_scores[row['true_eco_score']] += 1
                quality_levels[row['quality_level']] += 1
                
                # Weight distribution
                try:
                    weight = float(row['weight'])
                    if weight <= 0.5:
                        weight_ranges['0-0.5kg'] += 1
                    elif weight <= 2:
                        weight_ranges['0.5-2kg'] += 1
                    elif weight <= 10:
                        weight_ranges['2-10kg'] += 1
                    else:
                        weight_ranges['10kg+'] += 1
                except ValueError:
                    pass
                
                # CO2 distribution
                try:
                    co2 = float(row['co2_emissions'])
                    if co2 <= 50:
                        co2_ranges['0-50'] += 1
                    elif co2 <= 200:
                        co2_ranges['50-200'] += 1
                    elif co2 <= 1000:
                        co2_ranges['200-1000'] += 1
                    else:
                        co2_ranges['1000+'] += 1
                except ValueError:
                    pass
        
        result = {
            'top_categories': dict(categories.most_common(10)),
            'top_materials': dict(materials.most_common(10)),
            'top_origins': dict(origins.most_common(10)),
            'transport_distribution': dict(transports),
            'eco_score_distribution': dict(eco_scores),
            'quality_distribution': dict(quality_levels),
            'weight_ranges': weight_ranges,
            'co2_ranges': co2_ranges,
            'total_unique_categories': len(categories),
            'total_unique_materials': len(materials),
            'total_unique_origins': len(origins)
        }
        
        print(f"📊 Found {result['total_unique_categories']} unique categories")
        print(f"📊 Found {result['total_unique_materials']} unique materials")
        print(f"📊 Found {result['total_unique_origins']} unique origins")
        
        return result
    
    def check_data_quality(self) -> Dict[str, Any]:
        """Check overall data quality metrics"""
        print("🔍 Checking data quality...")
        
        quality_issues = []
        sample_products = []
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                # Sample first 5 and last 5 products
                if row_num <= 5 or row_num >= 50000:
                    sample_products.append({
                        'row': row_num,
                        'title': row['title'][:50] + '...' if len(row['title']) > 50 else row['title'],
                        'material': row['material'],
                        'category': row['inferred_category'],
                        'eco_score': row['true_eco_score'],
                        'origin': row['origin']
                    })
                
                # Check for suspicious patterns
                if row['title'].count(' ') < 1:
                    quality_issues.append(f"Row {row_num}: Very short title '{row['title']}'")
                
                if len(quality_issues) >= 20:
                    break
        
        result = {
            'quality_issues': quality_issues,
            'sample_products': sample_products,
            'total_quality_issues': len(quality_issues)
        }
        
        print(f"📊 Found {result['total_quality_issues']} quality issues")
        
        return result
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Starting full dataset validation...")
        print(f"📁 Dataset: {self.dataset_path}")
        
        # Get dataset size
        with open(self.dataset_path, 'r') as f:
            total_lines = sum(1 for _ in f)
        
        print(f"📊 Total rows: {total_lines:,} (including header)")
        
        results = {
            'dataset_info': {
                'path': self.dataset_path,
                'total_rows': total_lines,
                'size_mb': os.path.getsize(self.dataset_path) / 1024 / 1024
            },
            'column_validation': self.validate_column_structure(),
            'data_validation': self.validate_data_types_and_ranges(),
            'distribution_analysis': self.analyze_data_distribution(),
            'quality_check': self.check_data_quality()
        }
        
        # Overall assessment
        has_critical_errors = (
            not results['column_validation']['valid_structure'] or
            results['data_validation']['total_errors'] > 100
        )
        
        results['overall_assessment'] = {
            'status': 'FAIL' if has_critical_errors else 'PASS',
            'ready_for_production': not has_critical_errors,
            'critical_issues': has_critical_errors
        }
        
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        print(f"Status: {'❌ FAIL' if has_critical_errors else '✅ PASS'}")
        print(f"Dataset size: {total_lines:,} rows ({results['dataset_info']['size_mb']:.1f} MB)")
        print(f"Column structure: {'✅ Valid' if results['column_validation']['valid_structure'] else '❌ Invalid'}")
        print(f"Data validation: {results['data_validation']['total_errors']} errors, {results['data_validation']['total_warnings']} warnings")
        print(f"Unique categories: {results['distribution_analysis']['total_unique_categories']}")
        print(f"Unique materials: {results['distribution_analysis']['total_unique_materials']}")
        print(f"Ready for production: {'✅ Yes' if results['overall_assessment']['ready_for_production'] else '❌ No'}")
        print("="*60)
        
        return results
    
    def export_validation_report(self, results: Dict[str, Any], output_path: str = None):
        """Export detailed validation report"""
        if not output_path:
            import os
            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            SERVICES_DIR = os.path.join(PROJECT_ROOT, 'backend', 'services')
            output_path = os.path.join(SERVICES_DIR, 'dataset_validation_report.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Validation report saved to: {output_path}")

if __name__ == "__main__":
    import os
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    dataset_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
    validator = DatasetValidator(dataset_path)
    results = validator.run_full_validation()
    validator.export_validation_report(results)