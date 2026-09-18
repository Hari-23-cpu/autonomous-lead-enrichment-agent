from urllib.parse import urlparse

from app.crawler import crawl_domain
from app.content_cleaner import clean_html
from app.deterministic_extractor import (
    extract_emails,
    extract_linkedin_urls,
)
from app.extractor import extract_company_data
from app.search import (
    discover_from_company_pages,
    search_external_leadership,
)
from app.schemas import (
    ContactPoint,
    TeamMember,
)


GENERIC_EMAIL_PREFIXES = {
    "info",
    "hello",
    "contact",
    "sales",
    "support",
    "admin",
    "office",
    "team",
    "enquiries",
    "inquiries",
    "general",
}

SPECIALIZED_EMAIL_PREFIXES = {
    "privacy",
    "legal",
    "security",
    "infosec",
    "talent",
    "careers",
    "jobs",
    "hr",
    "press",
    "media",
    "billing",
    "abuse",
    "dpo",
    "compliance",
}


LEADERSHIP_ROLE_KEYWORDS = {
    "founder",
    "co-founder",
    "cofounder",
    "ceo",
    "chief executive officer",
    "cto",
    "chief technology officer",
    "cpo",
    "chief product officer",
    "coo",
    "chief operating officer",
    "cfo",
    "chief financial officer",
    "president",
    "vice president",
    "vp",
}


FORBIDDEN_TERMS = {
    "investor",
    "investors",
    "partner",
    "partners",
    "customer",
    "customers",
    "client",
    "clients",
    "advisor",
    "advisors",
    "advisory",
    "community",
    "speaker",
    "speakers",
    "author",
    "authors",
    "ambassador",
    "consultant",
    "consultants",
}


BAD_NAME_TERMS = {
    "the",
    "founders",
    "founder",
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
    "team",
    "leadership",
    "company",
    "capital",
    "ventures",
    "venture",
    "fund",
    "funds",
    "base",
    "case",
    "chatbase",
    "rally",
    "join",
    "from",
    "pagerduty",
    "scores",
    "improved",
    "software",
    "development",
    "trusted",
    "provider",
    "customer",
    "customers",
    "platform",
    "optional",
    "solutions",
    "integrate",
    "integration",
    "engineering",
    "product",
    "technology",
    "technologies",
    "business",
    "services",
    "global",
    "growth",
    "marketing",
    "sales",
    "design",
    "energy",
    "inc",
    "corp",
    "corporation",
    "llc",
    "ltd",
    "limited",
    "group",
    "database",
    "authentication",
    "developer",
    "developers",
    "documentation",
    "pricing",
    "privacy",
    "security",
    "support",
    "community",
    "partnership",
    "partnerships",
    "indemnitee",
    "subscriber",
    "router",
    "chatbot",
    "scaled",
    "unified",
    "managed",
    "remedy",
    "service",
    "services",
    "policy",
}


def normalize_domain(domain: str):
    if not domain:
        return ""

    domain = domain.strip()

    if "://" in domain:
        parsed = urlparse(domain)
        domain = parsed.hostname or domain

    domain = domain.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain.rstrip("/")


def get_value(item):
    if isinstance(item, dict):
        return (
            item.get("email")
            or item.get("url")
            or item.get("linkedin_url")
            or ""
        )

    return str(item)


def unique_values(items):
    output = []
    seen = set()

    for item in items:
        value = get_value(item).strip().lower()

        if not value:
            continue

        if value in seen:
            continue

        seen.add(value)
        output.append(item)

    return output


def is_generic_email(email: str):
    email = email.strip().lower()

    if "@" not in email:
        return False

    local = email.split("@", 1)[0]

    if local in SPECIALIZED_EMAIL_PREFIXES:
        return False

    return local in GENERIC_EMAIL_PREFIXES


def collect_emails(pages):
    emails = []
    evidence = {}

    for page in pages:
        url = page["url"]
        text = page["text"]

        try:
            found = extract_emails(
                text,
                url,
            )
        except Exception as exc:
            print(
                f"[WARNING] Email extraction failed "
                f"for {url}: {exc}"
            )
            continue

        for item in found:
            email = get_value(item).strip().lower()

            if not email:
                continue

            if not is_generic_email(email):
                continue

            if email not in evidence:
                evidence[email] = url

            emails.append(email)

    return (
        unique_values(emails),
        evidence,
    )


def collect_linkedin(pages):
    urls = []

    for page in pages:
        url = page["url"]
        text = page["text"]

        try:
            found = extract_linkedin_urls(
                text,
                url,
            )
        except Exception as exc:
            print(
                f"[WARNING] LinkedIn extraction failed "
                f"for {url}: {exc}"
            )
            continue

        for item in found:
            value = get_value(item).strip()

            if "linkedin.com/in/" not in value.lower():
                continue

            urls.append(value.rstrip("/"))

    return unique_values(urls)


def build_context(pages):
    sections = []

    for page in pages:
        url = page["url"]
        text = page["text"]

        if not text:
            continue

        sections.append(
            f"""
==================================================
SOURCE URL: {url}
==================================================

{text}
"""
        )

    return "\n".join(sections)[:50000]


def company_name_from_domain(domain):
    value = domain.split(".")[0]
    return value.title()


def valid_role(role):
    if not role:
        return False

    role_lower = role.lower().strip()

    for forbidden in FORBIDDEN_TERMS:
        if forbidden in role_lower:
            return False

    return any(
        keyword in role_lower
        for keyword in LEADERSHIP_ROLE_KEYWORDS
    )


def valid_person_name(name):
    if not name:
        return False

    name = " ".join(name.strip().split())

    if "\n" in name or "\r" in name:
        return False

    if len(name) < 5 or len(name) > 60:
        return False

    words = name.lower().split()

    if len(words) < 2 or len(words) > 4:
        return False

    if any(len(word) < 2 for word in words):
        return False

    if any(char.isdigit() for char in name):
        return False

    if not all(
        any(char.isalpha() for char in word)
        for word in words
    ):
        return False

    lowered_words = {
        word.strip(".,'’-").lower()
        for word in words
    }

    if lowered_words.intersection(BAD_NAME_TERMS):
        return False

    return True


def convert_page_candidates(candidates):
    result = []

    for candidate in candidates:
        name = candidate.get(
            "name",
            "",
        ).strip()

        role = candidate.get(
            "role",
            "",
        ).strip()

        source_url = candidate.get(
            "source_url",
            "",
        ).strip()

        if not valid_person_name(name):
            continue

        if not valid_role(role):
            continue

        if not source_url:
            continue

        result.append(
            TeamMember(
                name=name,
                role=role,
                linkedin_url=None,
                source_url=source_url,
            )
        )

    return result


def convert_external_candidates(candidates):
    result = []

    for candidate in candidates:
        url = (
            candidate.get("linkedin_url")
            or candidate.get("url")
            or ""
        ).strip()

        if not url:
            continue

        title = candidate.get(
            "title",
            "",
        )

        snippet = candidate.get(
            "snippet",
            "",
        )

        evidence = title + " " + snippet
        evidence_lower = evidence.lower()

        role = None

        if "co-founder" in evidence_lower:
            role = "Co-Founder"

        elif "cofounder" in evidence_lower:
            role = "Co-Founder"

        elif "founder" in evidence_lower:
            role = "Founder"

        elif "chief executive officer" in evidence_lower:
            role = "CEO"

        elif " ceo " in (
            " " + evidence_lower + " "
        ):
            role = "CEO"

        elif "chief technology officer" in evidence_lower:
            role = "CTO"

        elif " cto " in (
            " " + evidence_lower + " "
        ):
            role = "CTO"

        if not role:
            continue

        possible_name = ""

        separators = [
            " - ",
            " | ",
            " — ",
            " – ",
        ]

        for separator in separators:
            if separator in title:
                possible_name = title.split(
                    separator,
                    1,
                )[0].strip()
                break

        if not valid_person_name(possible_name):
            continue

        result.append(
            TeamMember(
                name=possible_name,
                role=role,
                linkedin_url=url,
                source_url=url,
            )
        )

    return result


def build_candidate_pool(
    page_members,
    external_members,
):
    candidates = []

    candidates.extend(page_members)
    candidates.extend(external_members)

    unique = {}
    linkedin_seen = set()

    for member in candidates:
        name = member.name.strip().lower()

        role = (
            member.role.strip().lower()
            if member.role
            else ""
        )

        key = (
            name,
            role,
        )

        if key in unique:
            existing = unique[key]

            if (
                not existing.linkedin_url
                and member.linkedin_url
            ):
                existing.linkedin_url = (
                    member.linkedin_url
                )

            continue

        if member.linkedin_url:
            linkedin_key = (
                member.linkedin_url
                .strip()
                .lower()
            )

            if linkedin_key in linkedin_seen:
                continue

            linkedin_seen.add(
                linkedin_key
            )

        unique[key] = member

    return list(unique.values())


def validate_llm_leadership(
    llm_members,
    candidate_pool,
):
    candidate_index = {}

    for candidate in candidate_pool:
        key = (
            candidate.name.strip().lower(),
            candidate.role.strip().lower()
            if candidate.role
            else "",
        )

        candidate_index[key] = candidate

    verified = []

    for member in llm_members:
        name = (
            member.name.strip()
            if member.name
            else ""
        )

        role = (
            member.role.strip()
            if member.role
            else ""
        )

        if not valid_person_name(name):
            continue

        if not valid_role(role):
            continue

        key = (
            name.lower(),
            role.lower(),
        )

        candidate = candidate_index.get(key)

        if not candidate:
            same_person = None

            for pool_candidate in candidate_pool:
                if (
                    pool_candidate.name.lower()
                    == name.lower()
                ):
                    same_person = pool_candidate
                    break

            if not same_person:
                continue

            candidate = same_person

        verified.append(
            TeamMember(
                name=candidate.name,
                role=candidate.role,
                linkedin_url=candidate.linkedin_url,
                source_url=candidate.source_url,
            )
        )

    unique = {}

    for member in verified:
        key = (
            member.name.lower(),
            member.role.lower(),
        )

        unique[key] = member

    return list(unique.values())


def fallback_leadership(candidate_pool):
    output = []

    for candidate in candidate_pool:
        if not valid_person_name(candidate.name):
            continue

        if not valid_role(candidate.role):
            continue

        output.append(candidate)

        if len(output) >= 10:
            break

    return output


def calculate_confidence(
    result,
    page_count,
    emails,
    leadership_count,
    external_count,
):
    score = 0.0

    if result.company_overview:
        score += 0.20

    if result.target_audience:
        score += 0.20

    if emails:
        score += 0.15

    if leadership_count >= 3:
        score += 0.20

    elif leadership_count == 2:
        score += 0.15

    elif leadership_count == 1:
        score += 0.10

    if external_count >= 2:
        score += 0.10

    elif external_count == 1:
        score += 0.05

    if page_count >= 6:
        score += 0.15

    elif page_count >= 4:
        score += 0.12

    elif page_count >= 2:
        score += 0.08

    elif page_count >= 1:
        score += 0.05

    return round(
        min(score, 1.0),
        2,
    )


class LeadEnrichmentAgent:

    def process(self, domain):

        domain = normalize_domain(domain)

        print()
        print("=" * 60)
        print(
            f"[AGENT] Processing {domain}"
        )
        print("=" * 60)

        try:

            pages = crawl_domain(domain)

            if not pages:
                raise RuntimeError(
                    "No pages retrieved"
                )

            print(
                f"[CRAWL] Retrieved "
                f"{len(pages)} pages"
            )

            cleaned_pages = []

            for page in pages:

                url = page.get(
                    "url",
                    "",
                )

                html = page.get(
                    "html",
                    "",
                )

                if not html:
                    continue

                try:
                    text = clean_html(
                        html
                    )

                except Exception as exc:
                    print(
                        f"[WARNING] Cleaning failed "
                        f"for {url}: {exc}"
                    )
                    continue

                if not text:
                    continue

                cleaned_pages.append(
                    {
                        "url": url,
                        "text": text,
                    }
                )

            if not cleaned_pages:
                raise RuntimeError(
                    "No usable content"
                )

            print(
                f"[CLEAN] Usable pages: "
                f"{len(cleaned_pages)}"
            )

            emails, email_evidence = (
                collect_emails(
                    cleaned_pages
                )
            )

            print(
                f"[EXTRACT] Generic emails: "
                f"{len(emails)}"
            )

            linkedin_urls = (
                collect_linkedin(
                    cleaned_pages
                )
            )

            print(
                f"[EXTRACT] Website LinkedIn URLs: "
                f"{len(linkedin_urls)}"
            )

            page_candidates = (
                discover_from_company_pages(
                    cleaned_pages
                )
            )

            page_members = (
                convert_page_candidates(
                    page_candidates
                )
            )

            print(
                f"[LEADERSHIP] Company-page candidates: "
                f"{len(page_members)}"
            )

            company_name = (
                company_name_from_domain(
                    domain
                )
            )

            external_candidates = (
                search_external_leadership(
                    company_name
                )
            )

            external_members = (
                convert_external_candidates(
                    external_candidates
                )
            )

            print(
                f"[LEADERSHIP] External candidates: "
                f"{len(external_members)}"
            )

            candidate_pool = (
                build_candidate_pool(
                    page_members,
                    external_members,
                )
            )

            print(
                f"[LEADERSHIP] Verified candidate pool: "
                f"{len(candidate_pool)}"
            )

            context = build_context(
                cleaned_pages
            )

            result = extract_company_data(
                domain=domain,
                context=context,
                verified_emails=emails,
                verified_linkedin_urls=linkedin_urls,
                external_leadership=external_candidates,
            )

            result.domain = domain

            result.contact_points = []

            for email in emails:
                result.contact_points.append(
                    ContactPoint(
                        email=email,
                        source_url=email_evidence.get(
                            email
                        ),
                    )
                )

            verified_leadership = validate_llm_leadership(
                result.leadership_team,
                candidate_pool
                )
            if not verified_leadership and candidate_pool:
                print("[LEADERSHIP] LLM missed verified candidates; using deterministic candidates.")
                verified_leadership = [
                    candidate
                    if isinstance(candidate, TeamMember)
                    else TeamMember(
                        name=candidate["name"],
                        role=candidate.get("role"),
                        linkedin_url=candidate.get("linkedin_url"),
                        source_url=candidate.get("source_url"),
                        )
                        for candidate in candidate_pool
                        if (
                            (isinstance(candidate, TeamMember) and candidate.name)
                            or (isinstance(candidate, dict) and candidate.get("name"))
                            )
                            ]
                result.leadership_team = verified_leadership[:10]

                if result.company_overview:
                    result.company_overview = (
                        " ".join(
                        result.company_overview.split()
                    ).strip()
                )

            result.confidence_score = (
                calculate_confidence(
                    result=result,
                    page_count=len(
                        cleaned_pages
                    ),
                    emails=emails,
                    leadership_count=len(
                        result.leadership_team
                    ),
                    external_count=len(
                        external_candidates
                    ),
                )
            )

            print(
                f"[RESULT] Leadership: "
                f"{len(result.leadership_team)}"
            )

            print(
                f"[RESULT] Contacts: "
                f"{len(result.contact_points)}"
            )

            print(
                f"[RESULT] Confidence: "
                f"{result.confidence_score}"
            )

            return result

        except Exception as exc:

            print(
                f"[ERROR] {domain}: {exc}"
            )

            return {
                "domain": domain,
                "company_overview": "",
                "target_audience": "",
                "contact_points": [],
                "leadership_team": [],
                "confidence_score": 0.0,
                "error": str(exc),
            }

    def enrich(self, domain):
        return self.process(domain)
    