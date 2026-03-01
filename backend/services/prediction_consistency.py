from typing import Dict, Any
import re
from urllib.parse import urlparse


def normalize_brand_for_lookup(brand: str) -> str:
    cleaned = re.sub(r'^(visit the|brand:|by)\s+', '', str(brand or ''), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+(store|shop|official)$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def apply_material_title_consistency(product: Dict[str, Any]) -> str:
    title_text = str(product.get('title', '') or '').lower()
    current_material = str(product.get('material_type') or product.get('material') or '').strip()

    title_has_wood_signal = any(token in title_text for token in [
        'wooden', 'wood spoon', 'wood cutlery', 'bamboo', 'birchwood'
    ])
    title_has_anti_plastic_signal = any(token in title_text for token in [
        'plastic free', 'plastic-free', 'no plastic'
    ])
    title_has_wood_utensil_signal = any(token in title_text for token in [
        'spoon', 'fork', 'knife', 'cutlery', 'icecream', 'dessert spoon'
    ])

    if (
        current_material.lower() == 'plastic'
        and title_has_wood_signal
        and (title_has_anti_plastic_signal or title_has_wood_utensil_signal)
    ):
        product['material_type'] = 'Wood'
        if isinstance(product.get('materials'), dict):
            product['materials']['primary_material'] = 'Wood'
        return 'Wood'

    return product.get('material_type') or current_material


def normalize_amazon_url(url: str) -> str:
    value = str(url or '').strip()
    if not value:
        return value

    lower_value = value.lower()
    if lower_value.startswith(('http://', 'https://')):
        normalized = value
    elif lower_value.startswith('www.amazon.') or lower_value.startswith('amazon.'):
        normalized = f"https://{value}"
    else:
        return value

    parsed = urlparse(normalized)
    domain = parsed.netloc.lower()
    if not domain or 'amazon.' not in domain:
        return normalized

    asin_match = re.search(r'/(?:dp|gp/product|product)/([A-Z0-9]{10})(?:[/?]|$)', parsed.path, flags=re.IGNORECASE)
    if not asin_match:
        asin_match = re.search(r'([A-Z0-9]{10})', normalized, flags=re.IGNORECASE)

    if asin_match:
        asin = asin_match.group(1).upper()
        return f"https://{domain}/dp/{asin}"

    return normalized


def extract_asin_from_amazon_url(url: str) -> str:
    value = str(url or '').strip()
    if not value:
        return ""
    match = re.search(r'([A-Z0-9]{10})', value, flags=re.IGNORECASE)
    return match.group(1).upper() if match else ""
