import time
import json
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import quote


BASE_URL = "https://www.bi.go.id/hargapangan/WebSite/Home"

TEMP_ID = "1aba4c18-30fd-4e89-9ec2-83e5110e2a78"


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.bi.go.id/hargapangan",
    "X-Requested-With": "XMLHttpRequest",
}


def get_json(url: str):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def get_commodities_tree():
    url = f"{BASE_URL}/GetCommoditiesTree?_={int(time.time() * 1000)}"
    return get_json(url)


def get_provinces():
    url = f'{BASE_URL}/GetProvinceAll?filter=%5B%22province_id%22%2C0%5D&_={int(time.time() * 1000)}'
    return get_json(url)


def get_chart_data(commodity_name: str):
    encoded_name = quote(commodity_name)
    url = (
        f"{BASE_URL}/GetChartData"
        f"?tempId={TEMP_ID}"
        f"&comName={encoded_name}"
        f"&_={int(time.time() * 1000)}"
    )
    return get_json(url)


def save_json(data, filename: str):
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path


def main():
    print("Fetching commodities...")
    commodities = get_commodities_tree()
    save_json(commodities, "pihps_commodities.json")

    print("Fetching provinces...")
    provinces = get_provinces()
    save_json(provinces, "pihps_provinces.json")

    test_commodities = [
        "Bawang Merah Ukuran Sedang",
        "Beras Kualitas Medium I",
        "Cabai Merah Besar",
        "Minyak Goreng Curah",
        "Telur Ayam Ras Segar",
    ]

    for commodity in test_commodities:
        print(f"Fetching chart data: {commodity}")
        data = get_chart_data(commodity)

        safe_name = commodity.lower().replace(" ", "_").replace("/", "_")
        save_json(data, f"pihps_chart_{safe_name}.json")

    print("Done.")


if __name__ == "__main__":
    main()