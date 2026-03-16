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
    "usa": "USA",
    "u.s": "USA",
    "u.s.": "USA",
    "us": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "prc": "China",
    "people s republic of china": "China",
    "peoples republic of china": "China",
    "korea": "South Korea",
    "republic of korea": "South Korea",
    "korea republic of": "South Korea",
    "russian federation": "Russia",
    "viet nam": "Vietnam",
    "taiwan province of china": "Taiwan",
    "taiwan province": "Taiwan",
    "iran islamic republic of": "Iran",
    "uae": "United Arab Emirates",
    "deutschland": "Germany",
    "espana": "Spain",
    "nederland": "Netherlands",
    "holland": "Netherlands",
    "belgie": "Belgium",
    "belgique": "Belgium",
    "suisse": "Switzerland",
    "schweiz": "Switzerland",
    "osterreich": "Austria",
    "polska": "Poland",
    "eire": "Ireland",
}

FALLBACK_COUNTRIES = {
    "UK", "USA", "China", "Germany", "France", "Italy", "Spain", "Japan", "Canada", "India",
    "Netherlands", "Switzerland", "Austria", "Poland", "Ireland", "Denmark", "Sweden", "Norway",
    "Belgium", "Portugal", "Turkey", "Greece", "Czech Republic", "Hungary", "Romania", "Finland",
    "South Korea", "Taiwan", "Vietnam", "Thailand", "Malaysia", "Indonesia", "Singapore", "Mexico",
    "Brazil", "Australia", "New Zealand", "South Africa", "Russia", "United Arab Emirates"
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
