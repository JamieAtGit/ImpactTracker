#!/usr/bin/env python3
"""
🚀 RELIABLE REQUESTS-BASED SCRAPER
==================================

When Selenium gets blocked, fall back to smart HTTP requests with:
- Rotating user agents
- Session management
- Header spoofing
- Request timing
"""

import requests
import time
import random
import re
import json
import os
import difflib
import unicodedata
from bs4 import BeautifulSoup
from typing import Dict, Optional, Tuple

try:
    from .country_normalizer import normalize_country_name
except ImportError:
    from country_normalizer import normalize_country_name

class RequestsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
        ]
        self.brand_origin_index = self._load_brand_origin_index()
        self.asin_origin_index = self._load_asin_origin_index()

    def _load_asin_origin_index(self) -> Dict[str, str]:
        """Load historical ASIN->origin hints from cleaned products dataset."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        cleaned_candidates = [
            os.path.join(project_root, 'common', 'data', 'json', 'cleaned_products.json'),
            os.path.join(project_root, 'cleaned_products.json')
        ]

        index: Dict[str, str] = {}
        for path in cleaned_candidates:
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    payload = json.load(file)
                if not isinstance(payload, list):
                    continue

                for row in payload:
                    if not isinstance(row, dict):
                        continue
                    asin = str(row.get('asin', '')).strip().upper()
                    if not asin:
                        continue
                    candidate = (
                        row.get('country_of_origin')
                        or row.get('origin')
                        or row.get('brand_estimated_origin')
                        or row.get('origin_country')
                    )
                    normalized = normalize_country_name(str(candidate or '').strip())
                    if normalized != 'Unknown':
                        index[asin] = normalized
            except Exception as error:
                print(f"⚠️ Could not load ASIN origin index from {path}: {error}")

        if index:
            print(f"📚 Loaded {len(index)} ASIN origin hints from cleaned products")
        return index

    def lookup_asin_origin(self, asin: str) -> str:
        asin_key = str(asin or '').strip().upper()
        if not asin_key:
            return "Unknown"
        return self.asin_origin_index.get(asin_key, "Unknown")

    def _normalize_extraction_text(self, text: str) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize('NFKD', text)
        normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Cf')
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def _normalize_brand_key(self, brand: str) -> str:
        text = (brand or "").lower().strip()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'^(by|visit the|brand:)\s+', '', text)
        text = re.sub(r'\b(store|official|shop|online)\b', ' ', text)
        text = re.sub(r'[^a-z0-9\s&+.-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _load_brand_origin_index(self) -> Dict[str, str]:
        """Load canonical brand origins from common/data/json/brand_locations.json."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        brand_locations_path = os.path.join(project_root, 'common', 'data', 'json', 'brand_locations.json')
        index: Dict[str, str] = {}

        try:
            with open(brand_locations_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for brand_name, payload in data.items():
                if brand_name.startswith('_'):
                    continue
                if not isinstance(payload, dict):
                    continue
                origin_data = payload.get('origin') or {}
                country = origin_data.get('country') if isinstance(origin_data, dict) else None
                if not country:
                    continue

                normalized = self._normalize_brand_key(brand_name)
                if normalized:
                    index[normalized] = country

            print(f"📚 Loaded {len(index)} brand origins from brand_locations.json")
        except Exception as error:
            print(f"⚠️ Could not load brand origin index: {error}")

        return index

    def lookup_brand_origin(self, brand: str) -> Tuple[str, str]:
        """Resolve brand origin via exact, partial, then fuzzy matching."""
        normalized_brand = self._normalize_brand_key(brand)
        if not normalized_brand:
            return "Unknown", "none"

        # 1) Exact normalized match
        if normalized_brand in self.brand_origin_index:
            return self.brand_origin_index[normalized_brand], "brand_locations_exact"

        # 2) Substring containment match (handles minor byline noise)
        for known_brand, country in self.brand_origin_index.items():
            if normalized_brand in known_brand or known_brand in normalized_brand:
                # Avoid weak single-token accidental matches
                if min(len(normalized_brand), len(known_brand)) >= 4:
                    return country, "brand_locations_partial"

        # 3) Fuzzy closest match
        close = difflib.get_close_matches(normalized_brand, list(self.brand_origin_index.keys()), n=1, cutoff=0.88)
        if close:
            matched = close[0]
            return self.brand_origin_index[matched], "brand_locations_fuzzy"

        return "Unknown", "none"
    
    def get_headers(self):
        """Get realistic headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def scrape_product(self, url: str) -> Optional[Dict]:
        """Scrape product using requests"""
        print(f"📡 Requests scraping: {url}")
        
        # Extract ASIN for clean URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if asin_match:
            asin = asin_match.group(1)
            clean_url = f"https://www.amazon.co.uk/dp/{asin}"
        else:
            clean_url = url
            asin = "Unknown"
        
        try:
            # Random delay
            time.sleep(random.uniform(2, 5))

            headers = self.get_headers()
            scraperapi_key = os.environ.get('SCRAPERAPI_KEY')
            if scraperapi_key:
                proxy_url = f"http://api.scraperapi.com?api_key={scraperapi_key}&url={clean_url}&country_code=gb"
                response = self.session.get(proxy_url, timeout=60)
            else:
                response = self.session.get(clean_url, headers=headers, timeout=15)

            print(f"📡 Response: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for bot detection
                if self.is_blocked(soup):
                    print("🚫 Bot detection in requests method")
                    return self.create_intelligent_fallback(url, asin)
                
                # Extract data
                return self.extract_from_soup(soup, asin, clean_url)
            
            else:
                print(f"⚠️ HTTP {response.status_code}")
                return self.create_intelligent_fallback(url, asin)
                
        except Exception as e:
            print(f"📡 Requests error: {e}")
            return self.create_intelligent_fallback(url, asin)
    
    def is_blocked(self, soup) -> bool:
        """Check if we're being blocked"""
        page_text = soup.get_text().lower()
        blocked_indicators = [
            'captcha', 'robot', 'blocked', 'access denied',
            'unusual traffic', 'automated', 'verify you are human'
        ]
        return any(indicator in page_text for indicator in blocked_indicators)
    
    def extract_from_soup(self, soup, asin: str, url: str) -> Dict:
        """Extract product data from HTML"""
        
        # Extract title with improved selectors
        title = "Unknown Product"
        title_selectors = [
            '#productTitle',
            '.product-title',
            '[data-automation-id="product-title"]',
            'h1.a-size-large',
            'h1[data-automation-id="product-title"]',
            'h1 span'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                extracted_title = element.get_text().strip()
                if extracted_title and len(extracted_title) > 5:  # Valid title
                    title = extracted_title
                    break
        
        # Extract brand
        brand = "Unknown"
        brand_selectors = [
            '#bylineInfo',
            '.author.notFaded a',
            '[data-automation-id="byline-info-section"]'
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                brand_text = element.get_text().strip()
                # Clean brand text
                brand = re.sub(r'^(by|visit the|brand:)\s*', '', brand_text, flags=re.IGNORECASE).strip()
                if len(brand) > 50:
                    brand = brand[:50]
                break
        
        # Get all text for analysis
        all_text = soup.get_text()
        
        # 1) Look for origin in technical details first (HIGHEST PRIORITY)
        origin_from_tech = self.extract_origin_from_tech_details(all_text)
        print(f"🔍 Tech details extraction result: '{origin_from_tech}'")
        
        if origin_from_tech != "Unknown":
            origin = origin_from_tech
            origin_source = "technical_details"
            origin_confidence = "high"
            print(f"📍 ✅ Using origin from technical details: {origin}")
        else:
            # 2) Other explicit page sections
            origin_from_explicit = self.extract_origin_from_explicit_sections(soup)
            if origin_from_explicit != "Unknown":
                origin = origin_from_explicit
                origin_source = "explicit_sections"
                origin_confidence = "high"
                print(f"📍 ✅ Using explicit sections fallback: {origin}")
            else:
                # 3) Description / bullets keyword extraction
                origin_from_keywords = self.extract_origin_from_description_bullets(soup)
                if origin_from_keywords != "Unknown":
                    origin = origin_from_keywords
                    origin_source = "description_keywords"
                    origin_confidence = "medium"
                    print(f"📍 ✅ Using description keyword fallback: {origin}")
                else:
                    # 4) Deep text mining
                    origin_from_text_mining = self.extract_origin_from_text_mining(all_text)
                    if origin_from_text_mining != "Unknown":
                        origin = origin_from_text_mining
                        origin_source = "text_mining"
                        origin_confidence = "low"
                        print(f"📍 ✅ Using text mining fallback: {origin}")
                    else:
                        # 5) Brand database fallback
                        brand_origin, source = self.lookup_brand_origin(brand)
                        if brand_origin != "Unknown":
                            origin = brand_origin
                            origin_source = source
                            origin_confidence = "medium"
                            print(f"📍 ✅ Using brand_locations fallback: {origin} (source: {source}, brand: {brand})")
                        else:
                            # 6) ASIN history fallback
                            asin_origin = self.lookup_asin_origin(asin)
                            if asin_origin != "Unknown":
                                origin = asin_origin
                                origin_source = "asin_history"
                                origin_confidence = "low"
                                print(f"📍 ✅ Using ASIN history fallback: {origin} (asin: {asin})")
                            else:
                                # 7) Weak heuristic fallback
                                brand_origin = self.estimate_origin(brand)
                                origin = brand_origin
                                origin_source = "heuristic_brand_default"
                                origin_confidence = "low"
                                print(f"📍 ⚠️ Using heuristic brand fallback: {origin} (from brand: {brand})")
            print(f"📍 NOTE: Technical details did not contain valid origin information")
        
        # Extract weight
        weight = self.extract_weight(all_text)
        # Also try to extract from title
        if weight == 1.0:  # Default weight, try title
            title_weight = self.extract_weight(title)
            if title_weight != 1.0:
                weight = title_weight
                print(f"⚖️ Found weight in title: {weight} kg")
            else:
                print(f"⚖️ Using default weight: {weight} kg")
        else:
            print(f"⚖️ Found weight in tech details: {weight} kg")
        
        # Smart material detection - check for protein powder first
        if any(keyword in title.lower() for keyword in ['protein', 'powder', 'mass gainer', 'supplement', 'whey', 'casein']):
            material = "Plastic"  # Protein powder containers are typically plastic
            
            # For protein powder, if weight is suspiciously low, try better extraction
            if weight < 0.5:  # Protein powder should be at least 500g
                print(f"⚠️ Protein powder weight seems low ({weight}kg), trying enhanced extraction...")
                
                # Look for common protein powder weights in title/text
                protein_weight_patterns = [
                    r'(\d+(?:\.\d+)?)\s*kg\b',  # "1kg", "2.5kg"
                    r'(\d+(?:\.\d+)?)\s*g\b',   # "900g", "1000g"
                    r'(\d+(?:\.\d+)?)\s*lbs?\b', # "5lb", "2.2lbs"
                ]
                
                for pattern in protein_weight_patterns:
                    matches = re.findall(pattern, title.lower())
                    if matches:
                        try:
                            weight_val = float(matches[0])
                            if pattern.endswith('g\\b'):  # Grams
                                if weight_val >= 500:  # At least 500g
                                    weight = weight_val / 1000
                                    print(f"⚖️ Found better protein weight in title: {weight}kg")
                                    break
                            elif pattern.endswith('kg\\b'):  # Kilograms
                                if 0.5 <= weight_val <= 5:  # Reasonable protein weight
                                    weight = weight_val
                                    print(f"⚖️ Found better protein weight in title: {weight}kg")
                                    break
                            elif pattern.endswith('lbs?\\b'):  # Pounds
                                weight_kg = weight_val * 0.453592
                                if 0.5 <= weight_kg <= 5:  # Reasonable protein weight
                                    weight = weight_kg
                                    print(f"⚖️ Found better protein weight in title: {weight}kg")
                                    break
                        except:
                            continue
        else:
            material = self.detect_material(title, all_text)
        
        result = {
            "title": title,
            "origin": origin,
            "country_of_origin": origin,
            "origin_source": origin_source,
            "origin_confidence": origin_confidence,
            "weight_kg": weight,
            "dimensions_cm": [20, 15, 10],
            "material_type": material,
            "recyclability": "Medium",
            "eco_score_ml": "C",
            "transport_mode": "Ship", 
            "carbon_kg": None,
            "brand": brand,
            "asin": asin,
            "data_quality_score": 85,
            "confidence": "High",
            "method": "Requests Scraping"
        }
        
        print(f"📡 Requests extracted: {title[:50]}...")
        return result
    
    def create_intelligent_fallback(self, url: str, asin: str) -> Dict:
        """Create intelligent fallback based on URL analysis"""
        print("🧠 Creating intelligent fallback...")
        
        # Analyze URL for clues
        url_lower = url.lower()
        
        # Protein powder detection
        if 'protein' in url_lower:
            title = "Protein Powder Supplement"
            material = "Plastic"
            weight = 2.5  # Typical protein powder weight
            brand = "Unknown Nutrition Brand"
            
        # Electronic detection  
        elif any(term in url_lower for term in ['electronic', 'phone', 'laptop', 'tablet']):
            title = "Electronic Device"
            material = "Mixed"
            weight = 0.8
            brand = "Unknown Electronics"
            
        # Book detection
        elif 'book' in url_lower:
            title = "Book"
            material = "Paper"
            weight = 0.3
            brand = "Unknown Publisher"
            
        # Clothing detection
        elif any(term in url_lower for term in ['clothing', 'shirt', 'dress', 'shoes']):
            title = "Clothing Item"
            material = "Fabric"
            weight = 0.2
            brand = "Unknown Fashion"
            
        else:
            # Generic fallback
            title = "Amazon Product"
            material = "Unknown"
            weight = 1.0
            brand = "Unknown Brand"
        
        return {
            "title": title,
            "origin": "UK",
            "weight_kg": weight,
            "dimensions_cm": [15, 10, 8],
            "material_type": material,
            "recyclability": "Medium",
            "eco_score_ml": "C",
            "transport_mode": "Ship",
            "carbon_kg": None,
            "brand": brand,
            "asin": asin,
            "data_quality_score": 60,  # Lower quality for fallback
            "confidence": "Medium",
            "method": "Intelligent URL Analysis"
        }
    
    def extract_weight(self, text: str) -> float:
        """Extract weight from text with improved precision"""
        text_lower = text.lower()

        # Priority patterns - look for specific weight fields first
        # Amazon UK uses \u200e (left-to-right mark) as separators in tech tables,
        # e.g. "Item Weight \u200e : \u200e 5.94 kg" — patterns must include these.
        priority_patterns = [
            # Amazon-style "Item Weight" / "Package Weight" with unicode separators
            (r'(?:item|package|net|gross)?\s*weight[\s\u200e\u200f]*:[\s\u200e\u200f]*(\d+(?:\.\d+)?)\s*(kg|kilograms?)', 'kg'),
            (r'(?:item|package|net|gross)?\s*weight[\s\u200e\u200f]*:[\s\u200e\u200f]*(\d+(?:\.\d+)?)\s*(g|grams?)', 'g'),
            # Plain weight field (no unicode)
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(kg|kilograms?)', 'kg'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(g|grams?)', 'g'),
            # Product dimensions trailing weight (e.g., "11 x 7 x 27 cm; 600 g")
            (r';\s*(\d+(?:\.\d+)?)\s*(kg)\b', 'kg'),
            (r';\s*(\d+(?:\.\d+)?)\s*(g)\b', 'g'),
            # Units field patterns (e.g., "Units: 600.0 gram")
            (r'units[:\s]+(\d+(?:\.\d+)?)\s*(g|gram)', 'g'),
            # Standalone kg/g in title (lower priority — broad match)
            (r'\b(\d+(?:\.\d+)?)\s*kg\b', 'kg'),
            (r'\b(\d+(?:\.\d+)?)\s*g\b(?!ram)', 'g'),  # Avoid "program"
        ]
        
        # Check each pattern in priority order
        for pattern, unit_type in priority_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                for match in matches:
                    try:
                        if isinstance(match, tuple):
                            weight_val = float(match[0])
                        else:
                            weight_val = float(match)
                        
                        # Skip very small values that are likely errors
                        if weight_val < 0.01 and unit_type == 'kg':
                            continue
                        if weight_val < 10 and unit_type == 'g':
                            continue
                            
                        # Convert to kg
                        if unit_type == 'kg':
                            return weight_val
                        elif unit_type == 'g':
                            return weight_val / 1000
                    except:
                        continue
        
        # Pound patterns as fallback
        lb_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)',
            r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)'
        ]
        
        for pattern in lb_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    weight = float(matches[0])
                    return weight * 0.453592  # Convert lbs to kg
                except:
                    continue
        
        return 1.0  # Default weight
    
    def detect_material(self, title: str, text: str) -> str:
        """Detect material type — checks title first to avoid false positives from page text."""
        title_lower = title.lower()

        materials = {
            'Glass':    ['glass', 'crystal', 'borosilicate', 'tempered glass', 'stained glass'],
            'Ceramic':  ['ceramic', 'porcelain', 'terracotta', 'stoneware', 'earthenware',
                         'pottery', 'clay', 'bisque'],
            'Stone':    ['marble', 'granite', 'slate', 'quartz stone', 'quartz countertop', 'sandstone',
                         'limestone', 'travertine'],
            'Wood':     ['wood', 'wooden', 'timber', 'bamboo', 'acacia', 'oak', 'pine',
                         'teak', 'walnut', 'mahogany', 'birch', 'cedar', 'rattan',
                         'wicker', 'cork', 'plywood', 'mdf', 'hardwood'],
            'Metal':    ['metal', 'steel', 'aluminum', 'aluminium', 'stainless', 'iron',
                         'brass', 'copper', 'zinc', 'titanium', 'chrome', 'cast iron',
                         'carbon steel', 'alloy', 'pewter', 'nickel'],
            'Paper':    ['paper', 'cardboard', 'book', 'notebook', 'journal',
                         'paperback', 'hardback', 'kraft'],
            'Leather':  ['leather', 'suede', 'nubuck', 'faux leather', 'pu leather',
                         'vegan leather', 'patent leather', 'genuine leather'],
            'Fabric':   ['fabric', 'cotton', 'polyester', 'clothing', 'textile',
                         'plush', 'cuddly', 'stuffed', 'fleece', 'velvet',
                         'wool', 'woollen', 'knit', 'knitted', 'yarn', 'felt',
                         'teddy', 'plushie', 'denim', 'silk', 'linen', 'nylon',
                         'woven', 'cashmere', 'viscose', 'rayon', 'spandex', 'lycra',
                         'canvas', 'microfibre', 'microfiber', 'satin', 'tweed',
                         'flannel', 'chenille', 'jersey', 'chiffon'],
            'Rubber':   ['rubber', 'latex', 'neoprene', 'silicone', 'memory foam',
                         'eva foam', 'gel pad', 'foam mat', 'resistance band',
                         'exercise band', 'gym mat', 'foam roller'],
            'Plastic':  ['plastic', 'polymer', 'polypropylene', 'polyethylene', 'bpa',
                         'pvc', 'acrylic', 'resin', 'abs plastic', 'hard shell',
                         'hardshell', 'polycarbonate', 'hdpe', 'thermoplastic', 'perspex'],
            'Mixed':    ['electronic', 'device', 'phone', 'laptop', 'tablet',
                         'headphone', 'speaker', 'keyboard', 'monitor', 'router',
                         'printer', 'camera', 'smartwatch', 'console', 'gaming',
                         'earphone', 'earbud', 'wearable', 'television', 'smart tv',
                         'qled', 'oled', 'smart home', 'smart plug', 'smart bulb'],
        }

        # Check title first — most reliable signal
        for material, keywords in materials.items():
            if any(kw in title_lower for kw in keywords):
                return material

        # Fall back to full page text with two rules:
        # 1. Order from most distinctive to least — specific compound terms first.
        # 2. Metal uses COMPOUND-ONLY keywords for text scan. Single words like
        #    'iron', 'chrome', 'nickel', 'copper' appear on every Amazon page
        #    (reviews, cross-sells, pool chemistry, "chrome extension", etc.).
        #    Genuine metal products always use phrases like "stainless steel" or
        #    "cast iron" — those are unambiguous in any context.
        # 3. Mixed (electronics) is excluded — 'device'/'phone' appear in nav/cross-sells.
        text_metal_keywords = [
            'stainless steel', 'cast iron', 'carbon steel', 'wrought iron',
            'aluminium alloy', 'aluminum alloy', 'galvanised steel', 'galvanized steel',
            'mild steel', 'high carbon', 'tool steel', 'spring steel',
        ]
        text_scan_order = [
            'Paper', 'Leather', 'Rubber', 'Wood', 'Ceramic',
            'Fabric', 'Plastic', 'Stone', 'Glass',
        ]
        text_lower = text.lower()
        for material in text_scan_order:
            if material in materials and any(kw in text_lower for kw in materials[material]):
                return material
        if any(kw in text_lower for kw in text_metal_keywords):
            return 'Metal'

        return 'Unknown'
    
    def estimate_origin(self, brand: str) -> str:
        """Estimate origin from brand"""
        if not brand or brand == "Unknown":
            return "UK"
        
        # Enhanced brand-to-origin mapping for common brands
        brand_origins = {
            # Protein/Supplement brands
            'optimum nutrition': 'USA',
            'dymatize': 'USA',  # Actually made in Germany but US brand
            'bsn': 'USA',
            'muscletech': 'USA',
            'cellucor': 'USA',
            'gat sport': 'USA',
            'evlution': 'USA',
            'bulk protein': 'England',  # Manchester-based
            'bulk powders': 'England',  # Essex-based
            'myprotein': 'England',     # Manchester-based
            'the protein works': 'England',  # Cheshire-based
            'applied nutrition': 'UK',
            'phd nutrition': 'UK',
            'sci-mx': 'UK',
            'sci mx': 'UK',
            'free soul': 'England',     # London-based
            'grenade': 'England',       # Birmingham-based
            'nxt nutrition': 'UK',      # UK-based supplement company
            'usn uk': 'England',        # UK operations
            'usn': 'South Africa',
            'mutant': 'Canada',
            'allmax': 'Canada',
            'scitec': 'Hungary',
            'weider': 'Germany',
            'esn': 'Germany',
            'biotech usa': 'Hungary',
            'whole supp': 'UK',         # UK-based supplement company
            'wholesupp': 'UK',          # Alternative brand format
            # Electronics
            'samsung': 'South Korea',
            'apple': 'China',
            'sony': 'Japan',
            'lg': 'South Korea',
            'huawei': 'China',
            'xiaomi': 'China',
            'lenovo': 'China',
            'asus': 'Taiwan',
            'dell': 'China',
            'hp': 'China',
            'avlash': 'China'
        }
        
        brand_lower = brand.lower()
        for brand_key, origin in brand_origins.items():
            if brand_key in brand_lower:
                return origin
        
        return "UK"  # Default
    
    def extract_origin_from_tech_details(self, text: str) -> str:
        """Extract origin from Amazon's technical details with improved accuracy"""
        text_lower = text.lower()
        
        # Debug: Check for key countries in the text
        debug_countries = ['belgium', 'germany', 'england', 'uk', 'usa', 'china', 'pakistan', 'india', 'bangladesh', 'turkey', 'vietnam', 'indonesia']
        for country in debug_countries:
            if country in text_lower:
                country_pos = text_lower.find(country)
                context_start = max(0, country_pos - 80)
                context_end = min(len(text_lower), country_pos + 80)
                context = text_lower[context_start:context_end]
                print(f"🔍 DEBUG: Found '{country}' in text: '{context}'")
        
        # Look for country of origin patterns with improved regex (ordered by specificity)
        # Note: Amazon HTML uses Unicode left-to-right marks (\u200e) as separators in
        # technical detail tables, e.g. "Country of Origin \u200e : \u200e Cambodia"
        patterns = [
            # Handles Amazon's actual HTML format with \u200e separators AND plain colons
            # Also handles "Country/Region of Origin" (Amazon UK format)
            (r"country(?:\s*/\s*region)?\s+of\s+origin[\s\u200e\u200f:]*([a-zA-Z][a-zA-Z\s]{1,24}?)(?=\s*[\n\r]|\s{3,}|\s*(?:brand|asin|model|package|item|manufacturer|best|colour|color|size|weight|$))", "country_of_origin_broad"),

            # Made in patterns (high confidence)
            (r"made\s+in[\s\u200e\u200f:]*([a-zA-Z][a-zA-Z\s]{1,24}?)(?=\s*[\n\r]|\s{2,}|\s*(?:brand|asin|$))", "made_in"),

            # Manufactured in patterns (medium confidence)
            (r"manufactured\s+in[:\s]*\b([a-zA-Z][a-zA-Z\s]{1,20})\b", "manufactured_in"),

            # Product of patterns (medium confidence)
            (r"product\s+of[:\s]*\b([a-zA-Z][a-zA-Z\s]{1,20})\b", "product_of"),

            # Origin patterns (medium confidence)
            (r"origin[:\s]*\b([a-zA-Z][a-zA-Z\s]{1,20})\b", "origin")
        ]
        
        for pattern, pattern_name in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            print(f"🔍 Pattern '{pattern_name}': {matches}")
            
            if matches:
                # Take the first match and clean it
                candidate = matches[0].strip()
                candidate = re.sub(r'[^a-zA-Z\s\-]', ' ', candidate)
                candidate = re.sub(r'\s+', ' ', candidate).strip()
                
                # Remove any trailing words that aren't part of country name
                candidate = re.sub(r'\s*(brand|format|age|additional|country|manufacturer|item|model|dimensions?).*$', '', candidate).strip()

                # Reject obvious non-country text fragments from noisy technical details
                invalid_tokens = [
                    "splinter", "crack", "break", "bpa", "plastic", "cutlery", "disposable",
                    "friendly", "set", "piece", "pack", "size", "weight", "model", "item"
                ]
                candidate_lower = candidate.lower()
                if any(token in candidate_lower for token in invalid_tokens):
                    print(f"🔍 ⚠️ Rejecting non-country candidate: '{candidate}'")
                    continue
                
                print(f"🔍 Candidate after cleaning: '{candidate}'")
                
                if candidate and len(candidate) >= 2:  # At least 2 characters
                    normalized = normalize_country_name(candidate)
                    if normalized != "Unknown":
                        result = normalized
                        print(f"🔍 ✅ Normalized '{candidate}' -> '{result}' using pattern '{pattern_name}'")
                        return result
                    else:
                        print(f"🔍 ⚠️ Rejected non-canonical origin candidate: '{candidate}'")
        
        print(f"🔍 ❌ No origin found in technical details")
        return "Unknown"

    def extract_origin_from_explicit_sections(self, soup: BeautifulSoup) -> str:
        """Extract from explicit sections like manufacturer address/spec rows."""
        selectors = [
            'table#productDetails_techSpec_section_1',
            'table#productDetails_detailBullets_sections1',
            'div#productDetails_db_sections',
            'div#detailBullets_feature_div',
            '.po-attribute-list',
            'table'
        ]
        key_markers = [
            'country of origin',
            'manufacturer',
            'manufacturer address',
            'manufactured in',
            'imported from',
            'product of'
        ]

        for selector in selectors:
            for node in soup.select(selector):
                section_text = self._normalize_extraction_text(node.get_text(' ', strip=True)).lower()
                if not section_text:
                    continue
                if not any(marker in section_text for marker in key_markers):
                    continue

                country = self.extract_origin_from_text_mining(section_text)
                if country != "Unknown":
                    return country

        return "Unknown"

    def extract_origin_from_description_bullets(self, soup: BeautifulSoup) -> str:
        """Extract from description bullets and product description sections."""
        selectors = [
            '#feature-bullets li',
            '#feature-bullets .a-list-item',
            '#productDescription',
            '#aplus',
            '.a-unordered-list .a-list-item'
        ]

        text_parts = []
        for selector in selectors:
            for node in soup.select(selector):
                value = self._normalize_extraction_text(node.get_text(' ', strip=True))
                if value:
                    text_parts.append(value)

        if not text_parts:
            return "Unknown"

        combined = ' '.join(text_parts)
        return self.extract_origin_from_text_mining(combined)

    def extract_origin_from_text_mining(self, text: str) -> str:
        """Deep text mining for made in/imported from/ships from patterns."""
        normalized = self._normalize_extraction_text(text).lower()
        if not normalized:
            return "Unknown"

        patterns = [
            r'country\s+of\s+origin[:\s-]*([a-z][a-z\s\-]{2,30})',
            r'manufactured\s+in[:\s-]*([a-z][a-z\s\-]{2,30})',
            r'made\s+in[:\s-]*([a-z][a-z\s\-]{2,30})',
            r'imported\s+from[:\s-]*([a-z][a-z\s\-]{2,30})',
            r'product\s+of[:\s-]*([a-z][a-z\s\-]{2,30})',
            r'ships\s+from[:\s-]*([a-z][a-z\s\-]{2,30})'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, normalized, re.IGNORECASE)
            for match in matches:
                candidate = re.sub(r'\s+(brand|format|age|additional|manufacturer|item|model|dimensions?|seller|store).*$', '', match).strip()
                if not candidate:
                    continue
                country = normalize_country_name(candidate)
                if country != "Unknown":
                    return country

        return "Unknown"

def scrape_with_requests(url: str) -> Optional[Dict]:
    """Enhanced scraping with anti-bot strategies"""
    
    # Try enhanced scraper first
    try:
        import sys
        import os
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        sys.path.insert(0, project_root)
        
        from enhanced_scraper_fix import EnhancedAmazonScraper
        
        scraper = EnhancedAmazonScraper()
        result = scraper.scrape_product_enhanced(url)
        
        if result and result.get('title', 'Unknown Product') != 'Unknown Product':
            print(f"✅ Enhanced scraper success: {result.get('title', '')[:50]}...")
            # Convert to expected format
            return {
                'title': result.get('title', 'Unknown Product'),
                'origin': result.get('origin', 'Unknown'), 
                'weight_kg': result.get('weight_kg', 1.0),
                'brand': result.get('brand', 'Unknown'),
                'material_type': result.get('material_type', 'Unknown'),
                'asin': result.get('asin', 'Unknown'),
                'dimensions_cm': [15, 10, 8],  # Default dimensions
                'recyclability': 'Medium'      # Default recyclability
            }
    except Exception as e:
        print(f"🔧 Enhanced scraper failed, using fallback: {e}")
    
    # Fallback to original method
    print("🔄 Falling back to original RequestsScraper...")
    scraper = RequestsScraper()
    return scraper.scrape_product(url)

if __name__ == "__main__":
    test_url = "https://www.amazon.co.uk/dp/B000GIPJ0M"
    result = scrape_with_requests(test_url)
    print(f"Result: {result}")