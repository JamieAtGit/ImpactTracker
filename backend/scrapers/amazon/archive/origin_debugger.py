#!/usr/bin/env python3
"""
🔍 ORIGIN EXTRACTION DEBUGGER
============================

Detailed diagnostic tool to understand exactly what Amazon is showing
for the Grenade protein powder product origin information.
"""

import requests
import time
import random
import re
from bs4 import BeautifulSoup

def debug_origin_extraction(url: str):
    """Debug origin extraction step by step"""
    print(f"🔍 DEBUGGING ORIGIN EXTRACTION")
    print(f"📍 URL: {url}")
    print("=" * 80)
    
    # Headers to mimic browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"📡 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. Look for technical details sections
            print("\n🔧 TECHNICAL DETAILS SECTIONS:")
            tech_sections = soup.find_all(['div', 'table', 'section'], class_=re.compile(r'tech|detail|spec|feature', re.I))
            
            for i, section in enumerate(tech_sections[:5]):  # Limit to first 5
                text = section.get_text().strip()
                if len(text) > 50:  # Only show substantial content
                    print(f"  Section {i+1}: {text[:200]}...")
                    if 'belgium' in text.lower() or 'origin' in text.lower():
                        print(f"    🎯 FOUND RELEVANT CONTENT!")
            
            # 2. Search for any mention of countries
            all_text = soup.get_text()
            countries_found = []
            
            test_countries = ['belgium', 'germany', 'england', 'uk', 'usa', 'china', 'france', 'italy', 'spain']
            for country in test_countries:
                if country in all_text.lower():
                    countries_found.append(country)
                    
            print(f"\n🌍 COUNTRIES FOUND IN PAGE: {countries_found}")
            
            # 3. Look specifically for "Country of origin" patterns
            print(f"\n📋 ORIGIN PATTERN SEARCH:")
            origin_patterns = [
                r"country\s+of\s+origin[:\s]*([^,\n]{1,50})",
                r"made\s+in[:\s]*([^,\n]{1,20})",
                r"origin[:\s]*([^,\n]{1,30})",
                r"manufactured\s+in[:\s]*([^,\n]{1,20})"
            ]
            
            for pattern in origin_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                if matches:
                    print(f"  Pattern '{pattern}' found: {matches}")
                else:
                    print(f"  Pattern '{pattern}': No matches")
            
            # 4. Look for specific "Belgium" context
            print(f"\n🇧🇪 BELGIUM CONTEXT SEARCH:")
            belgium_pos = all_text.lower().find('belgium')
            if belgium_pos >= 0:
                context_start = max(0, belgium_pos - 100)
                context_end = min(len(all_text), belgium_pos + 100)
                context = all_text[context_start:context_end]
                print(f"  Found Belgium at position {belgium_pos}")
                print(f"  Context: '{context}'")
            else:
                print(f"  Belgium not found in page content")
                
            # 5. Look for product details table specifically
            print(f"\n📊 PRODUCT DETAILS TABLE:")
            detail_tables = soup.find_all('table')
            for i, table in enumerate(detail_tables):
                table_text = table.get_text()
                if 'origin' in table_text.lower() or len(table_text) > 100:
                    print(f"  Table {i+1}: {table_text[:300]}...")
                    
            # 6. Check for hidden/dynamic content
            print(f"\n🔍 HIDDEN CONTENT CHECK:")
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('origin' in script.string.lower() or 'belgium' in script.string.lower()):
                    print(f"  Found origin/belgium in script content")
                    break
            else:
                print(f"  No origin/belgium found in script content")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_url = "https://www.amazon.co.uk/Grenade-Protein-Powder-Serving-Servings/dp/B0CKFK6716/ref=sr_1_51"
    debug_origin_extraction(test_url)