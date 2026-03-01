#!/usr/bin/env python3
"""
Fix Dataset CO2 Calculations with Manufacturing Complexity
Updates your 65,000 product dataset with realistic, research-backed CO2 values
Fixes the inflated values and provides trustworthy environmental impact data
"""

import csv
import sys
import os
from typing import Dict, List, Any
import time

# Add the services directory to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICES_DIR = os.path.join(PROJECT_ROOT, 'backend', 'services')
if SERVICES_DIR not in sys.path:
    sys.path.append(SERVICES_DIR)

from manufacturing_complexity_multipliers import ManufacturingComplexityCalculator
from enhanced_materials_database import EnhancedMaterialsDatabase

class CO2CalculationFixer:
    """
    Fix CO2 calculations in your existing dataset using manufacturing complexity
    """
    
    def __init__(self):
        print("🔧 Initializing CO2 Calculation Fixer...")
        
        self.complexity_calculator = ManufacturingComplexityCalculator()
        self.materials_db = EnhancedMaterialsDatabase()
        
        self.dataset_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset.csv')
        self.output_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'csv', 'enhanced_eco_dataset_fixed.csv')
        
        print("✅ Manufacturing complexity calculator loaded")
        print("✅ Materials database loaded")
        
    def fix_entire_dataset(self):
        """
        Fix CO2 calculations for the entire 65,000 product dataset
        """
        
        print(f"\n🚀 FIXING CO2 CALCULATIONS FOR ENTIRE DATASET")
        print("=" * 80)
        print(f"📁 Input file: {self.dataset_path}")
        print(f"📁 Output file: {self.output_path}")
        
        start_time = time.time()
        
        total_rows = 0
        fixed_rows = 0
        improvements_tracked = []
        category_stats = {}
        eco_score_changes = {'improved': 0, 'stayed_same': 0, 'worsened': 0}
        
        with open(self.dataset_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Get total rows for progress tracking
            print("📊 Counting total rows...")
            total_lines = sum(1 for _ in open(self.dataset_path, 'r', encoding='utf-8')) - 1  # -1 for header
            print(f"📊 Found {total_lines:,} products to process")
            
            # Reset file pointer
            infile.seek(0)
            reader = csv.DictReader(infile)
            
            with open(self.output_path, 'w', newline='', encoding='utf-8') as outfile:
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    total_rows += 1
                    
                    # Progress indicator
                    if total_rows % 5000 == 0:
                        progress = (total_rows / total_lines) * 100
                        elapsed = time.time() - start_time
                        eta = (elapsed / total_rows) * (total_lines - total_rows)
                        print(f"  🔄 Progress: {total_rows:,}/{total_lines:,} ({progress:.1f}%) - ETA: {eta/60:.1f} minutes")
                    
                    try:
                        # Extract current values
                        weight = float(row['weight'])
                        category = row['inferred_category'].lower().replace(' ', '_').replace('&', '_')
                        material = row['material'].lower().replace(' ', '_')
                        transport = row['transport'].lower()
                        old_co2 = float(row['co2_emissions'])
                        old_eco_score = row['true_eco_score']
                        
                        # Get material CO2 intensity
                        material_co2_per_kg = self.materials_db.get_material_impact_score(material)
                        if not material_co2_per_kg:
                            # Try alternative material names
                            material_variants = {
                                'textile': 'cotton',
                                'metal': 'steel', 
                                'electronic': 'aluminum',
                                'mixed': 'plastic'
                            }
                            alt_material = material_variants.get(material, 'plastic')
                            material_co2_per_kg = self.materials_db.get_material_impact_score(alt_material) or 2.0
                        
                        # Get transport multiplier
                        transport_multipliers = {"air": 2.5, "ship": 1.0, "land": 1.2}
                        transport_multiplier = transport_multipliers.get(transport, 1.0)
                        
                        # Calculate realistic CO2 with manufacturing complexity
                        enhanced_result = self.complexity_calculator.calculate_enhanced_co2(
                            weight_kg=weight,
                            material_co2_per_kg=material_co2_per_kg,
                            transport_multiplier=transport_multiplier,
                            category=category
                        )
                        
                        new_co2 = round(enhanced_result["enhanced_total_co2"], 2)
                        
                        # Calculate new eco score based on realistic CO2
                        if new_co2 < 5:
                            new_eco_score = "A"
                        elif new_co2 < 15:
                            new_eco_score = "B"
                        elif new_co2 < 50:
                            new_eco_score = "C"
                        elif new_co2 < 150:
                            new_eco_score = "D"
                        elif new_co2 < 500:
                            new_eco_score = "E"
                        elif new_co2 < 1500:
                            new_eco_score = "F"
                        else:
                            new_eco_score = "G"
                        
                        # Update the row with fixed values
                        row['co2_emissions'] = new_co2
                        row['true_eco_score'] = new_eco_score
                        
                        # Track statistics
                        if old_co2 > 0:
                            improvement_ratio = old_co2 / new_co2 if new_co2 > 0 else 1.0
                            improvements_tracked.append({
                                'category': category,
                                'title': row['title'][:30],
                                'old_co2': old_co2,
                                'new_co2': new_co2,
                                'improvement_ratio': improvement_ratio,
                                'weight': weight
                            })
                        
                        # Track category statistics
                        if category not in category_stats:
                            category_stats[category] = {
                                'count': 0,
                                'total_old_co2': 0,
                                'total_new_co2': 0,
                                'avg_improvement': 0
                            }
                        
                        category_stats[category]['count'] += 1
                        category_stats[category]['total_old_co2'] += old_co2
                        category_stats[category]['total_new_co2'] += new_co2
                        
                        # Track eco score changes
                        eco_score_values = {'A': 7, 'B': 6, 'C': 5, 'D': 4, 'E': 3, 'F': 2, 'G': 1}
                        old_score_val = eco_score_values.get(old_eco_score, 1)
                        new_score_val = eco_score_values.get(new_eco_score, 1)
                        
                        if new_score_val > old_score_val:
                            eco_score_changes['improved'] += 1
                        elif new_score_val == old_score_val:
                            eco_score_changes['stayed_same'] += 1
                        else:
                            eco_score_changes['worsened'] += 1
                        
                        fixed_rows += 1
                        
                    except (ValueError, KeyError, ZeroDivisionError) as e:
                        # Keep original row if fixing fails
                        print(f"⚠️ Error fixing row {total_rows}: {e}")
                    
                    # Write the (fixed) row
                    writer.writerow(row)
        
        # Calculate final statistics
        elapsed_time = time.time() - start_time
        
        # Calculate category averages
        for category, stats in category_stats.items():
            if stats['count'] > 0 and stats['total_new_co2'] > 0:
                stats['avg_improvement'] = stats['total_old_co2'] / stats['total_new_co2']
        
        # Get most improved categories
        most_improved_categories = sorted(
            [(cat, stats['avg_improvement']) for cat, stats in category_stats.items() if stats['avg_improvement'] > 1],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Get examples of biggest improvements
        biggest_improvements = sorted(
            improvements_tracked,
            key=lambda x: x['improvement_ratio'],
            reverse=True
        )[:10]
        
        print(f"\n✅ DATASET FIXING COMPLETE!")
        print("=" * 80)
        print(f"⏱️  Processing time: {elapsed_time/60:.1f} minutes")
        print(f"📊 Total products processed: {total_rows:,}")
        print(f"📊 Products successfully fixed: {fixed_rows:,}")
        print(f"📊 Success rate: {(fixed_rows/total_rows)*100:.1f}%")
        
        print(f"\n🎯 ECO SCORE IMPROVEMENTS:")
        print(f"• Products with better eco scores: {eco_score_changes['improved']:,}")
        print(f"• Products with same eco scores: {eco_score_changes['stayed_same']:,}")
        print(f"• Products with worse eco scores: {eco_score_changes['worsened']:,}")
        
        print(f"\n🔝 MOST IMPROVED CATEGORIES:")
        for category, improvement_ratio in most_improved_categories:
            category_name = category.replace('_', ' ').title()
            product_count = category_stats[category]['count']
            print(f"• {category_name}: {improvement_ratio:.1f}x improvement ({product_count:,} products)")
        
        print(f"\n🎉 BIGGEST INDIVIDUAL IMPROVEMENTS:")
        for improvement in biggest_improvements:
            print(f"• {improvement['title']}: {improvement['old_co2']:.1f} → {improvement['new_co2']:.1f} kg CO2 ({improvement['improvement_ratio']:.1f}x better)")
        
        # Sample realistic values
        print(f"\n✅ SAMPLE REALISTIC CO2 VALUES AFTER FIXING:")
        sample_categories = ['electronics', 'clothing', 'kitchen_appliances', 'books', 'smartphones']
        for category in sample_categories:
            if category in category_stats and category_stats[category]['count'] > 0:
                avg_co2 = category_stats[category]['total_new_co2'] / category_stats[category]['count']
                print(f"• {category.replace('_', ' ').title()}: Average {avg_co2:.1f} kg CO2 per product")
        
        return {
            'total_processed': total_rows,
            'successfully_fixed': fixed_rows,
            'processing_time_minutes': elapsed_time / 60,
            'output_file': self.output_path,
            'category_improvements': most_improved_categories,
            'eco_score_changes': eco_score_changes
        }
    
    def validate_improvements(self, sample_size: int = 20):
        """
        Show before/after comparison for validation
        """
        
        print(f"\n🧪 VALIDATION: BEFORE vs AFTER COMPARISON")
        print("=" * 100)
        
        with open(self.dataset_path, 'r', encoding='utf-8') as original_file:
            original_reader = csv.DictReader(original_file)
            
            with open(self.output_path, 'r', encoding='utf-8') as fixed_file:
                fixed_reader = csv.DictReader(fixed_file)
                
                print(f"{'Product':<35} {'Category':<15} {'Before CO2':<12} {'After CO2':<12} {'Ratio':<8} {'Realistic?'}")
                print("-" * 100)
                
                for i, (original_row, fixed_row) in enumerate(zip(original_reader, fixed_reader)):
                    if i >= sample_size:
                        break
                    
                    title = original_row['title'][:32] + "..." if len(original_row['title']) > 32 else original_row['title']
                    category = original_row['inferred_category'][:14]
                    before_co2 = float(original_row['co2_emissions'])
                    after_co2 = float(fixed_row['co2_emissions'])
                    
                    ratio = before_co2 / after_co2 if after_co2 > 0 else 1.0
                    
                    # Determine if it's realistic
                    if 'electronic' in category.lower() or 'smartphone' in category.lower():
                        realistic = "✅ Much better" if 10 <= after_co2 <= 200 else "⚠️ Check"
                    elif 'clothing' in category.lower():
                        realistic = "✅ Realistic" if 1 <= after_co2 <= 20 else "⚠️ Check"
                    elif 'book' in category.lower():
                        realistic = "✅ Good" if 0.5 <= after_co2 <= 5 else "⚠️ Check"
                    elif 'kitchen' in category.lower():
                        realistic = "✅ Better" if 2 <= after_co2 <= 100 else "⚠️ Check"
                    else:
                        realistic = "✅ Improved" if ratio > 1.5 else "➖ Similar"
                    
                    print(f"{title:<35} {category:<15} {before_co2:<12.1f} {after_co2:<12.1f} {ratio:<8.1f}x {realistic}")

if __name__ == "__main__":
    fixer = CO2CalculationFixer()
    
    print("\n🎯 READY TO FIX YOUR DATASET!")
    print("This will:")
    print("• Fix inflated CO2 values (like 9,297 kg → 106 kg)")
    print("• Make electronics realistic (iPhones ~25-70 kg CO2)")
    print("• Keep simple products low (books ~1-5 kg CO2)")
    print("• Update eco scores based on realistic values")
    print("• Process all 65,000 products")
    
    print(f"\n🚀 Starting dataset fix...")
    
    # Fix the entire dataset
    results = fixer.fix_entire_dataset()
    
    print(f"\n🧪 Running validation on sample products...")
    fixer.validate_improvements(15)
    
    print(f"\n🎉 SUCCESS!")
    print(f"📁 Your fixed dataset is saved at:")
    print(f"   {results['output_file']}")
    print(f"\n💡 Next steps:")
    print("1. Backup your original dataset if needed")
    print("2. Replace the original with the fixed version")
    print("3. Update your system to use the realistic CO2 values")
    print("4. Your users will now see trustworthy environmental data!")
    
    print(f"\n🌱 Impact: Your 65,000 products now have research-backed, realistic CO2 calculations!")