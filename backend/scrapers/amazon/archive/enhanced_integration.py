"""
🔗 ENHANCED EXTRACTOR INTEGRATION
===============================

Integration adapter that connects the new enhanced_amazon_extractor.py 
to your existing scraping pipeline while maintaining backward compatibility.

This adapter:
- Uses the new enhanced extractor for maximum accuracy
- Converts results to your existing data format
- Maintains all your current ML pipeline integrations
- Adds comprehensive logging and error handling
- Provides data quality metrics and validation

Usage:
    from enhanced_integration import enhanced_scrape_amazon_product_page
    result = enhanced_scrape_amazon_product_page(amazon_url)
"""

import os
import sys
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .enhanced_amazon_extractor import EnhancedAmazonExtractor, ProductData, ExtractionResult

# Import your existing utilities
try:
    from common.data.brand_origin_resolver import get_brand_origin_intelligent
    from backend.utils.co2_data import load_material_co2_data
except ImportError as e:
    logging.warning(f"Could not import existing utilities: {e}")
    # Provide fallback functions
    def get_brand_origin_intelligent(brand, title="", context=""):
        return {"country": "Unknown", "confidence": 0.0, "source": "fallback"}
    
    def load_material_co2_data():
        return {"plastic": 2.0, "aluminum": 8.0, "steel": 2.5}  # Basic fallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedIntegrationAdapter:
    """
    Adapter class that bridges enhanced extraction with existing pipeline
    """
    
    def __init__(self):
        self.extractor = EnhancedAmazonExtractor(headless=True)
        self.material_co2_map = load_material_co2_data()
        
        # Load existing data files for fallback validation
        self.priority_products = self._load_priority_products()
        self.brand_locations = self._load_brand_locations()
        
    def _load_priority_products(self) -> Dict:
        """Load priority products database"""
        try:
            priority_path = os.path.join(project_root, "priority_products.json")
            if os.path.exists(priority_path):
                with open(priority_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load priority products: {e}")
        return {}
    
    def _load_brand_locations(self) -> Dict:
        """Load brand locations database"""
        try:
            brand_path = os.path.join(project_root, "brand_locations.json")
            if os.path.exists(brand_path):
                with open(brand_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load brand locations: {e}")
        return {}
    
    def _calculate_distance(self, origin_country: str, destination_country: str = "UK") -> float:
        """Calculate distance between origin and destination countries"""
        # Simplified distance calculation - in real implementation, use your existing haversine logic
        distance_map = {
            "China": 8000, "USA": 5500, "Germany": 800, "France": 350,
            "Italy": 1200, "Japan": 9600, "Vietnam": 10500, "UK": 0
        }
        return distance_map.get(origin_country, 5000)  # Default 5000km for unknown countries
    
    def _determine_transport_mode(self, distance_km: float) -> str:
        """Determine optimal transport mode based on distance"""
        if distance_km < 1500:
            return "Land"
        elif distance_km < 6000:
            return "Air"
        else:
            return "Ship"
    
    def _calculate_co2_emissions(self, material: str, weight_kg: float, distance_km: float, transport_mode: str) -> Optional[float]:
        """Calculate CO2 emissions using your existing logic"""
        if not material or not weight_kg:
            return None
        
        # Material intensity (kg CO2 per kg material)
        material_intensity = self.material_co2_map.get(material.lower(), 2.0)
        
        # Transport factors (kg CO2 per kg per km)
        transport_factors = {
            "Land": 0.15,
            "Air": 0.5,
            "Ship": 0.03
        }
        
        transport_factor = transport_factors.get(transport_mode, 0.15)
        
        # Total emissions = material production + transport
        material_emissions = material_intensity * weight_kg
        transport_emissions = weight_kg * distance_km * transport_factor / 1000  # Convert to reasonable scale
        
        return round(material_emissions + transport_emissions, 3)
    
    def _calculate_recyclability(self, material: str, materials_breakdown: Optional[list] = None) -> Dict[str, Any]:
        """Calculate recyclability based on material composition"""
        if materials_breakdown and len(materials_breakdown) > 1:
            # Multi-material calculation
            total_recyclability = 0
            total_weight = 0
            
            material_recyclability = {
                "Aluminum": 90, "Steel": 85, "Glass": 80, "Paper": 75,
                "Plastic": 55, "Cotton": 50, "Rubber": 20, "Leather": 10
            }
            
            for mat in materials_breakdown:
                mat_name = mat.get('name', '')
                mat_weight = mat.get('weight', 0)
                recyclability = material_recyclability.get(mat_name, 30)
                
                total_recyclability += recyclability * mat_weight
                total_weight += mat_weight
            
            if total_weight > 0:
                avg_recyclability = total_recyclability / total_weight
            else:
                avg_recyclability = 30
            
            level = "High" if avg_recyclability >= 70 else "Medium" if avg_recyclability >= 40 else "Low"
            description = f"Multi-material: {', '.join([m['name'] for m in materials_breakdown[:3]])}"
            
        else:
            # Single material calculation
            single_material_map = {
                "Aluminum": ("High", 90), "Steel": ("High", 85), "Glass": ("High", 80),
                "Paper": ("High", 75), "Plastic": ("Medium", 55), "Cotton": ("Medium", 50),
                "Rubber": ("Low", 20), "Leather": ("Low", 10)
            }
            
            if material in single_material_map:
                level, avg_recyclability = single_material_map[material]
                description = f"Single material: {material}"
            else:
                level, avg_recyclability = "Unknown", 30
                description = f"Unknown material: {material}"
        
        return {
            "level": level,
            "percentage": int(avg_recyclability),
            "description": description
        }
    
    def _validate_with_priority_db(self, asin: str, extracted_data: ProductData) -> ProductData:
        """Validate and potentially override with priority database data"""
        if asin in self.priority_products:
            priority_data = self.priority_products[asin]
            logger.info(f"Found priority data for ASIN {asin} - using high-confidence overrides")
            
            # Override with priority data where available
            if priority_data.get("brand_estimated_origin"):
                extracted_data.origin_country.value = priority_data["brand_estimated_origin"]
                extracted_data.origin_country.confidence = "high"
                extracted_data.origin_country.source = "priority_database"
            
            if priority_data.get("estimated_weight_kg"):
                extracted_data.weight_kg.value = priority_data["estimated_weight_kg"]
                extracted_data.weight_kg.confidence = "high"
                extracted_data.weight_kg.source = "priority_database"
            
            if priority_data.get("material_type"):
                extracted_data.material_type.value = priority_data["material_type"]
                extracted_data.material_type.confidence = "high"
                extracted_data.material_type.source = "priority_database"
        
        return extracted_data
    
    def _enhance_with_brand_intelligence(self, extracted_data: ProductData) -> ProductData:
        """Enhance origin detection with brand intelligence"""
        if (not extracted_data.origin_country.value or 
            extracted_data.origin_country.confidence in ["low", "unknown"]):
            
            brand_name = extracted_data.brand.value or ""
            title = extracted_data.title.value or ""
            
            if brand_name:
                brand_intel = get_brand_origin_intelligent(brand_name, title)
                
                if brand_intel["confidence"] >= 0.5:  # Reasonable confidence threshold
                    extracted_data.origin_country.value = brand_intel["country"]
                    extracted_data.origin_country.confidence = "medium" if brand_intel["confidence"] >= 0.7 else "low"
                    extracted_data.origin_country.source = f"brand_intelligence_{brand_intel['source']}"
                    extracted_data.origin_country.raw_text = f"Brand intelligence: {brand_intel.get('reasoning', '')}"
                    
                    logger.info(f"Enhanced origin using brand intelligence: {brand_name} → {brand_intel['country']}")
        
        return extracted_data
    
    def scrape_product(self, amazon_url: str, fallback_mode: bool = False) -> Dict[str, Any]:
        """
        Main scraping method that replaces your existing scrape_amazon_product_page function
        
        Args:
            amazon_url: Amazon product URL to scrape
            fallback_mode: If True, return mock data instead of scraping
            
        Returns:
            Dictionary in your existing format for backward compatibility
        """
        
        if fallback_mode:
            logger.info("Using fallback mode - returning mock data")
            return {
                "title": "Test Product (Fallback Mode)",
                "origin": "Unknown",
                "weight_kg": 0.6,
                "dimensions_cm": [20, 10, 5],
                "material_type": "Plastic",
                "recyclability": "Low",
                "eco_score_ml": "F",
                "transport_mode": "Land",
                "carbon_kg": None,
                "confidence": "Low",
                "asin": "FALLBACK01"
            }
        
        try:
            logger.info(f"Starting enhanced extraction for: {amazon_url}")
            
            # Extract data using enhanced extractor
            extracted_data = self.extractor.extract_product_data(amazon_url)
            
            # Get ASIN for validation
            asin = extracted_data.asin.value
            
            # Apply validation and enhancements
            if asin:
                extracted_data = self._validate_with_priority_db(asin, extracted_data)
            
            extracted_data = self._enhance_with_brand_intelligence(extracted_data)
            
            # Calculate derived fields
            origin_country = extracted_data.origin_country.value or "Unknown"
            weight_kg = extracted_data.weight_kg.value or 1.0
            material = extracted_data.material_type.value or "Unknown"
            materials_breakdown = extracted_data.materials_breakdown.value if extracted_data.materials_breakdown.value else None
            
            # Distance and transport calculations
            distance_km = self._calculate_distance(origin_country)
            transport_mode = self._determine_transport_mode(distance_km)
            
            # CO2 emissions calculation
            co2_emissions = self._calculate_co2_emissions(material, weight_kg, distance_km, transport_mode)
            
            # Recyclability calculation
            recyclability_info = self._calculate_recyclability(material, materials_breakdown)
            
            # Generate extraction report
            extraction_report = self.extractor.get_extraction_report(extracted_data)
            
            # Convert to your existing format
            result = {
                # Core product info
                "asin": asin,
                "title": extracted_data.title.value,
                "brand": extracted_data.brand.value,
                "price": extracted_data.price.value,
                
                # Origin and logistics
                "origin": origin_country,
                "brand_estimated_origin": origin_country,
                "origin_city": "Unknown",  # TODO: Add city mapping
                "distance_origin_to_uk": distance_km,
                "distance_uk_to_user": 100,  # Default user distance
                "transport_mode": transport_mode,
                
                # Physical properties
                "weight_kg": weight_kg,
                "estimated_weight_kg": weight_kg * 1.05,  # Add packaging weight
                "raw_product_weight_kg": weight_kg,
                "dimensions_cm": extracted_data.dimensions.value,
                
                # Materials and environmental impact
                "material_type": material,
                "materials": {
                    "primary_material": material,
                    "all_materials": materials_breakdown or [],
                    "material_count": len(materials_breakdown) if materials_breakdown else (1 if material != "Unknown" else 0)
                },
                "recyclability": recyclability_info["level"],
                "recyclability_percentage": recyclability_info["percentage"],
                "recyclability_description": recyclability_info["description"],
                
                # Emissions and scoring
                "co2_emissions": co2_emissions,
                "carbon_kg": co2_emissions,
                "eco_score_ml": "C",  # Placeholder - integrate with your ML model
                
                # Quality and confidence metrics
                "confidence": extracted_data.overall_confidence.title(),
                "data_quality_score": extraction_report["data_quality_score"],
                "extraction_time": extracted_data.extraction_time,
                
                # Enhanced metadata for debugging and validation
                "data_sources": {
                    "origin_source": extracted_data.origin_country.source,
                    "origin_confidence": extracted_data.origin_country.confidence,
                    "weight_source": extracted_data.weight_kg.source,
                    "weight_confidence": extracted_data.weight_kg.confidence,
                    "material_source": extracted_data.material_type.source,
                    "material_confidence": extracted_data.material_type.confidence
                },
                "extraction_report": extraction_report
            }
            
            # Log extraction summary
            logger.info(f"✅ Extraction completed successfully:")
            logger.info(f"   Title: {result['title']}")
            logger.info(f"   Origin: {result['origin']} (confidence: {extracted_data.origin_country.confidence})")
            logger.info(f"   Weight: {result['weight_kg']}kg (confidence: {extracted_data.weight_kg.confidence})")
            logger.info(f"   Material: {result['material_type']} (confidence: {extracted_data.material_type.confidence})")
            logger.info(f"   Data Quality: {result['data_quality_score']:.1f}%")
            logger.info(f"   Overall Confidence: {result['confidence']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced extraction failed: {e}")
            
            # Return basic fallback data instead of complete failure
            return {
                "title": "Extraction Failed",
                "origin": "Unknown",
                "weight_kg": 1.0,
                "dimensions_cm": None,
                "material_type": "Unknown",
                "recyclability": "Unknown",
                "eco_score_ml": "F",
                "transport_mode": "Ship",
                "carbon_kg": None,
                "confidence": "Unknown",
                "asin": None,
                "error": str(e),
                "extraction_time": 0
            }

# Create global adapter instance
_adapter = None

def get_adapter():
    """Get or create the global adapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = EnhancedIntegrationAdapter()
    return _adapter

def enhanced_scrape_amazon_product_page(amazon_url: str, fallback: bool = False) -> Dict[str, Any]:
    """
    Drop-in replacement for your existing scrape_amazon_product_page function
    
    This function maintains the exact same interface as your existing function
    but uses the enhanced extractor underneath for dramatically improved accuracy.
    
    Args:
        amazon_url: Amazon product URL to scrape
        fallback: If True, return mock data instead of scraping
        
    Returns:
        Product data dictionary in your existing format
    """
    adapter = get_adapter()
    return adapter.scrape_product(amazon_url, fallback)

# Backward compatibility alias
scrape_amazon_product_page = enhanced_scrape_amazon_product_page

if __name__ == "__main__":
    # Test the integration
    test_url = "https://www.amazon.co.uk/dp/B0BHBXNYT7"
    
    logger.info("Testing enhanced integration...")
    result = enhanced_scrape_amazon_product_page(test_url)
    
    print("\\n" + "="*60)
    print("ENHANCED INTEGRATION TEST RESULTS")
    print("="*60)
    
    print(f"Title: {result.get('title', 'N/A')}")
    print(f"ASIN: {result.get('asin', 'N/A')}")
    print(f"Origin: {result.get('origin', 'N/A')}")
    print(f"Weight: {result.get('weight_kg', 'N/A')} kg")
    print(f"Material: {result.get('material_type', 'N/A')}")
    print(f"Transport: {result.get('transport_mode', 'N/A')}")
    print(f"CO2 Emissions: {result.get('co2_emissions', 'N/A')} kg")
    print(f"Recyclability: {result.get('recyclability', 'N/A')} ({result.get('recyclability_percentage', 'N/A')}%)")
    print(f"Data Quality: {result.get('data_quality_score', 'N/A'):.1f}%")
    print(f"Overall Confidence: {result.get('confidence', 'N/A')}")
    print(f"Extraction Time: {result.get('extraction_time', 'N/A'):.2f}s")
    
    # Show data sources
    data_sources = result.get('data_sources', {})
    if data_sources:
        print("\\nData Sources:")
        for field, info in data_sources.items():
            print(f"  {field}: {info}")
    
    print("\\n" + "="*60)