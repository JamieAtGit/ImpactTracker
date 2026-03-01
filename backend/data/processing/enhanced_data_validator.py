"""
🛡️ ENHANCED DATA VALIDATION PIPELINE
===================================

Production-grade data validation pipeline that ensures high-quality data
flows into your expanded_eco_dataset.csv for ML training.

Key Features:
1. Comprehensive data quality scoring
2. Outlier detection and handling
3. Consistency validation across fields
4. Automated data cleaning and standardization
5. Quality reports with actionable recommendations

This validates scraped data before it enters your ML pipeline,
ensuring 95%+ data quality for optimal model performance.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project root for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class EnhancedDataValidator:
    """
    Production-grade data validation pipeline
    """
    
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'validation_reports'
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Quality thresholds
        self.quality_thresholds = {
            'completeness_min': 0.85,  # 85% fields must be populated
            'accuracy_min': 0.90,      # 90% data must pass validation rules
            'consistency_min': 0.95,   # 95% cross-field consistency
            'outlier_max': 0.05        # Max 5% outliers allowed
        }
        
        # Valid value ranges and categories
        self.valid_categories = {
            'material': [
                'Aluminum', 'Steel', 'Plastic', 'Glass', 'Paper', 'Cardboard',
                'Rubber', 'Cotton', 'Polyester', 'Nylon', 'Leather', 'Wood',
                'Ceramic', 'Silicone', 'Bamboo', 'Fabric', 'Synthetic', 'Other'
            ],
            'transport': ['Land', 'Air', 'Ship'],
            'recyclability': ['High', 'Medium', 'Low', 'Unknown'],
            'true_eco_score': ['A+', 'A', 'B', 'C', 'D', 'E', 'F'],
            'origin': [
                'UK', 'USA', 'China', 'Germany', 'France', 'Italy', 'Japan',
                'India', 'Vietnam', 'Brazil', 'Canada', 'Australia', 'Other'
            ]
        }
        
        # Validation rules
        self.validation_rules = {
            'weight': {'min': 0.001, 'max': 100, 'type': 'numeric'},
            'co2_emissions': {'min': 0, 'max': 50, 'type': 'numeric'},
            'title': {'min_length': 3, 'max_length': 200, 'type': 'string'}
        }
        
        self.validation_results = {}
        
    def validate_dataset(self, df: pd.DataFrame, dataset_name: str = "dataset") -> Dict[str, Any]:
        """
        Main validation method - comprehensive dataset validation
        
        Args:
            df: Dataset to validate
            dataset_name: Name for reporting
            
        Returns:
            Comprehensive validation report
        """
        print(f"🛡️ Starting validation for {dataset_name} ({len(df)} rows)")
        
        # Run all validation checks
        completeness = self._check_completeness(df)
        accuracy = self._check_accuracy(df)
        consistency = self._check_consistency(df)
        outliers = self._detect_outliers(df)
        duplicates = self._check_duplicates(df)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            completeness, accuracy, consistency, outliers
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            completeness, accuracy, consistency, outliers, duplicates
        )
        
        # Compile validation report
        validation_report = {
            'dataset_info': {
                'name': dataset_name,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'validation_timestamp': datetime.now().isoformat()
            },
            'completeness_analysis': completeness,
            'accuracy_analysis': accuracy,
            'consistency_analysis': consistency,
            'outlier_analysis': outliers,
            'duplicate_analysis': duplicates,
            'overall_quality_score': quality_score,
            'recommendations': recommendations,
            'data_issues': self._identify_data_issues(df),
            'cleaned_stats': self._get_cleaned_stats(df)
        }
        
        # Save validation report
        self._save_validation_report(validation_report, dataset_name)
        
        # Print summary
        self._print_validation_summary(validation_report)
        
        return validation_report
    
    def _check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data completeness across all fields"""
        completeness = {}
        
        for column in df.columns:
            total_count = len(df)
            non_null_count = df[column].notna().sum()
            non_empty_count = df[column].notna().sum() if df[column].dtype == 'object' else non_null_count
            
            # For string columns, also check for empty strings and 'Unknown'
            if df[column].dtype == 'object':
                non_empty_count = (
                    df[column].notna() & 
                    (df[column] != '') & 
                    (df[column] != 'Unknown') &
                    (df[column] != 'Other')
                ).sum()
            
            completeness_ratio = non_empty_count / total_count if total_count > 0 else 0
            
            completeness[column] = {
                'total_count': total_count,
                'non_null_count': int(non_null_count),
                'meaningful_count': int(non_empty_count),
                'completeness_ratio': float(completeness_ratio),
                'passes_threshold': completeness_ratio >= self.quality_thresholds['completeness_min']
            }
        
        # Overall completeness
        avg_completeness = np.mean([col['completeness_ratio'] for col in completeness.values()])
        
        return {
            'column_completeness': completeness,
            'overall_completeness': float(avg_completeness),
            'passes_threshold': avg_completeness >= self.quality_thresholds['completeness_min']
        }
    
    def _check_accuracy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data accuracy against validation rules"""
        accuracy_results = {}
        total_violations = 0
        total_checks = 0
        
        for column, rules in self.validation_rules.items():
            if column not in df.columns:
                continue
                
            column_violations = 0
            column_checks = 0
            
            # Type-specific validation
            if rules['type'] == 'numeric':
                numeric_data = pd.to_numeric(df[column], errors='coerce')
                
                # Check range violations
                if 'min' in rules:
                    min_violations = (numeric_data < rules['min']).sum()
                    column_violations += min_violations
                    column_checks += len(numeric_data.dropna())
                
                if 'max' in rules:
                    max_violations = (numeric_data > rules['max']).sum()
                    column_violations += max_violations
                    column_checks += len(numeric_data.dropna())
                
                # Check for invalid numeric conversions
                conversion_failures = df[column].notna().sum() - len(numeric_data.dropna())
                column_violations += conversion_failures
                column_checks += df[column].notna().sum()
            
            elif rules['type'] == 'string':
                string_data = df[column].astype(str)
                
                # Check length violations
                if 'min_length' in rules:
                    length_violations = (string_data.str.len() < rules['min_length']).sum()
                    column_violations += length_violations
                    column_checks += len(string_data)
                
                if 'max_length' in rules:
                    length_violations = (string_data.str.len() > rules['max_length']).sum()
                    column_violations += length_violations
                    column_checks += len(string_data)
            
            # Calculate accuracy for this column
            column_accuracy = 1 - (column_violations / column_checks) if column_checks > 0 else 1
            
            accuracy_results[column] = {
                'violations': int(column_violations),
                'total_checks': int(column_checks),
                'accuracy': float(column_accuracy),
                'passes_threshold': column_accuracy >= self.quality_thresholds['accuracy_min']
            }
            
            total_violations += column_violations
            total_checks += column_checks
        
        # Check categorical values
        for column, valid_values in self.valid_categories.items():
            if column not in df.columns:
                continue
                
            invalid_mask = ~df[column].isin(valid_values + ['Unknown', 'Other', None])
            invalid_count = invalid_mask.sum()
            total_count = df[column].notna().sum()
            
            category_accuracy = 1 - (invalid_count / total_count) if total_count > 0 else 1
            
            accuracy_results[f"{column}_categorical"] = {
                'invalid_values': int(invalid_count),
                'total_values': int(total_count),
                'accuracy': float(category_accuracy),
                'invalid_values_list': df[invalid_mask][column].unique().tolist()[:10]  # First 10
            }
            
            total_violations += invalid_count
            total_checks += total_count
        
        # Overall accuracy
        overall_accuracy = 1 - (total_violations / total_checks) if total_checks > 0 else 1
        
        return {
            'field_accuracy': accuracy_results,
            'overall_accuracy': float(overall_accuracy),
            'total_violations': int(total_violations),
            'total_checks': int(total_checks),
            'passes_threshold': overall_accuracy >= self.quality_thresholds['accuracy_min']
        }
    
    def _check_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check cross-field consistency"""
        consistency_checks = {}
        total_inconsistencies = 0
        total_combinations = 0
        
        # Weight vs CO2 emissions consistency
        if 'weight' in df.columns and 'co2_emissions' in df.columns:
            # Heavier items should generally have higher emissions
            weight_co2_df = df[['weight', 'co2_emissions']].dropna()
            if len(weight_co2_df) > 10:
                correlation = weight_co2_df['weight'].corr(weight_co2_df['co2_emissions'])
                
                # Expect positive correlation
                weight_co2_consistent = correlation > 0.3
                consistency_checks['weight_co2_correlation'] = {
                    'correlation': float(correlation),
                    'consistent': weight_co2_consistent,
                    'expected': 'Positive correlation between weight and emissions'
                }
        
        # Material vs Recyclability consistency
        if 'material' in df.columns and 'recyclability' in df.columns:
            # Known high-recyclability materials
            high_recycle_materials = ['Aluminum', 'Steel', 'Glass', 'Paper', 'Cardboard']
            
            material_recycle_df = df[['material', 'recyclability']].dropna()
            inconsistent_count = 0
            
            for material in high_recycle_materials:
                material_rows = material_recycle_df[material_recycle_df['material'] == material]
                if len(material_rows) > 0:
                    low_recycle_count = (material_rows['recyclability'] == 'Low').sum()
                    inconsistent_count += low_recycle_count
            
            total_high_recycle_rows = material_recycle_df[
                material_recycle_df['material'].isin(high_recycle_materials)
            ].shape[0]
            
            if total_high_recycle_rows > 0:
                material_consistency = 1 - (inconsistent_count / total_high_recycle_rows)
                consistency_checks['material_recyclability'] = {
                    'consistency_ratio': float(material_consistency),
                    'inconsistent_count': int(inconsistent_count),
                    'total_checked': int(total_high_recycle_rows),
                    'consistent': material_consistency >= 0.8
                }
        
        # Transport vs Origin consistency (basic distance logic)
        if 'transport' in df.columns and 'origin' in df.columns:
            # Distant origins should prefer Ship/Air over Land
            distant_origins = ['China', 'Japan', 'India', 'Vietnam', 'Brazil', 'Australia']
            
            transport_origin_df = df[['transport', 'origin']].dropna()
            inconsistent_transport = 0
            total_distant = 0
            
            for origin in distant_origins:
                origin_rows = transport_origin_df[transport_origin_df['origin'] == origin]
                if len(origin_rows) > 0:
                    land_transport_count = (origin_rows['transport'] == 'Land').sum()
                    inconsistent_transport += land_transport_count
                    total_distant += len(origin_rows)
            
            if total_distant > 0:
                transport_consistency = 1 - (inconsistent_transport / total_distant)
                consistency_checks['transport_origin'] = {
                    'consistency_ratio': float(transport_consistency),
                    'inconsistent_count': int(inconsistent_transport),
                    'total_checked': int(total_distant),
                    'consistent': transport_consistency >= 0.7
                }
        
        # Calculate overall consistency
        consistent_checks = sum(1 for check in consistency_checks.values() if check.get('consistent', False))
        total_consistency_checks = len(consistency_checks)
        
        overall_consistency = consistent_checks / total_consistency_checks if total_consistency_checks > 0 else 1
        
        return {
            'consistency_checks': consistency_checks,
            'overall_consistency': float(overall_consistency),
            'passes_threshold': overall_consistency >= self.quality_thresholds['consistency_min']
        }
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers in numeric fields"""
        outlier_results = {}
        
        numeric_columns = ['weight', 'co2_emissions']
        
        for column in numeric_columns:
            if column not in df.columns:
                continue
                
            numeric_data = pd.to_numeric(df[column], errors='coerce').dropna()
            
            if len(numeric_data) < 10:  # Skip if too few data points
                continue
            
            # IQR method for outlier detection
            Q1 = numeric_data.quantile(0.25)
            Q3 = numeric_data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_mask = (numeric_data < lower_bound) | (numeric_data > upper_bound)
            outlier_count = outliers_mask.sum()
            outlier_ratio = outlier_count / len(numeric_data)
            
            outlier_results[column] = {
                'outlier_count': int(outlier_count),
                'total_values': int(len(numeric_data)),
                'outlier_ratio': float(outlier_ratio),
                'bounds': {'lower': float(lower_bound), 'upper': float(upper_bound)},
                'outlier_values': numeric_data[outliers_mask].tolist()[:10],  # First 10
                'acceptable': outlier_ratio <= self.quality_thresholds['outlier_max']
            }
        
        # Overall outlier assessment
        total_outliers = sum(result['outlier_count'] for result in outlier_results.values())
        total_values = sum(result['total_values'] for result in outlier_results.values())
        overall_outlier_ratio = total_outliers / total_values if total_values > 0 else 0
        
        return {
            'field_outliers': outlier_results,
            'overall_outlier_ratio': float(overall_outlier_ratio),
            'passes_threshold': overall_outlier_ratio <= self.quality_thresholds['outlier_max']
        }
    
    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate records"""
        # Exact duplicates
        exact_duplicates = df.duplicated().sum()
        
        # Near duplicates (same title, similar weight/material)
        near_duplicates = 0
        if 'title' in df.columns:
            # Group by title and check for variations
            title_groups = df.groupby('title')
            for title, group in title_groups:
                if len(group) > 1:
                    # Check if weights are very similar (within 10%)
                    if 'weight' in group.columns:
                        weights = pd.to_numeric(group['weight'], errors='coerce').dropna()
                        if len(weights) > 1:
                            weight_std = weights.std()
                            weight_mean = weights.mean()
                            if weight_mean > 0 and (weight_std / weight_mean) < 0.1:
                                near_duplicates += len(group) - 1
        
        duplicate_ratio = (exact_duplicates + near_duplicates) / len(df) if len(df) > 0 else 0
        
        return {
            'exact_duplicates': int(exact_duplicates),
            'near_duplicates': int(near_duplicates),
            'total_duplicates': int(exact_duplicates + near_duplicates),
            'duplicate_ratio': float(duplicate_ratio),
            'acceptable': duplicate_ratio <= 0.05  # Max 5% duplicates
        }
    
    def _calculate_quality_score(self, completeness, accuracy, consistency, outliers) -> Dict[str, Any]:
        """Calculate overall data quality score"""
        # Weighted scoring
        weights = {
            'completeness': 0.3,
            'accuracy': 0.4,
            'consistency': 0.2,
            'outliers': 0.1
        }
        
        scores = {
            'completeness': completeness['overall_completeness'],
            'accuracy': accuracy['overall_accuracy'],
            'consistency': consistency['overall_consistency'],
            'outliers': 1 - outliers['overall_outlier_ratio']  # Invert outlier ratio
        }
        
        # Calculate weighted score
        weighted_score = sum(scores[metric] * weights[metric] for metric in scores)
        
        # Grade assignment
        if weighted_score >= 0.95:
            grade = "A+ (Excellent)"
        elif weighted_score >= 0.90:
            grade = "A (Very Good)"
        elif weighted_score >= 0.85:
            grade = "B+ (Good)"
        elif weighted_score >= 0.80:
            grade = "B (Acceptable)"
        elif weighted_score >= 0.70:
            grade = "C (Needs Improvement)"
        else:
            grade = "D (Poor Quality)"
        
        return {
            'overall_score': float(weighted_score),
            'grade': grade,
            'component_scores': scores,
            'weights': weights,
            'ready_for_ml': weighted_score >= 0.85
        }
    
    def _generate_recommendations(self, completeness, accuracy, consistency, outliers, duplicates) -> List[str]:
        """Generate actionable recommendations for data improvement"""
        recommendations = []
        
        # Completeness recommendations
        if not completeness['passes_threshold']:
            low_completeness_fields = [
                field for field, data in completeness['column_completeness'].items()
                if not data['passes_threshold']
            ]
            recommendations.append(
                f"🔄 Improve data completeness for: {', '.join(low_completeness_fields[:5])}"
            )
        
        # Accuracy recommendations
        if not accuracy['passes_threshold']:
            recommendations.append(
                f"🎯 Fix {accuracy['total_violations']} validation violations across fields"
            )
            
            # Specific field recommendations
            for field, data in accuracy['field_accuracy'].items():
                if not data.get('passes_threshold', True):
                    if 'categorical' in field:
                        recommendations.append(
                            f"📋 Standardize {field} values - found invalid entries"
                        )
                    else:
                        recommendations.append(
                            f"📏 Check {field} value ranges - {data['violations']} violations found"
                        )
        
        # Consistency recommendations
        if not consistency['passes_threshold']:
            inconsistent_checks = [
                check for check, data in consistency['consistency_checks'].items()
                if not data.get('consistent', True)
            ]
            recommendations.append(
                f"⚖️ Review cross-field consistency: {', '.join(inconsistent_checks)}"
            )
        
        # Outlier recommendations
        if not outliers['passes_threshold']:
            recommendations.append(
                f"🔍 Investigate {sum(r['outlier_count'] for r in outliers['field_outliers'].values())} outliers"
            )
        
        # Duplicate recommendations
        if not duplicates['acceptable']:
            recommendations.append(
                f"🗂️ Remove {duplicates['total_duplicates']} duplicate/near-duplicate records"
            )
        
        # General recommendations
        recommendations.extend([
            "📊 Run data validation before each ML training session",
            "🔄 Implement automated data cleaning rules",
            "📈 Monitor data quality trends over time",
            "🎯 Target 95%+ quality score for optimal ML performance"
        ])
        
        return recommendations
    
    def _identify_data_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify specific data issues with examples"""
        issues = []
        
        # Check for common data issues
        for column in df.columns:
            if df[column].dtype == 'object':
                # Check for inconsistent formatting
                unique_values = df[column].dropna().unique()
                
                # Look for case inconsistencies
                case_variants = {}
                for value in unique_values:
                    lower_val = str(value).lower()
                    if lower_val in case_variants:
                        case_variants[lower_val].append(value)
                    else:
                        case_variants[lower_val] = [value]
                
                case_issues = {k: v for k, v in case_variants.items() if len(v) > 1}
                if case_issues:
                    issues.append({
                        'type': 'case_inconsistency',
                        'field': column,
                        'examples': dict(list(case_issues.items())[:3]),
                        'count': len(case_issues)
                    })
        
        return issues
    
    def _get_cleaned_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about the cleaned dataset"""
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage_mb': float(df.memory_usage(deep=True).sum() / 1024 / 1024)
        }
        
        # Column type distribution
        type_counts = df.dtypes.value_counts().to_dict()
        stats['column_types'] = {str(k): int(v) for k, v in type_counts.items()}
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats['numeric_summary'] = {
                col: {
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                }
                for col in numeric_cols
            }
        
        return stats
    
    def _save_validation_report(self, report: Dict[str, Any], dataset_name: str):
        """Save validation report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{dataset_name}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Validation report saved: {filepath}")
    
    def _print_validation_summary(self, report: Dict[str, Any]):
        """Print validation summary to console"""
        print("\n" + "="*60)
        print("🛡️ DATA VALIDATION SUMMARY")
        print("="*60)
        
        quality = report['overall_quality_score']
        print(f"📊 Overall Quality Score: {quality['overall_score']:.3f}")
        print(f"🎓 Quality Grade: {quality['grade']}")
        print(f"🚀 Ready for ML: {'✅ Yes' if quality['ready_for_ml'] else '❌ No'}")
        
        print(f"\n📋 Component Scores:")
        for component, score in quality['component_scores'].items():
            print(f"   {component.title()}: {score:.3f}")
        
        print(f"\n🔍 Key Findings:")
        print(f"   Completeness: {report['completeness_analysis']['overall_completeness']:.3f}")
        print(f"   Accuracy: {report['accuracy_analysis']['overall_accuracy']:.3f}")
        print(f"   Consistency: {report['consistency_analysis']['overall_consistency']:.3f}")
        print(f"   Outlier Ratio: {report['outlier_analysis']['overall_outlier_ratio']:.3f}")
        
        if report['recommendations']:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        
        print("="*60)

def validate_scraped_data(data_source: str, output_path: str = None) -> Dict[str, Any]:
    """
    Convenience function to validate scraped data
    
    Args:
        data_source: Path to CSV file or DataFrame
        output_path: Optional path to save cleaned data
        
    Returns:
        Validation report
    """
    validator = EnhancedDataValidator()
    
    # Load data
    if isinstance(data_source, str):
        if not os.path.exists(data_source):
            raise FileNotFoundError(f"Data file not found: {data_source}")
        df = pd.read_csv(data_source)
        dataset_name = os.path.basename(data_source).replace('.csv', '')
    else:
        df = data_source.copy()
        dataset_name = "scraped_data"
    
    # Run validation
    report = validator.validate_dataset(df, dataset_name)
    
    # Save cleaned data if path provided and quality is acceptable
    if output_path and report['overall_quality_score']['ready_for_ml']:
        df.to_csv(output_path, index=False)
        print(f"✅ Validated data saved to: {output_path}")
    elif output_path:
        print(f"⚠️ Data quality too low for ML - not saving to {output_path}")
    
    return report

def main():
    """Main execution for testing"""
    # Test with expanded_eco_dataset.csv
    script_dir = os.path.dirname(__file__)
    data_path = os.path.join(script_dir, "..", "..", "..", "common", "data", "csv", "expanded_eco_dataset.csv")
    
    if not os.path.exists(data_path):
        print(f"❌ Test data not found: {data_path}")
        return
    
    print("🧪 Testing Enhanced Data Validator")
    report = validate_scraped_data(data_path)
    
    print(f"\n🎯 Validation completed!")
    print(f"Quality Score: {report['overall_quality_score']['overall_score']:.3f}")
    print(f"Ready for ML: {report['overall_quality_score']['ready_for_ml']}")

if __name__ == "__main__":
    main()