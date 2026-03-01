#!/usr/bin/env python3
"""
Debug script to test the materials intelligence integration in the API
"""
import sys
import os
import json

# Add the backend directory to the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.materials_service import detect_product_materials

def test_materials_service():
    print("🧪 TESTING MATERIALS SERVICE INTEGRATION")
    print("=" * 60)
    
    # Test with sample product data (simulating what comes from scraper)
    test_product = {
        'title': 'Optimum Nutrition Gold Standard 100% Whey Protein Powder',
        'category': 'Health & Personal Care',
        'brand': 'Optimum Nutrition'
    }
    
    # Test without Amazon materials (should use Tier 4)
    print("📦 Testing product:", test_product['title'])
    result = detect_product_materials(test_product, None)
    
    print("\n🎯 MATERIALS INTELLIGENCE RESULT:")
    print(json.dumps(result, indent=2))
    
    print(f"\n✅ Tier {result['tier']}: {result['tier_name']}")
    print(f"✅ Primary Material: {result['primary_material']}")
    print(f"✅ Confidence: {result['confidence']}")
    
    if result.get('secondary_materials'):
        print(f"✅ Secondary Materials: {[m['name'] for m in result['secondary_materials']]}")
    
    print(f"✅ Environmental Impact: {result['environmental_impact_score']} kg CO₂/kg")
    
    return result

def simulate_api_integration():
    print("\n" + "=" * 60)
    print("🔧 SIMULATING API INTEGRATION")
    print("=" * 60)
    
    # Simulate what happens in the API
    product = {
        'title': 'Apple MacBook Pro 16-inch Laptop',
        'category': 'Electronics',
        'brand': 'Apple',
        'material_type': 'Mixed'  # What the old system might detect
    }
    
    # This is what happens in app.py around line 1613
    product_analysis_data = {
        'title': product.get('title', ''),
        'description': product.get('description', ''),
        'category': product.get('category', ''),
        'brand': product.get('brand', '')
    }
    
    amazon_materials = None  # No detailed materials from scraper
    
    # Apply 5-tier materials intelligence
    materials_result = detect_product_materials(product_analysis_data, amazon_materials)
    
    # Update product with enhanced materials data (as done in API)
    product['materials'] = {
        'primary_material': materials_result['primary_material'],
        'primary_percentage': materials_result.get('primary_percentage'),
        'secondary_materials': materials_result.get('secondary_materials', []),
        'all_materials': materials_result.get('all_materials', []),
        'confidence': materials_result['confidence'],
        'environmental_impact_score': materials_result.get('environmental_impact_score', 2.5),
        'has_percentages': materials_result.get('has_percentages', False),
        'tier': materials_result['tier'],
        'tier_name': materials_result['tier_name'],
        'prediction_method': materials_result.get('prediction_method', '')
    }
    
    print("📱 SIMULATED API RESPONSE STRUCTURE:")
    print("data.attributes.materials =", json.dumps(product['materials'], indent=2))
    
    # Check what frontend should see
    print("\n🖥️ WHAT FRONTEND SHOULD DISPLAY:")
    materials = product['materials']
    if materials['tier'] and materials['primary_material'] not in ['Mixed', 'Unknown']:
        print(f"✅ Enhanced materials display should show:")
        print(f"   Primary Material: {materials['primary_material']}")
        print(f"   Tier: {materials['tier']} - {materials['tier_name']}")
        print(f"   Confidence: {materials['confidence'] * 100:.0f}%")
        if materials['secondary_materials']:
            print(f"   Secondary: {[m['name'] for m in materials['secondary_materials']]}")
    else:
        print("⚠️ Would fall back to basic material display")
    
    return product

if __name__ == "__main__":
    try:
        # Test 1: Basic service functionality
        test_materials_service()
        
        # Test 2: API integration simulation
        simulate_api_integration()
        
        print("\n🎉 All tests completed successfully!")
        print("If you're not seeing materials data in frontend, the issue is likely:")
        print("1. Frontend not making API calls with the enhanced backend")
        print("2. Data not flowing from API response to frontend state")
        print("3. Frontend conditional logic preventing display")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
