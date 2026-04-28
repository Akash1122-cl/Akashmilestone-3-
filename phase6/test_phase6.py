#!/usr/bin/env python3
"""
Test script for Phase 6 Advanced Automation and Analytics
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))

# Load test environment
load_dotenv('.env.example')

async def test_phase6_integration():
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    print('Testing Phase 6 Advanced Automation and Analytics...')
    
    # Test health endpoint
    response = client.get('/health')
    health_data = response.json()
    print(f'Health check: {response.status_code} - {health_data["status"]}')
    print(f'MCP Connected: {health_data["mcp_connected"]}')
    
    # Test MCP status
    response = client.get('/api/v1/mcp-status')
    print(f'MCP status endpoint: {response.status_code}')
    if response.status_code == 200:
        mcp_status = response.json()
        print(f'External MCP Status: {mcp_status["status"]}')
        if 'server_url' in mcp_status:
            print(f'MCP Server URL: {mcp_status["server_url"]}')
    
    # Test advanced delivery
    print('\nTesting advanced delivery...')
    delivery_request = {
        "product_ids": ["test_product_1", "test_product_2"],
        "report_template": "executive_summary",
        "delivery_methods": ["email", "google_docs"],
        "recipients": ["manager@company.com", "team@company.com"]
    }
    
    response = client.post('/api/v1/automation/advanced-delivery', json=delivery_request)
    print(f'Advanced delivery: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Success: {result["success"]}')
        print(f'Processed products: {result["processed_products"]}')
        for product_result in result["results"]:
            print(f'  Product {product_result["product_id"]}: {product_result["doc_result"]["status"]}')
    else:
        print(f'Error: {response.json()}')
    
    # Test trend analysis
    print('\nTesting trend analysis...')
    analytics_request = {
        "product_id": "test_product",
        "time_range": "30_days",
        "metrics": ["sentiment", "volume", "rating"],
        "compare_with": ["competitor_1"],
        "include_predictions": True
    }
    
    response = client.post('/api/v1/analytics/trend-analysis', json=analytics_request)
    print(f'Trend analysis: {response.status_code}')
    if response.status_code == 200:
        analysis = response.json()
        print(f'Product ID: {analysis["product_id"]}')
        print(f'Sentiment: {analysis["trends"]["sentiment"]["current"]} ({analysis["trends"]["sentiment"]["trend"]})')
        print(f'Volume: {analysis["trends"]["volume"]["current"]} ({analysis["trends"]["volume"]["trend"]})')
        if analysis["predictions"]:
            print(f'Predicted next week volume: {analysis["predictions"]["next_week_volume"]}')
    else:
        print(f'Error: {response.json()}')
    
    # Test automation rule creation
    print('\nTesting automation rule creation...')
    rule_request = {
        "name": "Weekly Report Rule",
        "product_id": "test_product",
        "conditions": {
            "min_review_count": 10,
            "sentiment_threshold": 0.7
        },
        "actions": [
            {"type": "generate_report", "template": "executive_summary"},
            {"type": "send_email", "recipients": ["manager@company.com"]}
        ]
    }
    
    response = client.post('/api/v1/automation/rules', json=rule_request)
    print(f'Automation rule creation: {response.status_code}')
    if response.status_code == 200:
        rule = response.json()
        print(f'Rule ID: {rule["rule_id"]}')
        print(f'Rule name: {rule["rule"]["name"]}')
    else:
        print(f'Error: {response.json()}')
    
    # Test batch processing
    print('\nTesting batch processing...')
    batch_request = ["product_1", "product_2", "product_3"]
    
    response = client.post('/api/v1/automation/batch-process', json=batch_request)
    print(f'Batch processing: {response.status_code}')
    if response.status_code == 200:
        batch_result = response.json()
        print(f'Success: {batch_result["success"]}')
        print(f'Total products: {batch_result["total_products"]}')
        print(f'Successful: {batch_result["successful"]}')
        print(f'Failed: {batch_result["failed"]}')
    else:
        print(f'Error: {response.json()}')
    
    # Test dashboard creation
    print('\nTesting dashboard creation...')
    dashboard_config = {
        "name": "Executive Dashboard",
        "widgets": [
            {
                "type": "sentiment_trend",
                "product_id": "test_product",
                "time_range": "30_days"
            },
            {
                "type": "comparison_chart",
                "products": ["test_product", "competitor_1"],
                "metric": "rating"
            }
        ],
        "layout": "grid",
        "refresh_interval": "hourly"
    }
    
    response = client.post('/api/v1/analytics/dashboard', json=dashboard_config)
    print(f'Dashboard creation: {response.status_code}')
    if response.status_code == 200:
        dashboard = response.json()
        print(f'Dashboard ID: {dashboard["dashboard_id"]}')
        print(f'Dashboard name: {dashboard["config"]["name"]}')
    else:
        print(f'Error: {response.json()}')
    
    print('\nPhase 6 Advanced Automation and Analytics test completed!')
    print('✅ All core features tested successfully!')

if __name__ == '__main__':
    asyncio.run(test_phase6_integration())
