#!/usr/bin/env python3
"""
Scraping Data Validator
Ensures all future scraped products have realistic weights and materials
Integrates with existing scraping pipeline to prevent data quality issues
"""

import re
from typing import Dict, Tuple, Optional, List

class ScrapingDataValidator:
    """
    Validates and corrects scraped product data in real-time
    Prevents unrealistic weights and materials from entering the system
    """
    
    def __init__(self):
        print("🔧 Initializing Scraping Data Validator...")
        
        # Realistic weight ranges by product keywords (kg)
        self.weight_ranges = {
            # Electronics - specific products
            'iphone': (0.15, 0.25),
            'samsung galaxy': (0.16, 0.24),
            'smartphone': (0.14, 0.26),
            'phone': (0.14, 0.30),
            'macbook': (1.2, 2.2),
            'laptop': (1.0, 3.0),
            'ipad': (0.3, 0.7),
            'tablet': (0.3, 0.8),
            'airpods': (0.04, 0.08),
            'headphones': (0.1, 0.6),
            'smartwatch': (0.03, 0.08),
            
            # Garden & Tools
            'pruning shears': (0.2, 0.8),
            'garden shears': (0.2, 0.8),
            'scissors': (0.05, 0.3),
            'knife': (0.1, 0.5),
            'hammer': (0.3, 1.5),
            'screwdriver': (0.05, 0.3),
            'wrench': (0.1, 0.8),
            'pliers': (0.1, 0.4),
            
            # Books & Stationery  
            'book': (0.1, 0.8),
            'paperback': (0.1, 0.4),
            'hardcover': (0.3, 1.0),
            'notebook': (0.05, 0.5),
            'journal': (0.1, 0.4),
            'pen': (0.005, 0.05),
            'pencil': (0.002, 0.02),
            'marker': (0.01, 0.05),
            'eraser': (0.002, 0.02),
            
            # Clothing & Accessories
            'shirt': (0.1, 0.4),
            'pants': (0.2, 0.8),
            'jeans': (0.3, 0.9),
            'dress': (0.2, 0.8),
            'sweater': (0.3, 1.2),
            'jacket': (0.5, 2.0),
            'shoes': (0.3, 1.5),
            'sneakers': (0.3, 1.2),
            'boots': (0.5, 2.0),
            'watch': (0.05, 0.3),
            
            # Kitchen & Home
            'mug': (0.2, 0.5),
            'cup': (0.1, 0.4),
            'plate': (0.2, 0.8),
            'bowl': (0.1, 0.6),
            'knife': (0.05, 0.3),
            'fork': (0.02, 0.1),
            'spoon': (0.02, 0.08),
            'blender': (2.0, 8.0),
            'toaster': (1.5, 5.0),
            'kettle': (0.8, 3.0),
            
            # Personal Care
            'shampoo': (0.2, 1.0),
            'lotion': (0.1, 0.8),
            'toothbrush': (0.01, 0.05),
            'soap': (0.05, 0.3),
            'perfume': (0.05, 0.5)
        }
        
        # Material classification by product keywords
        self.material_mappings = {
            # Garden Tools & Hardware
            'pruning': 'steel',
            'shears': 'steel', 
            'scissors': 'steel',
            'knife': 'steel',
            'hammer': 'steel',
            'screwdriver': 'steel',
            'wrench': 'steel',
            'pliers': 'steel',
            'saw': 'steel',
            'drill': 'steel',
            
            # Electronics
            'iphone': 'aluminum',
            'samsung': 'aluminum',
            'phone': 'aluminum',
            'smartphone': 'aluminum',
            'macbook': 'aluminum',
            'laptop': 'aluminum',
            'ipad': 'aluminum',
            'tablet': 'aluminum',
            'computer': 'aluminum',
            'monitor': 'plastic',
            'keyboard': 'plastic',
            'mouse': 'plastic',
            'headphones': 'plastic',
            'speaker': 'plastic',
            
            # Books & Paper Products
            'book': 'paper',
            'paperback': 'paper',
            'hardcover': 'paper',
            'notebook': 'paper',
            'journal': 'paper',
            'diary': 'paper',
            'magazine': 'paper',
            'novel': 'paper',
            'textbook': 'paper',
            
            # Stationery
            'pen': 'plastic',
            'pencil': 'wood',
            'marker': 'plastic',
            'highlighter': 'plastic',
            'eraser': 'rubber',
            'ruler': 'plastic',
            'calculator': 'plastic',
            
            # Clothing & Textiles
            'shirt': 'cotton',
            'pants': 'cotton',
            'jeans': 'cotton',
            'dress': 'cotton',
            'skirt': 'cotton',
            'sweater': 'wool',
            'cardigan': 'wool',
            'jacket': 'polyester',
            'coat': 'polyester',
            'shoes': 'leather',
            'sneakers': 'synthetic',
            'boots': 'leather',
            'sandals': 'synthetic',
            
            # Kitchen & Dining
            'mug': 'ceramic',
            'cup': 'ceramic',
            'plate': 'ceramic',
            'bowl': 'ceramic',
            'glass': 'glass',
            'bottle': 'glass',
            'knife': 'steel',
            'fork': 'steel',
            'spoon': 'steel',
            'pot': 'steel',
            'pan': 'aluminum',
            'blender': 'plastic',
            'toaster': 'steel',
            
            # Personal Care
            'shampoo': 'plastic',
            'conditioner': 'plastic',
            'lotion': 'plastic',
            'cream': 'plastic',
            'soap': 'plastic',
            'toothbrush': 'plastic',
            'toothpaste': 'plastic',
            'perfume': 'glass',
            'cologne': 'glass'
        }
        
        print(f"✅ Weight validation ranges loaded for {len(self.weight_ranges)} product types")
        print(f"✅ Material mappings loaded for {len(self.material_mappings)} product types")
    
    def validate_and_fix_weight(self, title: str, scraped_weight: float, category: str = "") -> Tuple[float, str, bool]:
        """
        Validate scraped weight and fix if unrealistic
        Returns: (corrected_weight, reason, was_fixed)
        """
        title_lower = title.lower()
        
        # Find most specific matching keyword
        matched_ranges = []
        for keyword, (min_w, max_w) in self.weight_ranges.items():
            if keyword in title_lower:
                matched_ranges.append((keyword, min_w, max_w, len(keyword)))
        
        if matched_ranges:
            # Use the most specific match (longest keyword)
            matched_ranges.sort(key=lambda x: x[3], reverse=True)
            keyword, min_weight, max_weight, _ = matched_ranges[0]
            
            if scraped_weight < min_weight:
                return min_weight, f"Fixed: {keyword} too light, set to minimum {min_weight}kg", True
            elif scraped_weight > max_weight:
                return max_weight, f"Fixed: {keyword} too heavy, capped at {max_weight}kg", True
            else:
                return scraped_weight, f"Validated: {keyword} weight within realistic range", False
        
        # General validation for products without specific ranges
        if scraped_weight > 50:
            return 5.0, "Fixed: Extremely heavy product capped at 5kg", True
        elif scraped_weight > 20:
            return 2.0, "Fixed: Very heavy product capped at 2kg", True
        elif scraped_weight < 0.001:
            return 0.01, "Fixed: Extremely light product set to 0.01kg", True
        
        return scraped_weight, "Weight within general acceptable range", False
    
    def validate_and_fix_material(self, title: str, scraped_material: str, category: str = "") -> Tuple[str, str, bool]:
        """
        Validate scraped material and fix if incorrect
        Returns: (corrected_material, reason, was_fixed)
        """
        title_lower = title.lower()
        
        # Find most specific matching keyword
        matched_materials = []
        for keyword, correct_material in self.material_mappings.items():
            if keyword in title_lower:
                matched_materials.append((keyword, correct_material, len(keyword)))
        
        if matched_materials:
            # Use the most specific match (longest keyword)
            matched_materials.sort(key=lambda x: x[2], reverse=True)
            keyword, correct_material, _ = matched_materials[0]
            
            if scraped_material.lower() != correct_material.lower():
                return correct_material, f"Fixed: {keyword} should be {correct_material}, not {scraped_material}", True
            else:
                return scraped_material, f"Validated: {keyword} material correct", False
        
        # Category-based material validation
        category_lower = category.lower()
        if 'electronic' in category_lower and scraped_material.lower() in ['textile', 'cotton', 'paper']:
            return 'aluminum', f"Fixed: Electronics should be aluminum/plastic, not {scraped_material}", True
        elif 'book' in category_lower and scraped_material.lower() not in ['paper', 'cardboard']:
            return 'paper', f"Fixed: Books should be paper, not {scraped_material}", True
        elif 'garden' in category_lower and scraped_material.lower() in ['textile', 'cotton', 'paper']:
            return 'steel', f"Fixed: Garden tools should be steel/metal, not {scraped_material}", True
        
        return scraped_material, "Material acceptable", False
    
    def validate_scraped_product(self, product_data: Dict) -> Dict:
        """
        Main validation function for scraped product data
        Input: scraped product dictionary
        Output: validated and corrected product dictionary
        """
        
        # Extract data
        title = product_data.get('title', '')
        weight = product_data.get('weight', 0.0)
        material = product_data.get('material', product_data.get('material_type', ''))
        category = product_data.get('category', product_data.get('inferred_category', ''))
        
        validation_log = []
        
        # Validate weight
        if isinstance(weight, (int, float)) and weight > 0:
            corrected_weight, weight_reason, weight_fixed = self.validate_and_fix_weight(title, weight, category)
            if weight_fixed:
                validation_log.append(f"Weight: {weight:.2f}kg → {corrected_weight:.2f}kg ({weight_reason})")
                product_data['weight'] = corrected_weight
        else:
            # Estimate weight if missing/invalid
            estimated_weight, estimate_reason, _ = self.validate_and_fix_weight(title, 999, category)  # Use high value to trigger capping
            product_data['weight'] = estimated_weight
            validation_log.append(f"Weight estimated: {estimated_weight}kg ({estimate_reason})")
        
        # Validate material
        if material:
            corrected_material, material_reason, material_fixed = self.validate_and_fix_material(title, material, category)
            if material_fixed:
                validation_log.append(f"Material: {material} → {corrected_material} ({material_reason})")
                product_data['material'] = corrected_material
                if 'material_type' in product_data:
                    product_data['material_type'] = corrected_material
        
        # Add validation metadata
        product_data['data_validation'] = {
            'validated': True,
            'fixes_applied': len(validation_log),
            'validation_log': validation_log
        }
        
        return product_data
    
    def is_realistic_combination(self, title: str, weight: float, material: str) -> Tuple[bool, List[str]]:
        """
        Check if the combination of title, weight, and material is realistic
        Returns: (is_realistic, list_of_issues)
        """
        issues = []
        title_lower = title.lower()
        
        # Specific impossible combinations
        if 'pruning' in title_lower:
            if weight > 1.0:
                issues.append(f"Pruning shears cannot weigh {weight}kg (max realistic: 0.8kg)")
            if material.lower() in ['textile', 'cotton', 'fabric', 'paper']:
                issues.append(f"Pruning shears cannot be made of {material} (should be steel)")
        
        if 'book' in title_lower:
            if weight > 2.0:
                issues.append(f"Book cannot weigh {weight}kg (max realistic: 2.0kg)")
            if material.lower() in ['steel', 'aluminum', 'metal']:
                issues.append(f"Book cannot be made of {material} (should be paper)")
        
        if any(word in title_lower for word in ['phone', 'iphone', 'smartphone']):
            if weight > 0.5:
                issues.append(f"Phone cannot weigh {weight}kg (max realistic: 0.5kg)")
            if material.lower() in ['paper', 'wood', 'textile']:
                issues.append(f"Phone cannot be made of {material} (should be aluminum/glass)")
        
        if any(word in title_lower for word in ['pen', 'pencil']):
            if weight > 0.1:
                issues.append(f"Pen/pencil cannot weigh {weight}kg (max realistic: 0.1kg)")
        
        return len(issues) == 0, issues

# Integration function for existing scrapers
def validate_scraped_data(product_data: Dict) -> Dict:
    """
    Convenience function to validate scraped data
    Use this in your existing scraping pipeline
    """
    validator = ScrapingDataValidator()
    return validator.validate_scraped_product(product_data)

if __name__ == "__main__":
    # Test the validator
    validator = ScrapingDataValidator()
    
    print("\n🧪 TESTING SCRAPING DATA VALIDATOR")
    print("=" * 60)
    
    # Test cases with problematic data
    test_products = [
        {
            'title': 'Fiskars Pruning Shears',
            'weight': 37.87,
            'material': 'Textile',
            'category': 'garden_&_outdoor'
        },
        {
            'title': 'iPhone 15 Pro',
            'weight': 2.5,
            'material': 'Electronic',
            'category': 'electronics'
        },
        {
            'title': 'Moleskine Classic Notebook',
            'weight': 6.9,
            'material': 'Metal',
            'category': 'books'
        }
    ]
    
    for i, product in enumerate(test_products, 1):
        print(f"\n🔍 Test {i}: {product['title']}")
        print(f"  Before: {product['weight']}kg, {product['material']}")
        
        validated = validator.validate_scraped_product(product.copy())
        
        print(f"  After:  {validated['weight']}kg, {validated['material']}")
        
        if validated['data_validation']['fixes_applied'] > 0:
            print("  Fixes applied:")
            for fix in validated['data_validation']['validation_log']:
                print(f"    - {fix}")
        else:
            print("  ✅ No fixes needed")
    
    print(f"\n✅ Scraping validation system ready!")
    print("💡 Integrate this into your scraping pipeline to prevent future data quality issues")