from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from datetime import date, datetime


from app.database.db import get_connection


def serialize_database_value(value):
    """
    Convert PostgreSQL values into JSON-safe Python values.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: serialize_database_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_database_value(item)
            for item in value
        ]

    return value


def serialize_database_record(
    record: dict,
) -> dict:
    """
    Convert an entire database record into JSON-safe values.
    """

    return {
        key: serialize_database_value(value)
        for key, value in record.items()
    }


class AIReportRepository:
    """
    Persistence layer for AI analysis runs and report versions.
    """

    def create_analysis_run(
        self,
        report_type: str,
        analysis_date: date,
        context_version: str,
        context_hash: str,
        context_json: dict[str, Any],
    ) -> int:
        coverage = context_json.get(
            "data_coverage",
            {},
        )

        query = """
            INSERT INTO ai_analysis_runs (
                report_type,
                analysis_date,
                context_version,
                context_hash,
                context_json,
                status,
                source_score_records,
                source_province_records,
                source_analytics_records,
                covered_province_count,
                province_coverage_percentage
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                'PROCESSING',
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id;
        """

        values = (
            report_type,
            analysis_date,
            context_version,
            context_hash,
            json.dumps(
                context_json,
                ensure_ascii=False,
                allow_nan=False,
            ),
            coverage.get(
                "score_record_count",
                0,
            ),
            coverage.get(
                "province_analytics_record_count",
                0,
            ),
            coverage.get(
                "commodity_analytics_record_count",
                0,
            ),
            coverage.get(
                "covered_province_count",
            ),
            coverage.get(
                "province_coverage_percentage",
            ),
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    values,
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "Gagal membuat AI analysis run."
                    )

                run_id = int(row[0])

            connection.commit()

        return run_id

    def get_next_version_number(
        self,
        analysis_run_id: int,
    ) -> int:
        query = """
            SELECT COALESCE(
                MAX(version_number),
                0
            ) + 1
            FROM ai_report_versions
            WHERE analysis_run_id = %s;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (analysis_run_id,),
                )

                row = cursor.fetchone()

        return int(row[0])

    def save_report_version(
        self,
        analysis_run_id: int,
        provider: str,
        model_name: str,
        prompt_version: str,
        schema_version: str,
        system_instructions: str,
        prompt_text: str,
        report_json: dict[str, Any],
        market_status: str,
        confidence_score: float,
        headline: str,
        input_tokens: int | None,
        output_tokens: int | None,
        reasoning_tokens: int | None,
        total_tokens: int | None,
        estimated_cost_usd: Decimal | None,
        latency_ms: int,
        response_id: str | None,
        response_status: str | None,
    ) -> int:
        version_number = (
            self.get_next_version_number(
                analysis_run_id,
            )
        )

        query = """
            INSERT INTO ai_report_versions (
                analysis_run_id,
                version_number,
                provider,
                model_name,
                prompt_version,
                schema_version,
                system_instructions,
                prompt_text,
                report_json,
                market_status,
                confidence_score,
                headline,
                input_tokens,
                output_tokens,
                reasoning_tokens,
                total_tokens,
                estimated_cost_usd,
                latency_ms,
                response_id,
                response_status,
                generation_status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s::jsonb,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'COMPLETED'
            )
            RETURNING id;
        """

        values = (
            analysis_run_id,
            version_number,
            provider,
            model_name,
            prompt_version,
            schema_version,
            system_instructions,
            prompt_text,
            json.dumps(
                report_json,
                ensure_ascii=False,
                allow_nan=False,
            ),
            market_status,
            confidence_score,
            headline,
            input_tokens,
            output_tokens,
            reasoning_tokens,
            total_tokens,
            estimated_cost_usd,
            latency_ms,
            response_id,
            response_status,
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    values,
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "Gagal menyimpan AI report version."
                    )

                report_version_id = int(
                    row[0],
                )

            connection.commit()

        return report_version_id

    def save_failed_version(
        self,
        analysis_run_id: int,
        provider: str,
        model_name: str,
        prompt_version: str,
        schema_version: str,
        system_instructions: str,
        prompt_text: str,
        error_message: str,
        latency_ms: int | None = None,
    ) -> int:
        version_number = (
            self.get_next_version_number(
                analysis_run_id,
            )
        )

        query = """
            INSERT INTO ai_report_versions (
                analysis_run_id,
                version_number,
                provider,
                model_name,
                prompt_version,
                schema_version,
                system_instructions,
                prompt_text,
                generation_status,
                error_message,
                latency_ms
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'FAILED',
                %s,
                %s
            )
            RETURNING id;
        """

        values = (
            analysis_run_id,
            version_number,
            provider,
            model_name,
            prompt_version,
            schema_version,
            system_instructions,
            prompt_text,
            error_message,
            latency_ms,
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    values,
                )

                row = cursor.fetchone()

                report_version_id = int(
                    row[0],
                )

            connection.commit()

        return report_version_id

    def mark_run_completed(
        self,
        analysis_run_id: int,
    ) -> None:
        query = """
            UPDATE ai_analysis_runs
            SET
                status = 'COMPLETED',
                completed_at = NOW(),
                error_message = NULL
            WHERE id = %s;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (analysis_run_id,),
                )

            connection.commit()

    def mark_run_failed(
        self,
        analysis_run_id: int,
        error_message: str,
    ) -> None:
        query = """
            UPDATE ai_analysis_runs
            SET
                status = 'FAILED',
                completed_at = NOW(),
                error_message = %s
            WHERE id = %s;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        error_message,
                        analysis_run_id,
                    ),
                )

            connection.commit()

    def get_latest_report(
        self,
        report_type: str = "national",
    ) -> dict[str, Any] | None:
        query = """
            SELECT
                ar.id AS analysis_run_id,
                ar.analysis_date,
                ar.context_hash,
                rv.id AS report_version_id,
                rv.version_number,
                rv.provider,
                rv.model_name,
                rv.market_status,
                rv.confidence_score,
                rv.headline,
                rv.report_json,
                rv.input_tokens,
                rv.output_tokens,
                rv.total_tokens,
                rv.estimated_cost_usd,
                rv.latency_ms,
                rv.generated_at
            FROM ai_analysis_runs ar
            JOIN ai_report_versions rv
                ON rv.analysis_run_id = ar.id
            WHERE
                ar.report_type = %s
                AND ar.status = 'COMPLETED'
                AND rv.generation_status = 'COMPLETED'
            ORDER BY
                rv.generated_at DESC
            LIMIT 1;
        """

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (report_type,),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                columns = [
                    description[0]
                    for description
                    in cursor.description
                ]


        record = dict(
            zip(
                columns,
                row,
            )
        )

        return serialize_database_record(record)
    