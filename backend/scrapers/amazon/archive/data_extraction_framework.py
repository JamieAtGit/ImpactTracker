"""
Amazon Product Data Extraction Framework
Separates data extraction, processing, and fallback logic
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum
import re
from bs4 import BeautifulSoup

class DataSource(Enum):
    """Track where each piece of data came from"""
    PAGE_PRODUCT_DETAILS = "page_product_details"
    PAGE_TECH_SPECS = "page_tech_specs" 
    PAGE_DESCRIPTION = "page_description"
    PAGE_BULLETS = "page_bullets"
    BRAND_DATABASE = "brand_database"
    CATEGORY_DEFAULT = "category_default"
    GENERIC_DEFAULT = "generic_default"
    CALCULATED = "calculated"

class ConfidenceLevel(Enum):
    """Data confidence levels"""
    HIGH = "high"      # Direct page extraction from structured fields
    MEDIUM = "medium"  # Inferred from page content or reliable database
    LOW = "low"        # Category defaults or weak patterns
    UNKNOWN = "unknown" # Generic fallbacks

@dataclass
class ExtractedValue:
    """Container for extracted data with metadata"""
    value: any
    source: DataSource
    confidence: ConfidenceLevel
    extraction_method: str
    raw_text: Optional[str] = None

class AmazonDataExtractor:
    """Structured data extraction from Amazon product pages"""
    
    def __init__(self, driver):
        self.driver = driver
        self.extraction_log = []
    
    def extract_all_data(self) -> Dict[str, ExtractedValue]:
        """Extract all product data with provenance tracking"""
        results = {}
        
        # 1. Extract from structured sections (highest priority)
        results.update(self._extract_from_product_details())
        results.update(self._extract_from_tech_specs())
        
        # 2. Extract from unstructured content (medium priority)  
        results.update(self._extract_from_description())
        results.update(self._extract_from_bullets())
        
        # 3. Log what we found
        self._log_extraction_results(results)
        
        return results
    
    def _extract_from_product_details(self) -> Dict[str, ExtractedValue]:
        """Extract from Amazon's Product Details section"""
        results = {}
        
        try:
            # Look for structured product details table
            details_tables = self.driver.find_elements(By.CSS_SELECTOR, 
                "table.a-keyvalue, #detailBullets_feature_div")
            
            for table in details_tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        # Origin extraction
                        if "country of origin" in label:
                            results["origin"] = ExtractedValue(
                                value=value,
                                source=DataSource.PAGE_PRODUCT_DETAILS,
                                confidence=ConfidenceLevel.HIGH,
                                extraction_method="product_details_table",
                                raw_text=f"{label}: {value}"
                            )
                        
                        # Weight extraction
                        elif any(kw in label for kw in ["weight", "item weight"]):
                            parsed_weight = self._parse_weight(value)
                            if parsed_weight:
                                results["weight"] = ExtractedValue(
                                    value=parsed_weight,
                                    source=DataSource.PAGE_PRODUCT_DETAILS,
                                    confidence=ConfidenceLevel.HIGH,
                                    extraction_method="product_details_weight",
                                    raw_text=f"{label}: {value}"
                                )
                        
                        # Material extraction
                        elif any(kw in label for kw in ["material", "sole material", "outer material"]):
                            normalized_material = self._normalize_material(value)
                            if normalized_material != "Unknown":
                                results["material"] = ExtractedValue(
                                    value=normalized_material,
                                    source=DataSource.PAGE_PRODUCT_DETAILS,
                                    confidence=ConfidenceLevel.HIGH,
                                    extraction_method="product_details_material",
                                    raw_text=f"{label}: {value}"
                                )
        
        except Exception as e:
            self.extraction_log.append(f"Product details extraction failed: {e}")
        
        return results
    
    def _extract_from_dimensions(self) -> Dict[str, ExtractedValue]:
        """Extract weight from Product Dimensions if available"""
        results = {}
        
        try:
            # Look for dimensions patterns that include weight
            page_text = self.driver.page_source.lower()
            
            # Enhanced patterns for dimensions + weight
            dimension_patterns = [
                r"product dimensions\s*[:\s]+[\d\s.x×*cm;,]+[;,]\s*([\d.]+)\s*g\b",
                r"package dimensions\s*[:\s]+[\d\s.x×*cm;,]+[;,]\s*([\d.]+)\s*g\b",
                r"[\d.]+\s*[x×]\s*[\d.]+\s*[x×]\s*[\d.]+\s*cm[;,\s]+([\d.]+)\s*g\b"
            ]
            
            for pattern in dimension_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    weight_grams = float(match.group(1))
                    weight_kg = weight_grams / 1000
                    
                    results["weight"] = ExtractedValue(
                        value=weight_kg,
                        source=DataSource.PAGE_PRODUCT_DETAILS,
                        confidence=ConfidenceLevel.HIGH,
                        extraction_method="dimensions_weight_extraction",
                        raw_text=match.group(0)
                    )
                    break
        
        except Exception as e:
            self.extraction_log.append(f"Dimensions weight extraction failed: {e}")
        
        return results
    
    def _parse_weight(self, weight_text: str) -> Optional[float]:
        """Parse weight from various formats"""
        if not weight_text:
            return None
        
        weight_text = weight_text.lower().strip()
        
        # Pattern for kg
        kg_match = re.search(r'([\d.]+)\s*kg', weight_text)
        if kg_match:
            return float(kg_match.group(1))
        
        # Pattern for grams  
        g_match = re.search(r'([\d.]+)\s*g\b', weight_text)
        if g_match:
            return float(g_match.group(1)) / 1000
        
        return None
    
    def _normalize_material(self, material_text: str) -> str:
        """Normalize material names with confidence"""
        if not material_text:
            return "Unknown"
        
        material_lower = material_text.lower().strip()
        
        # High-confidence materials
        material_map = {
            "rubber": "Rubber",
            "leather": "Leather", 
            "plastic": "Plastic",
            "metal": "Metal",
            "aluminum": "Aluminum",
            "steel": "Steel",
            "cotton": "Cotton",
            "polyester": "Polyester",
            "nylon": "Nylon",
            "mesh": "Mesh",
            "canvas": "Canvas"
        }
        
        for key, normalized in material_map.items():
            if key in material_lower:
                return normalized
        
        # Medium-confidence materials
        if "synthetic" in material_lower:
            return "Synthetic"
        elif "fabric" in material_lower:
            return "Fabric"
        elif "composite" in material_lower:
            return "Composite"
        elif "compound" in material_lower:
            return "Compound"
        
        # Return original if it's a reasonable material name
        if len(material_lower) > 2 and material_lower not in ["unknown", "other", "n/a"]:
            return material_text.title()
        
        return "Unknown"
    
    def _log_extraction_results(self, results: Dict[str, ExtractedValue]):
        """Log what data was extracted from where"""
        for field, extracted_value in results.items():
            self.extraction_log.append(
                f"✅ {field}: {extracted_value.value} "
                f"(source: {extracted_value.source.value}, "
                f"confidence: {extracted_value.confidence.value})"
            )

class DataProcessor:
    """Process extracted data and apply fallbacks intelligently"""
    
    def __init__(self, brand_database: dict, category_defaults: dict):
        self.brand_database = brand_database
        self.category_defaults = category_defaults
    
    def process_with_fallbacks(self, extracted_data: Dict[str, ExtractedValue], 
                             product_info: dict) -> Dict[str, ExtractedValue]:
        """Apply intelligent fallbacks only when necessary"""
        processed_data = extracted_data.copy()
        
        # Process each field with specific fallback logic
        processed_data.update(self._process_origin(extracted_data, product_info))
        processed_data.update(self._process_weight(extracted_data, product_info))
        processed_data.update(self._process_material(extracted_data, product_info))
        processed_data.update(self._process_recyclability(processed_data))
        
        return processed_data
    
    def _process_origin(self, extracted_data: Dict[str, ExtractedValue], 
                       product_info: dict) -> Dict[str, ExtractedValue]:
        """Process origin with smart fallbacks"""
        results = {}
        
        # If we have high-confidence page data, use it
        if "origin" in extracted_data and extracted_data["origin"].confidence == ConfidenceLevel.HIGH:
            return {}  # Keep the page data
        
        # If we have medium-confidence page data, keep it but note lower confidence
        if "origin" in extracted_data and extracted_data["origin"].confidence == ConfidenceLevel.MEDIUM:
            return {}  # Still prefer page data over database
        
        # Only use brand database if NO page data found
        if "origin" not in extracted_data:
            brand_name = product_info.get("brand", "").lower()
            if brand_name in self.brand_database:
                brand_origin = self.brand_database[brand_name]
                results["origin"] = ExtractedValue(
                    value=brand_origin["country"],
                    source=DataSource.BRAND_DATABASE,
                    confidence=ConfidenceLevel.MEDIUM,
                    extraction_method="brand_database_lookup",
                    raw_text=f"Brand: {brand_name} → {brand_origin['country']}"
                )
        
        return results
    
    def _process_weight(self, extracted_data: Dict[str, ExtractedValue], 
                       product_info: dict) -> Dict[str, ExtractedValue]:
        """Process weight with smart fallbacks"""
        results = {}
        
        # If we have page data, use it
        if "weight" in extracted_data:
            return {}  # Keep page data
        
        # Only use category defaults if NO weight found anywhere
        category = product_info.get("category", "").lower()
        if category in self.category_defaults:
            default_weight = self.category_defaults[category].get("weight")
            if default_weight:
                results["weight"] = ExtractedValue(
                    value=default_weight,
                    source=DataSource.CATEGORY_DEFAULT,
                    confidence=ConfidenceLevel.LOW,
                    extraction_method="category_default",
                    raw_text=f"Category {category} default: {default_weight}kg"
                )
        
        return results
    
    def _process_material(self, extracted_data: Dict[str, ExtractedValue], 
                         product_info: dict) -> Dict[str, ExtractedValue]:
        """Process material with smart fallbacks"""
        results = {}
        
        # If we have page data, use it
        if "material" in extracted_data and extracted_data["material"].value != "Unknown":
            return {}  # Keep page data
        
        # Don't guess materials - better to return Unknown than wrong data
        results["material"] = ExtractedValue(
            value="Unknown",
            source=DataSource.GENERIC_DEFAULT,
            confidence=ConfidenceLevel.UNKNOWN,
            extraction_method="no_material_found",
            raw_text="No material information found on page"
        )
        
        return results
    
    def _process_recyclability(self, processed_data: Dict[str, ExtractedValue]) -> Dict[str, ExtractedValue]:
        """Calculate recyclability based on material"""
        results = {}
        
        if "material" not in processed_data:
            results["recyclability"] = ExtractedValue(
                value="Unknown",
                source=DataSource.CALCULATED,
                confidence=ConfidenceLevel.UNKNOWN,
                extraction_method="no_material_for_recyclability"
            )
            return results
        
        material_value = processed_data["material"].value
        material_confidence = processed_data["material"].confidence
        
        # Recyclability mapping
        recyclability_map = {
            "Rubber": (20, "Low", "Limited recycling - mainly downcycled"),
            "Plastic": (55, "Medium", "Varies by plastic type"),
            "Aluminum": (90, "High", "Infinitely recyclable"),
            "Steel": (85, "High", "Highly recyclable metal"),
            "Cotton": (50, "Medium", "Textile recycling programs"),
            "Leather": (10, "Low", "Not traditionally recyclable"),
            "Unknown": (0, "Unknown", "Cannot assess without material ID")
        }
        
        percentage, level, description = recyclability_map.get(material_value, (0, "Unknown", "No data available"))
        
        # Reduce confidence if material confidence is low
        if material_confidence == ConfidenceLevel.LOW:
            recyclability_confidence = ConfidenceLevel.LOW
        elif material_confidence == ConfidenceLevel.UNKNOWN:
            recyclability_confidence = ConfidenceLevel.UNKNOWN
        else:
            recyclability_confidence = ConfidenceLevel.MEDIUM
        
        results["recyclability"] = ExtractedValue(
            value=level,
            source=DataSource.CALCULATED,
            confidence=recyclability_confidence,
            extraction_method="material_based_calculation",
            raw_text=f"{material_value} → {percentage}% recyclable"
        )
        
        results["recyclability_percentage"] = ExtractedValue(
            value=percentage,
            source=DataSource.CALCULATED,
            confidence=recyclability_confidence,
            extraction_method="material_based_calculation"
        )
        
        results["recyclability_description"] = ExtractedValue(
            value=description,
            source=DataSource.CALCULATED,
            confidence=recyclability_confidence,
            extraction_method="material_based_calculation"
        )
        
        return results

# Example usage in main scraper:
def scrape_product_with_framework(driver, product_url):
    """Main scraper function using the new framework"""
    
    # 1. Extract data with provenance
    extractor = AmazonDataExtractor(driver)
    extracted_data = extractor.extract_all_data()
    
    # 2. Process with intelligent fallbacks
    processor = DataProcessor(brand_database={}, category_defaults={})
    final_data = processor.process_with_fallbacks(extracted_data, {"brand": "nike"})
    
    # 3. Log the extraction process
    print("=== EXTRACTION LOG ===")
    for log_entry in extractor.extraction_log:
        print(log_entry)
    
    # 4. Return structured result
    return final_data