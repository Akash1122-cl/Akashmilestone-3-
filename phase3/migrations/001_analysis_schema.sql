-- Phase 3: Analysis and Clustering Database Schema
-- This migration creates tables for storing clustering results, themes, and validation data

-- Analysis runs table
CREATE TABLE IF NOT EXISTS analysis_runs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    analysis_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_reviews INTEGER NOT NULL,
    num_clusters INTEGER NOT NULL,
    num_themes INTEGER NOT NULL,
    processing_time_seconds FLOAT NOT NULL,
    clustering_quality_metrics JSONB,
    validation_result JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for analysis_runs
CREATE INDEX IF NOT EXISTS idx_analysis_runs_product_id ON analysis_runs(product_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_timestamp ON analysis_runs(analysis_timestamp);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);

-- Themes table
CREATE TABLE IF NOT EXISTS themes (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    theme_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_size INTEGER NOT NULL,
    sentiment_score FLOAT NOT NULL DEFAULT 0.5,
    quality_score FLOAT NOT NULL DEFAULT 0.5,
    representative_quotes JSONB NOT NULL DEFAULT '[]'::jsonb,
    action_ideas JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(analysis_run_id, theme_id)
);

-- Indexes for themes
CREATE INDEX IF NOT EXISTS idx_themes_analysis_run_id ON themes(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_themes_cluster_id ON themes(cluster_id);
CREATE INDEX IF NOT EXISTS idx_themes_quality_score ON themes(quality_score);

-- Cluster assignments table (maps reviews to clusters)
CREATE TABLE IF NOT EXISTS cluster_assignments (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    review_id VARCHAR(255) NOT NULL,
    cluster_id INTEGER NOT NULL,
    is_noise BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(analysis_run_id, review_id)
);

-- Indexes for cluster_assignments
CREATE INDEX IF NOT EXISTS idx_cluster_assignments_analysis_run_id ON cluster_assignments(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_cluster_assignments_review_id ON cluster_assignments(review_id);
CREATE INDEX IF NOT EXISTS idx_cluster_assignments_cluster_id ON cluster_assignments(cluster_id);

-- Validation results table
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    analysis_run_id INTEGER NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    is_valid BOOLEAN NOT NULL,
    quote_accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    theme_coherence_score FLOAT NOT NULL DEFAULT 0.0,
    action_relevance_score FLOAT NOT NULL DEFAULT 0.0,
    overall_quality_score FLOAT NOT NULL DEFAULT 0.0,
    validation_errors JSONB DEFAULT '[]'::jsonb,
    validation_warnings JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(analysis_run_id)
);

-- Indexes for validation_results
CREATE INDEX IF NOT EXISTS idx_validation_results_analysis_run_id ON validation_results(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_validation_results_is_valid ON validation_results(is_valid);
CREATE INDEX IF NOT EXISTS idx_validation_results_quality_score ON validation_results(overall_quality_score);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_analysis_runs_updated_at BEFORE UPDATE ON analysis_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_themes_updated_at BEFORE UPDATE ON themes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE analysis_runs IS 'Stores metadata and results of analysis runs';
COMMENT ON TABLE themes IS 'Stores discovered themes from clustering analysis';
COMMENT ON TABLE cluster_assignments IS 'Maps individual reviews to their cluster assignments';
COMMENT ON TABLE validation_results IS 'Stores validation results for analysis runs';

COMMENT ON COLUMN analysis_runs.clustering_quality_metrics IS 'JSONB containing silhouette_score, davies_bouldin_score, calinski_harabasz_score';
COMMENT ON COLUMN themes.representative_quotes IS 'JSONB array of representative quote strings';
COMMENT ON COLUMN themes.action_ideas IS 'JSONB array of actionable suggestion strings';
COMMENT ON COLUMN cluster_assignments.confidence_score IS 'Confidence score for cluster assignment (if available)';
