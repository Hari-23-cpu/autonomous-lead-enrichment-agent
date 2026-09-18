import json
import os

from app.agent import LeadEnrichmentAgent


TARGET_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


def main():

    agent = LeadEnrichmentAgent()

    results = []

    for domain in TARGET_DOMAINS:

        result = agent.process(domain)

        if hasattr(result, "model_dump"):
            result = result.model_dump()

        results.append(result)

    os.makedirs(
        "output",
        exist_ok=True
    )

    output_path = "output/output.json"

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )

    print()
    print(
        f"[SUCCESS] Results saved to {output_path}"
    )


if __name__ == "__main__":
    main()