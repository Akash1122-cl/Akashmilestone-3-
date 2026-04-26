# Phase 2: Data Processing Pipeline

## Overview

Phase 2 implements the data processing pipeline that transforms raw review data from Phase 1 into structured, analyzed, and searchable information using embeddings, quality analysis, and vector storage.

## Architecture

### Core Components

1. **Review Preprocessor** - Text cleaning, language detection, deduplication
2. **Embedding Service** - OpenAI text-embedding-3-small integration
3. **Data Quality Pipeline** - Quality metrics and anomaly detection
4. **Vector Database** - Pinecone integration for similarity search
5. **Cache Manager** - Redis/memory caching for performance
6. **FastAPI Endpoints** - RESTful API for processing operations
7. **Celery Tasks** - Background processing and scheduled tasks

## Installation

### Prerequisites

```bash
# Python dependencies
pip install -r requirements.txt

# External services
- Redis (for caching and Celery)
- Pinecone (for vector database)
- OpenAI API key (for embeddings)

# Optional dependencies
pip install langdetect textblob sentence-transformers
```

### Configuration

Copy and configure the environment variables:

```bash
# Environment variables
export OPENAI_API_KEY="your-openai-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export REDIS_PASSWORD="your-redis-password"
export DB_PASSWORD="your-db-password"
```

## Usage

### Starting the Services

```bash
# Start Redis
redis-server

# Start Celery worker
celery -A src.tasks worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A src.tasks beat --loglevel=info

# Start FastAPI server
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### API Endpoints

#### Preprocessing
- `POST /preprocess/single` - Process single review
- `POST /preprocess/batch` - Process batch of reviews

#### Embeddings
- `POST /embeddings/generate` - Generate embedding for text
- `POST /embeddings/batch` - Generate embeddings for batch
- `GET /embeddings/stats` - Get embedding service statistics

#### Quality Analysis
- `POST /quality/analyze` - Analyze quality of reviews
- `POST /quality/metrics` - Get quality metrics

#### Vector Database
- `POST /vectors/index` - Create vector index from reviews
- `POST /vectors/search` - Search similar vectors
- `GET /vectors/stats` - Get vector database statistics

#### Complete Pipeline
- `POST /process/complete` - Run complete processing pipeline

#### Health & Monitoring
- `GET /health` - Health check
- `GET /stats/overview` - Overview statistics
- `GET /` - Service information

## Processing Pipeline

### 1. Review Preprocessing

```python
from review_preprocessor import ReviewPreprocessor

preprocessor = ReviewPreprocessor(config)
processed_reviews = preprocessor.process_batch(raw_reviews)
```

**Features:**
- Text cleaning (HTML, URLs, special characters)
- Language detection (English focus)
- Duplicate detection and removal
- Quality scoring
- Sentiment analysis
- Metadata enrichment

### 2. Embedding Generation

```python
from embedding_service import EmbeddingService

embedding_service = EmbeddingService(config)
reviews_with_embeddings = embedding_service.process_reviews_embeddings(processed_reviews)
```

**Features:**
- OpenAI text-embedding-3-small model
- Fallback to sentence-transformers
- Batch processing (100 reviews/batch)
- Caching for performance
- Error handling and retries

### 3. Quality Analysis

```python
from data_quality_pipeline import DataQualityPipeline

quality_pipeline = DataQualityPipeline(config)
quality_report = quality_pipeline.generate_quality_report(reviews_with_embeddings)
```

**Features:**
- Quality scoring (excellent, good, acceptable, poor)
- Anomaly detection (rating spikes, spam, bots)
- Comprehensive metrics
- Actionable recommendations

### 4. Vector Indexing

```python
from vector_database import VectorDatabase

vector_db = VectorDatabase(config)
success = vector_db.create_index_from_reviews(reviews_with_embeddings)
```

**Features:**
- Pinecone vector database integration
- Similarity search
- Metadata filtering
- Index statistics and monitoring

## Background Tasks

### Celery Tasks

```bash
# Process reviews in background
celery -A src.tasks call tasks.preprocess_batch_task --args='[reviews]'

# Generate embeddings
celery -A src.tasks call tasks.generate_embeddings_batch_task --args='[reviews]'

# Quality analysis
celery -A src.tasks call tasks.quality_analysis_batch_task --args='[reviews]'

# Complete pipeline
celery -A src.tasks call tasks.complete_processing_pipeline_task --args='[reviews]'
```

### Scheduled Tasks

- **Quality Check**: Every 6 hours
- **Cache Cleanup**: Daily at 2 AM UTC
- **Vector Index Maintenance**: Daily at 3 AM UTC
- **Health Check**: Every 30 minutes

## Caching Strategy

### Redis Cache

```python
from cache_manager import CacheManager

cache_manager = CacheManager(config)

# Cache embeddings
cache_manager.set_embedding(text, embedding, ttl=86400)

# Get cached embedding
embedding = cache_manager.get_embedding(text)

# Cache processed reviews
cache_manager.set_processed_review(review_id, review_data)
```

### Cache Types

- **Embeddings**: 24-hour TTL
- **Processed Reviews**: 1-hour TTL
- **Quality Metrics**: 6-hour TTL
- **Search Results**: 30-minute TTL

## Performance Optimization

### Batch Processing

- **Preprocessing**: 1000 reviews/batch
- **Embeddings**: 100 reviews/batch
- **Vector Operations**: 100 vectors/batch

### Caching

- **Hit Rate**: Target >80%
- **Memory Usage**: <2GB
- **Redis Memory**: Configurable limits

### Monitoring

```python
# Get service statistics
GET /stats/overview

# Get component health
GET /health

# Get embedding stats
GET /embeddings/stats

# Get vector stats
GET /vectors/stats
```

## Quality Metrics

### Review Quality Levels

- **Excellent** (80-100%): High-quality, detailed reviews
- **Good** (60-79%): Useful reviews with decent content
- **Acceptable** (40-59%): Basic reviews, minimal content
- **Poor** (20-39%): Low-quality, potential spam
- **Very Poor** (0-19%): Spam or bot-generated

### Anomaly Detection

- **Rating Spikes**: Statistical outliers in ratings
- **Text Length Anomalies**: Unusually short/long reviews
- **Sentiment Anomalies**: Rating-sentiment mismatches
- **Spam Patterns**: Promotional content, URLs
- **Bot Patterns**: Generic usernames, repetitive content

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_review_preprocessor.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run integration tests
pytest tests/ -m integration
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Mock Tests**: External service mocking
- **Performance Tests**: Load and stress testing

## Configuration

### Key Settings

```yaml
preprocessing:
  target_language: en
  min_text_length: 10
  max_text_length: 5000
  quality_threshold: 0.3

embeddings:
  model: text-embedding-3-small
  batch_size: 100
  cache_enabled: true

vector_database:
  index_name: review-embeddings
  dimension: 1536
  metric: cosine

cache_manager:
  default_backend: memory
  redis:
    enabled: true
    prefix: phase2:
```

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `PINECONE_API_KEY`: Pinecone API key
- `REDIS_PASSWORD`: Redis password
- `DB_PASSWORD`: Database password
- `JWT_SECRET`: JWT secret for authentication

## Troubleshooting

### Common Issues

1. **OpenAI API Rate Limits**
   - Reduce batch size
   - Implement exponential backoff
   - Use fallback models

2. **Pinecone Connection Issues**
   - Check API key
   - Verify index configuration
   - Monitor quota limits

3. **Redis Connection Problems**
   - Verify Redis server running
   - Check connection parameters
   - Monitor memory usage

4. **Memory Issues**
   - Reduce batch sizes
   - Enable caching
   - Monitor process memory

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug mode
uvicorn src.main:app --reload --log-level debug
```

## Monitoring and Logging

### Log Levels

- **INFO**: General operation information
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **DEBUG**: Detailed debugging information

### Metrics

- **Processing Speed**: Reviews/second
- **Cache Hit Rate**: Percentage
- **Quality Scores**: Distribution
- **Error Rates**: By component
- **Resource Usage**: CPU, memory, network

## Next Steps

### Phase 3 Preparation

Phase 2 provides the foundation for Phase 3 (Analysis and Clustering):

1. **Vector embeddings** ready for clustering
2. **Quality metrics** for filtering
3. **Search capabilities** for similarity analysis
4. **Processing pipeline** for continuous data flow

### Scaling Considerations

- **Horizontal Scaling**: Multiple workers
- **Database Scaling**: Connection pooling
- **Cache Scaling**: Redis clustering
- **API Scaling**: Load balancing

## Security

### Data Protection

- **PII Removal**: No personal data stored
- **Encryption**: Data in transit encryption
- **Access Control**: API key authentication
- **Audit Logging**: Operation tracking

### API Security

- **Rate Limiting**: 100 requests/minute
- **CORS**: Configurable origins
- **Authentication**: JWT tokens (optional)
- **Input Validation**: Comprehensive validation

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd phase2

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server
uvicorn src.main:app --reload
```

### Code Quality

- **Linting**: flake8, black
- **Type Hints**: mypy
- **Testing**: pytest, coverage
- **Documentation**: docstrings, README

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Check the test cases for examples
4. Create an issue with detailed information

---

**Phase 2 Status**: ✅ Complete  
**Next Phase**: Phase 3 - Analysis and Clustering  
**Last Updated**: 2024-01-26
