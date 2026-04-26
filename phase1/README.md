# Phase 1: Data Ingestion Foundation

## Overview
Phase 1 implements the data ingestion foundation for the Weekly Product Review Pulse system. This phase focuses on collecting reviews from Apple App Store (RSS) and Google Play Store (web scraping) for Groww.

## Components

### 1. Database Schema6
- **Products table**: Stores Groww app information
- **Reviews table**: Stores collected reviews with deduplication
- **Ingestion logs table**: Tracks data collection runs and their status

### 2. Ingestion Services
- **AppStore Ingestor**: Collects reviews from iTunes Customer Reviews RSS feed
- **GooglePlay Ingestor**: Scrapes reviews from Google Play Store with proxy rotation

### 3. Infrastructure
- **PostgreSQL**: Primary database for storing reviews
- **Redis**: Caching layer for deduplication and performance
- **FastAPI**: REST API for triggering ingestion and health checks
- **Celery**: Background task queue for scheduled ingestion

## Project Structure
```
phase1/
├── config/
│   └── config.yaml          # Application configuration
├── migrations/
│   └── 001_init_schema.sql  # Database schema
├── src/
│   ├── appstore_ingestor.py  # App Store RSS ingestor
│   ├── googleplay_ingestor.py # Google Play scraper
│   ├── database.py           # Database models and connection
│   ├── redis_cache.py        # Redis caching layer
│   ├── config_manager.py     # Configuration management
│   ├── logger.py             # Logging configuration
│   ├── main.py               # FastAPI application
│   └── tasks.py              # Celery background tasks
├── tests/                    # Test files
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Container definition
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL client tools (optional)

### Quick Start with Docker

1. **Clone and navigate to phase1 directory**
   ```bash
   cd phase1
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker-compose ps
   ```

5. **Check health status**
   ```bash
   curl http://localhost:8000/health
   ```

### Local Development Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL**
   ```bash
   # Using Docker
   docker run -d --name postgres \
     -e POSTGRES_DB=review_pulse \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Set up Redis**
   ```bash
   # Using Docker
   docker run -d --name redis \
     -p 6379:6379 \
     redis:7-alpine
   ```

4. **Run database migrations**
   ```bash
   psql -h localhost -U postgres -d review_pulse -f migrations/001_init_schema.sql
   ```

5. **Start the API server**
   ```bash
   cd src
   python main.py
   ```

6. **Start Celery worker (separate terminal)**
   ```bash
   cd src
   celery -A tasks worker --loglevel=info
   ```

7. **Start Celery beat scheduler (separate terminal)**
   ```bash
   cd src
   celery -A tasks beat --loglevel=info
   ```

## API Endpoints

### Health Check
```bash
GET /health
```
Returns system health status including database and Redis connectivity.

### Products
```bash
GET /products              # List all products
GET /products/{id}         # Get specific product
```

### Ingestion
```bash
POST /ingest/app-store/{product_id}    # Trigger App Store ingestion
POST /ingest/google-play/{product_id}  # Trigger Google Play ingestion
POST /ingest/all                        # Ingest all products
```

### Logs and Stats
```bash
GET /ingestion/logs       # Get ingestion logs
GET /stats                # Get system statistics
```

## Configuration

Edit `config/config.yaml` to customize:

- **Database connection settings**
- **Redis connection settings**
- **App Store RSS feed parameters**
- **Google Play scraping settings**
- **Product configurations**
- **Ingestion schedule**
- **Logging configuration**

## Scheduled Ingestion

The system uses Celery Beat for scheduled tasks:
- **Daily ingestion**: Runs at 2 AM UTC by default
- **Health checks**: Every 5 minutes

To modify the schedule, edit the `beat_schedule` in `src/tasks.py`.

## Monitoring

### Logs
Logs are stored in the `logs/` directory with automatic rotation:
- `ingestion.log`: Main application logs
- JSON format for structured logging
- 10MB max file size with 5 backup files

### Health Monitoring
Use the `/health` endpoint to monitor:
- Database connectivity
- Redis connectivity
- Redis statistics (keys, memory, hits/misses)

### Ingestion Monitoring
Use the `/ingestion/logs` endpoint to track:
- Ingestion status (success/partial/failed)
- Reviews collected vs processed
- Duration and error messages

## Testing

Run tests (to be implemented):
```bash
pytest tests/
```

## Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running: `docker-compose ps postgres`
- Verify credentials in `.env` file
- Check database logs: `docker-compose logs postgres`

### Redis Connection Issues
- Check Redis is running: `docker-compose ps redis`
- Verify Redis password in configuration
- Test connection: `redis-cli ping`

### Ingestion Failures
- Check ingestion logs: `docker-compose logs ingestion_service`
- Verify product IDs and URLs in configuration
- Check for rate limiting or scraping blocks
- Review error messages in `/ingestion/logs`

### Google Play Scraping Issues
- Ensure proxy configuration is correct
- Check if proxies are working
- Consider using play-scraper library
- Monitor for CAPTCHA challenges

## Evaluation Criteria

Phase 1 success is measured by:

- **Data Collection Success Rate**: ≥95% of available reviews collected
- **Data Coverage**: Groww product
- **Data Freshness**: Reviews within 24 hours
- **Ingestion Speed**: ≥100 reviews/minute
- **Service Uptime**: ≥95% availability
- **Duplicate Prevention**: <1% duplicate rate

## Next Steps

After completing Phase 1:
1. Verify data quality and completeness
2. Set up monitoring and alerting
3. Proceed to Phase 2: Data Processing Pipeline

## Notes

- The system uses exponential backoff for retries
- Redis caching helps prevent duplicate ingestion
- Database schema includes triggers for automatic timestamp updates
- All configuration is externalized in YAML files
- Logging is structured JSON for easy parsing
