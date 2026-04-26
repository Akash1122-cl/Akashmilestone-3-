# Groww Data Collection Documentation

## Overview
This document captures the data collection process, parameters, and context for Groww reviews from Google Play Store as part of Phase 1 implementation.

## Data Collection Parameters

### Google Play Store Configuration
- **Target Product**: Groww (com.groww)
- **Data Source**: Google Play Store
- **Collection Method**: Web scraping with play-scraper library
- **Review Limit**: Up to 1000 effective reviews
- **Time Window**: Last 8 weeks (56 days)
- **Language Filter**: English reviews only
- **Deduplication**: Enabled across runs
- **Effective Reviews Only**: Enabled (filters out spam/low-quality reviews)

### App Store Configuration
- **Status**: Disabled
- **Reason**: Focus on Google Play Store data only
- **Future**: Can be enabled if needed

## Data Schema

### Review Data Structure
```json
{
  "external_review_id": "gp_review_123",
  "title": "Great investment app!",
  "review_text": "Very user friendly interface and good features",
  "author_name": "John Doe",
  "rating": 5,
  "review_date": "2024-01-15T12:00:00Z",
  "review_url": "https://play.google.com/store/apps/details?id=com.groww&reviewId=123",
  "version": "2.1.0",
  "source": "google_play",
  "product_id": 1
}
```

### Product Data Structure
```json
{
  "id": 1,
  "name": "Groww",
  "app_store_id": "987654321",
  "play_store_url": "https://play.google.com/store/apps/details?id=com.groww",
  "enabled": true,
  "sources": {
    "app_store": false,
    "google_play": true
  }
}
```

## Collection Process

### 1. Manual Trigger
```bash
# Trigger Google Play ingestion
curl -X POST http://localhost:8000/ingest/google-play/1

# Response
{
  "status": "completed",
  "log_id": 123,
  "product": "Groww",
  "source": "google_play",
  "reviews_collected": 1000,
  "reviews_processed": 950,
  "duration_seconds": 180,
  "error": null
}
```

### 2. Scheduled Collection
- **Frequency**: Daily at 2:00 AM UTC
- **Method**: Celery background task
- **Task**: `ingest_google_play_task`
- **Retry Logic**: Exponential backoff (60s, 120s, 240s)

### 3. Data Processing Pipeline
1. **Fetch**: Retrieve reviews from Google Play Store
2. **Filter**: Apply effective reviews filter
3. **Parse**: Extract structured data
4. **Deduplicate**: Check against existing reviews
5. **Store**: Save to PostgreSQL database
6. **Log**: Record ingestion statistics

## Quality Assurance

### Data Validation Rules
- **Rating Range**: 1-5 stars
- **Required Fields**: review_text, author_name, rating, review_date
- **Date Format**: ISO 8601 (UTC)
- **Text Length**: Minimum 10 characters
- **Language**: English only (detected via library)

### Data Quality Metrics
- **Collection Success Rate**: Target >95%
- **Parse Success Rate**: Target >98%
- **Deduplication Accuracy**: Target >99%
- **Data Freshness**: Reviews within 8 weeks

## Context Share Information

### Business Context
- **Product Type**: Investment/Trading App
- **Target Market**: Indian retail investors
- **Use Case**: Weekly product review pulse for stakeholders
- **Review Focus**: User experience, features, bugs, suggestions

### Technical Context
- **Scraping Strategy**: Proxy rotation with user agents
- **Rate Limiting**: Respect Google Play policies
- **Error Handling**: Retry with exponential backoff
- **Monitoring**: Redis caching + PostgreSQL logging

### Data Usage Context
- **Primary Consumers**: Product managers, UX team, executives
- **Analysis Purpose**: Theme clustering, sentiment analysis, feature feedback
- **Reporting**: Weekly summary reports
- **Action Items**: Product improvements based on feedback

## Storage and Access

### Database Schema
```sql
-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    app_store_id VARCHAR(100),
    play_store_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table  
CREATE TABLE reviews (
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
```

### Access Methods
- **API Endpoints**: `/reviews`, `/products`, `/ingestion/logs`
- **Direct Database**: PostgreSQL connection
- **Export**: CSV/JSON via API
- **Real-time**: WebSocket streaming (future)

## Monitoring and Maintenance

### Collection Monitoring
- **Success Rate**: Reviews collected vs. expected
- **Error Tracking**: Failed requests, parsing errors
- **Performance**: Collection time per review
- **Storage**: Database size, growth rate

### Health Checks
- **API Status**: Google Play Store accessibility
- **Proxy Health**: Rotating proxy performance
- **Database Status**: Connection, query performance
- **Cache Status**: Redis hit/miss ratios

## Compliance and Ethics

### Data Collection Compliance
- **Terms of Service**: Google Play Store ToS compliance
- **Rate Limiting**: Respect API limits
- **User Privacy**: No personal data beyond public reviews
- **Data Retention**: Reviews stored for analysis purposes only

### Ethical Considerations
- **Transparency**: Clear data collection methodology
- **Purpose Limitation**: Use only for stated business purposes
- **Data Minimization**: Collect only necessary review data
- **User Rights**: Respect user-generated content rights

## Future Enhancements

### Planned Improvements
- **Additional Sources**: App Store (if enabled), third-party review sites
- **Advanced Filtering**: Sentiment-based filtering, topic-specific collection
- **Real-time Collection**: Continuous monitoring instead of daily batches
- **Machine Learning**: Automated quality scoring and spam detection

### Scaling Considerations
- **Multiple Products**: Support for additional fintech apps
- **Increased Volume**: Handle 10,000+ reviews per product
- **Faster Processing**: Parallel collection and processing
- **Cloud Storage**: Archive historical data for trend analysis

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-26  
**Next Review**: 2024-02-02  
**Owner**: Phase 1 Development Team
