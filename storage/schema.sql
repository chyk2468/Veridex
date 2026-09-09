-- SQLite Schema for Fact Knowledge Layer

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    page_count INTEGER NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',
    processing_duration REAL,
    extraction_method TEXT,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    extraction_method TEXT,
    metadata JSON,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_id TEXT,
    page_number INTEGER NOT NULL,
    section TEXT,
    text TEXT NOT NULL,
    bbox JSON,
    evidence_type TEXT DEFAULT 'text',
    extraction_method TEXT,
    confidence REAL DEFAULT 1.0,
    document_name TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS facts (
    fact_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,
    value_type TEXT DEFAULT 'numeric',
    numeric_value REAL,
    canonical_value REAL,
    unit TEXT,
    canonical_unit TEXT,
    currency TEXT,
    period_label TEXT,
    period_type TEXT,
    start_date TEXT,
    end_date TEXT,
    geographic_scope TEXT DEFAULT 'India',
    population_scope TEXT,
    business_scope TEXT,
    category TEXT DEFAULT 'general',
    qualifiers JSON,
    raw_text TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    evidence_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    document_name TEXT,
    extraction_status TEXT DEFAULT 'valid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relationships (
    relationship_id TEXT PRIMARY KEY,
    fact_a_id TEXT NOT NULL,
    fact_b_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    comparison_features JSON,
    confidence REAL DEFAULT 1.0,
    confidence_breakdown JSON,
    explanation TEXT NOT NULL,
    evidence_a_id TEXT,
    evidence_b_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fact_a_id) REFERENCES facts(fact_id) ON DELETE CASCADE,
    FOREIGN KEY (fact_b_id) REFERENCES facts(fact_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS processing_runs (
    run_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    facts_extracted INTEGER DEFAULT 0,
    relationships_found INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high-performance querying
CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_doc ON evidence(document_id);
CREATE INDEX IF NOT EXISTS idx_facts_doc ON facts(document_id);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);
CREATE INDEX IF NOT EXISTS idx_facts_period ON facts(period_label);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_facts ON relationships(fact_a_id, fact_b_id);
