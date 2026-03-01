#!/usr/bin/env python3
"""
Category Detection System for Amazon Products
Detects product categories from URLs and content to apply category-specific extraction rules
"""

import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

class CategoryDetector:
    """Intelligent product category detection for Amazon products"""
    
    def __init__(self):
        # URL-based category patterns
        self.url_category_patterns = {
            'books': [
                r'/books/',
                r'/kindle-ebooks/',
                r'/book/',
                r'/dp/[0-9]{10}',  # Traditional ISBN-like format often indicates books
                r'/textbooks/',
                r'/literature/',
                r'/biography/'
            ],
            'electronics': [
                r'/electronics/',
                r'/computers/',
                r'/phones/',
                r'/tv-audio/',
                r'/camera/',
                r'/gaming/',
                r'/smart-home/',
                r'/wearable-tech/',
                r'/tablets/',
                r'/laptops/'
            ],
            'health': [
                r'/health/',
                r'/sports/',
                r'/beauty/',
                r'/vitamins/',
                r'/supplements/',
                r'/nutrition/',
                r'/fitness/',
                r'/wellness/',
                r'/personal-care/'
            ],
            'home': [
                r'/home/',
                r'/kitchen/',
                r'/garden/',
                r'/diy/',
                r'/furniture/',
                r'/appliances/',
                r'/bedding/',
                r'/lighting/',
                r'/storage/'
            ],
            'clothing': [
                r'/clothing/',
                r'/shoes/',
                r'/fashion/',
                r'/jewelry/',
                r'/watches/',
                r'/bags/',
                r'/accessories/',
                r'/mens/',
                r'/womens/'
            ],
            'toys': [
                r'/toys/',
                r'/games/',
                r'/baby/',
                r'/kids/',
                r'/educational/',
                r'/outdoor-play/',
                r'/board-games/',
                r'/puzzles/'
            ],
            'automotive': [
                r'/automotive/',
                r'/car/',
                r'/motorbike/',
                r'/tools/',
                r'/garage/',
                r'/vehicle/'
            ],
            'food': [
                r'/grocery/',
                r'/food/',
                r'/beverages/',
                r'/snacks/',
                r'/pantry/',
                r'/fresh/',
                r'/organic/'
            ]
        }
        
        # Title-based keyword patterns for content analysis
        self.title_keywords = {
            'books': [
                'book', 'novel', 'guide', 'manual', 'autobiography', 'biography',
                'textbook', 'cookbook', 'diary', 'journal', 'paperback', 'hardcover',
                'kindle', 'ebook', 'audio book', 'story', 'tales', 'edition',
                'volume', 'series', 'collection', 'memoir', 'history', 'fiction'
            ],
            'electronics': [
                'phone', 'tablet', 'laptop', 'computer', 'camera', 'headphones',
                'speaker', 'tv', 'monitor', 'mouse', 'keyboard', 'charger',
                'cable', 'adapter', 'battery', 'case', 'screen', 'wireless',
                'bluetooth', 'usb', 'hdmi', 'smart', 'digital', 'electronic'
            ],
            'health': [
                'protein', 'vitamin', 'supplement', 'whey', 'creatine', 'bcaa',
                'omega', 'probiotic', 'multivitamin', 'calcium', 'iron',
                'magnesium', 'zinc', 'fitness', 'workout', 'nutrition',
                'health', 'wellness', 'medical', 'therapy', 'treatment'
            ],
            'home': [
                'kitchen', 'cookware', 'utensil', 'appliance', 'furniture',
                'chair', 'table', 'bed', 'sofa', 'lamp', 'light', 'curtain',
                'rug', 'carpet', 'storage', 'organizer', 'decor', 'vase',
                'plant', 'garden', 'tool', 'cleaning', 'vacuum'
            ],
            'clothing': [
                'shirt', 't-shirt', 'dress', 'pants', 'jeans', 'jacket',
                'coat', 'shoes', 'boots', 'sneakers', 'hat', 'cap',
                'scarf', 'gloves', 'belt', 'bag', 'purse', 'wallet',
                'watch', 'jewelry', 'necklace', 'ring', 'bracelet'
            ],
            'toys': [
                'toy', 'game', 'puzzle', 'doll', 'action figure', 'lego',
                'blocks', 'board game', 'card game', 'educational toy',
                'baby toy', 'plush', 'stuffed animal', 'craft', 'art',
                'play', 'playground', 'outdoor toy', 'sports toy'
            ],
            'automotive': [
                'car', 'auto', 'vehicle', 'tire', 'wheel', 'engine',
                'brake', 'filter', 'oil', 'battery', 'alternator',
                'starter', 'suspension', 'exhaust', 'transmission',
                'clutch', 'steering', 'dashboard', 'seat cover'
            ],
            'food': [
                'food', 'snack', 'drink', 'beverage', 'coffee', 'tea',
                'chocolate', 'candy', 'cookie', 'cereal', 'pasta',
                'sauce', 'spice', 'seasoning', 'organic', 'natural',
                'fresh', 'frozen', 'canned', 'dried', 'healthy'
            ]
        }
        
        # Category-specific extraction rules
        self.category_rules = {
            'books': {
                'brand_detection': False,  # Authors are not brands
                'typical_weight_range': (0.1, 2.0),  # 100g - 2kg
                'material_default': 'Paper',
                'origin_importance': 'low',  # Books can be printed anywhere
                'author_patterns': [r'by\s+([A-Z][a-zA-Z\s\.]+)', r'author[:\s]*([A-Z][a-zA-Z\s\.]+)']
            },
            'electronics': {
                'brand_detection': True,
                'typical_weight_range': (0.01, 10.0),  # 10g - 10kg
                'material_default': 'Mixed',
                'origin_importance': 'high',  # Origin matters for electronics
                'common_materials': ['Plastic', 'Metal', 'Glass', 'Mixed']
            },
            'health': {
                'brand_detection': True,
                'typical_weight_range': (0.05, 5.0),  # 50g - 5kg
                'material_default': 'Mixed',
                'origin_importance': 'medium',
                'serving_exclusions': [  # Ignore serving size info
                    r'\d+\s*g\s*per\s*serving',
                    r'\d+\s*mg\s*(?:sodium|caffeine|vitamin)',
                    r'\d+\s*(?:cal|kcal)\b',
                    r'\d+\s*servings?\b'
                ]
            },
            'home': {
                'brand_detection': True,
                'typical_weight_range': (0.1, 50.0),  # 100g - 50kg
                'material_default': 'Mixed',
                'origin_importance': 'medium',
                'common_materials': ['Wood', 'Metal', 'Plastic', 'Fabric', 'Glass', 'Mixed']
            },
            'clothing': {
                'brand_detection': True,
                'typical_weight_range': (0.02, 3.0),  # 20g - 3kg
                'material_default': 'Fabric',
                'origin_importance': 'medium',
                'common_materials': ['Fabric', 'Cotton', 'Leather', 'Synthetic']
            },
            'toys': {
                'brand_detection': True,
                'typical_weight_range': (0.01, 10.0),  # 10g - 10kg
                'material_default': 'Plastic',
                'origin_importance': 'high',  # Safety regulations vary by country
                'common_materials': ['Plastic', 'Wood', 'Metal', 'Fabric', 'Mixed']
            },
            'automotive': {
                'brand_detection': True,
                'typical_weight_range': (0.05, 100.0),  # 50g - 100kg
                'material_default': 'Metal',
                'origin_importance': 'high',
                'common_materials': ['Metal', 'Plastic', 'Rubber', 'Mixed']
            },
            'food': {
                'brand_detection': True,
                'typical_weight_range': (0.01, 10.0),  # 10g - 10kg
                'material_default': 'Mixed',
                'origin_importance': 'medium',
                'nutritional_exclusions': [  # Ignore nutritional facts
                    r'\d+\s*(?:cal|kcal)\b',
                    r'\d+\s*g\s*(?:protein|carb|fat|sugar|fiber)\b',
                    r'\d+\s*mg\s*(?:sodium|caffeine|vitamin)\b'
                ]
            }
        }
        
    def detect_category(self, url: str, title: str = "", soup: BeautifulSoup = None) -> Dict[str, any]:
        """
        Detect product category using URL patterns, title keywords, and page content
        Returns category with confidence score and detection method
        """
        result = {
            'category': 'general',
            'confidence': 0.0,
            'detection_method': 'default',
            'evidence': []
        }
        
        # Method 1: URL-based detection (highest confidence)
        url_category = self.detect_from_url(url)
        if url_category:
            result.update({
                'category': url_category['category'],
                'confidence': url_category['confidence'],
                'detection_method': 'url_pattern',
                'evidence': url_category['evidence']
            })
            
            # If URL detection is highly confident, return early
            if url_category['confidence'] >= 0.9:
                return result
        
        # Method 2: Title-based detection
        if title:
            title_category = self.detect_from_title(title)
            if title_category:
                # Combine with URL evidence if available
                if result['confidence'] < title_category['confidence']:
                    result.update({
                        'category': title_category['category'],
                        'confidence': title_category['confidence'],
                        'detection_method': 'title_keywords'
                    })
                result['evidence'].extend(title_category['evidence'])
        
        # Method 3: Content-based detection (if BeautifulSoup provided)
        if soup:
            content_category = self.detect_from_content(soup)
            if content_category and content_category['confidence'] > result['confidence']:
                result.update({
                    'category': content_category['category'],
                    'confidence': content_category['confidence'],
                    'detection_method': 'page_content'
                })
                result['evidence'].extend(content_category['evidence'])
        
        return result
        
    def detect_from_url(self, url: str) -> Optional[Dict[str, any]]:
        """Detect category from URL patterns"""
        if not url:
            return None
            
        url_lower = url.lower()
        
        for category, patterns in self.url_category_patterns.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    matches.append(pattern)
            
            if matches:
                # More matches = higher confidence
                confidence = min(0.5 + (len(matches) * 0.2), 0.95)
                return {
                    'category': category,
                    'confidence': confidence,
                    'evidence': [f"URL pattern: {match}" for match in matches]
                }
        
        return None
        
    def detect_from_title(self, title: str) -> Optional[Dict[str, any]]:
        """Detect category from title keywords"""
        if not title:
            return None
            
        title_lower = title.lower()
        category_scores = {}
        
        for category, keywords in self.title_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword in title_lower:
                    matches.append(keyword)
            
            if matches:
                # Calculate score based on number and relevance of matches
                score = len(matches) / len(keywords)
                category_scores[category] = {
                    'score': score,
                    'matches': matches
                }
        
        if category_scores:
            # Get category with highest score
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
            best_score = category_scores[best_category]['score']
            
            # Convert score to confidence (0.3 - 0.8 range for title detection)
            confidence = min(0.3 + (best_score * 0.5), 0.8)
            
            return {
                'category': best_category,
                'confidence': confidence,
                'evidence': [f"Title keyword: {match}" for match in category_scores[best_category]['matches']]
            }
        
        return None
        
    def detect_from_content(self, soup: BeautifulSoup) -> Optional[Dict[str, any]]:
        """Detect category from page content analysis"""
        if not soup:
            return None
            
        # Extract relevant text sections
        content_sections = []
        
        # Product description
        desc_selectors = ['#feature-bullets', '.a-unordered-list', '#productDescription']
        for selector in desc_selectors:
            elements = soup.select(selector)
            for element in elements:
                content_sections.append(element.get_text().lower())
        
        # Category breadcrumbs
        breadcrumb_selectors = ['#wayfinding-breadcrumbs', '.a-breadcrumb', '.breadcrumb']
        for selector in breadcrumb_selectors:
            elements = soup.select(selector)
            for element in elements:
                content_sections.append(element.get_text().lower())
        
        if not content_sections:
            return None
            
        # Analyze combined content
        combined_content = ' '.join(content_sections)
        
        category_scores = {}
        for category, keywords in self.title_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword in combined_content:
                    matches.append(keyword)
            
            if matches:
                # Weight content matches lower than title matches
                score = len(matches) / len(keywords) * 0.7
                category_scores[category] = {
                    'score': score,
                    'matches': matches
                }
        
        if category_scores:
            best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
            best_score = category_scores[best_category]['score']
            
            # Lower confidence for content-based detection
            confidence = min(0.2 + (best_score * 0.4), 0.6)
            
            return {
                'category': best_category,
                'confidence': confidence,
                'evidence': [f"Content keyword: {match}" for match in category_scores[best_category]['matches'][:3]]
            }
        
        return None
        
    def get_category_rules(self, category: str) -> Dict[str, any]:
        """Get extraction rules for a specific category"""
        return self.category_rules.get(category, self.category_rules.get('general', {}))
        
    def should_detect_brand(self, category: str) -> bool:
        """Check if brand detection should be performed for this category"""
        rules = self.get_category_rules(category)
        return rules.get('brand_detection', True)
        
    def get_expected_weight_range(self, category: str) -> Tuple[float, float]:
        """Get expected weight range for category validation"""
        rules = self.get_category_rules(category)
        return rules.get('typical_weight_range', (0.01, 100.0))
        
    def get_default_material(self, category: str) -> str:
        """Get default material for category"""
        rules = self.get_category_rules(category)
        return rules.get('material_default', 'Mixed')
        
    def get_nutritional_exclusions(self, category: str) -> List[str]:
        """Get nutritional content exclusion patterns for category"""
        rules = self.get_category_rules(category)
        return rules.get('nutritional_exclusions', []) + rules.get('serving_exclusions', [])
        
    def validate_weight_for_category(self, weight: float, category: str) -> Dict[str, any]:
        """Validate if weight is reasonable for the detected category"""
        expected_range = self.get_expected_weight_range(category)
        min_weight, max_weight = expected_range
        
        is_valid = min_weight <= weight <= max_weight
        
        result = {
            'is_valid': is_valid,
            'expected_range': expected_range,
            'weight': weight,
            'category': category
        }
        
        if not is_valid:
            if weight < min_weight:
                result['issue'] = f"Weight too low for {category} (got {weight}kg, expected ≥{min_weight}kg)"
            else:
                result['issue'] = f"Weight too high for {category} (got {weight}kg, expected ≤{max_weight}kg)"
        
        return result


def test_category_detector():
    """Test the category detection system"""
    detector = CategoryDetector()
    
    test_cases = [
        {
            'url': 'https://www.amazon.co.uk/Isolate-Protein-Fast-digesting-hydrolysate-Gourmet/dp/B01H3O2AMG',
            'title': 'MUTANT ISO Surge | Whey Isolate Protein Powder | 25g Protein',
            'expected_category': 'health'
        },
        {
            'url': 'https://www.amazon.co.uk/books/dp/0241988462',
            'title': 'All In: The Autobiography of Billie Jean King',
            'expected_category': 'books'
        },
        {
            'url': 'https://www.amazon.co.uk/electronics/dp/B0CHWRXH8B',
            'title': 'iPhone 15 Pro Case Clear Protective Cover',
            'expected_category': 'electronics'
        },
        {
            'url': 'https://www.amazon.co.uk/kitchen/dp/B087LBQZPX',
            'title': 'De\'Longhi Coffee Machine Espresso Maker',
            'expected_category': 'home'
        }
    ]
    
    print("🧪 Testing Category Detection System")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📦 TEST {i}: {case['expected_category'].upper()}")
        print(f"URL: {case['url'][:50]}...")
        print(f"Title: {case['title']}")
        
        result = detector.detect_category(case['url'], case['title'])
        
        success = "✅" if result['category'] == case['expected_category'] else "❌"
        print(f"\n{success} Detected: {result['category']} (confidence: {result['confidence']:.1%})")
        print(f"   Method: {result['detection_method']}")
        print(f"   Evidence: {', '.join(result['evidence'][:3])}")
        
        # Test category rules
        rules = detector.get_category_rules(result['category'])
        print(f"   Brand detection: {'Yes' if detector.should_detect_brand(result['category']) else 'No'}")
        print(f"   Weight range: {detector.get_expected_weight_range(result['category'])}")
        print(f"   Default material: {detector.get_default_material(result['category'])}")


if __name__ == "__main__":
    test_category_detector()