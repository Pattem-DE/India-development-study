import requests
import os
import time

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policy_docs", "niti_aayog")
os.makedirs(DOCS_DIR, exist_ok=True)

# Confirmed direct static PDF URLs from niti.gov.in
NITI_DOCS = {
    "ev_charging_infrastructure": "https://www.niti.gov.in/sites/default/files/2023-05/Final-smaller_Electric-Vehicles-Charging-Infrastructure.pdf",
    "ev_charging_handbook": "https://niti.gov.in/sites/default/files/2023-02/EV_Handbook_Final_14Oct.pdf",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

REQUEST_DELAY_SECONDS = 3

def fetch_all():
    print("Fetching NITI Aayog policy documents...\n")
    docs = list(NITI_DOCS.items())

    for i, (name, url) in enumerate(docs):
        filename = f"{name}.pdf"
        filepath = os.path.join(DOCS_DIR, filename)

        if os.path.exists(filepath):
            print(f"  {name}: already downloaded, skipping")
            continue

        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                size_kb = len(response.content) / 1024
                print(f"  {name}: saved ({size_kb:.0f} KB)")
            else:
                print(f"  {name}: FAILED (status {response.status_code})")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

        if i < len(docs) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    print("\nDone. Files saved to:", DOCS_DIR)

if __name__ == "__main__":
    fetch_all()
