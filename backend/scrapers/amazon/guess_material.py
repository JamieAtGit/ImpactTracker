# backend/scrapers/amazon/guess_material.py

def smart_guess_material(title):
    if not title:
        return None

    title = title.lower()

    material_keywords = {
        "plastic": ["plastic", "polypropylene", "acrylic", "pet"],
        "glass": ["glass", "borosilicate"],
        "aluminium": ["aluminum", "aluminium"],
        "steel": ["steel", "stainless"],
        "paper": ["paper", "pulp"],
        "cardboard": ["cardboard", "carton", "kraft"],
        "bamboo": ["bamboo"],
        "wood": ["wood", "oak", "pine"],
        "cotton": ["cotton", "organic cotton"],
        "silicone": ["silicone"],
        "ceramic": ["ceramic", "stoneware", "porcelain"]
    }

    for material, keywords in material_keywords.items():
        if any(keyword in title for keyword in keywords):
            return material.title()

    return None
