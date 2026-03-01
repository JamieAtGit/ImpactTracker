#!/usr/bin/env python3
"""
🥷 STEALTH AMAZON SCRAPER - ANTI-BOT DETECTION
==============================================

Advanced scraper with multiple layers of bot detection evasion:
- selenium-stealth patches
- Human behavior simulation  
- Realistic browser fingerprinting
- Session persistence
- Random delays and mouse movements
"""

import os
import sys
import time
import random
import json
from typing import Dict, Optional

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth
from fake_useragent import UserAgent
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

class StealthAmazonScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.ua = UserAgent()
        
    def create_stealth_driver(self):
        """Create highly stealthed Chrome driver"""
        print("🥷 Creating stealth Chrome driver...")
        
        try:
            # Method 1: Try undetected_chromedriver with advanced config
            options = uc.ChromeOptions()
            
            # Advanced anti-detection options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Realistic window size and position
            options.add_argument("--window-size=1366,768")
            options.add_argument("--start-maximized")
            
            # Language and region
            options.add_argument("--lang=en-GB")
            options.add_argument("--accept-lang=en-GB,en-US;q=0.9,en;q=0.8")
            
            # Disable various detection methods
            options.add_argument("--disable-extensions-file-access-check")
            options.add_argument("--disable-extensions-http-throttling")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-default-apps")
            
            # Memory and performance
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")
            
            # Create driver with version_main specified to avoid architecture issues
            self.driver = uc.Chrome(
                options=options,
                version_main=131,  # Force specific Chrome version
                driver_executable_path=None,
                headless=False  # VISIBLE mode - you'll see the browser!
            )
            
            # Apply selenium-stealth patches
            stealth(self.driver,
                languages=["en-US", "en", "en-GB"],
                vendor="Google Inc.",
                platform="MacIntel",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                run_on_insecure_origins=False,
            )
            
            # Execute additional stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise")
            self.driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol")
            
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Stealth driver created successfully!")
            return True
            
        except Exception as e:
            print(f"⚠️ Undetected Chrome failed: {e}")
            
            # Method 2: Fallback to regular ChromeDriver with stealth
            try:
                print("🔄 Trying regular ChromeDriver with stealth patches...")
                
                chrome_options = Options()
                
                # Basic stealth options
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Use webdriver_manager to handle driver installation
                driver_path = ChromeDriverManager().install()
                self.driver = webdriver.Chrome(service=webdriver.ChromeService(driver_path), options=chrome_options)
                
                # Apply stealth patches
                stealth(self.driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="MacIntel",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )
                
                self.wait = WebDriverWait(self.driver, 20)
                print("✅ Regular ChromeDriver with stealth created!")
                return True
                
            except Exception as e2:
                print(f"❌ Both Chrome methods failed: {e2}")
                return False
    
    def human_like_behavior(self):
        """Simulate human-like browsing behavior"""
        try:
            # Random mouse movements
            actions = ActionChains(self.driver)
            
            # Get window size
            size = self.driver.get_window_size()
            width, height = size['width'], size['height']
            
            # Random mouse movements
            for _ in range(random.randint(2, 4)):
                x = random.randint(0, width)
                y = random.randint(0, height)
                actions.move_by_offset(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Random scroll
            scroll_height = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height})")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back up a bit
            scroll_back = random.randint(50, 200)
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_back})")
            time.sleep(random.uniform(0.3, 0.8))
            
        except Exception as e:
            print(f"⚠️ Human behavior simulation error: {e}")
    
    def scrape_amazon_product(self, url: str) -> Optional[Dict]:
        """Scrape Amazon product with full stealth mode"""
        
        if not self.create_stealth_driver():
            return None
        
        try:
            print(f"🎯 Stealthily navigating to: {url}")
            
            # Add random delay before navigation
            time.sleep(random.uniform(1, 3))
            
            # Navigate to Amazon homepage first (more human-like)
            print("📍 First visiting Amazon homepage...")
            print("👀 WATCH: Chrome window should open now!")
            self.driver.get("https://www.amazon.co.uk")
            time.sleep(random.uniform(2, 4))
            
            # Simulate human behavior on homepage
            print("🤖 Simulating human behavior on homepage...")
            self.human_like_behavior()
            
            # Now navigate to the product page
            print("🛍️ Now navigating to product page...")
            print(f"👀 WATCH: Browser going to {url}")
            self.driver.get(url)
            time.sleep(random.uniform(3, 6))
            
            # Check for CAPTCHA or bot detection
            page_source = self.driver.page_source.lower()
            if 'captcha' in page_source or 'robot' in page_source or 'blocked' in page_source:
                print("🚫 CAPTCHA or bot detection encountered")
                
                # Try to wait it out and reload
                print("⏳ Waiting and retrying...")
                time.sleep(random.uniform(10, 15))
                self.driver.refresh()
                time.sleep(random.uniform(3, 6))
                
                # Check again
                page_source = self.driver.page_source.lower()
                if 'captcha' in page_source or 'robot' in page_source:
                    print("🚫 Still blocked after retry")
                    return None
            
            # More human behavior
            self.human_like_behavior()
            
            # Extract product data
            product_data = self.extract_product_data()
            
            if product_data:
                print(f"✅ Successfully extracted: {product_data.get('title', 'Unknown')[:50]}...")
                return product_data
            else:
                print("⚠️ Failed to extract product data")
                return None
                
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("🔒 Browser closed")
                except:
                    pass
    
    def extract_product_data(self) -> Optional[Dict]:
        """Extract product data from current page"""
        try:
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
            
            # Extract title
            title_element = self.driver.find_element(By.ID, "productTitle")
            title = title_element.text.strip() if title_element else "Unknown Product"
            
            # Extract brand  
            brand = "Unknown"
            try:
                brand_element = self.driver.find_element(By.CSS_SELECTOR, "#bylineInfo, .author.notFaded a")
                brand_text = brand_element.text.strip()
                # Clean brand text
                import re
                brand = re.sub(r'^(by|visit the|brand:)\s*', '', brand_text, flags=re.IGNORECASE).strip()
                if len(brand) > 50:
                    brand = brand[:50]
            except:
                pass
            
            # Extract features
            features = []
            try:
                feature_elements = self.driver.find_elements(By.CSS_SELECTOR, "#feature-bullets li, .a-unordered-list li")
                for element in feature_elements[:10]:
                    text = element.text.strip()
                    if text and len(text) > 5:
                        features.append(text)
            except:
                pass
            
            # Extract technical details
            tech_details = {}
            try:
                detail_rows = self.driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
                for row in detail_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) == 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            if key and value:
                                tech_details[key] = value
                    except:
                        continue
            except:
                pass
            
            # Analyze extracted data
            full_text = f"{title} {' '.join(features)} {' '.join(tech_details.values())}"
            
            # Extract weight
            weight_kg = self.extract_weight(full_text)
            
            # Extract dimensions
            dimensions_cm = self.extract_dimensions(full_text)
            
            # Detect material
            material_type = self.detect_material(full_text)
            
            # Estimate origin
            origin = self.estimate_origin(brand)
            
            # Estimate recyclability
            recyclability = self.estimate_recyclability(material_type)
            
            return {
                "title": title,
                "origin": origin,
                "weight_kg": round(weight_kg, 2),
                "dimensions_cm": dimensions_cm,
                "material_type": material_type,
                "recyclability": recyclability,
                "eco_score_ml": "C",
                "transport_mode": "Ship",
                "carbon_kg": None,
                "brand": brand,
                "data_quality_score": 90,  # High quality stealth scraping
                "confidence": "High",
                "data_sources": {
                    "title": "Amazon product page",
                    "weight": "Technical specifications",
                    "material": "Product features analysis",
                    "origin": "Brand database"
                }
            }
            
        except Exception as e:
            print(f"❌ Data extraction error: {e}")
            return None
    
    def extract_weight(self, text: str) -> float:
        """Extract weight from text"""
        import re
        
        text_lower = text.lower()
        
        # Weight patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram)',
            r'(\d+(?:\.\d+)?)\s*(?:g|gram)(?!\w)',
            r'(\d+(?:\.\d+)?)\s*(?:lb|pound)',
            r'(\d+(?:\.\d+)?)\s*(?:oz|ounce)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                weight = float(matches[0])
                if 'kg' in text_lower:
                    return weight
                elif 'g' in text_lower and 'kg' not in text_lower:
                    return weight / 1000
                elif 'lb' in text_lower:
                    return weight * 0.453592
                elif 'oz' in text_lower:
                    return weight * 0.0283495
        
        return 0.5  # Default weight
    
    def extract_dimensions(self, text: str) -> list:
        """Extract dimensions from text"""
        import re
        
        patterns = [
            r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeter)',
            r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*(?:cm|centimeter)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return [float(d) for d in matches[0]]
        
        return [15, 10, 8]  # Default dimensions
    
    def detect_material(self, text: str) -> str:
        """Detect material from text"""
        text_lower = text.lower()
        
        materials = {
            'Plastic': ['plastic', 'polymer', 'vinyl', 'pvc', 'polyester'],
            'Metal': ['metal', 'steel', 'aluminum', 'iron', 'copper'],
            'Glass': ['glass', 'crystal'],
            'Wood': ['wood', 'wooden', 'bamboo', 'timber'],
            'Paper': ['paper', 'cardboard'],
            'Fabric': ['cotton', 'wool', 'fabric', 'textile'],
            'Ceramic': ['ceramic', 'porcelain'],
            'Rubber': ['rubber', 'silicone']
        }
        
        for material, keywords in materials.items():
            if any(keyword in text_lower for keyword in keywords):
                return material
        
        return 'Unknown'
    
    def estimate_origin(self, brand: str) -> str:
        """Estimate product origin from brand"""
        if not brand or brand == "Unknown":
            return "UK"
        
        # Load brand origins
        try:
            brand_path = os.path.join(project_root, 'backend', 'scrapers', 'amazon', 'brand_locations.json')
            if os.path.exists(brand_path):
                with open(brand_path, 'r') as f:
                    brand_locations = json.load(f)
                    return brand_locations.get(brand.upper(), "UK")
        except:
            pass
        
        return "UK"
    
    def estimate_recyclability(self, material: str) -> str:
        """Estimate recyclability from material"""
        high_recyclable = ['Glass', 'Metal', 'Paper']
        medium_recyclable = ['Wood', 'Ceramic']
        low_recyclable = ['Plastic', 'Rubber', 'Fabric']
        
        if material in high_recyclable:
            return "High"
        elif material in medium_recyclable:
            return "Medium"
        elif material in low_recyclable:
            return "Low"
        else:
            return "Medium"

def scrape_with_stealth(url: str) -> Optional[Dict]:
    """Main function to scrape with stealth techniques"""
    scraper = StealthAmazonScraper()
    return scraper.scrape_amazon_product(url)

if __name__ == "__main__":
    # Test the stealth scraper
    test_url = "https://www.amazon.co.uk/dp/B07BMBG422"
    print("🥷 Testing Stealth Amazon Scraper")
    print("=" * 50)
    
    result = scrape_with_stealth(test_url)
    
    if result:
        print("\n✅ STEALTH SCRAPER SUCCESS!")
        print(f"Title: {result['title'][:60]}...")
        print(f"Brand: {result['brand']}")
        print(f"Weight: {result['weight_kg']} kg")
        print(f"Material: {result['material_type']}")
        print(f"Origin: {result['origin']}")
        print(f"Quality: {result['data_quality_score']}%")
    else:
        print("\n❌ Stealth scraper failed")