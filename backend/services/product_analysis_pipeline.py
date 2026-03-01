#!/usr/bin/env python3
"""
Product Analysis Pipeline - How We Calculate All Product Fields
Comprehensive explanation and implementation of how each field is derived
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
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

class ProductAnalysisPipeline:
    """
    Complete pipeline showing how we extract and calculate all product fields
    from a simple product title and basic information
    """
    
    def __init__(self):
        print("🔧 Initializing Product Analysis Pipeline...")
        
        # Load our enhanced databases
        self.categories_db = AmazonProductCategories()
        self.materials_db = EnhancedMaterialsDatabase()
        self.brands_db = AmazonFocusedBrandDatabase()
        
        # Field calculation methods mapped to their explanations
        self.field_calculators = {
            'title': self._explain_title,
            'material': self._explain_material,
            'weight': self._explain_weight,
            'transport': self._explain_transport,
            'recyclability': self._explain_recyclability,
            'true_eco_score': self._explain_eco_score,
            'co2_emissions': self._explain_co2_emissions,
            'origin': self._explain_origin,
            'material_confidence': self._explain_material_confidence,
            'secondary_materials': self._explain_secondary_materials,
            'packaging_type': self._explain_packaging_type,
            'packaging_materials': self._explain_packaging_materials,
            'packaging_weight_ratio': self._explain_packaging_weight_ratio,
            'inferred_category': self._explain_inferred_category,
            'origin_confidence': self._explain_origin_confidence,
            'estimated_lifespan_years': self._explain_lifespan,
            'repairability_score': self._explain_repairability_score,
            'size_category': self._explain_size_category,
            'quality_level': self._explain_quality_level,
            'is_eco_labeled': self._explain_eco_labeled,
            'is_amazon_choice': self._explain_amazon_choice,
            'pack_size': self._explain_pack_size,
            'estimated_volume_l': self._explain_volume,
            'weight_confidence': self._explain_weight_confidence
        }
        
        print("✅ Pipeline initialized with all field calculators")

    def analyze_product_step_by_step(self, product_title: str, additional_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Take a product title and show step-by-step how we calculate each field
        """
        print(f"\n🔍 ANALYZING PRODUCT: '{product_title}'")
        print("=" * 80)
        
        if additional_info is None:
            additional_info = {}
        
        analysis_result = {
            'input': {
                'title': product_title,
                'additional_info': additional_info
            },
            'field_calculations': {},
            'final_product': {}
        }
        
        # Step 1: Extract basic information
        extracted_info = self._extract_basic_info(product_title)
        print(f"📋 EXTRACTED INFO: {extracted_info}")
        
        # Step 2: Calculate each field with detailed explanation
        for field_name, calculator_method in self.field_calculators.items():
            try:
                calculation_result = calculator_method(product_title, extracted_info, additional_info)
                analysis_result['field_calculations'][field_name] = calculation_result
                analysis_result['final_product'][field_name] = calculation_result['value']
                
                print(f"\n📊 {field_name.upper()}:")
                print(f"   Value: {calculation_result['value']}")
                print(f"   Method: {calculation_result['method']}")
                print(f"   Confidence: {calculation_result.get('confidence', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Error calculating {field_name}: {e}")
                analysis_result['field_calculations'][field_name] = {
                    'value': 'Error',
                    'method': 'Failed calculation',
                    'error': str(e)
                }
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        
        return analysis_result

    def _extract_basic_info(self, product_title: str) -> Dict[str, Any]:
        """
        Extract basic information from product title using pattern matching
        """
        info = {
            'detected_brand': None,
            'detected_category': None,
            'detected_materials': [],
            'detected_specs': [],
            'product_keywords': []
        }
        
        title_lower = product_title.lower()
        
        # Detect brand
        for brand_name, brand_data in self.brands_db.amazon_brands.items():
            if brand_name.lower() in title_lower:
                info['detected_brand'] = brand_name
                break
        
        # Detect category from keywords
        category_keywords = {
            'smartphones': ['iphone', 'galaxy', 'pixel', 'phone', 'smartphone'],
            'laptops': ['macbook', 'thinkpad', 'laptop', 'notebook'],
            'headphones': ['headphones', 'earbuds', 'airpods', 'headset'],
            'casual_clothing': ['shirt', 'jeans', 'hoodie', 't-shirt', 'polo'],
            'kitchen_appliances': ['blender', 'coffee maker', 'mixer', 'toaster'],
            'skincare': ['moisturizer', 'cleanser', 'serum', 'cream']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                info['detected_category'] = category
                break
        
        # Extract specifications
        specs = re.findall(r'\b\d+(?:gb|kg|ml|oz|inch|")\b', title_lower)
        info['detected_specs'] = specs
        
        # Extract general keywords
        words = re.findall(r'\b[a-zA-Z]+\b', product_title)
        info['product_keywords'] = [w.lower() for w in words if len(w) > 2]
        
        return info

    # Individual field calculation methods with detailed explanations

    def _explain_title(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we handle the product title"""
        return {
            'value': title,
            'method': 'Direct input from user or scraping',
            'confidence': 'high',
            'explanation': 'Title is the primary input - either provided by user search or scraped from Amazon product page'
        }

    def _explain_material(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine the primary material"""
        
        # Method 1: Category-based material inference
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                primary_material = category_data['primary_material']
                return {
                    'value': primary_material.replace('_', ' ').title(),
                    'method': f'Inferred from category "{category}" - most common material for this product type',
                    'confidence': 'high',
                    'explanation': f'Based on analysis of {category} products, {primary_material} is the most common primary material'
                }
        
        # Method 2: Title keyword detection
        material_keywords = {
            'aluminum': ['aluminum', 'aluminium', 'metal'],
            'plastic': ['plastic', 'polymer'],
            'cotton': ['cotton', '100% cotton'],
            'stainless_steel': ['stainless steel', 'steel'],
            'glass': ['glass', 'tempered glass']
        }
        
        title_lower = title.lower()
        for material, keywords in material_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return {
                    'value': material.replace('_', ' ').title(),
                    'method': f'Detected from title keywords: {keywords}',
                    'confidence': 'medium',
                    'explanation': 'Material explicitly mentioned in product title'
                }
        
        # Method 3: Default fallback
        return {
            'value': 'Mixed',
            'method': 'Default fallback when material cannot be determined',
            'confidence': 'low',
            'explanation': 'No clear material indicators found, using generic "Mixed" classification'
        }

    def _explain_weight(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we estimate product weight"""
        
        # Method 1: Explicit weight from title or specs
        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|pounds?|lbs?|g|grams?)', title.lower())
        if weight_match:
            weight_value = float(weight_match.group(1))
            unit = weight_match.group(0).split()[-1]
            
            # Convert to kg if needed
            if unit in ['g', 'grams', 'gram']:
                weight_value = weight_value / 1000
            elif unit in ['lbs', 'pounds', 'pound']:
                weight_value = weight_value * 0.453592
            
            return {
                'value': round(weight_value, 2),
                'method': f'Extracted from title: "{weight_match.group(0)}"',
                'confidence': 'very_high',
                'explanation': 'Weight explicitly stated in product title or specifications'
            }
        
        # Method 2: Category-based estimation
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                avg_weight = category_data.get('avg_weight_kg', 1.0)
                weight_range = category_data.get('weight_range', [0.1, 2.0])
                
                return {
                    'value': avg_weight,
                    'method': f'Category average for {category}: {avg_weight}kg (range: {weight_range[0]}-{weight_range[1]}kg)',
                    'confidence': 'medium',
                    'explanation': f'Based on statistical analysis of {category} products from our database'
                }
        
        # Method 3: Size-based estimation
        if any(word in title.lower() for word in ['mini', 'small', 'compact']):
            return {
                'value': 0.3,
                'method': 'Size keyword detection: small/mini products typically ~0.3kg',
                'confidence': 'low',
                'explanation': 'Estimated based on size descriptors in title'
            }
        elif any(word in title.lower() for word in ['large', 'big', 'jumbo']):
            return {
                'value': 2.5,
                'method': 'Size keyword detection: large products typically ~2.5kg',
                'confidence': 'low',
                'explanation': 'Estimated based on size descriptors in title'
            }
        
        return {
            'value': 1.0,
            'method': 'Default average weight when no other indicators available',
            'confidence': 'very_low',
            'explanation': 'Fallback estimate based on general product average'
        }

    def _explain_transport(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine shipping method"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                transport_method = category_data.get('transport_method', 'ship')
                
                transport_explanations = {
                    'air': 'High-value, time-sensitive electronics typically shipped by air',
                    'ship': 'Most cost-effective for non-urgent items, standard for most Amazon products',
                    'land': 'Heavy/bulky items within same continent, furniture and appliances'
                }
                
                return {
                    'value': transport_method.title(),
                    'method': f'Category-based determination for {category}',
                    'confidence': 'high',
                    'explanation': transport_explanations.get(transport_method, 'Standard shipping method for this category')
                }
        
        # Default logic based on keywords
        if any(word in title.lower() for word in ['iphone', 'samsung', 'apple', 'urgent']):
            return {
                'value': 'Air',
                'method': 'High-value electronics typically use air transport',
                'confidence': 'medium',
                'explanation': 'Premium electronics prioritize speed over cost for shipping'
            }
        
        return {
            'value': 'Ship',
            'method': 'Default shipping method for most Amazon products',
            'confidence': 'medium',
            'explanation': 'Sea shipping is most common for international Amazon deliveries'
        }

    def _explain_recyclability(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess recyclability"""
        
        # Get material-based recyclability
        material_result = self._explain_material(title, extracted_info, additional_info)
        material = material_result['value'].lower().replace(' ', '_')
        
        material_data = self.materials_db.get_material_properties(material)
        if material_data:
            recyclability = material_data.get('recyclability', 'medium')
            
            recyclability_explanations = {
                'very_high': 'Material is easily recyclable with existing infrastructure (metals, glass)',
                'high': 'Recyclable with good success rates (some plastics, paper)',
                'medium': 'Limited recyclability, requires specialized facilities',
                'low': 'Difficult to recycle, often goes to landfill (mixed materials, thermosets)'
            }
            
            return {
                'value': recyclability.replace('_', ' ').title(),
                'method': f'Based on material properties of {material}',
                'confidence': 'high',
                'explanation': recyclability_explanations.get(recyclability, 'Standard recyclability assessment')
            }
        
        return {
            'value': 'Medium',
            'method': 'Default recyclability when material properties unknown',
            'confidence': 'low',
            'explanation': 'Conservative estimate for unknown material composition'
        }

    def _explain_co2_emissions(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we calculate CO2 emissions"""
        
        # Get weight and material
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        material_result = self._explain_material(title, extracted_info, additional_info)
        transport_result = self._explain_transport(title, extracted_info, additional_info)
        
        weight = weight_result['value']
        material = material_result['value'].lower().replace(' ', '_')
        transport = transport_result['value'].lower()
        
        # Get material CO2 intensity (kg CO2 per kg material)
        co2_intensity = self.materials_db.get_material_impact_score(material)
        if not co2_intensity:
            co2_intensity = 2.0  # Default
        
        # Calculate base emissions from material
        base_co2 = weight * co2_intensity
        
        # Add transport multiplier
        transport_multipliers = {
            'air': 2.5,    # Air freight has high emissions
            'ship': 1.0,   # Baseline (most efficient per kg)
            'land': 1.2    # Truck transport
        }
        
        transport_multiplier = transport_multipliers.get(transport, 1.0)
        total_co2 = base_co2 * transport_multiplier
        
        return {
            'value': round(total_co2, 2),
            'method': f'({weight}kg × {co2_intensity} kg CO2/kg material) × {transport_multiplier} transport multiplier',
            'confidence': 'high',
            'explanation': f'Material production: {round(base_co2, 2)} kg CO2, Transport factor: {transport_multiplier}x for {transport}'
        }

    def _explain_eco_score(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we calculate the eco-score grade"""
        
        co2_result = self._explain_co2_emissions(title, extracted_info, additional_info)
        co2_emissions = co2_result['value']
        
        # Eco score bands based on CO2 emissions
        if co2_emissions < 50:
            score = "A"
            explanation = "Excellent: Very low carbon footprint"
        elif co2_emissions < 200:
            score = "B"
            explanation = "Good: Below average emissions"
        elif co2_emissions < 500:
            score = "C"
            explanation = "Fair: Average environmental impact"
        elif co2_emissions < 1000:
            score = "D"
            explanation = "Below average: Higher than typical emissions"
        elif co2_emissions < 2000:
            score = "E"
            explanation = "Poor: High environmental impact"
        elif co2_emissions < 5000:
            score = "F"
            explanation = "Very poor: Very high emissions"
        else:
            score = "G"
            explanation = "Extremely poor: Exceptionally high carbon footprint"
        
        return {
            'value': score,
            'method': f'Banded scoring based on {co2_emissions} kg CO2 emissions',
            'confidence': 'high',
            'explanation': explanation
        }

    def _explain_origin(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine manufacturing origin"""
        
        # Method 1: Brand-based origin
        brand = extracted_info.get('detected_brand')
        if brand:
            brand_info = self.brands_db.get_brand_info(brand)
            if brand_info and brand_info.get('origin', {}).get('country') != 'Unknown':
                country = brand_info['origin']['country']
                return {
                    'value': country,
                    'method': f'Brand "{brand}" headquarters/primary manufacturing location',
                    'confidence': 'high',
                    'explanation': f'{brand} is primarily based in {country}'
                }
        
        # Method 2: Category-based manufacturing patterns
        category = extracted_info.get('detected_category')
        category_origins = {
            'smartphones': ['China', 'South Korea', 'Taiwan'],
            'clothing': ['China', 'Bangladesh', 'Vietnam'],
            'electronics': ['China', 'Japan', 'South Korea'],
            'furniture': ['China', 'Germany', 'USA']
        }
        
        if category and category in category_origins:
            likely_origins = category_origins[category]
            primary_origin = likely_origins[0]  # Most common
            
            return {
                'value': primary_origin,
                'method': f'Category-based: {category} products are typically manufactured in {", ".join(likely_origins)}',
                'confidence': 'medium',
                'explanation': f'Statistical analysis shows {primary_origin} produces majority of {category} products'
            }
        
        return {
            'value': 'China',
            'method': 'Default: China manufactures ~40% of global consumer goods',
            'confidence': 'low',
            'explanation': 'Statistically most likely origin when no other indicators available'
        }

    def _explain_material_confidence(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess confidence in material detection"""
        
        material_result = self._explain_material(title, extracted_info, additional_info)
        material_confidence = material_result.get('confidence', 'low')
        
        confidence_scores = {
            'very_high': 0.95,  # Explicitly stated in title
            'high': 0.85,       # Category-based with strong correlation
            'medium': 0.70,     # Keyword detection
            'low': 0.50,        # Default fallback
            'very_low': 0.30    # Pure guess
        }
        
        score = confidence_scores.get(material_confidence, 0.50)
        
        return {
            'value': score,
            'method': f'Based on material detection method confidence: {material_confidence}',
            'confidence': material_confidence,
            'explanation': f'Higher scores indicate more reliable material identification (0.3-0.95 scale)'
        }

    def _explain_secondary_materials(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we identify secondary materials"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                all_materials = category_data.get('common_materials', [])
                secondary = all_materials[1:4] if len(all_materials) > 1 else []
                
                return {
                    'value': secondary,
                    'method': f'Category analysis: {category} products typically contain these secondary materials',
                    'confidence': 'medium',
                    'explanation': f'Based on material composition analysis of {category} products'
                }
        
        return {
            'value': [],
            'method': 'No secondary materials identified',
            'confidence': 'low',
            'explanation': 'Insufficient information to determine secondary material composition'
        }

    def _explain_packaging_type(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine packaging type"""
        
        category = extracted_info.get('detected_category')
        
        # Category-based packaging patterns
        packaging_patterns = {
            'smartphones': 'box',
            'clothing': 'bag',
            'skincare': 'bottle',
            'supplements': 'bottle',
            'books': 'envelope',
            'electronics': 'box'
        }
        
        # Size-based patterns
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        weight = weight_result['value']
        
        if weight > 5.0:
            packaging_type = 'box'
            method = f'Heavy items ({weight}kg) typically use box packaging'
        elif any(word in title.lower() for word in ['cream', 'lotion', 'liquid', 'shampoo']):
            packaging_type = 'bottle'
            method = 'Liquid products detected, bottle packaging assumed'
        elif category and category in packaging_patterns:
            packaging_type = packaging_patterns[category]
            method = f'Standard packaging for {category} products'
        else:
            packaging_type = 'box'
            method = 'Default packaging type for most products'
        
        return {
            'value': packaging_type,
            'method': method,
            'confidence': 'medium',
            'explanation': f'Packaging type optimized for product protection and shipping efficiency'
        }

    def _explain_packaging_materials(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine packaging materials"""
        
        packaging_result = self._explain_packaging_type(title, extracted_info, additional_info)
        packaging_type = packaging_result['value']
        
        material_combinations = {
            'box': ['cardboard', 'plastic'],
            'bottle': ['plastic', 'glass'],
            'bag': ['plastic', 'paper'],
            'tube': ['plastic', 'aluminum'],
            'envelope': ['paper', 'plastic']
        }
        
        materials = material_combinations.get(packaging_type, ['cardboard', 'plastic'])
        
        return {
            'value': materials,
            'method': f'Standard material combination for {packaging_type} packaging',
            'confidence': 'high',
            'explanation': f'{packaging_type.title()} packaging typically uses {" and ".join(materials)} for optimal protection'
        }

    def _explain_packaging_weight_ratio(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we estimate packaging weight ratio"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                ratio = category_data.get('packaging_weight_ratio', 0.15)
                return {
                    'value': ratio,
                    'method': f'Category average for {category}: {ratio:.0%} of product weight',
                    'confidence': 'medium',
                    'explanation': f'Based on packaging efficiency analysis for {category} products'
                }
        
        # Weight-based estimation
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        weight = weight_result['value']
        
        if weight < 0.5:
            ratio = 0.25  # Small items need proportionally more packaging
        elif weight > 10:
            ratio = 0.08  # Large items have packaging efficiency
        else:
            ratio = 0.15  # Standard ratio
        
        return {
            'value': ratio,
            'method': f'Weight-based estimation: {weight}kg products typically have {ratio:.0%} packaging ratio',
            'confidence': 'medium',
            'explanation': 'Packaging efficiency scales with product size and fragility'
        }

    def _explain_inferred_category(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we categorize products"""
        
        category = extracted_info.get('detected_category')
        if category:
            return {
                'value': category.replace('_', ' '),
                'method': f'Keyword matching detected: {category}',
                'confidence': 'high',
                'explanation': f'Product title contains clear indicators for {category} category'
            }
        
        # Fallback categorization based on brand
        brand = extracted_info.get('detected_brand')
        if brand:
            brand_info = self.brands_db.get_brand_info(brand)
            if brand_info:
                categories = brand_info.get('amazon_categories', [])
                if categories:
                    primary_category = categories[0].lower().replace(' ', '_')
                    return {
                        'value': primary_category.replace('_', ' '),
                        'method': f'Brand-based: {brand} primarily sells {primary_category} products',
                        'confidence': 'medium',
                        'explanation': f'{brand} is categorized under {categories[0]} on Amazon'
                    }
        
        return {
            'value': 'general merchandise',
            'method': 'Default category when classification unclear',
            'confidence': 'low',
            'explanation': 'Insufficient indicators for specific category classification'
        }

    def _explain_origin_confidence(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess confidence in origin determination"""
        
        origin_result = self._explain_origin(title, extracted_info, additional_info)
        origin_confidence = origin_result.get('confidence', 'low')
        
        confidence_scores = {
            'high': 0.90,     # Brand-based with verified info
            'medium': 0.75,   # Category-based statistical
            'low': 0.55       # Default assumption
        }
        
        score = confidence_scores.get(origin_confidence, 0.55)
        
        return {
            'value': round(score, 2),
            'method': f'Based on origin detection method reliability: {origin_confidence}',
            'confidence': origin_confidence,
            'explanation': 'Higher values indicate more reliable origin identification'
        }

    def _explain_lifespan(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we estimate product lifespan"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                lifespan = category_data.get('estimated_lifespan_years', 5)
                return {
                    'value': lifespan,
                    'method': f'Category average: {category} products typically last {lifespan} years',
                    'confidence': 'high',
                    'explanation': f'Based on consumer usage patterns and durability studies for {category}'
                }
        
        # Default lifespans by product type keywords
        lifespan_keywords = {
            15: ['furniture', 'appliance'],
            10: ['tool', 'equipment'],
            5: ['electronic', 'gadget'],
            3: ['clothing', 'fashion'],
            1: ['consumable', 'beauty', 'food']
        }
        
        title_lower = title.lower()
        for years, keywords in lifespan_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return {
                    'value': years,
                    'method': f'Keyword-based estimation: {keywords} products typically last {years} years',
                    'confidence': 'medium',
                    'explanation': f'Industry standard lifespan for products containing: {keywords}'
                }
        
        return {
            'value': 5,
            'method': 'Default consumer product lifespan',
            'confidence': 'low',
            'explanation': 'Average lifespan when specific category unknown'
        }

    def _explain_repairability_score(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess repairability (1-10 scale)"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                score = category_data.get('repairability_score', 5)
                
                score_explanations = {
                    1: 'Disposable/consumable - not designed for repair',
                    2: 'Very difficult - requires specialized tools/skills',
                    3: 'Difficult - limited repair options',
                    5: 'Moderate - some components can be replaced',
                    7: 'Good - designed with repair in mind',
                    9: 'Excellent - easily repairable by consumers'
                }
                
                explanation = score_explanations.get(score, 'Standard repairability for this category')
                
                return {
                    'value': score,
                    'method': f'Category-based assessment for {category}',
                    'confidence': 'medium',
                    'explanation': f'Score {score}/10: {explanation}'
                }
        
        return {
            'value': 5,
            'method': 'Default moderate repairability score',
            'confidence': 'low',
            'explanation': 'Average repairability when category unknown'
        }

    def _explain_size_category(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine size category"""
        
        category = extracted_info.get('detected_category')
        if category:
            category_data = self.categories_db.get_category_data(category)
            if category_data:
                size = category_data.get('size_category', 'medium')
                return {
                    'value': size,
                    'method': f'Category standard: {category} products are typically {size}',
                    'confidence': 'high',
                    'explanation': f'Based on dimensional analysis of {category} products'
                }
        
        # Weight-based size estimation
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        weight = weight_result['value']
        
        if weight < 0.5:
            size = 'small'
        elif weight < 5.0:
            size = 'medium'
        elif weight < 20.0:
            size = 'large'
        else:
            size = 'extra_large'
        
        return {
            'value': size,
            'method': f'Weight-based: {weight}kg indicates {size} size category',
            'confidence': 'medium',
            'explanation': f'Size categories: small(<0.5kg), medium(0.5-5kg), large(5-20kg), extra_large(>20kg)'
        }

    def _explain_quality_level(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess quality level"""
        
        # Brand-based quality assessment
        brand = extracted_info.get('detected_brand')
        if brand:
            premium_brands = ['apple', 'samsung', 'sony', 'nike', 'adidas', 'le_creuset']
            budget_brands = ['generic', 'basic', 'economy']
            
            if brand.lower() in premium_brands:
                return {
                    'value': 'premium',
                    'method': f'{brand} is recognized as a premium brand',
                    'confidence': 'high',
                    'explanation': f'{brand} products typically command premium pricing due to quality/brand value'
                }
            elif brand.lower() in budget_brands:
                return {
                    'value': 'budget',
                    'method': f'{brand} is positioned as a budget-friendly option',
                    'confidence': 'high',
                    'explanation': 'Budget brands focus on cost-effectiveness over premium features'
                }
        
        # Title keyword analysis
        title_lower = title.lower()
        if any(word in title_lower for word in ['premium', 'professional', 'pro', 'elite', 'luxury']):
            return {
                'value': 'premium',
                'method': 'Premium keywords detected in title',
                'confidence': 'medium',
                'explanation': 'Title contains indicators of premium positioning'
            }
        elif any(word in title_lower for word in ['basic', 'economy', 'budget', 'value']):
            return {
                'value': 'budget',
                'method': 'Budget keywords detected in title',
                'confidence': 'medium',
                'explanation': 'Title contains indicators of budget positioning'
            }
        
        return {
            'value': 'standard',
            'method': 'Default quality level - no clear premium/budget indicators',
            'confidence': 'low',
            'explanation': 'Standard quality assumed for mainstream products'
        }

    def _explain_eco_labeled(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine if product has eco labeling"""
        
        # Check for eco keywords in title
        eco_keywords = ['organic', 'eco', 'sustainable', 'recycled', 'green', 'bio', 'natural', 'environmentally friendly']
        title_lower = title.lower()
        
        found_keywords = [keyword for keyword in eco_keywords if keyword in title_lower]
        
        if found_keywords:
            return {
                'value': True,
                'method': f'Eco keywords detected: {found_keywords}',
                'confidence': 'high',
                'explanation': 'Product explicitly marketed with environmental benefits'
            }
        
        # Check eco score
        eco_score_result = self._explain_eco_score(title, extracted_info, additional_info)
        eco_score = eco_score_result['value']
        
        if eco_score in ['A', 'B']:
            return {
                'value': True,
                'method': f'High eco score ({eco_score}) suggests environmental certification',
                'confidence': 'medium',
                'explanation': 'Products with excellent environmental performance often have eco labels'
            }
        
        return {
            'value': False,
            'method': 'No eco indicators found in title or performance metrics',
            'confidence': 'medium',
            'explanation': 'Most products do not carry environmental certifications'
        }

    def _explain_amazon_choice(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we predict Amazon's Choice status"""
        
        # Check quality and popularity indicators
        quality_result = self._explain_quality_level(title, extracted_info, additional_info)
        quality = quality_result['value']
        
        brand = extracted_info.get('detected_brand')
        popular_brands = ['amazon_basics', 'apple', 'samsung', 'nike', 'adidas']
        
        # Amazon's Choice typically goes to:
        # 1. Well-reviewed, popular products
        # 2. Good value for money
        # 3. Fast shipping
        # 4. Amazon's own brands
        
        if brand and brand.lower() in ['amazon_basics', 'amazonbasics']:
            return {
                'value': True,
                'method': 'Amazon-owned brand products often get Amazon\'s Choice',
                'confidence': 'high',
                'explanation': 'Amazon promotes its own brands for customer satisfaction and margins'
            }
        
        if quality in ['standard', 'premium'] and brand and brand.lower() in popular_brands:
            return {
                'value': True,
                'method': f'Popular brand ({brand}) with {quality} quality level',
                'confidence': 'medium',
                'explanation': 'Combination of brand recognition and quality often leads to Amazon\'s Choice'
            }
        
        return {
            'value': False,
            'method': 'Amazon\'s Choice is selective - most products don\'t qualify',
            'confidence': 'medium',
            'explanation': 'Only ~5-10% of products receive Amazon\'s Choice designation'
        }

    def _explain_pack_size(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we determine pack size/quantity"""
        
        # Look for explicit pack size in title
        pack_patterns = [
            r'(\d+)[-\s]*pack',
            r'pack\s*of\s*(\d+)',
            r'(\d+)[-\s]*count',
            r'set\s*of\s*(\d+)',
            r'(\d+)[-\s]*piece'
        ]
        
        title_lower = title.lower()
        for pattern in pack_patterns:
            match = re.search(pattern, title_lower)
            if match:
                pack_size = int(match.group(1))
                return {
                    'value': pack_size,
                    'method': f'Explicit pack size found in title: "{match.group(0)}"',
                    'confidence': 'very_high',
                    'explanation': f'Product clearly states it contains {pack_size} units'
                }
        
        # Category-based pack size patterns
        category = extracted_info.get('detected_category')
        category_pack_patterns = {
            'supplements': 1,      # Usually single bottles
            'skincare': 1,         # Individual products
            'office_supplies': 12, # Often sold in dozens
            'clothing': 1,         # Individual items
            'electronics': 1       # Single devices
        }
        
        if category and category in category_pack_patterns:
            pack_size = category_pack_patterns[category]
            return {
                'value': pack_size,
                'method': f'Category default: {category} products typically sold as {pack_size} unit(s)',
                'confidence': 'medium',
                'explanation': f'Standard packaging for {category} based on consumer purchasing patterns'
            }
        
        return {
            'value': 1,
            'method': 'Default single unit when no pack indicators found',
            'confidence': 'medium',
            'explanation': 'Most products are sold individually unless explicitly stated otherwise'
        }

    def _explain_volume(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we estimate product volume"""
        
        # Method 1: Explicit volume from title
        volume_patterns = [
            r'(\d+(?:\.\d+)?)\s*l(?:iters?)?',
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*fl\s*oz'
        ]
        
        title_lower = title.lower()
        for pattern in volume_patterns:
            match = re.search(pattern, title_lower)
            if match:
                volume = float(match.group(1))
                unit = match.group(0).split()[-1]
                
                # Convert to liters
                if 'ml' in unit:
                    volume = volume / 1000
                elif 'oz' in unit:
                    volume = volume * 0.0295735  # fl oz to liters
                
                return {
                    'value': round(volume, 2),
                    'method': f'Explicit volume from title: "{match.group(0)}"',
                    'confidence': 'very_high',
                    'explanation': f'Volume directly stated in product specifications'
                }
        
        # Method 2: Weight and density estimation
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        size_result = self._explain_size_category(title, extracted_info, additional_info)
        
        weight = weight_result['value']
        size_category = size_result['value']
        
        # Estimated density by size category (kg/L)
        density_estimates = {
            'small': 0.8,       # Light, compact items
            'medium': 1.5,      # Average density
            'large': 1.0,       # Bulkier items
            'extra_large': 0.5  # Very bulky, light items
        }
        
        density = density_estimates.get(size_category, 1.0)
        estimated_volume = weight / density
        
        return {
            'value': round(max(0.01, estimated_volume), 2),  # Minimum 0.01L
            'method': f'Estimated from weight ({weight}kg) and size category ({size_category}): density ~{density}kg/L',
            'confidence': 'low',
            'explanation': f'Volume estimation based on typical density for {size_category} products'
        }

    def _explain_weight_confidence(self, title: str, extracted_info: Dict, additional_info: Dict) -> Dict[str, Any]:
        """How we assess confidence in weight estimation"""
        
        weight_result = self._explain_weight(title, extracted_info, additional_info)
        weight_confidence = weight_result.get('confidence', 'low')
        
        confidence_scores = {
            'very_high': 0.95,  # Explicitly stated
            'high': 0.80,       # Category average
            'medium': 0.65,     # Size-based estimation
            'low': 0.45,        # Keyword-based guess
            'very_low': 0.25    # Pure default
        }
        
        score = confidence_scores.get(weight_confidence, 0.45)
        
        return {
            'value': round(score, 2),
            'method': f'Based on weight estimation method reliability: {weight_confidence}',
            'confidence': weight_confidence,
            'explanation': f'{weight_confidence.replace("_", " ").title()} confidence in weight accuracy'
        }

    def demonstrate_full_pipeline(self):
        """Demonstrate the complete pipeline with example products"""
        
        print("\n🎯 COMPLETE PIPELINE DEMONSTRATION")
        print("=" * 100)
        
        example_products = [
            "Apple iPhone 14 Pro 128GB Space Black",
            "Nike Air Max 270 Running Shoes Men's Size 10",
            "KitchenAid Stand Mixer 5-Quart Artisan Series",
            "The Great Gatsby Paperback Book",
            "CeraVe Daily Moisturizing Lotion 473ml"
        ]
        
        for product in example_products:
            analysis = self.analyze_product_step_by_step(product)
            
            print(f"\n{'='*20} FINAL PRODUCT DATA {'='*20}")
            final_product = analysis['final_product']
            
            # Format for CSV output
            csv_row = []
            for field in ['title', 'material', 'weight', 'transport', 'recyclability', 
                         'true_eco_score', 'co2_emissions', 'origin', 'material_confidence',
                         'secondary_materials', 'packaging_type', 'packaging_materials',
                         'packaging_weight_ratio', 'inferred_category', 'origin_confidence',
                         'estimated_lifespan_years', 'repairability_score', 'size_category',
                         'quality_level', 'is_eco_labeled', 'is_amazon_choice', 'pack_size',
                         'estimated_volume_l', 'weight_confidence']:
                csv_row.append(str(final_product.get(field, '')))
            
            print("CSV FORMAT:")
            print(','.join(csv_row))
            print("\n" + "="*100)

if __name__ == "__main__":
    pipeline = ProductAnalysisPipeline()
    pipeline.demonstrate_full_pipeline()