#!/usr/bin/env python3
"""
🔗 INTEGRATED ENHANCED SCRAPER
=============================

Drop-in replacement for your existing scrape_amazon_product_page function.
This maintains 100% backward compatibility while adding enhanced accuracy.

Usage:
    # Replace this:
    from scrape_amazon_titles import scrape_amazon_product_page
    
    # With this:
    from integrated_scraper import scrape_amazon_product_page
    
    # Everything else works exactly the same!
    result = scrape_amazon_product_page(amazon_url, fallback=False)
"""

import os
import sys
import json
import logging
from typing import Dict, Optional, Any

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all the other functions from your original scraper
# This makes integrated_scraper a complete drop-in replacement
try:
    from .scrape_amazon_titles import (
        estimate_origin_country,
        resolve_brand_origin,
        save_brand_locations,
        haversine,
        origin_hubs,
        uk_hub
    )
except ImportError:
    # If relative import fails, try absolute
    from backend.scrapers.amazon.scrape_amazon_titles import (
        estimate_origin_country,
        resolve_brand_origin,
        save_brand_locations,
        haversine,
        origin_hubs,
        uk_hub
    )

def scrape_amazon_product_page(amazon_url: str, fallback: bool = False) -> Dict[str, Any]:
    """
    Enhanced scraper with fallback to your existing method
    
    Args:
        amazon_url: Amazon product URL
        fallback: If True, use mock data (your existing behavior)
        
    Returns:
        Product data dictionary in your existing format
    """
    logger.info(f"🧪 Scraping {amazon_url}, fallback mode: {fallback}")
    
    # Handle fallback mode first (your existing behavior)
    if fallback:
        logger.info("🟡 Using fallback mode, returning mock product.")
        return {
            "title": "Test Product (Fallback Mode)",
            "origin": "Unknown", 
            "weight_kg": 0.6,
            "dimensions_cm": [20, 10, 5],
            "material_type": "Plastic",
            "recyclability": "Low",
            "eco_score_ml": "F",
            "transport_mode": "Land",
            "carbon_kg": None
        }
    
    # Try REQUESTS scraper first (no ChromeDriver needed - most reliable)
    try:
        logger.info("📡 Attempting requests-based extraction...")
        from .requests_scraper import scrape_with_requests
        
        requests_result = scrape_with_requests(amazon_url)
        
        if requests_result and requests_result.get("title") != "Unknown Product":
            logger.info("✅ Requests extraction successful!")
            return requests_result
        else:
            logger.warning("⚠️ Requests extraction failed, trying master stealth")
            
    except Exception as e:
        logger.warning(f"⚠️ Requests scraper error: {e}, trying master stealth")
    
    # Try MASTER stealth scraper as backup (ultimate anti-bot detection)
    try:
        logger.info("🎓 Attempting MASTER stealth extraction...")
        from .master_stealth import master_scrape_amazon
        
        master_result = master_scrape_amazon(amazon_url)
        
        if master_result and master_result.get("title") != "Unknown Product":
            logger.info("✅ MASTER stealth extraction successful!")
            return master_result
        else:
            logger.warning("⚠️ Master stealth failed, trying standard stealth")
            
    except Exception as e:
        logger.warning(f"⚠️ Master stealth error: {e}, trying standard stealth")
    
    # Try stealth scraper as backup
    try:
        logger.info("🥷 Attempting stealth extraction...")
        from .stealth_scraper import scrape_with_stealth
        
        stealth_result = scrape_with_stealth(amazon_url)
        
        if stealth_result and stealth_result.get("title") != "Unknown Product":
            logger.info("✅ Stealth extraction successful!")
            return stealth_result
        else:
            logger.warning("⚠️ Stealth extraction failed, trying mobile stealth")
            
    except Exception as e:
        logger.warning(f"⚠️ Stealth scraper error: {e}, trying mobile stealth")
    
    # Try mobile stealth scraper (faster alternative)
    try:
        logger.info("📱 Attempting mobile stealth extraction...")
        from .mobile_stealth import scrape_mobile_stealth
        
        mobile_result = scrape_mobile_stealth(amazon_url)
        
        if mobile_result and mobile_result.get("title") != "Unknown Product":
            logger.info("✅ Mobile stealth extraction successful!")
            return mobile_result
        else:
            logger.warning("⚠️ Mobile stealth failed, trying enhanced scraper")
            
    except Exception as e:
        logger.warning(f"⚠️ Mobile stealth error: {e}, trying enhanced scraper")
    
    # Try enhanced scraper as backup
    try:
        logger.info("🚀 Attempting enhanced extraction...")
        from .enhanced_integration import enhanced_scrape_amazon_product_page
        
        enhanced_result = enhanced_scrape_amazon_product_page(amazon_url, fallback=False)
        
        # Check if enhanced scraper was successful
        if enhanced_result and enhanced_result.get("title") != "Extraction Failed":
            logger.info("✅ Enhanced extraction successful!")
            
            # Convert enhanced result to your existing format
            converted_result = convert_enhanced_to_legacy_format(enhanced_result)
            return converted_result
        else:
            logger.warning("⚠️ Enhanced extraction failed, falling back to original scraper")
            
    except Exception as e:
        logger.warning(f"⚠️ Enhanced scraper error: {e}, falling back to original scraper")
    
    # Fallback to your existing scraper
    try:
        logger.info("🔄 Using original scraper as fallback...")
        from .scrape_amazon_titles import scrape_amazon_product_page as original_scraper
        
        # Use your existing scraper
        original_result = original_scraper(amazon_url, fallback=False)
        logger.info("✅ Original scraper completed")
        return original_result
        
    except Exception as e:
        logger.error(f"❌ Both scrapers failed: {e}")
        
        # Return safe fallback data in your format
        return {
            "title": "Scraping Failed",
            "origin": "Unknown",
            "weight_kg": 1.0,
            "dimensions_cm": [10, 10, 10],
            "material_type": "Unknown",
            "recyclability": "Unknown", 
            "eco_score_ml": "C",
            "transport_mode": "Ship",
            "carbon_kg": None,
            "error": str(e)
        }

def convert_enhanced_to_legacy_format(enhanced_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert enhanced scraper result to your existing format
    
    Enhanced format -> Your existing format
    """
    try:
        # Your existing format keys
        legacy_result = {
            "title": enhanced_result.get("title", "Unknown"),
            "origin": enhanced_result.get("origin", "Unknown"),
            "weight_kg": float(enhanced_result.get("weight_kg", 1.0)),
            "dimensions_cm": enhanced_result.get("dimensions_cm", [10, 10, 10]),
            "material_type": enhanced_result.get("material_type", "Unknown"),
            "recyclability": enhanced_result.get("recyclability", "Unknown"),
            "eco_score_ml": enhanced_result.get("eco_score_ml", "C"),
            "transport_mode": enhanced_result.get("transport_mode", "Ship"),
            "carbon_kg": enhanced_result.get("carbon_kg")
        }
        
        # Add enhanced metadata (optional - your existing code will ignore these)
        legacy_result.update({
            "enhanced_quality_score": enhanced_result.get("data_quality_score", 0),
            "enhanced_confidence": enhanced_result.get("confidence", "Unknown"),
            "enhanced_data_sources": enhanced_result.get("data_sources", {}),
            "asin": enhanced_result.get("asin"),
            "brand": enhanced_result.get("brand")
        })
        
        logger.info(f"✅ Converted enhanced result - Quality: {legacy_result.get('enhanced_quality_score', 0)}%")
        return legacy_result
        
    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        # Return safe fallback
        return {
            "title": enhanced_result.get("title", "Conversion Failed"),
            "origin": "Unknown",
            "weight_kg": 1.0,
            "dimensions_cm": [10, 10, 10],
            "material_type": "Unknown",
            "recyclability": "Unknown",
            "eco_score_ml": "C", 
            "transport_mode": "Ship",
            "carbon_kg": None
        }

def test_integration():
    """Test the integrated scraper"""
    print("🧪 Testing Integrated Enhanced Scraper")
    print("=" * 50)
    
    # Test with fallback mode
    print("\n1. Testing fallback mode...")
    result1 = scrape_amazon_product_page("https://amazon.co.uk/test", fallback=True)
    print(f"   Result: {result1['title']}")
    
    # Test with a real URL (will fall back to original scraper due to bot detection)
    print("\n2. Testing with real URL (will demonstrate fallback)...")
    test_url = "https://www.amazon.co.uk/dp/B0BHBXNYT7"
    result2 = scrape_amazon_product_page(test_url, fallback=False)
    print(f"   Title: {result2['title']}")
    print(f"   Origin: {result2['origin']}")
    print(f"   Weight: {result2['weight_kg']} kg")
    print(f"   Material: {result2['material_type']}")
    
    # Show enhanced metadata if available
    if "enhanced_quality_score" in result2:
        print(f"   Enhanced Quality: {result2['enhanced_quality_score']}%")
        print(f"   Enhanced Confidence: {result2['enhanced_confidence']}")
    
    print("\n✅ Integration test completed!")
    print("\n🔗 HOW TO INTEGRATE:")
    print("1. Replace your import:")
    print("   # from scrape_amazon_titles import scrape_amazon_product_page")
    print("   from integrated_scraper import scrape_amazon_product_page")
    print("\n2. All your existing code works the same!")
    print("3. You automatically get enhanced accuracy when possible")
    print("4. Graceful fallback when enhanced scraper hits bot detection")

if __name__ == "__main__":
    test_integration()

# Export all functions for drop-in replacement
__all__ = [
    'scrape_amazon_product_page',
    'estimate_origin_country',
    'resolve_brand_origin',
    'save_brand_locations',
    'haversine',
    'origin_hubs',
    'uk_hub'
]