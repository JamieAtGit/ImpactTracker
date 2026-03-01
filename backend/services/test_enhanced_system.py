#!/usr/bin/env python3
"""
End-to-End Testing of Enhanced Eco Tracker System
Tests integration of all enhanced databases and dataset functionality
"""

import csv
import json
import random
from typing import Dict, List, Any
import sys
import os

# Add the services directory to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICES_DIR = os.path.join(PROJECT_ROOT, 'backend', 'services')
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)

from amazon_product_categories import AmazonProductCategories
from enhanced_materials_database import EnhancedMaterialsDatabase
from amazon_focused_brand_database import AmazonFocusedBrandDatabase

class EnhancedSystemTester:
    """
    Comprehensive end-to-end testing of the enhanced eco tracker system
    """
    
    def __init__(self):
        print("🚀 Initializing Enhanced System E2E Tests...")
        
        # Initialize all databases
        self.categories_db = AmazonProductCategories()
        self.materials_db = EnhancedMaterialsDatabase()
        self.brands_db = AmazonFocusedBrandDatabase()
        
        # Load dataset sample for testing
        self.dataset_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        self.test_results = {}
        
        print("✅ System initialized successfully")
    
    def test_database_integration(self) -> Dict[str, Any]:
        """Test that all databases work together correctly"""
        print("\n🔧 Testing database integration...")
        
        results = {
            'categories_loaded': len(self.categories_db.categories),
            'materials_loaded': len(self.materials_db.materials_database),
            'brands_loaded': len(self.brands_db.amazon_brands),
            'integration_tests': []
        }
        
        # Test 1: Category-Material mapping
        test_category = 'smartphones'
        category_data = self.categories_db.get_category_data(test_category)
        
        if category_data:
            primary_material = category_data['primary_material']
            material_score = self.materials_db.get_material_impact_score(primary_material)
            
            results['integration_tests'].append({
                'test': 'category_material_lookup',
                'category': test_category,
                'primary_material': primary_material,
                'co2_score': material_score,
                'status': 'PASS' if material_score > 0 else 'FAIL'
            })
        
        # Test 2: Brand-Category alignment
        electronics_brands = []
        for brand_name, brand_data in self.brands_db.amazon_brands.items():
            if 'Electronics' in brand_data.get('amazon_categories', []):
                electronics_brands.append(brand_name)
        
        results['integration_tests'].append({
            'test': 'brand_category_alignment',
            'electronics_brands_found': len(electronics_brands),
            'sample_brands': electronics_brands[:5],
            'status': 'PASS' if len(electronics_brands) > 10 else 'FAIL'
        })
        
        # Test 3: Complete product simulation
        try:
            simulated_product = self._simulate_product_creation('laptops')
            results['integration_tests'].append({
                'test': 'complete_product_simulation',
                'product_created': simulated_product is not None,
                'product_sample': simulated_product,
                'status': 'PASS' if simulated_product else 'FAIL'
            })
        except Exception as e:
            results['integration_tests'].append({
                'test': 'complete_product_simulation',
                'error': str(e),
                'status': 'FAIL'
            })
        
        passed_tests = sum(1 for test in results['integration_tests'] if test['status'] == 'PASS')
        total_tests = len(results['integration_tests'])
        
        print(f"✅ Database Integration: {passed_tests}/{total_tests} tests passed")
        
        return results
    
    def test_dataset_functionality(self) -> Dict[str, Any]:
        """Test dataset loading and querying functionality"""
        print("\n📊 Testing dataset functionality...")
        
        results = {
            'dataset_accessible': False,
            'sample_queries': [],
            'data_quality_checks': []
        }
        
        try:
            # Test dataset accessibility
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                sample_rows = [next(reader) for _ in range(5)]
            
            results['dataset_accessible'] = True
            results['sample_rows_loaded'] = len(sample_rows)
            
            # Test sample queries
            
            # Query 1: Find products by material
            aluminum_products = []
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if 'aluminum' in row['material'].lower():
                        aluminum_products.append(row['title'])
                    if i >= 1000 or len(aluminum_products) >= 10:  # Limit search
                        break
            
            results['sample_queries'].append({
                'query': 'find_aluminum_products',
                'results_found': len(aluminum_products),
                'sample_results': aluminum_products[:3],
                'status': 'PASS' if len(aluminum_products) > 0 else 'FAIL'
            })
            
            # Query 2: Find high eco-score products
            eco_friendly_products = []
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if row['true_eco_score'] in ['A', 'B']:
                        eco_friendly_products.append({
                            'title': row['title'],
                            'score': row['true_eco_score'],
                            'co2': row['co2_emissions']
                        })
                    if i >= 1000 or len(eco_friendly_products) >= 10:
                        break
            
            results['sample_queries'].append({
                'query': 'find_eco_friendly_products',
                'results_found': len(eco_friendly_products),
                'sample_results': eco_friendly_products[:3],
                'status': 'PASS' if len(eco_friendly_products) > 0 else 'FAIL'
            })
            
            # Data quality checks
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                empty_titles = 0
                invalid_weights = 0
                invalid_co2 = 0
                
                for i, row in enumerate(reader):
                    if not row['title'].strip():
                        empty_titles += 1
                    
                    try:
                        weight = float(row['weight'])
                        if weight <= 0:
                            invalid_weights += 1
                    except ValueError:
                        invalid_weights += 1
                    
                    try:
                        co2 = float(row['co2_emissions'])
                        if co2 <= 0:
                            invalid_co2 += 1
                    except ValueError:
                        invalid_co2 += 1
                    
                    if i >= 5000:  # Check first 5000 rows
                        break
                
                results['data_quality_checks'] = {
                    'empty_titles': empty_titles,
                    'invalid_weights': invalid_weights,
                    'invalid_co2': invalid_co2,
                    'rows_checked': min(5000, i + 1),
                    'quality_score': 1.0 - (empty_titles + invalid_weights + invalid_co2) / min(5000, i + 1)
                }
        
        except Exception as e:
            results['error'] = str(e)
            results['dataset_accessible'] = False
        
        passed_queries = sum(1 for query in results['sample_queries'] if query['status'] == 'PASS')
        total_queries = len(results['sample_queries'])
        
        print(f"✅ Dataset Functionality: {passed_queries}/{total_queries} queries passed")
        
        return results
    
    def test_realistic_usage_scenarios(self) -> Dict[str, Any]:
        """Test realistic usage scenarios that the system should handle"""
        print("\n🎯 Testing realistic usage scenarios...")
        
        results = {
            'scenarios': []
        }
        
        # Scenario 1: User searches for "iPhone"
        try:
            iphone_matches = self._search_products_by_title("iphone")
            results['scenarios'].append({
                'scenario': 'search_iphone',
                'matches_found': len(iphone_matches),
                'sample_matches': iphone_matches[:3],
                'status': 'PASS' if len(iphone_matches) > 0 else 'FAIL'
            })
        except Exception as e:
            results['scenarios'].append({
                'scenario': 'search_iphone',
                'error': str(e),
                'status': 'FAIL'
            })
        
        # Scenario 2: Material impact analysis
        try:
            aluminum_impact = self.materials_db.get_material_impact_score('aluminum')
            plastic_impact = self.materials_db.get_material_impact_score('abs_plastic')
            
            results['scenarios'].append({
                'scenario': 'material_impact_comparison',
                'aluminum_co2': aluminum_impact,
                'plastic_co2': plastic_impact,
                'comparison_valid': aluminum_impact != plastic_impact,
                'status': 'PASS' if aluminum_impact and plastic_impact else 'FAIL'
            })
        except Exception as e:
            results['scenarios'].append({
                'scenario': 'material_impact_comparison',
                'error': str(e),
                'status': 'FAIL'
            })
        
        # Scenario 3: Category-based product recommendation
        try:
            kitchen_products = self._get_products_by_category('kitchen')
            eco_friendly_kitchen = [p for p in kitchen_products if p.get('eco_score') in ['A', 'B']]
            
            results['scenarios'].append({
                'scenario': 'category_eco_recommendations',
                'total_kitchen_products': len(kitchen_products),
                'eco_friendly_count': len(eco_friendly_kitchen),
                'recommendation_ratio': len(eco_friendly_kitchen) / max(len(kitchen_products), 1),
                'status': 'PASS' if len(kitchen_products) > 0 else 'FAIL'
            })
        except Exception as e:
            results['scenarios'].append({
                'scenario': 'category_eco_recommendations',
                'error': str(e),
                'status': 'FAIL'
            })
        
        # Scenario 4: Brand origin verification
        try:
            apple_info = self.brands_db.get_brand_info('apple')
            nike_info = self.brands_db.get_brand_info('nike')
            
            results['scenarios'].append({
                'scenario': 'brand_origin_lookup',
                'apple_found': apple_info is not None,
                'nike_found': nike_info is not None,
                'apple_origin': apple_info.get('origin', {}).get('country') if apple_info else None,
                'nike_origin': nike_info.get('origin', {}).get('country') if nike_info else None,
                'status': 'PASS' if apple_info and nike_info else 'FAIL'
            })
        except Exception as e:
            results['scenarios'].append({
                'scenario': 'brand_origin_lookup',
                'error': str(e),
                'status': 'FAIL'
            })
        
        passed_scenarios = sum(1 for scenario in results['scenarios'] if scenario['status'] == 'PASS')
        total_scenarios = len(results['scenarios'])
        
        print(f"✅ Usage Scenarios: {passed_scenarios}/{total_scenarios} scenarios passed")
        
        return results
    
    def _simulate_product_creation(self, category: str) -> Dict[str, Any]:
        """Simulate creating a product using all databases"""
        
        # Get category data
        category_data = self.categories_db.get_category_data(category)
        if not category_data:
            return None
        
        # Get material impact
        material = category_data['primary_material']
        co2_intensity = self.materials_db.get_material_impact_score(material)
        
        # Get suitable brand
        suitable_brands = []
        for brand_name, brand_data in self.brands_db.amazon_brands.items():
            categories = brand_data.get('amazon_categories', [])
            if any(cat.lower() in category.lower() for cat in categories):
                suitable_brands.append(brand_name)
        
        brand = random.choice(suitable_brands) if suitable_brands else 'Generic'
        
        return {
            'name': f"{brand.title()} {category.title()} Product",
            'category': category,
            'material': material,
            'co2_intensity': co2_intensity,
            'estimated_weight': category_data.get('avg_weight_kg', 1.0),
            'transport': category_data.get('transport_method', 'ship'),
            'brand_origin': self.brands_db.get_brand_info(brand),
        }
    
    def _search_products_by_title(self, search_term: str, limit: int = 20) -> List[Dict[str, str]]:
        """Search products by title"""
        matches = []
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if search_term.lower() in row['title'].lower():
                    matches.append({
                        'title': row['title'],
                        'material': row['material'],
                        'eco_score': row['true_eco_score'],
                        'co2': row['co2_emissions']
                    })
                
                if len(matches) >= limit:
                    break
        
        return matches
    
    def _get_products_by_category(self, category_search: str, limit: int = 50) -> List[Dict[str, str]]:
        """Get products by category"""
        products = []
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if category_search.lower() in row['inferred_category'].lower():
                    products.append({
                        'title': row['title'],
                        'category': row['inferred_category'],
                        'eco_score': row['true_eco_score'],
                        'material': row['material']
                    })
                
                if len(products) >= limit:
                    break
        
        return products
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        print("🚀 Starting Comprehensive Enhanced System Testing")
        print("=" * 60)
        
        all_results = {
            'system_info': {
                'categories_available': len(self.categories_db.categories),
                'materials_available': len(self.materials_db.materials_database),
                'brands_available': len(self.brands_db.amazon_brands),
                'dataset_path': self.dataset_path
            },
            'database_integration': self.test_database_integration(),
            'dataset_functionality': self.test_dataset_functionality(),
            'usage_scenarios': self.test_realistic_usage_scenarios()
        }
        
        # Calculate overall scores
        integration_score = sum(1 for test in all_results['database_integration']['integration_tests'] 
                               if test['status'] == 'PASS') / len(all_results['database_integration']['integration_tests'])
        
        functionality_score = sum(1 for query in all_results['dataset_functionality']['sample_queries'] 
                                 if query['status'] == 'PASS') / max(len(all_results['dataset_functionality']['sample_queries']), 1)
        
        scenario_score = sum(1 for scenario in all_results['usage_scenarios']['scenarios'] 
                            if scenario['status'] == 'PASS') / len(all_results['usage_scenarios']['scenarios'])
        
        overall_score = (integration_score + functionality_score + scenario_score) / 3
        
        all_results['summary'] = {
            'integration_score': integration_score,
            'functionality_score': functionality_score,
            'scenario_score': scenario_score,
            'overall_score': overall_score,
            'status': 'PASS' if overall_score >= 0.8 else 'FAIL',
            'ready_for_production': overall_score >= 0.9
        }
        
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Score: {overall_score:.1%}")
        print(f"Integration: {integration_score:.1%}")
        print(f"Functionality: {functionality_score:.1%}")
        print(f"Usage Scenarios: {scenario_score:.1%}")
        print(f"Status: {'✅ PASS' if all_results['summary']['status'] == 'PASS' else '❌ FAIL'}")
        print(f"Production Ready: {'✅ Yes' if all_results['summary']['ready_for_production'] else '❌ No'}")
        print("=" * 60)
        
        return all_results
    
    def export_test_report(self, results: Dict[str, Any], output_path: str = None):
        """Export comprehensive test report"""
        if not output_path:
            output_path = os.path.join(SERVICES_DIR, 'system_test_report.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Test report saved to: {output_path}")

if __name__ == "__main__":
    tester = EnhancedSystemTester()
    results = tester.run_comprehensive_test()
    tester.export_test_report(results)