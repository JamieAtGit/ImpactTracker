#!/usr/bin/env python3
"""
Production Amazon Scraper with enhanced anti-detection and full URL support
Handles complete Amazon URLs as users provide them with 90%+ reliability target
"""

import requests
import time
import random
import json
import re
import unicodedata
import os
import difflib
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse

try:
    from .url_processor import AmazonURLProcessor
    from .category_detector import CategoryDetector
    from .country_normalizer import normalize_country_name as normalize_country_name_shared
except ImportError:
    from url_processor import AmazonURLProcessor
    from category_detector import CategoryDetector
    from country_normalizer import normalize_country_name as normalize_country_name_shared


class ProductionAmazonScraper:
    """Production-ready Amazon scraper with enhanced reliability"""
    
    def __init__(self):
        self.session = requests.Session()
        self.url_processor = AmazonURLProcessor()
        self.category_detector = CategoryDetector()
        self.brand_origin_index = self._load_brand_origin_index()
        
        # Enhanced user agent rotation (20+ realistic signatures)
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Firefox on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15',
            
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Mobile browsers
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 14; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0',
            'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36'
        ]
        
        # Initialize session with realistic settings
        self.setup_session()
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2.0
        self.max_delay = 16.0
        
        # Success tracking
        self.request_count = 0
        self.success_count = 0

    def _normalize_brand_key(self, brand: str) -> str:
        text = (brand or "").lower().strip()
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'^(by|visit the|brand:)\s+', '', text)
        text = re.sub(r'\b(store|official|shop|online)\b', ' ', text)
        text = re.sub(r'[^a-z0-9\s&+.-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _load_brand_origin_index(self) -> Dict[str, str]:
        """Load normalized brand -> country map from canonical brand_locations.json."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        path = os.path.join(project_root, 'common', 'data', 'json', 'brand_locations.json')
        index: Dict[str, str] = {}

        try:
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for brand_name, payload in data.items():
                if str(brand_name).startswith('_'):
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

            print(f"📚 Production scraper loaded {len(index)} brand origins")
        except Exception as error:
            print(f"⚠️ Could not load production brand origin index: {error}")

        return index

    def lookup_brand_origin(self, brand: str) -> str:
        """Resolve brand origin via exact, partial, then fuzzy matching."""
        normalized_brand = self._normalize_brand_key(brand)
        if not normalized_brand:
            return "Unknown"

        if normalized_brand in self.brand_origin_index:
            return self.brand_origin_index[normalized_brand]

        for known_brand, country in self.brand_origin_index.items():
            if normalized_brand in known_brand or known_brand in normalized_brand:
                if min(len(normalized_brand), len(known_brand)) >= 4:
                    return country

        close = difflib.get_close_matches(normalized_brand, list(self.brand_origin_index.keys()), n=1, cutoff=0.95)
        if close:
            return self.brand_origin_index[close[0]]

        return "Unknown"
        
    def setup_session(self):
        """Setup session with realistic browser behavior"""
        # Set persistent cookies that look realistic
        self.session.cookies.update({
            'session-id': f'262-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}',
            'ubid-acbuk': f'{random.randint(100, 999)}-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}',
            'i18n-prefs': 'GBP',
            'lc-acbuk': 'en_GB',
            'at-acbuk': 'Atza|' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=200)),
            'sess-at-acbuk': '"' + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', k=150)) + '"',
        })
        
    def get_realistic_headers(self, url: str, referer: str = None) -> Dict[str, str]:
        """Generate realistic browser headers"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        # Add browser-specific headers
        if 'Chrome' in user_agent:
            version = re.search(r'Chrome/(\d+)', user_agent)
            if version:
                chrome_version = version.group(1)
                headers.update({
                    'Sec-CH-UA': f'"Not_A Brand";v="8", "Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}"',
                    'Sec-CH-UA-Mobile': '?0',
                    'Sec-CH-UA-Platform': '"Windows"' if 'Windows' in user_agent else '"macOS"' if 'Mac' in user_agent else '"Linux"',
                    'Sec-CH-UA-Platform-Version': '"10.0.0"' if 'Windows' in user_agent else '"13.0.0"'
                })
        
        if referer:
            headers['Referer'] = referer
            
        return headers
        
    def exponential_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0.1, 0.5) * delay
        return delay + jitter
        
    def is_blocked_or_captcha(self, soup: BeautifulSoup) -> bool:
        """Enhanced detection of blocking or CAPTCHA pages"""
        if not soup:
            return True
            
        page_text = soup.get_text().lower()
        title = soup.find('title')
        title_text = title.get_text().lower() if title else ""
        
        # Common blocking indicators
        blocking_indicators = [
            'captcha', 'robot', 'automated', 'unusual traffic',
            'verify you are human', 'access denied', 'blocked',
            'sorry, something went wrong', 'try again later',
            'temporarily unavailable', 'service unavailable',
            'click the button below to continue'
        ]
        
        # Check page text and title
        for indicator in blocking_indicators:
            if indicator in page_text or indicator in title_text:
                return True
                
        # Check for CAPTCHA forms
        captcha_forms = soup.find_all('form', {'action': re.compile(r'captcha', re.I)})
        if captcha_forms:
            return True
            
        # Check for missing essential elements (sign of error page)
        if not soup.find('title') or len(page_text.strip()) < 100:
            return True
            
        return False
        
    def make_request_with_retry(self, url: str, strategy_name: str = "direct") -> Optional[requests.Response]:
        """Make HTTP request with exponential backoff retry logic"""
        self.request_count += 1
        
        for attempt in range(self.max_retries):
            try:
                # Add realistic delay between requests
                if attempt > 0:
                    delay = self.exponential_backoff_delay(attempt - 1)
                    print(f"⏳ Retry {attempt}/{self.max_retries} after {delay:.1f}s delay")
                    time.sleep(delay)
                else:
                    # Random delay even for first request (human-like)
                    time.sleep(random.uniform(1.0, 3.0))
                
                # Get headers
                headers = self.get_realistic_headers(url)
                
                print(f"🌐 [{strategy_name}] Making request to: {url[:60]}{'...' if len(url) > 60 else ''}")
                
                # Make request
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=20,
                    allow_redirects=True
                )
                
                print(f"📊 Response: {response.status_code} ({len(response.content)} bytes)")
                
                if response.status_code == 200:
                    # Quick check if we got blocked
                    soup = BeautifulSoup(response.content, 'html.parser')
                    if not self.is_blocked_or_captcha(soup):
                        self.success_count += 1
                        return response
                    else:
                        print(f"🚫 Blocked or CAPTCHA detected")
                        
                elif response.status_code == 503:
                    print(f"⚠️ Service unavailable (503) - will retry")
                    
                elif response.status_code == 429:
                    print(f"⚠️ Rate limited (429) - will retry with longer delay")
                    time.sleep(random.uniform(5.0, 10.0))
                    
                elif response.status_code in [404, 410]:
                    print(f"❌ Product not found ({response.status_code}) - no retry")
                    break  # Don't retry for missing products
                    
                else:
                    print(f"⚠️ HTTP {response.status_code} - will retry")
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout - attempt {attempt + 1}/{self.max_retries}")
                
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error - attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                
            except Exception as e:
                print(f"❌ Unexpected error - attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                
        print(f"💥 All {self.max_retries} attempts failed")
        return None
        
    def scrape_with_full_url(self, user_url: str) -> Optional[Dict[str, Any]]:
        """
        Main scraping method that handles full URLs as users provide them
        Uses multi-tier fallback strategy for maximum reliability
        """
        print(f"\n🚀 Starting production scrape for: {user_url}")
        print("=" * 70)
        
        # Validate URL first
        validation = self.url_processor.validate_amazon_url(user_url)
        if not validation['is_valid']:
            print(f"❌ Invalid Amazon URL: {', '.join(validation['issues'])}")
            return None
            
        print(f"✅ Valid Amazon URL - Domain: {validation['domain']}, Type: {validation['url_type']}")
        
        # Get processing strategies in priority order
        strategies = self.url_processor.get_processing_strategies(user_url)
        
        if not strategies:
            print(f"❌ No processing strategies available")
            return None
            
        print(f"📋 Available strategies: {len(strategies)}")
        
        # Try each strategy in order
        for i, strategy in enumerate(strategies, 1):
            print(f"\n🎯 Strategy {i}/{len(strategies)}: {strategy['name']}")
            print(f"   Description: {strategy['description']}")
            
            if strategy['name'] == 'search_fallback':
                # Special handling for search fallback
                result = self.try_search_fallback(strategy)
            else:
                # Standard URL scraping
                result = self.try_url_strategy(strategy)
                
            if result:
                print(f"✅ Strategy '{strategy['name']}' succeeded!")
                
                # Add metadata about which strategy worked
                result['scraping_metadata'] = {
                    'successful_strategy': strategy['name'],
                    'strategy_priority': strategy['priority'],
                    'original_url': user_url,
                    'successful_url': strategy['url'],
                    'attempts_made': i,
                    'success_rate': f"{self.success_count}/{self.request_count}"
                }
                
                return result
            else:
                print(f"❌ Strategy '{strategy['name']}' failed")
                
        print(f"\n💥 All {len(strategies)} strategies failed")
        return None
        
    def try_url_strategy(self, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try scraping with a specific URL strategy"""
        response = self.make_request_with_retry(strategy['url'], strategy['name'])
        
        if not response:
            return None
            
        # Parse the response
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product data using our proven extraction methods
        return self.extract_product_data(soup, strategy)
        
    def try_search_fallback(self, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try search-based fallback approach"""
        print(f"🔍 Searching for: {', '.join(strategy.get('search_terms', []))}")
        
        response = self.make_request_with_retry(strategy['url'], strategy['name'])
        
        if not response:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find product in search results
        product_links = soup.select('h2 a[href*="/dp/"], h2 a[href*="/gp/product/"]')
        
        if product_links:
            # Take the first search result
            first_result = product_links[0]
            title = first_result.get_text().strip()
            
            print(f"🎯 Found search result: {title[:50]}...")
            
            # Create basic product data from search results
            return {
                'title': title,
                'brand': 'Unknown',
                'weight_kg': 1.0,  # Default weight
                'origin': 'Unknown',
                'material_type': 'Mixed',
                'confidence_score': 0.3,  # Lower confidence for search results
                'extraction_source': 'search_results'
            }
            
        return None
        
    def extract_product_data(self, soup: BeautifulSoup, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract product data using our proven extraction methods with category intelligence
        This integrates the weight extraction success we achieved
        """
        data = {}
        
        # Extract title first (needed for category detection)
        title = self.extract_title(soup)
        data['title'] = title
        
        # Detect category for intelligent extraction
        url = strategy.get('url', '')
        category_info = self.category_detector.detect_category(url, title, soup)
        data['category'] = category_info['category']
        data['category_confidence'] = category_info['confidence']
        
        print(f"🏷️ Detected category: {category_info['category']} (confidence: {category_info['confidence']:.1%})")
        
        # Extract brand (category-aware)
        brand = self.extract_brand_category_aware(soup, category_info['category'])
        data['brand'] = brand
        
        # Extract weight using our proven method (with category validation)
        weight = self.extract_weight_enhanced_category_aware(soup, category_info['category'])
        data['weight_kg'] = weight
        
        # Extract origin with source metadata
        origin, origin_source = self.extract_origin_with_source(soup, title, brand)
        data['origin'] = origin
        data['country_of_origin'] = origin
        data['origin_source'] = origin_source
        if origin_source in {'product_details'}:
            data['origin_confidence'] = 'high'
        elif origin_source in {'manufacturer_contact', 'specifications'}:
            data['origin_confidence'] = 'medium'
        elif origin_source in {'brand_mapping'}:
            data['origin_confidence'] = 'medium'
        elif origin_source in {'title_description', 'raw_text'}:
            data['origin_confidence'] = 'low'
        else:
            data['origin_confidence'] = 'unknown'
        
        # Extract material (category-aware)
        material = self.guess_material_from_title_category_aware(title, category_info['category'])
        data['material_type'] = material
        
        # Calculate confidence score
        confidence = self.calculate_confidence_score(data, category_info)
        data['confidence_score'] = confidence
        
        # Add extraction metadata
        data['extraction_source'] = 'direct_scraping'
        data['category_evidence'] = category_info.get('evidence', [])
        
        print(f"✅ Extracted: {title[:40]}... | Weight: {weight}kg | Brand: {brand}")
        
        return data
        
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title using multiple selectors"""
        title_selectors = [
            '#productTitle',
            'span#productTitle',
            '.product-title',
            'h1.a-spacing-none',
            '[data-automation-id="product-title"]',
            '.pdTab h1',
            'h1'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 5:
                    return title[:200]  # Limit length
                    
        return "Unknown Product"
        
    def extract_brand(self, soup: BeautifulSoup) -> str:
        """Extract brand using multiple selectors"""
        brand_selectors = [
            '#bylineInfo',
            '.po-brand .po-break-word',
            'a#bylineInfo',
            '.brand',
            '[data-testid="byline-info"]'
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                brand = element.get_text().strip()
                if brand and 'visit' not in brand.lower():
                    return brand[:100]
                    
        return "Unknown"
        
    def extract_brand_category_aware(self, soup: BeautifulSoup, category: str) -> str:
        """Extract brand with category-specific intelligence"""
        # For books, don't detect authors as brands
        if category == 'books' and not self.category_detector.should_detect_brand(category):
            return "Unknown"
            
        # Standard brand extraction
        brand = self.extract_brand(soup)
        
        # Post-process based on category
        if category == 'books' and brand != "Unknown":
            # Check if this is an author pattern
            author_patterns = [
                r'by\s+',
                r'author[:\s]*',
                r'\(author\)',
                r'visit the .* store'
            ]
            
            brand_lower = brand.lower()
            for pattern in author_patterns:
                if re.search(pattern, brand_lower):
                    print(f"🔍 Book category: Skipping author '{brand}' as brand")
                    return "Unknown"
        
        return brand
        
    def extract_weight_enhanced(self, soup: BeautifulSoup) -> float:
        """
        Enhanced weight extraction - our proven method that works for protein powder
        Priority: Specifications → Details → Title → Default
        """
        print("🔍 Starting enhanced weight extraction...")
        
        # PRIORITY 1: Amazon specifications table
        weight = self.extract_weight_from_specs(soup)
        if weight > 0:
            print(f"✅ Found weight in specifications: {weight}kg")
            return weight
            
        # PRIORITY 2: Product details sections
        weight = self.extract_weight_from_details(soup)
        if weight > 0:
            print(f"✅ Found weight in details: {weight}kg")
            return weight
            
        # PRIORITY 3: Title (avoiding nutritional content)
        weight = self.extract_weight_from_title(soup)
        if weight > 0:
            print(f"✅ Found weight in title: {weight}kg")
            return weight
            
        print("⚠️ No weight found, using default 1.0kg")
        return 1.0
        
    def extract_weight_enhanced_category_aware(self, soup: BeautifulSoup, category: str) -> float:
        """Enhanced weight extraction with category-specific validation"""
        # Use our proven weight extraction method
        weight = self.extract_weight_enhanced(soup)
        
        # Validate weight against category expectations
        validation = self.category_detector.validate_weight_for_category(weight, category)
        
        if not validation['is_valid'] and weight != 1.0:  # Don't warn for default weight
            print(f"⚠️ Weight validation: {validation['issue']}")
            
            # For extreme outliers, use category default
            expected_range = validation['expected_range']
            min_weight, max_weight = expected_range
            
            if weight < min_weight / 10 or weight > max_weight * 10:  # Extreme outlier
                category_default = (min_weight + max_weight) / 2
                print(f"🔧 Using category default weight: {category_default}kg")
                return category_default
        
        return weight
        
    def extract_weight_from_specs(self, soup: BeautifulSoup) -> float:
        """Extract weight from Amazon specifications table"""
        spec_selectors = [
            'table#productDetails_techSpec_section_1',
            'table#productDetails_detailBullets_sections1',
            'div#productDetails_db_sections',
            'div#detailBullets_feature_div',
            'div.pdTab',
            '#feature-bullets'
        ]
        
        for selector in spec_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                
                # Weight specification patterns
                patterns = [
                    r'item\s*weight\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(g|gram|kg|kilogram|lb|pound|oz|ounce)',
                    r'net\s*weight\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(g|gram|kg|kilogram|lb|pound|oz|ounce)',
                    r'weight\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(g|gram|kg|kilogram|lb|pound|oz|ounce)',
                    r'(\d+(?:\.\d+)?)\s*(g|gram|kg|kilogram)(?!\s*protein)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        try:
                            weight_val = float(match[0])
                            unit = match[1].lower()
                            
                            # Convert to kg
                            if unit in ['g', 'gram']:
                                weight_kg = weight_val / 1000
                            elif unit in ['kg', 'kilogram']:
                                weight_kg = weight_val
                            elif unit in ['lb', 'pound']:
                                weight_kg = weight_val * 0.453592
                            elif unit in ['oz', 'ounce']:
                                weight_kg = weight_val * 0.0283495
                            else:
                                continue
                                
                            if 0.01 <= weight_kg <= 100:
                                return weight_kg
                                
                        except (ValueError, IndexError):
                            continue
                            
        return 0
        
    def extract_weight_from_details(self, soup: BeautifulSoup) -> float:
        """Extract weight from product details sections"""
        detail_selectors = [
            '#feature-bullets ul',
            '#feature-bullets li',
            '.a-unordered-list .a-list-item'
        ]
        
        for selector in detail_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                
                if any(keyword in text for keyword in ['weight', 'gram', 'kg', 'lb', 'oz']):
                    patterns = [
                        r'(\d+(?:\.\d+)?)\s*g\b(?!\s*protein)',
                        r'(\d+(?:\.\d+)?)\s*kg\b',
                        r'(\d+(?:\.\d+)?)\s*lb[s]?\b',
                        r'(\d+(?:\.\d+)?)\s*oz\b',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            try:
                                weight_val = float(match)
                                
                                if 'g\\b' in pattern and 'kg' not in pattern:
                                    weight_kg = weight_val / 1000
                                elif 'kg' in pattern:
                                    weight_kg = weight_val
                                elif 'lb' in pattern:
                                    weight_kg = weight_val * 0.453592
                                elif 'oz' in pattern:
                                    weight_kg = weight_val * 0.0283495
                                else:
                                    continue
                                    
                                if 0.01 <= weight_kg <= 100:
                                    return weight_kg
                                    
                            except (ValueError, IndexError):
                                continue
                                
        return 0
        
    def extract_weight_from_title(self, soup: BeautifulSoup) -> float:
        """Extract weight from title, avoiding nutritional content"""
        title_element = soup.select_one('#productTitle')
        if not title_element:
            return 0
            
        title = title_element.get_text().lower()
        
        # Remove nutritional content
        nutritional_exclusions = [
            r'\d+\s*g\s*protein\b',
            r'\d+\s*g\s*carbs?\b',
            r'\d+\s*g\s*fat\b',
            r'\d+\s*mg\s*(?:sodium|caffeine)\b',
        ]
        
        cleaned_title = title
        for exclusion in nutritional_exclusions:
            cleaned_title = re.sub(exclusion, '', cleaned_title)
            
        # Look for container weight
        patterns = [
            (r'(\d+(?:\.\d+)?)\s*kg\b', 1.0),
            (r'(\d+(?:\.\d+)?)\s*lb[s]?\b', 0.453592),
            (r'(\d+(?:\.\d+)?)\s*g\b(?!\s*protein)', 0.001),
            (r'(\d+(?:\.\d+)?)\s*oz\b', 0.0283495),
        ]
        
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, cleaned_title)
            if matches:
                try:
                    weight = float(matches[0]) * multiplier
                    if 0.01 <= weight <= 100:
                        return weight
                except ValueError:
                    continue
                    
        return 0
        
    def extract_origin_with_source(self, soup: BeautifulSoup, title: str, brand_hint: str = ""):
        """Return origin and source to support source-aware arbitration upstream."""
        print("🌍 Starting comprehensive origin extraction...")

        origin = self.extract_origin_from_product_details(soup)
        if origin != "Unknown":
            print(f"✅ Found origin in product details: {origin}")
            return origin, "product_details"

        origin = self.extract_origin_from_manufacturer_contact(soup)
        if origin != "Unknown":
            print(f"✅ Found origin in manufacturer contact: {origin}")
            return origin, "manufacturer_contact"

        origin = self.extract_origin_from_specifications(soup)
        if origin != "Unknown":
            print(f"✅ Found origin in specifications: {origin}")
            return origin, "specifications"

        origin = self.extract_origin_from_raw_text(soup)
        if origin != "Unknown":
            print(f"✅ Found origin in normalized raw text: {origin}")
            return origin, "raw_text"

        brand = brand_hint
        if not brand or str(brand).strip().lower() == "unknown":
            brand = self.extract_brand(soup)
        origin = self.extract_origin_from_brand_mapping(title, brand)
        if origin != "Unknown":
            print(f"✅ Found origin from brand mapping: {origin}")
            return origin, "brand_mapping"

        origin = self.extract_origin_from_title(title, soup)
        if origin != "Unknown":
            print(f"✅ Found origin in title/description: {origin}")
            return origin, "title_description"

        print("⚠️ No origin found, using default 'Unknown'")
        return "Unknown", "unknown"

    def _normalize_extraction_text(self, text: str) -> str:
        """Normalize hidden unicode separators so origin regex can match reliably."""
        if not text:
            return ""
        normalized = unicodedata.normalize('NFKD', text)
        normalized = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Cf')
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    def extract_origin_from_raw_text(self, soup: BeautifulSoup) -> str:
        """Fallback extraction from full page text for layouts that hide product-detail keys."""
        text = self._normalize_extraction_text(soup.get_text(' ', strip=True)).lower()
        if not text:
            return "Unknown"

        patterns = [
            r'country[^a-z0-9]{0,12}of[^a-z0-9]{0,12}origin[^a-z0-9]{0,12}([a-z][a-z\s\-]{2,30})',
            r'made[^a-z0-9]{0,8}in[^a-z0-9]{0,8}([a-z][a-z\s\-]{2,30})',
            r'product[^a-z0-9]{0,8}of[^a-z0-9]{0,8}([a-z][a-z\s\-]{2,30})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                candidate = re.sub(r'\s+(brand|format|age|additional|manufacturer|item|model|dimensions?).*$', '', match).strip()
                country = self.normalize_country_name(candidate)
                if country != "Unknown":
                    return country

        return "Unknown"

    def extract_origin(self, soup: BeautifulSoup, title: str) -> str:
        """
        Comprehensive origin extraction from all Amazon sources
        Priority: Product Details → Manufacturer Contact → Specifications → Brand Mapping → Title
        """
        origin, _ = self.extract_origin_with_source(soup, title)
        return origin
        
    def extract_origin_from_product_details(self, soup: BeautifulSoup) -> str:
        """Extract origin from Amazon product details tables - UNIVERSAL for all products"""
        # Pass 0: Prefer explicit key-value rows like "Country of Origin | China"
        try:
            for row in soup.select('tr'):
                cells = row.find_all(['th', 'td'])
                if len(cells) < 2:
                    continue

                key_text = self._normalize_extraction_text(cells[0].get_text(' ', strip=True)).lower()
                value_text = self._normalize_extraction_text(cells[1].get_text(' ', strip=True))

                if 'country of origin' in key_text or key_text == 'origin':
                    country = self.normalize_country_name(value_text)
                    if country != "Unknown":
                        print(f"🎯 Found origin in key-value row: '{value_text}' → '{country}'")
                        return country
        except Exception:
            pass

        # Comprehensive selectors for ALL Amazon layouts (current and future)
        detail_selectors = [
            # Current Amazon selectors
            'table#productDetails_techSpec_section_1',
            'table#productDetails_detailBullets_sections1', 
            'div#productDetails_db_sections',
            'div#detailBullets_feature_div',
            'div.pdTab',
            '#feature-bullets',
            
            # Future-proof selectors (generic patterns)
            '[id*="productDetails"]',
            '[id*="techSpec"]',
            '[id*="detailBullets"]',
            '[class*="product-details"]',
            '[class*="tech-spec"]',
            '[class*="detail-bullets"]',
            'table[id*="product"]',
            'div[id*="product"]',
            
            # Backup generic selectors
            '.a-expander-content table',
            '.a-section table',
            '.a-unordered-list',
            '.po-attribute-list'
        ]
        
        # Enhanced origin patterns - covers all possible variations
        origin_patterns = [
            # Direct origin fields
            r'country\s*of\s*origin[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'country\s*origin[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'origin\s*country[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'origin[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Manufacturing location
            r'made\s*in[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'manufactured\s*in[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'produced\s*in[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'crafted\s*in[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Product source
            r'product\s*of[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'imported\s*from[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'sourced\s*from[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Location indicators
            r'location[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'place\s*of\s*manufacture[:\s]*([a-z\s,\-\.]+?)(?:\n|Brand|Format|Age|ASIN|$)',
        ]
        
        for selector in detail_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text()
                    text_lower = text.lower()
                    
                    # Skip irrelevant sections
                    if any(skip in text_lower for skip in ['customer reviews', 'related products', 'sponsored', 'advertisement']):
                        continue
                    
                    for pattern in origin_patterns:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            country = self.normalize_country_name(match.strip())
                            if country != "Unknown":
                                print(f"🎯 Found origin in product details: '{match.strip()}' → '{country}'")
                                return country
            except Exception as e:
                # Silently continue if selector fails
                continue
                            
        return "Unknown"
        
    def extract_origin_from_manufacturer_contact(self, soup: BeautifulSoup) -> str:
        """Extract origin from manufacturer contact information - UNIVERSAL system"""
        # Comprehensive selectors for manufacturer/contact information
        detail_selectors = [
            # Current Amazon selectors
            'table#productDetails_techSpec_section_1',
            'table#productDetails_detailBullets_sections1',
            'div#productDetails_db_sections', 
            'div#detailBullets_feature_div',
            
            # Future-proof selectors
            '[id*="productDetails"]',
            '[id*="techSpec"]',
            '[class*="product-details"]',
            '.a-expander-content',
            '.po-attribute-list',
            
            # Generic fallbacks
            'table',
            '.a-section'
        ]
        
        # Enhanced contact patterns - covers ALL possible variations
        contact_patterns = [
            # Manufacturer information
            r'manufacturer[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'manufacturer.*contact[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'manufacturer.*information[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'manufacturing.*company[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'made.*by[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Distribution information
            r'distributed.*by[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'distributor[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'distribution[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Import/Export information
            r'imported.*by[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'importer[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'exported.*by[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Supplier information
            r'supplied.*by[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'supplier[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'vendor[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Company/Business information
            r'company[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'business.*address[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'corporate.*address[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'head.*office[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'headquarters[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Contact details
            r'contact.*details[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'contact.*information[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'contact.*address[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            
            # Responsible party (regulatory)
            r'responsible.*party[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'responsible.*entity[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
            r'authorized.*representative[:\s]*(.+?)(?:\n|Brand|Format|Age|ASIN|$)',
        ]
        
        for selector in detail_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text()
                    
                    # Skip irrelevant sections
                    text_lower = text.lower()
                    if any(skip in text_lower for skip in ['customer reviews', 'related products', 'sponsored']):
                        continue
                    
                    for pattern in contact_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        for match in matches:
                            # Clean up the match
                            contact_info = match.strip()
                            
                            # Skip if match is too short or just punctuation
                            if len(contact_info) < 5 or contact_info.isspace():
                                continue
                            
                            # Extract country from contact information
                            country = self.extract_country_from_address(contact_info)
                            if country != "Unknown":
                                print(f"🎯 Found origin in manufacturer contact: '{contact_info[:50]}...' → '{country}'")
                                return country
            except Exception as e:
                # Silently continue if selector fails
                continue
                            
        return "Unknown"
        
    def extract_origin_from_specifications(self, soup: BeautifulSoup) -> str:
        """Extract origin from technical specifications"""
        spec_selectors = [
            '.a-unordered-list .a-list-item',
            '#feature-bullets li',
            '.a-spacing-mini .a-list-item'
        ]
        
        for selector in spec_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                
                if any(keyword in text for keyword in ['origin', 'made', 'manufactured', 'country']):
                    # Extract country information
                    origin_patterns = [
                        r'(?:made|manufactured|origin|country).*?(?:in|of)[:\s]*([a-z\s,]+)',
                        r'([a-z\s]+)(?:\s+made|\s+origin)',
                    ]
                    
                    for pattern in origin_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            country = self.normalize_country_name(match.strip())
                            if country != "Unknown":
                                return country
                                
        return "Unknown"
        
    def extract_origin_from_brand_mapping(self, title: str, brand: str = "") -> str:
        """Extract origin using enhanced brand mapping"""
        if brand:
            db_origin = self.lookup_brand_origin(brand)
            db_origin = self.normalize_country_name(db_origin)
            if db_origin != "Unknown":
                return db_origin

        brand_origins = {
            # Protein/Supplement brands
            'mutant': 'Canada',
            'optimum nutrition': 'USA',
            'myprotein': 'UK',
            'usn': 'South Africa',
            'dymatize': 'USA',
            'bsn': 'USA',
            'warrior': 'UK',  # Added Warrior as UK brand
            'phd': 'UK',
            'grenade': 'UK',
            'applied nutrition': 'UK',
            'reflex nutrition': 'UK',
            
            # General brands
            'amazon basics': 'China',
            'kindle': 'USA',
            'echo': 'USA',
            'fire tv': 'USA',
            # Household/common marketplace brands
            'avlash': 'China',
        }
        
        if not title and not brand:
            return "Unknown"
            
        title_lower = (title or "").lower()
        brand_lower = (brand or "").lower().replace('brand:', '').strip()
        for brand, country in brand_origins.items():
            if brand in title_lower or brand in brand_lower:
                return country
                
        return "Unknown"
        
    def extract_origin_from_title(self, title: str, soup: BeautifulSoup) -> str:
        """Extract origin from product title and description"""
        if not title:
            return "Unknown"
            
        # Check title for origin indicators
        title_text = title.lower()
        
        # Look for "UK Made", "Made in USA", etc.
        title_patterns = [
            r'(?:uk|british|england|scotland|wales)\s*made',
            r'made\s*in\s*(?:uk|usa|china|germany|france|italy|spain|canada)',
            r'(?:american|german|french|italian|canadian)\s*made',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, title_text)
            if match:
                country = self.normalize_country_name(match.group())
                if country != "Unknown":
                    return country
                    
        # Check product description
        desc_selectors = ['#feature-bullets', '#productDescription', '.a-unordered-list']
        for selector in desc_selectors:
            elements = soup.select(selector)
            for element in elements:
                desc_text = element.get_text().lower()
                
                for pattern in title_patterns:
                    match = re.search(pattern, desc_text)
                    if match:
                        country = self.normalize_country_name(match.group())
                        if country != "Unknown":
                            return country
                            
        return "Unknown"
        
    def extract_country_from_address(self, address_text: str) -> str:
        """Extract country from address/contact information - UNIVERSAL system"""
        if not address_text:
            return "Unknown"
            
        address_lower = address_text.lower()
        
        # Comprehensive country patterns for ALL major countries and regions
        country_patterns = {
            # English-speaking countries
            'UK': ['uk', 'united kingdom', 'england', 'scotland', 'wales', 'northern ireland', 'britain', 'great britain', 'british',
                   # Major UK cities
                   'london', 'manchester', 'birmingham', 'glasgow', 'edinburgh', 'liverpool', 'bristol', 'leeds', 'sheffield', 'cardiff',
                   # UK postcodes patterns
                   'sw1', 'nw1', 'se1', 'w1', 'ec1', 'm1', 'm17', 'b1', 'l1', 'ls1', 'ng1', 'ox1', 'cv1', 'cb1'],
                   
            'USA': ['usa', 'united states', 'america', 'us', 'american',
                    # Major US states
                    'california', 'texas', 'florida', 'new york', 'pennsylvania', 'illinois', 'ohio', 'georgia', 'michigan', 'washington',
                    # Major US cities  
                    'new york city', 'los angeles', 'chicago', 'houston', 'phoenix', 'philadelphia', 'san antonio', 'san diego', 'dallas', 'san jose',
                    # US zip code patterns
                    '90210', '10001', '60601', '77001', '85001'],
                    
            'Canada': ['canada', 'canadian',
                       # Canadian provinces
                       'ontario', 'quebec', 'british columbia', 'alberta', 'manitoba', 'saskatchewan', 'nova scotia', 'new brunswick',
                       # Major Canadian cities
                       'toronto', 'montreal', 'vancouver', 'calgary', 'ottawa', 'edmonton', 'winnipeg', 'quebec city'],
                       
            'Australia': ['australia', 'australian',
                          # Australian states
                          'new south wales', 'victoria', 'queensland', 'western australia', 'south australia', 'tasmania',
                          # Major Australian cities
                          'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra', 'darwin', 'hobart'],
            
            # European countries
            'Germany': ['germany', 'deutschland', 'german', 'deutsche',
                        'berlin', 'munich', 'hamburg', 'cologne', 'frankfurt', 'stuttgart', 'düsseldorf', 'dortmund', 'essen', 'leipzig'],
                        
            'France': ['france', 'french', 'français', 'française',
                       'paris', 'marseille', 'lyon', 'toulouse', 'nice', 'nantes', 'strasbourg', 'montpellier', 'bordeaux', 'lille'],
                       
            'Italy': ['italy', 'italia', 'italian', 'italiano',
                      'rome', 'milan', 'naples', 'turin', 'palermo', 'genoa', 'bologna', 'florence', 'bari', 'catania'],
                      
            'Spain': ['spain', 'españa', 'spanish', 'español',
                      'madrid', 'barcelona', 'valencia', 'seville', 'saragossa', 'málaga', 'murcia', 'palma', 'las palmas', 'bilbao'],
                      
            'Netherlands': ['netherlands', 'holland', 'dutch', 'nederland',
                            'amsterdam', 'rotterdam', 'the hague', 'utrecht', 'eindhoven', 'tilburg', 'groningen', 'almere'],
                            
            'Belgium': ['belgium', 'belgian', 'belgique', 'belgië',
                        'brussels', 'antwerp', 'ghent', 'charleroi', 'liège', 'bruges', 'namur', 'leuven'],
                        
            'Switzerland': ['switzerland', 'swiss', 'schweiz', 'suisse',
                            'zurich', 'geneva', 'basel', 'bern', 'lausanne', 'winterthur', 'lucerne', 'st. gallen'],
            
            # Asian countries
            'China': ['china', 'chinese', 'prc', '中国',
                      'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'chengdu', 'hangzhou', 'wuhan', 'xi\'an', 'nanjing', 'tianjin'],
                      
            'Japan': ['japan', 'japanese', 'nippon', 'nihon',
                      'tokyo', 'osaka', 'kyoto', 'nagoya', 'sapporo', 'fukuoka', 'kobe', 'kawasaki', 'saitama', 'hiroshima'],
                      
            'South Korea': ['south korea', 'korea', 'korean', 'republic of korea',
                            'seoul', 'busan', 'incheon', 'daegu', 'daejeon', 'gwangju', 'suwon', 'ulsan'],
                            
            'India': ['india', 'indian', 'bharat',
                      'mumbai', 'delhi', 'bangalore', 'hyderabad', 'ahmedabad', 'chennai', 'kolkata', 'pune', 'jaipur', 'lucknow'],
                      
            'Singapore': ['singapore', 'singaporean'],
            'Hong Kong': ['hong kong', 'hk'],
            'Taiwan': ['taiwan', 'taiwanese', 'republic of china'],
            
            # Other major countries
            'Brazil': ['brazil', 'brazilian', 'brasil',
                       'são paulo', 'rio de janeiro', 'brasilia', 'salvador', 'fortaleza', 'belo horizonte', 'manaus', 'curitiba'],
                       
            'Mexico': ['mexico', 'mexican', 'méxico',
                       'mexico city', 'guadalajara', 'monterrey', 'puebla', 'tijuana', 'león', 'juárez', 'torreón'],
                       
            'Russia': ['russia', 'russian', 'россия',
                       'moscow', 'saint petersburg', 'novosibirsk', 'yekaterinburg', 'nizhny novgorod', 'kazan', 'chelyabinsk', 'omsk'],
                       
            'South Africa': ['south africa', 'south african',
                             'johannesburg', 'cape town', 'durban', 'pretoria', 'port elizabeth', 'bloemfontein'],
        }
        
        # First pass: exact country name matching
        for country, indicators in country_patterns.items():
            for indicator in indicators:
                if indicator in address_lower:
                    # Additional validation to avoid false positives
                    if len(indicator) >= 3:  # Avoid matching very short patterns
                        return country
                
        # Second pass: regex patterns for postal codes and country codes
        postal_code_patterns = {
            'UK': [r'\b[a-z]{1,2}\d{1,2}[a-z]?\s*\d[a-z]{2}\b', r'\bmancheste?r\b', r'\blondon\b'],
            'USA': [r'\b\d{5}(-\d{4})?\b', r'\b[a-z]{2}\s+\d{5}\b'],
            'Canada': [r'\b[a-z]\d[a-z]\s*\d[a-z]\d\b'],
            'Germany': [r'\b\d{5}\b.*germany', r'\bde-\d{5}\b'],
            'France': [r'\b\d{5}\b.*france', r'\bfr-\d{5}\b'],
        }
        
        for country, patterns in postal_code_patterns.items():
            for pattern in patterns:
                if re.search(pattern, address_lower):
                    return country
                
        return "Unknown"
        
    def normalize_country_name(self, raw_country: str) -> str:
        """Normalize country names via shared ISO-backed normalizer."""
        return normalize_country_name_shared(raw_country)
        
    def guess_material_from_title(self, title: str) -> str:
        """Guess material type from product title"""
        if not title:
            return "Unknown"
            
        title_lower = title.lower()
        
        material_keywords = {
            'plastic': ['plastic', 'polymer', 'acrylic'],
            'metal': ['metal', 'steel', 'aluminum', 'iron'],
            'paper': ['paper', 'cardboard', 'book'],
            'fabric': ['fabric', 'cotton', 'cloth'],
            'glass': ['glass', 'crystal'],
            'mixed': ['supplement', 'protein', 'vitamin']
        }
        
        for material, keywords in material_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return material.title()
                
        return "Mixed"
        
    def guess_material_from_title_category_aware(self, title: str, category: str) -> str:
        """Guess material type with category-specific intelligence"""
        if not title:
            return self.category_detector.get_default_material(category)
            
        # Use standard material detection first
        material = self.guess_material_from_title(title)
        
        # If no specific material detected, use category default
        if material == "Mixed" or material == "Unknown":
            return self.category_detector.get_default_material(category)
            
        return material
        
    def calculate_confidence_score(self, data: Dict[str, Any], category_info: Dict[str, Any] = None) -> float:
        """Calculate confidence score for extracted data with category awareness"""
        score = 0.0
        max_score = 6.0  # Increased to include category confidence
        
        # Title confidence
        if data.get('title') and data['title'] != "Unknown Product":
            score += 1.0
            
        # Weight confidence (enhanced with category validation)
        weight = data.get('weight_kg', 0)
        if weight > 0 and weight != 1.0:  # Not default
            category = data.get('category', 'general')
            validation = self.category_detector.validate_weight_for_category(weight, category)
            if validation['is_valid']:
                score += 1.5  # Higher score for category-validated weight
            else:
                score += 1.0  # Lower score for invalid weight
        elif weight == 1.0:
            score += 0.5
            
        # Brand confidence (category-aware)
        if data.get('brand') and data['brand'] != "Unknown":
            score += 1.0
            
        # Origin confidence
        if data.get('origin') and data['origin'] != "Unknown":
            score += 1.0
            
        # Material confidence
        if data.get('material_type') and data['material_type'] != "Unknown":
            score += 0.5
            
        # Category detection confidence
        if category_info:
            category_confidence = category_info.get('confidence', 0)
            score += category_confidence * 1.0  # Up to 1.0 points for category
            
        return min(score / max_score, 1.0)
        
    def get_success_rate(self) -> str:
        """Get current success rate"""
        if self.request_count == 0:
            return "0/0 (0%)"
        rate = (self.success_count / self.request_count) * 100
        return f"{self.success_count}/{self.request_count} ({rate:.1f}%)"


def test_production_scraper():
    """Test the production scraper with known URLs"""
    scraper = ProductionAmazonScraper()
    
    test_urls = [
        # Known working protein powder
        "https://www.amazon.co.uk/Isolate-Protein-Fast-digesting-hydrolysate-Gourmet/dp/B01H3O2AMG/ref=sr_1_172?crid=3S6H6H4OUAWJY",
        
        # Simple format
        "https://amazon.co.uk/dp/B01H3O2AMG",
    ]
    
    print("🧪 Testing Production Amazon Scraper")
    print("=" * 70)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📦 TEST {i}/{len(test_urls)}")
        result = scraper.scrape_with_full_url(url)
        
        if result:
            print(f"\n🎉 SUCCESS! Confidence: {result['confidence_score']:.1%}")
            print(f"   Strategy: {result['scraping_metadata']['successful_strategy']}")
            print(f"   Category: {result.get('category', 'Unknown')} ({result.get('category_confidence', 0):.1%})")
            print(f"   Title: {result['title']}")
            print(f"   Weight: {result['weight_kg']}kg")
            print(f"   Brand: {result['brand']}")
            print(f"   Origin: {result['origin']}")
            print(f"   Material: {result['material_type']}")
        else:
            print(f"\n❌ FAILED")
            
        print(f"\n📈 Overall Success Rate: {scraper.get_success_rate()}")


if __name__ == "__main__":
    test_production_scraper()