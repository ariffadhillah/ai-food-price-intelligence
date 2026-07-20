import json

from app.ai.llm_client import (
    LLMConfigurationError,
    LLMGenerationError,
    create_llm_client,
)
from app.ai.schemas import NationalAIReport


TEST_PROMPT = """
Analyze this sample Indonesian food market data:

- National high-risk ratio: 14.5%
- Highest-risk province: Sulawesi Tenggara
- Province average risk score: 18.4
- Highest-risk commodity: Cabai Merah
- Commodity risk score: 25.8
- One-month price change: 12.6%
- Some Papua provinces have no source data

Return a concise national market assessment based only on these facts.
""".strip()


TEST_INSTRUCTIONS = """
You are an Indonesian food price intelligence analyst.

Use only the supplied facts.
Write narrative fields in professional Indonesian.
Do not invent additional values.
Return output matching the supplied schema.
""".strip()


def main():
    print("Testing structured AI output...")

    try:
        client = create_llm_client()

        report = client.generate_structured(
            prompt=TEST_PROMPT,
            instructions=TEST_INSTRUCTIONS,
            response_schema=NationalAIReport,
            max_output_tokens=1500,
        )

        print(
            json.dumps(
                report.model_dump(
                    mode="json",
                ),
                indent=2,
                ensure_ascii=False,
            )
        )

    except LLMConfigurationError as exc:
        print(
            f"Configuration error: {exc}"
        )
        raise SystemExit(1) from exc

    except LLMGenerationError as exc:
        print(
            f"Generation error: {exc}"
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()