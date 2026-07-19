import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


GEOJSON_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "indonesia_provinces.geojson"
)


PROVINCE_NAME_MAPPING = {
    "ACEH": "Aceh",
    "NANGGROE ACEH DARUSSALAM": "Aceh",

    "SUMATERA UTARA": "Sumatera Utara",
    "SUMATERA BARAT": "Sumatera Barat",
    "RIAU": "Riau",
    "JAMBI": "Jambi",
    "SUMATERA SELATAN": "Sumatera Selatan",
    "BENGKULU": "Bengkulu",
    "LAMPUNG": "Lampung",

    "KEPULAUAN BANGKA BELITUNG": "Kepulauan Bangka Belitung",
    "BANGKA BELITUNG": "Kepulauan Bangka Belitung",
    "KEPULAUAN RIAU": "Kepulauan Riau",

    "DKI JAKARTA": "DKI Jakarta",
    "DAERAH KHUSUS IBUKOTA JAKARTA": "DKI Jakarta",
    "JAKARTA RAYA": "DKI Jakarta",

    "JAWA BARAT": "Jawa Barat",
    "JAWA TENGAH": "Jawa Tengah",
    "DI YOGYAKARTA": "DI Yogyakarta",
    "DAERAH ISTIMEWA YOGYAKARTA": "DI Yogyakarta",
    "YOGYAKARTA": "DI Yogyakarta",
    "JAWA TIMUR": "Jawa Timur",
    "BANTEN": "Banten",
    "BALI": "Bali",

    "NUSA TENGGARA BARAT": "Nusa Tenggara Barat",
    "NUSA TENGGARA TIMUR": "Nusa Tenggara Timur",

    "KALIMANTAN BARAT": "Kalimantan Barat",
    "KALIMANTAN TENGAH": "Kalimantan Tengah",
    "KALIMANTAN SELATAN": "Kalimantan Selatan",
    "KALIMANTAN TIMUR": "Kalimantan Timur",
    "KALIMANTAN UTARA": "Kalimantan Utara",

    "SULAWESI UTARA": "Sulawesi Utara",
    "GORONTALO": "Gorontalo",
    "SULAWESI TENGAH": "Sulawesi Tengah",
    "SULAWESI BARAT": "Sulawesi Barat",
    "SULAWESI SELATAN": "Sulawesi Selatan",
    "SULAWESI TENGGARA": "Sulawesi Tenggara",

    "MALUKU": "Maluku",
    "MALUKU UTARA": "Maluku Utara",

    "PAPUA": "Papua",
    "PAPUA BARAT": "Papua Barat",
    "PAPUA BARAT DAYA": "Papua Barat Daya",
    "PAPUA SELATAN": "Papua Selatan",
    "PAPUA TENGAH": "Papua Tengah",
    "PAPUA PEGUNUNGAN": "Papua Pegunungan",
}

def calculate_ring_area(ring):
    """Menghitung signed area polygon ring."""
    area = 0.0

    if not ring or len(ring) < 4:
        return area

    for index in range(len(ring) - 1):
        x1, y1 = ring[index]
        x2, y2 = ring[index + 1]

        area += (x1 * y2) - (x2 * y1)

    return area / 2.0


def ensure_closed_ring(ring):
    """Memastikan titik pertama dan terakhir sama."""
    if not ring:
        return ring

    if ring[0] != ring[-1]:
        return ring + [ring[0]]

    return ring


def rewind_ring_clockwise(ring):
    """
    Plotly pada dataset ini membutuhkan outer ring clockwise.
    """
    ring = ensure_closed_ring(ring)

    # Area positif berarti counter-clockwise.
    # Balik supaya menjadi clockwise.
    if calculate_ring_area(ring) > 0:
        ring = list(reversed(ring))

    return ring


def rewind_ring_counter_clockwise(ring):
    """
    Hole atau inner ring harus berlawanan dengan outer ring.
    """
    ring = ensure_closed_ring(ring)

    if calculate_ring_area(ring) < 0:
        ring = list(reversed(ring))

    return ring


def normalize_polygon_rings(polygon):
    """
    Ring pertama adalah outer ring.
    Ring berikutnya, jika ada, adalah holes.
    """
    if not polygon:
        return polygon

    normalized = [
        rewind_ring_clockwise(polygon[0])
    ]

    for inner_ring in polygon[1:]:
        normalized.append(
            rewind_ring_counter_clockwise(inner_ring)
        )

    return normalized


def normalize_geojson_geometry(geojson):
    """
    Mempertahankan struktur Polygon/MultiPolygon asli,
    hanya memperbaiki arah ring.
    """
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry")

        if not geometry:
            continue

        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")

        if not coordinates:
            continue

        if geometry_type == "Polygon":
            geometry["coordinates"] = normalize_polygon_rings(
                coordinates
            )

        elif geometry_type == "MultiPolygon":
            geometry["coordinates"] = [
                normalize_polygon_rings(polygon)
                for polygon in coordinates
            ]

    return geojson

def load_geojson():
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(
            f"GeoJSON tidak ditemukan di {GEOJSON_PATH}"
        )

    with open(
        GEOJSON_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(file)

    return normalize_geojson_geometry(geojson)


def detect_province_property(geojson):
    features = geojson.get("features", [])

    if not features:
        raise ValueError("GeoJSON tidak memiliki features.")

    properties = features[0].get("properties", {})

    candidates = [
        "PROVINSI",
        "Provinsi",
        "PROPINSI",
        "Propinsi",
        "province",
        "PROVINCE",
        "name",
        "NAME",
        "NAME_1",
        "state",
    ]

    for candidate in candidates:
        if candidate in properties:
            return candidate

    raise ValueError(
        "Property nama provinsi tidak ditemukan. "
        f"Property tersedia: {list(properties.keys())}"
    )


def normalize_province_name(value):
    if pd.isna(value):
        return None

    cleaned = str(value).strip().upper()

    return PROVINCE_NAME_MAPPING.get(
        cleaned,
        str(value).strip().title(),
    )


def classify_map_risk(score):
    if pd.isna(score):
        return "NO DATA"

    if score >= 50:
        return "HIGH"

    if score >= 20:
        return "MEDIUM"

    return "LOW"


def prepare_complete_map_data(
    provinces,
    geojson,
    province_property,
):
    # Semua nama provinsi yang tersedia di GeoJSON
    geo_provinces = []

    for feature in geojson.get("features", []):
        raw_name = feature["properties"].get(province_property)
        normalized_name = normalize_province_name(raw_name)

        feature["properties"]["normalized_name"] = normalized_name
        geo_provinces.append(normalized_name)

    geo_df = pd.DataFrame(
        {"province_name": geo_provinces}
    ).drop_duplicates()

    province_data = provinces.copy()

    province_data["province_name"] = (
        province_data["province_name"]
        .apply(normalize_province_name)
    )

    # Left join agar provinsi tanpa data tetap tersedia
    map_data = geo_df.merge(
        province_data,
        on="province_name",
        how="left",
    )

    map_data["map_risk_level"] = (
        map_data["avg_risk_score"]
        .apply(classify_map_risk)
    )

    map_data["display_score"] = (
        map_data["avg_risk_score"].fillna(0)
    )

    map_data["data_status"] = map_data["avg_risk_score"].apply(
        lambda value: "Available"
        if pd.notna(value)
        else "No PIHPS data"
    )

    return map_data


def show_province_risk_map(provinces):
    st.subheader("🗺️ Indonesia Food Price Risk Map")

    st.caption(
        "Warna menunjukkan rata-rata risk score harga pangan "
        "untuk setiap provinsi. Provinsi tanpa data PIHPS "
        "ditampilkan sebagai NO DATA."
    )

    try:
        geojson = load_geojson()
        

        province_property = detect_province_property(geojson)

        map_data = prepare_complete_map_data(
            provinces=provinces,
            geojson=geojson,
            province_property=province_property,
        )

    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        st.error(str(error))
        return

    data_map = map_data[
        map_data["avg_risk_score"].notna()
    ].copy()

    fig = px.choropleth(
        data_map,
        geojson=geojson,
        locations="province_name",
        featureidkey="properties.normalized_name",
        color="avg_risk_score",
        hover_name="province_name",
        hover_data={
            "avg_risk_score": ":.2f",
            "max_risk_score": ":.2f",
            "high_risk_count": True,
            "top_risk_commodity": True,
            "top_risk_price": ":,.0f",
            "avg_change_1m": ":.2f",
            "avg_change_3m": ":.2f",
            "avg_change_6m": ":.2f",
            "data_status": True,
        },
        color_continuous_scale=[
            [0.00, "#22c55e"],
            [0.35, "#eab308"],
            [0.65, "#f97316"],
            [1.00, "#dc2626"],
        ],
        title="Average Food Price Risk Score by Province",
    )

    fig.update_geos(
        projection_type="mercator",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=False,
        lonaxis_range=[94, 142],
        lataxis_range=[-12, 7],
    )

    fig.update_traces(
        marker_line_width=1.0,
        marker_line_color="#f8fafc",
    )

    fig.update_layout(
        height=650,
        margin={
            "r": 0,
            "t": 60,
            "l": 0,
            "b": 0,
        },
        coloraxis_colorbar={
            "title": "Risk Score",
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    no_data = map_data[
        map_data["avg_risk_score"].isna()
    ]["province_name"].tolist()

    if no_data:
        with st.expander(
            f"ℹ️ Provinsi tanpa data PIHPS ({len(no_data)})"
        ):
            st.write(no_data)

    geo_names = set(map_data["province_name"].dropna())
    database_names = set(
        provinces["province_name"]
        .apply(normalize_province_name)
        .dropna()
    )

    unmatched_database = database_names - geo_names

    if unmatched_database:
        with st.expander(
            "⚠️ Nama provinsi database yang tidak cocok"
        ):
            st.write(sorted(unmatched_database))