import requests
import os
import time

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policy_docs", "budget_speeches")
os.makedirs(DOCS_DIR, exist_ok=True)

# Confirmed URL pattern from indiabudget.gov.in - direct static PDFs, no JS/CAPTCHA
BUDGET_SPEECH_URLS = {
    "2025-26": "https://www.indiabudget.gov.in/budget2025-26/doc/Budget_Speech.pdf",
    "2024-25": "https://www.indiabudget.gov.in/doc/bh1.pdf",
    "2023-24": "https://www.indiabudget.gov.in/budget2023-24/doc/Budget_Speech.pdf",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

REQUEST_DELAY_SECONDS = 3  # polite gap between each request to the same government server

def fetch_all():
    print("Fetching Union Budget speeches...\n")
    urls = list(BUDGET_SPEECH_URLS.items())

    for i, (year, url) in enumerate(urls):
        filename = f"budget_speech_{year}.pdf"
        filepath = os.path.join(DOCS_DIR, filename)

        # Skip re-downloading if already present - avoids unnecessary repeat hits
        if os.path.exists(filepath):
            print(f"  {year}: already downloaded, skipping")
            continue

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                size_kb = len(response.content) / 1024
                print(f"  {year}: saved ({size_kb:.0f} KB)")
            else:
                print(f"  {year}: FAILED (status {response.status_code})")
        except Exception as e:
            print(f"  {year}: ERROR - {e}")

        # Politeness delay between requests, skip after the last one
        if i < len(urls) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nDone. Files saved to:", DOCS_DIR)

if __name__ == "__main__":
    fetch_all()
