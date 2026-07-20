import json

from app.ai.llm_client import (
    LLMConfigurationError,
    LLMGenerationError,
    create_llm_client,
)


def main():
    print("Testing LLM client connection...")

    try:
        client = create_llm_client()
        result = client.health_check()

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    except LLMConfigurationError as exc:
        print(f"Configuration error: {exc}")
        raise SystemExit(1) from exc

    except LLMGenerationError as exc:
        print(f"Generation error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()