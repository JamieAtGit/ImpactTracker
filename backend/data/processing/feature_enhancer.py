"""
Amazon Product Feature Enhancement for Environmental Impact Prediction
Extracts features from Amazon product titles, descriptions, and categories
Rule-based methods using only text processing and keyword matching
"""
import re
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

class AmazonFeatureEnhancer:
    """Enhances Amazon product data with additional features using rule-based methods"""
    
    def __init__(self):
        self.packaging_keywords = self._load_amazon_packaging_keywords()
        self.category_mappings = self._load_amazon_category_mappings()
        self.brand_origins = self._load_amazon_brand_origins()
        self.material_keywords = self._load_amazon_material_keywords()
        self.amazon_patterns = self._load_amazon_specific_patterns()
        
    def _load_amazon_packaging_keywords(self) -> Dict[str, List[str]]:
        """Amazon-specific packaging type detection from product titles"""
        return {
            'bottle': ['bottle', 'bottled', 'flask', '16 oz', '32 oz', 'water bottle'],
            'box': ['box', 'boxed', 'carton', 'package', 'pack of', 'set of'],
            'bag': ['bag', 'bagged', 'pouch', 'sachet', 'ziplock', 'resealable'],
            'tube': ['tube', 'squeeze', 'dispenser', 'pump', 'gel'],
            'can': ['can', 'canned', 'tin', 'aluminum can'],
            'jar': ['jar', 'pot', 'container', 'glass jar'],
            'wrap': ['wrapped', 'film', 'sealed', 'shrink wrap'],
            'blister': ['blister pack', 'individual', 'single use'],
            'case': ['case', 'protective case', 'cover', 'shell'],
            'multipack': ['multipack', 'bulk', '12 pack', '24 pack', 'family size']
        }
    
    def _load_amazon_category_mappings(self) -> Dict[str, Dict]:
        """Category-based feature defaults"""
        return {
            'electronics': {
                'typical_materials': ['Plastic', 'Aluminum', 'Steel'],
                'avg_lifespan_years': 5,
                'packaging_intensity': 'high',
                'transport_mode': 'Air',
                'recyclability': 'Medium'
            },
            'clothing': {
                'typical_materials': ['Cotton', 'Polyester', 'Other'],
                'avg_lifespan_years': 3,
                'packaging_intensity': 'low',
                'transport_mode': 'Ship',
                'recyclability': 'Low'
            },
            'food': {
                'typical_materials': ['Paper', 'Plastic', 'Glass'],
                'avg_lifespan_years': 0.1,  # Consumable
                'packaging_intensity': 'medium',
                'transport_mode': 'Ship',
                'recyclability': 'High'
            },
            'home_garden': {
                'typical_materials': ['Plastic', 'Wood', 'Steel'],
                'avg_lifespan_years': 8,
                'packaging_intensity': 'medium',
                'transport_mode': 'Ship',
                'recyclability': 'Medium'
            }
        }
    
    def _load_amazon_brand_origins(self) -> Dict[str, str]:
        """Brand to likely origin country mapping (add to your existing brand_locations.json)"""
        return {
            # Electronics
            'apple': 'China', 'samsung': 'South Korea', 'sony': 'Japan',
            'lg': 'South Korea', 'dell': 'China', 'hp': 'China',
            
            # Fashion
            'nike': 'Vietnam', 'adidas': 'Vietnam', 'zara': 'Spain',
            'h&m': 'Bangladesh', 'uniqlo': 'China',
            
            # Home goods
            'ikea': 'Sweden', 'philips': 'China', 'bosch': 'Germany',
            
            # Default assumptions by brand patterns
            'chinese_patterns': ['xiaomi', 'huawei', 'oppo', 'vivo'],
            'german_patterns': ['siemens', 'miele', 'braun'],
            'japanese_patterns': ['panasonic', 'toshiba', 'canon']
        }
    
    def _load_amazon_material_keywords(self) -> Dict[str, List[str]]:
        """Enhanced material detection from product text"""
        return {
            'Plastic': [
                'plastic', 'acrylic', 'polycarbonate', 'abs', 'pvc', 
                'polyethylene', 'polypropylene', 'nylon', 'synthetic'
            ],
            'Aluminum': [
                'aluminum', 'aluminium', 'alloy', 'anodized'
            ],
            'Steel': [
                'steel', 'stainless', 'metal', 'iron', 'chrome'
            ],
            'Glass': [
                'glass', 'crystal', 'tempered glass', 'borosilicate'
            ],
            'Wood': [
                'wood', 'wooden', 'bamboo', 'oak', 'pine', 'teak', 'mdf'
            ],
            'Cotton': [
                'cotton', '100% cotton', 'organic cotton', 'cotton blend'
            ],
            'Leather': [
                'leather', 'genuine leather', 'faux leather', 'suede'
            ],
            'Paper': [
                'paper', 'cardboard', 'paperboard', 'corrugated'
            ],
            'Foam': [
                'foam', 'memory foam', 'polyurethane', 'cushion'
            ]
        }
    
    def _load_amazon_specific_patterns(self) -> Dict[str, List[str]]:
        """Amazon-specific patterns for feature detection"""
        return {
            'size_indicators': [
                'large', 'medium', 'small', 'xl', 'xxl', 'compact', 'mini',
                'travel size', 'full size', 'king size', 'queen size'
            ],
            'quality_indicators': [
                'premium', 'professional', 'heavy duty', 'commercial grade',
                'budget', 'economy', 'basic', 'standard', 'deluxe'
            ],
            'eco_keywords': [
                'eco-friendly', 'sustainable', 'recyclable', 'biodegradable',
                'organic', 'natural', 'green', 'environmentally friendly'
            ],
            'amazon_choice': ['amazon choice', "amazon's choice", 'bestseller'],
            'multipack_indicators': [
                'pack of', 'set of', 'bulk', 'multipack', '12 pack', '24 pack',
                'family pack', 'value pack', 'economy pack'
            ]
        }
    
    def enhance_amazon_product_features(self, product_data: Dict) -> Dict:
        """Add enhanced features to Amazon product data"""
        enhanced = product_data.copy()
        
        title = product_data.get('title', '').lower()
        # Amazon products often don't have separate descriptions, use title primarily
        text = title
        
        # 1. Enhanced material detection
        enhanced['material_confidence'] = self._get_material_confidence(text, enhanced.get('material', 'Other'))
        enhanced['secondary_materials'] = self._detect_secondary_materials(text, enhanced.get('material', 'Other'))
        
        # 2. Packaging inference
        enhanced['packaging_type'] = self._infer_packaging_type(text)
        enhanced['packaging_materials'] = self._infer_packaging_materials(text, enhanced['packaging_type'])
        enhanced['packaging_weight_ratio'] = self._estimate_packaging_ratio(enhanced['packaging_type'])
        
        # 3. Category-based defaults
        category = self._classify_product_category(text)
        enhanced['inferred_category'] = category
        enhanced.update(self._apply_category_defaults(category, enhanced))
        
        # 4. Enhanced origin detection
        enhanced['origin_confidence'] = self._get_origin_confidence(
            enhanced.get('origin', 'Other'), 
            product_data.get('brand', '')
        )
        
        # 5. Durability and lifecycle features
        enhanced['estimated_lifespan_years'] = self._estimate_lifespan(text, category)
        enhanced['repairability_score'] = self._estimate_repairability(text, category)
        
        # 6. Amazon-specific features
        enhanced['size_category'] = self._detect_size_category(text)
        enhanced['quality_level'] = self._detect_quality_level(text)
        enhanced['is_eco_labeled'] = self._detect_eco_labeling(text)
        enhanced['is_amazon_choice'] = self._detect_amazon_choice(text)
        enhanced['pack_size'] = self._detect_pack_size(text)
        
        # 7. Weight and volume estimation improvements
        enhanced['estimated_volume_l'] = self._estimate_volume_from_amazon_title(text)
        enhanced['weight_confidence'] = self._assess_weight_confidence(text, enhanced.get('weight', 0))
        
        return enhanced
    
    def _get_material_confidence(self, text: str, current_material: str) -> float:
        """Assess confidence in material classification"""
        if current_material == 'Other':
            return 0.3
            
        keywords = self.material_keywords.get(current_material, [])
        matches = sum(1 for keyword in keywords if keyword in text)
        
        if matches >= 2:
            return 0.9
        elif matches == 1:
            return 0.7
        else:
            return 0.4
    
    def _detect_secondary_materials(self, text: str, primary_material: str) -> List[str]:
        """Find additional materials mentioned in text"""
        secondary = []
        
        for material, keywords in self.material_keywords.items():
            if material != primary_material:
                if any(keyword in text for keyword in keywords):
                    secondary.append(material)
        
        return secondary[:2]  # Limit to 2 secondary materials
    
    def _infer_packaging_type(self, text: str) -> str:
        """Detect packaging type from text"""
        for pkg_type, keywords in self.packaging_keywords.items():
            if any(keyword in text for keyword in keywords):
                return pkg_type
        
        return 'box'  # Default
    
    def _infer_packaging_materials(self, text: str, packaging_type: str) -> List[str]:
        """Guess packaging materials based on type and product"""
        packaging_defaults = {
            'bottle': ['Plastic', 'Glass'],
            'box': ['Cardboard', 'Paper'],
            'bag': ['Plastic', 'Paper'],
            'tube': ['Plastic', 'Aluminum'],
            'can': ['Aluminum', 'Steel'],
            'jar': ['Glass', 'Plastic'],
            'wrap': ['Plastic'],
            'blister': ['Plastic', 'Cardboard']
        }
        
        return packaging_defaults.get(packaging_type, ['Cardboard'])
    
    def _estimate_packaging_ratio(self, packaging_type: str) -> float:
        """Estimate packaging weight as ratio of product weight"""
        ratios = {
            'bottle': 0.15,   # Bottles add significant weight
            'box': 0.05,      # Light cardboard
            'bag': 0.02,      # Very light
            'tube': 0.08,     # Moderate
            'can': 0.12,      # Metal is heavy
            'jar': 0.20,      # Glass is heavy
            'wrap': 0.01,     # Minimal
            'blister': 0.03   # Light plastic/card
        }
        
        return ratios.get(packaging_type, 0.05)
    
    def _classify_product_category(self, text: str) -> str:
        """Simple category classification"""
        category_keywords = {
            'electronics': ['phone', 'laptop', 'tablet', 'headphones', 'speaker', 'tv', 'camera'],
            'clothing': ['shirt', 'dress', 'pants', 'shoes', 'jacket', 'sweater', 'jeans'],
            'food': ['organic', 'snack', 'beverage', 'coffee', 'tea', 'sauce', 'oil'],
            'home_garden': ['furniture', 'lamp', 'cushion', 'plant', 'tool', 'storage']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'other'
    
    def _apply_category_defaults(self, category: str, current_data: Dict) -> Dict:
        """Apply category-based defaults for missing data"""
        defaults = self.category_mappings.get(category, {})
        enhanced = {}
        
        # Only apply defaults if current data is missing or generic
        if current_data.get('transport', 'Land') == 'Land' and 'transport_mode' in defaults:
            enhanced['transport'] = defaults['transport_mode']
        
        if current_data.get('recyclability', 'Medium') == 'Medium':
            enhanced['recyclability'] = defaults.get('recyclability', 'Medium')
        
        return enhanced
    
    def _get_origin_confidence(self, current_origin: str, brand: str) -> float:
        """Assess confidence in origin classification"""
        if current_origin != 'Other':
            return 0.8
        
        brand_lower = brand.lower()
        for known_brand, origin in self.brand_origins.items():
            if isinstance(known_brand, str) and known_brand in brand_lower:
                return 0.9
        
        return 0.3
    
    def _estimate_lifespan(self, text: str, category: str) -> float:
        """Estimate product lifespan in years"""
        # Keyword-based adjustments
        durability_keywords = {
            'high': ['professional', 'industrial', 'heavy duty', 'lifetime'],
            'low': ['disposable', 'single use', 'temporary', 'budget']
        }
        
        base_lifespan = self.category_mappings.get(category, {}).get('avg_lifespan_years', 3)
        
        if any(keyword in text for keyword in durability_keywords['high']):
            return base_lifespan * 1.5
        elif any(keyword in text for keyword in durability_keywords['low']):
            return base_lifespan * 0.5
        
        return base_lifespan
    
    def _estimate_repairability(self, text: str, category: str) -> float:
        """Estimate repairability score (1-10)"""
        base_scores = {
            'electronics': 4,
            'clothing': 6,
            'food': 1,
            'home_garden': 7
        }
        
        modular_keywords = ['modular', 'replaceable', 'spare parts', 'repair kit']
        sealed_keywords = ['sealed', 'integrated', 'non-removable', 'disposable']
        
        base = base_scores.get(category, 5)
        
        if any(keyword in text for keyword in modular_keywords):
            return min(10, base + 2)
        elif any(keyword in text for keyword in sealed_keywords):
            return max(1, base - 2)
        
        return base
    
    def _detect_size_category(self, text: str) -> str:
        """Detect size category from Amazon title"""
        size_patterns = self.amazon_patterns['size_indicators']
        
        for size in ['large', 'xl', 'xxl', 'king size', 'queen size']:
            if size in text:
                return 'large'
        
        for size in ['small', 'mini', 'compact', 'travel size']:
            if size in text:
                return 'small'
        
        return 'medium'
    
    def _detect_quality_level(self, text: str) -> str:
        """Detect quality level from Amazon title"""
        quality_patterns = self.amazon_patterns['quality_indicators']
        
        for quality in ['premium', 'professional', 'heavy duty', 'commercial grade', 'deluxe']:
            if quality in text:
                return 'high'
        
        for quality in ['budget', 'economy', 'basic']:
            if quality in text:
                return 'low'
        
        return 'standard'
    
    def _detect_eco_labeling(self, text: str) -> bool:
        """Detect eco-friendly labeling"""
        eco_keywords = self.amazon_patterns['eco_keywords']
        return any(keyword in text for keyword in eco_keywords)
    
    def _detect_amazon_choice(self, text: str) -> bool:
        """Detect Amazon's Choice products"""
        choice_keywords = self.amazon_patterns['amazon_choice']
        return any(keyword in text for keyword in choice_keywords)
    
    def _detect_pack_size(self, text: str) -> int:
        """Detect pack size from title"""
        import re
        
        # Look for pack size patterns
        pack_patterns = [
            r'pack of (\d+)',
            r'set of (\d+)', 
            r'(\d+) pack',
            r'(\d+) count'
        ]
        
        for pattern in pack_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return 1  # Single item
    
    def _estimate_volume_from_amazon_title(self, text: str) -> float:
        """Estimate product volume in liters from text"""
        import re
        
        # Look for dimension patterns
        dimension_patterns = [
            r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*cm',
            r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*inch',
            r'(\d+\.?\d*)\s*cm\s*x\s*(\d+\.?\d*)\s*cm\s*x\s*(\d+\.?\d*)\s*cm'
        ]
        
        for pattern in dimension_patterns:
            match = re.search(pattern, text)
            if match:
                dims = [float(match.group(i)) for i in range(1, 4)]
                if 'inch' in pattern:
                    dims = [d * 2.54 for d in dims]  # Convert to cm
                
                volume_cm3 = dims[0] * dims[1] * dims[2]
                return volume_cm3 / 1000  # Convert to liters
        
        return 1.0  # Default 1 liter
    
    def _assess_weight_confidence(self, text: str, current_weight) -> float:
        """Assess confidence in weight estimation"""
        # Convert weight to float if it's a string
        try:
            weight_val = float(current_weight) if current_weight is not None else 0.0
        except (ValueError, TypeError):
            weight_val = 0.0
            
        if re.search(r'\d+\.?\d*\s*(kg|g|lb|oz)', text):
            return 0.9  # Found explicit weight
        elif weight_val > 0:
            return 0.6  # Estimated weight
        else:
            return 0.3  # No weight info


def enhance_amazon_dataset(input_csv: str, output_csv: str):
    """Enhance your existing Amazon dataset with additional features"""
    enhancer = AmazonFeatureEnhancer()
    
    df = pd.read_csv(input_csv)
    
    # Fix data types to prevent errors
    if 'weight' in df.columns:
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(1.0)
    if 'co2_emissions' in df.columns:
        df['co2_emissions'] = pd.to_numeric(df['co2_emissions'], errors='coerce').fillna(0.0)
    
    enhanced_rows = []
    
    print(f"🔧 Enhancing {len(df)} Amazon products...")
    
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  Processed {idx} rows...")
        
        product_dict = row.to_dict()
        enhanced = enhancer.enhance_amazon_product_features(product_dict)
        enhanced_rows.append(enhanced)
    
    enhanced_df = pd.DataFrame(enhanced_rows)
    enhanced_df.to_csv(output_csv, index=False)
    
    print(f"✅ Enhanced Amazon dataset saved to {output_csv}")
    print(f"📊 Added {len(enhanced_df.columns) - len(df.columns)} new features")
    
    # Show summary of new features
    print("\n🎯 New Amazon-specific features added:")
    new_features = ['material_confidence', 'packaging_type', 'size_category', 
                   'quality_level', 'is_eco_labeled', 'pack_size']
    
    for feature in new_features:
        if feature in enhanced_df.columns:
            if enhanced_df[feature].dtype == 'bool':
                print(f"  {feature}: {enhanced_df[feature].sum()} products (True)")
            elif enhanced_df[feature].dtype in ['int64', 'float64']:
                print(f"  {feature}: mean = {enhanced_df[feature].mean():.2f}")
            else:
                print(f"  {feature}: {enhanced_df[feature].value_counts().head(3).to_dict()}")

if __name__ == "__main__":
    # Example usage with your Amazon dataset
    enhance_amazon_dataset(
        "../../../common/data/csv/eco_dataset.csv",
        "../../../common/data/csv/enhanced_amazon_dataset.csv"
    )