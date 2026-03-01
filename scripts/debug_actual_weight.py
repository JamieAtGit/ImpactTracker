#!/usr/bin/env python3
"""
🔍 DEBUG ACTUAL MUTANT PROTEIN WEIGHT - 727g
============================================

The product actually weighs 727g according to Amazon specs.
Let's debug why this isn't being extracted properly.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import re

sys.path.insert(0, os.path.abspath('.'))

def test_direct_amazon_scraping():
    """Test scraping the actual Amazon page to find 727g"""
    
    url = "https://www.amazon.co.uk/Isolate-Protein-Fast-digesting-hydrolysate-Gourmet/dp/B01H3O2AMG"
    
    print("🔍 DEBUGGING ACTUAL AMAZON PAGE FOR 727g")
    print("=" * 60)
    print(f"URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for weight in different sections
            print(f"\n🔍 SEARCHING FOR 727g IN PAGE CONTENT...")
            
            # Method 1: Search for "727" in the HTML
            page_text = soup.get_text().lower()
            if '727' in page_text:
                print("✅ Found '727' in page content!")
                
                # Find context around 727
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if '727' in line:
                        print(f"   Context: {line.strip()}")
                        # Show surrounding lines
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if j != i:
                                print(f"           {lines[j].strip()}")
            else:
                print("❌ '727' not found in page text")
            
            # Method 2: Look in product specifications table
            print(f"\n🔍 SEARCHING PRODUCT SPECIFICATIONS...")
            
            # Common selectors for Amazon product specs
            spec_selectors = [
                'table#productDetails_techSpec_section_1',
                'table#productDetails_detailBullets_sections1',
                'div#feature-bullets',
                'div#productDetails_db_sections',
                'span.cr-original-review-text'
            ]
            
            for selector in spec_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().lower()
                    if '727' in text or 'gram' in text or 'weight' in text:
                        print(f"✅ Found in {selector}:")
                        print(f"   {text[:200]}...")
            
            # Method 3: Look for weight patterns
            print(f"\n🔍 SEARCHING FOR WEIGHT PATTERNS...")
            
            weight_patterns = [
                r'(\d+(?:\.\d+)?)\s*g\b',
                r'(\d+(?:\.\d+)?)\s*gram',
                r'(\d+(?:\.\d+)?)\s*kg',
                r'(\d+(?:\.\d+)?)\s*lb',
                r'weight.*?(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*ounce'
            ]
            
            for pattern in weight_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"Pattern '{pattern}' found:")
                    for match in matches:
                        weight_val = float(match)
                        if 500 <= weight_val <= 1000:  # Reasonable range for protein powder
                            print(f"   ✅ Potential weight: {weight_val}")
            
            # Method 4: Look in structured data (JSON-LD)
            print(f"\n🔍 SEARCHING JSON-LD STRUCTURED DATA...")
            
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if 'weight' in str(data).lower():
                        print(f"✅ Found weight in JSON-LD:")
                        print(f"   {data}")
                except:
                    pass
            
        else:
            print(f"❌ Failed to fetch page: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error scraping: {e}")

def test_enhanced_scraper_with_727g():
    """Test if our enhanced scraper can find 727g"""
    
    print(f"\n🧪 TESTING ENHANCED SCRAPER FOR 727g")
    print("=" * 50)
    
    url = "https://www.amazon.co.uk/Isolate-Protein-Fast-digesting-hydrolysate-Gourmet/dp/B01H3O2AMG"
    
    try:
        from enhanced_scraper_fix import EnhancedAmazonScraper
        
        scraper = EnhancedAmazonScraper()
        result = scraper.scrape_product_enhanced(url)
        
        if result:
            print(f"✅ Enhanced scraper result:")
            print(f"   Title: {result.get('title', 'Unknown')}")
            print(f"   Weight: {result.get('weight_kg', 'Unknown')}kg")
            print(f"   Raw weight: {result.get('weight_raw', 'Unknown')}")
            
            weight_kg = result.get('weight_kg', 0)
            if abs(weight_kg - 0.727) < 0.01:  # Within 10g
                print(f"✅ SUCCESS: Found correct weight {weight_kg}kg ≈ 727g")
            else:
                print(f"❌ WRONG WEIGHT: Got {weight_kg}kg, expected ~0.727kg")
                
                # Check if it's in the raw data
                raw_weight = result.get('weight_raw', '')
                if '727' in str(raw_weight):
                    print(f"💡 Found 727 in raw weight: {raw_weight}")
                    print(f"💡 Parsing issue - weight is there but not extracted properly")
        else:
            print(f"❌ Enhanced scraper returned no result")
            
    except ImportError:
        print(f"❌ Enhanced scraper not available")
    except Exception as e:
        print(f"❌ Enhanced scraper failed: {e}")

def create_727g_weight_fix():
    """Create a fix to properly extract 727g from specs"""
    
    print(f"\n🔧 CREATING FIX FOR 727g EXTRACTION")
    print("=" * 50)
    
    print("The issue is likely that:")
    print("1. 727g is in Amazon's product specifications section")
    print("2. Our scraper is only looking at the title")
    print("3. Title shows '25g Protein' (nutritional info) not '727g' (product weight)")
    print("4. Need to scrape the specifications table or shipping weight")
    
    print(f"\nProposed fix:")
    print(f"1. Add specifications table scraping to enhanced_scraper_fix.py")
    print(f"2. Look for patterns like 'Item Weight: 727g' or 'Net Weight: 727g'")
    print(f"3. Parse shipping dimensions and weight")
    print(f"4. Update weight extraction to check specs before using fallbacks")
    
    # Test what the title-based extraction should NOT capture
    title = "MUTANT ISO Surge | Whey Isolate Protein Powder | 25g Protein, Fast-digesting whey Protein Isolate &"
    
    print(f"\nTitle: {title}")
    print(f"Should extract: 0g (no container weight in title)")
    print(f"Should then check: Product specifications for 727g")
    print(f"Final result: 0.727kg")
    
if __name__ == "__main__":
    test_direct_amazon_scraping()
    test_enhanced_scraper_with_727g()
    create_727g_weight_fix()
