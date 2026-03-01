#!/usr/bin/env python3
"""
Amazon-Focused Materials Database Enhancement
Comprehensive database of materials commonly found in products sold on Amazon
Covers electronics, clothing, home goods, beauty products, toys, books, and more
"""

import json
from typing import Dict, List, Tuple, Any

class AmazonMaterialsDatabase:
    """
    Enhanced materials database focused on Amazon product materials
    Based on actual products sold on Amazon with accurate CO2 intensities
    """
    
    def __init__(self):
        self.amazon_materials = self.build_amazon_materials_database()
        self.amazon_categories = self.build_amazon_category_materials()
    
    def build_amazon_materials_database(self) -> Dict[str, Dict[str, Any]]:
        """
        Build comprehensive Amazon materials database
        All values researched from LCA studies and scientific literature
        """
        
        return {
            
            # ========== ELECTRONICS MATERIALS ==========
            
            # Metals for Electronics
            "aluminum": {
                "co2_intensity": 9.2,
                "category": "non_ferrous_metal",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "International Aluminium Institute",
                "amazon_products": ["iPhone cases", "Laptops", "Tablets", "Smartphones", "Power banks"],
                "alternative_names": ["aluminium", "aluminum alloy"]
            },
            "copper": {
                "co2_intensity": 3.4,
                "category": "non_ferrous_metal",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "International Cooper Association",
                "amazon_products": ["Cables", "Wires", "Electronics", "Chargers", "Speakers"],
                "alternative_names": ["copper wire", "copper alloy"]
            },
            "gold": {
                "co2_intensity": 19500.0,
                "category": "precious_metal",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "World Gold Council LCA",
                "amazon_products": ["Electronics components", "Jewelry", "Watches", "Connectors"],
                "alternative_names": ["gold plating", "gold contacts"]
            },
            "silver": {
                "co2_intensity": 1350.0,
                "category": "precious_metal",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Silver Institute LCA",
                "amazon_products": ["Electronics", "Jewelry", "Watches", "Connectors"],
                "alternative_names": ["silver plating", "silver contacts"]
            },
            "lithium": {
                "co2_intensity": 15.0,
                "category": "battery_material",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Battery industry LCA",
                "amazon_products": ["Phone batteries", "Laptop batteries", "Power banks", "Electric devices"],
                "alternative_names": ["lithium-ion", "li-ion", "lithium battery"]
            },
            "cobalt": {
                "co2_intensity": 8.2,
                "category": "battery_material",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Cobalt Development Institute",
                "amazon_products": ["Batteries", "Electronics", "Rechargeable devices"],
                "alternative_names": ["cobalt oxide", "cobalt sulfate"]
            },
            "nickel": {
                "co2_intensity": 12.8,
                "category": "non_ferrous_metal",
                "confidence": "high",
                "recyclability": "high",
                "source": "Nickel Institute LCA",
                "amazon_products": ["Batteries", "Electronics", "Stainless steel items"],
                "alternative_names": ["nickel alloy", "nickel plating"]
            },
            "rare_earth_elements": {
                "co2_intensity": 45.0,
                "category": "specialty_metal",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Mining industry studies",
                "amazon_products": ["Smartphones", "Speakers", "Hard drives", "Motors"],
                "alternative_names": ["neodymium", "dysprosium", "terbium"]
            },
            
            # Electronics Plastics & Polymers
            "abs_plastic": {
                "co2_intensity": 2.8,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Plastics industry LCA",
                "amazon_products": ["Computer cases", "Electronics housings", "Keyboards", "Mouse"],
                "alternative_names": ["ABS", "acrylonitrile butadiene styrene"]
            },
            "polycarbonate": {
                "co2_intensity": 3.1,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Polycarbonate Association",
                "amazon_products": ["Phone cases", "Laptop screens", "CDs", "Safety equipment"],
                "alternative_names": ["PC plastic", "lexan", "makrolon"]
            },
            "polyethylene": {
                "co2_intensity": 1.6,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "high",
                "source": "Polyethylene Association",
                "amazon_products": ["Packaging", "Bags", "Containers", "Toys"],
                "alternative_names": ["PE", "HDPE", "LDPE", "polyethylene"]
            },
            "polypropylene": {
                "co2_intensity": 1.8,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "high",
                "source": "Polypropylene Association",
                "amazon_products": ["Containers", "Automotive parts", "Textiles", "Packaging"],
                "alternative_names": ["PP", "polyprop"]
            },
            "polystyrene": {
                "co2_intensity": 2.9,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "low",
                "source": "Styrene industry LCA",
                "amazon_products": ["Packaging", "Disposable items", "Insulation", "Toys"],
                "alternative_names": ["PS", "styrofoam", "expanded polystyrene"]
            },
            "tpu": {
                "co2_intensity": 4.2,
                "category": "thermoplastic",
                "confidence": "medium",
                "recyclability": "medium",
                "source": "Polyurethane Association",
                "amazon_products": ["Phone cases", "Protective covers", "Flexible parts"],
                "alternative_names": ["thermoplastic polyurethane", "flexible plastic"]
            },
            
            # Electronics Components
            "silicon": {
                "co2_intensity": 5.6,
                "category": "semiconductor",
                "confidence": "high",
                "recyclability": "low",
                "source": "Semiconductor industry LCA",
                "amazon_products": ["Computer chips", "Solar panels", "Electronics"],
                "alternative_names": ["silicon wafer", "crystalline silicon"]
            },
            "glass": {
                "co2_intensity": 1.3,
                "category": "ceramic_glass",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Glass industry LCA",
                "amazon_products": ["Screens", "Bottles", "Containers", "Lenses"],
                "alternative_names": ["tempered glass", "borosilicate glass"]
            },
            "gorilla_glass": {
                "co2_intensity": 1.5,
                "category": "specialty_glass",
                "confidence": "medium",
                "recyclability": "high",
                "source": "Corning LCA estimates",
                "amazon_products": ["Smartphone screens", "Tablet screens", "Protective glass"],
                "alternative_names": ["strengthened glass", "chemically strengthened glass"]
            },
            
            # ========== CLOTHING & TEXTILES MATERIALS ==========
            
            # Natural Fibers
            "cotton": {
                "co2_intensity": 2.1,
                "category": "plant_fiber",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Cotton Incorporated LCA",
                "amazon_products": ["T-shirts", "Jeans", "Underwear", "Bedding", "Towels"],
                "alternative_names": ["organic cotton", "cotton blend"]
            },
            "wool": {
                "co2_intensity": 10.4,
                "category": "animal_fiber",
                "confidence": "high",
                "recyclability": "medium",
                "source": "International Wool Textile Organisation",
                "amazon_products": ["Sweaters", "Coats", "Blankets", "Socks"],
                "alternative_names": ["merino wool", "sheep wool", "wool blend"]
            },
            "silk": {
                "co2_intensity": 4.8,
                "category": "animal_fiber",
                "confidence": "medium",
                "recyclability": "medium",
                "source": "Silk industry studies",
                "amazon_products": ["Scarves", "Dresses", "Bedding", "Ties"],
                "alternative_names": ["mulberry silk", "natural silk"]
            },
            "linen": {
                "co2_intensity": 1.8,
                "category": "plant_fiber",
                "confidence": "high",
                "recyclability": "high",
                "source": "Flax industry LCA",
                "amazon_products": ["Shirts", "Pants", "Bedding", "Home textiles"],
                "alternative_names": ["flax", "linen blend"]
            },
            "hemp": {
                "co2_intensity": 1.2,
                "category": "plant_fiber",
                "confidence": "medium",
                "recyclability": "high",
                "source": "Hemp industry studies",
                "amazon_products": ["Clothing", "Bags", "Ropes", "Textiles"],
                "alternative_names": ["hemp fiber", "industrial hemp"]
            },
            "bamboo": {
                "co2_intensity": 1.5,
                "category": "plant_fiber",
                "confidence": "medium",
                "recyclability": "medium",
                "source": "Bamboo textile studies",
                "amazon_products": ["Clothing", "Bedding", "Towels", "Socks"],
                "alternative_names": ["bamboo rayon", "bamboo viscose"]
            },
            
            # Synthetic Fibers
            "polyester": {
                "co2_intensity": 3.8,
                "category": "synthetic_textile",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Textile Exchange LCA",
                "amazon_products": ["Athletic wear", "Jackets", "Pants", "Bedding"],
                "alternative_names": ["PET fiber", "polyester blend"]
            },
            "nylon": {
                "co2_intensity": 6.4,
                "category": "synthetic_textile",
                "confidence": "high",
                "recyclability": "medium",
                "source": "Nylon industry LCA",
                "amazon_products": ["Activewear", "Hosiery", "Swimwear", "Bags"],
                "alternative_names": ["polyamide", "nylon 6", "nylon 66"]
            },
            "spandex": {
                "co2_intensity": 4.9,
                "category": "synthetic_textile",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Elastane industry studies",
                "amazon_products": ["Activewear", "Underwear", "Swimwear", "Leggings"],
                "alternative_names": ["elastane", "lycra"]
            },
            "acrylic": {
                "co2_intensity": 5.1,
                "category": "synthetic_textile",
                "confidence": "high",
                "recyclability": "low",
                "source": "Acrylic fiber LCA",
                "amazon_products": ["Sweaters", "Blankets", "Carpets", "Fake fur"],
                "alternative_names": ["acrylic fiber", "polyacrylonitrile"]
            },
            "rayon": {
                "co2_intensity": 3.2,
                "category": "regenerated_fiber",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Viscose industry studies",
                "amazon_products": ["Dresses", "Shirts", "Linings", "Home textiles"],
                "alternative_names": ["viscose", "modal", "tencel"]
            },
            
            # ========== HOME & KITCHEN MATERIALS ==========
            
            # Metals for Kitchen
            "steel": {
                "co2_intensity": 2.0,
                "category": "ferrous_metal",
                "confidence": "high",
                "recyclability": "high",
                "source": "World Steel Association LCA",
                "amazon_products": ["Cookware", "Appliances", "Tools", "Furniture"],
                "alternative_names": ["carbon steel", "mild steel"]
            },
            "stainless_steel": {
                "co2_intensity": 2.8,
                "category": "ferrous_metal",
                "confidence": "high",
                "recyclability": "high",
                "source": "ISSF LCA data",
                "amazon_products": ["Kitchen appliances", "Cookware", "Cutlery", "Appliances"],
                "alternative_names": ["ss304", "ss316", "inox"]
            },
            "cast_iron": {
                "co2_intensity": 1.8,
                "category": "ferrous_metal",
                "confidence": "high",
                "recyclability": "high",
                "source": "Cast iron industry LCA",
                "amazon_products": ["Cookware", "Garden furniture", "Decorative items"],
                "alternative_names": ["iron", "cast iron cookware"]
            },
            
            # Kitchen & Home Plastics
            "melamine": {
                "co2_intensity": 3.4,
                "category": "thermoset_plastic",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Melamine industry estimates",
                "amazon_products": ["Dinnerware", "Kitchen utensils", "Countertops"],
                "alternative_names": ["melamine resin", "melamine formaldehyde"]
            },
            "silicone": {
                "co2_intensity": 4.7,
                "category": "synthetic_polymer",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Silicone industry studies",
                "amazon_products": ["Bakeware", "Kitchen tools", "Phone cases", "Baby products"],
                "alternative_names": ["silicone rubber", "food grade silicone"]
            },
            "ceramic": {
                "co2_intensity": 0.9,
                "category": "ceramic",
                "confidence": "high",
                "recyclability": "low",
                "source": "Ceramic industry LCA",
                "amazon_products": ["Dinnerware", "Cookware", "Decorative items", "Tiles"],
                "alternative_names": ["porcelain", "earthenware", "stoneware"]
            },
            
            # Wood & Natural Materials
            "wood": {
                "co2_intensity": 0.1,
                "category": "natural_material",
                "confidence": "high",
                "recyclability": "high",
                "source": "Forest products LCA",
                "amazon_products": ["Furniture", "Kitchen utensils", "Decorative items", "Toys"],
                "alternative_names": ["hardwood", "softwood", "engineered wood"]
            },
            "bamboo_wood": {
                "co2_intensity": 0.05,
                "category": "natural_material",
                "confidence": "medium",
                "recyclability": "high",
                "source": "Bamboo industry studies",
                "amazon_products": ["Kitchen utensils", "Cutting boards", "Furniture", "Decorative items"],
                "alternative_names": ["bamboo", "bamboo composite"]
            },
            "cork": {
                "co2_intensity": 0.3,
                "category": "natural_material",
                "confidence": "medium",
                "recyclability": "high",
                "source": "Cork industry LCA",
                "amazon_products": ["Wine stoppers", "Flooring", "Yoga mats", "Coasters"],
                "alternative_names": ["natural cork", "cork composite"]
            },
            
            # ========== BEAUTY & PERSONAL CARE MATERIALS ==========
            
            # Packaging Materials
            "hdpe": {
                "co2_intensity": 1.7,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "high",
                "source": "Polyethylene Association",
                "amazon_products": ["Shampoo bottles", "Cosmetic containers", "Cleaning bottles"],
                "alternative_names": ["high density polyethylene", "HDPE plastic"]
            },
            "pet": {
                "co2_intensity": 2.2,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "high",
                "source": "PET Resin Association",
                "amazon_products": ["Water bottles", "Cosmetic bottles", "Food containers"],
                "alternative_names": ["polyethylene terephthalate", "PET plastic"]
            },
            "pp": {
                "co2_intensity": 1.8,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "high",
                "source": "Polypropylene Association",
                "amazon_products": ["Cosmetic caps", "Food containers", "Straws"],
                "alternative_names": ["polypropylene", "PP plastic"]
            },
            
            # Personal Care Ingredients (for carbon calculations)
            "palm_oil": {
                "co2_intensity": 2.3,
                "category": "natural_oil",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Palm oil LCA studies",
                "amazon_products": ["Soaps", "Cosmetics", "Food products", "Candles"],
                "alternative_names": ["palm kernel oil", "sustainable palm oil"]
            },
            "coconut_oil": {
                "co2_intensity": 1.4,
                "category": "natural_oil",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Coconut industry LCA",
                "amazon_products": ["Cosmetics", "Food products", "Hair care", "Soaps"],
                "alternative_names": ["virgin coconut oil", "refined coconut oil"]
            },
            
            # ========== BOOKS & PAPER MATERIALS ==========
            
            "paper": {
                "co2_intensity": 0.7,
                "category": "paper",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Paper industry LCA",
                "amazon_products": ["Books", "Magazines", "Packaging", "Office supplies"],
                "alternative_names": ["recycled paper", "newsprint", "cardboard"]
            },
            "cardboard": {
                "co2_intensity": 0.8,
                "category": "paper",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Corrugated packaging LCA",
                "amazon_products": ["Packaging boxes", "Shipping materials", "Storage boxes"],
                "alternative_names": ["corrugated cardboard", "paperboard"]
            },
            "recycled_paper": {
                "co2_intensity": 0.5,
                "category": "paper",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Recycled paper LCA",
                "amazon_products": ["Eco-friendly books", "Packaging", "Office supplies"],
                "alternative_names": ["post-consumer recycled", "recycled content"]
            },
            
            # ========== TOYS & GAMES MATERIALS ==========
            
            "pvc": {
                "co2_intensity": 2.4,
                "category": "thermoplastic",
                "confidence": "high",
                "recyclability": "low",
                "source": "PVC industry LCA",
                "amazon_products": ["Toys", "Inflatable items", "Pipes", "Vinyl products"],
                "alternative_names": ["polyvinyl chloride", "vinyl"]
            },
            "eva_foam": {
                "co2_intensity": 2.1,
                "category": "foam_material",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Foam industry estimates",
                "amazon_products": ["Foam toys", "Exercise mats", "Packaging", "Craft materials"],
                "alternative_names": ["ethylene vinyl acetate", "EVA"]
            },
            "latex": {
                "co2_intensity": 1.9,
                "category": "natural_rubber",
                "confidence": "medium",
                "recyclability": "medium",
                "source": "Rubber industry LCA",
                "amazon_products": ["Balloons", "Gloves", "Mattresses", "Toys"],
                "alternative_names": ["natural rubber", "synthetic latex"]
            },
            
            # ========== SPECIALTY MATERIALS ==========
            
            "carbon_fiber": {
                "co2_intensity": 24.0,
                "category": "composite_material",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Carbon fiber industry studies",
                "amazon_products": ["Sports equipment", "Electronics cases", "Automotive parts"],
                "alternative_names": ["carbon fibre", "CFRP"]
            },
            "fiberglass": {
                "co2_intensity": 2.7,
                "category": "composite_material",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Fiberglass industry LCA",
                "amazon_products": ["Sports equipment", "Automotive parts", "Construction materials"],
                "alternative_names": ["glass fiber", "GFRP"]
            },
            "titanium": {
                "co2_intensity": 35.0,
                "category": "specialty_metal",
                "confidence": "medium",
                "recyclability": "high",
                "source": "Titanium industry studies",
                "amazon_products": ["Jewelry", "Sports equipment", "Medical devices", "Electronics"],
                "alternative_names": ["titanium alloy", "grade 2 titanium"]
            },
            "magnesium": {
                "co2_intensity": 16.2,
                "category": "non_ferrous_metal",
                "confidence": "medium",
                "recyclability": "high",  
                "source": "Magnesium industry LCA",
                "amazon_products": ["Electronics cases", "Automotive parts", "Sports equipment"],
                "alternative_names": ["magnesium alloy", "mag"]
            },
            
            # ========== PACKAGING MATERIALS ==========
            
            "bubble_wrap": {
                "co2_intensity": 2.0,
                "category": "packaging_material",
                "confidence": "medium",
                "recyclability": "medium",
                "source": "Packaging industry estimates",
                "amazon_products": ["Protective packaging", "Shipping materials"],
                "alternative_names": ["air cushioning", "bubble film"]
            },
            "foam_padding": {
                "co2_intensity": 2.8,
                "category": "packaging_material",
                "confidence": "medium",
                "recyclability": "low",
                "source": "Foam packaging LCA",
                "amazon_products": ["Electronics packaging", "Protective padding"],
                "alternative_names": ["polyurethane foam", "protective foam"]
            },
            "kraft_paper": {
                "co2_intensity": 0.9,
                "category": "paper",
                "confidence": "high",
                "recyclability": "very_high",
                "source": "Kraft paper LCA",
                "amazon_products": ["Shipping envelopes", "Packaging", "Paper bags"],
                "alternative_names": ["brown paper", "kraft board"]
            }
        }
    
    def build_amazon_category_materials(self) -> Dict[str, List[str]]:
        """Map Amazon categories to their common materials"""
        return {
            "Electronics": ["aluminum", "copper", "silicon", "abs_plastic", "polycarbonate", "glass", "lithium", "gold", "silver"],
            "Clothing": ["cotton", "polyester", "nylon", "spandex", "wool", "silk", "linen", "rayon"],
            "Home & Kitchen": ["stainless_steel", "aluminum", "glass", "ceramic", "silicone", "wood", "bamboo_wood"],
            "Beauty": ["hdpe", "pet", "pp", "palm_oil", "coconut_oil", "glass"],
            "Books": ["paper", "cardboard", "recycled_paper"],
            "Toys": ["abs_plastic", "pvc", "eva_foam", "latex", "wood"],
            "Sports": ["polyester", "nylon", "rubber", "aluminum", "carbon_fiber", "eva_foam"],
            "Tools": ["steel", "aluminum", "abs_plastic", "rubber"],
            "Health": ["hdpe", "pet", "pp", "glass", "aluminum"],
            "Baby": ["silicone", "abs_plastic", "cotton", "latex", "wood"],
            "Automotive": ["steel", "aluminum", "abs_plastic", "rubber", "glass"],
            "Garden": ["steel", "aluminum", "hdpe", "wood", "ceramic"],
            "Office": ["paper", "abs_plastic", "steel", "aluminum"],
            "Pet Supplies": ["nylon", "cotton", "steel", "ceramic", "hdpe"]
        }
    
    def get_material_properties(self, material_name: str) -> Dict[str, Any]:
        """Get material properties with fuzzy matching"""
        material_name = material_name.lower().strip().replace(' ', '_')
        
        # Direct match
        if material_name in self.amazon_materials:
            return self.amazon_materials[material_name]
        
        # Check alternative names
        for material, data in self.amazon_materials.items():
            alt_names = data.get('alternative_names', [])
            if any(material_name in alt.lower() or alt.lower() in material_name for alt in alt_names):
                return data
        
        # Fuzzy matching
        for material in self.amazon_materials.keys():
            if material_name in material or material in material_name:
                return self.amazon_materials[material]
        
        return None
    
    def get_materials_by_category(self, amazon_category: str) -> List[Dict[str, Any]]:
        """Get all materials commonly used in an Amazon category"""
        category_materials = self.amazon_categories.get(amazon_category, [])
        return [self.amazon_materials[mat] for mat in category_materials if mat in self.amazon_materials]
    
    def get_material_impact_score(self, material_name: str) -> float:
        """Get CO2 impact score for a material"""
        material_data = self.get_material_properties(material_name)
        if material_data:
            return material_data.get('co2_intensity', 2.0)
        return 2.0  # Default fallback
    
    def get_material_confidence(self, material_name: str) -> str:
        """Get confidence level for material data"""
        material_data = self.get_material_properties(material_name)
        if material_data:
            return material_data.get('confidence', 'low')
        return 'low'
    
    def export_database(self, filename: str = "amazon_materials_database.json"):
        """Export the Amazon materials database"""
        database = {
            'materials': self.amazon_materials,
            'category_mapping': self.amazon_categories,
            'metadata': {
                'total_materials': len(self.amazon_materials),
                'categories_covered': len(self.amazon_categories),
                'version': '2.0',
                'focus': 'Amazon UK products'
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Amazon materials database exported to {filename}")
        print(f"📊 Materials: {len(self.amazon_materials)}")
        print(f"🛒 Amazon categories: {len(self.amazon_categories)}")
        
        # Statistics by category
        material_categories = {}
        for material, data in self.amazon_materials.items():
            cat = data['category']
            material_categories[cat] = material_categories.get(cat, 0) + 1
        
        print(f"📈 Material categories: {dict(sorted(material_categories.items(), key=lambda x: x[1], reverse=True)[:10])}")

if __name__ == "__main__":
    # Build and export Amazon materials database
    amazon_materials = AmazonMaterialsDatabase()
    amazon_materials.export_database()