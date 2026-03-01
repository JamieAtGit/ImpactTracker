import json
import os
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

# === CONFIG ===
BRAND_ORIGIN_JSON = os.path.join(os.path.dirname(__file__), "json", "brand_orign_data.json")  # Note: keeping existing typo

# === INTELLIGENT BRAND ORIGIN DETECTION ===

class EnhancedBrandResolver:
    """
    🧠 INTELLIGENT BRAND ORIGIN DETECTION - Senior Developer Grade
    
    What assumptions are you making here?
    - Brand names have common variations (Apple vs Apple Inc.)
    - Product titles contain origin clues ("Made in Germany")
    - Company suffixes indicate origin (GmbH = Germany, Ltd = UK)
    - Domain patterns correlate with origin (.de = Germany)
    - Industry clusters exist (luxury fashion → Italy/France)
    
    Check for hidden edge cases:
    - International brands with manufacturing subsidiaries
    - Generic brand names (Amazon Basics, Kirkland)
    - Typos and formatting differences
    - Multiple brand variations (Coca-Cola, Coke, Coca Cola)
    """
    
    def __init__(self):
        self.exact_matches = self._load_brand_data()
        self.domain_patterns = self._build_domain_patterns()
        self.company_suffix_patterns = self._build_suffix_patterns()
        self.industry_patterns = self._build_industry_patterns()
        self.origin_keywords = self._build_origin_keywords()
        self.learning_cache = {}
    
    def _load_brand_data(self) -> Dict:
        """Load existing brand data with error handling"""
        try:
            if os.path.exists(BRAND_ORIGIN_JSON):
                with open(BRAND_ORIGIN_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading brand data: {e}")
        return {}
    
    def _build_domain_patterns(self) -> Dict[str, str]:
        """Domain TLD to country mapping - Handle edge cases"""
        return {
            '.de': 'Germany', '.fr': 'France', '.it': 'Italy', '.es': 'Spain',
            '.co.uk': 'UK', '.uk': 'UK', '.com.au': 'Australia', '.ca': 'Canada',
            '.jp': 'Japan', '.kr': 'South Korea', '.cn': 'China', '.in': 'India',
            '.br': 'Brazil', '.mx': 'Mexico', '.nl': 'Netherlands', '.se': 'Sweden',
            '.dk': 'Denmark', '.no': 'Norway', '.fi': 'Finland', '.ch': 'Switzerland',
            '.at': 'Austria', '.be': 'Belgium', '.ie': 'Ireland', '.pl': 'Poland'
        }
    
    def _build_suffix_patterns(self) -> Dict[str, str]:
        """Company suffix patterns with confidence scoring"""
        return {
            # High confidence patterns
            'gmbh': 'Germany', 'ag': 'Germany', 'kg': 'Germany',
            'ltd': 'UK', 'limited': 'UK', 'plc': 'UK',
            'srl': 'Italy', 'spa': 'Italy', 'sas': 'France', 'sarl': 'France',
            'bv': 'Netherlands', 'nv': 'Netherlands', 'ab': 'Sweden',
            'oy': 'Finland', 'as': 'Norway', 'aps': 'Denmark',
            'pty': 'Australia', 'sa': 'Switzerland',
            # Medium confidence patterns  
            'inc': 'USA', 'corp': 'USA', 'llc': 'USA', 'co': 'USA'
        }
    
    def _build_industry_patterns(self) -> Dict[str, List[Tuple[str, float]]]:
        """Industry clustering with probability scores"""
        return {
            'luxury_fashion': [('Italy', 0.35), ('France', 0.30), ('UK', 0.15), ('USA', 0.20)],
            'automotive': [('Germany', 0.25), ('Japan', 0.25), ('USA', 0.20), ('South Korea', 0.15), ('Italy', 0.15)],
            'electronics': [('China', 0.35), ('South Korea', 0.20), ('Japan', 0.20), ('Taiwan', 0.15), ('USA', 0.10)],
            'furniture': [('Sweden', 0.20), ('Germany', 0.15), ('China', 0.30), ('Italy', 0.15), ('Denmark', 0.20)],
            'watches': [('Switzerland', 0.60), ('Japan', 0.25), ('Germany', 0.10), ('USA', 0.05)],
            'cosmetics': [('France', 0.25), ('USA', 0.25), ('South Korea', 0.20), ('Japan', 0.15), ('Germany', 0.15)],
            'spirits': [('UK', 0.25), ('France', 0.20), ('USA', 0.20), ('Germany', 0.15), ('Japan', 0.20)],
            'tools': [('Germany', 0.30), ('USA', 0.25), ('Japan', 0.20), ('Sweden', 0.15), ('UK', 0.10)]
        }
    
    def _build_origin_keywords(self) -> Dict[str, List[str]]:
        """Direct origin mentions in product text"""
        return {
            'Germany': ['made in germany', 'german made', 'manufactured in germany', 'deutsches qualität'],
            'Japan': ['made in japan', 'japanese', 'manufactured in japan', 'japan quality'],
            'USA': ['made in usa', 'american made', 'manufactured in america', 'us made'],
            'UK': ['made in uk', 'british made', 'made in britain', 'english made'],
            'Italy': ['made in italy', 'italian made', 'fatto in italia'],
            'France': ['made in france', 'french made', 'fabriqué en france'],
            'Switzerland': ['swiss made', 'made in switzerland', 'schweizer qualität'],
            'China': ['made in china', 'manufactured in china', 'chinese made'],
            'South Korea': ['made in korea', 'korean made', 'manufactured in korea'],
            'Sweden': ['swedish made', 'made in sweden', 'svensk kvalitet']
        }
    
    def fuzzy_match_brand(self, target_brand: str, threshold: float = 0.75) -> Optional[Tuple[str, float]]:
        """
        Fuzzy brand matching with intelligent normalization
        Handles edge cases like abbreviations, typos, format differences
        """
        target_clean = self._normalize_brand_name(target_brand)
        best_match = None
        best_score = 0.0
        
        for known_brand in self.exact_matches.keys():
            known_clean = self._normalize_brand_name(known_brand)
            
            # Multiple similarity algorithms
            similarity = SequenceMatcher(None, target_clean, known_clean).ratio()
            
            # Bonus scoring for exact word matches
            if self._has_exact_word_match(target_clean, known_clean):
                similarity += 0.15
            
            # Bonus for common abbreviations
            if self._is_common_abbreviation(target_clean, known_clean):
                similarity += 0.20
                
            if similarity >= threshold and similarity > best_score:
                best_match = known_brand
                best_score = similarity
        
        return (best_match, best_score) if best_match else None
    
    def _normalize_brand_name(self, brand: str) -> str:
        """Intelligent brand name normalization"""
        if not brand:
            return ""
            
        # Convert to lowercase and strip
        brand = brand.lower().strip()
        
        # Remove common corporate suffixes
        brand = re.sub(r'\b(inc|corp|corporation|ltd|limited|gmbh|ag|sa|srl|llc|co|company)\b\.?', '', brand)
        
        # Remove special characters but preserve spaces
        brand = re.sub(r'[^\w\s]', '', brand)
        
        # Normalize multiple spaces
        brand = re.sub(r'\s+', ' ', brand).strip()
        
        return brand
    
    def _has_exact_word_match(self, brand1: str, brand2: str) -> bool:
        """Check for exact word overlaps"""
        words1 = set(word for word in brand1.split() if len(word) > 2)
        words2 = set(word for word in brand2.split() if len(word) > 2)
        return len(words1.intersection(words2)) > 0
    
    def _is_common_abbreviation(self, short: str, long: str) -> bool:
        """Detect common brand abbreviations"""
        if len(short) < len(long):
            # Check if short is acronym of long
            acronym = ''.join(word[0] for word in long.split() if word)
            return short == acronym
        return False
    
    def extract_origin_from_text(self, text: str) -> Optional[Tuple[str, float]]:
        """Extract origin mentions from product title/description"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        for country, keywords in self.origin_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Higher confidence for explicit "made in" statements
                    confidence = 0.90 if 'made in' in keyword else 0.75
                    return (country, confidence)
        
        return None
    
    def analyze_domain_origin(self, text: str) -> Optional[Tuple[str, float]]:
        """Extract origin from domain mentions"""
        if not text:
            return None
            
        text = text.lower()
        
        for domain, country in self.domain_patterns.items():
            if domain in text:
                # Higher confidence for longer, more specific domains
                confidence = 0.70 if len(domain) > 3 else 0.50
                return (country, confidence)
        
        return None
    
    def analyze_company_suffix(self, brand: str) -> Optional[Tuple[str, float]]:
        """Detect origin from company legal structure"""
        brand_lower = brand.lower().strip()
        
        for suffix, country in self.company_suffix_patterns.items():
            pattern = f'\\b{re.escape(suffix)}\\b'
            if re.search(pattern, brand_lower):
                # Different confidence levels based on suffix specificity
                confidence_map = {
                    'gmbh': 0.85, 'ag': 0.85, 'srl': 0.85, 'oy': 0.85,
                    'ltd': 0.70, 'inc': 0.60, 'llc': 0.60, 'co': 0.30
                }
                confidence = confidence_map.get(suffix, 0.50)
                return (country, confidence)
        
        return None
    
    def get_industry_pattern(self, product_title: str) -> Optional[Tuple[str, float]]:
        """Industry-based origin prediction with intelligent categorization"""
        if not product_title:
            return None
            
        text = product_title.lower()
        
        # Enhanced keyword matching for industries
        industry_keywords = {
            'luxury_fashion': ['luxury', 'designer', 'haute couture', 'fashion', 'gucci', 'prada', 'chanel', 'dior'],
            'automotive': ['car', 'vehicle', 'automotive', 'bmw', 'mercedes', 'audi', 'volkswagen', 'toyota'],
            'electronics': ['smartphone', 'laptop', 'computer', 'electronics', 'samsung', 'apple', 'sony', 'lg'],
            'furniture': ['furniture', 'chair', 'table', 'sofa', 'desk', 'ikea', 'herman miller'],
            'watches': ['watch', 'timepiece', 'chronograph', 'rolex', 'omega', 'tag heuer', 'tissot'],
            'cosmetics': ['cosmetics', 'makeup', 'skincare', 'beauty', 'perfume', 'loreal', 'chanel'],
            'spirits': ['whisky', 'vodka', 'gin', 'rum', 'cognac', 'wine', 'champagne'],
            'tools': ['tools', 'drill', 'saw', 'wrench', 'bosch', 'makita', 'dewalt']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                if industry in self.industry_patterns:
                    # Return most likely country for this industry
                    country, probability = self.industry_patterns[industry][0]
                    return (country, probability)
        
        return None
    
    def intelligent_brand_resolution(self, brand: str, product_title: str = "", 
                                   additional_context: str = "") -> Dict:
        """
        🎯 MAIN INTELLIGENT RESOLUTION - Comprehensive brand origin detection
        
        Hierarchical approach with confidence scoring:
        1. Exact match (confidence: 0.95)
        2. Fuzzy match (confidence: 0.75-0.90)
        3. Direct origin mentions (confidence: 0.75-0.90)
        4. Domain analysis (confidence: 0.50-0.70)
        5. Company suffix (confidence: 0.30-0.85)
        6. Industry patterns (confidence: 0.20-0.60)
        """
        
        if not brand or brand.strip() == "":
            return self._unknown_result("Empty brand name provided")
        
        brand_clean = brand.strip()
        combined_text = f"{brand} {product_title} {additional_context}"
        
        # Step 1: Exact Match (Highest Confidence)
        exact_match = self.exact_matches.get(brand_clean.lower())
        if exact_match:
            return {
                "country": exact_match["country"],
                "city": exact_match.get("city", "Unknown"),
                "confidence": 0.95,
                "source": "exact_database_match",
                "reasoning": f"✅ Exact database match for '{brand_clean}'"
            }
        
        # Step 2: Fuzzy Match (High Confidence)
        fuzzy_result = self.fuzzy_match_brand(brand_clean)
        if fuzzy_result:
            matched_brand, similarity = fuzzy_result
            match_data = self.exact_matches[matched_brand]
            return {
                "country": match_data["country"],
                "city": match_data.get("city", "Unknown"),
                "confidence": 0.75 + (similarity * 0.15),  # 0.75-0.90 range
                "source": "fuzzy_database_match",
                "reasoning": f"🔍 Fuzzy match: '{brand_clean}' → '{matched_brand}' ({similarity:.2f} similarity)"
            }
        
        # Step 3: Direct Origin Mentions (High Confidence)
        origin_mention = self.extract_origin_from_text(combined_text)
        if origin_mention:
            country, confidence = origin_mention
            return {
                "country": country,
                "city": "Unknown",
                "confidence": confidence,
                "source": "text_origin_mention",
                "reasoning": f"📝 Direct origin mention found in product text: {country}"
            }
        
        # Step 4: Domain Analysis (Medium Confidence)
        domain_result = self.analyze_domain_origin(combined_text)
        if domain_result:
            country, confidence = domain_result
            return {
                "country": country,
                "city": "Unknown",
                "confidence": confidence,
                "source": "domain_analysis",
                "reasoning": f"🌐 Domain pattern suggests {country} origin"
            }
        
        # Step 5: Company Suffix Analysis (Variable Confidence)
        suffix_result = self.analyze_company_suffix(brand_clean)
        if suffix_result:
            country, confidence = suffix_result
            return {
                "country": country,
                "city": "Unknown",
                "confidence": confidence,
                "source": "company_suffix",
                "reasoning": f"🏢 Company legal structure suggests {country} origin"
            }
        
        # Step 6: Industry Pattern Analysis (Lower Confidence)
        industry_result = self.get_industry_pattern(product_title)
        if industry_result:
            country, confidence = industry_result
            return {
                "country": country,
                "city": "Unknown",
                "confidence": confidence,
                "source": "industry_pattern",
                "reasoning": f"📊 Industry pattern analysis suggests {country} origin"
            }
        
        # Final fallback
        return self._unknown_result(f"No reliable origin data found for brand '{brand_clean}'")
    
    def _unknown_result(self, reason: str) -> Dict:
        """Standardized unknown result"""
        return {
            "country": "Unknown",
            "city": "Unknown",
            "confidence": 0.0,
            "source": "no_data_found",
            "reasoning": f"❌ {reason}"
        }
    
    def learn_from_success(self, brand: str, detected_country: str, confidence: float):
        """Machine learning component - learn from successful detections"""
        if confidence >= 0.80:  # Only learn from high-confidence matches
            self.learning_cache[brand.lower()] = {
                "country": detected_country,
                "confidence": confidence,
                "learned_at": "auto_detection"
            }

# === GLOBAL RESOLVER INSTANCE ===
_enhanced_resolver = EnhancedBrandResolver()

# === BACKWARD COMPATIBILITY FUNCTIONS ===

def load_brand_origin_data():
    """Legacy function for backward compatibility"""
    return _enhanced_resolver.exact_matches

def save_brand_origin_data(data):
    """Legacy function for backward compatibility"""
    try:
        with open(BRAND_ORIGIN_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"⚠️ Error saving brand data: {e}")

def get_brand_origin(brand):
    """Legacy function - now uses intelligent resolution"""
    result = _enhanced_resolver.intelligent_brand_resolution(brand)
    return {
        "country": result["country"],
        "city": result["city"]
    }

def get_brand_origin_intelligent(brand, product_title="", additional_context=""):
    """
    🚀 NEW INTELLIGENT FUNCTION - Use this for enhanced brand detection
    
    Returns comprehensive result with confidence scoring and reasoning
    """
    return _enhanced_resolver.intelligent_brand_resolution(brand, product_title, additional_context)

def update_brand_origin(brand, country, city="Unknown"):
    """Legacy function for backward compatibility"""
    brand = brand.lower().strip()
    data = load_brand_origin_data()
    data[brand] = {"country": country.title(), "city": city.title()}
    save_brand_origin_data(data)
