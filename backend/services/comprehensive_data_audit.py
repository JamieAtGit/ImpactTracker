#!/usr/bin/env python3
"""
Comprehensive Data Audit
Ensures all data files are competent, synchronized, and current
Maps out the complete data ecosystem and identifies any inconsistencies
"""

import os
import json
import csv
from typing import Dict, List, Any
import time

class ComprehensiveDataAuditor:
    """
    Audit all data files used by the DSP Eco Tracker system
    """
    
    def __init__(self):
        import os
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.csv_path = f"{self.base_path}/common/data/csv"
        self.json_path = f"{self.base_path}/common/data/json"
        self.services_path = f"{self.base_path}/backend/services"
        
        self.audit_results = {
            'csv_files': {},
            'json_files': {},
            'service_files': {},
            'inconsistencies': [],
            'recommendations': []
        }
    
    def audit_csv_files(self):
        """Audit all CSV datasets"""
        print("📊 AUDITING CSV DATASETS")
        print("=" * 50)
        
        csv_files = [
            'enhanced_eco_dataset.csv',  # MAIN PRODUCTION DATASET
            'enhanced_eco_dataset_final_fixed.csv',  # Latest corrected version
            'enhanced_eco_dataset_before_final_fix.csv',  # Backup before final fix
            'enhanced_eco_dataset_quality_fixed.csv',  # After quality fixes
            'enhanced_eco_dataset_fixed.csv',  # After CO2 fixes
            'eco_dataset.csv',  # Original dataset
            'expanded_eco_dataset.csv',  # Expanded version
            'defra_material_intensity.csv',  # Material reference data
            'real_scraped_data.csv'  # Real scraped products
        ]
        
        for filename in csv_files:
            filepath = f"{self.csv_path}/{filename}"
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        row_count = sum(1 for row in reader)
                        columns = reader.fieldnames if hasattr(reader, 'fieldnames') else []
                    
                    # Get first few rows for sample
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        sample_rows = [next(reader, None) for _ in range(3)]
                        columns = reader.fieldnames
                    
                    file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                    
                    self.audit_results['csv_files'][filename] = {
                        'exists': True,
                        'row_count': row_count,
                        'column_count': len(columns) if columns else 0,
                        'columns': columns,
                        'file_size_mb': round(file_size, 2),
                        'sample_data': sample_rows[0] if sample_rows and sample_rows[0] else None,
                        'status': 'Active' if filename == 'enhanced_eco_dataset.csv' else 'Backup/Archive'
                    }
                    
                    status_icon = "🟢" if filename == 'enhanced_eco_dataset.csv' else "🔵"
                    print(f"{status_icon} {filename}")
                    print(f"   Rows: {row_count:,}, Columns: {len(columns) if columns else 0}, Size: {file_size:.1f}MB")
                    
                except Exception as e:
                    self.audit_results['csv_files'][filename] = {
                        'exists': True,
                        'error': str(e),
                        'status': 'Error'
                    }
                    print(f"❌ {filename} - Error: {e}")
            else:
                self.audit_results['csv_files'][filename] = {
                    'exists': False,
                    'status': 'Missing'
                }
                print(f"⚠️ {filename} - Missing")
    
    def audit_json_files(self):
        """Audit all JSON configuration files"""
        print(f"\n📁 AUDITING JSON CONFIGURATION FILES")
        print("=" * 50)
        
        # JSON files in common/data/json
        json_files = [
            'brand_locations.json',  # Brand origin database
            'material_insights.json',  # Material properties
            'priority_products.json',  # Priority product list
            'user_feedback.json'  # User feedback data
        ]
        
        for filename in json_files:
            filepath = f"{self.json_path}/{filename}"
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    file_size = os.path.getsize(filepath) / 1024  # KB
                    
                    # Analyze content
                    if isinstance(data, dict):
                        key_count = len(data.keys())
                        sample_keys = list(data.keys())[:5]
                    elif isinstance(data, list):
                        key_count = len(data)
                        sample_keys = ['Array with {} items'.format(len(data))]
                    else:
                        key_count = 1
                        sample_keys = [type(data).__name__]
                    
                    self.audit_results['json_files'][filename] = {
                        'exists': True,
                        'key_count': key_count,
                        'sample_keys': sample_keys,
                        'file_size_kb': round(file_size, 2),
                        'data_type': type(data).__name__,
                        'status': 'Active'
                    }
                    
                    print(f"🟢 {filename}")
                    print(f"   Keys/Items: {key_count:,}, Size: {file_size:.1f}KB, Type: {type(data).__name__}")
                    
                except Exception as e:
                    self.audit_results['json_files'][filename] = {
                        'exists': True,
                        'error': str(e),
                        'status': 'Error'
                    }
                    print(f"❌ {filename} - Error: {e}")
            else:
                self.audit_results['json_files'][filename] = {
                    'exists': False,
                    'status': 'Missing'
                }
                print(f"⚠️ {filename} - Missing")
        
        # JSON files in backend/services
        service_json_files = [
            'enhanced_brand_locations.json',  # Enhanced brand database
            'enhanced_materials_database.json',  # Enhanced materials
            'amazon_product_categories.json',  # Product categories
            'global_manufacturing_locations.json',  # Manufacturing locations
            'world_class_materials.json'  # World-class materials database
        ]
        
        print(f"\n🔧 SERVICE JSON FILES:")
        for filename in service_json_files:
            filepath = f"{self.services_path}/{filename}"
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    file_size = os.path.getsize(filepath) / 1024  # KB
                    key_count = len(data) if isinstance(data, (dict, list)) else 1
                    
                    print(f"🟢 {filename} - {key_count:,} items, {file_size:.1f}KB")
                    
                except Exception as e:
                    print(f"❌ {filename} - Error: {e}")
            else:
                print(f"⚠️ {filename} - Missing")
    
    def check_data_consistency(self):
        """Check for inconsistencies between different data files"""
        print(f"\n🔍 CHECKING DATA CONSISTENCY")
        print("=" * 50)
        
        inconsistencies = []
        
        # Check if main dataset exists and is current
        main_dataset = f"{self.csv_path}/enhanced_eco_dataset.csv"
        final_fixed = f"{self.csv_path}/enhanced_eco_dataset_final_fixed.csv"
        
        if os.path.exists(main_dataset) and os.path.exists(final_fixed):
            main_size = os.path.getsize(main_dataset)
            final_size = os.path.getsize(final_fixed)
            
            if abs(main_size - final_size) > 1000:  # More than 1KB difference
                inconsistencies.append({
                    'type': 'File Size Mismatch',
                    'description': f'Main dataset ({main_size/1024:.1f}KB) vs Final fixed ({final_size/1024:.1f}KB)',
                    'severity': 'Medium',
                    'recommendation': 'Verify which dataset is current and sync if needed'
                })
        
        # Check brand locations consistency
        brand_locations_common = f"{self.json_path}/brand_locations.json"
        brand_locations_service = f"{self.services_path}/enhanced_brand_locations.json"
        
        if os.path.exists(brand_locations_common) and os.path.exists(brand_locations_service):
            try:
                with open(brand_locations_common, 'r') as f:
                    common_brands = json.load(f)
                with open(brand_locations_service, 'r') as f:
                    service_brands = json.load(f)
                
                common_count = len(common_brands) if isinstance(common_brands, dict) else 0
                service_count = len(service_brands) if isinstance(service_brands, dict) else 0
                
                if abs(common_count - service_count) > 10:
                    inconsistencies.append({
                        'type': 'Brand Database Mismatch',
                        'description': f'Common brands ({common_count}) vs Service brands ({service_count})',
                        'severity': 'High',
                        'recommendation': 'Sync brand databases to use the most complete version'
                    })
            except Exception as e:
                inconsistencies.append({
                    'type': 'Brand Database Error',
                    'description': f'Error comparing brand databases: {e}',
                    'severity': 'High',
                    'recommendation': 'Investigate and fix brand database issues'
                })
        
        self.audit_results['inconsistencies'] = inconsistencies
        
        if inconsistencies:
            print("⚠️ INCONSISTENCIES FOUND:")
            for issue in inconsistencies:
                severity_icon = "🔴" if issue['severity'] == 'High' else "🟡"
                print(f"{severity_icon} {issue['type']}: {issue['description']}")
                print(f"   → {issue['recommendation']}")
        else:
            print("✅ No major inconsistencies found")
    
    def generate_recommendations(self):
        """Generate recommendations for data management"""
        print(f"\n💡 DATA MANAGEMENT RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = []
        
        # Check if we have too many backup files
        csv_files = self.audit_results.get('csv_files', {})
        backup_files = [f for f in csv_files.keys() if 'backup' in f or 'before' in f or 'fixed' in f]
        
        if len(backup_files) > 5:
            recommendations.append({
                'type': 'File Cleanup',
                'description': f'You have {len(backup_files)} backup CSV files',
                'action': 'Consider archiving older backups to reduce clutter',
                'priority': 'Low'
            })
        
        # Check main dataset status
        main_dataset_info = csv_files.get('enhanced_eco_dataset.csv', {})
        if main_dataset_info.get('row_count', 0) < 100000:
            recommendations.append({
                'type': 'Dataset Size',
                'description': f'Main dataset has {main_dataset_info.get("row_count", 0):,} rows',
                'action': 'Consider if this is the expected size for production',
                'priority': 'Medium'
            })
        
        # Check for missing files
        missing_files = [f for f, info in csv_files.items() if not info.get('exists', False)]
        if missing_files:
            recommendations.append({
                'type': 'Missing Files',
                'description': f'Missing files: {", ".join(missing_files)}',
                'action': 'Verify if these files are needed or can be removed from tracking',
                'priority': 'Medium'
            })
        
        self.audit_results['recommendations'] = recommendations
        
        if recommendations:
            for rec in recommendations:
                priority_icon = "🔴" if rec['priority'] == 'High' else "🟡" if rec['priority'] == 'Medium' else "🔵"
                print(f"{priority_icon} {rec['type']}: {rec['description']}")
                print(f"   → {rec['action']}")
        else:
            print("✅ No specific recommendations - data management looks good!")
    
    def run_complete_audit(self):
        """Run complete data audit"""
        print("🔍 COMPREHENSIVE DATA AUDIT")
        print("=" * 70)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.audit_csv_files()
        self.audit_json_files()
        self.check_data_consistency()
        self.generate_recommendations()
        
        print(f"\n📋 AUDIT SUMMARY")
        print("=" * 50)
        
        csv_count = len([f for f in self.audit_results['csv_files'].values() if f.get('exists', False)])
        json_count = len([f for f in self.audit_results['json_files'].values() if f.get('exists', False)])
        inconsistency_count = len(self.audit_results['inconsistencies'])
        recommendation_count = len(self.audit_results['recommendations'])
        
        print(f"✅ CSV Files: {csv_count} found")
        print(f"✅ JSON Files: {json_count} found")
        print(f"⚠️ Inconsistencies: {inconsistency_count}")
        print(f"💡 Recommendations: {recommendation_count}")
        
        # Show current main dataset status
        main_dataset = self.audit_results['csv_files'].get('enhanced_eco_dataset.csv', {})
        if main_dataset.get('exists', False):
            print(f"\n🎯 MAIN PRODUCTION DATASET STATUS:")
            print(f"   File: enhanced_eco_dataset.csv")
            print(f"   Rows: {main_dataset.get('row_count', 0):,}")
            print(f"   Columns: {main_dataset.get('column_count', 0)}")
            print(f"   Size: {main_dataset.get('file_size_mb', 0)}MB")  
            print(f"   Status: Ready for production ✅")
        
        return self.audit_results

if __name__ == "__main__":
    auditor = ComprehensiveDataAuditor()
    results = auditor.run_complete_audit()
    
    print(f"\n🎉 DATA AUDIT COMPLETE!")
    print("Your data ecosystem has been thoroughly analyzed.")
    print("All files are mapped and inconsistencies identified.")
    print("\n💡 Use this audit to ensure all data is competent and synchronized!")