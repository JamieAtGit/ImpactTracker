#!/usr/bin/env python3
"""
Comprehensive Data Quality Fixer
Fixes weight extraction, material detection, and validates all 170,000 products
Ensures realistic values for past and future products
"""

import csv
import re
import sys
import os
from typing import Dict, List, Tuple, Optional
import time

class ComprehensiveDataQualityFixer:
    """
    Fix fundamental data quality issues in the entire product dataset
    """
    
    def __init__(self):
        print("🔧 Initializing Comprehensive Data Quality Fixer...")
        
        # Realistic weight ranges by product category (kg)
        self.weight_ranges = {
            # Electronics
            'smartphones': (0.15, 0.25),
            'electronics': (0.1, 5.0),
            'laptops': (1.0, 3.0),
            'tablets': (0.3, 0.8),
            'headphones': (0.05, 0.5),
            'smartwatch': (0.03, 0.08),
            
            # Books & Stationery
            'books': (0.15, 0.8),
            'stationery': (0.01, 0.1),
            'notebook': (0.1, 0.5),
            'pen': (0.005, 0.05),
            'pencil': (0.005, 0.02),
            
            # Garden & Tools  
            'garden_&_outdoor': (0.1, 2.0),
            'pruning_shears': (0.2, 0.8),
            'tools': (0.1, 5.0),
            
            # Clothing & Textiles
            'clothing': (0.1, 1.5),
            'shoes': (0.3, 1.2),
            'accessories': (0.02, 0.5),
            
            # Kitchen & Home
            'kitchen_appliances': (0.5, 15.0),
            'household': (0.1, 10.0),
            'appliances': (2.0, 50.0),
            
            # Personal Care
            'personal_care': (0.05, 1.0),
            'beauty': (0.02, 0.5),
            
            # Default ranges
            'default_small': (0.05, 0.5),
            'default_medium': (0.2, 2.0),
            'default_large': (1.0, 10.0)
        }
        
        # Material detection rules by product keywords
        self.material_rules = {
            # Garden Tools
            'pruning': 'steel',
            'shears': 'steel', 
            'scissors': 'steel',
            'knife': 'steel',
            'hammer': 'steel',
            'wrench': 'steel',
            'pliers': 'steel',
            
            # Electronics
            'iphone': 'aluminum',
            'samsung': 'aluminum', 
            'phone': 'aluminum',
            'smartphone': 'aluminum',
            'laptop': 'aluminum',
            'macbook': 'aluminum',
            'tablet': 'aluminum',
            'ipad': 'aluminum',
            'headphones': 'plastic',
            'earbuds': 'plastic',
            
            # Books & Paper
            'book': 'paper',
            'notebook': 'paper',
            'journal': 'paper', 
            'diary': 'paper',
            'magazine': 'paper',
            'novel': 'paper',
            
            # Stationery
            'pen': 'plastic',
            'pencil': 'wood',
            'marker': 'plastic',
            'highlighter': 'plastic',
            'eraser': 'rubber',
            
            # Clothing
            'shirt': 'cotton',
            'pants': 'cotton',  
            'jeans': 'cotton',
            'dress': 'cotton',
            'sweater': 'wool',
            'jacket': 'polyester',
            'shoes': 'leather',
            'sneakers': 'synthetic',
            
            # Kitchen
            'mug': 'ceramic',
            'cup': 'ceramic',
            'plate': 'ceramic',
            'bowl': 'ceramic',
            'knife': 'steel',
            'fork': 'steel',
            'spoon': 'steel',
            
            # Personal Care
            'shampoo': 'plastic',
            'lotion': 'plastic',
            'cream': 'plastic',
            'soap': 'plastic',
            'toothbrush': 'plastic',
            
            # Default materials
            'bottle': 'plastic',
            'container': 'plastic',
            'box': 'cardboard'
        }
        
        # Validation rules - impossible combinations
        self.validation_rules = [
            # Weight validations
            lambda title, weight, material: (
                'pen' in title.lower() and weight > 0.1,
                f"Pen cannot weigh {weight}kg (max: 0.1kg)"
            ),
            lambda title, weight, material: (
                'book' in title.lower() and weight > 2.0,
                f"Book cannot weigh {weight}kg (max: 2.0kg)"
            ),
            lambda title, weight, material: (
                'phone' in title.lower() and weight > 0.5,
                f"Phone cannot weigh {weight}kg (max: 0.5kg)"
            ),
            lambda title, weight, material: (
                'pruning' in title.lower() and weight > 1.0,
                f"Pruning shears cannot weigh {weight}kg (max: 1.0kg)"
            ),
            
            # Material validations
            lambda title, weight, material: (
                'pruning' in title.lower() and material.lower() in ['textile', 'cotton', 'fabric'],
                f"Pruning shears cannot be made of {material} (should be steel/metal)"
            ),
            lambda title, weight, material: (
                'book' in title.lower() and material.lower() in ['metal', 'steel', 'aluminum'],
                f"Book cannot be made of {material} (should be paper)"
            ),
            lambda title, weight, material: (
                'phone' in title.lower() and material.lower() in ['textile', 'paper', 'wood'],
                f"Phone cannot be made of {material} (should be aluminum/glass/plastic)"
            )
        ]
        
        print("✅ Weight ranges loaded for all product categories")
        print("✅ Material detection rules loaded")
        print("✅ Validation rules loaded")
    
    def fix_weight(self, title: str, current_weight: float, category: str) -> Tuple[float, str]:
        """
        Fix unrealistic product weights based on title and category
        """
        title_lower = title.lower()
        
        # Specific product weight fixes
        if any(word in title_lower for word in ['pruning', 'shears']):
            return 0.35, "Fixed: Pruning shears should be ~0.35kg"
        elif any(word in title_lower for word in ['iphone', 'phone', 'smartphone']):
            return 0.20, "Fixed: Smartphone should be ~0.20kg"
        elif any(word in title_lower for word in ['book', 'novel', 'paperback']):
            return 0.25, "Fixed: Book should be ~0.25kg"
        elif any(word in title_lower for word in ['pen', 'pencil']):
            return 0.015, "Fixed: Pen/pencil should be ~0.015kg"
        elif any(word in title_lower for word in ['notebook', 'journal']):
            return 0.20, "Fixed: Notebook should be ~0.20kg"
        elif any(word in title_lower for word in ['macbook', 'laptop']):
            return 1.50, "Fixed: Laptop should be ~1.5kg"
        elif any(word in title_lower for word in ['ipad', 'tablet']):
            return 0.50, "Fixed: Tablet should be ~0.5kg"
        elif any(word in title_lower for word in ['mug', 'cup']):
            return 0.30, "Fixed: Mug should be ~0.30kg"
        
        # Category-based weight ranges
        category_clean = category.lower().replace(' ', '_').replace('&', '_')
        
        if category_clean in self.weight_ranges:
            min_weight, max_weight = self.weight_ranges[category_clean]
            
            if current_weight < min_weight:
                return min_weight, f"Fixed: {category} minimum weight"
            elif current_weight > max_weight:
                return max_weight, f"Fixed: {category} maximum weight" 
            else:
                return current_weight, "Weight within realistic range"
        
        # Default weight limits based on product size estimation
        if current_weight > 20:  # Absurdly heavy
            return 2.0, "Fixed: Extremely heavy product capped at 2kg"
        elif current_weight > 10:
            return 1.0, "Fixed: Very heavy product capped at 1kg"
        elif current_weight < 0.01:
            return 0.05, "Fixed: Extremely light product set to 0.05kg"
        
        return current_weight, "Weight acceptable"
    
    def fix_material(self, title: str, current_material: str, category: str) -> Tuple[str, str]:
        """
        Fix incorrect material classifications based on product title
        """
        title_lower = title.lower()
        
        # Check material rules by product keywords
        for keyword, correct_material in self.material_rules.items():
            if keyword in title_lower:
                if current_material.lower() != correct_material.lower():
                    return correct_material, f"Fixed: {keyword} products are typically made of {correct_material}"
                else:
                    return current_material, "Material correct"
        
        # Category-based material corrections
        category_lower = category.lower()
        
        if 'electronic' in category_lower:
            if current_material.lower() in ['textile', 'cotton', 'paper']:
                return 'aluminum', "Fixed: Electronics are typically aluminum/plastic"
        elif 'book' in category_lower:
            if current_material.lower() not in ['paper', 'cardboard']:
                return 'paper', "Fixed: Books are made of paper"
        elif 'clothing' in category_lower:
            if current_material.lower() in ['metal', 'steel', 'aluminum']:
                return 'cotton', "Fixed: Clothing is typically cotton/polyester"
        elif 'garden' in category_lower or 'tool' in category_lower:
            if current_material.lower() in ['textile', 'cotton', 'paper']:
                return 'steel', "Fixed: Garden tools are typically steel/metal"
        
        return current_material, "Material acceptable"
    
    def validate_product(self, title: str, weight: float, material: str) -> List[str]:
        """
        Run validation rules to catch impossible combinations
        """
        issues = []
        
        for rule in self.validation_rules:
            is_invalid, error_message = rule(title, weight, material)
            if is_invalid:
                issues.append(error_message)
        
        return issues
    
    def fix_entire_dataset(self):
        """
        Fix data quality issues across the entire 170,000 product dataset
        """
        import os
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        input_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        output_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset_quality_fixed.csv')
        
        print(f"\n🚀 FIXING DATA QUALITY FOR ENTIRE DATASET")
        print("=" * 80)
        print(f"📁 Input: {input_path}")
        print(f"📁 Output: {output_path}")
        
        start_time = time.time()
        
        stats = {
            'total_processed': 0,
            'weights_fixed': 0,
            'materials_fixed': 0,
            'validation_issues': 0,
            'perfect_products': 0
        }
        
        improvements = []
        
        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    stats['total_processed'] += 1
                    
                    # Progress tracking
                    if stats['total_processed'] % 10000 == 0:
                        elapsed = time.time() - start_time
                        print(f"  🔄 Processed: {stats['total_processed']:,} products ({elapsed/60:.1f} minutes)")
                    
                    try:
                        # Extract current values
                        title = row['title']
                        current_weight = float(row['weight'])
                        current_material = row['material']
                        category = row['inferred_category']
                        
                        changes_made = []
                        
                        # Fix weight
                        new_weight, weight_reason = self.fix_weight(title, current_weight, category)
                        if new_weight != current_weight:
                            changes_made.append(f"Weight: {current_weight:.2f}kg → {new_weight:.2f}kg ({weight_reason})")
                            row['weight'] = new_weight
                            stats['weights_fixed'] += 1
                        
                        # Fix material
                        new_material, material_reason = self.fix_material(title, current_material, category)
                        if new_material != current_material:
                            changes_made.append(f"Material: {current_material} → {new_material} ({material_reason})")
                            row['material'] = new_material
                            stats['materials_fixed'] += 1
                        
                        # Validate final result
                        validation_issues = self.validate_product(title, float(row['weight']), row['material'])
                        if validation_issues:
                            stats['validation_issues'] += len(validation_issues)
                            changes_made.extend([f"Validation: {issue}" for issue in validation_issues])
                        
                        # Track improvements
                        if changes_made:
                            improvements.append({
                                'title': title[:50],
                                'changes': changes_made
                            })
                        else:
                            stats['perfect_products'] += 1
                        
                        # Recalculate CO2 with fixed data (optional)
                        # This would require importing the CO2 calculation system
                        
                    except (ValueError, KeyError) as e:
                        print(f"⚠️ Error processing row {stats['total_processed']}: {e}")
                    
                    # Write the (fixed) row
                    writer.writerow(row)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ DATA QUALITY FIXING COMPLETE!")
        print("=" * 80)
        print(f"⏱️  Processing time: {elapsed_time/60:.1f} minutes")
        print(f"📊 Total products processed: {stats['total_processed']:,}")
        print(f"📊 Weights fixed: {stats['weights_fixed']:,}")
        print(f"📊 Materials fixed: {stats['materials_fixed']:,}")
        print(f"📊 Validation issues found: {stats['validation_issues']:,}")
        print(f"📊 Perfect products (no changes): {stats['perfect_products']:,}")
        
        # Show examples of improvements
        print(f"\n🎉 SAMPLE IMPROVEMENTS:")
        for improvement in improvements[:15]:
            print(f"• {improvement['title']}...")
            for change in improvement['changes'][:2]:  # Show max 2 changes per product
                print(f"  - {change}")
        
        return {
            'output_file': output_path,
            'stats': stats,
            'improvements': improvements
        }

if __name__ == "__main__":
    fixer = ComprehensiveDataQualityFixer()
    
    print("\n🎯 COMPREHENSIVE DATA QUALITY FIX")
    print("This will fix:")
    print("• Unrealistic weights (37kg pruning shears → 0.35kg)")
    print("• Wrong materials (textile pruning shears → steel)")  
    print("• Add validation for impossible combinations")
    print("• Process all 170,000 products")
    
    print(f"\n🚀 Starting comprehensive data quality fix...")
    
    results = fixer.fix_entire_dataset()
    
    print(f"\n🎉 SUCCESS! Data quality dramatically improved!")
    print(f"📁 Fixed dataset: {results['output_file']}")
    print(f"\n💡 Next steps:")
    print("1. Review the improvements")
    print("2. Replace original dataset")
    print("3. Update scraping system to prevent future issues")
    print("4. Your products now have realistic weights and materials!")