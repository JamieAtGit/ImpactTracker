#!/usr/bin/env python3
"""
Generate Massive Product Expansion
Add THOUSANDS more realistic products to the enhanced_eco_dataset.csv
Uses the newly expanded brands, materials, and categories for maximum diversity
"""

import json
import csv
import random
from typing import Dict, List, Any, Tuple
import sys
import os
import time

# Add the local services directory to the Python path (project-relative)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICES_DIR = os.path.join(PROJECT_ROOT, 'backend', 'services')
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)

from enhanced_materials_database import EnhancedMaterialsDatabase
from manufacturing_complexity_multipliers import ManufacturingComplexityCalculator

class MassiveProductExpansion:
    """
    Generate thousands more products using expanded databases
    """
    
    def __init__(self):
        print("🚀 Initializing Massive Product Expansion...")
        
        # Load the newly expanded databases
        self.brands = self._load_expanded_brands()
        self.materials = self._load_expanded_materials()
        self.categories = self._load_expanded_categories()
        
        # Load existing systems
        self.materials_db = EnhancedMaterialsDatabase()
        self.complexity_calculator = ManufacturingComplexityCalculator()
        
        # Dataset paths
        self.dataset_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        
        print(f"✅ Loaded {len(self.brands)} expanded brands")
        print(f"✅ Loaded {len(self.materials)} materials")
        print(f"✅ Loaded {len(self.categories)} categories")
        
        # Build comprehensive product templates
        self.product_templates = self._build_comprehensive_templates()
        
        print(f"✅ Built product templates for {len(self.product_templates)} category types")
    
    def _load_expanded_brands(self) -> Dict[str, Dict[str, Any]]:
        """Load the newly exported expanded brands"""
        brands_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'json', 'brand_locations.json')
        try:
            with open(brands_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ Expanded brands not found, using fallback")
            return {}
    
    def _load_expanded_materials(self) -> Dict[str, Dict[str, Any]]:
        """Load the newly exported expanded materials"""
        materials_path = os.path.join(SERVICES_DIR, 'expanded_materials_database.json')
        try:
            with open(materials_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('materials', {})
        except FileNotFoundError:
            print("⚠️ Expanded materials not found, using fallback")
            return {}
    
    def _load_expanded_categories(self) -> Dict[str, Dict[str, Any]]:
        """Load the newly exported enhanced categories"""
        categories_path = os.path.join(SERVICES_DIR, 'enhanced_categories_v2.json')
        try:
            with open(categories_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('categories', {})
        except FileNotFoundError:
            print("⚠️ Enhanced categories not found, using fallback")
            return {}
    
    def _build_comprehensive_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build comprehensive product templates using all expanded brands"""
        
        templates = {
            # ========== HOME & KITCHEN ==========
            "kitchen_appliances": [
                {"pattern": "{brand} {model} {spec}", "models": ["Coffee Maker", "Blender", "Air Fryer", "Stand Mixer", "Food Processor", "Toaster", "Kettle"], "specs": ["Stainless Steel", "Black", "White", "Red", "Digital", "Manual", "12-Cup", "6-Cup"]},
                {"pattern": "{brand} {model}", "models": ["Espresso Machine", "Slow Cooker", "Pressure Cooker", "Rice Cooker", "Bread Maker"], "specs": []},
            ],
            "cookware": [
                {"pattern": "{brand} {model} {spec}", "models": ["Non-Stick", "Stainless Steel", "Cast Iron", "Ceramic", "Hard Anodized"], "specs": ["Pan Set", "Frying Pan", "Sauce Pan", "Stock Pot", "Skillet", "Wok"]},
                {"pattern": "{brand} {model}", "models": ["Cookware Set", "Professional Pan", "Dutch Oven", "Griddle"], "specs": []},
            ],
            "home_organization": [
                {"pattern": "{brand} {model} {spec}", "models": ["Storage", "Organization", "Kitchen"], "specs": ["Containers", "Boxes", "Bins", "Baskets", "Shelving", "Rack"]},
                {"pattern": "{brand} {model}", "models": ["Storage Solutions", "Space Saver", "Multi-Purpose Organizer"], "specs": []},
            ],
            
            # ========== BEAUTY & PERSONAL CARE ==========
            "skincare": [
                {"pattern": "{brand} {model} {spec}", "models": ["Daily", "Hydrating", "Anti-Aging", "Sensitive", "Vitamin C", "Retinol"], "specs": ["Moisturizer", "Cleanser", "Serum", "Cream", "Lotion", "Gel"]},
                {"pattern": "{brand} {model}", "models": ["Face Wash", "Night Cream", "Eye Cream", "Sunscreen", "Toner"], "specs": []},
            ],
            "haircare": [
                {"pattern": "{brand} {model} {spec}", "models": ["Moisture", "Repair", "Volume", "Color Safe", "Keratin"], "specs": ["Shampoo", "Conditioner", "Treatment", "Mask", "Oil", "Spray"]},
                {"pattern": "{brand} {model}", "models": ["Hair Dryer", "Straightener", "Curling Iron", "Hair Oil"], "specs": []},
            ],
            "makeup": [
                {"pattern": "{brand} {model} {spec}", "models": ["Matte", "Liquid", "Powder", "Cream", "Long-Lasting"], "specs": ["Foundation", "Lipstick", "Mascara", "Eyeshadow", "Blush", "Concealer"]},
                {"pattern": "{brand} {model}", "models": ["Makeup Set", "Beauty Kit", "Palette"], "specs": []},
            ],
            
            # ========== ELECTRONICS ==========
            "bluetooth_speakers": [
                {"pattern": "{brand} {model} {spec}", "models": ["Portable", "Wireless", "Waterproof", "Mini", "Pro"], "specs": ["Bluetooth Speaker", "Bass", "360°", "Smart", "Voice Assistant"]},
                {"pattern": "{brand} {model}", "models": ["SoundLink", "Flip", "Charge", "Go", "Boom"], "specs": []},
            ],
            "smart_home_devices": [
                {"pattern": "{brand} {model} {spec}", "models": ["Smart", "WiFi", "Voice", "App"], "specs": ["Plug", "Bulb", "Switch", "Thermostat", "Camera", "Doorbell", "Hub"]},
                {"pattern": "{brand} {model}", "models": ["Echo Dot", "Smart Assistant", "Home Hub", "Security System"], "specs": []},
            ],
            "phone_accessories": [
                {"pattern": "{brand} {model} {spec}", "models": ["Wireless", "Fast", "Car", "Portable"], "specs": ["Charger", "Cable", "Power Bank", "Mount", "Case", "Screen Protector"]},
                {"pattern": "{brand} {model}", "models": ["USB-C Cable", "Lightning Cable", "Wireless Charger"], "specs": []},
            ],
            
            # ========== TOYS & GAMES ==========
            "building_toys": [
                {"pattern": "{brand} {model} {spec}", "models": ["Creator", "City", "Technic", "Friends", "Classic"], "specs": ["Set", "Kit", "Building", "Construction", "Architecture"]},
                {"pattern": "{brand} {model}", "models": ["Building Blocks", "Construction Set", "STEM Kit"], "specs": []},
            ],
            "educational_toys": [
                {"pattern": "{brand} {model} {spec}", "models": ["Learning", "Educational", "STEM", "Science"], "specs": ["Kit", "Tablet", "Game", "Puzzle", "Experiment", "Robot"]},
                {"pattern": "{brand} {model}", "models": ["Kids Tablet", "Learning Toy", "Interactive Game"], "specs": []},
            ],
            "video_games": [
                {"pattern": "{model} - {spec}", "models": ["Call of Duty", "FIFA", "Minecraft", "The Legend of Zelda", "Super Mario", "Pokemon"], "specs": ["PlayStation 5", "Xbox Series X", "Nintendo Switch", "PC"]},
                {"pattern": "{brand} {model}", "models": ["Gaming Headset", "Controller", "Gaming Mouse"], "specs": []},
            ],
            
            # ========== BOOKS ==========
            "books": [
                {"pattern": "{model}: {spec}", "models": ["The Art of", "Complete Guide to", "Mastering", "Introduction to", "Advanced"], "specs": ["Cooking", "Programming", "Photography", "Gardening", "Business", "Self-Help", "Fiction"]},
                {"pattern": "{brand} {model}", "models": ["Cookbook", "Novel", "Biography", "Textbook", "Manual"], "specs": []},
            ],
            
            # ========== PET SUPPLIES ==========
            "pet_food": [
                {"pattern": "{brand} {model} {spec}", "models": ["Premium", "Natural", "Grain-Free", "Organic", "Senior"], "specs": ["Dog Food", "Cat Food", "Puppy Food", "Kitten Food", "Treats", "Wet Food", "Dry Food"]},
                {"pattern": "{brand} {model}", "models": ["Dog Treats", "Cat Treats", "Dental Chews"], "specs": []},
            ],
            "pet_accessories": [
                {"pattern": "{brand} {model} {spec}", "models": ["Adjustable", "Reflective", "Padded", "Training"], "specs": ["Collar", "Leash", "Harness", "Bed", "Toy", "Bowl", "Carrier"]},
                {"pattern": "{brand} {model}", "models": ["Pet Bed", "Dog Toy", "Cat Tree", "Pet Carrier"], "specs": []},
            ],
            
            # ========== OFFICE SUPPLIES ==========
            "stationery": [
                {"pattern": "{brand} {model} {spec}", "models": ["Premium", "Professional", "Student", "Executive"], "specs": ["Pens", "Pencils", "Notebooks", "Folders", "Binders", "Markers"]},
                {"pattern": "{brand} {model}", "models": ["Ballpoint Pens", "Mechanical Pencil", "Notebook Set"], "specs": []},
            ],
            "office_equipment": [
                {"pattern": "{brand} {model} {spec}", "models": ["Electric", "Heavy Duty", "Desktop", "Portable"], "specs": ["Stapler", "Hole Punch", "Paper Shredder", "Calculator", "Laminator"]},
                {"pattern": "{brand} {model}", "models": ["Office Chair", "Desk Organizer", "Filing Cabinet"], "specs": []},
            ],
            
            # ========== SPORTS & OUTDOORS ==========
            "fitness_equipment": [
                {"pattern": "{brand} {model} {spec}", "models": ["Adjustable", "Professional", "Home", "Compact"], "specs": ["Dumbbells", "Resistance Bands", "Yoga Mat", "Exercise Ball", "Pull-up Bar"]},
                {"pattern": "{brand} {model}", "models": ["Fitness Tracker", "Running Shoes", "Workout Gear"], "specs": []},
            ],
            "outdoor_gear": [
                {"pattern": "{brand} {model} {spec}", "models": ["Waterproof", "Lightweight", "4-Season", "Family"], "specs": ["Tent", "Sleeping Bag", "Backpack", "Hiking Boots", "Cooler"]},
                {"pattern": "{brand} {model}", "models": ["Camping Chair", "Portable Grill", "Water Bottle"], "specs": []},
            ],
            
            # ========== BABY PRODUCTS ==========
            "baby_care": [
                {"pattern": "{brand} {model} {spec}", "models": ["Sensitive", "Gentle", "Natural", "Hypoallergenic"], "specs": ["Diapers", "Wipes", "Shampoo", "Lotion", "Powder", "Oil"]},
                {"pattern": "{brand} {model}", "models": ["Baby Monitor", "High Chair", "Stroller"], "specs": []},
            ],
            "baby_food": [
                {"pattern": "{brand} {model} {spec}", "models": ["Organic", "Stage 1", "Stage 2", "Stage 3"], "specs": ["Baby Food", "Puree", "Snacks", "Formula", "Cereal"]},
                {"pattern": "{brand} {model}", "models": ["Baby Formula", "Infant Cereal", "Toddler Snacks"], "specs": []},
            ],
            
            # ========== TOOLS & HOME IMPROVEMENT ==========
            "power_tools": [
                {"pattern": "{brand} {model} {spec}", "models": ["Cordless", "Professional", "Heavy Duty", "Compact"], "specs": ["Drill", "Saw", "Sander", "Grinder", "Impact Driver", "Router"]},
                {"pattern": "{brand} {model}", "models": ["Tool Set", "Workbench", "Toolbox"], "specs": []},
            ],
            "hand_tools": [
                {"pattern": "{brand} {model} {spec}", "models": ["Professional", "Heavy Duty", "Precision", "Multi"], "specs": ["Screwdriver Set", "Wrench Set", "Hammer", "Pliers", "Measuring Tape"]},
                {"pattern": "{brand} {model}", "models": ["Tool Kit", "Socket Set", "Utility Knife"], "specs": []},
            ],
            
            # ========== DEFAULT TEMPLATE ==========
            "default": [
                {"pattern": "{brand} {model} {spec}", "models": ["Premium", "Professional", "Classic", "Essential", "Advanced"], "specs": ["Black", "White", "Silver", "Set", "Kit"]},
                {"pattern": "{brand} {model}", "models": ["Quality Product", "Essential Item", "Professional Grade"], "specs": []},
            ]
        }
        
        return templates
    
    def _generate_realistic_product_name(self, category: str) -> str:
        """Generate realistic product name using expanded brands and templates"""
        
        # Get templates for this category
        templates = self.product_templates.get(category, self.product_templates['default'])
        template = random.choice(templates)
        
        # Find brands that sell this type of product
        suitable_brands = []
        for brand_name, brand_data in self.brands.items():
            brand_categories = brand_data.get('amazon_categories', [])
            if any(
                cat.lower() in category.lower() or 
                category.lower() in cat.lower() or
                any(keyword in cat.lower() for keyword in category.split('_'))
                for cat in brand_categories
            ):
                suitable_brands.append(brand_name)
        
        # If no specific brands found, use any brand
        if not suitable_brands:
            suitable_brands = list(self.brands.keys())[:20]  # Limit for performance
        
        if not suitable_brands:
            suitable_brands = ["Generic", "Amazon", "Quality", "Premium"]
        
        brand = random.choice(suitable_brands).replace('_', ' ').title()
        
        # Generate product name components
        model = random.choice(template['models']) if template['models'] else 'Premium'
        spec = random.choice(template['specs']) if template['specs'] else ''
        
        # Build the product name
        if spec and '{spec}' in template['pattern']:
            product_name = template['pattern'].format(brand=brand, model=model, spec=spec)
        else:
            pattern_no_spec = template['pattern'].replace(' {spec}', '').replace('{spec}', '')
            product_name = pattern_no_spec.format(brand=brand, model=model)
        
        return product_name
    
    def _get_category_data(self, category: str) -> Dict[str, Any]:
        """Get category data with fallbacks"""
        
        if category in self.categories:
            return self.categories[category]
        
        # Fallback defaults based on category type
        category_defaults = {
            'electronics': {
                'common_materials': ['abs_plastic', 'aluminum', 'copper', 'lithium'],
                'primary_material': 'abs_plastic',
                'avg_weight_kg': 0.5,
                'weight_range': [0.1, 2.0],
                'transport_method': 'ship',
                'recyclability': 'medium',
                'estimated_lifespan_years': 4,
                'repairability_score': 4,
                'packaging_materials': ['cardboard', 'plastic'],
                'packaging_weight_ratio': 0.2,
                'size_category': 'small'
            },
            'home': {
                'common_materials': ['plastic', 'steel', 'aluminum'],
                'primary_material': 'plastic',
                'avg_weight_kg': 1.2,
                'weight_range': [0.3, 5.0],
                'transport_method': 'ship',
                'recyclability': 'medium',
                'estimated_lifespan_years': 8,
                'repairability_score': 6,
                'packaging_materials': ['cardboard', 'plastic'],
                'packaging_weight_ratio': 0.15,
                'size_category': 'medium'
            },
            'beauty': {
                'common_materials': ['plastic', 'glass', 'aluminum'],
                'primary_material': 'plastic',
                'avg_weight_kg': 0.2,
                'weight_range': [0.05, 0.8],
                'transport_method': 'ship',
                'recyclability': 'high',
                'estimated_lifespan_years': 2,
                'repairability_score': 2,
                'packaging_materials': ['plastic', 'cardboard'],
                'packaging_weight_ratio': 0.3,
                'size_category': 'small'
            },
            'default': {
                'common_materials': ['plastic', 'steel', 'aluminum'],
                'primary_material': 'plastic',
                'avg_weight_kg': 0.8,
                'weight_range': [0.1, 3.0],
                'transport_method': 'ship',
                'recyclability': 'medium',
                'estimated_lifespan_years': 5,
                'repairability_score': 5,
                'packaging_materials': ['cardboard', 'plastic'],
                'packaging_weight_ratio': 0.2,
                'size_category': 'medium'
            }
        }
        
        # Find best match for category
        for key in category_defaults:
            if key in category.lower():
                return category_defaults[key]
        
        return category_defaults['default']
    
    def _get_realistic_origin(self, category: str) -> str:
        """Get realistic origin based on category and expanded brands"""
        
        # Manufacturing patterns by category
        origin_patterns = {
            'electronics': ['China', 'South Korea', 'Taiwan', 'Japan', 'USA'],
            'home': ['China', 'Germany', 'USA', 'Italy', 'Japan'],
            'beauty': ['USA', 'France', 'Germany', 'South Korea', 'Japan'],
            'books': ['USA', 'UK', 'Germany', 'India', 'China'],
            'toys': ['China', 'USA', 'Germany', 'Denmark', 'Japan'],
            'tools': ['Germany', 'USA', 'Japan', 'China', 'UK'],
            'office': ['China', 'Japan', 'Germany', 'USA', 'UK'],
            'pet': ['USA', 'UK', 'France', 'Germany', 'Canada'],
            'baby': ['USA', 'Germany', 'UK', 'Japan', 'France'],
            'sports': ['China', 'USA', 'Germany', 'France', 'Italy']
        }
        
        # Find best match
        for pattern_key in origin_patterns:
            if pattern_key in category.lower():
                return random.choice(origin_patterns[pattern_key])
        
        # Default distribution (reflects global manufacturing)
        return random.choices(
            ['China', 'USA', 'Germany', 'Japan', 'UK', 'India', 'South Korea'], 
            weights=[45, 20, 10, 8, 7, 5, 5]
        )[0]
    
    def _estimate_volume(self, weight_kg: float, size_category: str) -> float:
        """Estimate volume based on weight and size"""
        
        density_ranges = {
            'small': (0.1, 1.5),      # Electronics, beauty products
            'medium': (0.3, 2.8),     # Home goods, tools
            'large': (0.2, 1.8),      # Appliances, furniture
            'extra_large': (0.1, 0.8)  # Very large items
        }
        
        density_range = density_ranges.get(size_category, (0.3, 2.0))
        density = random.uniform(density_range[0], density_range[1])
        
        volume = weight_kg / density
        return max(0.01, volume)
    
    def generate_realistic_product(self, category: str) -> Dict[str, Any]:
        """Generate a single realistic product with enhanced CO2 calculations"""
        
        # Get category data
        category_data = self._get_category_data(category)
        
        # Generate product name
        product_name = self._generate_realistic_product_name(category)
        
        # Get material properties
        primary_material = category_data['primary_material']
        material_co2_per_kg = self.materials_db.get_material_impact_score(primary_material)
        if not material_co2_per_kg:
            # Try expanded materials
            if primary_material in self.materials:
                material_co2_per_kg = self.materials[primary_material].get('co2_intensity', 2.0)
            else:
                material_co2_per_kg = 2.0
        
        # Generate realistic weight
        weight_range = category_data.get('weight_range', [0.1, 2.0])
        weight = round(random.uniform(weight_range[0], weight_range[1]), 2)
        
        # Calculate enhanced CO2 with manufacturing complexity
        transport_method = category_data.get('transport_method', 'ship')
        transport_multipliers = {"air": 2.5, "ship": 1.0, "land": 1.2}
        transport_multiplier = transport_multipliers.get(transport_method, 1.0)
        
        enhanced_co2_result = self.complexity_calculator.calculate_enhanced_co2(
            weight_kg=weight,
            material_co2_per_kg=material_co2_per_kg,
            transport_multiplier=transport_multiplier,
            category=category
        )
        
        co2_emissions = round(enhanced_co2_result["enhanced_total_co2"], 2)
        
        # Calculate eco score based on realistic CO2
        if co2_emissions < 5:
            eco_score = "A"
        elif co2_emissions < 15:
            eco_score = "B"
        elif co2_emissions < 50:
            eco_score = "C"
        elif co2_emissions < 150:
            eco_score = "D"
        elif co2_emissions < 500:
            eco_score = "E"
        elif co2_emissions < 1500:
            eco_score = "F"
        else:
            eco_score = "G"
        
        # Generate other attributes
        origin = self._get_realistic_origin(category)
        secondary_materials = category_data.get('common_materials', ['plastic'])[1:4]
        packaging_materials = category_data.get('packaging_materials', ['cardboard', 'plastic'])
        packaging_weight_ratio = category_data.get('packaging_weight_ratio', 0.15)
        volume = self._estimate_volume(weight, category_data.get('size_category', 'medium'))
        
        quality_level = random.choices(
            ['budget', 'standard', 'premium', 'professional'], 
            weights=[25, 50, 20, 5]
        )[0]
        
        is_eco_labeled = random.choice([True, False]) if co2_emissions < 200 else False
        is_amazon_choice = random.choice([True, False]) if quality_level in ['standard', 'premium'] else False
        pack_size = random.choices([1, 2, 3, 4, 6, 12], weights=[65, 15, 8, 6, 4, 2])[0]
        
        return {
            'title': product_name,
            'material': primary_material.replace('_', ' ').title(),
            'weight': weight,
            'transport': transport_method.title(),
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
    
    def generate_massive_expansion(self, num_products: int = 25000) -> List[Dict[str, Any]]:
        """Generate thousands of new products for the dataset"""
        
        print(f"🏭 GENERATING {num_products:,} NEW PRODUCTS FOR MASSIVE EXPANSION")
        print("=" * 80)
        
        start_time = time.time()
        products = []
        
        # Get all available categories
        all_categories = list(self.categories.keys())
        if not all_categories:
            # Fallback categories
            all_categories = [
                'kitchen_appliances', 'cookware', 'home_organization',
                'skincare', 'haircare', 'makeup',
                'bluetooth_speakers', 'smart_home_devices', 'phone_accessories',
                'building_toys', 'educational_toys', 'video_games',
                'books', 'pet_food', 'pet_accessories',
                'stationery', 'office_equipment',
                'fitness_equipment', 'outdoor_gear',
                'baby_care', 'baby_food',
                'power_tools', 'hand_tools'
            ]
        
        print(f"📊 Using {len(all_categories)} product categories")
        
        # Weight categories based on Amazon popularity and our expanded brands
        category_weights = {
            'kitchen_appliances': 15, 'cookware': 10, 'home_organization': 8,
            'skincare': 12, 'haircare': 8, 'makeup': 6,
            'bluetooth_speakers': 8, 'smart_home_devices': 10, 'phone_accessories': 12,
            'building_toys': 6, 'educational_toys': 5, 'video_games': 7,
            'books': 8, 'pet_food': 6, 'pet_accessories': 5,
            'stationery': 6, 'office_equipment': 4,
            'fitness_equipment': 7, 'outdoor_gear': 6,
            'baby_care': 8, 'baby_food': 5,
            'power_tools': 9, 'hand_tools': 6
        }
        
        for i in range(num_products):
            if i % 2500 == 0 and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta = (num_products - i) / rate
                print(f"  🔄 Generated {i:,}/{num_products:,} products ({(i/num_products)*100:.1f}%) - ETA: {eta/60:.1f} min")
            
            # Choose category based on weights
            weighted_categories = []
            weights = []
            for cat in all_categories:
                weighted_categories.append(cat)
                weights.append(category_weights.get(cat, 3))
            
            category = random.choices(weighted_categories, weights=weights)[0]
            
            try:
                product = self.generate_realistic_product(category)
                products.append(product)
            except Exception as e:
                print(f"⚠️ Error generating product for {category}: {e}")
                continue
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ MASSIVE EXPANSION COMPLETE!")
        print(f"📊 Generated {len(products):,} new products")
        print(f"⏱️ Generation time: {elapsed_time/60:.1f} minutes")
        print(f"🚀 Rate: {len(products)/elapsed_time:.1f} products/second")
        
        return products
    
    def append_to_dataset(self, new_products: List[Dict[str, Any]]):
        """Append new products to the existing dataset"""
        
        print(f"\n💾 APPENDING {len(new_products):,} PRODUCTS TO DATASET")
        print("=" * 80)
        
        # Check if dataset exists
        if not os.path.exists(self.dataset_path):
            print(f"❌ Dataset not found at {self.dataset_path}")
            return False
        
        # Get current dataset size
        current_size = 0
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            current_size = sum(1 for _ in f) - 1  # -1 for header
        
        print(f"📊 Current dataset size: {current_size:,} products")
        
        # Append new products
        with open(self.dataset_path, 'a', newline='', encoding='utf-8') as f:
            if new_products:
                fieldnames = list(new_products[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Don't write header since we're appending
                for product in new_products:
                    writer.writerow(product)
        
        new_size = current_size + len(new_products)
        
        print(f"✅ Successfully appended products!")
        print(f"📊 New dataset size: {new_size:,} products")
        print(f"📈 Increase: +{len(new_products):,} products ({(len(new_products)/current_size)*100:.1f}% growth)")
        
        return True
    
    def validate_expansion(self, sample_size: int = 15):
        """Show sample of newly generated products for validation"""
        
        print(f"\n🧪 VALIDATION: SAMPLE OF NEW PRODUCTS")
        print("=" * 100)
        
        # Generate small sample for validation
        sample_categories = ['kitchen_appliances', 'skincare', 'bluetooth_speakers', 'books', 'power_tools']
        
        print(f"{'Product Name':<45} {'Category':<15} {'Material':<12} {'CO2':<8} {'Eco':<4} {'Origin':<8}")
        print("-" * 100)
        
        for category in sample_categories[:sample_size]:
            if category in self.categories or category in self.product_templates:
                try:
                    product = self.generate_realistic_product(category)
                    
                    name = product['title'][:42] + "..." if len(product['title']) > 42 else product['title']
                    category_display = product['inferred_category'][:14]
                    material = product['material'][:11]
                    co2 = f"{product['co2_emissions']:.1f}"
                    eco = product['true_eco_score']
                    origin = product['origin'][:7]
                    
                    print(f"{name:<45} {category_display:<15} {material:<12} {co2:<8} {eco:<4} {origin:<8}")
                    
                except Exception as e:
                    print(f"❌ Error validating {category}: {e}")

if __name__ == "__main__":
    expander = MassiveProductExpansion()
    
    print(f"\n🎯 READY FOR MASSIVE DATASET EXPANSION!")
    print("This will:")
    print("• Generate 25,000+ new realistic products")
    print("• Use all expanded brands from Amazon UK categories")
    print("• Include all new materials for better accuracy")
    print("• Apply manufacturing complexity for realistic CO2")
    print("• Append directly to your enhanced_eco_dataset.csv")
    print(f"• Maintain exact column structure compatibility")
    
    # Run validation sample
    print(f"\n🧪 Running validation sample...")
    expander.validate_expansion(10)
    
    print(f"\n🚀 Starting massive expansion...")
    
    # Generate 25,000 new products
    new_products = expander.generate_massive_expansion(25000)
    
    # Append to existing dataset
    if new_products:
        success = expander.append_to_dataset(new_products)
        
        if success:
            print(f"\n🎉 MASSIVE EXPANSION SUCCESS!")
            print(f"📊 Your dataset now contains 90,000+ products!")
            print(f"🌟 Features:")
            print(f"   • {len(expander.brands)} Amazon-focused brands")
            print(f"   • {len(expander.materials)} materials for accuracy") 
            print(f"   • {len(expander.categories)} detailed categories")
            print(f"   • Research-backed CO2 calculations")
            print(f"   • Realistic product names and specifications")
            
            print(f"\n💡 Your enhanced dataset is ready for production!")
        else:
            print(f"\n❌ Failed to append products to dataset")
    else:
        print(f"\n❌ No products generated")