from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MarketStatus(str, Enum):
    STABLE = "STABLE"
    WATCHLIST = "WATCHLIST"
    HIGH_PRESSURE = "HIGH PRESSURE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CriticalProvince(BaseModel):
    model_config = ConfigDict(extra="forbid")

    province_name: str = Field(
        description="Nama provinsi.",
    )

    risk_score: float = Field(
        ge=0,
        description="Rata-rata risk score provinsi.",
    )

    risk_level: RiskLevel = Field(
        description="Kategori risiko provinsi.",
    )

    main_risk_driver: str = Field(
        description="Komoditas utama yang mendorong risiko.",
    )

    explanation: str = Field(
        description="Penjelasan singkat berdasarkan data.",
    )


class CriticalCommodity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commodity_name: str = Field(
        description="Nama komoditas.",
    )

    province_name: str = Field(
        description="Provinsi terkait risiko tertinggi.",
    )

    risk_score: float = Field(
        ge=0,
        description="Risk score komoditas.",
    )

    price_change_1m: float = Field(
        description="Perubahan harga satu bulan dalam persen.",
    )

    explanation: str = Field(
        description="Alasan komoditas dianggap kritis.",
    )


class KeyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        description="Judul temuan.",
    )

    finding: str = Field(
        description="Temuan berdasarkan data.",
    )

    importance: RiskLevel = Field(
        description="Tingkat kepentingan temuan.",
    )


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority: int = Field(
        ge=1,
        le=5,
        description="Urutan prioritas rekomendasi.",
    )

    action: str = Field(
        description="Tindakan yang direkomendasikan.",
    )

    reason: str = Field(
        description="Alasan rekomendasi tersebut diberikan.",
    )


class NationalAIReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    market_status: MarketStatus = Field(
        description="Status umum pasar pangan nasional.",
    )

    confidence_score: float = Field(
        ge=0,
        le=100,
        description="Tingkat keyakinan berdasarkan kelengkapan data.",
    )

    headline: str = Field(
        description="Headline singkat kondisi pasar.",
    )

    executive_summary: str = Field(
        description="Ringkasan analisis nasional.",
    )

    critical_provinces: list[CriticalProvince] = Field(
        max_length=5,
        description="Maksimal lima provinsi paling kritis.",
    )

    critical_commodities: list[CriticalCommodity] = Field(
        max_length=5,
        description="Maksimal lima komoditas paling kritis.",
    )

    key_findings: list[KeyFinding] = Field(
        max_length=6,
        description="Temuan utama berdasarkan data.",
    )

    recommendations: list[Recommendation] = Field(
        max_length=5,
        description="Rekomendasi yang dapat ditindaklanjuti.",
    )

    data_limitations: list[str] = Field(
        max_length=5,
        description="Keterbatasan data yang memengaruhi analisis.",
    )