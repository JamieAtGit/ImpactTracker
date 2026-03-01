#!/usr/bin/env python3
"""
Enhanced Eco Dataset Mass Generator
Generates thousands of realistic Amazon products using our enhanced databases
Creates products that match the existing dataset column structure exactly
"""

import json
import csv
import random
from typing import Dict, List, Any, Tuple
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

class EcoDatasetEnhancer:
    """
    Mass generator for realistic Amazon products using enhanced databases
    """
    
    def __init__(self):
        print("🚀 Initializing Enhanced Eco Dataset Generator...")
        
        # Load our enhanced databases
        self.categories_db = AmazonProductCategories()
        self.materials_db = EnhancedMaterialsDatabase()
        self.brands_db = AmazonFocusedBrandDatabase()
        
        # Load existing dataset for reference
        self.existing_products = self._load_existing_dataset()
        
        # Product generation templates based on real Amazon products
        self.product_templates = self._build_product_templates()
        
        print(f"✅ Initialized with {len(self.categories_db.categories)} categories")
        print(f"✅ Loaded {len(self.materials_db.materials_database)} materials")
        print(f"✅ Loaded {len(self.brands_db.amazon_brands)} brands")
        print(f"📊 Existing dataset: {len(self.existing_products)} products")
    
    def _load_existing_dataset(self) -> List[Dict[str, str]]:
        """Load existing dataset to understand patterns"""
        dataset_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        products = []
        
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Sample first 1000 rows for pattern analysis
                for i, row in enumerate(reader):
                    if i >= 1000:
                        break
                    products.append(row)
        except FileNotFoundError:
            print("⚠️ Existing dataset not found, will create new structure")
        
        return products
    
    def _build_product_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build realistic product name templates for each category"""
        return {
            # Electronics Templates
            "smartphones": [
                {"pattern": "{brand} {model} {spec}", "models": ["Pro", "Max", "Plus", "Ultra", "SE"], "specs": ["128GB", "256GB", "5G", "Dual SIM"]},
                {"pattern": "{brand} {model} Smartphone", "models": ["Galaxy", "Pixel", "iPhone", "OnePlus"], "specs": []},
            ],
            "laptops": [
                {"pattern": "{brand} {model} Laptop", "models": ["ThinkPad", "MacBook", "XPS", "Surface"], "specs": ["15.6\"", "13.3\"", "14\""]},
                {"pattern": "{brand} {model} {spec}", "models": ["Gaming", "Business", "Student"], "specs": ["Intel i7", "Ryzen 5", "M1"]},
            ],
            "headphones": [
                {"pattern": "{brand} {model} Headphones", "models": ["Wireless", "Bluetooth", "Noise Cancelling"], "specs": []},
                {"pattern": "{brand} {model} {spec}", "models": ["Pro", "Elite", "Studio"], "specs": ["Over-Ear", "In-Ear", "On-Ear"]},
            ],
            
            # Clothing Templates
            "casual_clothing": [
                {"pattern": "{brand} {model} {spec}", "models": ["T-Shirt", "Jeans", "Hoodie", "Polo"], "specs": ["Cotton", "Organic", "Slim Fit"]},
                {"pattern": "{brand} {model}", "models": ["Classic Tee", "Regular Jeans", "Casual Shirt"], "specs": []},
            ],
            "athletic_wear": [
                {"pattern": "{brand} {model} {spec}", "models": ["Running", "Training", "Yoga"], "specs": ["Shorts", "Leggings", "Top"]},
                {"pattern": "{brand} {model}", "models": ["Dri-FIT", "Activewear", "Sports"], "specs": []},
            ],
            
            # Home & Kitchen Templates
            "kitchen_appliances": [
                {"pattern": "{brand} {model} {spec}", "models": ["Coffee Maker", "Blender", "Air Fryer"], "specs": ["Stainless Steel", "Black", "12-Cup"]},
                {"pattern": "{brand} {model}", "models": ["Stand Mixer", "Food Processor", "Toaster"], "specs": []},
            ],
            "cookware": [
                {"pattern": "{brand} {model} {spec}", "models": ["Non-Stick", "Stainless Steel", "Cast Iron"], "specs": ["Pan", "Pot", "Set"]},
                {"pattern": "{brand} {model}", "models": ["Cookware Set", "Frying Pan", "Sauce Pan"], "specs": []},
            ],
            
            # Beauty & Personal Care
            "skincare": [
                {"pattern": "{brand} {model} {spec}", "models": ["Moisturizer", "Cleanser", "Serum"], "specs": ["Daily", "Night", "Anti-Aging"]},
                {"pattern": "{brand} {model}", "models": ["Face Cream", "Eye Cream", "Sunscreen"], "specs": []},
            ],
            
            # Default template for other categories
            "default": [
                {"pattern": "{brand} {model}", "models": ["Premium", "Classic", "Essential", "Pro"], "specs": []},
                {"pattern": "{brand} {model} {spec}", "models": ["Quality", "Standard", "Elite"], "specs": ["Black", "White", "Blue"]},
            ]
        }
    
    def generate_realistic_product(self, category: str) -> Dict[str, Any]:
        """Generate a single realistic product for the given category"""
        
        # Get category data
        category_data = self.categories_db.get_category_data(category)
        if not category_data:
            # Fallback to a random category
            category = random.choice(list(self.categories_db.categories.keys()))
            category_data = self.categories_db.get_category_data(category)
        
        # Generate product name
        product_name = self._generate_product_name(category, category_data)
        
        # Get primary material and properties
        primary_material = category_data['primary_material']
        material_data = self.materials_db.get_material_impact_score(primary_material)
        
        # Generate realistic weight within category range
        weight_range = category_data.get('weight_range', [0.1, 2.0])
        weight = round(random.uniform(weight_range[0], weight_range[1]), 2)
        
        # Calculate CO2 emissions based on material and weight
        co2_per_kg = material_data if material_data else 2.0
        base_co2 = weight * co2_per_kg
        
        # Add transport emissions
        transport_multiplier = {"air": 2.5, "ship": 1.0, "land": 1.2}
        transport = category_data.get('transport_method', 'ship')
        co2_emissions = round(base_co2 * transport_multiplier.get(transport, 1.0), 2)
        
        # Calculate eco score (inverse relationship with CO2)
        if co2_emissions < 50:
            eco_score = "A"
        elif co2_emissions < 200:
            eco_score = "B" 
        elif co2_emissions < 500:
            eco_score = "C"
        elif co2_emissions < 1000:
            eco_score = "D"
        elif co2_emissions < 2000:
            eco_score = "E"
        elif co2_emissions < 5000:
            eco_score = "F"
        else:
            eco_score = "G"
        
        # Generate origin
        origin = self._get_realistic_origin(category)
        
        # Generate secondary materials
        secondary_materials = category_data.get('common_materials', [])[1:4]
        
        # Generate packaging info
        packaging_materials = category_data.get('packaging_materials', ['cardboard', 'plastic'])
        packaging_weight_ratio = category_data.get('packaging_weight_ratio', 0.15)
        
        # Estimate volume based on weight and category
        volume = self._estimate_volume(weight, category_data.get('size_category', 'medium'))
        
        # Generate quality and other attributes
        quality_level = random.choices(
            ['budget', 'standard', 'premium', 'professional'], 
            weights=[30, 50, 15, 5]
        )[0]
        
        is_eco_labeled = random.choice([True, False]) if co2_emissions < 500 else False
        is_amazon_choice = random.choice([True, False]) if quality_level in ['standard', 'premium'] else False
        
        pack_size = random.choices([1, 2, 3, 4, 6, 12], weights=[60, 15, 10, 8, 4, 3])[0]
        
        return {
            'title': product_name,
            'material': primary_material.replace('_', ' ').title(),
            'weight': weight,
            'transport': transport.title(),
            'recyclability': category_data.get('recyclability', 'medium').title(),
            'true_eco_score': eco_score,
            'co2_emissions': co2_emissions,
            'origin': origin,
            'material_confidence': round(random.uniform(0.6, 0.95), 2),
            'secondary_materials': secondary_materials,
            'packaging_type': random.choice(['box', 'bag', 'bottle', 'tube', 'pouch']),
            'packaging_materials': str(packaging_materials).replace("'", '"'),
            'packaging_weight_ratio': round(packaging_weight_ratio, 2),
            'inferred_category': category.replace('_', ' '),
            'origin_confidence': round(random.uniform(0.65, 0.95), 2),
            'estimated_lifespan_years': category_data.get('estimated_lifespan_years', 5),
            'repairability_score': category_data.get('repairability_score', 5),
            'size_category': category_data.get('size_category', 'medium'),
            'quality_level': quality_level,
            'is_eco_labeled': is_eco_labeled,
            'is_amazon_choice': is_amazon_choice,
            'pack_size': pack_size,
            'estimated_volume_l': round(volume, 2),
            'weight_confidence': round(random.uniform(0.55, 0.85), 2)
        }
    
    def _generate_product_name(self, category: str, category_data: Dict[str, Any]) -> str:
        """Generate realistic product name based on category"""
        
        # Get templates for this category
        templates = self.product_templates.get(category, self.product_templates['default'])
        template = random.choice(templates)
        
        # Get a random brand that might sell this type of product
        suitable_brands = []
        for brand_name, brand_data in self.brands_db.amazon_brands.items():
            if any(cat.lower() in category.lower() or category.lower() in cat.lower() 
                   for cat in brand_data.get('amazon_categories', [])):
                suitable_brands.append(brand_name)
        
        if not suitable_brands:
            # Fallback to any brand
            suitable_brands = list(self.brands_db.amazon_brands.keys())
        
        brand = random.choice(suitable_brands).replace('_', ' ').title()
        
        # Generate product name
        model = random.choice(template['models']) if template['models'] else 'Classic'
        spec = random.choice(template['specs']) if template['specs'] else ''
        
        if spec:
            product_name = template['pattern'].format(brand=brand, model=model, spec=spec)
        else:
            pattern_no_spec = template['pattern'].replace(' {spec}', '')
            product_name = pattern_no_spec.format(brand=brand, model=model)
        
        return product_name
    
    def _get_realistic_origin(self, category: str) -> str:
        """Get realistic manufacturing origin based on category"""
        
        # Manufacturing patterns by category
        origin_patterns = {
            'electronics': ['China', 'South Korea', 'Taiwan', 'Japan', 'USA'],
            'clothing': ['China', 'Bangladesh', 'Vietnam', 'Turkey', 'India'],
            'home': ['China', 'Germany', 'USA', 'Italy', 'Japan'],
            'beauty': ['USA', 'France', 'Germany', 'South Korea', 'Japan'],
            'books': ['USA', 'UK', 'Germany', 'India', 'China'],
            'toys': ['China', 'USA', 'Germany', 'Denmark', 'Japan']
        }
        
        # Find best match
        for pattern_key in origin_patterns:
            if pattern_key in category.lower():
                return random.choice(origin_patterns[pattern_key])
        
        # Default distribution
        return random.choices(
            ['China', 'USA', 'Germany', 'Japan', 'UK', 'India', 'South Korea'], 
            weights=[40, 20, 10, 8, 7, 7, 8]
        )[0]
    
    def _estimate_volume(self, weight_kg: float, size_category: str) -> float:
        """Estimate volume based on weight and size category"""
        
        # Density estimates by size category (kg/L)
        density_ranges = {
            'small': (0.1, 1.2),      # Light items like clothing, books
            'medium': (0.3, 2.5),     # Electronics, kitchen items
            'large': (0.2, 1.8),      # Furniture, appliances
            'extra_large': (0.1, 0.8)  # Very large, light items
        }
        
        density_range = density_ranges.get(size_category, (0.3, 2.0))
        density = random.uniform(density_range[0], density_range[1])
        
        volume = weight_kg / density
        return max(0.01, volume)  # Minimum 0.01L
    
    def generate_products_batch(self, num_products: int) -> List[Dict[str, Any]]:
        """Generate a batch of realistic products"""
        
        print(f"🏭 Generating {num_products} realistic Amazon products...")
        
        products = []
        categories = list(self.categories_db.categories.keys())
        
        # Weight categories based on Amazon popularity
        category_weights = {
            'smartphones': 15, 'laptops': 12, 'headphones': 10,
            'casual_clothing': 25, 'athletic_wear': 15, 'shoes': 12,
            'kitchen_appliances': 8, 'cookware': 6, 'kitchen_tools': 5,
            'skincare': 10, 'haircare': 8, 'books': 6,
            'toys': 8, 'office_supplies': 5, 'pet_food': 4
        }
        
        for i in range(num_products):
            if i % 1000 == 0 and i > 0:
                print(f"  Generated {i}/{num_products} products...")
            
            # Choose category based on weights
            weighted_categories = []
            weights = []
            for cat in categories:
                weighted_categories.append(cat)
                weights.append(category_weights.get(cat, 3))
            
            category = random.choices(weighted_categories, weights=weights)[0]
            
            try:
                product = self.generate_realistic_product(category)
                products.append(product)
            except Exception as e:
                print(f"⚠️ Error generating product for {category}: {e}")
                continue
        
        print(f"✅ Generated {len(products)} products successfully")
        return products
    
    def append_to_dataset(self, new_products: List[Dict[str, Any]], output_path: str = None):
        """Append new products to the existing dataset"""
        
        if not output_path:
            output_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        
        print(f"📝 Appending {len(new_products)} products to dataset...")
        
        # Define the exact column order from the original dataset
        fieldnames = [
            'title', 'material', 'weight', 'transport', 'recyclability', 
            'true_eco_score', 'co2_emissions', 'origin', 'material_confidence',
            'secondary_materials', 'packaging_type', 'packaging_materials',
            'packaging_weight_ratio', 'inferred_category', 'origin_confidence',
            'estimated_lifespan_years', 'repairability_score', 'size_category',
            'quality_level', 'is_eco_labeled', 'is_amazon_choice', 'pack_size',
            'estimated_volume_l', 'weight_confidence'
        ]
        
        # Append to existing file
        with open(output_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            for product in new_products:
                # Format the row to match exactly
                row = {}
                for field in fieldnames:
                    value = product.get(field, '')
                    
                    # Handle list fields
                    if field == 'secondary_materials' and isinstance(value, list):
                        row[field] = str(value) if value else '[]'
                    elif field in ['is_eco_labeled', 'is_amazon_choice']:
                        row[field] = str(value)
                    else:
                        row[field] = value
                
                writer.writerow(row)
        
        print(f"✅ Successfully appended {len(new_products)} products to {output_path}")
    
    def enhance_dataset(self, target_additions: int = 10000):
        """Main method to enhance the dataset with new products"""
        
        print(f"🚀 Starting dataset enhancement with {target_additions} new products")
        print(f"📋 Using enhanced databases:")
        print(f"   • {len(self.categories_db.categories)} product categories")
        print(f"   • {len(self.materials_db.materials_database)} materials")
        print(f"   • {len(self.brands_db.amazon_brands)} brands")
        
        # Generate in batches to manage memory
        batch_size = 2000
        total_generated = 0
        
        while total_generated < target_additions:
            current_batch_size = min(batch_size, target_additions - total_generated)
            
            print(f"\n🔄 Batch {total_generated//batch_size + 1}: Generating {current_batch_size} products...")
            
            batch_products = self.generate_products_batch(current_batch_size)
            
            if batch_products:
                self.append_to_dataset(batch_products)
                total_generated += len(batch_products)
                print(f"✅ Total products generated so far: {total_generated}/{target_additions}")
            else:
                print("❌ Failed to generate products in this batch")
                break
        
        print(f"\n🎉 Dataset enhancement complete!")
        print(f"📊 Added {total_generated} new products")
        
        # Verify final count
        final_count_cmd = f"wc -l {os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')}"
        return total_generated

if __name__ == "__main__":
    enhancer = EcoDatasetEnhancer()
    enhancer.enhance_dataset(target_additions=15000)  # Add 15,000 products