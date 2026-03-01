# backend/services/materials_service.py

import re
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union

class MaterialsIntelligenceService:
    """
    5-Tier Materials Detection System
    
    Tier 1: Primary + Secondary + Percentages (Best)
    Tier 2: Primary + Secondary (No percentages) 
    Tier 3: Single main material (Current system)
    Tier 4: Category-based intelligent guessing
    Tier 5: Fallback defaults (Mixed/Unknown)
    """
    
    def __init__(self):
        self.load_material_data()
        self.setup_category_materials()
        self.setup_keyword_patterns()
    
    def load_material_data(self):
        """Load CO2 intensity data for environmental impact scoring"""
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            csv_path = os.path.join(base_dir, "common", "data", "csv", "defra_material_intensity.csv")
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                self.material_co2_map = dict(zip(df['material'].str.lower(), df['co2_per_kg']))
            else:
                self.material_co2_map = self.get_default_co2_map()
        except Exception as e:
            print(f"⚠️ Error loading material CO2 data: {e}")
            self.material_co2_map = self.get_default_co2_map()
    
    def get_default_co2_map(self):
        """Default CO2 intensity values (kg CO2 per kg material)"""
        return {
            'aluminum': 9.2, 'plastic': 3.5, 'steel': 2.0, 'glass': 1.3,
            'cardboard': 0.8, 'paper': 0.7, 'cotton': 2.1, 'wood': 0.4,
            'ceramic': 1.7, 'rubber': 2.8, 'fabric': 2.1, 'metal': 3.0,
            'mixed': 2.5, 'unknown': 2.0
        }
    
    def setup_category_materials(self):
        """Smart category-based material predictions (Tier 4)"""
        self.category_materials = {
            # Food & Supplements
            'protein': {'primary': 'Plastic', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'supplement': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.85},
            'vitamins': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.8},
            'powder': {'primary': 'Plastic', 'secondary': ['Cardboard', 'Metal'], 'confidence': 0.85},
            
            # Tools & Hardware
            'tweezers': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.95},
            'screwdriver': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'hammer': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'knife': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            
            # Clothing & Textiles
            'shirt': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'jeans': {'primary': 'Cotton', 'secondary': ['Elastane'], 'confidence': 0.85},
            'jacket': {'primary': 'Polyester', 'secondary': ['Cotton'], 'confidence': 0.8},
            'shoes': {'primary': 'Leather', 'secondary': ['Rubber', 'Fabric'], 'confidence': 0.8},
            
            # Outdoor & Camping
            'camping chair': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.9},
            'tent': {'primary': 'Polyester', 'secondary': ['Metal'], 'confidence': 0.85},
            'sleeping bag': {'primary': 'Polyester', 'secondary': ['Down'], 'confidence': 0.8},
            
            # Electronics - MAJOR EXPANSION
            'phone': {'primary': 'Glass', 'secondary': ['Metal', 'Plastic'], 'confidence': 0.85},
            'iphone': {'primary': 'Glass', 'secondary': ['Metal', 'Plastic'], 'confidence': 0.85},
            'android': {'primary': 'Glass', 'secondary': ['Metal', 'Plastic'], 'confidence': 0.85},
            'laptop': {'primary': 'Metal', 'secondary': ['Plastic', 'Glass'], 'confidence': 0.85},
            'macbook': {'primary': 'Metal', 'secondary': ['Glass'], 'confidence': 0.9},
            'computer': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'tablet': {'primary': 'Glass', 'secondary': ['Metal'], 'confidence': 0.85},
            'ipad': {'primary': 'Glass', 'secondary': ['Metal'], 'confidence': 0.85},
            'tv': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'television': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'monitor': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'headphones': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'earbuds': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'speaker': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'charger': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'cable': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'keyboard': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'mouse': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # Books & Media - NEW CATEGORY
            'book': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.95},
            'novel': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.95},
            'paperback': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'hardcover': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'textbook': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'magazine': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'notebook': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'diary': {'primary': 'Paper', 'secondary': ['Leather'], 'confidence': 0.8},
            
            # Furniture - NEW CATEGORY
            'chair': {'primary': 'Wood', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            'desk': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.8},
            'table': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            'sofa': {'primary': 'Fabric', 'secondary': ['Wood', 'Metal'], 'confidence': 0.85},
            'couch': {'primary': 'Fabric', 'secondary': ['Wood', 'Metal'], 'confidence': 0.85},
            'bed': {'primary': 'Wood', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            'mattress': {'primary': 'Fabric', 'secondary': ['Foam'], 'confidence': 0.85},
            'bookshelf': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'dresser': {'primary': 'Wood', 'secondary': [], 'confidence': 0.85},
            'nightstand': {'primary': 'Wood', 'secondary': [], 'confidence': 0.85},
            
            # Automotive - NEW CATEGORY  
            'tire': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.95},
            'tires': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.95},
            'battery': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.9},
            'filter': {'primary': 'Paper', 'secondary': ['Plastic'], 'confidence': 0.8},
            'oil': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'brake': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            
            # Beauty & Personal Care - NEW CATEGORY
            'shampoo': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'conditioner': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'soap': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.8},
            'lotion': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'cream': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'perfume': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.9},
            'makeup': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'lipstick': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'foundation': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'mascara': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # Sports & Fitness - EXPANDED
            'basketball': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.95},
            'football': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.9},
            'soccer': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.9},
            'tennis': {'primary': 'Rubber', 'secondary': ['Fabric'], 'confidence': 0.85},
            'yoga': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.9},
            'dumbbell': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'weights': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            
            # Kitchen & Home - EXPANDED
            'mug': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.85},
            'cup': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'bottle': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'plate': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'bowl': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'pot': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'pan': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'spoon': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'fork': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'spatula': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.8},
            'cutting board': {'primary': 'Wood', 'secondary': ['Plastic'], 'confidence': 0.8},
            
            # Toys & Games - EXPANDED
            'lego': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'puzzle': {'primary': 'Cardboard', 'secondary': ['Wood'], 'confidence': 0.8},
            'doll': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'toy': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.8},
            'plush': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'teddy': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'stuffed': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'bear': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'game': {'primary': 'Cardboard', 'secondary': ['Plastic'], 'confidence': 0.8},
        }
    
    def setup_keyword_patterns(self):
        """Enhanced keyword matching for material detection"""
        self.material_keywords = {
            'Stainless Steel': ['stainless steel', 'stainless', 'ss304', 'ss316'],
            'Aluminum': ['aluminum', 'aluminium'],  # Removed 'alloy' - too broad
            'Plastic': ['plastic', 'polypropylene', 'pp', 'pe', 'pet', 'abs', 'polycarbonate'],
            'Glass': ['glass', 'borosilicate', 'tempered glass'],
            'Cardboard': ['cardboard', 'carton', 'corrugated'],
            'Paper': ['paper', 'pulp', 'paperback', 'hardcover'],  # Added book-specific terms
            'Cotton': ['cotton', '100% cotton', 'organic cotton', 'denim'],
            'Polyester': ['polyester', 'poly', 'synthetic'],
            'Leather': ['leather', 'genuine leather'],
            'Rubber': ['rubber', 'silicone'],
            'Wood': ['wood', 'wooden', 'oak', 'pine', 'bamboo'],
            'Fabric': ['fabric', 'textile', 'cloth', 'mesh'],
            'Metal': ['metal', 'metallic', 'steel', 'iron'],  # More specific metal terms
            'Ceramic': ['ceramic', 'porcelain', 'clay']
        }
    
    def detect_materials(self, product_data: Dict, amazon_extracted_materials: Dict = None) -> Dict:
        """
        Main entry point for 5-tier materials detection
        
        Args:
            product_data: Product info (title, description, category, etc.)
            amazon_extracted_materials: Pre-extracted materials from Amazon scraping
            
        Returns:
            Dict with materials info, tier used, and confidence
        """
        
        # Try each tier in order of preference
        result = None
        
        # Tier 1: Try detailed extraction with percentages
        if amazon_extracted_materials and amazon_extracted_materials.get('materials'):
            result = self._tier1_detailed_with_percentages(amazon_extracted_materials)
            if result:
                result['tier'] = 1
                result['tier_name'] = 'Detailed with percentages'
                return result
        
        # Tier 2: Try detailed extraction without percentages
        if amazon_extracted_materials and amazon_extracted_materials.get('materials'):
            result = self._tier2_detailed_no_percentages(amazon_extracted_materials)
            if result:
                result['tier'] = 2
                result['tier_name'] = 'Detailed materials'
                return result
        
        # Tier 4: Category-based intelligent guessing (CHECK BEFORE TIER 3)
        result = self._tier4_category_based(product_data)
        if result:
            result['tier'] = 4
            result['tier_name'] = 'Category-based prediction'
            return result
        
        # Tier 3: Single material detection (fallback to keyword matching)
        result = self._tier3_single_material(product_data)
        if result and result['primary_material'] not in ['Mixed', 'Unknown']:
            result['tier'] = 3
            result['tier_name'] = 'Single material'
            return result
        
        # Tier 5: Fallback defaults
        result = self._tier5_fallback()
        result['tier'] = 5
        result['tier_name'] = 'Fallback default'
        return result
    
    def _tier1_detailed_with_percentages(self, amazon_materials: Dict) -> Optional[Dict]:
        """Tier 1: Detailed materials with percentage breakdown"""
        materials = amazon_materials.get('materials', [])
        if not materials or len(materials) < 1:
            return None
        
        # Check if we have percentage data
        has_percentages = any(m.get('weight', 0) > 0 for m in materials)
        if not has_percentages:
            return None
        
        # Sort by weight (highest first)
        materials_sorted = sorted(materials, key=lambda x: x.get('weight', 0), reverse=True)
        
        primary = materials_sorted[0]
        secondary = materials_sorted[1:] if len(materials_sorted) > 1 else []
        
        # Calculate environmental impact score
        env_impact = self._calculate_environmental_impact(materials_sorted)
        
        return {
            'primary_material': primary['name'],
            'primary_percentage': round(primary.get('weight', 0) * 100, 1),
            'secondary_materials': [
                {
                    'name': m['name'], 
                    'percentage': round(m.get('weight', 0) * 100, 1)
                } for m in secondary
            ],
            'all_materials': materials_sorted,
            'confidence': 0.95,
            'environmental_impact_score': env_impact,
            'has_percentages': True
        }
    
    def _tier2_detailed_no_percentages(self, amazon_materials: Dict) -> Optional[Dict]:
        """Tier 2: Detailed materials without percentages"""
        materials = amazon_materials.get('materials', [])
        if not materials or len(materials) < 1:
            return None
        
        # Use confidence scores to determine primary
        materials_sorted = sorted(materials, key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        primary = materials_sorted[0]
        secondary = materials_sorted[1:] if len(materials_sorted) > 1 else []
        
        # Estimate environmental impact without exact percentages
        env_impact = self._estimate_environmental_impact_no_percentages(materials_sorted)
        
        return {
            'primary_material': primary['name'],
            'primary_percentage': None,
            'secondary_materials': [{'name': m['name'], 'percentage': None} for m in secondary],
            'all_materials': materials_sorted,
            'confidence': 0.8,
            'environmental_impact_score': env_impact,
            'has_percentages': False
        }
    
    def _tier3_single_material(self, product_data: Dict) -> Dict:
        """Tier 3: Single material detection (current system)"""
        title = product_data.get('title', '').lower()
        description = product_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # Try keyword matching
        for material, keywords in self.material_keywords.items():
            if any(keyword in text for keyword in keywords):
                env_impact = self.material_co2_map.get(material.lower(), 2.5)
                return {
                    'primary_material': material,
                    'primary_percentage': None,
                    'secondary_materials': [],
                    'all_materials': [{'name': material, 'confidence_score': 0.7}],
                    'confidence': 0.7,
                    'environmental_impact_score': env_impact,
                    'has_percentages': False
                }
        
        return {
            'primary_material': 'Mixed',
            'primary_percentage': None,
            'secondary_materials': [],
            'all_materials': [],
            'confidence': 0.3,
            'environmental_impact_score': 2.5,
            'has_percentages': False
        }
    
    def _tier4_category_based(self, product_data: Dict) -> Optional[Dict]:
        """Tier 4: Smart category-based material prediction"""
        title = product_data.get('title', '').lower()
        category = product_data.get('category', '').lower()
        
        # Check for product type matches
        for product_type, material_info in self.category_materials.items():
            if product_type in title or product_type in category:
                primary = material_info['primary']
                secondary_list = material_info['secondary']
                confidence = material_info['confidence']
                
                # Create secondary materials list
                secondary_materials = [{'name': mat, 'percentage': None} for mat in secondary_list]
                
                # Calculate environmental impact
                all_materials = [primary] + secondary_list
                env_impact = sum(self.material_co2_map.get(mat.lower(), 2.5) for mat in all_materials) / len(all_materials)
                
                return {
                    'primary_material': primary,
                    'primary_percentage': None,
                    'secondary_materials': secondary_materials,
                    'all_materials': [{'name': mat, 'confidence_score': confidence} for mat in all_materials],
                    'confidence': confidence,
                    'environmental_impact_score': env_impact,
                    'has_percentages': False,
                    'prediction_method': f'Category-based: {product_type}'
                }
        
        return None
    
    def _tier5_fallback(self) -> Dict:
        """Tier 5: Final fallback when nothing else works"""
        return {
            'primary_material': 'Mixed',
            'primary_percentage': None,
            'secondary_materials': [],
            'all_materials': [],
            'confidence': 0.1,
            'environmental_impact_score': 2.5,
            'has_percentages': False,
            'prediction_method': 'Fallback default'
        }
    
    def _calculate_environmental_impact(self, materials_with_weights: List[Dict]) -> float:
        """Calculate weighted environmental impact based on material percentages"""
        total_impact = 0
        for material in materials_with_weights:
            material_name = material['name'].lower()
            weight = material.get('weight', 0)
            co2_intensity = self.material_co2_map.get(material_name, 2.5)
            total_impact += co2_intensity * weight
        
        return round(total_impact, 2)
    
    def _estimate_environmental_impact_no_percentages(self, materials: List[Dict]) -> float:
        """Estimate environmental impact when percentages unknown"""
        if not materials:
            return 2.5
        
        # Assume primary material is 70%, secondary materials split the rest
        impacts = []
        for i, material in enumerate(materials):
            material_name = material['name'].lower()
            co2_intensity = self.material_co2_map.get(material_name, 2.5)
            
            if i == 0:  # Primary material
                weight = 0.7
            else:  # Secondary materials
                weight = 0.3 / (len(materials) - 1) if len(materials) > 1 else 0
            
            impacts.append(co2_intensity * weight)
        
        return round(sum(impacts), 2)

# Convenience function for easy integration
def detect_product_materials(product_data: Dict, amazon_materials: Dict = None) -> Dict:
    """
    Easy-to-use function for detecting materials in any product
    
    Usage:
        result = detect_product_materials(product_data, amazon_materials)
        print(f"Primary: {result['primary_material']}")
        print(f"Tier used: {result['tier']} - {result['tier_name']}")
    """
    service = MaterialsIntelligenceService()
    return service.detect_materials(product_data, amazon_materials)