import json
import csv

with open("output/output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []

for company in data:
    emails = "; ".join(
        contact.get("email", "")
        for contact in company.get("contact_points", [])
        if contact.get("email")
    )

    leadership = "; ".join(
        f"{person.get('name', '')} - {person.get('role') or 'N/A'}"
        for person in company.get("leadership_team", [])
    )

    linkedin_urls = "; ".join(
        person.get("linkedin_url", "")
        for person in company.get("leadership_team", [])
        if person.get("linkedin_url")
    )

    source_urls = "; ".join(
        contact.get("source_url", "")
        for contact in company.get("contact_points", [])
        if contact.get("source_url")
    )

    rows.append({
        "domain": company.get("domain", ""),
        "company_overview": company.get("company_overview", ""),
        "target_audience": company.get("target_audience", ""),
        "emails": emails,
        "leadership_team": leadership,
        "linkedin_urls": linkedin_urls,
        "contact_source_urls": source_urls,
        "confidence_score": company.get("confidence_score", "")
    })

columns = [
    "domain",
    "company_overview",
    "target_audience",
    "emails",
    "leadership_team",
    "linkedin_urls",
    "contact_source_urls",
    "confidence_score"
]

with open("output/output.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("[SUCCESS] output/output.csv created")