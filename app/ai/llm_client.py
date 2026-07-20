import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

load_dotenv()

logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when the LLM client configuration is invalid."""


class LLMGenerationError(Exception):
    """Raised when text generation fails."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str
    timeout: float
    max_retries: int

    @classmethod
    def from_environment(cls) -> "LLMConfig":
        provider = os.getenv(
            "LLM_PROVIDER",
            "openai",
        ).strip().lower()

        api_key = os.getenv(
            "OPENAI_API_KEY",
            "",
        ).strip()

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini",
        ).strip()

        timeout_raw = os.getenv(
            "OPENAI_TIMEOUT",
            "60",
        ).strip()

        retries_raw = os.getenv(
            "OPENAI_MAX_RETRIES",
            "2",
        ).strip()

        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise LLMConfigurationError(
                "OPENAI_TIMEOUT harus berupa angka."
            ) from exc

        try:
            max_retries = int(retries_raw)
        except ValueError as exc:
            raise LLMConfigurationError(
                "OPENAI_MAX_RETRIES harus berupa integer."
            ) from exc

        if provider != "openai":
            raise LLMConfigurationError(
                f"Provider '{provider}' belum didukung."
            )

        if not api_key:
            raise LLMConfigurationError(
                "OPENAI_API_KEY belum ditemukan di environment."
            )

        if not model:
            raise LLMConfigurationError(
                "OPENAI_MODEL tidak boleh kosong."
            )

        if timeout <= 0:
            raise LLMConfigurationError(
                "OPENAI_TIMEOUT harus lebih besar dari 0."
            )

        if max_retries < 0:
            raise LLMConfigurationError(
                "OPENAI_MAX_RETRIES tidak boleh negatif."
            )

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
        )


class LLMClient:
    """
    Central client for all LLM-powered features.

    Dashboard pages and analytics modules should use this client
    instead of accessing the OpenAI SDK directly.
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
    ):
        self.config = config or LLMConfig.from_environment()

        self.client = OpenAI(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def generate_text(
        self,
        prompt: str,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        max_output_tokens: int = 800,
    ) -> str:
        """
        Generate plain text using the OpenAI Responses API.
        """

        clean_prompt = prompt.strip()

        if not clean_prompt:
            raise ValueError(
                "Prompt tidak boleh kosong."
            )

        if max_output_tokens <= 0:
            raise ValueError(
                "max_output_tokens harus lebih besar dari 0."
            )

        selected_model = model or self.config.model

        default_instructions = (
            "You are a careful food price intelligence analyst. "
            "Base every conclusion only on the data supplied by the user. "
            "Do not invent missing values. "
            "Clearly mention uncertainty when the data is incomplete. "
            "Write in professional Indonesian unless the user requests "
            "another language."
        )

        try:
            response = self.client.responses.create(
                model=selected_model,
                instructions=(
                    instructions.strip()
                    if instructions
                    else default_instructions
                ),
                input=clean_prompt,
                max_output_tokens=max_output_tokens,
            )

            output_text = (response.output_text or "").strip()

            if not output_text:
                status = getattr(response, "status", "unknown")
                incomplete_details = getattr(
                    response,
                    "incomplete_details",
                    None,
                )

                reason = getattr(
                    incomplete_details,
                    "reason",
                    None,
                )

                if status == "incomplete":
                    raise LLMGenerationError(
                        "Respons model tidak selesai. "
                        f"Reason: {reason or 'unknown'}. "
                        "Naikkan max_output_tokens atau gunakan model "
                        "non-reasoning seperti gpt-4.1-mini."
                    )

                raise LLMGenerationError(
                    "API berhasil merespons, tetapi tidak menghasilkan "
                    f"teks. Response status: {status}."
                )



            return output_text

        except AuthenticationError as exc:
            logger.exception(
                "OpenAI authentication failed."
            )
            raise LLMGenerationError(
                "Autentikasi OpenAI gagal. "
                "Periksa OPENAI_API_KEY."
            ) from exc

        except RateLimitError as exc:
            logger.exception(
                "OpenAI rate limit reached."
            )
            raise LLMGenerationError(
                "Batas penggunaan OpenAI tercapai. "
                "Silakan coba kembali beberapa saat lagi."
            ) from exc

        except APITimeoutError as exc:
            logger.exception(
                "OpenAI request timed out."
            )
            raise LLMGenerationError(
                "Permintaan ke OpenAI mengalami timeout."
            ) from exc

        except APIConnectionError as exc:
            logger.exception(
                "Unable to connect to OpenAI."
            )
            raise LLMGenerationError(
                "Tidak dapat terhubung ke layanan OpenAI."
            ) from exc

        except APIStatusError as exc:
            logger.exception(
                "OpenAI API status error: %s",
                exc.status_code,
            )
            raise LLMGenerationError(
                f"OpenAI API mengembalikan error "
                f"HTTP {exc.status_code}."
            ) from exc

        except LLMGenerationError:
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected LLM generation error."
            )
            raise LLMGenerationError(
                "Terjadi kesalahan tak terduga saat "
                "menghasilkan analisis AI."
            ) from exc


    def health_check(self) -> dict:
        """
        Verify that the API key and configured model are working.
        """

        output = self.generate_text(
            prompt="Balas hanya dengan: LLM connection successful",
            instructions=(
                "Ikuti instruksi pengguna secara tepat. "
                "Jangan menambahkan penjelasan."
            ),
            max_output_tokens=100,
        )

        return {
            "status": "connected",
            "provider": self.config.provider,
            "model": self.config.model,
            "response": output,
        }

def create_llm_client() -> LLMClient:
    """
    Factory function used by other AI modules.
    """

    return LLMClient()