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
    "Process Consultant",
    "Process Optimization Manager",
    "Process Specialist",
    "Process Optimization Specialist"
    "Process Improvement",
    "Process Optimization",
    "Process Improvement",
    "Process Optimization Lead",
    "Process Improvement Manager",
    "Process Improvement Lead",
    "Process Excellence Manager",
    "Process Transformation Lead",
    "Workflow Transformation Analyst",
    "Continuous Improvement Manager",
    "Operations Program Manager",
    "Operations Enablement Manager",
    "Delivery Operations Manager",
    "Business Operations Manager",
    "Business Process Manager",
    "Program Manager Operations",
    "Senior Program Manager",
    "Operational Excellence Manager",
    "Operational Excellence Lead",
    "Customer Operations Manager",
    "People Process Optimization Specialist",
    "Six Sigma Program Manager"
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
    "fraud",
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
    # continuous process improvement stack (example)
    "Continuous Process Improvement",
    "continuous improvement",
    "Process Optimization",
    "Process Transformation",
    "Workflow Design",
    "Operating Model Design",
    "Workflow Architecture",
    "Business Process Redesign",
    "Cross-Functional Program Management",
    "Lean Six Sigma Black Belt",
    "DMAIC",
    "FMEA",
    "SIPOC",
    "Value Stream Mapping",
    "Kaizen",
    "Root Cause Analysis",
    "Operational Excellence",
    "Control Plans",
    "Waste Elimination",
    "AI-Native Workflow Design",
    "AI-Enabled Workflows",
    "Workflow Automation",

]
MIN_CORE_STACK_MATCHES = 1

BROAD_SKILL_KEYWORDS = [
    # overall
    "KPI Development",
    "Experiment Governance",
    "Operational Readiness",
    "Impact Modeling",
    "Process Documentation",
    "Agentic AI",
    "Generative AI",
    "Prompt Engineering",
    "AI Governance",
    "Support Automation",
    "Process Digitization",
    "Automation Strategy",
    "Intelligent Process Automation",
    "Business Operations",
    "Operations Strategy",
    "Process Excellence",
    "Product Operations",
    "Strategic Planning",
    "Global Operations",
    "Scaled Operations",
    "Data-Driven Decision Making",
    "Analytics & Reporting",
    "Voice of Customer",
    "Customer Experience",
    "Agile",
    "Scrum",
    "Tableau",
    "Salesforce",
    "Zendesk",
    "Snowflake",
    "SQL",
    "Jira",
    "Lucidchart",
    "Airtable",
    "Smartsheet",
    "Confluence",
    "analysis",
    "data analysis",
    "sql",
    "data",

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
    "nashville",
]

# Substrings that count as a remote signal when found in the title or location string.
REMOTE_KEYWORDS = [
    "remote",
    "anywhere",
    "work from home",
    "wfh",
    "distributed",
    "fully remote",
    "hybrid",
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
    # Health/Wellness
    ("Whoop", "greenhouse", "whoop"),                   # [?]
    ("Oura", "greenhouse", "oura"),                     # [?]
    ("Eight Sleep", "ashby", "eightsleep"),             # [?]
    ("Headspace", "greenhouse", "hs"),                  # [?]
    ("Calm", "greenhouse", "calm"),                     # [?]
    ("Strava", "ashby", "strava"),                      # [?]

    # Tech / SaaS
    ("Linear", "ashby", "linear"),                      # [ok]
    ("Vercel", "greenhouse", "vercel"),                 # [ok]
    ("Datadog", "greenhouse", "datadog"),               # [ok]
    ("dbt Labs", "greenhouse", "dbtlabsinc"),           # [?]
    ("HubSpot", "greenhouse", "hubspot"),               # [ok]
    ("Asana", "greenhouse", "asana"),                   # [ok]
    ("Anthropic", "greenhouse", "anthropic"),           # [ok]
    ("OpenAI", "ashby", "openai"),                      # [ok]
    ("Airtable", "greenhouse", "airtable"),             # [?]
    ("Superhuman", "ashby", "superhuman"),              # [?]
    ("Reddit", "greenhouse", "reddit"),                 # [ok]

    # Education / Learning
    ("Teachable", "lever", "teachable"),                # [?]
    ("Maven", "ashby", "maven"),                        # [?]
    ("Brilliant", "greenhouse", "brilliant"),           # [?]
    ("Skillshare", "greenhouse", "skillshare"),         # [?]
    ("Outschool", "greenhouse", "outschool"),           # [?]
    ("Coursera", "workday", "coursera"),                # [?]
    
    # Creator tools / Design
    ("Canva", "greenhouse", "canva"),                   # [?]
    ("Loom", "greenhouse", "loom"),                     # [?]
    ("Descript", "ashby", "descript"),                  # [?]
    ("Framer", "ashby", "framer"),                      # [?]
    ("Gamma", "ashby", "gamma"),                        # [?]
    ("Miro", "greenhouse", "miro"),                     # [?]
    ("Runway ML", "ashby", "runway-ml"),                # [?]
    ("Pitch", "greenhouse", "pitch"),                   # [?]
    ("Rive", "ashby", "rive"),                          # [?]
    ("Spline", "ashby", "spline"),                      # [?]
    ("Pika Labs", "ashby", "pika"),                     # [?]
    ("Lucidchart", "greenhouse", "lucidchart"),         # [?]

    # Travel / Hospitality
    ("Hipcamp", "lever", "hipcamp"),                    # [?]
    ("AllTrails", "greenhouse", "alltrails"),           # [?]
    ("Navan", "greenhouse", "navan"),                   # [?]
    ("Hopper", "greenhouse", "hopper"),                 # [?]
    ("Going", "ashby", "going"),                        # [?]

    # Healthtech
    ("Oscar Health", "greenhouse", "oscar"),            # [ok]
    ("Headway", "ashby", "headway"),                    # [ok]
    ("Hims", "ashby", "hims-and-hers"),                 # [ok]
    ("Ro", "lever", "ro"),                              # [ok]
    ("Cedar", "greenhouse", "careportalinc"),           # [ok]

    # E-commerce / Retail
    ("Faire", "greenhouse", "faire"),                   # [ok]
    ("Klaviyo", "greenhouse", "klaviyo"),               # [ok]

    # Ops / Analytics-heavy
    ("Carta", "greenhouse", "carta"),                   # [ok]
    ("Gusto", "greenhouse", "gusto"),                   # [ok]
    ("Vanta", "ashby", "vanta"),                        # [ok]
    ("Scale AI", "greenhouse", "scaleai"),              # [ok]

    # Climate / Sustainability
    ("Overstory", "greenhouse", "overstory"),           # [?]
    ("Watershed", "ashby", "watershed"),                # [?]
    ("Arcadia", "greenhouse", "arcadiacareers"),        # [?]
    ("Pachama", "lever", "pachama"),                    # [?]
    ("Rubicon Carbon", "greenhouse", "rubicon-carbon"), # [?]
    ("Raptor Maps", "lever", "raptormaps"),             # [?]
    ("Rewiring America", "greenhouse", "rewiring-america"), # [?]
    ("Palmetto", "greenhouse", "palmetto"),             # [?]
    ("Crusoe Energy", "lever", "crusoe"),               # [?]
    ("Xpansiv", "greenhouse", "xpansiv"),               # [?]
    ("Banyan Infrastructure", "greenhouse", "banyan-infrastructure"), # [?]
]

# -----------------------------------------------------------------------------
# Gmail search queries for alert-email parsing.
# These are passed straight to Gmail's search. The defaults match the standard
# "from" addresses LinkedIn and Indeed use for job-alert emails.
# -----------------------------------------------------------------------------
GMAIL_LINKEDIN_QUERY = 'from:jobalerts-noreply@linkedin.com'
GMAIL_INDEED_QUERY = 'from:alert@indeed.com OR from:noreply@indeed.com'
