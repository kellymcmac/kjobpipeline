"""Pre-filter logic. Cheap checks that drop obvious misses before writing to Airtable."""

import logging
import re

from .models import JobPosting
from . import config

log = logging.getLogger(__name__)


def _word_match(text_low: str, phrase_low: str) -> bool:
    """True if `phrase_low` occurs in `text_low` bounded by non-alphanumeric
    edges (or string ends), tolerating a simple trailing plural "s". Both args
    must already be lowercase.

    This is a stricter cousin of location.py's _word_match: short tokens
    ("mode", "vp", "sas programming") match only as standalone words/phrases,
    not as substrings inside larger words ("model", "Kansas", "PostgreSQL").
    Internal punctuation in a phrase (e.g. "a/b test", "self-serve", "power bi")
    is preserved via re.escape so multi-word and punctuated keywords match.

    The optional trailing "s" before the closing boundary means plurals like
    "ETLs", "LLMs", "control charts" still match "etl"/"llm"/"control chart"
    without reopening substring collisions (the leading boundary still blocks
    "model", and "PostgreSQL" still fails because there's no boundary before
    "sql"). It is deliberately naive: it won't catch irregular plurals, but
    those are rare in the keyword set and a missed Tier 2 hit is low-cost.
    """
    pattern = r"(?:^|[^a-z0-9])" + re.escape(phrase_low) + r"s?(?:[^a-z0-9]|$)"
    return bool(re.search(pattern, text_low))


def passes_title_filter(title: str) -> bool:
    """True if title matches at least one TARGET_TITLES entry and no exclude term.

    Uses whole-word matching so exclude terms like "sales", "vp", "intern"
    match only as whole words and don't clobber legitimate titles (e.g. "intern"
    no longer matches "internal", "vp" no longer matches inside other tokens).
    """
    low = (title or "").lower()
    if not any(_word_match(low, target) for target in config.TARGET_TITLES):
        return False
    if any(_word_match(low, term) for term in config.EXCLUDE_TITLE_TERMS):
        return False
    return True


def is_remote_role(job: JobPosting) -> bool:
    """True if the role is remote.

    Looks at remote_type first (most reliable when populated by ATS sources),
    then falls back to keyword matches in the title and location strings.
    LinkedIn alert emails often pack the remote signal into the location field
    (e.g. "United States (Remote)"), so checking text is necessary.
    """
    if job.remote_type and job.remote_type.strip().lower() == "remote":
        return True
    haystack = f"{job.title or ''} {job.location or ''}".lower()
    return any(kw in haystack for kw in config.REMOTE_KEYWORDS)


def matches_allowed_city(job: JobPosting) -> bool:
    """True if the job's location contains one of ALLOWED_ONSITE_LOCATIONS."""
    loc = (job.location or "").lower()
    return any(city in loc for city in config.ALLOWED_ONSITE_LOCATIONS)


def passes_location_filter(job: JobPosting) -> bool:
    """Keep remote roles anywhere, or onsite/hybrid roles in an allowed city."""
    if is_remote_role(job):
        return True
    if matches_allowed_city(job):
        return True
    return False


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    """Return the subset of `keywords` that appear as whole words/phrases in
    `text` (case-insensitive, whole-word matched)."""
    if not text:
        return []
    low = text.lower()
    return [kw for kw in keywords if _word_match(low, kw)]


def count_core_stack_matches(text: str) -> list[str]:
    """Tier 1: tools and methods that signal stack alignment with your experience."""
    return _match_keywords(text, config.CORE_STACK_KEYWORDS)


def count_broad_skill_matches(text: str) -> list[str]:
    """Tier 2: broader signals that this is a data-analyst-shaped role in a relevant domain."""
    return _match_keywords(text, config.BROAD_SKILL_KEYWORDS)


def pre_filter(jobs: list[JobPosting]) -> list[JobPosting]:
    """Run title, location, and two-tier skill pre-filter.

    Order: title (cheapest) -> location (cheap) -> skill tiers (search the
    full description, so slightly costlier).

    LinkedIn and Indeed alert emails carry no description, so skill matching
    has nothing to work with. Those sources pass on title + location alone.
    Your LinkedIn alert settings are the de facto pre-filter for that source.

    A role with a description must pass:
      - At least MIN_CORE_STACK_MATCHES Tier 1 hits (tools you use)
      - At least MIN_BROAD_SKILL_MATCHES Tier 2 hits (broader signals)
    """
    survivors = []
    title_drops = 0
    location_drops = 0
    core_skill_drops = 0
    broad_skill_drops = 0

    for job in jobs:
        if not passes_title_filter(job.title):
            title_drops += 1
            continue

        if not passes_location_filter(job):
            location_drops += 1
            continue

        # Email sources have no description; trust title + location filter only
        if job.source in ("LinkedIn Email", "Indeed Email"):
            job.matched_skills = []
            survivors.append(job)
            continue

        haystack = f"{job.title} {job.description}"
        core_matched = count_core_stack_matches(haystack)
        broad_matched = count_broad_skill_matches(haystack)
        # Combine for visibility in Airtable / logging
        job.matched_skills = core_matched + broad_matched

        if len(core_matched) < config.MIN_CORE_STACK_MATCHES:
            core_skill_drops += 1
            continue

        if len(broad_matched) < config.MIN_BROAD_SKILL_MATCHES:
            broad_skill_drops += 1
            continue

        survivors.append(job)

    log.info(
        "Pre-filter: %d in, %d out (dropped %d on title, %d on location, "
        "%d on core stack, %d on broad skills)",
        len(jobs), len(survivors), title_drops, location_drops,
        core_skill_drops, broad_skill_drops,
    )
    return survivors
