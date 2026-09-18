import os
import re
from urllib.parse import urlparse

import requests


# ============================================================
# LEADERSHIP ROLES
# ============================================================

ROLE_REGEX = (
    r"founder|co[- ]founder|"
    r"ceo|cto|cfo|coo|cpo|"
    r"president|"
    r"vp|vice president|"
    r"chief executive officer|"
    r"chief technology officer|"
    r"chief financial officer|"
    r"chief operating officer|"
    r"chief product officer"
)

ROLE_PATTERN = re.compile(
    rf"\b({ROLE_REGEX})\b",
    re.IGNORECASE,
)


# ============================================================
# NAME VALIDATION
# ============================================================

NAME_PATTERN = re.compile(
    r"^[A-Z][a-zA-Z'’-]{1,30}"
    r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}$"
)


BAD_NAME_TERMS = {
    # leadership words
    "the",
    "founder",
    "founders",
    "cofounder",
    "co-founder",
    "ceo",
    "cto",
    "cfo",
    "coo",
    "cpo",
    "president",
    "vice",
    "vp",
    "chief",
    "executive",
    "officer",
    "leadership",

    # company / organization
    "company",
    "companies",
    "corporation",
    "corporate",
    "capital",
    "ventures",
    "venture",
    "fund",
    "funds",
    "group",
    "inc",
    "corp",
    "llc",
    "ltd",
    "limited",

    # common website words
    "team",
    "about",
    "contact",
    "pricing",
    "careers",
    "career",
    "resources",
    "community",
    "support",
    "customers",
    "customer",
    "partners",
    "partner",
    "developers",
    "developer",
    "platform",
    "platforms",
    "product",
    "products",
    "technology",
    "technologies",
    "software",
    "engineering",
    "development",
    "solutions",
    "services",
    "business",
    "marketing",
    "sales",
    "design",
    "growth",
    "global",
    "security",
    "data",
    "cloud",
    "api",
    "apis",

    # known false-positive words from crawled pages
    "base",
    "case",
    "chatbase",
    "rally",
    "join",
    "from",
    "pagerduty",
    "scores",
    "improved",
    "trusted",
    "provider",
    "optional",
    "integrate",
    "integration",
    "energy",
    "open",
    "source",
    "build",
    "building",
    "work",
    "users",
    "user",
    "people",
    "world",
    "future",
    "today",
    "modern",
    "leading",
    "better",
    "best",
    "more",
    "new",
    "next",
    "your",
    "our",
    "their",
    "they",
    "we",
    "you",
}


def valid_person_name(name):
    """
    Conservative person-name validation.

    False positives are worse than missing a person because
    the LLM should receive only plausible leadership candidates.
    """

    if not name:
        return False

    name = " ".join(name.strip().split())

    if "\n" in name or "\r" in name:
        return False

    if len(name) < 5 or len(name) > 60:
        return False

    if not NAME_PATTERN.fullmatch(name):
        return False

    words = name.split()

    if len(words) < 2 or len(words) > 4:
        return False

    lowered = {
        word.strip(".,'’-").lower()
        for word in words
    }

    if lowered.intersection(BAD_NAME_TERMS):
        return False

    if any(char.isdigit() for char in name):
        return False

    if any(
        len(word.strip(".,'’-")) < 2
        for word in words
    ):
        return False

    return True


def looks_like_person_name(name):
    return valid_person_name(name)


# ============================================================
# ROLE NORMALIZATION
# ============================================================

def normalize_role(role):
    if not role:
        return None

    role = " ".join(role.strip().split())
    key = role.lower()

    mapping = {
        "founder": "Founder",
        "cofounder": "Co-Founder",
        "co-founder": "Co-Founder",
        "co founder": "Co-Founder",

        "ceo": "CEO",
        "chief executive officer": "CEO",

        "cto": "CTO",
        "chief technology officer": "CTO",

        "cfo": "CFO",
        "chief financial officer": "CFO",

        "coo": "COO",
        "chief operating officer": "COO",

        "cpo": "CPO",
        "chief product officer": "CPO",

        "president": "President",
        "vp": "VP",
        "vice president": "VP",
    }

    return mapping.get(key, role)


# ============================================================
# LINKEDIN HELPERS
# ============================================================

def clean_linkedin_url(url):
    if not url:
        return None

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None

    hostname = parsed.netloc.lower()

    if hostname not in {
        "linkedin.com",
        "www.linkedin.com",
    }:
        return None

    path = parsed.path.rstrip("/")

    if not path.lower().startswith("/in/"):
        return None

    profile = path[4:].strip()

    if not profile:
        return None

    return f"https://www.linkedin.com/in/{profile}"


def is_linkedin_profile(url):
    return clean_linkedin_url(url) is not None


# ============================================================
# CANDIDATE CREATION
# ============================================================

def make_candidate(name, role, source_url):
    name = " ".join(name.strip().split())

    if not valid_person_name(name):
        return None

    if not role:
        return None

    return {
        "name": name,
        "role": normalize_role(role),
        "linkedin_url": None,
        "source_url": source_url,
    }


# ============================================================
# EXTRACT FROM "OUR FOUNDERS" SECTIONS
# ============================================================

def extract_founder_section(lines, source_url):
    """
    Handles layouts such as:

        Our Founders
        Abhinav Asthana
        Ankit Sobti
        Abhijit Kane

    Also handles names appearing immediately after the
    "Our Founders" heading.
    """

    candidates = []

    for i, line in enumerate(lines):

        if not re.search(
            r"\bour founders?\b",
            line,
            re.IGNORECASE,
        ):
            continue

        # ----------------------------------------------------
        # Look at the next few lines.
        # ----------------------------------------------------

        for offset in range(1, 6):

            index = i + offset

            if index >= len(lines):
                break

            candidate_line = lines[index]

            # Stop if another obvious section begins.
            if re.search(
                r"^(about|contact|pricing|careers|"
                r"products?|resources?|customers?|"
                r"team|leadership)$",
                candidate_line,
                re.IGNORECASE,
            ):
                break

            if len(candidate_line) > 80:
                continue

            if valid_person_name(candidate_line):

                candidate = make_candidate(
                    candidate_line,
                    "Founder",
                    source_url,
                )

                if candidate:
                    candidates.append(candidate)

    return candidates


# ============================================================
# EXPLICIT SENTENCE EXTRACTION
# ============================================================

def extract_explicit_sentences(lines, source_url):

    candidates = []

    for line in lines:

        if len(line) > 500:
            continue

        # ----------------------------------------------------
        # Pattern:
        #
        # Abhinav Asthana is the co-founder and CEO of Postman
        # ----------------------------------------------------

        pattern = re.compile(
            rf"\b("
            r"[A-Z][a-zA-Z'’-]{1,30}"
            r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
            rf")\s+"
            r"(?:is|was|serves as|served as|became)"
            r"\s+(?:the\s+|a\s+|an\s+)?"
            rf"[^.\n]{{0,80}}?"
            rf"\b({ROLE_REGEX})\b",
            re.IGNORECASE,
        )

        for match in pattern.finditer(line):

            name = match.group(1)
            role = match.group(2)

            candidate = make_candidate(
                name,
                role,
                source_url,
            )

            if candidate:
                candidates.append(candidate)

        # ----------------------------------------------------
        # Pattern:
        #
        # Abhinav Asthana, Postman's CEO and co-founder
        #
        # IMPORTANT:
        # Only accept this when possessive company context
        # exists.
        # ----------------------------------------------------

        pattern = re.compile(
            rf"\b("
            r"[A-Z][a-zA-Z'’-]{1,30}"
            r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
            rf")"
            r"\s*,\s*"
            r"[^.\n]{0,60}?"
            r"\b(?:[A-Z][a-zA-Z0-9_-]*'s)\s+"
            rf"({ROLE_REGEX})\b",
            re.IGNORECASE,
        )

        for match in pattern.finditer(line):

            name = match.group(1)
            role = match.group(2)

            candidate = make_candidate(
                name,
                role,
                source_url,
            )

            if candidate:
                candidates.append(candidate)

    return candidates


# ============================================================
# STRUCTURED NAME / ROLE EXTRACTION
# ============================================================

def extract_structured(lines, source_url):

    candidates = []

    for line in lines:

        if len(line) > 180:
            continue

        # ----------------------------------------------------
        # Name — Role
        # ----------------------------------------------------

        match = re.match(
            rf"^\s*("
            r"[A-Z][a-zA-Z'’-]{1,30}"
            r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
            r")"
            r"\s*[-–—:|]\s*"
            rf"({ROLE_REGEX})\s*$",
            line,
            re.IGNORECASE,
        )

        if match:

            candidate = make_candidate(
                match.group(1),
                match.group(2),
                source_url,
            )

            if candidate:
                candidates.append(candidate)

        # ----------------------------------------------------
        # Role — Name
        # ----------------------------------------------------

        match = re.match(
            rf"^\s*"
            rf"({ROLE_REGEX})"
            r"\s*[-–—:|]\s*"
            r"("
            r"[A-Z][a-zA-Z'’-]{1,30}"
            r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
            r")\s*$",
            line,
            re.IGNORECASE,
        )

        if match:

            candidate = make_candidate(
                match.group(2),
                match.group(1),
                source_url,
            )

            if candidate:
                candidates.append(candidate)

    return candidates


# ============================================================
# ADJACENT NAME / ROLE LAYOUT
# ============================================================

def extract_adjacent(lines, source_url):

    candidates = []

    for i in range(len(lines) - 1):

        first = lines[i]
        second = lines[i + 1]

        if len(first) > 80:
            continue

        if len(second) > 100:
            continue

        first_role = ROLE_PATTERN.fullmatch(
            first.strip()
        )

        second_role = ROLE_PATTERN.fullmatch(
            second.strip()
        )

        # ----------------------------------------------------
        # Name
        # CEO
        # ----------------------------------------------------

        if second_role and valid_person_name(first):

            candidate = make_candidate(
                first,
                second_role.group(1),
                source_url,
            )

            if candidate:
                candidates.append(candidate)

        # ----------------------------------------------------
        # CEO
        # Name
        # ----------------------------------------------------

        elif first_role and valid_person_name(second):

            candidate = make_candidate(
                second,
                first_role.group(1),
                source_url,
            )

            if candidate:
                candidates.append(candidate)

    return candidates


# ============================================================
# MAIN COMPANY-PAGE EXTRACTION
# ============================================================

def extract_names_from_text(text, source_url):

    if not text:
        return []

    lines = [
        " ".join(line.strip().split())
        for line in text.splitlines()
        if line.strip()
    ]

    candidates = []

    # 1. "Our Founders" sections
    candidates.extend(
        extract_founder_section(
            lines,
            source_url,
        )
    )

    # 2. Explicit sentences
    candidates.extend(
        extract_explicit_sentences(
            lines,
            source_url,
        )
    )

    # 3. Structured layouts
    candidates.extend(
        extract_structured(
            lines,
            source_url,
        )
    )

    # 4. Adjacent name / role layouts
    candidates.extend(
        extract_adjacent(
            lines,
            source_url,
        )
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique = []
    seen = set()

    for candidate in candidates:

        name = candidate.get(
            "name",
            "",
        ).strip()

        role = candidate.get(
            "role",
            "",
        ).strip()

        source = candidate.get(
            "source_url",
            "",
        ).strip()

        if not valid_person_name(name):
            continue

        if not role:
            continue

        key = (
            name.lower(),
            role.lower(),
            source,
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    return unique


# ============================================================
# DISCOVER FROM CRAWLED COMPANY PAGES
# ============================================================

def discover_from_company_pages(pages):

    results = []

    for page in pages:

        text = page.get(
            "text",
            "",
        )

        source_url = page.get(
            "url",
            "",
        )

        results.extend(
            extract_names_from_text(
                text,
                source_url,
            )
        )

    unique = []
    seen = set()

    for item in results:

        key = (
            item["name"].lower(),
            item["role"].lower(),
            item["source_url"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


# ============================================================
# TAVILY SEARCH
# ============================================================

def search_tavily(query):

    api_key = os.getenv(
        "TAVILY_API_KEY"
    )

    if not api_key:

        print(
            "[SEARCH] Tavily API key not configured; "
            "skipping external search."
        )

        return []

    try:

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
            },
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "results",
            [],
        )

    except Exception as exc:

        print(
            f"[SEARCH] Tavily search failed: {exc}"
        )

        return []


# ============================================================
# EXTERNAL LINKEDIN LEADERSHIP SEARCH
# ============================================================

def search_external_leadership(
    company_name,
    roles=None,
):
    """
    Optional external search.

    Compatible with:

        search_external_leadership(company_name)

    This does NOT invent people if Tavily is unavailable.
    """

    results = []

    if not company_name:
        return results

    if roles is None:
        roles = [
            "founder",
            "CEO",
            "CTO",
        ]

    for role in roles:

        query = (
            f'"{company_name}" '
            f'{role} LinkedIn'
        )

        print(
            f'[SEARCH] "{company_name}" '
            f'{role} LinkedIn'
        )

        search_results = search_tavily(
            query
        )

        for result in search_results:

            url = result.get(
                "url",
                "",
            )

            linkedin_url = clean_linkedin_url(
                url
            )

            if not linkedin_url:
                continue

            title = result.get(
                "title",
                "",
            ) or ""

            content = result.get(
                "content",
                "",
            ) or ""

            combined = (
                f"{title} {content}"
            )

            # ----------------------------------------------
            # Find a person name close to the searched role.
            # ----------------------------------------------

            patterns = [

                re.compile(
                    r"\b("
                    r"[A-Z][a-zA-Z'’-]{1,30}"
                    r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
                    r")\b"
                    r"[^.\n]{0,80}"
                    r"\b"
                    + re.escape(role)
                    + r"\b",
                    re.IGNORECASE,
                ),

                re.compile(
                    r"\b"
                    + re.escape(role)
                    + r"\b"
                    r"[^.\n]{0,80}"
                    r"\b("
                    r"[A-Z][a-zA-Z'’-]{1,30}"
                    r"(?:\s+[A-Z][a-zA-Z'’-]{1,30}){1,3}"
                    r")\b",
                    re.IGNORECASE,
                ),
            ]

            for pattern in patterns:

                for match in pattern.finditer(
                    combined
                ):

                    name = None

                    for group in match.groups():

                        if (
                            group
                            and valid_person_name(
                                group
                            )
                        ):
                            name = group
                            break

                    if not name:
                        continue

                    results.append(
                        {
                            "name": name,
                            "role": normalize_role(
                                role
                            ),
                            "linkedin_url": linkedin_url,
                            "source_url": url,
                        }
                    )

    unique = []
    seen = set()

    for item in results:

        key = (
            item["name"].lower(),
            item["role"].lower(),
            item["linkedin_url"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique

