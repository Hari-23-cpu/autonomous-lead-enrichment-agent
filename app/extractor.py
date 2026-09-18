import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas import CompanyIntelligence


load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def extract_company_data(
    domain: str,
    context: str,
    verified_emails: list[str],
    verified_linkedin_urls: list[str],
    external_leadership: list[dict] | None = None,
):
    """
    Extract structured company intelligence using Ollama/Gemma.

    The model is explicitly instructed to use only evidence
    supplied in the prompt.
    """

    external_leadership = external_leadership or []

    verified_email_text = (
        "\n".join(
            f"- {email}"
            for email in verified_emails
        )
        if verified_emails
        else "NONE"
    )

    verified_linkedin_text = (
        "\n".join(
            f"- {url}"
            for url in verified_linkedin_urls
        )
        if verified_linkedin_urls
        else "NONE"
    )

    external_text = (
        "\n".join(
            (
                f"- URL: {item.get('url', '')}\n"
                f"  TITLE: {item.get('title', '')}\n"
                f"  SNIPPET: {item.get('snippet', '')}"
            )
            for item in external_leadership
        )
        if external_leadership
        else "NONE"
    )

    prompt = f"""
You are a strict company intelligence extraction system.

TARGET COMPANY DOMAIN:
{domain}

Your job is to extract factual information about ONLY the company
represented by the TARGET COMPANY DOMAIN.

=========================================================
SOURCE COMPANY WEBSITE CONTENT
=========================================================

{context}

=========================================================
VERIFIED PUBLIC EMAILS
=========================================================

{verified_email_text}

=========================================================
VERIFIED LINKEDIN URLS FROM COMPANY WEBSITE
=========================================================

{verified_linkedin_text}

=========================================================
EXTERNAL LEADERSHIP SEARCH RESULTS
=========================================================

{external_text}

=========================================================
STRICT RULES
=========================================================

1. COMPANY IDENTITY

The output MUST describe the company at:

{domain}

Never replace the company with:

- a customer
- a case study
- a partner
- an investor
- a community member
- another company mentioned on the website
- an unrelated search result

If a page talks about another company, ignore that company's
description when creating the target company's overview.

---------------------------------------------------------

2. COMPANY OVERVIEW

Write EXACTLY TWO sentences.

Sentence 1:
Clearly state what the TARGET COMPANY itself does.

Sentence 2:
State the main product/service/use case or target market,
but ONLY when supported by the supplied evidence.

Do NOT use general world knowledge.

Do NOT invent information.

Do NOT infer the company from its domain name alone.

If the evidence is insufficient, write a short factual description
based only on the strongest available company evidence.

---------------------------------------------------------

3. TARGET AUDIENCE

Identify the target audience using only evidence from the company
website.

Examples:

- developers
- startups
- enterprises
- API teams
- engineering teams
- businesses
- healthcare organizations

Do not invent an audience.

---------------------------------------------------------

4. EMAILS

Use ONLY emails appearing in VERIFIED PUBLIC EMAILS.

Do NOT invent emails.

Do NOT include:

privacy@
legal@
security@
infosec@
talent@
careers@
jobs@
hr@
billing@
abuse@
dpo@
compliance@

Prefer generic public contact addresses such as:

info@
hello@
contact@
sales@
support@

Only include a specialized address if there is no generic address
and it is clearly useful as a public company contact.

---------------------------------------------------------

5. LEADERSHIP

A leadership member must have evidence.

Accept roles such as:

Founder
Co-Founder
CEO
CTO
CPO
COO
CFO
President
VP
Vice President
Head of
Director
Executive

Do NOT classify these as leadership:

Customer
Client
Partner
Investor
Advisor
Speaker
Author
Community member
Consultant
Ambassador

The person must be associated with the TARGET COMPANY.

---------------------------------------------------------

6. LINKEDIN

Only use LinkedIn URLs supplied in the verified LinkedIn list
or external leadership search results.

Never invent a LinkedIn URL.

Only use:

https://www.linkedin.com/in/...

---------------------------------------------------------

7. SOURCE URL

Every leadership member MUST have a source_url.

For company website evidence, use the exact source page URL.

For external LinkedIn discovery, use the LinkedIn profile URL
as source_url.

---------------------------------------------------------

8. NULL VALUES

Never write the string:

"null"

Use:

null

when a value is unavailable.

---------------------------------------------------------

9. CONFIDENCE

Return a preliminary confidence score from 0.0 to 1.0.

However, the final application may replace this score with an
evidence-based score.

=========================================================
OUTPUT
=========================================================

Return ONLY valid JSON matching the supplied schema.

No markdown.

No explanation.

No additional fields.

"""

    try:

        response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "company_intelligence",
            "strict": True,
            "schema": CompanyIntelligence.model_json_schema(),
        },
    },
    temperature=0,
)

        content = response.choices[0].message.content

        # Sometimes models wrap JSON in markdown.
        content = content.strip()

        if content.startswith("```"):
            content = content.replace(
                "```json",
                "",
            )
            content = content.replace(
                "```",
                "",
            )
            content = content.strip()

        data = json.loads(content)

        return CompanyIntelligence.model_validate(data)

    except Exception as exc:

        print(
            f"[ERROR] LLM extraction failed "
            f"for {domain}: {exc}"
        )

        # Safe fallback.
        return CompanyIntelligence(
            domain=domain,
            company_overview="",
            target_audience="",
            contact_points=[],
            leadership_team=[],
            confidence_score=0.0,
        )