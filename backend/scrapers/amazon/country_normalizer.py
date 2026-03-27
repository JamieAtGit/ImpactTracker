import re
import unicodedata
from typing import Optional

try:
    import pycountry  # type: ignore
except Exception:
    pycountry = None


INVALID_TOKENS = {
    "splinter", "warning", "bpa", "plastic", "disposable", "cutlery",
    "pack", "piece", "set", "size", "weight", "model", "item", "friendly",
    "format", "manufacturer", "age", "dimensions", "additional"
}

ALIASES = {
    # UK variants
    "gb": "UK",
    "uk": "UK",
    "u.k": "UK",
    "u.k.": "UK",
    "united kingdom": "UK",
    "great britain": "UK",
    "britain": "UK",
    "england": "UK",
    "scotland": "UK",
    "wales": "UK",
    "northern ireland": "UK",
    # USA variants
    "usa": "USA",
    "u.s": "USA",
    "u.s.": "USA",
    "u.s.a": "USA",
    "u.s.a.": "USA",
    "us": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "america": "USA",
    # China variants
    "prc": "China",
    "p.r.c": "China",
    "p.r.c.": "China",
    "p.r. china": "China",
    "pr china": "China",
    "peoples republic of china": "China",
    "people s republic of china": "China",
    "the peoples republic of china": "China",
    "mainland china": "China",
    "china mainland": "China",
    # Korea
    "korea": "South Korea",
    "republic of korea": "South Korea",
    "korea republic of": "South Korea",
    "south korea": "South Korea",
    "dprk": "North Korea",
    "north korea": "North Korea",
    # Other common aliases
    "russian federation": "Russia",
    "russia": "Russia",
    "viet nam": "Vietnam",
    "vietnam": "Vietnam",
    "taiwan province of china": "Taiwan",
    "taiwan province": "Taiwan",
    "iran islamic republic of": "Iran",
    "iran": "Iran",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    # Europe
    "deutschland": "Germany",
    "espana": "Spain",
    "nederland": "Netherlands",
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    "belgie": "Belgium",
    "belgique": "Belgium",
    "belgium": "Belgium",
    "suisse": "Switzerland",
    "schweiz": "Switzerland",
    "switzerland": "Switzerland",
    "osterreich": "Austria",
    "austria": "Austria",
    "polska": "Poland",
    "poland": "Poland",
    "eire": "Ireland",
    "republic of ireland": "Ireland",
    "ireland": "Ireland",
    "czechia": "Czech Republic",
    "czech republic": "Czech Republic",
    "turkiye": "Turkey",
    "turkey": "Turkey",
    # Asia-Pacific
    "hong kong sar": "Hong Kong",
    "hong kong": "Hong Kong",
    "macau": "Macau",
    "macao": "Macau",
    "myanmar": "Myanmar",
    "burma": "Myanmar",
    "sri lanka": "Sri Lanka",
    "ceylon": "Sri Lanka",
    # Africa / Americas
    "ivory coast": "Ivory Coast",
    "cote d ivoire": "Ivory Coast",
    "south africa": "South Africa",
    "brasil": "Brazil",
    "mexico": "Mexico",
    "mejico": "Mexico",
}

FALLBACK_COUNTRIES = {
    "UK", "USA", "China", "Germany", "France", "Italy", "Spain", "Japan", "Canada", "India",
    "Netherlands", "Switzerland", "Austria", "Poland", "Ireland", "Denmark", "Sweden", "Norway",
    "Belgium", "Portugal", "Turkey", "Greece", "Czech Republic", "Hungary", "Romania", "Finland",
    "South Korea", "Taiwan", "Vietnam", "Thailand", "Malaysia", "Indonesia", "Singapore", "Mexico",
    "Brazil", "Australia", "New Zealand", "South Africa", "Russia", "United Arab Emirates",
    "Hong Kong", "Macau", "Myanmar", "Sri Lanka", "Bangladesh", "Pakistan", "Cambodia",
    "Philippines", "Ethiopia", "Egypt", "Morocco", "Tunisia", "Nigeria", "Kenya",
    "Israel", "Jordan", "Saudi Arabia", "Qatar", "Kuwait", "Iran",
    "Argentina", "Colombia", "Chile", "Peru",
    "Ivory Coast", "North Korea",
}


def _clean(raw_text: str) -> str:
    text = (raw_text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z\s\-.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_country_name(raw_country: str) -> str:
    if not raw_country:
        return "Unknown"

    cleaned = _clean(raw_country)
    if not cleaned:
        return "Unknown"

    if any(token in cleaned for token in INVALID_TOKENS):
        return "Unknown"

    if cleaned in ALIASES:
        return ALIASES[cleaned]

    if pycountry is not None:
        try:
            direct = pycountry.countries.lookup(cleaned)
            name = direct.name
            if name == "United Kingdom":
                return "UK"
            if name == "United States":
                return "USA"
            return name
        except LookupError:
            pass

        try:
            # Fuzzy fallback for small typos (e.g. "Germny")
            fuzzy = pycountry.countries.search_fuzzy(cleaned)
            if fuzzy:
                name = fuzzy[0].name
                if name == "United Kingdom":
                    return "UK"
                if name == "United States":
                    return "USA"
                return name
        except Exception:
            pass

    titled = cleaned.title()
    if titled in FALLBACK_COUNTRIES:
        return titled

    return "Unknown"


def is_valid_country(raw_country: str) -> bool:
    return normalize_country_name(raw_country) != "Unknown"
