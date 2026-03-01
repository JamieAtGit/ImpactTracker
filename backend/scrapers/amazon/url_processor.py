#!/usr/bin/env python3
"""
URL Processor for handling full Amazon URLs as users provide them
No ASIN extraction - works directly with complete URLs
"""

import re
import urllib.parse as urlparse
from typing import Dict, List, Optional, Tuple

class AmazonURLProcessor:
    """Process and validate Amazon URLs exactly as users provide them"""
    
    def __init__(self):
        # Common Amazon domain patterns
        self.amazon_domains = [
            'amazon.co.uk', 'amazon.com', 'amazon.ca', 'amazon.de',
            'amazon.fr', 'amazon.it', 'amazon.es', 'amazon.com.au',
            'amazon.in', 'amazon.co.jp'
        ]
        
        # Product URL patterns that indicate valid Amazon product pages
        self.product_patterns = [
            r'/dp/',           # Standard product page: /dp/B01H3O2AMG
            r'/gp/product/',   # Alternative format: /gp/product/B01H3O2AMG  
            r'/product/',      # Short format: /product/B01H3O2AMG
            r'/gp/aw/d/',      # Mobile format: /gp/aw/d/B01H3O2AMG
        ]
        
        # Parameters to remove for cleaner URLs (tracking, session, etc.)
        self.tracking_params = {
            'ref', 'ref_', 'tag', 'linkCode', 'camp', 'creative', 'creativeASIN',
            'adid', 'crid', 'dchild', 'keywords', 'pd_rd_i', 'pd_rd_r', 'pd_rd_w',
            'pd_rd_wg', 'pf_rd_i', 'pf_rd_m', 'pf_rd_p', 'pf_rd_r', 'pf_rd_s',
            'pf_rd_t', 'qid', 'sr', 'sprefix', 'th', 'psc', 'dib', 'dib_tag'
        }
        
    def validate_amazon_url(self, url: str) -> Dict[str, any]:
        """
        Validate if URL is a valid Amazon product URL
        Returns validation result with details
        """
        result = {
            'is_valid': False,
            'domain': None,
            'is_product_page': False,
            'url_type': None,
            'issues': []
        }
        
        if not url or not isinstance(url, str):
            result['issues'].append("URL is empty or invalid type")
            return result
            
        # Parse URL
        try:
            parsed = urlparse.urlparse(url.strip())
        except Exception as e:
            result['issues'].append(f"Failed to parse URL: {str(e)}")
            return result
            
        # Check if it's an Amazon domain
        domain = parsed.netloc.lower()
        # Remove www. prefix for matching
        domain = re.sub(r'^www\.', '', domain)
        
        if domain not in self.amazon_domains:
            result['issues'].append(f"Not an Amazon domain: {domain}")
            return result
            
        result['domain'] = domain
        
        # Check if it's a product page
        path = parsed.path.lower()
        url_type = None
        
        for pattern in self.product_patterns:
            if re.search(pattern, path):
                result['is_product_page'] = True
                url_type = pattern.strip('/')
                break
                
        if not result['is_product_page']:
            result['issues'].append(f"Not a product page URL: {path}")
            return result
            
        result['url_type'] = url_type
        result['is_valid'] = True
        
        return result
        
    def clean_url(self, url: str) -> str:
        """
        Clean Amazon URL by removing tracking parameters while preserving product path
        """
        try:
            parsed = urlparse.urlparse(url)
            
            # Parse query parameters
            query_params = urlparse.parse_qs(parsed.query)
            
            # Remove tracking parameters
            cleaned_params = {}
            for param, values in query_params.items():
                if param.lower() not in self.tracking_params:
                    cleaned_params[param] = values
                    
            # Rebuild query string
            cleaned_query = urlparse.urlencode(cleaned_params, doseq=True)
            
            # Rebuild URL
            cleaned_parsed = urlparse.ParseResult(
                scheme=parsed.scheme or 'https',
                netloc=parsed.netloc,
                path=parsed.path,
                params=parsed.params,
                query=cleaned_query,
                fragment=''  # Remove fragments
            )
            
            return urlparse.urlunparse(cleaned_parsed)
            
        except Exception as e:
            print(f"⚠️ URL cleaning failed: {e}, returning original URL")
            return url
            
    def convert_to_mobile(self, url: str) -> str:
        """Convert desktop Amazon URL to mobile version"""
        try:
            parsed = urlparse.urlparse(url)
            
            # Replace domain with mobile version
            mobile_domain = parsed.netloc.replace('amazon.', 'amazon.')  # Keep same domain
            
            # Convert path to mobile format
            path = parsed.path
            
            # Extract product ID from various formats
            product_id = None
            
            # Try to find product ID
            dp_match = re.search(r'/dp/([A-Z0-9]{10})', path)
            product_match = re.search(r'/(?:gp/)?product/([A-Z0-9]{10})', path)
            
            if dp_match:
                product_id = dp_match.group(1)
            elif product_match:
                product_id = product_match.group(1)
                
            if product_id:
                # Create mobile URL format
                mobile_path = f'/gp/aw/d/{product_id}'
                
                mobile_parsed = urlparse.ParseResult(
                    scheme='https',
                    netloc=mobile_domain,
                    path=mobile_path,
                    params='',
                    query='',
                    fragment=''
                )
                
                return urlparse.urlunparse(mobile_parsed)
                
        except Exception as e:
            print(f"⚠️ Mobile conversion failed: {e}")
            
        return url  # Return original if conversion fails
        
    def extract_search_terms(self, url: str) -> List[str]:
        """
        Extract search terms from Amazon URL for fallback search
        """
        search_terms = []
        
        try:
            # Try to get product title from URL structure
            parsed = urlparse.urlparse(url)
            path_segments = parsed.path.strip('/').split('/')
            
            # Look for descriptive segments (often between product ID and parameters)
            for segment in path_segments:
                # Decode URL encoding
                decoded = urlparse.unquote(segment)
                
                # Skip technical segments
                if decoded.lower() in ['dp', 'gp', 'product', 'aw', 'd']:
                    continue
                    
                # Skip product IDs (10 character alphanumeric)
                if re.match(r'^[A-Z0-9]{10}$', decoded):
                    continue
                    
                # Extract meaningful words
                words = re.findall(r'[a-zA-Z]{3,}', decoded)
                search_terms.extend(words)
                
            # Also check query parameters for keywords
            query_params = urlparse.parse_qs(parsed.query)
            if 'keywords' in query_params:
                keyword_terms = query_params['keywords'][0].split()
                search_terms.extend(keyword_terms)
                
            # Remove duplicates and short terms
            search_terms = list(set([term.lower() for term in search_terms if len(term) >= 3]))
            
        except Exception as e:
            print(f"⚠️ Search term extraction failed: {e}")
            
        return search_terms[:5]  # Limit to 5 most relevant terms
        
    def detect_category_from_url(self, url: str) -> Optional[str]:
        """
        Detect product category from URL structure
        """
        try:
            url_lower = url.lower()
            
            # Direct category indicators in URL
            category_patterns = {
                'books': ['/books/', '/book/', 'kindle-ebooks'],
                'electronics': ['/electronics/', '/computers/', '/phones/', '/tv-audio'],
                'health': ['/health/', '/sports/', '/beauty/', '/baby/'],
                'home': ['/home/', '/kitchen/', '/garden/', '/diy/'],
                'clothing': ['/clothing/', '/shoes/', '/fashion/', '/jewelry/'],
                'toys': ['/toys/', '/games/', '/baby-toddler/'],
                'automotive': ['/automotive/', '/car/', '/motorbike/']
            }
            
            for category, patterns in category_patterns.items():
                for pattern in patterns:
                    if pattern in url_lower:
                        return category
                        
        except Exception as e:
            print(f"⚠️ Category detection failed: {e}")
            
        return None
        
    def get_processing_strategies(self, url: str) -> List[Dict[str, str]]:
        """
        Get ordered list of URL processing strategies for the given URL
        """
        validation = self.validate_amazon_url(url)
        
        if not validation['is_valid']:
            return []
            
        strategies = []
        
        # Strategy 1: Direct URL (user's exact URL)
        strategies.append({
            'name': 'direct_url',
            'description': 'User provided URL exactly as given',
            'url': url,
            'priority': 1
        })
        
        # Strategy 2: Cleaned URL (remove tracking parameters)
        cleaned_url = self.clean_url(url)
        if cleaned_url != url:
            strategies.append({
                'name': 'cleaned_url', 
                'description': 'URL with tracking parameters removed',
                'url': cleaned_url,
                'priority': 2
            })
            
        # Strategy 3: Mobile version
        mobile_url = self.convert_to_mobile(url)
        if mobile_url != url:
            strategies.append({
                'name': 'mobile_url',
                'description': 'Mobile version of the URL',
                'url': mobile_url,
                'priority': 3
            })
            
        # Strategy 4: Search terms (for complete fallback)
        search_terms = self.extract_search_terms(url)
        if search_terms:
            strategies.append({
                'name': 'search_fallback',
                'description': 'Search using extracted terms',
                'url': f"https://{validation['domain']}/s?k={'+'.join(search_terms[:3])}",
                'priority': 4,
                'search_terms': search_terms
            })
            
        return strategies


def test_url_processor():
    """Test the URL processor with various Amazon URL formats"""
    processor = AmazonURLProcessor()
    
    test_urls = [
        # Protein powder (known working)
        "https://www.amazon.co.uk/Isolate-Protein-Fast-digesting-hydrolysate-Gourmet/dp/B01H3O2AMG/ref=sr_1_172?crid=3S6H6H4OUAWJY&dib=test&keywords=protein+powder",
        
        # Different URL formats
        "https://amazon.co.uk/dp/B01H3O2AMG",
        "https://www.amazon.com/gp/product/B01H3O2AMG",
        "https://amazon.co.uk/gp/aw/d/B01H3O2AMG",
        
        # Invalid URLs
        "https://google.com/search?q=amazon",
        "https://amazon.co.uk/best-sellers",
        "",
    ]
    
    print("🧪 Testing Amazon URL Processor")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\n📄 Testing: {url[:50]}{'...' if len(url) > 50 else ''}")
        
        # Validate
        validation = processor.validate_amazon_url(url)
        print(f"   Valid: {'✅' if validation['is_valid'] else '❌'}")
        if validation['issues']:
            print(f"   Issues: {', '.join(validation['issues'])}")
            
        if validation['is_valid']:
            # Get processing strategies
            strategies = processor.get_processing_strategies(url)
            print(f"   Strategies: {len(strategies)}")
            
            for i, strategy in enumerate(strategies, 1):
                print(f"      {i}. {strategy['name']}: {strategy['description']}")
                print(f"         URL: {strategy['url'][:60]}{'...' if len(strategy['url']) > 60 else ''}")
                
            # Category detection
            category = processor.detect_category_from_url(url)
            if category:
                print(f"   Category: {category}")


if __name__ == "__main__":
    test_url_processor()