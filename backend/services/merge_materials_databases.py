#!/usr/bin/env python3
"""
Merge the Amazon-focused materials database with the existing enhanced materials database
"""

import json
import os

def merge_materials_databases():
    """Merge Amazon materials with existing enhanced materials"""
    
    # Load existing enhanced materials database
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    services_dir = os.path.join(project_root, 'backend', 'services')
    enhanced_path = os.path.join(services_dir, 'enhanced_materials_database.json')
    amazon_path = os.path.join(services_dir, 'amazon_materials_database.json')
    
    with open(enhanced_path, 'r', encoding='utf-8') as f:
        enhanced_data = json.load(f)
    
    with open(amazon_path, 'r', encoding='utf-8') as f:
        amazon_data = json.load(f)
    
    existing_materials = enhanced_data.get('materials', {})
    amazon_materials = amazon_data.get('materials', {})
    
    print(f"📥 Existing materials: {len(existing_materials)}")
    print(f"🛒 Amazon materials: {len(amazon_materials)}")
    
    # Merge materials (Amazon materials take priority for Amazon-specific data)
    merged_materials = {}
    merged_materials.update(existing_materials)  # Start with existing
    
    added_count = 0
    updated_count = 0
    
    for material_name, amazon_material in amazon_materials.items():
        if material_name in merged_materials:
            # Update existing material with Amazon-specific data
            existing_material = merged_materials[material_name]
            
            # Merge the data, keeping the best information
            merged_material = existing_material.copy()
            
            # Add Amazon-specific fields
            if 'amazon_products' in amazon_material:
                merged_material['amazon_products'] = amazon_material['amazon_products']
            if 'alternative_names' in amazon_material:
                merged_material['alternative_names'] = amazon_material['alternative_names']
            
            # Update CO2 intensity if Amazon version is more specific/recent
            if amazon_material.get('confidence') == 'high':
                merged_material['co2_intensity'] = amazon_material['co2_intensity']
                merged_material['source'] = amazon_material['source']
            
            merged_materials[material_name] = merged_material
            updated_count += 1
        else:
            # Add new Amazon material
            merged_materials[material_name] = amazon_material
            added_count += 1
    
    print(f"➕ Added {added_count} new materials")
    print(f"🔄 Updated {updated_count} existing materials with Amazon data")
    
    # Create merged database structure
    merged_database = {
        'materials': merged_materials,
        'product_categories': enhanced_data.get('product_categories', {}),
        'amazon_category_mapping': amazon_data.get('category_mapping', {}),
        'metadata': {
            'total_materials': len(merged_materials),
            'version': '3.0',
            'description': 'Enhanced materials database with Amazon-focused materials',
            'sources': ['LCA studies', 'Industry associations', 'Scientific literature', 'Amazon product analysis']
        }
    }
    
    # Export merged database
    output_path = os.path.join(services_dir, 'enhanced_materials_database.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_database, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Merged materials database exported with {len(merged_materials)} total materials")
    
    # Statistics
    categories = {}
    amazon_specific = 0
    
    for material, data in merged_materials.items():
        category = data.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1
        
        if 'amazon_products' in data:
            amazon_specific += 1
    
    print(f"🛒 Materials with Amazon product data: {amazon_specific}")
    print(f"📊 Material categories: {len(categories)}")
    print(f"📈 Top categories: {dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10])}")

if __name__ == "__main__":
    merge_materials_databases()