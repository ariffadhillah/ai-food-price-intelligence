import json
from typing import Any


NATIONAL_ANALYST_INSTRUCTIONS = """
You are a senior Indonesian food price intelligence analyst.

Your responsibility is to transform supplied analytics data into a
professional national market assessment.

Rules:

1. Use only the supplied data.
2. Never invent prices, percentages, provinces, commodities, or causes.
3. Do not claim causal relationships unless directly supported by the data.
4. Clearly identify uncertainty and missing information.
5. Write all narrative fields in professional Indonesian.
6. Keep explanations concise and suitable for an executive dashboard.
7. Rank recommendations from most urgent to least urgent.
8. A confidence score must reflect data completeness, not personal certainty.
9. Preserve official province and commodity names from the supplied data.
10. Return data that conforms exactly to the requested structured schema.
""".strip()


def make_json_safe(value: Any) -> Any:
    """
    Convert common pandas and NumPy values into JSON-safe Python values.
    """

    if value is None:
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (ValueError, TypeError):
            pass

    return value


def sanitize_mapping(data: dict) -> dict:
    """
    Recursively convert a dictionary into JSON-safe values.
    """

    sanitized = {}

    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_mapping(value)

        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_mapping(item)
                if isinstance(item, dict)
                else make_json_safe(item)
                for item in value
            ]

        else:
            sanitized[key] = make_json_safe(value)

    return sanitized


def build_national_report_prompt(
    rule_report: dict,
    province_records: list[dict],
    commodity_records: list[dict],
    analytics_records: list[dict],
) -> str:
    """
    Build a compact, grounded prompt for the national AI analyst.
    """

    context = {
        "rule_based_assessment": sanitize_mapping(rule_report),
        "highest_risk_provinces": [
            sanitize_mapping(record)
            for record in province_records[:10]
        ],
        "highest_risk_commodities": [
            sanitize_mapping(record)
            for record in commodity_records[:15]
        ],
        "highest_volatility_records": [
            sanitize_mapping(record)
            for record in analytics_records[:10]
        ],
    }

    serialized_context = json.dumps(
        context,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    )

    return f"""
Analyze the following Indonesian food price intelligence data.

The rule-based assessment is a deterministic baseline. You may improve
its wording and connect related findings, but you must not contradict
the supplied numerical data.

Determine:

- national market status;
- confidence based on data coverage;
- executive summary;
- critical provinces;
- critical commodities;
- key findings;
- prioritized recommendations;
- relevant data limitations.

Use percentage values exactly as supplied. Do not interpret correlation
as causation.

DATA CONTEXT:

{serialized_context}
""".strip()