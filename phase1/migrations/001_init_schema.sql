-- Phase 1: Database Schema Initialization
-- This schema supports review ingestion from App Store and Google Play

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    app_store_id VARCHAR(100),
    play_store_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL CHECK (source IN ('app_store', 'google_play')),
    external_review_id VARCHAR(255) NOT NULL,
    review_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    author_name VARCHAR(255),
    review_date TIMESTAMP NOT NULL,
    review_url TEXT,
    version VARCHAR(50),
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, source, external_review_id)
);

-- Ingestion logs table
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL CHECK (source IN ('app_store', 'google_play')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    reviews_collected INTEGER DEFAULT 0,
    reviews_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_reviews_review_date ON reviews(review_date DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_external_id ON reviews(product_id, source, external_review_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_product ON ingestion_logs(product_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_logs_date ON ingestion_logs(started_at DESC);

-- Insert initial product (Groww only)
INSERT INTO products (name, app_store_id, play_store_url) VALUES
('Groww', '987654321', 'https://play.google.com/store/apps/details?id=com.groww')
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
