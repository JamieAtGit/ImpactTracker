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
                    print("🚫 Bot detection — Amazon is blocking this IP. Set SCRAPERAPI_KEY env var to fix.")
                    return {"title": "blocked", "origin": "Unknown", "weight_kg": 1.0,
                            "material_type": "Unknown", "recyclability": "Medium",
                            "eco_score_ml": "C", "brand": "Unknown", "asin": asin}
                
                # Extract data
                return self.extract_from_soup(soup, asin, clean_url)
            
            else:
                print(f"⚠️ HTTP {response.status_code}")
                return self.create_intelligent_fallback(url, asin)
                
        except Exception as e:
            print(f"📡 Requests error: {e}")
            return self.create_intelligent_fallback(url, asin)
    
    def is_blocked(self, soup) -> bool:
        """Check if Amazon returned a CAPTCHA / bot-detection page.

        Only inspect the <title> tag and short-page heuristics — NOT the full
        body text, which legitimately contains words like 'robot', 'blocked',
        'automated' in product descriptions and reviews.
        """
        # Amazon CAPTCHA page title is literally "Robot Check"
        title_tag = soup.find('title')
        page_title = title_tag.get_text().strip().lower() if title_tag else ''
        captcha_titles = {'robot check', 'sorry!', 'service unavailable', ''}
        if page_title in captcha_titles and not soup.find(id='productTitle'):
            return True

        # CAPTCHA pages are very short — real product pages are >5 KB
        if len(soup.get_text()) < 1500 and not soup.find(id='productTitle'):
            return True

        # Explicit CAPTCHA form element present
        if soup.find('form', {'action': '/errors/validateCaptcha'}):
            return True

        return False
    
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

        # 0) Structured spec table extraction — th/td key-value rows (most accurate)
        origin_from_spec = self.extract_origin_from_spec_table(soup)
        # 1) Full-text tech details scan (handles \u200e-separated Amazon tables)
        origin_from_tech = self.extract_origin_from_tech_details(all_text)
        print(f"🔍 Spec table origin: '{origin_from_spec}', tech text origin: '{origin_from_tech}'")

        if origin_from_spec != "Unknown":
            origin = origin_from_spec
            origin_source = "technical_details"
            origin_confidence = "high"
            print(f"📍 ✅ Using structured spec table origin: {origin}")
        elif origin_from_tech != "Unknown":
            origin = origin_from_tech
            origin_source = "technical_details"
            origin_confidence = "high"
            print(f"📍 ✅ Using tech details origin: {origin}")
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
                        # 4.5) Title-based "Made in X" / "X Made" — e.g. "UK Made", "Made in UK"
                        _title_origin = self._extract_origin_from_title(title)
                        if _title_origin != "Unknown":
                            origin = _title_origin
                            origin_source = "title_keywords"
                            origin_confidence = "medium"
                            print(f"📍 ✅ Using title-based origin: {origin}")
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

                # Re-run extract_weight on just the title for better precision
                title_weight = self.extract_weight(title)
                if title_weight != 1.0 and 0.5 <= title_weight <= 10:
                    weight = title_weight
                    print(f"⚖️ Found better protein weight in title: {weight}kg")
        else:
            # First try spec table — explicit "Material: X" row is the most reliable source
            spec_material = self.extract_material_from_spec_table(soup)
            if spec_material:
                material = spec_material
                print(f"🧵 Using spec table material: {material}")
            else:
                material = self.detect_material(title, all_text)

        # Extract ALL material fields for multi-material pipeline
        amazon_materials_extracted = self.extract_all_materials_from_spec_table(soup)

        # Supplement with title-based multi-material detection to fill secondary/tertiary gaps
        title_materials = self._detect_all_materials_from_title(title)
        if title_materials:
            if amazon_materials_extracted is None:
                amazon_materials_extracted = title_materials
            else:
                existing_names = {m['name'].lower() for m in amazon_materials_extracted['materials']}
                for m in title_materials['materials']:
                    if m['name'].lower() not in existing_names:
                        amazon_materials_extracted['materials'].append(
                            {'name': m['name'], 'confidence_score': 0.65}
                        )
                        existing_names.add(m['name'].lower())

        # === Price extraction ===
        price = None
        price_selectors = [
            '.apexPriceToPay .a-offscreen',
            '#apex_offerDisplay_desktop .a-price .a-offscreen',
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#corePriceDisplay_desktop_feature_div .a-offscreen',
        ]
        # Price selectors are tried in priority order; the first value in a
        # realistic range wins.  The regex `[\d]+\.?\d*` is intentionally
        # broad, so we guard against false positives (star ratings, % values,
        # etc.) by requiring the extracted figure to sit within a plausible
        # retail price band.
        _PRICE_MIN = 0.50    # below this is almost certainly noise
        _PRICE_MAX = 10_000  # above this is almost certainly not a product price
        for _sel in price_selectors:
            _el = soup.select_one(_sel)
            if _el:
                _raw = _el.get_text().strip().replace(',', '')
                # Match the *first* decimal number that looks like a price
                _m = re.search(r'\d+(?:\.\d{1,2})?', _raw)
                if _m:
                    try:
                        _candidate = float(_m.group())
                        if _PRICE_MIN <= _candidate <= _PRICE_MAX:
                            price = _candidate
                            break
                    except Exception:
                        pass

        # === Amazon Climate Pledge Friendly ===
        climate_pledge_friendly = False
        _full_text = soup.get_text().lower()
        if 'climate pledge friendly' in _full_text:
            climate_pledge_friendly = True
        _cpf_el = soup.select_one(
            '#climatePledgeFriendlyBadge, '
            '[id*="climatePledge"], '
            '[data-feature-name="climatePledgeFriendlyBadge"], '
            '.a-section.certifications-label-container'
        )
        if _cpf_el:
            climate_pledge_friendly = True

        # === Eco Certifications ===
        # Use compound phrases to avoid false positives (e.g. 'organic chemistry')
        _CERT_PATTERNS = [
            (r'\bfsc[- ]certified\b|\bfsc[- ](?:wood|paper|label|timber)\b|\bcertified fsc\b', 'FSC Certified'),
            (r'\bfair ?trade[- ]certified\b|\bcertified fair ?trade\b|\bfairtrade\b', 'Fair Trade'),
            (r'\beu ecolabel\b|\beuropean ecolabel\b', 'EU Ecolabel'),
            (r'\bb[\s-]?corp\b|\bb corporation certified\b', 'B Corp'),
            (r'\brainforest alliance[- ]certified\b|\brainforest alliance\b', 'Rainforest Alliance'),
            (r'\boeko[- ]?tex\b', 'OEKO-TEX'),
            (r'\benergy[\s-]?star\b', 'ENERGY STAR'),
            (r'\bgots[- ]certified\b|\bglobal organic textile standard\b', 'GOTS'),
            (r'\bbluesign[- ]approved\b|\bbluesign\b', 'bluesign'),
            (r'\borganic cotton\b|\busda organic\b|\bcertified organic\b|\beu organic\b|\bsol organic\b', 'Organic'),
            (r'\bresponsible wool standard\b|\brws[- ]certified\b', 'Responsible Wool'),
            (r'\bcarbon neutral[- ]certified\b|\bnet[\s-]?zero certified\b|\bcarbon zero\b', 'Carbon Neutral'),
            (r'\bpost[\s-]?consumer recycled\b|\bpcr[\s-]content\b|\brecycled content certified\b', 'Recycled Content'),
            (r'\bcruelty[\s-]?free\b', 'Cruelty Free'),
        ]
        certifications = []
        # Priority: check the certifications container text first
        _cert_container = soup.select_one(
            '.a-section.certifications-label-container, #certifications-label-container, '
            '[data-feature-name="certifications"], #sustainability-label-container'
        )
        _cert_scan_text = (
            (_cert_container.get_text().lower() if _cert_container else '') + ' ' + _full_text
        )
        for _pattern, _label in _CERT_PATTERNS:
            if _label not in certifications and re.search(_pattern, _cert_scan_text):
                certifications.append(_label)

        # === Product image URL ===
        # Strategy 1: #landingImage is Amazon's dedicated main product image element
        image_url = None
        _landing = soup.select_one('#landingImage')
        if _landing:
            # data-old-hires is the highest resolution available
            image_url = _landing.get('data-old-hires') or _landing.get('data-a-hires')
            # data-a-dynamic-image is a JSON dict {url: [width, height]} — pick largest
            if not image_url:
                _dyn_raw = _landing.get('data-a-dynamic-image', '')
                if _dyn_raw:
                    try:
                        import json as _json
                        _dyn_map = _json.loads(_dyn_raw)
                        if _dyn_map:
                            image_url = max(
                                _dyn_map.keys(),
                                key=lambda u: _dyn_map[u][0] * _dyn_map[u][1]
                            )
                    except Exception:
                        pass
            if not image_url:
                _src = _landing.get('src', '')
                if _src and _src.startswith('http') and 'media-amazon' in _src:
                    image_url = _src

        # Strategy 2: main image block container (never .a-dynamic-image globally — too broad)
        if not image_url:
            _wrap = soup.select_one('#imgTagWrapperId img, #imageBlock #main-image')
            if _wrap:
                image_url = (_wrap.get('data-old-hires') or
                             _wrap.get('data-a-hires') or
                             _wrap.get('src') or None)

        # Strategy 3: Amazon embeds full image data in a JS "colorImages" variable
        if not image_url:
            _hi = re.search(r'"hiRes"\s*:\s*"(https://[^"]+\.(?:jpg|jpeg|png|webp))"', str(soup))
            if _hi:
                image_url = _hi.group(1)

        # Strategy 4: Regex — only match large product images (SL≥500 size code)
        # This deliberately skips small icons, Prime logos, and badges
        if not image_url:
            _large = re.search(
                r'https://m\.media-amazon\.com/images/I/[A-Za-z0-9+\-]+\.'
                r'_[A-Z_0-9,]*SL(?:500|750|1000|1200|1500|2000)[A-Z_0-9,]*_\.\w+',
                str(soup)
            )
            if _large:
                image_url = _large.group(0)

        # Strip Amazon's size-suffix codes (._AC_SL1500_.) to get the base high-res URL
        if image_url and '._' in image_url:
            _clean = re.sub(r'\._[A-Z0-9_,]+_\.', '.', image_url)
            if _clean.startswith('http'):
                image_url = _clean

        # === Gallery images (all product angles) ===
        # Amazon embeds all gallery image URLs inside a JS colorImages variable.
        # The "hiRes" key per entry is the full-resolution version.
        gallery_images = []
        _page_src = str(soup)
        for _m in re.finditer(
            r'"hiRes"\s*:\s*"(https://m\.media-amazon\.com/images/I/[^"]+)"',
            _page_src
        ):
            _gurl = _m.group(1)
            # Strip size suffix to get base URL, deduplicate, cap at 5
            if '._' in _gurl:
                _gurl = re.sub(r'\._[A-Z0-9_,]+_\.', '.', _gurl)
            if _gurl not in gallery_images and _gurl != image_url:
                gallery_images.append(_gurl)
            if len(gallery_images) >= 5:
                break

        # === Sold by / Dispatched from ===
        sold_by = None
        dispatched_from = None
        _buybox_el = soup.select_one('#tabular-buybox, #buybox, #desktop_buybox, #olpLinkWidget_feature_div')
        if _buybox_el:
            _bbox_text = _buybox_el.get_text()
            _sold_m = re.search(r'sold by[:\s]+([^\n\t]+)', _bbox_text, re.IGNORECASE)
            if _sold_m:
                sold_by = _sold_m.group(1).strip()[:100]
            _disp_m = re.search(r'dispatched from[:\s]+([^\n\t]+)', _bbox_text, re.IGNORECASE)
            if _disp_m:
                dispatched_from = _disp_m.group(1).strip()[:100]
        if not sold_by:
            _seller_el = soup.select_one('#sellerProfileTriggerId, #merchant-info')
            if _seller_el:
                sold_by = _seller_el.get_text().strip()[:100]

        result = {
            "title": title,
            "origin": origin,
            "country_of_origin": origin,
            "origin_source": origin_source,
            "origin_confidence": origin_confidence,
            "weight_kg": weight,
            "material_type": material,
            "amazon_materials_extracted": amazon_materials_extracted,
            "recyclability": "Medium",
            "eco_score_ml": "C",
            "transport_mode": "Ship",
            "carbon_kg": None,
            "brand": brand,
            "asin": asin,
            "data_quality_score": 85,
            "confidence": "High",
            "method": "Requests Scraping",
            "price": price,
            "climate_pledge_friendly": climate_pledge_friendly,
            "certifications": certifications,
            "sold_by": sold_by,
            "dispatched_from": dispatched_from,
            "image_url": image_url,
            "gallery_images": gallery_images,
            "category": self.detect_category_from_title(title),
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
        """Extract weight from text and convert to kg.

        Handles: kg, g, mg, lb/lbs/pounds, oz/ounces, stone/st,
        compound 'X lb Y oz', and Amazon's unicode-separated tech tables.
        """
        text_lower = text.lower()

        # ── Compound "X lb Y oz" (e.g. "1 lb 4 oz", "2 lbs 3 oz") ──────────
        compound = re.search(
            r'(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\s+(\d+(?:\.\d+)?)\s*(?:oz|ounces?)',
            text_lower
        )
        if compound:
            try:
                lbs = float(compound.group(1))
                oz  = float(compound.group(2))
                return round(lbs * 0.453592 + oz * 0.0283495, 4)
            except Exception:
                pass

        # ── Priority patterns (most specific first) ──────────────────────────
        # Amazon UK uses \u200e (left-to-right mark) as separators in tech tables,
        # e.g. "Item Weight \u200e : \u200e 5.94 kg"
        _W = r'(?:item|package|net|gross|product)?\s*weight[\s\u200e\u200f]*:[\s\u200e\u200f]*'
        priority_patterns = [
            # Amazon-style "Item Weight : X <unit>" with unicode separators
            (_W + r'(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)',          'kg'),
            (_W + r'(\d+(?:\.\d+)?)\s*(?:g|grams?)',               'g'),
            (_W + r'(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)',         'mg'),
            (_W + r'(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)',         'lb'),
            (_W + r'(\d+(?:\.\d+)?)\s*(?:oz|ounces?)',             'oz'),
            (_W + r'(\d+(?:\.\d+)?)\s*(?:stone|st)\b',            'st'),
            # Plain "weight: X <unit>"
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)',   'kg'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:g|grams?)',        'g'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:mg|milligrams?)',  'mg'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)',  'lb'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:oz|ounces?)',      'oz'),
            (r'weight[:\s]+(\d+(?:\.\d+)?)\s*(?:stone|st)\b',     'st'),
            # Dimensions trailing weight (e.g. "11 x 7 x 27 cm; 600 g")
            (r';\s*(\d+(?:\.\d+)?)\s*(?:kg)\b',                    'kg'),
            (r';\s*(\d+(?:\.\d+)?)\s*(?:g)\b',                     'g'),
            (r';\s*(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b',               'lb'),
            (r';\s*(\d+(?:\.\d+)?)\s*(?:oz)\b',                    'oz'),
            # Units field (e.g. "Units: 600.0 gram")
            (r'units[:\s]+(\d+(?:\.\d+)?)\s*(?:g|gram)',           'g'),
            # Standalone values in title (broad — lowest priority)
            (r'\b(\d+(?:\.\d+)?)\s*kg\b',                          'kg'),
            (r'\b(\d+(?:\.\d+)?)\s*g\b(?!ram)',                    'g'),   # avoid "program"
            (r'\b(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\b',         'lb'),
            (r'\b(\d+(?:\.\d+)?)\s*(?:oz|ounces?)\b',             'oz'),
        ]

        # Conversion factors → kg
        _TO_KG = {
            'kg': 1.0,
            'g':  1e-3,
            'mg': 1e-6,
            'lb': 0.453592,
            'oz': 0.0283495,
            'st': 6.35029,
        }
        # Minimum plausible value per unit (filters obvious noise)
        _MIN = {
            'kg': 0.01,
            'g':  10.0,
            'mg': 100.0,
            'lb': 0.05,
            'oz': 0.5,
            'st': 0.1,
        }
        # Maximum plausible product weight in kg (skip clear garbage)
        _MAX_KG = 500.0

        # ── Range "500g–600g" / "1.5–2 kg" / "1–2 lbs" → midpoint ────────
        # Must run after compound handler but before single-value scan.
        # Maps any unit string the regex can capture to a _TO_KG key.
        _UNIT_NORM = {
            'kg': 'kg', 'kilograms': 'kg', 'kilogram': 'kg',
            'g': 'g', 'grams': 'g', 'gram': 'g',
            'mg': 'mg', 'milligrams': 'mg', 'milligram': 'mg',
            'lb': 'lb', 'lbs': 'lb', 'pound': 'lb', 'pounds': 'lb',
            'oz': 'oz', 'ounces': 'oz', 'ounce': 'oz',
            'stone': 'st', 'st': 'st',
        }
        range_match = re.search(
            r'\b(\d+(?:\.\d+)?)\s*[-\u2013\u2014]\s*(\d+(?:\.\d+)?)\s*'
            r'(kg|kilograms?|g(?!ram)|grams?|mg|milligrams?|lb|lbs|pounds?|oz|ounces?|stone|st)\b',
            text_lower
        )
        if range_match:
            try:
                lo  = float(range_match.group(1))
                hi  = float(range_match.group(2))
                raw_unit = range_match.group(3).rstrip('s')  # 'gram' → 'gram' etc.
                unit_key = _UNIT_NORM.get(raw_unit, _UNIT_NORM.get(raw_unit.rstrip('s')))
                if unit_key and lo < hi:
                    mid = (lo + hi) / 2
                    if mid >= _MIN.get(unit_key, 0):
                        kg = mid * _TO_KG[unit_key]
                        if 0 < kg <= _MAX_KG:
                            return round(kg, 4)
            except Exception:
                pass

        for pattern, unit in priority_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    val = float(match[0] if isinstance(match, tuple) else match)
                    if val < _MIN.get(unit, 0):
                        continue
                    kg = val * _TO_KG[unit]
                    if kg > _MAX_KG:
                        continue
                    return round(kg, 4)
                except Exception:
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
                         'carbon steel', 'alloy', 'pewter', 'nickel',
                         'razor', 'razor blade', 'blade refill', 'shaving blade',
                         'knife', 'knives', 'scissors', 'cutlery', 'spanner', 'wrench'],
            'Paper':    ['paper', 'cardboard', 'book', 'journal',
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
            # Specific plastic sub-types checked BEFORE the generic 'Plastic' entry
            # so that the most precise match wins.  The CO₂ intensity dict in
            # app_production.py has individual entries for each of these.
            'Polypropylene': ['polypropylene', 'pp plastic', 'pp bottle', 'pp container'],
            'Polyethylene':  ['polyethylene', 'hdpe', 'ldpe', 'pe plastic', 'pe container'],
            'PVC':           ['pvc', 'polyvinyl chloride', 'vinyl chloride'],
            'Polycarbonate': ['polycarbonate', 'pc plastic', 'lexan'],
            'ABS Plastic':   ['abs plastic', 'acrylonitrile butadiene'],
            'Polystyrene':   ['polystyrene', 'styrofoam', 'eps foam', 'expanded polystyrene'],
            'Plastic':  ['plastic', 'polymer', 'bpa',
                         'acrylic', 'resin', 'hard shell',
                         'hardshell', 'thermoplastic', 'perspex'],
            'Mixed':    ['electronic', 'device', 'phone', 'laptop', 'tablet',
                         'headphone', 'speaker', 'keyboard', 'monitor', 'router',
                         'printer', 'camera', 'smartwatch', 'console', 'gaming',
                         'earphone', 'earbud', 'wearable', 'television', 'smart tv',
                         'qled', 'oled', 'smart home', 'smart plug', 'smart bulb',
                         # Home appliances — prevent "paper filter" etc. from
                         # winning in the text scan
                         'purifier', 'humidifier', 'dehumidifier',
                         'vacuum cleaner', 'air fryer', 'coffee maker',
                         'coffee machine', 'espresso', 'blender'],
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
        # For the full-page text scan, 'paper' alone is far too noisy:
        # air purifiers say "paper HEPA filter", vacuums say "paper bag",
        # coffee makers say "paper filter", printers are surrounded by the word.
        # Only match unambiguous compound phrases in the text scan.
        paper_text_keywords = [
            'kraft paper', 'wrapping paper', 'tissue paper', 'paper bag',
            'cardboard', 'paperback', 'hardback', 'kraft',
        ]

        # Paper is last — it's the most prone to false positives via page text.
        text_scan_order = [
            'Leather', 'Rubber', 'Wood', 'Ceramic',
            'Fabric', 'Plastic', 'Stone', 'Glass', 'Paper',
        ]
        text_lower = text.lower()
        for material in text_scan_order:
            kws = paper_text_keywords if material == 'Paper' else materials[material]
            if material in materials and any(kw in text_lower for kw in kws):
                return material
        if any(kw in text_lower for kw in text_metal_keywords):
            return 'Metal'

        return 'Unknown'
    
    def detect_category_from_title(self, title: str) -> str:
        """Map product title keywords to a broad product category.

        Used downstream to improve transport-mode defaults and origin estimates.
        Returns 'Other' when no keyword matches.
        """
        t = title.lower()
        _CATEGORIES = [
            ('Electronics',     ['phone', 'smartphone', 'laptop', 'tablet', 'headphone',
                                  'earphone', 'earbud', 'speaker', 'keyboard', 'mouse',
                                  'monitor', 'charger', 'cable', 'smartwatch', 'router',
                                  'printer', 'camera', 'television', ' tv ', 'smart tv',
                                  'gaming console', 'graphics card', 'ssd', 'hard drive']),
            ('Clothing',        ['t-shirt', 'shirt', 'hoodie', 'jacket', 'coat', 'dress',
                                  'jeans', 'trousers', 'socks', 'underwear', 'leggings',
                                  'shorts', 'boots', 'shoes', 'trainers', 'sneakers',
                                  'sandals', 'hat', 'baseball cap', 'scarf', 'gloves', 'swimwear',
                                  'pyjamas', 'lingerie', 'bra', 'sportswear']),
            ('Home & Kitchen',  ['mug', 'cup', 'plate', 'bowl', 'pan', 'pot', 'knife',
                                  'cutting board', 'kettle', 'toaster', 'blender', 'coffee maker',
                                  'pillow', 'cushion', 'duvet', 'bedsheet', 'towel', 'curtain',
                                  'rug', 'lamp', 'candle', 'vase', 'photo frame', 'mirror']),
            ('Sports & Fitness',['dumbbell', 'barbell', 'kettlebell', 'yoga mat', 'gym',
                                  'fitness', 'bicycle', 'treadmill', 'resistance band',
                                  'foam roller', 'running', 'cycling', 'swimming',
                                  'football', 'basketball', 'tennis', 'cricket', 'golf',
                                  'hiking', 'climbing', 'weightlifting']),
            ('Beauty & Health', ['shampoo', 'conditioner', 'moisturiser', 'moisturizer',
                                  'serum', 'sunscreen', 'toothbrush', 'toothpaste', 'razor',
                                  'perfume', 'lipstick', 'mascara', 'foundation',
                                  'vitamin', 'supplement', 'protein powder', 'whey']),
            ('Books & Media',   ['book', 'novel', 'textbook', 'dvd', 'blu-ray', 'vinyl', 'cd']),
            ('Toys & Games',    ['toy', 'lego', 'puzzle', 'board game', 'doll',
                                  'action figure', 'playset', 'remote control car']),
            ('Garden',          ['plant pot', 'garden', 'seed', 'fertiliser', 'fertilizer',
                                  'compost', 'lawn', 'garden hose', 'trowel', 'spade',
                                  'bbq', 'barbecue', 'patio', 'outdoor chair']),
            ('Baby & Kids',     ['baby', 'nappy', 'diaper', 'pram', 'stroller', 'cot',
                                  'crib', 'high chair', 'sippy cup', 'baby food']),
            ('Pet Supplies',    ['dog', 'cat', 'pet', 'cat food', 'dog food', 'pet bed',
                                  'collar', 'dog lead', 'cat litter', 'fish tank']),
            ('Food & Drink',    ['coffee beans', 'tea bags', 'chocolate', 'protein bar',
                                  'olive oil', 'pasta', 'cereal', 'biscuit', 'energy drink']),
        ]
        import re as _re
        for category, keywords in _CATEGORIES:
            if any(_re.search(r'\b' + _re.escape(kw), t) for kw in keywords):
                return category
        return 'Other'

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
        
        # Debug: Log country mentions only when surrounded by origin-indicating language
        # to avoid noise from navigation text, product descriptions, reviewer locations, etc.
        _ORIGIN_SIGNALS = {'origin', 'made in', 'manufactured in', 'country of', 'imported from', 'product of'}
        debug_countries = ['belgium', 'germany', 'england', 'uk', 'usa', 'china', 'pakistan', 'india', 'bangladesh', 'turkey', 'vietnam', 'indonesia']
        for country in debug_countries:
            if country in text_lower:
                country_pos = text_lower.find(country)
                context_start = max(0, country_pos - 80)
                context_end = min(len(text_lower), country_pos + 80)
                context = text_lower[context_start:context_end]
                if any(sig in context for sig in _ORIGIN_SIGNALS):
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

    def extract_material_from_spec_table(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract primary material from Amazon's structured product detail tables.

        Uses a two-pass strategy so the plain "Material" / "Material Type" field
        (whole-product) always wins over component-level fields like "Shade Material",
        "Frame Material", "Sole Material" etc., which describe only one part.
        """
        # Primary keys — these describe the whole product
        primary_exact = {'material', 'material type', 'material composition', 'fabric type'}
        # Secondary keys — subcomponent fields (used as fallback only)
        secondary_keys = {
            'outer material', 'inner material', 'lining material', 'shell material',
            'frame material', 'filling material', 'sole material', 'upper material',
            'shade material', 'body material', 'cover material', 'base material',
        }

        def _extract_rows(soup_obj):
            """Yield (key, raw_value) pairs from all known Amazon table formats."""
            # th/td product details tables
            for table in soup_obj.select(
                '#productDetails_techSpec_section_1, '
                '#productDetails_detailBullets_sections1, '
                '#productDetails_db_sections table, '
                'table'
            ):
                for row in table.select('tr'):
                    th = row.select_one('th')
                    td = row.select_one('td')
                    if th and td:
                        yield (
                            self._normalize_extraction_text(th.get_text(' ', strip=True)).lower(),
                            self._normalize_extraction_text(td.get_text(' ', strip=True)),
                        )
            # po-attribute-list (condensed attribute list)
            for row in soup_obj.select('.po-attribute-list tr, .po-attribute-list__item'):
                label_el = row.select_one('.po-attribute-list__label, .a-span3')
                value_el = row.select_one('.po-attribute-list__value, .a-span9')
                if label_el and value_el:
                    yield (
                        self._normalize_extraction_text(label_el.get_text(' ', strip=True)).lower(),
                        self._normalize_extraction_text(value_el.get_text(' ', strip=True)),
                    )

        primary_hit = None
        secondary_hit = None

        for key, value in _extract_rows(soup):
            if not value or not (2 < len(value) < 150):
                continue
            # Exact primary match (key IS one of the primary fields, no extra words)
            if key in primary_exact and primary_hit is None:
                primary_hit = value
                print(f"🧵 Spec table primary material field '{key}': '{value}'")
            # Substring secondary match (key CONTAINS a primary word but has a modifier)
            elif any(pk in key for pk in primary_exact) and secondary_hit is None:
                secondary_hit = value
                print(f"🧵 Spec table secondary material field '{key}': '{value}'")
            # Explicit subcomponent field
            elif any(sk in key for sk in secondary_keys) and secondary_hit is None:
                secondary_hit = value

        # Detail bullets — "Material ‎ : ‎ Velvet" format
        all_keys = primary_exact | secondary_keys
        for li in soup.select('#detailBullets_feature_div li, #detailBulletsWrapper_feature_div li'):
            text = self._normalize_extraction_text(li.get_text(' ', strip=True))
            text_lower = text.lower()
            for mk in sorted(primary_exact, key=len, reverse=True):  # longest first
                if mk in text_lower:
                    match = re.search(
                        r'(?:' + re.escape(mk) + r')[\s\u200e\u200f:‎]+([^:\n‎]{2,100})',
                        text, re.IGNORECASE
                    )
                    if match:
                        value = match.group(1).strip().strip('‎').strip()
                        if value and len(value) < 150 and primary_hit is None:
                            primary_hit = value
                            print(f"🧵 Detail bullets material '{mk}': '{value}'")

        result = primary_hit or secondary_hit
        return result

    def _detect_all_materials_from_title(self, title: str) -> Optional[Dict]:
        """Detect multiple materials from the product title using keyword matching.

        More specific compound terms (e.g. 'stainless steel') are checked before
        generic ones ('steel') so they take precedence. All matching materials are
        returned; duplicates are deduplicated. Returns None if nothing is found.
        """
        title_lower = title.lower()

        # Each entry: ([keywords], canonical_name, confidence)
        # Ordered so compound/specific terms appear before generic ones.
        material_patterns = [
            # Metals — compound first
            (['stainless steel', 'stainless-steel'],          'Stainless Steel',    0.90),
            (['cast iron'],                                    'Cast Iron',          0.90),
            (['carbon steel'],                                 'Carbon Steel',       0.88),
            (['galvanised steel', 'galvanized steel'],         'Galvanised Steel',   0.88),
            (['aluminium alloy', 'aluminum alloy'],            'Aluminium',          0.88),
            (['aluminium', 'aluminum'],                        'Aluminium',          0.82),
            (['titanium'],                                     'Titanium',           0.82),
            (['copper'],                                       'Copper',             0.78),
            (['brass'],                                        'Brass',              0.78),
            (['steel'],                                        'Steel',              0.75),
            (['iron'],                                         'Iron',               0.70),
            # Glass
            (['borosilicate glass', 'tempered glass'],         'Glass',              0.90),
            (['glass'],                                        'Glass',              0.80),
            # Plastics / composites — specific before generic
            (['polycarbonate', 'pc plastic'],                  'Polycarbonate',      0.85),
            (['polypropylene', 'pp plastic'],                  'Polypropylene',      0.85),
            (['polyethylene', 'hdpe', 'ldpe'],                 'Polyethylene',       0.85),
            (['abs plastic', 'abs shell'],                     'ABS Plastic',        0.85),
            (['polystyrene', 'eps foam'],                      'Polystyrene',        0.83),
            (['acrylic', 'perspex', 'plexiglass'],             'Acrylic',            0.82),
            (['silicone'],                                     'Silicone',           0.82),
            (['neoprene'],                                     'Neoprene',           0.80),
            (['plastic', 'pvc', 'polymer'],                    'Plastic',            0.70),
            # Wood / natural
            (['bamboo'],                                       'Bamboo',             0.85),
            (['solid wood', 'hardwood', 'mdf board', 'plywood'], 'Wood',            0.85),
            (['wood', 'wooden', 'timber', 'oak', 'pine', 'teak', 'walnut', 'birch'], 'Wood', 0.78),
            (['cork'],                                         'Cork',               0.82),
            (['rattan', 'wicker'],                             'Rattan',             0.82),
            (['marble'],                                       'Marble',             0.82),
            (['granite'],                                      'Granite',            0.82),
            # Fabric / textiles
            (['leather', 'genuine leather', 'full-grain'],     'Leather',            0.85),
            (['faux leather', 'pu leather', 'vegan leather'],  'Faux Leather',       0.85),
            (['cotton'],                                       'Cotton',             0.82),
            (['polyester'],                                    'Polyester',          0.80),
            (['nylon'],                                        'Nylon',              0.80),
            (['wool', 'woollen', 'cashmere'],                  'Wool',               0.80),
            (['canvas'],                                       'Canvas',             0.78),
            (['microfibre', 'microfiber'],                     'Microfibre',         0.78),
            # Other
            (['ceramic', 'porcelain'],                         'Ceramic',            0.82),
            (['rubber', 'latex'],                              'Rubber',             0.78),
            (['foam', 'memory foam', 'eva foam'],              'Foam',               0.72),
            (['paper', 'cardboard', 'kraft'],                  'Paper',              0.72),
        ]

        # Maps specific material → generic parents that become redundant
        _TITLE_PARENTS = {
            'polyethylene':      {'plastic'},
            'polypropylene':     {'plastic'},
            'polycarbonate':     {'plastic'},
            'abs plastic':       {'plastic'},
            'pvc':               {'plastic'},
            'polystyrene':       {'plastic'},
            'hdpe':              {'plastic'},
            'ldpe':              {'plastic'},
            'acrylic':           {'plastic'},
            'silicone':          {'rubber', 'plastic'},
            'neoprene':          {'rubber'},
            'stainless steel':   {'steel', 'metal', 'iron'},
            'cast iron':         {'iron', 'metal'},
            'carbon steel':      {'steel', 'metal'},
            'galvanised steel':  {'steel', 'metal'},
            'aluminium':         {'metal'},
            'copper':            {'metal'},
            'brass':             {'metal'},
            'titanium':          {'metal'},
            'solid wood':        {'wood', 'timber'},
            'bamboo':            {'wood'},
            'rattan':            {'wood'},
            'cork':              {'wood'},
            'cotton':            {'fabric'},
            'polyester':         {'fabric'},
            'nylon':             {'fabric'},
            'wool':              {'fabric'},
            'canvas':            {'fabric'},
            'microfibre':        {'fabric'},
            'leather':           {'fabric'},
            'faux leather':      {'leather', 'fabric'},
            'genuine leather':   {'leather', 'fabric'},
            'borosilicate glass':{'glass'},
            'tempered glass':    {'glass'},
            'memory foam':       {'foam'},
            'eva foam':          {'foam'},
        }

        import re as _re

        def _kw_match(kw: str, t: str) -> bool:
            """Whole-word match for single-word keywords; substring for multi-word."""
            if ' ' not in kw:
                return bool(_re.search(r'\b' + _re.escape(kw) + r'\b', t))
            return kw in t

        found = []
        seen: set = set()
        for keywords, material_name, confidence in material_patterns:
            if any(_kw_match(kw, title_lower) for kw in keywords):
                key = material_name.lower()
                if key not in seen:
                    seen.add(key)
                    found.append({'name': material_name, 'confidence_score': confidence})

        if not found:
            return None

        # Semantic dedup: drop generic parents when a specific subtype is present
        all_found_lower = {m['name'].lower() for m in found}
        suppress: set = set()
        for name_lower in all_found_lower:
            suppress |= _TITLE_PARENTS.get(name_lower, set())
        found = [m for m in found if m['name'].lower() not in suppress]

        if not found:
            return None
        print(f"🧵 Title-detected materials: {[m['name'] for m in found]}")
        return {'materials': found}

    def extract_all_materials_from_spec_table(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract ALL material fields from the spec table and return as structured data for multi-material detection."""
        # Exact primary keys (the whole product material) — highest confidence
        primary_exact = {'material', 'material type', 'material composition', 'fabric type'}
        # Subcomponent keys — lower confidence, treated as secondary
        subcomponent_keys = {
            'outer material', 'inner material', 'lining material', 'shell material',
            'frame material', 'filling material', 'sole material', 'upper material',
            'shade material', 'body material', 'cover material', 'base material',
        }
        # collected entries: (raw_value_string, is_primary_key)
        collected = []

        for table in soup.select(
            '#productDetails_techSpec_section_1, '
            '#productDetails_detailBullets_sections1, '
            '#productDetails_db_sections table, '
            'table'
        ):
            for row in table.select('tr'):
                th = row.select_one('th')
                td = row.select_one('td')
                if not th or not td:
                    continue
                key = self._normalize_extraction_text(th.get_text(' ', strip=True)).lower()
                raw = self._normalize_extraction_text(td.get_text(' ', strip=True))
                if not raw or not (1 < len(raw) < 150):
                    continue
                if key in primary_exact:
                    collected.append((raw, True))
                elif any(sk in key for sk in subcomponent_keys) or any(pk in key for pk in primary_exact):
                    collected.append((raw, False))

        if not collected:
            return None

        # Common single/multi-letter abbreviations that Amazon uses in spec tables.
        _ABBREV = {
            # Plastics
            'pe':    'Polyethylene',
            'pp':    'Polypropylene',
            # Common misspellings / verbose forms
            'polyproplene':              'Polypropylene',
            'polypropylene':             'Polypropylene',
            'polyproplylene':            'Polypropylene',
            'polypropene':               'Polypropylene',
            'polyvinyl chloride':        'PVC',
            'polyvinyl chloride (pvc)':  'PVC',
            'polyvinyl chloride(pvc)':   'PVC',
            'poly vinyl chloride':       'PVC',
            'pvc plastic':               'PVC',
            'acrylonitrile butadiene styrene': 'ABS Plastic',
            'pc':    'Polycarbonate',
            'abs':   'ABS Plastic',
            'pvc':   'PVC',
            'ps':    'Polystyrene',
            'hdpe':  'HDPE',
            'ldpe':  'LDPE',
            'pet':   'PET',
            'tpe':   'TPE',
            'tpu':   'TPU',
            'eva':   'EVA Foam',
            'pu':    'PU',
            'eps':   'Polystyrene',
            'pmma':  'Acrylic',
            # Metals
            'ss':    'Stainless Steel',
            'al':    'Aluminium',
            'cu':    'Copper',
            'zn':    'Zinc',
            # Rubber / elastomers
            'nr':    'Natural Rubber',
            'nbr':   'Rubber',
            'sbr':   'Rubber',
            'epdm':  'Rubber',
            # Textiles / fibres
            'pu leather': 'Faux Leather',
            'mdf':   'MDF',
            'hdf':   'MDF',
        }

        # If a specific subtype is present, its generic parent is redundant.
        # Maps canonical_lower → set of parent canonical_lowers to suppress.
        _PARENTS = {
            # Plastic subtypes → suppress 'Plastic'
            'polyethylene':      {'plastic'},
            'polypropylene':     {'plastic'},
            'polycarbonate':     {'plastic'},
            'abs plastic':       {'plastic'},
            'pvc':               {'plastic'},
            'polystyrene':       {'plastic'},
            'hdpe':              {'plastic'},
            'ldpe':              {'plastic'},
            'pet':               {'plastic'},
            'tpe':               {'plastic'},
            'tpu':               {'plastic'},
            'acrylic':           {'plastic'},
            'pu':                {'plastic'},
            'pmma':              {'plastic', 'acrylic'},
            # Metal subtypes → suppress 'Metal', 'Steel', 'Iron'
            'stainless steel':   {'steel', 'metal', 'iron'},
            'cast iron':         {'iron', 'metal'},
            'carbon steel':      {'steel', 'metal'},
            'galvanised steel':  {'steel', 'metal'},
            'aluminium':         {'metal'},
            'aluminum':          {'metal'},
            'copper':            {'metal'},
            'brass':             {'metal'},
            'bronze':            {'metal', 'brass'},
            'titanium':          {'metal'},
            'zinc':              {'metal'},
            'nickel':            {'metal'},
            'chrome':            {'metal'},
            # Wood subtypes → suppress 'Wood', 'Timber'
            'solid wood':        {'wood', 'timber'},
            'engineered wood':   {'wood', 'timber'},
            'mdf':               {'wood', 'timber'},
            'bamboo':            {'wood'},
            'rattan':            {'wood'},
            'cork':              {'wood'},
            'plywood':           {'wood', 'timber'},
            # Fabric subtypes → suppress 'Fabric'
            'cotton':            {'fabric'},
            'polyester':         {'fabric'},
            'nylon':             {'fabric'},
            'wool':              {'fabric'},
            'linen':             {'fabric'},
            'silk':              {'fabric'},
            'canvas':            {'fabric'},
            'microfibre':        {'fabric'},
            'microfiber':        {'fabric'},
            'velvet':            {'fabric'},
            'fleece':            {'fabric'},
            'denim':             {'fabric'},
            # Leather subtypes → suppress 'Leather'
            'genuine leather':   {'leather'},
            'suede':             {'leather'},
            'faux leather':      {'leather'},
            'pu leather':        {'leather', 'plastic'},
            # Rubber subtypes → suppress 'Rubber'
            'silicone':          {'rubber', 'plastic'},
            'neoprene':          {'rubber'},
            'natural rubber':    {'rubber'},
            'latex':             {'rubber'},
            # Glass subtypes → suppress 'Glass'
            'borosilicate glass':{'glass'},
            'tempered glass':    {'glass'},
            'toughened glass':   {'glass'},
            # Foam subtypes → suppress 'Foam'
            'memory foam':       {'foam'},
            'eva foam':          {'foam', 'plastic'},
        }

        # ── Material name normaliser ────────────────────────────────────────
        # Strips qualifiers that don't change the base material but confuse
        # abbreviation expansion and keyword matching.
        _QUAL_PREFIX = re.compile(
            r'^(?:'
            r'\d{1,4}[/\-]?\d{0,4}\s+'      # "304 " / "18/8 "
            r'|grade\s+\w+\s+'               # "Grade 5 " / "Grade A "
            r'|type\s+\w+\s+'                # "Type 304 "
            r'|bpa[\s\-]free\s+'             # "BPA-Free "
            r'|bpa\s+free\s+'
            r'|food[\s\-]grade\s+'           # "Food Grade "
            r'|medical[\s\-]grade\s+'        # "Medical Grade "
            r'|food[\s\-]safe\s+'            # "Food Safe "
            r'|fda[\s\-]approved\s+'         # "FDA Approved "
            r'|eco[\s\-]friendly\s+'         # "Eco-Friendly "
            r'|premium\s+'                   # "Premium "
            r'|high[\s\-]quality\s+'
            r'|heavy[\s\-]duty\s+'
            r')',
            re.IGNORECASE
        )
        _QUAL_SUFFIX = re.compile(
            r'\s*(?:'
            r'\(?bpa[\s\-]free\)?'           # trailing " (BPA Free)"
            r'|\(?food[\s\-]grade\)?'
            r'|\(?fda[\s\-]approved\)?'
            r'|\d{3,4}\s*(?:series|grade)?'  # trailing "304" / "6061"
            r')',
            re.IGNORECASE
        )
        # Proprietary brand names → generic equivalents
        _BRAND_MATERIALS = {
            'tritan':      'Plastic',
            'lexan':       'Polycarbonate',
            'lucite':      'Acrylic',
            'styrofoam':   'Polystyrene',
            'styropor':    'Polystyrene',
            'mylar':       'PET',
            'gore-tex':    'Synthetic Fabric',
            'gore tex':    'Synthetic Fabric',
            'kevlar':      'Aramid Fibre',
            'cordura':     'Nylon',
            'formica':     'Laminate',
            'corian':      'Acrylic',
            'spandex':     'Elastane',
            'lycra':       'Elastane',
        }

        def _clean_material_name(raw: str) -> str:
            """Strip qualifiers, expand abbreviations, map brand names."""
            n = raw.strip().strip('‎').strip()
            n = _QUAL_PREFIX.sub('', n).strip()
            n = _QUAL_SUFFIX.sub('', n).strip()
            # Strip parenthetical abbreviation suffixes like "(PP)", "(PVC)", "(PP-R)".
            # e.g. "Polypropylene (PP)" → "Polypropylene", "Polyvinyl Chloride (PVC)" → handled by _ABBREV
            n_no_paren = re.sub(r'\s*\([^)]{1,10}\)\s*$', '', n).strip()
            n_lower = n.lower()
            n_no_paren_lower = n_no_paren.lower()
            if n_lower in _BRAND_MATERIALS:
                return _BRAND_MATERIALS[n_lower]
            if n_lower in _ABBREV:
                return _ABBREV[n_lower]
            # Try the version without the parenthetical suffix
            if n_no_paren_lower in _BRAND_MATERIALS:
                return _BRAND_MATERIALS[n_no_paren_lower]
            if n_no_paren_lower in _ABBREV:
                return _ABBREV[n_no_paren_lower]
            return n_no_paren if n_no_paren else n

        # ── Percentage composition parser ───────────────────────────────────
        # Handles "95% Cotton, 5% Elastane" and "Cotton 95%, Elastane 5%"
        _PCT_FIRST = re.compile(
            r'(\d+(?:\.\d+)?)\s*%\s*([A-Za-z][A-Za-z\s\-]{1,30}?)(?=[,;/+]|\d|$)',
        )
        _PCT_LAST  = re.compile(
            r'([A-Za-z][A-Za-z\s\-]{1,30}?)\s+(\d+(?:\.\d+)?)\s*%(?=[,;/+]|$)',
        )

        def _try_parse_percentages(raw_val: str, confidence: float):
            """Return list of {name, confidence_score, weight} if valid % composition found."""
            matches = _PCT_FIRST.findall(raw_val)
            if not matches:
                matches = [(pct, nm) for nm, pct in _PCT_LAST.findall(raw_val)]
            if not matches:
                return None
            total = sum(float(p) for p, _ in matches)
            if not (85 <= total <= 105):   # must roughly sum to 100%
                return None
            result = []
            for pct, nm in matches:
                cleaned = _clean_material_name(nm.strip())
                if cleaned and 2 <= len(cleaned) <= 60:
                    result.append({
                        'name': cleaned,
                        'confidence_score': confidence,
                        'weight': round(float(pct) / 100, 4),
                    })
            return result if result else None

        # ── Main parsing loop ────────────────────────────────────────────────
        # Primary-key entries get confidence 0.95; subcomponent entries get 0.75.
        # Sort so primary-key materials come first.
        parsed = []
        seen = set()
        for raw_val, is_primary in sorted(collected, key=lambda x: not x[1]):
            confidence = 0.95 if is_primary else 0.75

            # Try percentage composition first (e.g. textiles)
            pct_items = _try_parse_percentages(raw_val, confidence)
            if pct_items:
                for item in pct_items:
                    key = item['name'].lower()
                    if key not in seen:
                        seen.add(key)
                        parsed.append(item)
                continue

            # Fallback: split on separators
            parts = re.split(r'[,+/;]', raw_val)
            for part in parts:
                name = _clean_material_name(part)
                if not name:
                    continue
                name_lower = name.lower()
                if len(name) < 2 or len(name) > 60:
                    continue
                if name_lower not in seen:
                    seen.add(name_lower)
                    parsed.append({'name': name, 'confidence_score': confidence})

        if not parsed:
            return None

        # Semantic deduplication: remove generic parents when a specific subtype is present.
        specific_names = {m['name'].lower() for m in parsed}
        parents_to_suppress: set = set()
        for name_lower in specific_names:
            parents_to_suppress |= _PARENTS.get(name_lower, set())
        parsed = [m for m in parsed if m['name'].lower() not in parents_to_suppress]

        if not parsed:
            return None

        # Filter out non-material attribute words that appear in "Material Features" rows.
        # These describe product properties, not the actual material composition.
        _NON_MATERIAL_WORDS = {
            'breathable', 'durable', 'eco friendly', 'eco-friendly', 'hypoallergenic',
            'lightweight', 'waterproof', 'water resistant', 'water-resistant',
            'anti-bacterial', 'antibacterial', 'antimicrobial', 'anti-slip', 'antislip',
            'non-slip', 'nonslip', 'fire resistant', 'fire-resistant', 'flame retardant',
            'heat resistant', 'heat-resistant', 'uv resistant', 'uv-resistant',
            'odour resistant', 'odor resistant', 'stain resistant', 'stain-resistant',
            'soft', 'smooth', 'stretchy', 'flexible', 'rigid', 'transparent',
            'insulated', 'padded', 'reinforced', 'recycled', 'sustainable',
            'machine washable', 'washable', 'dry clean', 'hand wash',
            # Eco-attribute words (not materials)
            'biodegradable', 'natural', 'recyclable', 'organic', 'compostable',
            'plant-based', 'plant based', 'cruelty-free', 'cruelty free', 'vegan',
            # Product-type / technology words
            'bluetooth', 'bluetooth speaker', 'speaker', 'wireless', 'wifi', 'wi-fi',
            'usb', 'usb-c', 'led', 'lcd', 'oled', 'amoled', 'hdmi', 'nfc',
            'rechargeable', 'battery', 'electric', 'electronic',
        }
        parsed = [m for m in parsed if m['name'].lower() not in _NON_MATERIAL_WORDS]

        if not parsed:
            return None

        print(f"🧵 All spec table materials: {[m['name'] for m in parsed]}")
        return {'materials': parsed}

    def _extract_origin_from_title(self, title: str) -> str:
        """Detect manufacturing country mentioned in the product title.

        Handles:
          - "UK Made", "British Made", "Made in UK", "UK Manufactured"
          - "Made in Germany", "Made in USA", "Italian Made" etc.
        Returns a normalised country name or 'Unknown'.
        """
        t = title.lower()

        # Pattern 1: "<country> Made" or "<country> Manufactured"
        m = re.search(r'\b([a-zA-Z][a-zA-Z\s]{1,20}?)\s+(?:made|manufactured)\b', t)
        if m:
            candidate = m.group(1).strip()
            result = normalize_country_name(candidate)
            if result != "Unknown":
                return result

        # Pattern 2: "Made in <country>" or "Manufactured in <country>"
        m = re.search(r'\b(?:made|manufactured)\s+in\s+([a-zA-Z][a-zA-Z\s]{1,20}?)\b(?:\s|$|,|\|)', t)
        if m:
            candidate = m.group(1).strip()
            result = normalize_country_name(candidate)
            if result != "Unknown":
                return result

        # Pattern 3: Nationality adjective — "British Made", "Italian Design"
        _NATIONALITY = {
            'british': 'UK', 'english': 'UK', 'scottish': 'UK', 'welsh': 'UK',
            'american': 'USA', 'german': 'Germany', 'french': 'France',
            'italian': 'Italy', 'spanish': 'Spain', 'japanese': 'Japan',
            'chinese': 'China', 'korean': 'South Korea', 'swedish': 'Sweden',
            'danish': 'Denmark', 'dutch': 'Netherlands', 'canadian': 'Canada',
            'australian': 'Australia', 'indian': 'India',
        }
        for adj, country in _NATIONALITY.items():
            if re.search(r'\b' + adj + r'\s+(?:made|manufactured|design|crafted|built)\b', t):
                return country

        return "Unknown"

    def extract_origin_from_spec_table(self, soup: BeautifulSoup) -> str:
        """Extract country of origin from Amazon's structured product detail tables (highest confidence)."""
        origin_keys = [
            'country of origin', 'country/region of origin', 'country or region of origin',
            'manufactured in', 'made in', 'imported from', 'product of', 'origin',
        ]

        # Method 1: th/td table rows
        for table in soup.select(
            '#productDetails_techSpec_section_1, '
            '#productDetails_detailBullets_sections1, '
            '#productDetails_db_sections table, '
            'table'
        ):
            for row in table.select('tr'):
                th = row.select_one('th')
                td = row.select_one('td')
                if not th or not td:
                    continue
                key = self._normalize_extraction_text(th.get_text(' ', strip=True)).lower()
                if any(ok in key for ok in origin_keys):
                    value = self._normalize_extraction_text(td.get_text(' ', strip=True))
                    normalized = normalize_country_name(value)
                    if normalized != "Unknown":
                        print(f"🌍 Spec table origin (th/td): '{value}' → '{normalized}'")
                        return normalized

        # Method 2: Detail bullets
        for li in soup.select('#detailBullets_feature_div li, #detailBulletsWrapper_feature_div li'):
            text = self._normalize_extraction_text(li.get_text(' ', strip=True))
            for ok in origin_keys:
                if ok in text.lower():
                    match = re.search(
                        r'(?:' + re.escape(ok) + r')[\s\u200e\u200f:‎]+([a-zA-Z][a-zA-Z\s\-]{1,40})',
                        text, re.IGNORECASE
                    )
                    if match:
                        candidate = match.group(1).strip().strip('‎').strip()
                        normalized = normalize_country_name(candidate)
                        if normalized != "Unknown":
                            print(f"🌍 Detail bullets origin: '{candidate}' → '{normalized}'")
                            return normalized

        # Method 3: po-attribute-list
        for row in soup.select('.po-attribute-list tr, .po-attribute-list__item'):
            label_el = row.select_one('.po-attribute-list__label, .a-span3')
            value_el = row.select_one('.po-attribute-list__value, .a-span9')
            if not label_el or not value_el:
                continue
            key = self._normalize_extraction_text(label_el.get_text(' ', strip=True)).lower()
            if any(ok in key for ok in origin_keys):
                value = self._normalize_extraction_text(value_el.get_text(' ', strip=True))
                normalized = normalize_country_name(value)
                if normalized != "Unknown":
                    print(f"🌍 po-attribute origin: '{value}' → '{normalized}'")
                    return normalized

        return "Unknown"

    def extract_origin_from_explicit_sections(self, soup: BeautifulSoup) -> str:
        """Extract from explicit sections like manufacturer address/spec rows."""
        # Note: extract_origin_from_spec_table is already called before this method
        # in extract_from_soup — skip it here to avoid redundant work.

        # Scan section text for patterns
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

    scraper = RequestsScraper()
    return scraper.scrape_product(url)

if __name__ == "__main__":
    test_url = "https://www.amazon.co.uk/dp/B000GIPJ0M"
    result = scrape_with_requests(test_url)
    print(f"Result: {result}")