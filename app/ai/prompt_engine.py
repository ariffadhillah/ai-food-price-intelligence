import json
from typing import Any


NATIONAL_ANALYST_INSTRUCTIONS = """
You are a senior Indonesian food price intelligence analyst.

Your responsibility is to transform supplied analytics context into
a professional national food market assessment.

Rules:

1. Use only the supplied context.
2. Never invent prices, percentages, provinces, commodities, or causes.
3. Do not claim causal relationships unless directly supported by the context.
4. Clearly identify uncertainty and missing information.
5. Write all narrative fields in professional Indonesian.
6. Keep explanations concise and suitable for an executive dashboard.
7. Rank recommendations from most urgent to least urgent.
8. Confidence must reflect data completeness and analytical coverage.
9. Preserve official province and commodity names from the context.
10. Return output conforming exactly to the requested structured schema.
""".strip()


def build_national_report_prompt(
    analysis_context: dict[str, Any],
) -> str:
    """
    Convert a prepared national analysis context into an LLM prompt.

    The prompt engine does not need to know whether the context
    originated from PostgreSQL, pandas, CSV, or another service.
    """

    serialized_context = json.dumps(
        analysis_context,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    )

    return f"""
Create a structured national food price intelligence report using the
analysis context supplied below.

Your report must include:

- national market status;
- confidence score based on data coverage;
- executive headline;
- concise executive summary;
- critical provinces;
- critical commodities;
- key findings;
- prioritized recommendations;
- relevant data limitations.

The rule-based assessment is a deterministic baseline. You may improve
the wording and connect related observations, but you must not
contradict the supplied numerical values.

Do not infer external causes such as weather, logistics, policy,
seasonality, production problems, or supply shortages unless those
causes are explicitly present in the context.

ANALYSIS CONTEXT:

{serialized_context}
""".strip()