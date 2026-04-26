# Phase 3: Analysis and Clustering

This phase implements clustering algorithms and LLM-based theme analysis for customer reviews.

## Overview

Phase 3 builds on the data processing pipeline from Phase 2 to:
- Cluster review embeddings using UMAP + HDBSCAN
- Generate meaningful themes with GPT-4
- Validate analysis results for quality assurance

## Components

### 1. Clustering Engine (`src/clustering_engine.py`)
- **UMAP** for dimensionality reduction
- **HDBSCAN** for density-based clustering
- Parameter optimization framework
- Cluster quality metrics (silhouette, Davies-Bouldin, Calinski-Harabasz)

### 2. Theme Analyzer (`src/theme_analyzer.py`)
- **GPT-4 integration** for theme naming and description
- Representative quote extraction
- Action idea generation
- Quality scoring for themes

### 3. Validation Framework (`src/validation_framework.py`)
- Quote verification against source reviews
- Theme consistency checking
- Action idea relevance validation
- Overall quality scoring

### 4. Database (`src/database.py`)
- PostgreSQL schema for analysis results
- Storage for themes, clusters, and validation data
- Query endpoints for historical analysis

### 5. API (`src/main.py`)
- FastAPI endpoints for clustering and analysis
- Full analysis pipeline endpoint
- Database query endpoints

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages
- `umap-learn` - Dimensionality reduction
- `hdbscan` - Density-based clustering
- `scikit-learn` - Quality metrics
- `openai` - GPT-4 API
- `fastapi` - API framework
- `psycopg2-binary` - PostgreSQL adapter
- `rapidfuzz` - Fuzzy string matching (optional)

## Configuration

Edit `config/config.yaml` to configure:

```yaml
# Clustering parameters
clustering:
  umap:
    n_components: 15
    n_neighbors: 15
    min_dist: 0.1
  hdbscan:
    min_cluster_size: 5
    min_samples: 3

# LLM configuration
theme_analyzer:
  llm:
    model: gpt-4
    api_key: ${OPENAI_API_KEY}

# Validation settings
validation:
  quote_verification:
    fuzzy_match_threshold: 0.85
  quality_scoring:
    min_quality_score: 0.7
```

## Database Setup

Run the migration script:

```bash
psql -U postgres -d review_pulse -f migrations/001_analysis_schema.sql
```

## Running the Application

### Development Mode

```bash
cd src
python main.py
```

The API will be available at `http://localhost:8002`

### Production Mode

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8002 --workers 4
```

## API Endpoints

### Health Check
```
GET /health
```

### Clustering
```
POST /api/v1/cluster
Content-Type: application/json

{
  "embeddings": [[0.1, 0.2, ...], ...],
  "review_ids": ["review_1", "review_2", ...],
  "optimize_parameters": false
}
```

### Theme Analysis
```
POST /api/v1/analyze-themes
Content-Type: application/json

{
  "clusters": {
    "0": [{"id": "1", "text": "..."}, ...],
    "1": [{"id": "2", "text": "..."}, ...]
  },
  "reviews": [{"id": "1", "text": "..."}, ...]
}
```

### Validation
```
POST /api/v1/validate
Content-Type: application/json

{
  "themes": [...],
  "reviews": [...]
}
```

### Full Analysis Pipeline
```
POST /api/v1/full-analysis
Content-Type: application/json

{
  "product_id": 1,
  "product_name": "TestApp",
  "embeddings": [[0.1, 0.2, ...], ...],
  "review_ids": ["review_1", ...],
  "reviews": [...],
  "optimize_parameters": false
}
```

### Query Analysis Results
```
GET /api/v1/analysis/{analysis_run_id}
GET /api/v1/product/{product_id}/latest-analysis
```

## Testing

Run unit tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Success Criteria

- Generate 5-7 meaningful themes per product
- Theme validation accuracy > 85%
- Processing time < 5 minutes per product
- Action idea relevance score > 80%

## Architecture

```
┌─────────────────┐
│  Embeddings     │
│  (from Phase 2) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Clustering      │
│ Engine          │
│ (UMAP+HDBSCAN)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Theme Analyzer  │
│ (GPT-4)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validation      │
│ Framework       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Database        │
│ Storage         │
└─────────────────┘
```

## Mock Mode

If ML libraries or OpenAI are not available, the system automatically falls back to mock mode:
- Mock clustering using simple index-based assignment
- Mock theme generation with predefined templates
- Basic validation without fuzzy matching

## Troubleshooting

### ML Libraries Not Available
If you see "ML libraries not available" warnings:
```bash
pip install umap-learn hdbscan scikit-learn
```

### OpenAI API Errors
Check your API key in config.yaml:
```bash
export OPENAI_API_KEY=your_key_here
```

### Database Connection Errors
Verify PostgreSQL is running and credentials are correct:
```bash
psql -U postgres -d review_pulse -c "SELECT 1"
```

## Next Steps

- Phase 4: Report Generation
- Phase 5: MCP Integration and Delivery
- Phase 6: Production Deployment
