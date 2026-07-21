CREATE TABLE IF NOT EXISTS ai_analysis_runs (
    id BIGSERIAL PRIMARY KEY,

    report_type VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,

    context_version VARCHAR(30) NOT NULL,
    context_hash VARCHAR(64) NOT NULL,
    context_json JSONB NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',

    source_score_records INTEGER NOT NULL DEFAULT 0,
    source_province_records INTEGER NOT NULL DEFAULT 0,
    source_analytics_records INTEGER NOT NULL DEFAULT 0,

    covered_province_count INTEGER,
    province_coverage_percentage NUMERIC(6, 2),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT chk_ai_analysis_run_status
        CHECK (
            status IN (
                'PENDING',
                'PROCESSING',
                'COMPLETED',
                'PARTIAL',
                'FAILED'
            )
        )
);


CREATE TABLE IF NOT EXISTS ai_report_versions (
    id BIGSERIAL PRIMARY KEY,

    analysis_run_id BIGINT NOT NULL
        REFERENCES ai_analysis_runs(id)
        ON DELETE CASCADE,

    version_number INTEGER NOT NULL,

    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,

    prompt_version VARCHAR(30) NOT NULL,
    schema_version VARCHAR(30) NOT NULL,

    system_instructions TEXT,
    prompt_text TEXT NOT NULL,

    report_json JSONB,

    market_status VARCHAR(30),
    confidence_score NUMERIC(6, 2),
    headline TEXT,

    input_tokens INTEGER,
    output_tokens INTEGER,
    reasoning_tokens INTEGER,
    total_tokens INTEGER,

    estimated_cost_usd NUMERIC(12, 8),
    latency_ms INTEGER,

    response_id VARCHAR(255),
    response_status VARCHAR(50),

    generation_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    error_message TEXT,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ai_report_run_version
        UNIQUE (analysis_run_id, version_number),

    CONSTRAINT chk_ai_report_generation_status
        CHECK (
            generation_status IN (
                'PENDING',
                'COMPLETED',
                'FAILED',
                'REFUSED',
                'INCOMPLETE'
            )
        )
);


CREATE INDEX IF NOT EXISTS idx_ai_analysis_runs_date
    ON ai_analysis_runs (analysis_date DESC);


CREATE INDEX IF NOT EXISTS idx_ai_analysis_runs_type_date
    ON ai_analysis_runs (
        report_type,
        analysis_date DESC
    );


CREATE INDEX IF NOT EXISTS idx_ai_analysis_runs_context_hash
    ON ai_analysis_runs (context_hash);


CREATE INDEX IF NOT EXISTS idx_ai_report_versions_run
    ON ai_report_versions (
        analysis_run_id,
        version_number DESC
    );


CREATE INDEX IF NOT EXISTS idx_ai_report_versions_model
    ON ai_report_versions (
        provider,
        model_name,
        generated_at DESC
    );


CREATE INDEX IF NOT EXISTS idx_ai_report_versions_status
    ON ai_report_versions (
        market_status,
        generated_at DESC
    );


CREATE INDEX IF NOT EXISTS idx_ai_report_versions_report_json
    ON ai_report_versions
    USING GIN (report_json);