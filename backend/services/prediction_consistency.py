from typing import Dict, Any
import re
from urllib.parse import urlparse


PLASTIC_SUBTYPE_RULES = [
    ("Polypropylene", [r"\bpolypropylene\b", r"\bpoly\s*propylene\b", r"\bpp\b", r"\bfood\s*grade\s*pp\b", r"\b#5\s*plastic\b"]),
    ("Polyethylene", [r"\bpolyethylene\b", r"\bpoly\s*ethylene\b", r"\bhdpe\b", r"\bldpe\b", r"\b#2\s*plastic\b", r"\b#4\s*plastic\b", r"\bpe\b"]),
    ("PET", [r"\bpolyethylene\s*terephthalate\b", r"\bpet\b", r"\b#1\s*plastic\b"]),
    ("PETG", [r"\bpetg\b", r"\bpolyethylene\s*terephthalate\s*glycol\b", r"\bcopolyester\b"]),
    ("ABS+PC", [r"\babs\+pc\b", r"\bpc\+abs\b", r"\bpolycarbonate\s*abs\b"]),
    ("FR-ABS", [r"\bfr[-\s]*abs\b", r"\bflame\s*retardant\s*abs\b"]),
    ("ABS", [r"\babs\s*plastic\b", r"\bacrylonitrile\s*butadiene\s*styrene\b", r"\babs\b"]),
    ("Polycarbonate", [r"\bpolycarbonate\b", r"\bpc\s*plastic\b", r"\bpc\b"]),
    ("PVC", [r"\bpvc\b", r"\bpolyvinyl\s*chloride\b", r"\bvinyl\b"]),
    ("Polystyrene", [r"\bpolystyrene\b", r"\bps\s*plastic\b", r"\b#6\s*plastic\b"]),
    ("Nylon", [r"\bnylon\b", r"\bpolyamide\b", r"\bpa6\b", r"\bpa66\b", r"\bnylon\s*6\b", r"\bnylon\s*66\b"]),
    ("Acrylic", [r"\bacrylic\b", r"\bpmma\b"]),
    ("Silicone", [r"\bsilicone\b", r"\bfood\s*grade\s*silicone\b"]),
    ("Melamine", [r"\bmelamine\b"]),
    ("SAN", [r"\bstyrene\s*acrylonitrile\b", r"\bsan\b"]),
    ("POM", [r"\bpolyoxymethylene\b", r"\bpom\b", r"\bacetal\b", r"\bdelrin\b"]),
    ("PBT", [r"\bpolybutylene\s*terephthalate\b", r"\bpbt\b"]),
    ("TPU", [r"\bthermoplastic\s*polyurethane\b", r"\btpu\b"]),
    ("TPE", [r"\bthermoplastic\s*elastomer\b", r"\btpe\b"]),
    ("EVA", [r"\bethylene\s*vinyl\s*acetate\b", r"\beva\b"]),
    ("PTFE", [r"\bpolytetrafluoroethylene\b", r"\bptfe\b", r"\bteflon\b"]),
    ("PEEK", [r"\bpolyether\s*ether\s*ketone\b", r"\bpeek\b"]),
    ("UHMWPE", [r"\bultra\s*high\s*molecular\s*weight\s*polyethylene\b", r"\buhmwpe\b"]),
    ("Polyester", [r"\bpolyester\b", r"\bpet\s*fiber\b", r"\bpolyester\s*fibre\b", r"\bpolyester\s*fiber\b"]),
    ("PLA", [r"\bpla\b", r"\bpolylactic\s*acid\b", r"\bcompostable\s*plastic\b", r"\bbioplastic\b"]),
    ("PBS", [r"\bpolybutylene\s*succinate\b", r"\bpbs\b"]),
    ("PHA", [r"\bpolyhydroxyalkanoate\b", r"\bpha\b"]),
    ("PHB", [r"\bpolyhydroxybutyrate\b", r"\bphb\b"]),
    ("Bio-PE", [r"\bbio\s*pe\b", r"\bbio\s*polyethylene\b"]),
]


def _collect_material_evidence_text(product: Dict[str, Any]) -> str:
    evidence_parts = [
        str(product.get('title', '') or ''),
        str(product.get('description', '') or ''),
        str(product.get('category', '') or ''),
        str(product.get('material_type', '') or ''),
        str(product.get('material', '') or ''),
        str(product.get('materials', '') or ''),
    ]

    for key, value in product.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in ['material', 'feature', 'detail', 'spec', 'bullet']):
            evidence_parts.append(str(value or ''))

    return " ".join(evidence_parts).lower()


def _infer_plastic_subtype(evidence_text: str) -> str:
    for subtype, patterns in PLASTIC_SUBTYPE_RULES:
        if any(re.search(pattern, evidence_text, flags=re.IGNORECASE) for pattern in patterns):
            return subtype
    return ""


def normalize_brand_for_lookup(brand: str) -> str:
    cleaned = re.sub(r'^(visit the|brand:|by)\s+', '', str(brand or ''), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+(store|shop|official)$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def apply_material_title_consistency(product: Dict[str, Any]) -> str:
    combined_text = _collect_material_evidence_text(product)
    current_material = str(product.get('material_type') or product.get('material') or '').strip()

    title_has_wood_signal = any(token in combined_text for token in [
        'wooden', 'wood spoon', 'wood cutlery', 'bamboo', 'birchwood'
    ])
    title_has_anti_plastic_signal = any(token in combined_text for token in [
        'plastic free', 'plastic-free', 'no plastic'
    ])
    title_has_wood_utensil_signal = any(token in combined_text for token in [
        'spoon', 'fork', 'knife', 'cutlery', 'icecream', 'dessert spoon'
    ])

    has_polypropylene_signal = any(token in combined_text for token in [
        'polypropylene', ' pp ', 'pp plastic', 'food grade pp'
    ])
    has_bpa_free_signal = any(token in combined_text for token in [
        'bpa free', 'bpa-free', 'without bpa'
    ])
    has_reusable_cutlery_signal = any(token in combined_text for token in [
        'reusable spoon', 'reusable teaspoons', 'reusable cutlery', 'plastic teaspoons', 'teaspoon'
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

    if current_material.lower() == 'plastic' and (has_polypropylene_signal or (has_bpa_free_signal and has_reusable_cutlery_signal)):
        product['material_type'] = 'Polypropylene'
        if isinstance(product.get('materials'), dict):
            product['materials']['primary_material'] = 'Polypropylene'
        return 'Polypropylene'

    if current_material.lower() == 'plastic':
        inferred_subtype = _infer_plastic_subtype(combined_text)
        if inferred_subtype:
            product['material_type'] = inferred_subtype
            if isinstance(product.get('materials'), dict):
                product['materials']['primary_material'] = inferred_subtype
            return inferred_subtype

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
