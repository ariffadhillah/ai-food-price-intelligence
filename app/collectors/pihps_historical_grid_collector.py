import time
import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import quote


BASE_URL = "https://www.bi.go.id/hargapangan/WebSite/Home"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.bi.go.id/hargapangan",
    "X-Requested-With": "XMLHttpRequest",
}


def get_grid_data(date_text: str, commodity_id: int = 1, prov_id: int = 0):
    encoded_date = quote(date_text)

    url = (
        f"{BASE_URL}/GetGridData1"
        f"?tanggal={encoded_date}"
        f"&commodity={commodity_id}"
        f"&priceType=1"
        f"&isPasokan=1"
        f"&jenis=1"
        f"&periode=1"
        f"&provId={prov_id}"
        f"&_={int(time.time() * 1000)}"
    )

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def save_json(data, filename: str):
    output_dir = Path("data/raw/grid_history")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path


def main():
    dates = [
        "Sep 1, 2025",
        "Oct 1, 2025",
        "Nov 1, 2025",
        "Dec 1, 2025",
        "Jan 1, 2026",
        "Feb 1, 2026",
        "Mar 1, 2026",
        "Apr 1, 2026",
        "May 1, 2026",
        "Jun 1, 2026",
    ]

    commodity_id = 1  # Beras

    for date_text in dates:
        print(f"Fetching {date_text} | commodity_id={commodity_id}")

        data = get_grid_data(date_text=date_text, commodity_id=commodity_id)

        safe_date = datetime.strptime(date_text, "%b %d, %Y").strftime("%Y_%m_%d")
        filename = f"pihps_grid_commodity_{commodity_id}_{safe_date}.json"

        output_path = save_json(data, filename)

        rows = data.get("data", [])
        print(f"Saved: {output_path} | rows: {len(rows)}")

        time.sleep(1)


if __name__ == "__main__":
    main()