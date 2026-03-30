# backend/scrapers/amazon/guess_material.py
#
# Title-based material guessing.  Longer / more specific phrases are checked
# first so "stainless steel" always wins over plain "steel", "velvet" wins
# over a generic "metal" frame, etc.

def smart_guess_material(title: str) -> str | None:
    if not title:
        return None

    t = title.lower()

    # ── Ordered from most-specific to least-specific ─────────────────────────
    # Each entry: (keywords_list, canonical_material_name)
    # First match wins, so put longer / more specific phrases earlier.

    RULES = [
        # ── Upholstery / soft furnishings (must beat generic "metal" frame) ──
        (["velvet", "velour"],                          "Velvet"),
        (["boucle", "bouclé"],                          "Boucle"),
        (["faux leather sofa", "pu sofa", "pu leather chair",
          "leather sofa", "leather chair", "leather stool"],  "Leather"),
        (["linen sofa", "linen chair", "linen fabric"], "Linen"),
        (["chenille"],                                  "Chenille"),
        (["upholstered", "upholstery"],                 "Fabric"),
        (["foam mattress", "memory foam", "foam"],      "Foam"),
        (["cushion", "pouf", "ottoman", "bean bag"],    "Fabric"),

        # ── Natural fibres ────────────────────────────────────────────────────
        (["100% cotton", "organic cotton", "pure cotton"], "Cotton"),
        (["cotton"],                                    "Cotton"),
        (["linen", "flax"],                             "Linen"),
        (["hemp"],                                      "Hemp"),
        (["jute", "sisal", "burlap"],                   "Jute"),
        (["merino wool", "pure wool", "100% wool"],     "Merino Wool"),
        (["wool"],                                      "Wool"),
        (["cashmere"],                                  "Cashmere"),
        (["silk"],                                      "Silk"),
        (["down jacket", "goose down", "duck down"],    "Down"),

        # ── Synthetic fibres ──────────────────────────────────────────────────
        (["recycled polyester", "rpet"],                "Recycled Polyester"),
        (["polyester", "fleece", "polar fleece"],       "Polyester"),
        (["nylon", "cordura"],                          "Nylon"),
        (["acrylic knit", "acrylic yarn"],              "Acrylic"),
        (["lycra", "spandex", "elastane"],              "Spandex"),
        (["viscose", "rayon"],                          "Viscose"),

        # ── Leather ───────────────────────────────────────────────────────────
        (["genuine leather", "real leather", "full grain", "top grain"], "Leather"),
        (["vegan leather", "faux leather", "pu leather",
          "synthetic leather", "pu coated"],            "Faux Leather"),
        (["suede"],                                     "Suede"),
        (["leather"],                                   "Leather"),

        # ── Wood ──────────────────────────────────────────────────────────────
        (["solid oak", "solid pine", "solid walnut",
          "solid beech", "solid wood", "solid timber"],  "Solid Wood"),
        (["oak", "pine", "walnut", "birch", "teak",
          "mahogany", "maple", "beech", "acacia"],      "Timber"),
        (["engineered wood", "mdf", "particleboard",
          "chipboard", "plywood", "fibreboard",
          "fsc-certified wood", "fsc certified"],       "Engineered Wood"),
        (["wooden", "timber", "reclaimed wood"],        "Timber"),
        (["bamboo"],                                    "Bamboo"),

        # ── Metals ────────────────────────────────────────────────────────────
        (["stainless steel", "surgical steel"],         "Stainless Steel"),
        (["cast iron"],                                 "Cast Iron"),
        (["carbon steel"],                              "Carbon Steel"),
        (["titanium"],                                  "Titanium"),
        (["aluminium alloy", "aluminum alloy",
          "anodised aluminium", "anodized aluminum"],   "Aluminium"),
        (["aluminium", "aluminum"],                     "Aluminium"),
        (["copper"],                                    "Copper"),
        (["brass", "bronze"],                           "Brass"),
        (["steel", "iron", "metal frame", "metal leg",
          "metal base", "metallic"],                    "Steel"),

        # ── Glass / ceramics ──────────────────────────────────────────────────
        (["borosilicate", "tempered glass", "toughened glass"], "Glass"),
        (["glass"],                                     "Glass"),
        (["porcelain", "stoneware", "earthenware"],     "Ceramic"),
        (["ceramic"],                                   "Ceramic"),

        # ── Plastics — specific subtypes before generic ───────────────────────
        (["recycled plastic", "recycled pp"],           "Recycled Plastic"),
        (["polycarbonate"],                             "Polycarbonate"),
        (["polypropylene"],                             "Polypropylene"),
        (["polyethylene", "hdpe", "ldpe"],              "Polyethylene"),
        (["abs plastic", "abs"],                        "ABS Plastic"),
        (["pvc", "polyvinyl chloride"],                 "PVC"),
        (["polystyrene", "eps foam"],                   "Polystyrene"),
        (["acrylic", "perspex", "plexiglass"],          "Acrylic"),
        (["plastic"],                                   "Plastic"),

        # ── Other ─────────────────────────────────────────────────────────────
        (["microfibre", "microfiber", "microfleece"],   "Microfibre"),
        (["faux fur", "fake fur", "sherpa"],             "Faux Fur"),
        (["neoprene"],                                  "Neoprene"),
        (["rattan", "wicker", "woven rattan"],           "Rattan"),
        (["cork"],                                      "Cork"),
        (["fiberglass", "fibreglass", "glass fibre",
          "glass fiber"],                               "Fibreglass"),
        (["vinyl", "pvc vinyl"],                        "Vinyl"),
        (["laminate", "laminated"],                     "Laminate"),
        (["melamine"],                                  "Melamine"),
        (["galvanised steel", "galvanized steel",
          "galvanised", "galvanized"],                  "Galvanised Steel"),
        (["epoxy"],                                     "Epoxy"),
        (["silicone"],                                  "Silicone"),
        (["rubber"],                                    "Rubber"),
        (["carbon fibre", "carbon fiber"],              "Carbon Fibre"),
        (["paper", "kraft", "pulp"],                    "Paper"),
        (["cardboard", "carton"],                       "Cardboard"),

        # ── Electronics / computers (must appear before Paper so "notebook"
        #    in page text doesn't cause laptops to be classified as Paper) ──
        (["macbook", "macbook air", "macbook pro"],     "Aluminium"),
        (["iphone", "ipad", "apple watch"],             "Aluminium"),
        (["laptop", "notebook computer", "ultrabook",
          "chromebook", "thinkpad", "surface pro",
          "gaming laptop"],                             "Mixed"),
        (["smartphone", "android phone", "tablet pc"], "Mixed"),
    ]

    for keywords, material in RULES:
        if any(kw in t for kw in keywords):
            return material

    return None
