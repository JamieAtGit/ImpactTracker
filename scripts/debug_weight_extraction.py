#!/usr/bin/env python3
"""
Debug weight extraction for specific protein powder product
"""

import re

def extract_weight_from_title(title: str) -> float:
    """
    Universal weight extraction from Amazon product titles
    Works for ANY product type - no hardcoding
    """
    if not title:
        return 0.0
        
    import re
    title_lower = title.lower()
    
    # Comprehensive weight patterns (ordered by precision)
    weight_patterns = [
        # Most precise: explicit weight mentions
        (r'(\d+(?:\.\d+)?)\s*kg\b', 'kg', 1.0),
        (r'(\d+(?:\.\d+)?)\s*g\b(?!ram)', 'g', 0.001),  # Avoid "program"
        (r'(\d+(?:\.\d+)?)\s*lb\b', 'lb', 0.453592),
        (r'(\d+(?:\.\d+)?)\s*lbs\b', 'lb', 0.453592),
        (r'(\d+(?:\.\d+)?)\s*oz\b', 'oz', 0.0283495),
        
        # Common Amazon formats
        (r'(\d+(?:\.\d+)?)\s*kilograms?\b', 'kg', 1.0),
        (r'(\d+(?:\.\d+)?)\s*grams?\b', 'g', 0.001),
        (r'(\d+(?:\.\d+)?)\s*pounds?\b', 'lb', 0.453592),
        (r'(\d+(?:\.\d+)?)\s*ounces?\b', 'oz', 0.0283495),
    ]
    
    for pattern, unit, multiplier in weight_patterns:
        matches = re.findall(pattern, title_lower)
        if matches:
            try:
                weight_val = float(matches[0])
                weight_kg = weight_val * multiplier
                
                # Sanity check - reasonable product weights
                if 0.001 <= weight_kg <= 100:  # 1g to 100kg range
                    print(f"⚖️ Extracted weight: {weight_val}{unit} = {weight_kg:.3f}kg")
                    return weight_kg
            except (ValueError, IndexError):
                continue
    
    return 0.0

def extract_weight_enhanced(title: str):
    """Enhanced weight extraction with better pattern matching"""
    
    # Prioritize title extraction first (most accurate)
    title_weight_patterns = [
        r'(\d+(?:\.\d+)?)\s*g\b',  # 476g
        r'(\d+(?:\.\d+)?)\s*kg\b', # 2.5kg
        r'(\d+(?:\.\d+)?)\s*oz\b', # 16oz
        r'(\d+(?:\.\d+)?)\s*lb[s]?\b', # 2lbs
    ]
    
    # Check title first (highest priority)
    for pattern in title_weight_patterns:
        matches = re.findall(pattern, title, re.IGNORECASE)
        if matches:
            try:
                weight = float(matches[0])
                
                # Convert to kg based on unit
                if 'g' in pattern and 'kg' not in pattern:
                    weight = weight / 1000  # grams to kg
                    print(f"🔍 Found weight in title: {matches[0]}g = {weight}kg")
                elif 'oz' in pattern:
                    weight = weight * 0.0283495  # oz to kg
                    print(f"🔍 Found weight in title: {matches[0]}oz = {weight}kg")
                elif 'lb' in pattern:
                    weight = weight * 0.453592  # lbs to kg
                    print(f"🔍 Found weight in title: {matches[0]}lbs = {weight}kg")
                else:
                    print(f"🔍 Found weight in title: {matches[0]}kg")
                
                if 0.01 <= weight <= 100:  # Reasonable weight range
                    return weight
            except ValueError:
                continue
    
    print("⚠️ No weight found, using default 1.0kg")
    return 1.0  # Default

def debug_weight_extraction():
    """Debug weight extraction for the specific failing product"""
    
    # The actual title from the failing product
    title = "MUTANT ISO Surge | Whey Isolate Protein Powder | 25g Protein, Fast-digesting whey Protein Isolate &"
    
    print("🧪 DEBUGGING WEIGHT EXTRACTION")
    print("=" * 60)
    print(f"Title: {title}")
    print(f"Title length: {len(title)}")
    print(f"Title truncated?: {'YES - TRUNCATED!' if title.endswith('&') else 'No'}")
    print()
    
    print("🔍 Testing app.py extract_weight_from_title function:")
    weight1 = extract_weight_from_title(title)
    print(f"Result: {weight1}kg")
    print()
    
    print("🔍 Testing enhanced_scraper_fix.py extract_weight_enhanced function:")
    weight2 = extract_weight_enhanced(title)
    print(f"Result: {weight2}kg")
    print()
    
    print("🔍 Manual regex debugging:")
    title_lower = title.lower()
    
    # Test each pattern individually
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*kg\b', 'kg'),
        (r'(\d+(?:\.\d+)?)\s*g\b(?!ram)', 'g'),
        (r'(\d+(?:\.\d+)?)\s*lb\b', 'lb'),
        (r'(\d+(?:\.\d+)?)\s*lbs\b', 'lbs'),
        (r'(\d+(?:\.\d+)?)\s*oz\b', 'oz'),
        (r'(\d+(?:\.\d+)?)\s*kilograms?\b', 'kilograms'),
        (r'(\d+(?:\.\d+)?)\s*grams?\b', 'grams'),
        (r'(\d+(?:\.\d+)?)\s*pounds?\b', 'pounds'),
        (r'(\d+(?:\.\d+)?)\s*ounces?\b', 'ounces'),
    ]
    
    for pattern, unit in patterns:
        matches = re.findall(pattern, title_lower)
        print(f"  Pattern {pattern} ({unit}): {matches}")
    
    print()
    print("🔍 Looking for protein content (25g) vs container weight:")
    protein_matches = re.findall(r'(\d+)g?\s*protein', title_lower)
    print(f"  Protein content matches: {protein_matches}")
    
    print()
    print("🧠 ANALYSIS:")
    print("  - Title appears to be truncated (ends with '&')")
    print("  - Contains '25g Protein' but this is protein content, not container weight")
    print("  - No actual container weight visible in the truncated title")
    print("  - This explains why weight extraction returns 0.0kg or fallback values")
    
    print()
    print("🔧 RECOMMENDED FIXES:")
    print("  1. Fix title truncation in scraper")
    print("  2. Look for weight in product specifications section")
    print("  3. Use fallback weight estimation for protein powder category")
    print("  4. Check Amazon's detailed product information tabs")
    
if __name__ == "__main__":
    debug_weight_extraction()
