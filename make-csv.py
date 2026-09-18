import json
import csv
from pathlib import Path

INPUT_FILE = Path("output/output.json")
OUTPUT_FILE = Path("output/output.csv")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []

for company in data:
    leadership = company.get("leadership_team", [])
    contacts = company.get("contact_points", [])

    leadership_text = "; ".join(
        f"{person.get('name', '')} - {person.get('role', '') or 'N/A'}"
        for person in leadership
    )

    linkedin_text = "; ".join(
        person.get("linkedin_url", "")
        for person in leadership
        if person.get("linkedin_url")
    )

    email_text = "; ".join(
        contact.get("email", "")
        for contact in contacts
        if contact.get("email")
    )

    source_urls = "; ".join(
        contact.get("source_url", "")
        for contact in contacts
        if contact.get("source_url")
    )

    rows.append({
        "domain": company.get("domain", ""),
        "company_overview": company.get("company_overview", ""),
        "target_audience": company.get("target_audience", ""),
        "emails": email_text,
        "leadership_team": leadership_text,
        "linkedin_urls": linkedin_text,
        "contact_source_urls": source_urls,
        "confidence_score": company.get("confidence_score", "")
    })

fieldnames = [
    "domain",
    "company_overview",
    "target_audience",
    "emails",
    "leadership_team",
    "linkedin_urls",
    "contact_source_urls",
    "confidence_score"
]

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"[SUCCESS] CSV saved to: {OUTPUT_FILE}")