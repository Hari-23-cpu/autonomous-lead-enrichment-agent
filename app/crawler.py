from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE_PATHS = [
    "/",
    "/about",
    "/team",
    "/company",
    "/contact",
    "/pricing",
    "/leadership",
    "/founders",
]

MAX_PAGES = 8
TIMEOUT = 30000


def normalize_url(url):
    if not url:
        return ""

    parsed = urlparse(url)

    if parsed.scheme.lower() not in {"http", "https"}:
        return ""

    hostname = parsed.netloc.lower()

    if hostname.startswith("www."):
        hostname = hostname[4:]

    path = parsed.path or "/"
    path = path.rstrip("/") or "/"

    return f"https://{hostname}{path}"


def crawl_domain(domain):
    base_url = f"https://{domain}"
    pages = []
    visited = set()

    urls = [
        normalize_url(
            urljoin(base_url, path)
        )
        for path in BASE_PATHS
    ]

    urls = list(dict.fromkeys(urls))

    print(f"[CRAWL] {base_url}")

    with sync_playwright() as playwright:
        browser = None

        try:
            browser = playwright.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                viewport={
                    "width": 1440,
                    "height": 900,
                },
            )

            page = context.new_page()

            for url in urls:
                if len(pages) >= MAX_PAGES:
                    break

                if url in visited:
                    continue

                visited.add(url)

                try:
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=TIMEOUT,
                    )

                    if response is None:
                        continue

                    if response.status >= 400:
                        print(
                            f"[WARNING] {response.status}: {url}"
                        )
                        continue

                    try:
                        page.wait_for_load_state(
                            "networkidle",
                            timeout=5000,
                        )
                    except Exception:
                        pass

                    final_url = normalize_url(
                        page.url
                    )

                    if not final_url:
                        continue

                    if final_url in {
                        item["url"]
                        for item in pages
                    }:
                        continue

                    print(
                        f"[CRAWL] Retrieved: {final_url}"
                    )

                    pages.append({
                        "url": final_url,
                        "html": page.content(),
                    })

                except Exception as exc:
                    print(
                        f"[WARNING] Failed to crawl "
                        f"{url}: {exc}"
                    )

        except Exception as exc:
            print(
                f"[ERROR] Browser startup failed: {exc}"
            )

        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

    print(
        f"[INFO] Retrieved {len(pages)} pages"
    )

    return pages

