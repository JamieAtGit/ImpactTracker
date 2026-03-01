import os
import json
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sources = [
    os.path.join(PROJECT_ROOT, 'common', 'data', 'json', 'brand_locations.json'),
    os.path.join(PROJECT_ROOT, 'brand_locations.json'),
    os.path.join(PROJECT_ROOT, 'backend', 'scrapers', 'amazon', 'brand_locations.json'),
    os.path.join(PROJECT_ROOT, 'ml', 'evaluation', 'brand_locations.json'),
    os.path.join(PROJECT_ROOT, 'backend', 'services', 'enhanced_brand_locations.json'),
]

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def merge_entries(existing, incoming):
    """Merge two brand entry values. Prefer dict with origin details; else use string country."""
    # Normalize incoming to dict form if string
    def to_dict(val):
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            return {"origin": {"country": val}}
        return {}
    A = to_dict(existing)
    B = to_dict(incoming)
    # If one is empty, return the other
    if not A:
        return B if B else existing
    if not B:
        return A if A else existing
    # Merge origin info, prefer B's non-empty fields
    originA = A.get('origin', {})
    originB = B.get('origin', {})
    origin = {
        'country': originB.get('country') or originA.get('country'),
        'city': originB.get('city') or originA.get('city'),
    }
    result = {**A, **B}
    result['origin'] = {k: v for k, v in origin.items() if v}
    return result

def main():
    merged = {}
    for src in sources:
        data = load_json(src)
        # Skip metadata keys later
        for k, v in data.items():
            if k == '_metadata':
                continue
            if k not in merged:
                merged[k] = v
            else:
                merged[k] = merge_entries(merged[k], v)

    # Sort keys for consistency
    merged_sorted = {k: merged[k] for k in sorted(merged.keys())}

    # Add metadata
    metadata = {
        'total_brands': str(len(merged_sorted)),
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d'),
        'source_files': [p for p in sources if os.path.exists(p)]
    }
    merged_sorted = {'_metadata': metadata, **merged_sorted}

    out_path = os.path.join(PROJECT_ROOT, 'common', 'data', 'json', 'brand_locations.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged_sorted, f, indent=2, ensure_ascii=False)
    print(f"✅ Merged brand_locations written to {out_path} ({len(merged_sorted)-1} brands)")

if __name__ == '__main__':
    main()
