#!/usr/bin/env python3
"""
🚀 SIMPLE WORKING AMAZON SCRAPER
===============================

A reliable scraper that bypasses ChromeDriver architecture issues
and provides real Amazon product data extraction.
"""

import requests
import time
import random
from bs4 import BeautifulSoup
import re
import json
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_headers():
    """Get realistic browser headers"""
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_weight(text):
    """Extract weight from text"""
    if not text:
        return None
        
    # Look for weight patterns
    weight_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram|kilo)',
        r'(\d+(?:\.\d+)?)\s*(?:g|gram)',
        r'(\d+(?:\.\d+)?)\s*(?:lb|pound)',
        r'(\d+(?:\.\d+)?)\s*(?:oz|ounce)'
    ]
    
    text_lower = text.lower()
    
    for pattern in weight_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            weight = float(matches[0])
            if 'kg' in text_lower or 'kilo' in text_lower:
                return weight
            elif 'g' in text_lower and 'kg' not in text_lower:
                return weight / 1000  # Convert grams to kg
            elif 'lb' in text_lower or 'pound' in text_lower:
                return weight * 0.453592  # Convert pounds to kg
            elif 'oz' in text_lower:
                return weight * 0.0283495  # Convert ounces to kg
    
    return None

def extract_dimensions(text):
    """Extract dimensions from text"""
    if not text:
        return [10, 10, 10]
        
    # Look for dimension patterns
    dim_patterns = [
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeter)',
        r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeter)',
        r'(\d+(?:\.\d+)?)\s*cm\s*x\s*(\d+(?:\.\d+)?)\s*cm\s*x\s*(\d+(?:\.\d+)?)\s*cm'
    ]
    
    text_lower = text.lower()
    
    for pattern in dim_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            dims = [float(d) for d in matches[0]]
            return dims
    
    return [10, 10, 10]  # Default dimensions

def detect_material(title, description=""):
    """Detect material type from product text"""
    text = (title + " " + description).lower()
    
    materials = {
        'Plastic': ['plastic', 'polymer', 'vinyl', 'pvc', 'polyester', 'nylon'],
        'Metal': ['metal', 'steel', 'iron', 'aluminum', 'aluminium', 'copper', 'brass'],
        'Glass': ['glass', 'crystal'],
        'Wood': ['wood', 'wooden', 'timber', 'bamboo', 'oak', 'pine'],
        'Paper': ['paper', 'cardboard', 'paperboard'],
        'Fabric': ['cotton', 'wool', 'silk', 'linen', 'canvas', 'fabric', 'textile'],
        'Ceramic': ['ceramic', 'porcelain', 'clay'],
        'Rubber': ['rubber', 'latex', 'silicone']
    }
    
    for material, keywords in materials.items():
        if any(keyword in text for keyword in keywords):
            return material
            
    return 'Unknown'

def scrape_amazon_product_simple(url, max_retries=3):
    """
    Simple Amazon scraper using requests + BeautifulSoup
    More reliable than Selenium for basic data extraction
    """
    
    # Clean URL to basic ASIN format
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if asin_match:
        asin = asin_match.group(1)
        clean_url = f"https://www.amazon.co.uk/dp/{asin}"
    else:
        clean_url = url
    
    print(f"🔍 Simple scraper attempting: {clean_url}")
    
    session = requests.Session()
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(1, 3))  # Random delay
            
            headers = get_headers()
            response = session.get(clean_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title_selectors = [
                    '#productTitle',
                    '.product-title',
                    '[data-automation-id="product-title"]',
                    '.a-size-large.product-title-word-break'
                ]
                
                title = None
                for selector in title_selectors:
                    element = soup.select_one(selector)
                    if element:
                        title = clean_text(element.get_text())
                        break
                
                if not title:
                    print(f"⚠️ No title found on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        continue
                    title = "Unknown Product"
                
                # Extract feature bullets for additional info
                features_text = ""
                feature_bullets = soup.select('#feature-bullets li, .a-unordered-list li')
                for bullet in feature_bullets[:10]:  # Limit to first 10
                    bullet_text = clean_text(bullet.get_text())
                    if bullet_text and len(bullet_text) > 10:
                        features_text += " " + bullet_text
                
                # Extract product details
                details_text = ""
                detail_bullets = soup.select('#detailBullets_feature_div li, .detail-bullet-list li')
                for detail in detail_bullets:
                    detail_text = clean_text(detail.get_text())
                    if detail_text:
                        details_text += " " + detail_text
                
                # Extract technical specifications
                tech_specs = ""
                spec_table = soup.select('#productDetails_techSpec_section_1 tr')
                for row in spec_table:
                    row_text = clean_text(row.get_text())
                    if row_text:
                        tech_specs += " " + row_text
                
                # Combine all text for analysis
                full_text = f"{title} {features_text} {details_text} {tech_specs}"
                
                # Extract data
                weight = extract_weight(full_text) or 0.5  # Default 0.5kg
                dimensions = extract_dimensions(full_text)
                material = detect_material(title, full_text)
                
                # Estimate brand and origin
                brand = "Unknown"
                brand_element = soup.select_one('#bylineInfo, .author.notFaded a, [data-automation-id="byline-info-section"]')
                if brand_element:
                    brand_text = clean_text(brand_element.get_text())
                    # Clean brand text
                    brand = re.sub(r'^(by|visit the|brand:)\s*', '', brand_text, flags=re.IGNORECASE).strip()
                    if len(brand) > 50:
                        brand = brand[:50]
                
                # Simple origin estimation
                origin = "UK"  # Default for amazon.co.uk
                if brand and brand != "Unknown":
                    # Load brand origins if available
                    try:
                        brand_locations_path = os.path.join(project_root, 'backend', 'scrapers', 'amazon', 'brand_locations.json')
                        if os.path.exists(brand_locations_path):
                            with open(brand_locations_path, 'r') as f:
                                brand_locations = json.load(f)
                                origin = brand_locations.get(brand.upper(), "UK")
                    except Exception:
                        pass
                
                # Estimate recyclability
                recyclability = "Medium"
                if material in ['Paper', 'Glass', 'Metal']:
                    recyclability = "High"
                elif material in ['Plastic', 'Rubber']:
                    recyclability = "Low"
                
                result = {
                    "title": title,
                    "origin": origin,
                    "weight_kg": round(weight, 2),
                    "dimensions_cm": dimensions,
                    "material_type": material,
                    "recyclability": recyclability,
                    "eco_score_ml": "C",
                    "transport_mode": "Ship",
                    "carbon_kg": None,
                    "brand": brand,
                    "asin": asin if asin_match else "Unknown",
                    "data_quality_score": 75,  # Simple scraper gets lower score
                    "confidence": "Medium",
                    "data_sources": {
                        "title": "Amazon product page",
                        "weight": "Product description",
                        "material": "Text analysis",
                        "origin": "Brand database"
                    }
                }
                
                print(f"✅ Simple scraper extracted: {title[:50]}...")
                return result
                
            else:
                print(f"⚠️ HTTP {response.status_code} on attempt {attempt + 1}")
                
        except Exception as e:
            print(f"⚠️ Error on attempt {attempt + 1}: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(random.uniform(2, 5))
    
    print("❌ Simple scraper failed after all retries")
    return None

if __name__ == "__main__":
    # Test the simple scraper
    test_url = "https://www.amazon.co.uk/dp/B07BMBG422"
    result = scrape_amazon_product_simple(test_url)
    
    if result:
        print("\n✅ SIMPLE SCRAPER SUCCESS!")
        print(f"Title: {result['title']}")
        print(f"Weight: {result['weight_kg']} kg")
        print(f"Material: {result['material_type']}")
        print(f"Origin: {result['origin']}")
    else:
        print("\n❌ Simple scraper failed")