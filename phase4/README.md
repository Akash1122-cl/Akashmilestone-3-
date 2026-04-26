# Phase 4: Report Generation

This phase implements narrative building, report formatting, and quality assurance for generating weekly product review reports.

## Overview

Phase 4 builds on the analysis results from Phase 3 to:
- Generate narratives using Jinja2 templates and LLM integration
- Format reports in HTML and Markdown with one-page layouts
- Validate report quality through comprehensive checks

## Components

### 1. Narrative Builder (`src/narrative_builder.py`)
- **Jinja2 Template Engine** - Template-based content generation
- **LLM Integration** - GPT-4 for executive summary generation
- **Content Selection** - Top 5-7 themes by cluster size
- **Quote Ranking** - Representative quote extraction
- **Action Idea Generation** - LLM-powered actionable suggestions

### 2. Report Formatter (`src/report_formatter.py`)
- **HTML Formatting** - Styled one-page reports with CSS
- **Markdown Formatting** - Simple text-based reports
- **PDF Placeholder** - Framework for PDF generation
- **Branding Support** - Customizable company branding
- **Layout Validation** - One-page layout verification

### 3. Quality Assurance (`src/quality_assurance.py`)
- **Content Validation** - Theme count, quote count, action idea count
- **Format Validation** - Required sections, structure checks
- **Readability Scoring** - Sentence length, paragraph length analysis
- **Completeness Scoring** - Required elements verification
- **Overall Quality Score** - Weighted score combining all metrics

### 4. API (`src/main.py`)
- FastAPI endpoints for narrative building, formatting, and validation
- Full report generation pipeline endpoint
- Template rendering endpoint
- Health check endpoint

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
- `jinja2` - Template engine
- `openai` - GPT-4 API for executive summary
- `fastapi` - API framework
- `pyyaml` - Configuration management

## Configuration

Edit `config/config.yaml` to configure:

```yaml
narrative_builder:
  max_themes: 7
  min_themes: 5
  max_quotes_per_theme: 3
  llm:
    model: gpt-4
    api_key: ${OPENAI_API_KEY}

report_formatter:
  output_formats:
    - html
    - markdown
  branding:
    company_name: "Review Pulse"
    primary_color: "#2563eb"

quality_assurance:
  content_validation:
    min_themes: 3
    max_themes: 7
  readability:
    min_readability_score: 0.6
```

## Running the Application

### Development Mode

```bash
cd src
python main.py
```

The API will be available at `http://localhost:8003`

### Production Mode

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8003 --workers 4
```

## API Endpoints

### Health Check
```
GET /health
```

### Build Narrative
```
POST /api/v1/build-narrative
Content-Type: application/json

{
  "analysis_result": {...},
  "themes": [...]
}
```

### Format Report
```
POST /api/v1/format-report
Content-Type: application/json

{
  "narrative_result": {...},
  "output_format": "html"
}
```

### Validate Report
```
POST /api/v1/validate-report
Content-Type: application/json

{
  "narrative_result": {...},
  "formatted_report": {...}
}
```

### Full Report Pipeline
```
POST /api/v1/generate-full-report
Content-Type: application/json

{
  "analysis_result": {...},
  "themes": [...],
  "output_format": "html"
}
```

### Render Template
```
POST /api/v1/render-template?template_name=report_template.html
Content-Type: application/json

{
  "product_name": "TestApp",
  "executive_summary": "...",
  "themes": [...]
}
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

- Generate complete narratives with executive summary, themes, quotes, and action ideas
- Format reports in HTML and Markdown with one-page layout
- Quality assurance score > 0.7 for valid reports
- Processing time < 2 minutes per report

## Architecture

```
┌─────────────────┐
│  Analysis       │
│  Results        │
│  (from Phase 3) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Narrative       │
│ Builder         │
│ (Jinja2 + GPT4) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Report          │
│ Formatter       │
│ (HTML/MD)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Quality         │
│ Assurance       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final Report    │
└─────────────────┘
```

## Templates

Templates are stored in the `templates/` directory:
- `report_template.html` - HTML report template with CSS styling
- `report_template.md` - Markdown report template

Templates can be customized by editing these files or creating new templates.

## Mock Mode

If Jinja2 or OpenAI is not available, the system automatically falls back to mock mode:
- Mock narrative generation with predefined templates
- Basic formatting without template rendering
- Simple validation without LLM assistance

## Troubleshooting

### Jinja2 Not Available
If you see "Jinja2 not available" warnings:
```bash
pip install jinja2
```

### OpenAI API Errors
Check your API key in config.yaml:
```bash
export OPENAI_API_KEY=your_key_here
```

### Template Rendering Errors
Ensure template files exist in the `templates/` directory and are valid Jinja2 templates.

## Next Steps

- Phase 5: MCP Integration and Delivery
- Phase 6: Production Deployment
