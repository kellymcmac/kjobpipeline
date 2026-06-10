"""Location string parsing.

Takes a raw location string (and optional remote_type) and returns structured
fields: region, country, state, city.

Examples:
    parse_location("Chicago, IL, USA")              -> Chicago, IL, United States, US
    parse_location("San Francisco, CA, USA")        -> San Francisco, CA, United States, US
    parse_location("Remote US")                     -> "", "", United States, US
    parse_location("United Kingdom")                -> "", "", United Kingdom, UK
    parse_location("Berlin, Germany")               -> Berlin, "", Germany, EU
    parse_location("Canada - Remote (ON, AB only)") -> "", "", Canada, Canada
    parse_location("Remote - EMEA")                 -> "", "", "", EU
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedLocation:
    city: str = ""
    state: str = ""
    country: str = ""
    region: str = ""
    is_remote: bool = False


# US states: 50 + DC, lowercase full names mapping to 2-letter codes
US_STATE_NAMES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}

US_STATE_CODES = set(US_STATE_NAMES.values())

# Country name (lowercase) -> (canonical display name, region code)
# Region codes: US, UK, Canada, EU, LATAM, APAC, ANZ, MENA, Africa, Global, Other
COUNTRY_TO_REGION = {
    # North America
    "united states": ("United States", "US"),
    "usa": ("United States", "US"),
    "u.s.": ("United States", "US"),
    "u.s.a.": ("United States", "US"),
    "us": ("United States", "US"),
    "canada": ("Canada", "Canada"),
    "mexico": ("Mexico", "LATAM"),

    # UK / Europe
    "united kingdom": ("United Kingdom", "UK"),
    "uk": ("United Kingdom", "UK"),
    "u.k.": ("United Kingdom", "UK"),
    "great britain": ("United Kingdom", "UK"),
    "britain": ("United Kingdom", "UK"),
    "england": ("United Kingdom", "UK"),
    "scotland": ("United Kingdom", "UK"),
    "wales": ("United Kingdom", "UK"),
    "ireland": ("Ireland", "EU"),
    "germany": ("Germany", "EU"),
    "deutschland": ("Germany", "EU"),
    "france": ("France", "EU"),
    "spain": ("Spain", "EU"),
    "italy": ("Italy", "EU"),
    "netherlands": ("Netherlands", "EU"),
    "holland": ("Netherlands", "EU"),
    "belgium": ("Belgium", "EU"),
    "luxembourg": ("Luxembourg", "EU"),
    "switzerland": ("Switzerland", "EU"),
    "austria": ("Austria", "EU"),
    "poland": ("Poland", "EU"),
    "portugal": ("Portugal", "EU"),
    "sweden": ("Sweden", "EU"),
    "norway": ("Norway", "EU"),
    "denmark": ("Denmark", "EU"),
    "finland": ("Finland", "EU"),
    "greece": ("Greece", "EU"),
    "czech republic": ("Czech Republic", "EU"),
    "czechia": ("Czech Republic", "EU"),
    "romania": ("Romania", "EU"),
    "bulgaria": ("Bulgaria", "EU"),
    "hungary": ("Hungary", "EU"),
    "estonia": ("Estonia", "EU"),
    "latvia": ("Latvia", "EU"),
    "lithuania": ("Lithuania", "EU"),
    "slovakia": ("Slovakia", "EU"),
    "slovenia": ("Slovenia", "EU"),
    "croatia": ("Croatia", "EU"),
    "iceland": ("Iceland", "EU"),

    # LATAM
    "brazil": ("Brazil", "LATAM"),
    "argentina": ("Argentina", "LATAM"),
    "chile": ("Chile", "LATAM"),
    "colombia": ("Colombia", "LATAM"),
    "peru": ("Peru", "LATAM"),
    "uruguay": ("Uruguay", "LATAM"),
    "venezuela": ("Venezuela", "LATAM"),
    "costa rica": ("Costa Rica", "LATAM"),
    "panama": ("Panama", "LATAM"),

    # APAC
    "japan": ("Japan", "APAC"),
    "china": ("China", "APAC"),
    "india": ("India", "APAC"),
    "singapore": ("Singapore", "APAC"),
    "hong kong": ("Hong Kong", "APAC"),
    "south korea": ("South Korea", "APAC"),
    "korea": ("South Korea", "APAC"),
    "philippines": ("Philippines", "APAC"),
    "thailand": ("Thailand", "APAC"),
    "vietnam": ("Vietnam", "APAC"),
    "indonesia": ("Indonesia", "APAC"),
    "malaysia": ("Malaysia", "APAC"),
    "taiwan": ("Taiwan", "APAC"),

    # ANZ
    "australia": ("Australia", "ANZ"),
    "new zealand": ("New Zealand", "ANZ"),

    # MENA
    "uae": ("UAE", "MENA"),
    "united arab emirates": ("UAE", "MENA"),
    "saudi arabia": ("Saudi Arabia", "MENA"),
    "israel": ("Israel", "MENA"),
    "egypt": ("Egypt", "MENA"),
    "turkey": ("Turkey", "MENA"),
    "qatar": ("Qatar", "MENA"),

    # Africa
    "south africa": ("South Africa", "Africa"),
    "nigeria": ("Nigeria", "Africa"),
    "kenya": ("Kenya", "Africa"),
    "morocco": ("Morocco", "Africa"),
    "ghana": ("Ghana", "Africa"),
}

# Direct region aliases (no country implied)
REGION_ALIASES = {
    "emea": "EU",
    "europe": "EU",
    "european union": "EU",
    "latam": "LATAM",
    "latin america": "LATAM",
    "south america": "LATAM",
    "central america": "LATAM",
    "north america": "US",  # ambiguous; usually means US in tech postings
    "americas": "US",
    "apac": "APAC",
    "asia": "APAC",
    "asia pacific": "APAC",
    "anz": "ANZ",
    "australasia": "ANZ",
    "mena": "MENA",
    "middle east": "MENA",
    "africa": "Africa",
    "worldwide": "Global",
    "global": "Global",
    "anywhere": "Global",
}

REMOTE_KEYWORDS = ["remote", "anywhere", "fully remote", "work from home", "wfh", "distributed"]

# Words to strip out of city candidates so they don't end up in the City field.
# Includes remote/hybrid/onsite signals, connecting words, and other noise.
CITY_NOISE_TERMS = REMOTE_KEYWORDS + [
    "hybrid", "onsite", "on-site", "in-office", "in office",
    " or ", " and ",
]


def _word_match(text: str, phrase: str) -> bool:
    """True if `phrase` appears as a whole word/phrase in `text` (already lowercase)."""
    pattern = r"(?:^|[^a-z0-9])" + re.escape(phrase) + r"(?:[^a-z0-9]|$)"
    return bool(re.search(pattern, text))


def parse_location(raw: str, remote_type: str = "") -> ParsedLocation:
    """Parse a raw location string into a ParsedLocation.

    Logic in priority order:
      1. Detect remote signal (from remote_type field or text keywords).
      2. Walk comma/semicolon-separated tokens looking for:
         - US state codes (CA, IL, NY...) -> sets state and implies country=US
         - US state full names -> same
         - Country names -> sets country and region
         - Region keywords (EMEA, APAC, etc.) -> sets region only
      3. First unclassified token becomes the city.
      4. If region is still empty but is_remote is True, default to "Global".
    """
    result = ParsedLocation()

    rt = (remote_type or "").strip().lower()
    raw = (raw or "").strip()
    low = raw.lower()

    if rt == "remote" or any(_word_match(low, kw) for kw in REMOTE_KEYWORDS):
        result.is_remote = True

    if not raw:
        if result.is_remote:
            result.region = "Global"
        return result

    # Strip parenthetical content from the WHOLE string before splitting on commas,
    # otherwise content like "Canada - Remote (ON, AB, BC)" splits the parens across tokens
    # and per-token stripping leaves "Canada - Remote (ON" intact.
    raw_no_parens = re.sub(r"\([^)]*\)", "", raw)
    # Also drop any orphan parens characters that survived (open-paren without close, etc.)
    raw_no_parens = re.sub(r"[()]", "", raw_no_parens).strip()
    low_no_parens = raw_no_parens.lower()

    # Check region aliases on whole string (longest first to handle multi-word)
    for region_kw in sorted(REGION_ALIASES, key=len, reverse=True):
        if _word_match(low, region_kw):
            result.region = REGION_ALIASES[region_kw]
            break

    # Check country names on whole string (longest first)
    for country_kw in sorted(COUNTRY_TO_REGION, key=len, reverse=True):
        if _word_match(low, country_kw):
            display, region_code = COUNTRY_TO_REGION[country_kw]
            if not result.country:
                result.country = display
            # Country-derived region overrides a generic region alias only if region wasn't already set by explicit alias
            if not result.region:
                result.region = region_code
            break

    # Tokenize for city/state extraction (use the parens-stripped version)
    tokens = [t.strip() for t in re.split(r"[,;·|/]", raw_no_parens) if t.strip()]
    cleaned_tokens = tokens  # already paren-free

    for token in cleaned_tokens:
        t_low = token.lower()
        t_upper = token.upper()

        # US state code (e.g. "IL")
        if t_upper in US_STATE_CODES and not result.state:
            result.state = t_upper
            if not result.country:
                result.country = "United States"
            if not result.region:
                result.region = "US"
            continue

        # US state full name (e.g. "Illinois")
        if t_low in US_STATE_NAMES and not result.state:
            result.state = US_STATE_NAMES[t_low]
            if not result.country:
                result.country = "United States"
            if not result.region:
                result.region = "US"
            continue

        # Skip tokens that ARE a country or region alias
        if t_low in COUNTRY_TO_REGION or t_low in REGION_ALIASES:
            continue

        # Strip remote/hybrid/onsite noise to find a city candidate
        candidate = t_low
        for kw in CITY_NOISE_TERMS:
            candidate = candidate.replace(kw, " ")
        candidate = re.sub(r"\s+", " ", candidate).strip(" -")

        # First valid leftover token becomes the city
        if not result.city and candidate and len(candidate) > 1:
            # Make sure cleaned form isn't itself a country/region/state
            if (candidate not in COUNTRY_TO_REGION
                    and candidate not in REGION_ALIASES
                    and candidate not in US_STATE_NAMES
                    and candidate.upper() not in US_STATE_CODES):
                # Recover original casing from the token (parens already stripped earlier)
                original = token
                for kw in CITY_NOISE_TERMS:
                    original = re.sub(re.escape(kw), " ", original, flags=re.IGNORECASE)
                original = re.sub(r"\s+", " ", original).strip(" -")
                # Skip if it's a country/region/state after final cleaning
                if (original.lower() not in COUNTRY_TO_REGION
                        and original.lower() not in REGION_ALIASES
                        and original.lower() not in US_STATE_NAMES
                        and original.upper() not in US_STATE_CODES
                        and original):
                    result.city = original

    # If still no region but is_remote, default to Global
    if not result.region and result.is_remote:
        result.region = "Global"

    return result
