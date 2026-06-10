"""
Configuration for the job pipeline.

================================================================================
THIS IS THE ONLY FILE YOU NORMALLY NEED TO EDIT.
================================================================================
Everything here controls what the pipeline considers a "fit": which job titles
to look for, which skills/tools matter, which locations are acceptable, and
which companies to poll. The values below are a working EXAMPLE aimed at a
senior data-analyst search. Replace them with whatever fits the roles you want.

Nothing sensitive lives here. API keys and passwords are read from environment
variables (see README.md / SETUP.md), never from this file.
"""

# How far back to look for new postings (in days).
# With daily runs, a 1-day lookback covers everything that arrived since
# yesterday's run. If a run is ever skipped, jobs from that day are missed.
LOOKBACK_DAYS = 1

# -----------------------------------------------------------------------------
# Target role titles - matched (whole-word) against the job title.
# A title only needs to match ONE of these to pass the title filter.
# EDIT THIS LIST to the titles you actually want.
# -----------------------------------------------------------------------------
TARGET_TITLES = [
    # Senior Data Analyst (and Sr/Lead/Staff/Principal variants)
    "senior data analyst",
    "sr data analyst",
    "sr. data analyst",
    "lead data analyst",
    "staff data analyst",
    "principal data analyst",

    # Analytics Engineer (any level)
    "analytics engineer",

    # Data Scientist (rely on EXCLUDE below to filter junior/entry)
    "data scientist",

    # Specialty Senior Analyst tracks
    "senior product analyst",
    "sr product analyst",
    "sr. product analyst",
    "senior business analyst",
    "sr business analyst",
    "sr. business analyst",
    "senior operations analyst",
    "sr operations analyst",
    "sr. operations analyst",
    "senior insights analyst",
    "sr insights analyst",
    "sr. insights analyst",

    # Strategy / Operations Analyst
    "strategy and operations",
    "strategy & operations",
    "strategy analyst",

    # Fraud / Risk / Disputes specialist tracks (example domain, edit freely)
    "fraud analyst",
    "senior fraud analyst",
    "sr fraud analyst",
    "disputes specialist",
    "disputes analyst",

    # Manager tracks
    "analytics manager",
    "insights manager",
    "data analytics manager",
    "continuous improvement analyst",
    "continuous improvement manager",
]

# -----------------------------------------------------------------------------
# Auto-exclude: if any of these terms appear in the title, drop the role.
# Runs AFTER target match, so a role like "Senior Sales Analyst" is excluded
# even if it superficially matches "senior analyst".
#
# Terms are matched with whole-word logic (see filter.py _word_match), not bare
# substrings, so single words like "sales" or "chief" won't match inside other
# words. EDIT THIS LIST to fit the levels and functions you want to avoid.
# -----------------------------------------------------------------------------
EXCLUDE_TITLE_TERMS = [
    # Junior levels
    "junior",
    "jr",
    "entry-level",
    "entry level",
    "intern",      # matches "intern"; "internal" is a separate word under whole-word matching

    # Executive levels (above where this example search is aimed)
    "director",
    "vp",
    "vice president",
    "head of",
    "c-suite",
    "chief",

    # Wrong functions
    "sales",
    "engineering manager",
    "software engineer",
    "ml engineer",
    "machine learning engineer",
    "research scientist",
]

# -----------------------------------------------------------------------------
# Two-tier skill filter.
#
# Tier 1 (CORE_STACK_KEYWORDS): the specific tools/methods that signal a role is
# really in your wheelhouse. A role must mention AT LEAST ONE of these. This is
# what prevents jobs at companies with a totally different stack from passing
# just because they say "SQL" and "stakeholder."
#
# Tier 2 (BROAD_SKILL_KEYWORDS): general signals that the role is genuinely
# data-analyst shaped (domain terms, methodologies, modern AI awareness).
# A role must hit AT LEAST MIN_BROAD_SKILL_MATCHES of these.
#
# Both tiers must pass. Generic terms like "stakeholder", "cross-functional",
# "kpi", and "dashboard" are deliberately NOT here because they appear in every
# analyst posting and provide no filtering signal.
#
# EDIT THESE LISTS to the tools and signals on your own resume. The example
# values below cover a modern analytics stack PLUS common enterprise BI tools
# (Power BI, SQL Server, SAS, Qlik) so cross-industry roles aren't dropped just
# for being on a different stack.
#
# WHOLE-WORD-MATCH CAUTION: filter.py matches keywords as whole words/phrases.
# Short tokens can still be risky if written as bare substrings, so some terms
# below are written as longer phrases (e.g. "sas programming" rather than bare
# "sas", which would otherwise match inside "Kansas"/"SaaS"). Keep that in mind
# if you add short keywords of your own.
# -----------------------------------------------------------------------------
CORE_STACK_KEYWORDS = [
    # Modern analytics/data stack (example)
    "snowflake",
    "looker",
    "lookml",
    "tableau",
    "dbt",
    "airflow",
    "lean six sigma",
    "dmaic",
    # "mode" matches only as a standalone word (not inside "model"/"modern").
    "mode",
    # Enterprise BI/analytics tools (cross-industry peers of the stack above)
    "power bi",
    "powerbi",
    "sql server",
    "qlik",
    "sas programming",  # phrased to avoid matching "Kansas"/"SaaS"; do NOT shorten to bare "sas"
    "base sas",         # common posting phrasing for the SAS language
]
MIN_CORE_STACK_MATCHES = 1

BROAD_SKILL_KEYWORDS = [
    # SQL is broad but expected; a reasonable Tier 2 signal, not a Tier 1 differentiator
    "sql",
    "etl",
    "elt",
    "data warehouse",
    "data model",
    "semantic layer",
    # Domain terms (example: fintech/payments). Swap for your own industry
    "fraud",
    "risk",
    "disputes",
    "chargeback",
    # Methodology
    "experimentation",
    "a/b test",
    "ab test",
    "hypothesis test",
    "root cause",
    "continuous improvement",
    "process improvement",
    # Statistical process control / quality (strong cross-industry signal:
    # manufacturing, healthcare, operations)
    "statistical process control",
    "control chart",
    "spc",              # short, but low collision risk; watch the logs on the first run
    "kaizen",
    "six sigma",
    "data governance",
    "data quality",
    # Ingestion / pipeline tooling
    "fivetran",
    # Modern AI awareness
    "generative ai",
    "llm",
    "agentic",
    "prompt engineering",
    "openai",
    "anthropic",
    "claude",
    "chatgpt",
    # Self-serve / democratization
    "self-serve",
    "data democratization",
    "data literacy",
]
MIN_BROAD_SKILL_MATCHES = 3

# -----------------------------------------------------------------------------
# Location filter
# -----------------------------------------------------------------------------
# A role passes the location filter if ANY of these are true:
#   1. The role is remote (signal found in title, location, or remote_type)
#   2. The role's location contains one of ALLOWED_ONSITE_LOCATIONS (case-insensitive)
# Onsite or hybrid roles outside those locations are dropped.
#
# >>> EDIT THIS <<< Replace "chicago" with your own city (lowercase). You can
# list more than one, e.g. ["chicago", "milwaukee"]. To keep ONLY remote roles
# and drop all onsite/hybrid, set this to an empty list: []
ALLOWED_ONSITE_LOCATIONS = [
    "chicago",
]

# Substrings that count as a remote signal when found in the title or location string.
REMOTE_KEYWORDS = [
    "remote",
    "anywhere",
    "work from home",
    "wfh",
    "distributed",
    "fully remote",
]

# -----------------------------------------------------------------------------
# Target companies for ATS polling.
# Format: (display_name, ats, slug)
# - display_name: how it appears in Airtable
# - ats: 'greenhouse' | 'lever' | 'ashby' | 'smartrecruiters'
# - slug: the company's ATS path slug (the part after the ATS domain in the
#         company's careers-page URL)
#
# This is an EXAMPLE starter list. Add/remove companies you care about. Find a
# company's slug from its careers page URL:
#   Greenhouse:       boards.greenhouse.io/<slug>
#   Lever:            jobs.lever.co/<slug>
#   Ashby:            jobs.ashbyhq.com/<slug>
#   SmartRecruiters:  jobs.smartrecruiters.com/<slug>
#
# Status legend in comments (from prior runs):
#   [ok]    = verified returning postings
#   [fixed] = slug or ATS corrected after a 404
#   [?]     = unverified guess; will just log a 404 if wrong, no harm
# -----------------------------------------------------------------------------
TARGET_COMPANIES = [
    # Fintech / Payments
    ("Stripe", "greenhouse", "stripe"),                  # [ok]
    ("Plaid", "lever", "plaid"),                         # [fixed] was Greenhouse, actually on Lever
    ("Mercury", "ashby", "mercury"),                     # [ok]
    ("Brex", "greenhouse", "brex"),                      # [ok]
    ("Ramp", "ashby", "ramp"),                           # [ok]
    ("Chime", "greenhouse", "chime"),                    # [ok]
    ("Affirm", "greenhouse", "affirm"),                  # [ok]
    ("Robinhood", "greenhouse", "robinhood"),            # [ok]
    ("Marqeta", "greenhouse", "marqeta"),                # [ok]
    ("Modern Treasury", "ashby", "moderntreasury"),      # [fixed] moved from Greenhouse to Ashby

    # Tech / SaaS
    ("Notion", "ashby", "notion"),                       # [ok]
    ("Linear", "ashby", "linear"),                       # [ok]
    ("Vercel", "greenhouse", "vercel"),                  # [ok]
    ("Datadog", "greenhouse", "datadog"),                # [ok]
    ("dbt Labs", "greenhouse", "dbtlabsinc"),            # [?]
    ("HubSpot", "greenhouse", "hubspot"),                # [ok]
    ("Asana", "greenhouse", "asana"),                    # [ok]
    ("Figma", "greenhouse", "figma"),                    # [ok]
    ("Anthropic", "greenhouse", "anthropic"),            # [ok]
    ("OpenAI", "ashby", "openai"),                       # [fixed] was Greenhouse, actually on Ashby

    # SmartRecruiters
    ("Atlassian", "smartrecruiters", "atlassian"),       # [fixed] moved from Lever (returned 0) to SmartRecruiters
    ("Visa", "smartrecruiters", "visa"),                 # [?] verified slug; first run will confirm
    ("McDonald's Corporation", "smartrecruiters", "mcdonaldscorporation"),  # [?] verified slug; first run will confirm

    # Marketplaces / Consumer
    ("DoorDash", "greenhouse", "doordashusa"),           # [fixed] slug is "doordashusa" not "doordash"
    ("Instacart", "greenhouse", "instacart"),            # [ok]
    ("Lyft", "greenhouse", "lyft"),                      # [ok]
    ("Airbnb", "greenhouse", "airbnb"),                  # [ok]
    ("Pinterest", "greenhouse", "pinterest"),            # [ok]
    ("Reddit", "greenhouse", "reddit"),                  # [ok]

    # Healthtech
    ("Oscar Health", "greenhouse", "oscar"),             # [ok]
    ("Headway", "ashby", "headway"),                     # [ok]
    ("Hims", "ashby", "hims-and-hers"),                  # [fixed] moved from Greenhouse to Ashby
    ("Ro", "lever", "ro"),                               # [fixed] on Lever as "ro"
    ("Cedar", "greenhouse", "careportalinc"),            # [fixed] on Greenhouse as "careportalinc"

    # E-commerce / Retail
    ("Faire", "greenhouse", "faire"),                    # [ok]
    ("Klaviyo", "greenhouse", "klaviyo"),                # [ok]

    # Ops / Analytics-heavy
    ("Carta", "greenhouse", "carta"),                    # [ok]
    ("Gusto", "greenhouse", "gusto"),                    # [?] may be on its own ATS now
    ("Vanta", "ashby", "vanta"),                         # [ok]
    ("Scale AI", "greenhouse", "scaleai"),               # [fixed] was Ashby, actually on Greenhouse
]

# -----------------------------------------------------------------------------
# Gmail search queries for alert-email parsing.
# These are passed straight to Gmail's search. The defaults match the standard
# "from" addresses LinkedIn and Indeed use for job-alert emails.
# -----------------------------------------------------------------------------
GMAIL_LINKEDIN_QUERY = 'from:jobalerts-noreply@linkedin.com'
GMAIL_INDEED_QUERY = 'from:alert@indeed.com OR from:noreply@indeed.com'
