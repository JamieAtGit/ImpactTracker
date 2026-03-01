#!/usr/bin/env python3
"""
Debug scraper to see what HTML we're actually getting from Amazon
"""

import requests
from bs4 import BeautifulSoup
import random
import time

def debug_amazon_scraping():
    url = "https://www.amazon.co.uk/dp/B08N5WRWNW"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }
    
    print(f"🔍 Testing URL: {url}")
    
    try:
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"Status code: {response.status_code}")
        print(f"Response length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check page title
            title_elem = soup.select_one('title')
            if title_elem:
                print(f"Page title: {title_elem.get_text()}")
            
            # Check for bot detection
            page_text = response.text.lower()
            if "robot" in page_text or "captcha" in page_text:
                print("🛑 Bot detection keywords found in page")
            
            # Try to find product title with various selectors
            title_selectors = [
                '#productTitle',
                'span#productTitle', 
                '.product-title',
                'h1',
                '[data-automation-id="product-title"]'
            ]
            
            print("\n🔍 Testing title selectors:")
            for selector in title_selectors:
                elements = soup.select(selector)
                print(f"  {selector}: {len(elements)} matches")
                if elements:
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.get_text().strip()[:100]
                        print(f"    [{i}]: {text}")
            
            # Check for common Amazon elements
            print("\n🔍 Testing common Amazon elements:")
            common_selectors = {
                'byline': '#bylineInfo',
                'price': '.a-price-whole',
                'features': '#feature-bullets li',
                'details': '#detailBullets_feature_div li'
            }
            
            for name, selector in common_selectors.items():
                elements = soup.select(selector)
                print(f"  {name} ({selector}): {len(elements)} matches")
            
            # Save a snippet of HTML for inspection
            html_snippet = str(soup)[:2000]
            print(f"\n📄 HTML snippet (first 2000 chars):")
            print(html_snippet)
            
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_amazon_scraping()
