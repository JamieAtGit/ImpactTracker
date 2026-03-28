#!/usr/bin/env python3
"""
🚀 UNIFIED PRODUCTION SCRAPER INTERFACE
======================================

Professional-grade scraper with strategy pattern, error handling,
and guaranteed results. This replaces all 8+ chaotic scrapers with
a single, reliable, maintainable interface.

Architecture:
- Strategy Pattern: Multiple scraping strategies with fallback chain
- Error Handling: Comprehensive exception handling with context
- Data Validation: Quality scoring and confidence assessment  
- Logging: Structured logging for debugging and monitoring
- Caching: Built-in result caching to avoid redundant requests

Usage:
    scraper = UnifiedProductScraper()
    result = scraper.scrape("https://amazon.co.uk/dp/B123")
    print(f"Quality: {result.quality_score}%")
"""

import logging
import time
import hashlib
import sys
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import our working scraper strategies
try:
    from .requests_scraper import scrape_with_requests
except ImportError:
    from requests_scraper import scrape_with_requests

# Import professional error handling
try:
    from backend.core.exceptions import (
        ScrapingException,
        DataValidationException,
        ErrorSeverity,
        ErrorCategory,
        error_handler
    )
except ImportError:
    try:
        from core.exceptions import (
            ScrapingException,
            DataValidationException,
            ErrorSeverity,
            ErrorCategory,
            error_handler
        )
    except ImportError:
        # Local fallback so scraper can run when shared exception package is absent.
        class ErrorSeverity(str, Enum):
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"
            CRITICAL = "critical"

        class ErrorCategory(str, Enum):
            NETWORK = "network"
            PARSING = "parsing"
            SYSTEM = "system"
            VALIDATION = "validation"

        class ScrapingException(Exception):
            def __init__(self, message, url=None, strategy=None, severity=None, category=None, context=None):
                super().__init__(message)
                self.url = url
                self.strategy = strategy
                self.severity = severity
                self.category = category
                self.context = context or {}

        class DataValidationException(ScrapingException):
            pass

        def error_handler(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingStrategy(str, Enum):
    """Enumeration of available scraping strategies"""
    REQUESTS = "requests"
    SELENIUM = "selenium"
    MOBILE = "mobile"
    FALLBACK = "fallback"

class ConfidenceLevel(str, Enum):
    """Data confidence levels"""
    HIGH = "high"      # 80-100% - Technical specs extracted
    MEDIUM = "medium"  # 60-79%  - Partial extraction + brand mapping  
    LOW = "low"        # 40-59%  - Mostly fallback/estimated data
    MINIMAL = "minimal" # 0-39%   - Intelligent URL analysis only

@dataclass
class ScrapingResult:
    """Standardized result object with comprehensive metadata"""
    
    # Core product data
    title: str
    origin: str
    weight_kg: float
    dimensions_cm: List[float]
    material_type: str
    recyclability: str
    
    # Enhanced metadata
    brand: str
    asin: str
    price: Optional[str] = None
    
    # Quality assessment
    quality_score: int = 0  # 0-100 overall confidence
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    
    # Extraction metadata
    strategy_used: ScrapingStrategy = ScrapingStrategy.FALLBACK
    extraction_time_ms: int = 0
    data_sources: Dict[str, str] = None
    
    # Error tracking
    errors_encountered: List[str] = None
    warnings: List[str] = None

    # Multi-material data from spec table (passed through to app_production)
    amazon_materials_extracted: Optional[Dict] = None

    # Product image URL (used by AI visual material analysis)
    image_url: Optional[str] = None

    # Additional gallery images for multi-angle AI analysis
    gallery_images: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.data_sources is None:
            self.data_sources = {}
        if self.errors_encountered is None:
            self.errors_encountered = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return asdict(self)
    
    def is_high_quality(self) -> bool:
        """Check if result meets high quality standards"""
        return self.quality_score >= 80 and self.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]

# ScrapingException now imported from core.exceptions
# This provides professional error handling with context, logging, and monitoring

class ScrapingStrategyBase(ABC):
    """Abstract base class for all scraping strategies"""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this strategy can handle the given URL"""
        pass
    
    @abstractmethod
    def scrape(self, url: str) -> ScrapingResult:
        """Scrape the URL and return standardized result"""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> ScrapingStrategy:
        """Return the strategy identifier"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """Return priority (lower = higher priority, 0 = highest)"""
        pass

class RequestsStrategy(ScrapingStrategyBase):
    """HTTP requests-based scraping strategy (fastest, most reliable)"""
    
    def can_handle(self, url: str) -> bool:
        """Can handle any Amazon URL"""
        return "amazon." in url.lower()
    
    def scrape(self, url: str) -> ScrapingResult:
        """Scrape using requests method"""
        start_time = time.time()
        
        try:
            logger.info(f"🌐 Attempting requests strategy for {url}")
            raw_result = scrape_with_requests(url)
            
            if raw_result and raw_result.get("title") != "Unknown Product":
                # Convert to standardized format
                result = ScrapingResult(
                    title=raw_result.get("title", "Unknown"),
                    origin=raw_result.get("origin", "Unknown"),
                    weight_kg=float(raw_result.get("weight_kg", 1.0)),
                    dimensions_cm=raw_result.get("dimensions_cm", [20, 15, 10]),
                    material_type=raw_result.get("material_type", "Unknown"),
                    recyclability=raw_result.get("recyclability", "Medium"),
                    brand=raw_result.get("brand", "Unknown"),
                    asin=raw_result.get("asin", "Unknown"),
                    
                    # Quality assessment
                    quality_score=self._calculate_quality_score(raw_result),
                    confidence_level=self._determine_confidence_level(raw_result),
                    strategy_used=ScrapingStrategy.REQUESTS,
                    extraction_time_ms=int((time.time() - start_time) * 1000),
                    
                    data_sources={
                        "title": "amazon_page_title",
                        "origin": raw_result.get("origin_source", "brand_mapping" if raw_result.get("origin") != "Unknown" else "unknown"),
                        "origin_confidence": raw_result.get("origin_confidence", "unknown"),
                        "weight": "technical_details" if raw_result.get("weight_kg", 1.0) != 1.0 else "default"
                    },
                    amazon_materials_extracted=raw_result.get("amazon_materials_extracted"),
                    image_url=raw_result.get("image_url"),
                    gallery_images=raw_result.get("gallery_images"),
                )
                
                logger.info(f"✅ Requests strategy successful - Quality: {result.quality_score}%")
                return result
            else:
                raise ScrapingException(
                    "Requests strategy returned no data", 
                    url=url,
                    strategy="requests",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.PARSING
                )
                
        except ScrapingException:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            logger.error(f"❌ Requests strategy failed: {e}")
            raise ScrapingException(
                f"Requests strategy failed: {e}", 
                url=url,
                strategy="requests",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.NETWORK
            )
    
    def _calculate_quality_score(self, raw_result: Dict) -> int:
        """Calculate quality score based on data completeness"""
        score = 0
        
        # Title quality (30 points)
        title = raw_result.get("title", "")
        if title and title != "Unknown" and len(title) > 20:
            score += 30
        elif title and title != "Unknown":
            score += 15
        
        # Origin quality (25 points)  
        origin = raw_result.get("origin", "")
        if origin and origin != "Unknown":
            score += 25
            
        # Weight quality (25 points)
        weight = raw_result.get("weight_kg", 1.0)
        if weight != 1.0:  # Not default weight
            score += 25
        
        # Brand quality (10 points)
        brand = raw_result.get("brand", "")
        if brand and brand != "Unknown":
            score += 10
            
        # Material quality (10 points)
        material = raw_result.get("material_type", "")
        if material and material != "Unknown":
            score += 10
            
        return min(score, 100)
    
    def _determine_confidence_level(self, raw_result: Dict) -> ConfidenceLevel:
        """Determine confidence level based on quality score"""
        score = self._calculate_quality_score(raw_result)
        
        if score >= 80:
            return ConfidenceLevel.HIGH
        elif score >= 60:
            return ConfidenceLevel.MEDIUM
        elif score >= 40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.MINIMAL
    
    @property
    def strategy_name(self) -> ScrapingStrategy:
        return ScrapingStrategy.REQUESTS
    
    @property
    def priority(self) -> int:
        return 0  # Highest priority (fastest, most reliable)

class FallbackStrategy(ScrapingStrategyBase):
    """Intelligent fallback when all other strategies fail"""
    
    def can_handle(self, url: str) -> bool:
        """Can handle any URL as last resort"""
        return True
    
    def scrape(self, url: str) -> ScrapingResult:
        """Generate intelligent fallback based on URL analysis"""
        start_time = time.time()
        
        logger.info(f"🧠 Using intelligent fallback for {url}")
        
        # Extract ASIN from URL
        import re
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        asin = asin_match.group(1) if asin_match else "Unknown"
        
        # Intelligent URL analysis
        url_lower = url.lower()
        
        if 'protein' in url_lower:
            title = "Protein Supplement"
            material = "Plastic"
            weight = 2.0
            origin = "UK"
        elif any(term in url_lower for term in ['electronic', 'phone', 'laptop']):
            title = "Electronic Device"  
            material = "Mixed"
            weight = 0.5
            origin = "China"
        elif 'book' in url_lower:
            title = "Book"
            material = "Paper"
            weight = 0.3
            origin = "UK"
        else:
            title = "Consumer Product"
            material = "Unknown"
            weight = 1.0
            origin = "UK"
        
        result = ScrapingResult(
            title=title,
            origin=origin,
            weight_kg=weight,
            dimensions_cm=[15, 10, 8],
            material_type=material,
            recyclability="Medium",
            brand="Unknown",
            asin=asin,
            
            quality_score=35,  # Low but consistent
            confidence_level=ConfidenceLevel.MINIMAL,
            strategy_used=ScrapingStrategy.FALLBACK,
            extraction_time_ms=int((time.time() - start_time) * 1000),
            
            data_sources={
                "title": "url_analysis",
                "origin": "default_uk",
                "weight": "category_estimate"
            },
            
            warnings=["Using fallback strategy - actual product data unavailable"]
        )
        
        logger.info(f"🔄 Fallback strategy completed - Quality: {result.quality_score}%")
        return result
    
    @property
    def strategy_name(self) -> ScrapingStrategy:
        return ScrapingStrategy.FALLBACK
    
    @property  
    def priority(self) -> int:
        return 999  # Lowest priority (last resort)

class UnifiedProductScraper:
    """
    Professional unified scraper with strategy pattern and comprehensive error handling.
    
    Features:
    - Multiple fallback strategies
    - Quality assessment and confidence scoring
    - Comprehensive error handling with context
    - Performance monitoring
    - Result caching
    - Structured logging
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize unified scraper
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.strategies: List[ScrapingStrategyBase] = [
            RequestsStrategy(),
            # SeleniumStrategy(),  # TODO: Add when Selenium dependencies fixed
            # MobileStrategy(),    # TODO: Add mobile strategy
            FallbackStrategy()   # Always last
        ]
        
        # Sort strategies by priority
        self.strategies.sort(key=lambda s: s.priority)
        
        self.cache: Dict[str, Tuple[ScrapingResult, float]] = {}
        self.cache_ttl = cache_ttl
        
        logger.info(f"🚀 Unified scraper initialized with {len(self.strategies)} strategies")
    
    def scrape(self, url: str, force_refresh: bool = False) -> ScrapingResult:
        """
        Scrape product data with guaranteed result
        
        Args:
            url: Amazon product URL
            force_refresh: Skip cache and force fresh scrape
            
        Returns:
            ScrapingResult with comprehensive metadata
            
        Raises:
            ScrapingException: When all strategies fail (extremely rare)
        """
        # Input validation
        if not url or not isinstance(url, str):
            raise DataValidationException(
                "Invalid URL provided",
                field_name="url",
                field_value=url,
                validation_rule="non_empty_string"
            )
        
        # Check cache first
        if not force_refresh:
            cached_result = self._get_cached_result(url)
            if cached_result:
                logger.info(f"📋 Cache hit for {url}")
                return cached_result
        
        logger.info(f"🔍 Starting scrape for {url}")
        start_time = time.time()
        
        # Try each strategy in priority order
        last_error = None
        
        for strategy in self.strategies:
            if not strategy.can_handle(url):
                continue
                
            try:
                logger.info(f"🎯 Trying {strategy.strategy_name} strategy")
                result = strategy.scrape(url)
                
                # Cache successful result
                self._cache_result(url, result)
                
                # Add overall performance metrics
                total_time = int((time.time() - start_time) * 1000)
                logger.info(f"✅ Scraping completed in {total_time}ms using {strategy.strategy_name}")
                
                return result
                
            except ScrapingException as e:
                logger.warning(f"⚠️ Strategy {strategy.strategy_name} failed: {e}")
                last_error = e
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error in {strategy.strategy_name}: {e}")
                last_error = ScrapingException(
                    f"Unexpected error: {e}",
                    url=url,
                    strategy=str(strategy.strategy_name),
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM
                )
                continue
        
        # If we reach here, all strategies failed (should never happen due to fallback)
        error_msg = f"All scraping strategies failed for {url}"
        logger.critical(error_msg)
        raise ScrapingException(
            error_msg, 
            url=url,
            strategy="all_strategies",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            context={"last_error": str(last_error)}
        )
    
    def _get_cached_result(self, url: str) -> Optional[ScrapingResult]:
        """Get cached result if still valid"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        if url_hash in self.cache:
            result, timestamp = self.cache[url_hash]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                # Cache expired
                del self.cache[url_hash]
        
        return None
    
    def _cache_result(self, url: str, result: ScrapingResult) -> None:
        """Cache successful result"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        self.cache[url_hash] = (result, time.time())
        logger.debug(f"💾 Cached result for {url}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        now = time.time()
        valid_entries = sum(1 for _, timestamp in self.cache.values() if now - timestamp < self.cache_ttl)
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl_hours": self.cache_ttl / 3600
        }
    
    def clear_cache(self) -> int:
        """Clear all cached results"""
        cleared = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ Cleared {cleared} cached entries")
        return cleared

# Convenience functions for backward compatibility
def scrape_amazon_product_page(amazon_url: str, fallback: bool = False) -> Dict[str, Any]:
    """
    Drop-in replacement for existing scrape_amazon_product_page function
    
    Args:
        amazon_url: Amazon product URL
        fallback: If True, force fallback strategy
        
    Returns:
        Product data dictionary in legacy format
    """
    scraper = UnifiedProductScraper()
    
    if fallback:
        # Force fallback strategy
        result = FallbackStrategy().scrape(amazon_url)
    else:
        result = scraper.scrape(amazon_url)
    
    # Convert to legacy format
    return {
        "title": result.title,
        "origin": result.origin,
        "country_of_origin": result.origin,
        "origin_source": (result.data_sources or {}).get("origin", "unknown"),
        "origin_confidence": (result.data_sources or {}).get("origin_confidence", str(result.confidence_level).split('.')[-1].lower() if result.confidence_level else "unknown"),
        "weight_kg": result.weight_kg,
        "dimensions_cm": result.dimensions_cm,
        "material_type": result.material_type,
        "recyclability": result.recyclability,
        "eco_score_ml": "C",  # Default for compatibility
        "transport_mode": "Ship",  # Default for compatibility
        "carbon_kg": None,  # Calculated elsewhere
        
        # Enhanced metadata (optional - existing code will ignore)
        "brand": result.brand,
        "asin": result.asin,
        "quality_score": result.quality_score,
        "confidence_level": result.confidence_level,
        "strategy_used": result.strategy_used,
        "extraction_time_ms": result.extraction_time_ms,
        # Multi-material spec table data for detect_materials pipeline
        "amazon_materials_extracted": result.amazon_materials_extracted,
        # Product image for AI visual analysis
        "image_url": result.image_url,
        "gallery_images": result.gallery_images or [],
    }

if __name__ == "__main__":
    # Test the unified scraper
    scraper = UnifiedProductScraper()
    
    test_url = "https://www.amazon.co.uk/Grenade-Protein-Powder-Serving-Servings/dp/B0CKFK6716/ref=sr_1_51"
    result = scraper.scrape(test_url)
    
    print("🚀 UNIFIED SCRAPER TEST RESULTS")
    print("=" * 50)
    print(f"Title: {result.title}")
    print(f"Origin: {result.origin}")
    print(f"Weight: {result.weight_kg} kg")
    print(f"Quality Score: {result.quality_score}%")
    print(f"Confidence: {result.confidence_level}")
    print(f"Strategy: {result.strategy_used}")
    print(f"Time: {result.extraction_time_ms}ms")
    print(f"High Quality: {result.is_high_quality()}")
    
    # Test cache
    print(f"\nCache Stats: {scraper.get_cache_stats()}")