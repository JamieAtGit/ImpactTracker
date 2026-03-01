#!/usr/bin/env python3
"""
Amazon Product Categories System
Comprehensive taxonomy based on actual Amazon UK categories and products
Maps to materials, typical weights, transport methods, and sustainability factors
"""

import json
from typing import Dict, List, Any, Tuple

class AmazonProductCategories:
    """
    Comprehensive Amazon UK product categories with sustainability data
    Based on actual Amazon taxonomy and product characteristics
    """
    
    def __init__(self):
        self.categories = self.build_amazon_categories()
        self.category_hierarchy = self.build_category_hierarchy()
    
    def build_amazon_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Build comprehensive Amazon categories with sustainability data
        Each category includes: materials, weight ranges, transport, recyclability, lifespan
        """
        
        return {
            
            # ========== ELECTRONICS & COMPUTERS ==========
            
            "smartphones": {
                "description": "Mobile phones and accessories",
                "common_materials": ["aluminum", "glass", "lithium", "copper", "rare_earth_elements"],
                "primary_material": "aluminum",
                "avg_weight_kg": 0.2,
                "weight_range": [0.1, 0.4],
                "transport_method": "air",
                "recyclability": "medium",
                "estimated_lifespan_years": 3,
                "repairability_score": 4,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.15,
                "size_category": "small",
                "amazon_examples": ["iPhone", "Samsung Galaxy", "Google Pixel", "OnePlus"]
            },
            
            "laptops": {
                "description": "Portable computers and ultrabooks",
                "common_materials": ["aluminum", "abs_plastic", "lithium", "copper", "silicon"],
                "primary_material": "aluminum",
                "avg_weight_kg": 1.8,
                "weight_range": [0.9, 3.5],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 5,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "foam_padding"],
                "packaging_weight_ratio": 0.25,
                "size_category": "medium",
                "amazon_examples": ["MacBook", "ThinkPad", "Dell XPS", "Surface"]
            },
            
            "tablets": {
                "description": "Tablet computers and e-readers",
                "common_materials": ["aluminum", "glass", "lithium", "silicon"],
                "primary_material": "aluminum",
                "avg_weight_kg": 0.5,
                "weight_range": [0.3, 0.8],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 4,
                "repairability_score": 2,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.2,
                "size_category": "small",
                "amazon_examples": ["iPad", "Kindle", "Samsung Tab", "Surface"]
            },
            
            "headphones": {
                "description": "Audio equipment and earphones",
                "common_materials": ["abs_plastic", "aluminum", "copper", "silicone"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 0.3,
                "weight_range": [0.05, 0.8],
                "transport_method": "ship",
                "recyclability": "low",
                "estimated_lifespan_years": 3,
                "repairability_score": 2,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.3,
                "size_category": "small",
                "amazon_examples": ["AirPods", "Sony WH-1000XM5", "Bose QC", "JBL"]
            },
            
            "computer_accessories": {
                "description": "Keyboards, mice, webcams, cables",
                "common_materials": ["abs_plastic", "copper", "aluminum"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 0.4,
                "weight_range": [0.05, 1.5],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 4,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.25,
                "size_category": "small",
                "amazon_examples": ["Logitech mouse", "Mechanical keyboard", "Webcam", "USB cables"]
            },
            
            "gaming_equipment": {
                "description": "Gaming consoles, controllers, accessories",
                "common_materials": ["abs_plastic", "aluminum", "lithium", "copper"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 1.2,
                "weight_range": [0.2, 4.5],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 6,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "foam_padding"],
                "packaging_weight_ratio": 0.3,
                "size_category": "medium",
                "amazon_examples": ["PlayStation", "Xbox", "Nintendo Switch", "Gaming headset"]
            },
            
            "cameras": {
                "description": "Digital cameras and photography equipment",
                "common_materials": ["aluminum", "glass", "abs_plastic", "lithium"],
                "primary_material": "aluminum",
                "avg_weight_kg": 0.8,
                "weight_range": [0.3, 2.5],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 7,
                "repairability_score": 4,
                "packaging_materials": ["cardboard", "foam_padding"],
                "packaging_weight_ratio": 0.35,
                "size_category": "medium",
                "amazon_examples": ["Canon DSLR", "Sony mirrorless", "GoPro", "Fujifilm"]
            },
            
            # ========== HOME & KITCHEN ==========
            
            "kitchen_appliances": {
                "description": "Small kitchen appliances and gadgets",
                "common_materials": ["stainless_steel", "abs_plastic", "aluminum"],
                "primary_material": "stainless_steel",
                "avg_weight_kg": 2.5,
                "weight_range": [0.5, 8.0],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 8,
                "repairability_score": 5,
                "packaging_materials": ["cardboard", "foam_padding"],
                "packaging_weight_ratio": 0.2,
                "size_category": "medium",
                "amazon_examples": ["KitchenAid mixer", "Ninja blender", "Coffee maker", "Air fryer"]
            },
            
            "cookware": {
                "description": "Pots, pans, and cooking utensils",
                "common_materials": ["stainless_steel", "aluminum", "cast_iron", "ceramic"],
                "primary_material": "stainless_steel",
                "avg_weight_kg": 1.8,
                "weight_range": [0.2, 5.0],
                "transport_method": "ship",
                "recyclability": "very_high",
                "estimated_lifespan_years": 15,
                "repairability_score": 8,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.1,
                "size_category": "medium",
                "amazon_examples": ["Le Creuset", "All-Clad", "Lodge cast iron", "Ceramic bowls"]
            },
            
            "kitchen_tools": {
                "description": "Utensils, gadgets, and small tools",
                "common_materials": ["stainless_steel", "wood", "silicone", "abs_plastic"],
                "primary_material": "stainless_steel",
                "avg_weight_kg": 0.3,
                "weight_range": [0.05, 1.0],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 10,
                "repairability_score": 7,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.15,
                "size_category": "small",
                "amazon_examples": ["OXO tools", "Bamboo cutting board", "Silicone spatula", "Knives"]
            },
            
            "home_decor": {
                "description": "Decorative items and home accessories",
                "common_materials": ["ceramic", "wood", "glass", "cotton"],
                "primary_material": "ceramic",
                "avg_weight_kg": 1.2,
                "weight_range": [0.1, 5.0],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 10,
                "repairability_score": 2,
                "packaging_materials": ["cardboard", "bubble_wrap"],
                "packaging_weight_ratio": 0.25,
                "size_category": "medium",
                "amazon_examples": ["Vases", "Picture frames", "Candles", "Throw pillows"]
            },
            
            "furniture": {
                "description": "Home and office furniture",
                "common_materials": ["wood", "steel", "polyester", "foam_padding"],
                "primary_material": "wood",
                "avg_weight_kg": 25.0,
                "weight_range": [2.0, 80.0],
                "transport_method": "land",
                "recyclability": "medium",
                "estimated_lifespan_years": 12,
                "repairability_score": 6,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.08,
                "size_category": "extra_large",
                "amazon_examples": ["Office chair", "Bookshelf", "Dining table", "Sofa"]
            },
            
            # ========== CLOTHING & FASHION ==========
            
            "casual_clothing": {
                "description": "Everyday shirts, pants, and casual wear",
                "common_materials": ["cotton", "polyester", "spandex"],
                "primary_material": "cotton",
                "avg_weight_kg": 0.4,
                "weight_range": [0.1, 1.2],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 3,
                "repairability_score": 4,
                "packaging_materials": ["plastic", "cardboard"],
                "packaging_weight_ratio": 0.05,
                "size_category": "small",
                "amazon_examples": ["T-shirts", "Jeans", "Hoodies", "Casual pants"]
            },
            
            "athletic_wear": {
                "description": "Sports and fitness clothing",
                "common_materials": ["polyester", "nylon", "spandex"],
                "primary_material": "polyester",
                "avg_weight_kg": 0.3,
                "weight_range": [0.08, 0.8],
                "transport_method": "ship",
                "recyclability": "low",
                "estimated_lifespan_years": 2,
                "repairability_score": 3,
                "packaging_materials": ["plastic"],
                "packaging_weight_ratio": 0.03,
                "size_category": "small",
                "amazon_examples": ["Nike running shirt", "Adidas leggings", "Under Armour shorts"]
            },
            
            "shoes": {
                "description": "Footwear for all occasions",
                "common_materials": ["polyester", "rubber", "eva_foam", "leather"],
                "primary_material": "polyester",
                "avg_weight_kg": 0.8,
                "weight_range": [0.3, 1.5],
                "transport_method": "ship",
                "recyclability": "low",
                "estimated_lifespan_years": 2,
                "repairability_score": 2,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.15,
                "size_category": "small",
                "amazon_examples": ["Nike sneakers", "Dress shoes", "Boots", "Sandals"]
            },
            
            "accessories": {
                "description": "Bags, belts, jewelry, and fashion accessories",
                "common_materials": ["polyester", "aluminum", "steel", "leather"],
                "primary_material": "polyester",
                "avg_weight_kg": 0.6,
                "weight_range": [0.05, 2.0],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 4,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.2,
                "size_category": "small",
                "amazon_examples": ["Handbags", "Watches", "Jewelry", "Belts"]
            },
            
            # ========== BEAUTY & PERSONAL CARE ==========
            
            "skincare": {
                "description": "Facial and body care products", 
                "common_materials": ["hdpe", "pet", "pp", "palm_oil"],
                "primary_material": "hdpe",
                "avg_weight_kg": 0.2,
                "weight_range": [0.05, 0.8],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 1,
                "repairability_score": 1,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.12,
                "size_category": "small",
                "amazon_examples": ["Moisturizer", "Cleanser", "Sunscreen", "Serum"]
            },
            
            "haircare": {
                "description": "Shampoo, conditioner, and styling products",
                "common_materials": ["hdpe", "pet", "pp"],
                "primary_material": "hdpe",
                "avg_weight_kg": 0.4,
                "weight_range": [0.1, 1.0],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 1,
                "repairability_score": 1,
                "packaging_materials": ["plastic"],
                "packaging_weight_ratio": 0.08,
                "size_category": "small",
                "amazon_examples": ["Shampoo", "Conditioner", "Hair oil", "Styling gel"]
            },
            
            "personal_care_devices": {
                "description": "Electric toothbrushes, shavers, hair dryers",
                "common_materials": ["abs_plastic", "aluminum", "lithium"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 0.5,
                "weight_range": [0.1, 1.2],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 4,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.25,
                "size_category": "small",
                "amazon_examples": ["Electric toothbrush", "Hair dryer", "Electric shaver", "Curling iron"]
            },
            
            # ========== HEALTH & WELLNESS ==========
            
            "supplements": {
                "description": "Vitamins, minerals, and nutritional supplements",
                "common_materials": ["hdpe", "pet", "glass"],
                "primary_material": "hdpe",
                "avg_weight_kg": 0.3,
                "weight_range": [0.1, 0.6],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 1,
                "repairability_score": 1,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.1,
                "size_category": "small",
                "amazon_examples": ["Multivitamins", "Protein powder", "Fish oil", "Probiotics"]
            },
            
            "fitness_equipment": {
                "description": "Exercise equipment and accessories",
                "common_materials": ["steel", "eva_foam", "rubber", "nylon"],
                "primary_material": "steel",
                "avg_weight_kg": 5.0,
                "weight_range": [0.2, 50.0],
                "transport_method": "land",
                "recyclability": "high",
                "estimated_lifespan_years": 8,
                "repairability_score": 6,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.15,
                "size_category": "large",
                "amazon_examples": ["Dumbbells", "Yoga mat", "Resistance bands", "Exercise bike"]
            },
            
            # ========== BOOKS & MEDIA ==========
            
            "books": {
                "description": "Physical books and publications",
                "common_materials": ["paper", "cardboard"],
                "primary_material": "paper",
                "avg_weight_kg": 0.4,
                "weight_range": [0.1, 2.0],
                "transport_method": "ship",
                "recyclability": "very_high",
                "estimated_lifespan_years": 20,
                "repairability_score": 2,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.05,
                "size_category": "small",
                "amazon_examples": ["Fiction novels", "Textbooks", "Cookbooks", "Children's books"]
            },
            
            "magazines": {
                "description": "Periodicals and magazines",
                "common_materials": ["paper", "recycled_paper"],
                "primary_material": "recycled_paper",
                "avg_weight_kg": 0.2,
                "weight_range": [0.05, 0.5],
                "transport_method": "ship",
                "recyclability": "very_high",
                "estimated_lifespan_years": 1,
                "repairability_score": 1,
                "packaging_materials": ["plastic"],
                "packaging_weight_ratio": 0.02,
                "size_category": "small",
                "amazon_examples": ["Fashion magazines", "News weekly", "Hobby magazines"]
            },
            
            # ========== TOYS & GAMES ==========
            
            "toys": {
                "description": "Children's toys and games",
                "common_materials": ["abs_plastic", "wood", "eva_foam", "cotton"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 0.8,
                "weight_range": [0.05, 5.0],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 5,
                "repairability_score": 3,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.3,
                "size_category": "medium",
                "amazon_examples": ["LEGO sets", "Barbie dolls", "Action figures", "Board games"]
            },
            
            "building_sets": {
                "description": "Construction toys and building blocks",
                "common_materials": ["abs_plastic", "wood"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 1.2,
                "weight_range": [0.2, 5.0],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 15,
                "repairability_score": 9,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.25,
                "size_category": "medium",
                "amazon_examples": ["LEGO", "K'NEX", "Wooden blocks", "Magnetic tiles"]
            },
            
            # ========== OFFICE & SCHOOL SUPPLIES ==========
            
            "office_supplies": {
                "description": "Stationery and office essentials",
                "common_materials": ["paper", "abs_plastic", "steel"],
                "primary_material": "paper",
                "avg_weight_kg": 0.3,
                "weight_range": [0.01, 2.0],
                "transport_method": "ship",
                "recyclability": "high",
                "estimated_lifespan_years": 3,
                "repairability_score": 2,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.2,
                "size_category": "small",
                "amazon_examples": ["Notebooks", "Pens", "Staplers", "Paper clips"]
            },
            
            # ========== GARDEN & OUTDOOR ==========
            
            "gardening_tools": {
                "description": "Tools and equipment for gardening",
                "common_materials": ["steel", "wood", "aluminum"],
                "primary_material": "steel",
                "avg_weight_kg": 1.5,
                "weight_range": [0.2, 8.0],
                "transport_method": "land",
                "recyclability": "high",
                "estimated_lifespan_years": 12,
                "repairability_score": 8,
                "packaging_materials": ["cardboard"],
                "packaging_weight_ratio": 0.1,
                "size_category": "large",
                "amazon_examples": ["Shovels", "Pruning shears", "Watering can", "Wheelbarrow"]
            },
            
            "outdoor_furniture": {
                "description": "Patio and garden furniture",
                "common_materials": ["aluminum", "steel", "wood", "polyester"],
                "primary_material": "aluminum",
                "avg_weight_kg": 15.0,
                "weight_range": [3.0, 50.0],
                "transport_method": "land",
                "recyclability": "high",
                "estimated_lifespan_years": 8,
                "repairability_score": 5,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.12,
                "size_category": "extra_large",
                "amazon_examples": ["Patio table", "Garden chairs", "Umbrellas", "Cushions"]
            },
            
            # ========== PET SUPPLIES ==========
            
            "pet_food": {
                "description": "Food and treats for pets",
                "common_materials": ["cardboard", "plastic", "aluminum"],
                "primary_material": "cardboard",
                "avg_weight_kg": 2.0,
                "weight_range": [0.1, 15.0],
                "transport_method": "land",
                "recyclability": "medium",
                "estimated_lifespan_years": 1,
                "repairability_score": 1,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.08,
                "size_category": "medium",
                "amazon_examples": ["Dog food", "Cat treats", "Bird seed", "Fish food"]
            },
            
            "pet_accessories": {
                "description": "Toys, beds, and accessories for pets",
                "common_materials": ["nylon", "cotton", "abs_plastic", "steel"],
                "primary_material": "nylon",
                "avg_weight_kg": 0.8,
                "weight_range": [0.05, 5.0],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 3,
                "repairability_score": 4,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.2,
                "size_category": "medium",
                "amazon_examples": ["Dog leash", "Cat bed", "Pet toys", "Food bowls"]
            },
            
            # ========== AUTOMOTIVE (ACCESSORIES ONLY) ==========
            
            "car_accessories": {
                "description": "Car accessories and parts (not vehicles)",
                "common_materials": ["abs_plastic", "rubber", "steel", "aluminum"],
                "primary_material": "abs_plastic",
                "avg_weight_kg": 1.2,
                "weight_range": [0.1, 10.0],
                "transport_method": "ship",
                "recyclability": "medium",
                "estimated_lifespan_years": 6,
                "repairability_score": 4,
                "packaging_materials": ["cardboard", "plastic"],
                "packaging_weight_ratio": 0.15,
                "size_category": "medium",
                "amazon_examples": ["Phone holders", "Floor mats", "Seat covers", "Air fresheners"]
            }
        }
    
    def build_category_hierarchy(self) -> Dict[str, List[str]]:
        """Build hierarchical mapping of Amazon departments to categories"""
        return {
            "Electronics": [
                "smartphones", "laptops", "tablets", "headphones", 
                "computer_accessories", "gaming_equipment", "cameras"
            ],
            "Home & Kitchen": [
                "kitchen_appliances", "cookware", "kitchen_tools", 
                "home_decor", "furniture"
            ],
            "Clothing": [
                "casual_clothing", "athletic_wear", "shoes", "accessories"
            ],
            "Beauty & Personal Care": [
                "skincare", "haircare", "personal_care_devices"
            ],
            "Health & Household": [
                "supplements", "fitness_equipment"
            ],
            "Books": [
                "books", "magazines"
            ],
            "Toys & Games": [
                "toys", "building_sets"
            ],
            "Office Products": [
                "office_supplies"
            ],
            "Garden & Outdoors": [
                "gardening_tools", "outdoor_furniture"
            ],
            "Pet Supplies": [
                "pet_food", "pet_accessories"
            ],
            "Automotive": [
                "car_accessories"
            ]
        }
    
    def get_category_data(self, category_name: str) -> Dict[str, Any]:
        """Get detailed data for a specific category"""
        return self.categories.get(category_name.lower(), None)
    
    def search_categories(self, query: str) -> Dict[str, Dict[str, Any]]:
        """Search categories by name or description"""
        query = query.lower()
        results = {}
        
        for category, data in self.categories.items():
            if (query in category.lower() or 
                query in data.get('description', '').lower() or
                any(query in example.lower() for example in data.get('amazon_examples', []))):
                results[category] = data
        
        return results
    
    def get_categories_by_material(self, material: str) -> List[str]:
        """Get categories that commonly use a specific material"""
        material = material.lower()
        matching_categories = []
        
        for category, data in self.categories.items():
            materials = data.get('common_materials', [])
            if any(material in mat.lower() or mat.lower() in material for mat in materials):
                matching_categories.append(category)
        
        return matching_categories
    
    def get_categories_by_department(self, department: str) -> List[str]:
        """Get all categories within an Amazon department"""
        return self.category_hierarchy.get(department, [])
    
    def estimate_product_attributes(self, category: str, specific_weight: float = None) -> Dict[str, Any]:
        """Estimate product attributes based on category"""
        category_data = self.get_category_data(category)
        if not category_data:
            return self._get_default_attributes()
        
        # Use specific weight if provided, otherwise use category average
        weight = specific_weight if specific_weight else category_data['avg_weight_kg']
        
        return {
            'material': category_data['primary_material'],
            'weight': weight,
            'transport': category_data['transport_method'],
            'recyclability': category_data['recyclability'],
            'inferred_category': category,
            'estimated_lifespan_years': category_data['estimated_lifespan_years'],
            'repairability_score': category_data['repairability_score'],
            'size_category': category_data['size_category'],
            'packaging_type': 'box',  # Most common
            'packaging_materials': category_data['packaging_materials'],
            'packaging_weight_ratio': category_data['packaging_weight_ratio'],
            'secondary_materials': category_data['common_materials'][1:4] if len(category_data['common_materials']) > 1 else []
        }
    
    def _get_default_attributes(self) -> Dict[str, Any]:
        """Default attributes for unknown categories"""
        return {
            'material': 'Mixed',
            'weight': 1.0,
            'transport': 'Ship',
            'recyclability': 'Medium',
            'inferred_category': 'unknown',
            'estimated_lifespan_years': 5,
            'repairability_score': 5,
            'size_category': 'medium',
            'packaging_type': 'box',
            'packaging_materials': ['cardboard', 'plastic'],
            'packaging_weight_ratio': 0.15,
            'secondary_materials': []
        }
    
    def export_categories(self, filename: str = "amazon_product_categories.json"):
        """Export the categories database"""
        database = {
            'categories': self.categories,
            'hierarchy': self.category_hierarchy,
            'metadata': {
                'total_categories': len(self.categories),
                'departments': len(self.category_hierarchy),
                'version': '1.0',
                'description': 'Amazon UK product categories with sustainability data'
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Amazon categories database exported to {filename}")
        print(f"📊 Categories: {len(self.categories)}")
        print(f"🏢 Departments: {len(self.category_hierarchy)}")
        
        # Statistics
        materials_count = {}
        transport_methods = {}
        
        for category, data in self.categories.items():
            # Count materials
            for material in data.get('common_materials', []):
                materials_count[material] = materials_count.get(material, 0) + 1
            
            # Count transport methods
            transport = data.get('transport_method', 'unknown')
            transport_methods[transport] = transport_methods.get(transport, 0) + 1
        
        print(f"📦 Most common materials: {dict(sorted(materials_count.items(), key=lambda x: x[1], reverse=True)[:10])}")
        print(f"🚚 Transport methods: {transport_methods}")

if __name__ == "__main__":
    # Build and export Amazon categories database
    categories_db = AmazonProductCategories()
    categories_db.export_categories()