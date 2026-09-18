import re
from urllib.parse import urljoin


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


def extract_emails(
    text: str,
    source_url: str
):

    emails = EMAIL_PATTERN.findall(
        text
    )

    results = []

    for email in emails:

        email = email.lower()

        if email not in [
            item["email"]
            for item in results
        ]:

            results.append({
                "email": email,
                "source_url": source_url
            })

    return results


def extract_linkedin_urls(
    html: str,
    source_url: str
):

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link["href"]

        if "linkedin.com/in/" in href:

            absolute_url = urljoin(
                source_url,
                href
            )

            if absolute_url not in results:
                results.append(
                    absolute_url
                )

    return results