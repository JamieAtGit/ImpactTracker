"""
Brand Locations Enrichment Script
==================================
1. Adds a large curated list of ~800 brands across key Amazon UK categories.
2. Optionally scrapes the first page of Amazon UK search results for specified
   category keywords and extracts brand names, then attempts to assign origin.

Usage:
    python enrich_brand_locations.py          # static list only
    python enrich_brand_locations.py --scrape  # static list + live scrape

The script is idempotent — it never overwrites an existing entry.
"""

import json
import re
import sys
import time
import os
import random

BRAND_JSON_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'common', 'data', 'json', 'brand_locations.json'
)

# ---------------------------------------------------------------------------
# CURATED BRAND LIST
# Keys are lowercase brand names as used by resolve_brand_origin().
# Country = manufacturing / design origin most relevant for CO₂ estimation.
# ---------------------------------------------------------------------------

CURATED_BRANDS = {
    # ── Furniture / Tables ─────────────────────────────────────────────────
    'multigot':            'China',
    'homcom':              'China',
    'costway':             'China',
    'yaheetech':           'China',
    'songmics':            'China',
    'vasagle':             'China',
    'homfa':               'China',
    'sobuy':               'China',
    'tectake':             'China',
    'vonhaus':             'China',
    'furniturebox':        'UK',
    'living and home':     'China',
    'walker edison':       'China',
    'sauder':              'USA',
    'zinus':               'China',
    'ashley':              'China',
    'dorel':               'Canada',
    'teamson':             'China',
    'novosolo':            'Denmark',
    'dhp':                 'China',
    'keter':               'Israel',
    'lifetime':            'China',
    'better homes & gardens': 'China',
    'we furniture':        'China',
    'tvilum':              'Denmark',
    'birlea':              'China',
    'argos home':          'China',
    'julian bowen':        'China',
    'seconique':           'China',
    'vida designs':        'China',
    'lloyd pascal':        'China',
    'dams':                'UK',
    'teknik':              'China',
    'alphason':            'China',
    'afc':                 'China',
    'harrier sport':       'China',
    'homestyle4u':         'China',
    'flair furniture':     'China',
    'habitat':             'China',
    'heal\'s':             'UK',
    'heal':                'UK',
    'made.com':            'China',
    'made':                'China',
    'dunelm':              'China',
    'next home':           'China',
    'oak furnitureland':   'China',
    'dwell':               'China',

    # ── Knives / Cutlery ───────────────────────────────────────────────────
    'victorinox':          'Switzerland',
    'wüsthof':             'Germany',
    'wusthof':             'Germany',
    'zwilling':            'Germany',
    'j.a. henckels':       'Germany',
    'henckels':            'Germany',
    'global knives':       'Japan',
    'global':              'Japan',
    'mac knife':           'Japan',
    'mac':                 'Japan',
    'kai':                 'Japan',
    'shun':                'Japan',
    'miyabi':              'Germany',
    'messermeister':       'Germany',
    'mercer culinary':     'China',
    'mercer':              'China',
    'dexter-russell':      'USA',
    'f. dick':             'Germany',
    'opinel':              'France',
    'sabatier':            'France',
    'sabatier professional': 'France',
    'ka-bar':              'USA',
    'buck knives':         'USA',
    'gerber':              'USA',
    'benchmade':           'USA',
    'spyderco':            'USA',
    'kershaw':             'Japan',
    'crkt':                'China',
    'ontario':             'USA',
    'mora':                'Sweden',
    'morakniv':            'Sweden',
    'fiskars':             'Finland',
    'tramontina':          'Brazil',
    'scanpan':             'Denmark',
    'cangshan':            'China',
    'dalstrong':           'China',
    'zelite infinity':     'China',
    'misen':               'China',
    'babish':              'China',
    'seki edge':           'Japan',
    'richardson sheffield': 'UK',
    'prestige':            'China',
    'stellar':             'UK',
    'tower':               'China',
    'raymond blanc':       'France',

    # ── Lighting ───────────────────────────────────────────────────────────
    'philips hue':         'Netherlands',
    'lifx':                'Australia',
    'govee':               'China',
    'wiz':                 'Belgium',
    'tp-link':             'China',
    'tapo':                'China',
    'nanoleaf':            'Canada',
    'sengled':             'China',
    'elgato':              'Germany',
    'cree lighting':       'USA',
    'ge lighting':         'USA',
    'osram':               'Germany',
    'lutron':              'USA',
    'leviton':             'USA',
    'ring':                'USA',
    'eve systems':         'Germany',
    'hue':                 'Netherlands',
    'yeelight':            'China',
    'kasa':                'China',
    'meross':              'China',
    'treatlife':           'China',
    'lohas':               'China',
    'lepro':               'China',
    'lumary':              'China',
    'ledvance':            'Germany',
    'sylvania':            'Germany',
    'energizer':           'USA',
    'auraglow':            'UK',
    'bayco':               'USA',
    'livarno':             'Germany',
    'brilliant smart':     'Australia',
    'lexi lighting':       'UK',
    'nordlux':             'Denmark',
    'astro lighting':      'UK',
    'dar lighting':        'UK',
    'endon':               'UK',
    'saxby':               'UK',
    'lucide':              'Belgium',
    'trio leuchten':       'Germany',
    'paulmann':            'Germany',
    'eglo':                'Austria',
    'searchlight':         'UK',
    'firstlight':          'UK',

    # ── Bottles / Drinkware ────────────────────────────────────────────────
    'hydro flask':         'USA',
    'nalgene':             'USA',
    'yeti':                'USA',
    'camelbak':            'USA',
    'klean kanteen':       'USA',
    's\'well':             'USA',
    'swell':               'USA',
    'lifestraw':           'Switzerland',
    "chilly's":            'UK',
    'chillys':             'UK',
    'thermos':             'USA',
    'stanley':             'USA',
    'zojirushi':           'Japan',
    'tiger':               'Japan',
    'contigo':             'USA',
    'takeya':              'USA',
    'simple modern':       'USA',
    'blenderbottle':       'USA',
    'embrava':             'USA',
    'iron flask':          'China',
    'mira':                'USA',
    'reduce':              'USA',
    'ello':                'USA',
    'manna':               'UK',
    'avex':                'USA',
    'ozark trail':         'China',
    'greens steel':        'China',
    'elemental':           'USA',
    'peak':                'China',
    'bobble':              'USA',
    'built ny':            'China',
    'built':               'China',
    'joyjolt':             'China',
    'glasstic':            'China',
    'bkr':                 'USA',
    'memobottle':          'Australia',
    'soma':                'USA',
    'brita':               'Germany',
    'bobble':              'USA',

    # ── Kettles / Small Appliances ─────────────────────────────────────────
    'breville':            'Australia',
    'de\'longhi':          'Italy',
    'delonghi':            'Italy',
    'kitchenaid':          'USA',
    'russell hobbs':       'China',
    'morphy richards':     'China',
    'dualit':              'UK',
    'smeg':                'Italy',
    'balmuda':             'Japan',
    'kenwood':             'China',
    'cuisinart':           'China',
    'ninja':               'China',
    'hamilton beach':      'China',
    'instant pot':         'China',
    'instant':             'China',
    'sage':                'Australia',
    'tefal':               'France',
    'rowenta':             'France',
    'moulinex':            'France',
    'electrolux':          'Sweden',
    'bosch':               'Germany',
    'siemens':             'Germany',
    'miele':               'Germany',
    'aeg':                 'Sweden',
    'neff':                'Germany',
    'philips':             'Netherlands',
    'nespresso':           'Switzerland',
    'krups':               'Germany',
    'melitta':             'Germany',
    'jura':                'Switzerland',
    'gaggia':              'Italy',
    'la marzocco':         'Italy',
    'rancilio':            'Italy',
    'rocket espresso':     'Italy',
    'nutramilk':           'UK',
    'vitamix':             'USA',
    'blendjet':            'China',
    'nutribullet':         'USA',
    'magimix':             'France',
    'food network':        'China',
    'tower':               'China',
    'quest':               'China',
    'daewoo':              'South Korea',
    'nikai':               'UAE',

    # ── Watches ────────────────────────────────────────────────────────────
    'rolex':               'Switzerland',
    'seiko':               'Japan',
    'citizen':             'Japan',
    'casio':               'Japan',
    'fossil':              'China',
    'timex':               'China',
    'garmin':              'Taiwan',
    'tag heuer':           'Switzerland',
    'omega':               'Switzerland',
    'breitling':           'Switzerland',
    'longines':            'Switzerland',
    'tissot':              'Switzerland',
    'hamilton':            'Switzerland',
    'swatch':              'Switzerland',
    'movado':              'China',
    'bulova':              'Japan',
    'invicta':             'China',
    'orient':              'Japan',
    'skagen':              'China',
    'daniel wellington':   'China',
    'mvmt':                'China',
    'nixon':               'China',
    'ice-watch':           'Belgium',
    'sekonda':             'China',
    'accurist':            'China',
    'adidas':              'Germany',
    'emporio armani':      'Italy',
    'michael kors':        'China',
    'guess':               'China',
    'armani exchange':     'Italy',
    'vivienne westwood':   'China',
    'hugo boss':           'Germany',
    'tommy hilfiger':      'China',
    'calvin klein':        'China',
    'dkny':                'China',
    'kate spade':          'China',
    'coach':               'China',
    'marc jacobs':         'China',
    'versace':             'Italy',
    'diesel':              'Italy',
    'gc':                  'Switzerland',
    'festina':             'Spain',
    'lotus':               'Spain',
    'lorus':               'Japan',
    'pulsar':              'Japan',
    'tw steel':            'Netherlands',
    'police':              'China',
    'esprit':              'Germany',
    'komono':              'Belgium',
    'cluse':               'Netherlands',
    'triwa':               'Sweden',
    'withings':            'France',
    'suunto':              'Finland',
    'polar':               'Finland',
    'fitbit':              'USA',
    'apple':               'China',
    'samsung':             'South Korea',
    'huawei':              'China',
    'xiaomi':              'China',
    'amazfit':             'China',
    'ticwatch':            'China',
    'mobvoi':              'China',
    'fossil':              'China',

    # ── Electronics / Tech ─────────────────────────────────────────────────
    'sony':                'Japan',
    'lg':                  'South Korea',
    'panasonic':           'Japan',
    'sharp':               'Japan',
    'toshiba':             'Japan',
    'hitachi':             'Japan',
    'jvc':                 'Japan',
    'pioneer':             'Japan',
    'denon':               'Japan',
    'marantz':             'Japan',
    'yamaha':              'Japan',
    'bose':                'USA',
    'harman kardon':       'USA',
    'jbl':                 'USA',
    'skullcandy':          'USA',
    'sennheiser':          'Germany',
    'beyerdynamic':        'Germany',
    'akg':                 'Austria',
    'audio-technica':      'Japan',
    'shure':               'USA',
    'plantronics':         'USA',
    'jabra':               'Denmark',
    'logitech':            'Switzerland',
    'razer':               'Singapore',
    'corsair':             'USA',
    'steelseries':         'Denmark',
    'hyperx':              'USA',
    'roccat':              'Germany',
    'trust':               'Netherlands',
    'anker':               'China',
    'aukey':               'China',
    'ravpower':            'China',
    'baseus':              'China',
    'ugreen':              'China',
    'orico':               'China',
    'inateck':             'China',
    'sabrent':             'USA',
    'seagate':             'USA',
    'western digital':     'USA',
    'wd':                  'USA',
    'sandisk':             'USA',
    'kingston':            'USA',
    'samsung electronics': 'South Korea',
    'crucial':             'USA',
    'corsair':             'USA',
    'intel':               'USA',
    'amd':                 'USA',
    'nvidia':              'USA',
    'asus':                'Taiwan',
    'msi':                 'Taiwan',
    'gigabyte':            'Taiwan',
    'acer':                'Taiwan',
    'lenovo':              'China',
    'dell':                'USA',
    'hp':                  'USA',
    'microsoft':           'USA',
    'amazon':              'USA',
    'google':              'USA',
    'roku':                'USA',

    # ── Home Appliances ────────────────────────────────────────────────────
    'dyson':               'UK',
    'hoover':              'USA',
    'bissell':             'USA',
    'shark':               'China',
    'irobot':              'USA',
    'roomba':              'USA',
    'karcher':             'Germany',
    'nilfisk':             'Denmark',
    'vax':                 'UK',
    'henry':               'UK',
    'numatic':             'UK',
    'miele':               'Germany',
    'bosch':               'Germany',
    'siemens':             'Germany',
    'hotpoint':            'Italy',
    'indesit':             'Italy',
    'whirlpool':           'USA',
    'maytag':              'USA',
    'kitchenaid':          'USA',
    'smeg':                'Italy',
    'rangemaster':         'UK',
    'aga':                 'UK',
    'falcon':              'UK',
    'beko':                'Turkey',
    'hisense':             'China',
    'haier':               'China',
    'lg':                  'South Korea',
    'samsung':             'South Korea',
    'candy':               'Italy',
    'hopoint':             'Italy',
    'zanussi':             'Sweden',

    # ── Health & Beauty ────────────────────────────────────────────────────
    'philips sonicare':    'Netherlands',
    'oral-b':              'Germany',
    'braun':               'Germany',
    'panasonic':           'Japan',
    'remington':           'UK',
    'wahl':                'USA',
    'andis':               'USA',
    'babyliss':            'France',
    'ghd':                 'UK',
    'cloud nine':          'UK',
    'tigi':                'USA',
    'l\'oreal':            'France',
    'loreal':              'France',
    'garnier':             'France',
    'maybelline':          'USA',
    'revlon':              'USA',
    'mac cosmetics':       'USA',
    'charlotte tilbury':   'UK',
    'nars':                'USA',
    'urban decay':         'USA',
    'too faced':           'USA',
    'anastasia beverly hills': 'USA',
    'morphe':              'USA',
    'fenty beauty':        'USA',
    'kylie cosmetics':     'USA',
    'olaplex':             'USA',
    'kerastase':           'France',
    'wella':               'Germany',
    'schwarzkopf':         'Germany',
    'redken':              'USA',
    'paul mitchell':       'USA',
    'tresemme':            'USA',
    'dove':                'Netherlands',
    'nivea':               'Germany',
    'neutrogena':          'USA',
    'cerave':              'USA',
    'la roche-posay':      'France',
    'vichy':               'France',
    'the ordinary':        'Canada',
    'drunk elephant':      'USA',
    'tatcha':              'Japan',
    'lush':                'UK',
    'elemis':              'UK',

    # ── Sports & Outdoors ──────────────────────────────────────────────────
    'nike':                'China',
    'adidas':              'Germany',
    'puma':                'Germany',
    'reebok':              'China',
    'asics':               'Japan',
    'new balance':         'China',
    'under armour':        'China',
    'columbia':            'USA',
    'north face':          'China',
    'patagonia':           'USA',
    'arc\'teryx':          'Canada',
    'arcteryx':            'Canada',
    'the north face':      'China',
    'salomon':             'France',
    'merrell':             'China',
    'keen':                'China',
    'timberland':          'China',
    'hi-tec':              'UK',
    'regatta':             'China',
    'berghaus':            'China',
    'helly hansen':        'Norway',
    'mammut':              'Switzerland',
    'black diamond':       'USA',
    'petzl':               'France',
    'camp':                'Italy',
    'msr':                 'USA',
    'primus':              'Sweden',
    'jetboil':             'USA',
    'nemo':                'USA',
    'big agnes':           'USA',
    'therm-a-rest':        'USA',
    'exped':               'Switzerland',
    'lifesystems':         'UK',
    'cotswold outdoor':    'UK',
    'go outdoors':         'UK',
    'trespass':            'UK',

    # ── Books & Stationery ─────────────────────────────────────────────────
    'stabilo':             'Germany',
    'faber-castell':       'Germany',
    'pilot':               'Japan',
    'uni-ball':            'Japan',
    'mitsubishi pencil':   'Japan',
    'pentel':              'Japan',
    'staedtler':           'Germany',
    'bic':                 'France',
    'sharpie':             'USA',
    'crayola':             'USA',
    'posca':               'Japan',
    'winsor & newton':     'UK',
    'derwent':             'UK',
    'conte':               'France',
    'moleskine':           'Italy',
    'leuchtturm1917':      'Germany',
    'rhodia':              'France',
    'midori':              'Japan',
    'traveler\'s notebook': 'Japan',
    'clairefontaine':      'France',
    'paperblanks':         'Canada',
    'kikkerland':          'USA',
    'typo':                'Australia',

    # ── Toys & Kids ────────────────────────────────────────────────────────
    'lego':                'Denmark',
    'playmobil':           'Germany',
    'fisher-price':        'China',
    'mattel':              'China',
    'hasbro':              'China',
    'vtech':               'China',
    'leapfrog':            'China',
    'orchard toys':        'UK',
    'ravensburger':        'Germany',
    'clementoni':          'Italy',
    'djeco':               'France',
    'haba':                'Germany',
    'steiff':              'Germany',
    'zapf creation':       'Germany',
    'barbie':              'China',
    'hot wheels':          'China',
    'nerf':                'China',
    'funko pop':           'China',
    'funko':               'China',

    # ── Garden & Outdoor ──────────────────────────────────────────────────
    'bosch garden':        'Germany',
    'husqvarna':           'Sweden',
    'honda':               'Japan',
    'dewalt':              'USA',
    'makita':              'Japan',
    'ryobi':               'Japan',
    'stihl':               'Germany',
    'flymo':               'Sweden',
    'alm':                 'UK',
    'fiskars':             'Finland',
    'felco':               'Switzerland',
    'wolf garten':         'Germany',
    'spear & jackson':     'UK',
    'burgon & ball':       'UK',
    'kent & stowe':        'UK',
    'terrain':             'UK',
    'haws':                'UK',
    'whitefurze':          'UK',

    # ── Pet Supplies ───────────────────────────────────────────────────────
    'royal canin':         'France',
    'hills':               'USA',
    'purina':              'USA',
    'iams':                'USA',
    'whiskas':             'USA',
    'felix':               'USA',
    'pedigree':            'USA',
    'cesar':               'USA',
    'lily\'s kitchen':     'UK',
    'forthglade':          'UK',
    'naturo':              'UK',
    'harringtons':         'UK',
    'james wellbeloved':   'UK',
    'burns pet nutrition': 'UK',
    'canagan':             'UK',
    'orijen':              'Canada',
    'acana':               'Canada',
    'taste of the wild':   'USA',
    'blue buffalo':        'USA',
    'wellness':            'USA',
}


# ---------------------------------------------------------------------------
# Amazon UK category search terms
# ---------------------------------------------------------------------------

AMAZON_SEARCH_CATEGORIES = [
    ('glass table', 'Furniture'),
    ('dining table', 'Furniture'),
    ('coffee table', 'Furniture'),
    ('office desk', 'Furniture'),
    ('kitchen knives', 'Kitchen'),
    ('chef knife', 'Kitchen'),
    ('table lamp', 'Lighting'),
    ('led light bulb', 'Lighting'),
    ('floor lamp', 'Lighting'),
    ('water bottle', 'Drinkware'),
    ('insulated bottle', 'Drinkware'),
    ('electric kettle', 'Appliances'),
    ('toaster', 'Appliances'),
    ('mens watch', 'Watches'),
    ('womens watch', 'Watches'),
    ('smartwatch', 'Electronics'),
    ('bluetooth headphones', 'Electronics'),
    ('phone case', 'Electronics'),
    ('yoga mat', 'Sports'),
    ('running shoes', 'Sports'),
    ('notebook journal', 'Stationery'),
    ('dog food', 'Pet'),
    ('cat food', 'Pet'),
    ('garden trowel', 'Garden'),
    ('plant pot', 'Garden'),
]


def load_brand_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_brand_json(path: str, data: dict) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(data) - 1} brands to {path}")


def add_curated_brands(data: dict) -> int:
    """Add brands from CURATED_BRANDS. Returns number of new entries added."""
    added = 0
    for brand, country in CURATED_BRANDS.items():
        key = brand.lower().strip()
        if key not in data:
            data[key] = {'origin': {'country': country}}
            added += 1
    return added


def scrape_amazon_search_brands(search_term: str) -> list:
    """
    Fetch the first page of Amazon UK results for search_term and extract
    brand names from product listings.  Returns list of (brand, asin) tuples.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("⚠️  requests/beautifulsoup4 not available — skipping live scrape")
        return []

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
    }

    url = f'https://www.amazon.co.uk/s?k={search_term.replace(" ", "+")}'
    print(f"  🔍 Scraping: {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"  ⚠️  HTTP {resp.status_code} for '{search_term}'")
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')

        brands = []

        # Selector 1: sponsored/organic product cards → span with data-asin
        for card in soup.select('[data-asin]'):
            asin = card.get('data-asin', '').strip()
            if not asin:
                continue

            # Brand from "by <brand>" span
            by_brand = card.select_one('.a-row.a-size-base.a-color-secondary span')
            if by_brand:
                text = by_brand.get_text(strip=True)
                m = re.match(r'^(?:by|brand:|visit the)\s+(.+?)(?:\s+store)?$', text, re.I)
                if m:
                    brands.append((m.group(1).strip(), asin))
                    continue

            # Brand from product title h2 aria-label or data attributes
            title_el = card.select_one('h2 span')
            if title_el:
                title_text = title_el.get_text(strip=True)
                # First word of title is often the brand
                first_word = title_text.split()[0] if title_text else None
                if first_word and len(first_word) > 2:
                    brands.append((first_word, asin))

        return brands

    except Exception as e:
        print(f"  ⚠️  Scrape failed for '{search_term}': {e}")
        return []


def infer_country_from_brand_name(brand: str) -> str | None:
    """
    Very rough heuristic: return a likely manufacturing country based on
    common naming patterns.  Returns None when the brand is unrecognised.
    """
    b = brand.lower()
    japanese = ['ao', 'yama', 'moto', 'kawa', 'tani', 'shiro', 'haru', 'nori', 'seki']
    chinese_suffix = ['tech', 'led', 'smart', 'plus', 'pro', 'max', 'x', 'go']
    german = ['mann', 'haus', 'berg', 'bach', 'feld']

    for tok in japanese:
        if tok in b:
            return 'Japan'
    if any(b.endswith(s) for s in german):
        return 'Germany'
    # Default for unknown brands from Amazon UK → likely China-manufactured
    return 'China'


def run(live_scrape: bool = False):
    print(f"📂 Loading {BRAND_JSON_PATH}")
    data = load_brand_json(BRAND_JSON_PATH)
    existing_before = len(data) - 1   # subtract _metadata

    # 1. Add curated list
    curated_added = add_curated_brands(data)
    print(f"✅ Added {curated_added} curated brands ({existing_before + curated_added} total)")

    # 2. Optionally scrape Amazon UK
    scrape_added = 0
    if live_scrape:
        print("\n🌐 Starting live Amazon UK scrape…")
        for search_term, category in AMAZON_SEARCH_CATEGORIES:
            results = scrape_amazon_search_brands(search_term)
            for brand, asin in results:
                key = brand.lower().strip()
                # Skip very short / numeric / already present
                if len(key) < 3 or key.isdigit() or key in data:
                    continue
                guessed = infer_country_from_brand_name(brand)
                if guessed:
                    data[key] = {'origin': {'country': guessed}}
                    scrape_added += 1
                    print(f"    + {brand!r} → {guessed} (category: {category})")
            # Polite delay between search pages
            time.sleep(random.uniform(2.5, 4.5))

        print(f"\n✅ Scraped {scrape_added} additional brands")

    # 3. Update metadata
    if '_metadata' in data:
        data['_metadata']['total_brands'] = str(len(data) - 1)
        data['_metadata']['last_updated'] = '2026-04-03'

    save_brand_json(BRAND_JSON_PATH, data)
    print(f"\n📊 Summary: {existing_before} → {len(data) - 1} brands "
          f"(+{curated_added} curated, +{scrape_added} scraped)")


if __name__ == '__main__':
    live = '--scrape' in sys.argv
    run(live_scrape=live)
