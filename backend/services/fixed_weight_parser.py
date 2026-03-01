#!/usr/bin/env python3
"""
Fixed Weight Parser + Real Product Weight Database
CRITICAL FIX: No more 128kg iPhones! 
Includes database of real product weights from manufacturer specifications
"""

import re
import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class WeightResult:
    weight_kg: float
    confidence: str  # 'very_high', 'high', 'medium', 'low'
    source: str
    method: str

class FixedWeightParser:
    """
    Properly parse product weights and provide real manufacturer specifications
    """
    
    def __init__(self):
        # Load real product weight database
        self.product_weights = self._build_real_weight_database()
        print(f"✅ Loaded {len(self.product_weights)} real product weights")
    
    def get_accurate_weight(self, product_title: str) -> WeightResult:
        """
        Get accurate product weight using multiple methods
        """
        
        # Method 1: Exact product match from database (HIGHEST accuracy)
        exact_match = self._find_exact_product_match(product_title)
        if exact_match:
            return WeightResult(
                weight_kg=exact_match['weight_kg'],
                confidence='very_high',
                source='manufacturer_database',
                method=f'Exact match: {exact_match["model"]}'
            )
        
        # Method 2: Fuzzy product match (HIGH accuracy)
        fuzzy_match = self._find_fuzzy_product_match(product_title)
        if fuzzy_match:
            return WeightResult(
                weight_kg=fuzzy_match['weight_kg'],
                confidence='high',
                source='manufacturer_database',
                method=f'Fuzzy match: {fuzzy_match["model"]} (similar product)'
            )
        
        # Method 3: Parse weight from title - FIXED VERSION (MEDIUM accuracy)
        parsed_weight = self._parse_weight_from_title_fixed(product_title)
        if parsed_weight:
            return WeightResult(
                weight_kg=parsed_weight['weight_kg'],
                confidence=parsed_weight['confidence'],
                source='title_parsing',
                method=f'Parsed from title: "{parsed_weight["matched_text"]}"'
            )
        
        # Method 4: Category-based estimation (LOW accuracy)
        category_weight = self._estimate_weight_by_category(product_title)
        return WeightResult(
            weight_kg=category_weight['weight_kg'],
            confidence='low',
            source='category_estimation',
            method=f'Category-based estimate: {category_weight["category"]}'
        )
    
    def _build_real_weight_database(self) -> Dict[str, Dict]:
        """
        Real product weights from manufacturer specifications
        This would be expanded with thousands more products
        """
        
        return {
            # ========== SMARTPHONES ==========
            'iphone_14_pro': {
                'model': 'iPhone 14 Pro',
                'weight_kg': 0.206,
                'brand': 'Apple',
                'category': 'smartphone',
                'keywords': ['iphone 14 pro', 'iphone14pro'],
                'source': 'Apple Technical Specifications'
            },
            'iphone_14': {
                'model': 'iPhone 14',
                'weight_kg': 0.172,
                'brand': 'Apple', 
                'category': 'smartphone',
                'keywords': ['iphone 14', 'iphone14'],
                'source': 'Apple Technical Specifications'
            },
            'iphone_13_pro': {
                'model': 'iPhone 13 Pro',
                'weight_kg': 0.204,
                'brand': 'Apple',
                'category': 'smartphone', 
                'keywords': ['iphone 13 pro', 'iphone13pro'],
                'source': 'Apple Technical Specifications'
            },
            'samsung_galaxy_s23': {
                'model': 'Samsung Galaxy S23',
                'weight_kg': 0.168,
                'brand': 'Samsung',
                'category': 'smartphone',
                'keywords': ['galaxy s23', 'samsung s23'],
                'source': 'Samsung Specifications'
            },
            'samsung_galaxy_s23_ultra': {
                'model': 'Samsung Galaxy S23 Ultra',
                'weight_kg': 0.234,
                'brand': 'Samsung',
                'category': 'smartphone',
                'keywords': ['galaxy s23 ultra', 'samsung s23 ultra'],
                'source': 'Samsung Specifications'
            },
            
            # ========== LAPTOPS ==========
            'macbook_air_13': {
                'model': 'MacBook Air 13-inch',
                'weight_kg': 1.24,
                'brand': 'Apple',
                'category': 'laptop',
                'keywords': ['macbook air 13', 'macbook air m2'],
                'source': 'Apple Technical Specifications'
            },
            'macbook_pro_14': {
                'model': 'MacBook Pro 14-inch',
                'weight_kg': 1.60,
                'brand': 'Apple',
                'category': 'laptop',
                'keywords': ['macbook pro 14', 'macbook pro m2'],
                'source': 'Apple Technical Specifications'
            },
            'dell_xps_13': {
                'model': 'Dell XPS 13',
                'weight_kg': 1.25,
                'brand': 'Dell',
                'category': 'laptop',
                'keywords': ['dell xps 13', 'xps13'],
                'source': 'Dell Specifications'
            },
            'thinkpad_x1_carbon': {
                'model': 'ThinkPad X1 Carbon',
                'weight_kg': 1.12,
                'brand': 'Lenovo',
                'category': 'laptop',
                'keywords': ['thinkpad x1 carbon', 'x1 carbon'],
                'source': 'Lenovo Specifications'
            },
            
            # ========== TABLETS ==========
            'ipad_pro_12_9': {
                'model': 'iPad Pro 12.9-inch',
                'weight_kg': 0.682,
                'brand': 'Apple',
                'category': 'tablet',
                'keywords': ['ipad pro 12.9', 'ipad pro 12'],
                'source': 'Apple Technical Specifications'
            },
            'ipad_air': {
                'model': 'iPad Air',
                'weight_kg': 0.461,
                'brand': 'Apple',
                'category': 'tablet',
                'keywords': ['ipad air'],
                'source': 'Apple Technical Specifications'
            },
            'samsung_galaxy_tab_s8': {
                'model': 'Samsung Galaxy Tab S8',
                'weight_kg': 0.503,
                'brand': 'Samsung',
                'category': 'tablet',
                'keywords': ['galaxy tab s8', 'samsung tab s8'],
                'source': 'Samsung Specifications'
            },
            
            # ========== HEADPHONES ==========
            'airpods_pro': {
                'model': 'AirPods Pro',
                'weight_kg': 0.0056,  # Each earbud
                'brand': 'Apple',
                'category': 'headphones',
                'keywords': ['airpods pro'],
                'source': 'Apple Technical Specifications'
            },
            'sony_wh_1000xm5': {
                'model': 'Sony WH-1000XM5',
                'weight_kg': 0.250,
                'brand': 'Sony',
                'category': 'headphones',
                'keywords': ['sony wh-1000xm5', 'wh1000xm5'],
                'source': 'Sony Specifications'
            },
            
            # ========== KITCHEN APPLIANCES ==========
            'kitchenaid_stand_mixer': {
                'model': 'KitchenAid Artisan Stand Mixer',
                'weight_kg': 11.12,
                'brand': 'KitchenAid',
                'category': 'kitchen_appliance',
                'keywords': ['kitchenaid stand mixer', 'kitchenaid artisan'],
                'source': 'KitchenAid Specifications'
            },
            'ninja_blender': {
                'model': 'Ninja Professional Blender',
                'weight_kg': 2.67,
                'brand': 'Ninja',
                'category': 'kitchen_appliance',
                'keywords': ['ninja blender', 'ninja professional'],
                'source': 'Ninja Specifications'
            },
            
            # ========== BOOKS (EXAMPLES) ==========
            'paperback_book_average': {
                'model': 'Average Paperback Book',
                'weight_kg': 0.35,
                'brand': 'Generic',
                'category': 'book',
                'keywords': ['paperback', 'book'],
                'source': 'Publishing Industry Average'
            },
            'hardcover_book_average': {
                'model': 'Average Hardcover Book',
                'weight_kg': 0.65,
                'brand': 'Generic',
                'category': 'book',
                'keywords': ['hardcover', 'hardback'],
                'source': 'Publishing Industry Average'
            },
            
            # ========== CLOTHING (EXAMPLES) ==========
            't_shirt_cotton': {
                'model': 'Cotton T-Shirt (Medium)',
                'weight_kg': 0.15,
                'brand': 'Generic',
                'category': 'clothing',
                'keywords': ['t-shirt', 'tshirt', 'tee'],
                'source': 'Textile Industry Average'
            },
            'jeans_denim': {
                'model': 'Denim Jeans (Medium)',
                'weight_kg': 0.65,
                'brand': 'Generic',
                'category': 'clothing',
                'keywords': ['jeans', 'denim'],
                'source': 'Textile Industry Average'
            }
        }
    
    def _find_exact_product_match(self, product_title: str) -> Optional[Dict]:
        """Find exact product match in database"""
        
        title_lower = product_title.lower()
        
        for product_id, product_data in self.product_weights.items():
            for keyword in product_data['keywords']:
                if keyword.lower() in title_lower:
                    # Additional validation for common keywords
                    if self._validate_exact_match(title_lower, keyword, product_data):
                        return product_data
        
        return None
    
    def _find_fuzzy_product_match(self, product_title: str) -> Optional[Dict]:
        """Find similar products for weight estimation"""
        
        title_lower = product_title.lower()
        
        # Brand + category matching
        for product_id, product_data in self.product_weights.items():
            brand = product_data['brand'].lower()  
            category = product_data['category'].lower()
            
            if brand in title_lower and self._detect_category_in_title(title_lower, category):
                return product_data
        
        return None
    
    def _parse_weight_from_title_fixed(self, product_title: str) -> Optional[Dict]:
        """
        FIXED weight parsing - no more storage units parsed as weight!
        """
        
        title_lower = product_title.lower()
        
        # CRITICAL FIX: Exclude storage units and other non-weight measurements
        excluded_patterns = [
            r'\d+\s*(?:gb|tb|mb|kb)',  # Storage units
            r'\d+\s*(?:ghz|mhz)',      # Frequency
            r'\d+\s*(?:mp|megapixel)', # Camera
            r'\d+\s*(?:inch|")',       # Screen size
            r'\d+\s*(?:volt|v|amp)',   # Electrical
        ]
        
        # Check if title contains storage units - if so, be extra careful
        has_storage = any(re.search(pattern, title_lower) for pattern in excluded_patterns)
        
        # Weight patterns (in order of preference)
        weight_patterns = [
            # Most specific patterns first
            (r'(?:weighs?\s+)?(\d+(?:\.\d+)?)\s*kg(?:\s|$)', 'kg', 1.0),
            (r'(?:weighs?\s+)?(\d+(?:\.\d+)?)\s*pound?s?(?:\s|$)', 'pounds', 0.453592),
            (r'(?:weighs?\s+)?(\d+(?:\.\d+)?)\s*lbs?(?:\s|$)', 'lbs', 0.453592),
            
            # Grams - but be very careful not to catch GB!
            (r'(?:weighs?\s+)?(\d+(?:\.\d+)?)\s*g(?:ram)?s?(?:\s|$|[^b])', 'grams', 0.001),
            (r'(?:weighs?\s+)?(\d+(?:\.\d+)?)\s*oz(?:unce)?s?(?:\s|$)', 'ounces', 0.0283495),
        ]
        
        for pattern, unit, conversion_factor in weight_patterns:
            matches = re.findall(pattern, title_lower)
            
            if matches:
                for match in matches:
                    weight_value = float(match)
                    weight_kg = weight_value * conversion_factor
                    
                    # Sanity checks
                    if not self._is_reasonable_weight(weight_kg, product_title):
                        continue
                    
                    # If we found storage units, be extra cautious about grams
                    if has_storage and unit == 'grams' and weight_value > 500:
                        continue  # Likely a false positive
                    
                    confidence = 'very_high' if unit in ['kg', 'pounds'] else 'high'
                    
                    return {
                        'weight_kg': weight_kg,
                        'confidence': confidence,
                        'matched_text': f"{weight_value} {unit}",
                        'conversion_used': f"{weight_value} {unit} = {weight_kg:.3f} kg"
                    }
        
        return None
    
    def _is_reasonable_weight(self, weight_kg: float, product_title: str) -> bool:
        """Check if weight is reasonable for the product type"""
        
        title_lower = product_title.lower()
        
        # Product type weight ranges (kg)
        weight_ranges = {
            'phone': (0.1, 0.5),
            'laptop': (0.8, 4.0),
            'tablet': (0.3, 1.0),
            'headphones': (0.005, 1.0),
            'book': (0.1, 2.0),
            'clothing': (0.05, 2.0),
            'kitchen': (0.1, 50.0),
            'furniture': (1.0, 200.0),
        }
        
        for product_type, (min_weight, max_weight) in weight_ranges.items():
            if any(keyword in title_lower for keyword in self._get_keywords_for_type(product_type)):
                return min_weight <= weight_kg <= max_weight
        
        # General sanity check: most consumer products are between 10g and 100kg
        return 0.01 <= weight_kg <= 100.0
    
    def _get_keywords_for_type(self, product_type: str) -> List[str]:
        """Get keywords that indicate product type"""
        
        keywords_map = {
            'phone': ['iphone', 'phone', 'smartphone', 'galaxy', 'pixel'],
            'laptop': ['macbook', 'laptop', 'notebook', 'thinkpad'],
            'tablet': ['ipad', 'tablet'], 
            'headphones': ['airpods', 'headphones', 'earbuds', 'headset'],
            'book': ['book', 'paperback', 'hardcover', 'novel'],
            'clothing': ['shirt', 'jeans', 'dress', 'jacket', 'pants'],
            'kitchen': ['mixer', 'blender', 'toaster', 'coffee', 'kettle'],
            'furniture': ['chair', 'table', 'sofa', 'desk', 'bed'],
        }
        
        return keywords_map.get(product_type, [])
    
    def _estimate_weight_by_category(self, product_title: str) -> Dict:
        """Estimate weight based on product category"""
        
        title_lower = product_title.lower()
        
        # Category-based weight estimates
        category_weights = {
            'smartphone': {'weight_kg': 0.2, 'category': 'smartphone'},
            'laptop': {'weight_kg': 1.8, 'category': 'laptop'},
            'tablet': {'weight_kg': 0.5, 'category': 'tablet'},
            'headphones': {'weight_kg': 0.3, 'category': 'headphones'},
            'book': {'weight_kg': 0.4, 'category': 'book'},
            'clothing': {'weight_kg': 0.4, 'category': 'clothing'},
            'kitchen_appliance': {'weight_kg': 2.5, 'category': 'kitchen appliance'},
            'furniture': {'weight_kg': 15.0, 'category': 'furniture'},
        }
        
        # Detect category from title
        for category, data in category_weights.items():
            if self._detect_category_in_title(title_lower, category):
                return data
        
        # Default fallback
        return {'weight_kg': 1.0, 'category': 'general product'}
    
    def _detect_category_in_title(self, title_lower: str, category: str) -> bool:
        """Detect if title contains indicators of specific category"""
        
        category_indicators = {
            'smartphone': ['iphone', 'galaxy', 'pixel', 'phone', 'smartphone'],
            'laptop': ['macbook', 'laptop', 'notebook', 'thinkpad', 'surface'],
            'tablet': ['ipad', 'tablet', 'kindle'],
            'headphones': ['airpods', 'headphones', 'earbuds', 'headset'],
            'book': ['book', 'paperback', 'hardcover', 'novel'],
            'clothing': ['shirt', 'jeans', 'dress', 'jacket', 'pants', 'shoes'],
            'kitchen_appliance': ['mixer', 'blender', 'toaster', 'coffee maker'],
            'furniture': ['chair', 'table', 'sofa', 'desk', 'bed']
        }
        
        indicators = category_indicators.get(category, [])
        return any(indicator in title_lower for indicator in indicators)
    
    def _validate_exact_match(self, title_lower: str, keyword: str, product_data: Dict) -> bool:
        """Additional validation for exact matches"""
        
        # For Apple products, also check for brand
        if product_data['brand'].lower() == 'apple':
            return 'apple' in title_lower or 'iphone' in title_lower or 'ipad' in title_lower or 'macbook' in title_lower
        
        # For Samsung products, check for brand
        if product_data['brand'].lower() == 'samsung':
            return 'samsung' in title_lower or 'galaxy' in title_lower
        
        return True  # Default validation passes
    
    def demonstrate_fixed_parsing(self):
        """Demonstrate the fixed weight parsing with problem cases"""
        
        print("\n🔧 FIXED WEIGHT PARSING DEMONSTRATION")
        print("=" * 80)
        
        test_cases = [
            # Previous problem cases
            "Apple iPhone 14 Pro 128GB Space Black",
            "Samsung Galaxy S23 Ultra 512GB", 
            "MacBook Pro M2 1TB SSD 16GB RAM",
            
            # Cases with explicit weights
            "Laptop weighs 1.5kg with 512GB storage",
            "iPhone 14 Pro 206g weight, 128GB capacity",
            "Book paperback 350g",
            
            # Tricky cases
            "Gaming chair 25kg weight capacity 500GB",
            "Monitor 24 inch 4.2kg weight",
            
            # Known products (should use database)
            "Apple iPhone 14 Pro",
            "MacBook Air 13-inch M2",
            "KitchenAid Artisan Stand Mixer"
        ]
        
        print("\n📊 TEST RESULTS:")
        print("-" * 80)
        
        for i, test_case in enumerate(test_cases, 1):
            result = self.get_accurate_weight(test_case)
            
            print(f"\n{i:2d}. {test_case}")
            print(f"    Weight: {result.weight_kg:.3f} kg")
            print(f"    Confidence: {result.confidence}")
            print(f"    Source: {result.source}")
            print(f"    Method: {result.method}")
            
            # Highlight fixes
            if "128gb" in test_case.lower() and result.weight_kg < 1.0:
                print(f"    ✅ FIXED: No longer parsing 128GB as 128kg!")
            elif result.source == 'manufacturer_database':
                print(f"    ✅ REAL DATA: Using manufacturer specifications!")

if __name__ == "__main__":
    parser = FixedWeightParser()
    parser.demonstrate_fixed_parsing()
    
    print(f"\n🎯 KEY IMPROVEMENTS:")
    print("• Fixed storage unit parsing (GB/TB no longer parsed as weight)")
    print("• Added real product weight database with manufacturer specs")
    print("• Implemented fuzzy matching for similar products")
    print("• Added sanity checks for unreasonable weights")
    print("• Confidence scoring for transparency")
    print("\n🚀 Result: No more 128kg iPhones! Real manufacturer weights used!")