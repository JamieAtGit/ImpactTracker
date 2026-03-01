#!/usr/bin/env python3
"""
Debug origin extraction for Warrior protein flapjack
Test the current scraper to see exactly what's being extracted
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.scrapers.amazon.production_scraper import ProductionAmazonScraper

def debug_origin_extraction():
    """Debug current origin extraction behavior"""
    
    scraper = ProductionAmazonScraper()
    url = "https://www.amazon.co.uk/Warrior-Supplements-Protein-Flapjack-Honey/dp/B07F6HGNQF/ref=sr_1_2_sspa?crid=2BWCYB026Q8DS&dib=eyJ2IjoiMSJ9.5LB35VjlIw5T1yQfhbPA9VCTiy3LonsQoq81NlJ5ozpn0Fl-GAEb5xg1QwiQEh9_3-1MfVgpKL9bOAF8ouqdmnU74QfUa_PuJp2UEs0tjjPyW7zcyMcg5QTDrFPHG3yVqeUC4F8DUFqpKb33jQzmILCCU88YBRh3noeZBvBHOkW5TKP2KPM-QuuPfZmoWX8dIQx6sn53gKZ32h285c35om4_vs3wjOpUx9BGYVK88B-nYrCXUjPtvefR6Y_h8mdJez4MJxEKkJ-y8WY_4YbhZVdbcvSwSm-E--HysWrhWZE.M7k3n0UJx0muWXi39Zn618qSKTd4aZf5JwmO1-bneKs&dib_tag=se&keywords=protein%2Bbar&qid=1753296583&sprefix=protein%2Bba%2Caps%2C439&sr=8-2-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1"
    
    print("🔍 DEBUGGING ORIGIN EXTRACTION")
    print("=" * 60)
    print(f"URL: {url[:80]}...")
    
    # Test current scraper
    result = scraper.scrape_with_full_url(url)
    
    if result:
        print(f"\n📦 CURRENT SCRAPER RESULTS:")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Brand: {result.get('brand', 'N/A')}")
        print(f"   Origin: {result.get('origin', 'N/A')}")
        print(f"   Weight: {result.get('weight_kg', 'N/A')}kg")
        print(f"   Material: {result.get('material_type', 'N/A')}")
        print(f"   Category: {result.get('category', 'N/A')}")
        print(f"   Confidence: {result.get('confidence_score', 0):.1%}")
        
        # Now let's examine the raw HTML to see what we're missing
        print(f"\n🔍 DEBUGGING RAW HTML EXTRACTION...")
        
        # Make a fresh request to analyze the HTML
        response = scraper.make_request_with_retry(url, "debug")
        if response:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"\n📋 SEARCHING FOR ORIGIN INFORMATION:")
            
            # Search for manufacturer/origin patterns
            text_content = soup.get_text().lower()
            
            # Look for specific origin indicators
            origin_patterns = [
                r'country.*origin[:\s]*([a-z\s]+)',
                r'made.*in[:\s]*([a-z\s]+)',
                r'manufactured.*in[:\s]*([a-z\s]+)',
                r'origin[:\s]*([a-z\s]+)',
                r'product.*of[:\s]*([a-z\s]+)',
                r'distributed.*by[:\s]*(.+?)(?:,|\.|\n)',
                r'manufacturer.*contact[:\s]*(.+?)(?:,|\.|\n)',
            ]
            
            import re
            for pattern in origin_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    print(f"   Found '{pattern}': {matches[:3]}")
            
            # Look specifically in product details tables
            print(f"\n📊 SEARCHING IN PRODUCT DETAILS TABLES:")
            
            detail_selectors = [
                'table#productDetails_techSpec_section_1',
                'table#productDetails_detailBullets_sections1', 
                'div#productDetails_db_sections',
                'div#detailBullets_feature_div',
                'div.pdTab',
                '#feature-bullets',
                '.a-unordered-list'
            ]
            
            for selector in detail_selectors:
                elements = soup.select(selector)
                for i, element in enumerate(elements):
                    element_text = element.get_text().lower()
                    
                    if any(keyword in element_text for keyword in ['origin', 'made', 'manufactured', 'distributor', 'manufacturer', 'contact', 'manchester', 'uk']):
                        print(f"   {selector} #{i}: Found relevant content")
                        print(f"      Text: {element.get_text()[:200]}...")
                        
                        # Extract manufacturer contact specifically
                        if 'manufacturer contact' in element_text or 'distributed by' in element_text:
                            print(f"      🎯 MANUFACTURER INFO FOUND!")
                            full_text = element.get_text()
                            print(f"         Full text: {full_text}")
                            
            print(f"\n🔍 SEARCHING FOR SPECIFIC WARRIOR INFO:")
            # Look for the specific text mentioned
            search_terms = ['distributed by kbf', 'manchester', 'guinness road', 'warrior', 'kbf enterprises']
            for term in search_terms:
                if term in text_content:
                    print(f"   ✅ Found '{term}' in page content")
                    # Find surrounding context
                    import re
                    context_match = re.search(f'.{{0,100}}{re.escape(term)}.{{0,100}}', text_content, re.IGNORECASE)
                    if context_match:
                        print(f"      Context: {context_match.group()}")
                else:
                    print(f"   ❌ Missing '{term}' in page content")
                    
    else:
        print("❌ Scraper failed to extract data")

if __name__ == "__main__":
    debug_origin_extraction()
