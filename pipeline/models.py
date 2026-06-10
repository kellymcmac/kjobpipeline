"""Data classes for job postings."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .location import parse_location


@dataclass
class JobPosting:
    """A single job posting from any source."""
    title: str
    company: str
    source: str  # 'LinkedIn Email' | 'Indeed Email' | 'Greenhouse' | 'Lever' | 'Ashby' | 'SmartRecruiters'
    url: str
    job_id: str = ""
    location: str = ""
    remote_type: str = ""  # 'Remote' | 'Hybrid' | 'Onsite' | ''
    salary_range: str = "N/A"
    description: str = ""
    posted_date: Optional[date] = None
    matched_skills: list = field(default_factory=list)
    match_score: int = 0
    # Parsed location fields, populated automatically in __post_init__
    city: str = ""
    state: str = ""
    country: str = ""
    region: str = ""

    def __post_init__(self):
        # Skip parsing if these were already set explicitly by the caller
        if not (self.city or self.state or self.country or self.region):
            parsed = parse_location(self.location, self.remote_type)
            self.city = parsed.city
            self.state = parsed.state
            self.country = parsed.country
            self.region = parsed.region

    def dedup_keys(self) -> dict:
        """Keys this posting can be deduped against."""
        return {
            "url": (self.url or "").strip().lower(),
            "source_id": (self.source, self.job_id) if self.job_id else None,
            "fuzzy": (
                _normalize(self.company),
                _normalize(self.title),
            ),
        }


def _normalize(s: str) -> str:
    """Lowercase, strip, collapse whitespace for fuzzy matching."""
    if not s:
        return ""
    return " ".join(s.lower().split())
