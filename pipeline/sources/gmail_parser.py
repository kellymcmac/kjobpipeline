"""
Gmail alert email parser via IMAP.

Uses Gmail's IMAP server with an App Password for auth. No Google Cloud
project, no OAuth flow.

Setup:
  1. Enable 2-Step Verification on your Google account
  2. Go to https://myaccount.google.com/apppasswords
  3. Create an app password (e.g. "curious_squid")
  4. Set these GitHub secrets:
       GMAIL_ADDRESS       - your gmail address
       GMAIL_APP_PASSWORD  - the 16-character app password (no spaces)
"""

import email as email_lib
import imaplib
import logging
import re
from datetime import date
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from ..models import JobPosting

log = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


# ============================================================================
# IMAP transport
# ============================================================================

def connect(email_address: str, app_password: str) -> imaplib.IMAP4_SSL:
    """Connect to Gmail IMAP and select INBOX read-only."""
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(email_address, app_password)
    conn.select("INBOX", readonly=True)
    return conn


def search_messages(conn, gmail_query: str, lookback_days: int) -> list[bytes]:
    """Search using Gmail's X-GM-RAW extension so the query supports
    Gmail's native search operators (from:, OR, newer_than:, etc.)."""
    full_query = f"{gmail_query} newer_than:{lookback_days}d"
    typ, data = conn.search(None, "X-GM-RAW", f'"{full_query}"')
    if typ != "OK":
        log.warning("IMAP search returned %s for %r", typ, full_query)
        return []
    if not data or not data[0]:
        return []
    return data[0].split()


def fetch_message(conn, msg_id: bytes) -> tuple[str, str, date | None]:
    """Return (html_body, plain_body, received_date) for a single message."""
    typ, data = conn.fetch(msg_id, "(RFC822)")
    if typ != "OK" or not data or not data[0]:
        return "", "", None
    raw = data[0][1]
    msg = email_lib.message_from_bytes(raw)

    received = None
    date_hdr = msg.get("Date")
    if date_hdr:
        try:
            received = parsedate_to_datetime(date_hdr).date()
        except Exception:
            pass

    html = ""
    plain = ""
    for part in msg.walk():
        ctype = part.get_content_type()
        if ctype == "text/html" and not html:
            payload = part.get_payload(decode=True)
            if payload:
                html = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        elif ctype == "text/plain" and not plain:
            payload = part.get_payload(decode=True)
            if payload:
                plain = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
    return html, plain, received


# ============================================================================
# LinkedIn alert email parsing (uses text/plain body)
# ============================================================================
#
# LinkedIn digest emails have a much cleaner text/plain part than HTML.
# Each job block in the plain body looks like:
#
#   <title>
#   <company>
#   <location>
#
#   <optional badge: "This company is actively hiring" / "Fast growing" /
#                    "Actively recruiting" / "N company alum" / etc.>
#   View job: https://www.linkedin.com/comm/jobs/view/<JOB_ID>/?...
#
#   ---------------------------------------------------------
#
# Blocks are separated by a long dashed line. The first block also contains
# the digest header ("Your job alert for X", "New jobs match your preferences");
# the last block has the footer ("See all jobs on LinkedIn", copyright, etc).

LINKEDIN_VIEW_URL = re.compile(
    r"View job:\s*(https://www\.linkedin\.com/comm/jobs/view/(\d+)/[^\s]*)"
)
LINKEDIN_SEPARATOR = re.compile(r"-{30,}")
LINKEDIN_HEADER_PREFIXES = (
    "your job alert",
    "new jobs",
    "see all jobs",
)
LINKEDIN_BADGE_LINES = {
    "this company is actively hiring",
    "actively recruiting",
    "fast growing",
}
LINKEDIN_ALUM_RE = re.compile(
    r"^\s*\d+\s+(company|school)\s+alum", re.IGNORECASE
)


def parse_linkedin_email(
    html: str, plain: str, received: date | None
) -> list[JobPosting]:
    """Parse a LinkedIn job alert digest email using the text/plain body."""
    if not plain:
        return []

    blocks = LINKEDIN_SEPARATOR.split(plain)
    jobs: list[JobPosting] = []
    seen_ids: set[str] = set()

    for block in blocks:
        url_match = LINKEDIN_VIEW_URL.search(block)
        if not url_match:
            continue

        job_id = url_match.group(2)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        # Lines before the "View job:" line are title / company / location,
        # possibly preceded by a header (first block only) and followed by a
        # badge line.
        pre_url = block[: url_match.start()]
        raw_lines = [ln.strip() for ln in pre_url.split("\n") if ln.strip()]

        content: list[str] = []
        for line in raw_lines:
            low = line.lower()
            if any(low.startswith(p) for p in LINKEDIN_HEADER_PREFIXES):
                continue
            if low in LINKEDIN_BADGE_LINES:
                continue
            if LINKEDIN_ALUM_RE.search(line):
                continue
            content.append(line)

        if len(content) < 2:
            continue

        # The last three filtered lines are title / company / location.
        # If only two remain, location is unknown.
        if len(content) >= 3:
            title, company, location = content[-3], content[-2], content[-1]
        else:
            title, company, location = content[-2], content[-1], ""

        jobs.append(
            JobPosting(
                title=title,
                company=company,
                source="LinkedIn Email",
                url=f"https://www.linkedin.com/jobs/view/{job_id}/",
                job_id=job_id,
                location=location,
                remote_type=_infer_remote(location),
                salary_range="N/A",
                description="",
                posted_date=received,
            )
        )

    return jobs


# ============================================================================
# Indeed alert email parsing
# ============================================================================

INDEED_JOB_LINK = re.compile(r"jk=([a-f0-9]+)", re.IGNORECASE)


def parse_indeed_email(
    html: str, plain: str, received: date | None
) -> list[JobPosting]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    seen_ids = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        m = INDEED_JOB_LINK.search(href)
        if not m:
            continue
        job_id = m.group(1)
        if job_id in seen_ids:
            continue

        title = link.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        if any(skip in title.lower() for skip in ["unsubscribe", "view all", "see more"]):
            continue

        seen_ids.add(job_id)
        company, location, salary = _extract_indeed_context(link)

        jobs.append(JobPosting(
            title=title,
            company=company,
            source="Indeed Email",
            url=f"https://www.indeed.com/viewjob?jk={job_id}",
            job_id=job_id,
            location=location,
            remote_type=_infer_remote(location),
            salary_range=salary or "N/A",
            description="",
            posted_date=received,
        ))
    return jobs


def _extract_indeed_context(link) -> tuple[str, str, str]:
    container = link.find_parent("td") or link.find_parent("div") or link.parent
    if not container:
        return "", "", ""
    title_text = link.get_text(strip=True)
    texts = [t.strip() for t in container.stripped_strings if t.strip() and t != title_text]
    company = texts[0] if texts else ""
    location = texts[1] if len(texts) > 1 else ""
    salary = ""
    for t in texts[2:6]:
        if "$" in t:
            salary = t
            break
    return company, location, salary


def _infer_remote(location: str) -> str:
    if not location:
        return ""
    low = location.lower()
    if "remote" in low and "hybrid" not in low:
        return "Remote"
    if "hybrid" in low:
        return "Hybrid"
    return "Onsite"


# ============================================================================
# Public entrypoint
# ============================================================================

def fetch_all(
    email_address: str,
    app_password: str,
    linkedin_query: str,
    indeed_query: str,
    lookback_days: int,
) -> list[JobPosting]:
    """Fetch and parse jobs from LinkedIn and Indeed alert emails via IMAP."""
    try:
        conn = connect(email_address, app_password)
    except imaplib.IMAP4.error as e:
        log.error("Gmail IMAP login failed: %s. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD.", e)
        return []
    except Exception as e:
        log.error("Could not connect to Gmail IMAP: %s", e)
        return []

    all_jobs = []
    try:
        for label, query, parser in (
            ("LinkedIn", linkedin_query, parse_linkedin_email),
            ("Indeed", indeed_query, parse_indeed_email),
        ):
            try:
                msg_ids = search_messages(conn, query, lookback_days)
            except Exception as e:
                log.warning("%s gmail search failed: %s", label, e)
                continue

            log.info("%s: %d alert emails in lookback window", label, len(msg_ids))
            label_count = 0
            for msg_id in msg_ids:
                try:
                    html, plain, received = fetch_message(conn, msg_id)
                    jobs = parser(html, plain, received)
                    all_jobs.extend(jobs)
                    label_count += len(jobs)
                except Exception as e:
                    log.warning("%s message %r failed: %s", label, msg_id, e)
            log.info("%s: parsed %d job postings", label, label_count)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            conn.logout()
        except Exception:
            pass

    return all_jobs
