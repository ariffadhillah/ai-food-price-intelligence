import requests
import pandas as pd
from datetime import datetime
from pathlib import Path


BASE_URL = "https://www.bi.go.id/hargapangan"


def fetch_pihps_page():
    response = requests.get(BASE_URL, timeout=30)
    response.raise_for_status()
    return response.text


def save_raw_html(html: str):
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"pihps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    output_path = output_dir / filename

    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    print("Fetching PIHPS page...")
    html = fetch_pihps_page()

    output_path = save_raw_html(html)

    print(f"Saved raw HTML to: {output_path}")
    print("Collector test completed.")


if __name__ == "__main__":
    main()