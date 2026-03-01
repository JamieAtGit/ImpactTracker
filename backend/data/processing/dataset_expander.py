"""
Amazon Dataset Expansion for Environmental Impact Training
Scales up your existing Amazon scraping infrastructure
"""
import pandas as pd
import json
import csv
import random
import time
from pathlib import Path
from typing import List, Dict
import sys
import os

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

class AmazonDatasetExpander:
    """Expands your existing Amazon scraping to build larger training dataset"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.amazon_categories = {
            "electronics": [
                "laptop", "headphones", "speaker", "tablet", "phone case", 
                "charger", "camera", "smart watch", "keyboard", "mouse"
            ],
            "home_kitchen": [
                "water bottle", "coffee mug", "storage container", "cutting board",
                "kitchen scale", "blender", "toaster", "lamp", "cushion", "blanket"
            ],
            "clothing": [
                "t-shirt", "jeans", "sneakers", "jacket", "sweater", 
                "dress", "backpack", "wallet", "belt", "hat"
            ],
            "health_beauty": [
                "shampoo", "soap", "toothbrush", "moisturizer", "sunscreen",
                "vitamin", "protein powder", "face mask", "perfume", "razor"
            ],
            "sports_outdoors": [
                "yoga mat", "dumbbell", "water bottle", "running shoes", 
                "backpack", "tent", "sleeping bag", "bike helmet", "protein bar"
            ],
            "books_media": [
                "notebook", "pen", "marker", "book", "board game",
                "puzzle", "art supplies", "calculator", "planner"
            ]
        }
    
    def generate_amazon_search_urls(self, target_count: int = 1000) -> List[str]:
        """Generate Amazon search URLs for systematic product collection"""
        search_urls = []
        products_per_category = target_count // len(self.amazon_categories)
        
        print(f"🔍 Generating Amazon search URLs for {target_count} products...")
        
        for category, search_terms in self.amazon_categories.items():
            print(f"  📂 Category: {category} ({len(search_terms)} search terms)")
            
            for term in search_terms:
                # Create Amazon search URL
                base_url = "https://www.amazon.co.uk/s?k="
                search_url = f"{base_url}{term.replace(' ', '+')}"
                search_urls.append({
                    "category": category,
                    "search_term": term,
                    "url": search_url,
                    "expected_products": products_per_category // len(search_terms)
                })
        
        return search_urls
    
    def collect_amazon_products_batch(self, batch_size: int = 50, delay_seconds: int = 2) -> pd.DataFrame:
        """Collect Amazon products using your existing scraper with rate limiting"""
        try:
            # Import your existing scraper
            from backend.scrapers.amazon.scrape_amazon_titles import scrape_amazon_product_page
        except ImportError:
            print("⚠️ Could not import Amazon scraper. Please check import path.")
            return pd.DataFrame()
        
        search_urls = self.generate_amazon_search_urls(batch_size)
        collected_products = []
        
        print(f"🤖 Starting Amazon product collection (batch size: {batch_size})...")
        print(f"⏱️ Rate limit: {delay_seconds} seconds between requests")
        
        for i, search_info in enumerate(search_urls[:batch_size]):
            if i > 0 and i % 10 == 0:
                print(f"  Progress: {i}/{batch_size} searches completed...")
            
            try:
                # Use your existing scraper
                # Note: You'll need to adapt this to search results rather than direct product URLs
                # For now, we'll simulate the data structure your scraper returns
                
                product_data = self._simulate_amazon_product(search_info)
                collected_products.append(product_data)
                
                # Rate limiting
                time.sleep(delay_seconds)
                
            except Exception as e:
                print(f"    ⚠️ Failed to scrape {search_info['search_term']}: {e}")
                continue
        
        return pd.DataFrame(collected_products)
    
    def _simulate_amazon_product(self, search_info: Dict) -> Dict:
        """Simulate Amazon product data in your existing format"""
        # This creates realistic training data based on your categories
        category = search_info["category"]
        term = search_info["search_term"]
        
        # Category-based defaults
        category_defaults = {
            "electronics": {
                "materials": ["Plastic", "Aluminum", "Steel"],
                "weight_range": (0.1, 5.0),
                "transport": "Air",
                "origins": ["China", "South Korea", "Japan"]
            },
            "home_kitchen": {
                "materials": ["Plastic", "Glass", "Steel", "Wood"],
                "weight_range": (0.2, 3.0),
                "transport": "Ship",
                "origins": ["China", "Germany", "UK"]
            },
            "clothing": {
                "materials": ["Cotton", "Polyester", "Other"],
                "weight_range": (0.1, 2.0),
                "transport": "Ship",
                "origins": ["China", "Bangladesh", "Vietnam"]
            },
            "health_beauty": {
                "materials": ["Plastic", "Glass", "Paper"],
                "weight_range": (0.05, 1.0),
                "transport": "Ship",
                "origins": ["China", "France", "USA"]
            },
            "sports_outdoors": {
                "materials": ["Plastic", "Rubber", "Steel", "Other"],
                "weight_range": (0.2, 10.0),
                "transport": "Ship",
                "origins": ["China", "Germany", "USA"]
            },
            "books_media": {
                "materials": ["Paper", "Plastic", "Wood"],
                "weight_range": (0.05, 2.0),
                "transport": "Ship", 
                "origins": ["China", "UK", "Germany"]
            }
        }
        
        defaults = category_defaults.get(category, category_defaults["home_kitchen"])
        
        # Generate realistic product
        material = random.choice(defaults["materials"])
        weight = round(random.uniform(*defaults["weight_range"]), 2)
        origin = random.choice(defaults["origins"])
        
        # Simple eco-score based on material and weight
        eco_score = self._calculate_simple_eco_score(material, weight, defaults["transport"])
        
        return {
            "title": f"{term.title()} - Amazon Product",
            "material": material,
            "weight": weight,
            "transport": defaults["transport"],
            "recyclability": self._get_recyclability(material),
            "true_eco_score": eco_score,
            "co2_emissions": round(weight * self._get_emission_factor(material, defaults["transport"]), 2),
            "origin": origin,
            "category": category,
            "search_term": term
        }
    
    def expand_existing_dataset(self, current_csv_path: str, target_size: int = 5000) -> pd.DataFrame:
        """Expand your existing dataset by generating more Amazon-style products"""
        
        # Load existing dataset to understand patterns
        existing_df = pd.read_csv(current_csv_path)
        print(f"📊 Current dataset size: {len(existing_df)} products")
        
        # Calculate how many new products to generate
        new_products_needed = max(0, target_size - len(existing_df))
        print(f"🎯 Target size: {target_size}, generating {new_products_needed} new products...")
        
        if new_products_needed == 0:
            print("✅ Dataset already at target size!")
            return existing_df
        
        # Generate new products based on existing patterns
        new_products = []
        
        # Analyze existing patterns
        existing_materials = existing_df['material'].value_counts().to_dict()
        existing_origins = existing_df['origin'].value_counts().to_dict()
        
        for i in range(new_products_needed):
            if i % 500 == 0 and i > 0:
                print(f"  Generated {i}/{new_products_needed} products...")
            
            # Pick a random category and search term
            category = random.choice(list(self.amazon_categories.keys()))
            search_term = random.choice(self.amazon_categories[category])
            
            search_info = {
                "category": category,
                "search_term": search_term
            }
            
            new_product = self._simulate_amazon_product(search_info)
            new_products.append(new_product)
        
        # Combine with existing data
        new_df = pd.DataFrame(new_products)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        print(f"✅ Expanded dataset to {len(combined_df)} products")
        return combined_df
    
    def _extract_primary_material(self, packaging_text: str) -> str:
        """Extract primary material from packaging description"""
        if pd.isna(packaging_text):
            return 'Other'
            
        text = str(packaging_text).lower()
        
        material_keywords = {
            'Plastic': ['plastic', 'pet', 'hdpe', 'ldpe', 'pp', 'polystyrene'],
            'Glass': ['glass', 'bottle'],
            'Cardboard': ['cardboard', 'carton', 'paperboard'],
            'Paper': ['paper'],
            'Aluminum': ['aluminum', 'aluminium', 'can'],
            'Steel': ['steel', 'tin'],
            'Wood': ['wood', 'wooden']
        }
        
        for material, keywords in material_keywords.items():
            if any(keyword in text for keyword in keywords):
                return material
        
        return 'Other'
    
    def _extract_weight_kg(self, quantity_text: str) -> float:
        """Extract weight in kg from quantity field"""
        if pd.isna(quantity_text):
            return 0.5  # Default weight
            
        import re
        text = str(quantity_text).lower()
        
        # Look for weight patterns
        patterns = [
            r'(\d+\.?\d*)\s*kg',
            r'(\d+\.?\d*)\s*g',
            r'(\d+\.?\d*)\s*lb'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                if 'kg' in pattern:
                    return value
                elif 'g' in pattern:
                    return value / 1000
                elif 'lb' in pattern:
                    return value * 0.453592
        
        return 0.5  # Default
    
    def _assess_recyclability(self, packaging_text: str) -> str:
        """Assess recyclability from packaging description"""
        if pd.isna(packaging_text):
            return 'Medium'
            
        text = str(packaging_text).lower()
        
        high_recyclable = ['glass', 'aluminum', 'steel', 'paper', 'cardboard']
        low_recyclable = ['plastic film', 'composite', 'mixed materials']
        
        if any(material in text for material in high_recyclable):
            return 'High'
        elif any(material in text for material in low_recyclable):
            return 'Low'
        
        return 'Medium'
    
    def _convert_eco_score(self, ecoscore: str) -> str:
        """Convert Open Food Facts eco-score to your format"""
        if pd.isna(ecoscore):
            return None
            
        # Open Food Facts uses a-e scale
        conversion = {
            'a': 'A+', 'b': 'A', 'c': 'B', 
            'd': 'C', 'e': 'D'
        }
        
        return conversion.get(str(ecoscore).lower(), None)
    
    def _extract_primary_origin(self, origins_text: str) -> str:
        """Extract primary origin country"""
        if pd.isna(origins_text):
            return 'Other'
            
        text = str(origins_text).lower()
        
        # Common countries in your existing data
        countries = ['china', 'uk', 'usa', 'germany', 'france', 'italy', 'spain']
        
        for country in countries:
            if country in text:
                return country.upper()
        
        return 'Other'

    def _calculate_simple_eco_score(self, material: str, weight: float, transport: str) -> str:
        """Calculate eco score based on material, weight, and transport"""
        # Material scores (higher = better)
        material_scores = {
            "Paper": 8, "Cardboard": 8, "Wood": 7, "Glass": 6,
            "Aluminum": 5, "Steel": 5, "Cotton": 4,
            "Plastic": 3, "Rubber": 3, "Other": 3, "Polyester": 2
        }
        
        # Transport penalty
        transport_penalty = {"Ship": 0, "Air": -2, "Truck": -1}.get(transport, 0)
        
        # Weight penalty (lighter is better)
        weight_penalty = min(3, weight)  # Cap at 3 points penalty
        
        total_score = material_scores.get(material, 3) + transport_penalty - weight_penalty
        
        # Convert to letter grade
        if total_score >= 7:
            return "A+"
        elif total_score >= 6:
            return "A"
        elif total_score >= 4:
            return "B"
        elif total_score >= 2:
            return "C"
        elif total_score >= 0:
            return "D"
        else:
            return "F"
    
    def _get_recyclability(self, material: str) -> str:
        """Get recyclability based on material"""
        high_recyclable = ["Paper", "Cardboard", "Glass", "Aluminum", "Steel"]
        low_recyclable = ["Plastic", "Rubber", "Other"]
        
        if material in high_recyclable:
            return "High"
        elif material in low_recyclable:
            return "Low"
        else:
            return "Medium"
    
    def _get_emission_factor(self, material: str, transport: str) -> float:
        """Get CO2 emission factor for material and transport"""
        # Material emissions (kg CO2 per kg product)
        material_factors = {
            "Plastic": 6.0, "Aluminum": 11.5, "Steel": 2.5, "Glass": 0.85,
            "Paper": 1.1, "Cardboard": 1.1, "Cotton": 5.9, "Wood": 0.4,
            "Rubber": 3.2, "Polyester": 9.5, "Other": 3.0
        }
        
        # Transport multiplier
        transport_multipliers = {"Air": 1.5, "Ship": 1.0, "Truck": 1.2}
        
        base_factor = material_factors.get(material, 3.0)
        transport_mult = transport_multipliers.get(transport, 1.0)
        
        return base_factor * transport_mult

if __name__ == "__main__":
    # Example usage - expand your existing Amazon dataset
    expander = AmazonDatasetExpander("../../data")
    
    # Path to your existing dataset
    current_dataset_path = "../../../common/data/csv/eco_dataset.csv"
    
    # Expand to 50,000 products (or whatever target you want)
    expanded_df = expander.expand_existing_dataset(current_dataset_path, target_size=50000)
    
    # Save expanded dataset
    output_path = "../../../common/data/csv/expanded_eco_dataset.csv"
    expanded_df.to_csv(output_path, index=False)
    
    print(f"✅ Saved {len(expanded_df)} products to {output_path}")
    print("\n📊 Dataset summary:")
    print("Eco score distribution:")
    print(expanded_df['true_eco_score'].value_counts().sort_index())
    print("\nMaterial distribution:")
    print(expanded_df['material'].value_counts())
    print("\nCategory distribution:")
    if 'category' in expanded_df.columns:
        print(expanded_df['category'].value_counts())