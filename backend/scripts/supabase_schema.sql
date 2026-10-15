-- Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Tabel projects
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    files JSONB DEFAULT '[]'::jsonb,
    total_text_length INTEGER DEFAULT 0,
    ontology JSONB NULL,
    analysis_summary TEXT NULL,
    graph_id VARCHAR(128) NULL,
    graph_build_task_id VARCHAR(128) NULL,
    zep_batch_id VARCHAR(128) NULL,
    zep_batch_operation_id VARCHAR(128) NULL,
    simulation_requirement TEXT NULL,
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,
    error TEXT NULL,
    description TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- Tabel tasks
CREATE TABLE IF NOT EXISTS tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    task_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    message TEXT DEFAULT '',
    result JSONB NULL,
    error TEXT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    progress_detail JSONB DEFAULT '{}'::jsonb,
    params_json TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- Tabel jobs
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES tasks(task_id) ON DELETE CASCADE,
    project_id VARCHAR(64) NOT NULL,
    state VARCHAR(32) DEFAULT 'queued',
    pid INTEGER NULL,
    current_round INTEGER DEFAULT 0,
    total_rounds INTEGER DEFAULT 10,
    progress_pct FLOAT DEFAULT 0.0,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_task_id ON jobs(task_id);

-- Tabel checkpoints
CREATE TABLE IF NOT EXISTS checkpoints (
    id VARCHAR(64) PRIMARY KEY,
    job_id VARCHAR(64) REFERENCES jobs(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    snapshot_path VARCHAR(512) NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_checkpoints_job_id ON checkpoints(job_id);

-- Tabel platforms_config
CREATE TABLE IF NOT EXISTS platforms_config (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    platform VARCHAR(32) NOT NULL,
    params_json TEXT NOT NULL
);

-- Tabel research_reports
CREATE TABLE IF NOT EXISTS research_reports (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    query VARCHAR(512) NOT NULL,
    research_type VARCHAR(32) DEFAULT 'general',
    facts_json TEXT NULL,
    entities_json TEXT NULL,
    trends_json TEXT NULL,
    credibility_score FLOAT DEFAULT 0.0,
    raw_results_json TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabel settings
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(128) PRIMARY KEY,
    value_encrypted TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabel audit_log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    actor VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource_id VARCHAR(64) NULL,
    details_json TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
