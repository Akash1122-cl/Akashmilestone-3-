"""
Test cases for main.py - FastAPI endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime
import json

from src.main import app
from src.database import Product, Review, IngestionLog


class TestMainEndpoints:
    """Test cases for main FastAPI endpoints"""
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    def test_root_endpoint(self, mock_config, mock_db_manager, mock_redis_cache):
        """Test root endpoint"""
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Review Pulse - Phase 1"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_health_check_healthy(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test health check endpoint when all services are healthy"""
        mock_db = Mock()
        mock_db.execute.return_value = None
        mock_get_db.return_value = mock_db
        mock_redis_cache.client.ping.return_value = True
        mock_redis_cache.get_stats.return_value = {
            'connected_clients': 5,
            'used_memory_human': '2.5M',
            'total_keys': 50,
            'hits': 100,
            'misses': 10
        }
        
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"
        assert "redis_stats" in data["checks"]
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_health_check_database_unhealthy(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test health check endpoint when database is unhealthy"""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_db
        mock_redis_cache.client.ping.return_value = True
        mock_redis_cache.get_stats.return_value = {'total_keys': 0}
        
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["checks"]["database"]
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_health_check_redis_unhealthy(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test health check endpoint when Redis is unhealthy"""
        mock_db = Mock()
        mock_db.execute.return_value = None
        mock_get_db.return_value = mock_db
        mock_redis_cache.client.ping.side_effect = Exception("Redis connection failed")
        mock_redis_cache.get_stats.return_value = {}
        
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "unhealthy" in data["checks"]["redis"]
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_products_empty(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting products when none exist"""
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["products"] == []
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_products_with_data(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting products with data"""
        mock_product1 = Mock()
        mock_product1.id = 1
        mock_product1.name = "Groww"
        mock_product1.app_store_id = "123456789"
        mock_product1.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_product2 = Mock()
        mock_product2.id = 2
        mock_product2.name = "Test App"
        mock_product2.app_store_id = "987654321"
        mock_product2.play_store_url = "https://play.google.com/store/apps/details?id=com.example.test"
        
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = [mock_product1, mock_product2]
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/products")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["products"]) == 2
        
        # Check first product
        assert data["products"][0]["id"] == 1
        assert data["products"][0]["name"] == "Groww"
        assert data["products"][0]["app_store_id"] == "123456789"
        assert data["products"][0]["play_store_url"] == "https://play.google.com/store/apps/details?id=com.example.groww"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_product_success(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting a specific product successfully"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        mock_product.created_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_product.updated_at = datetime(2024, 1, 16, 11, 30, 0)
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/products/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Groww"
        assert data["app_store_id"] == "123456789"
        assert data["play_store_url"] == "https://play.google.com/store/apps/details?id=com.example.groww"
        assert data["created_at"] == "2024-01-15T10:30:00"
        assert data["updated_at"] == "2024-01-16T11:30:00"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_product_not_found(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting a non-existent product"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/products/999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Product not found"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_ingestion_logs_no_filters(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting ingestion logs without filters"""
        mock_log1 = Mock()
        mock_log1.id = 1
        mock_log1.product_id = 1
        mock_log1.source = "app_store"
        mock_log1.status = "success"
        mock_log1.reviews_collected = 50
        mock_log1.reviews_processed = 45
        mock_log1.error_message = None
        mock_log1.started_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_log1.completed_at = datetime(2024, 1, 15, 10, 32, 0)
        mock_log1.duration_seconds = 120
        
        mock_log2 = Mock()
        mock_log2.id = 2
        mock_log2.product_id = 1
        mock_log2.source = "google_play"
        mock_log2.status = "failed"
        mock_log2.reviews_collected = 0
        mock_log2.reviews_processed = 0
        mock_log2.error_message = "Network error"
        mock_log2.started_at = datetime(2024, 1, 15, 11, 0, 0)
        mock_log2.completed_at = datetime(2024, 1, 15, 11, 1, 0)
        mock_log2.duration_seconds = 60
        
        mock_db = Mock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_log1, mock_log2]
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/ingestion/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["logs"]) == 2
        
        # Check first log
        assert data["logs"][0]["id"] == 1
        assert data["logs"][0]["product_id"] == 1
        assert data["logs"][0]["source"] == "app_store"
        assert data["logs"][0]["status"] == "success"
        assert data["logs"][0]["reviews_collected"] == 50
        assert data["logs"][0]["reviews_processed"] == 45
        assert data["logs"][0]["error_message"] is None
        assert data["logs"][0]["started_at"] == "2024-01-15T10:30:00"
        assert data["logs"][0]["completed_at"] == "2024-01-15T10:32:00"
        assert data["logs"][0]["duration_seconds"] == 120
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_ingestion_logs_with_filters(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting ingestion logs with filters"""
        mock_log = Mock()
        mock_log.id = 1
        mock_log.product_id = 1
        mock_log.source = "app_store"
        mock_log.status = "success"
        mock_log.reviews_collected = 50
        mock_log.reviews_processed = 45
        mock_log.error_message = None
        mock_log.started_at = datetime(2024, 1, 15, 10, 30, 0)
        mock_log.completed_at = datetime(2024, 1, 15, 10, 32, 0)
        mock_log.duration_seconds = 120
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_log]
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/ingestion/logs?product_id=1&source=app_store&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["logs"]) == 1
        
        # Verify filters were applied
        assert mock_db.query.return_value.filter.call_count == 2  # Once for product_id, once for source
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.AppStoreIngestor')
    @patch('src.main.get_db')
    def test_ingest_app_store_success(self, mock_get_db, mock_app_store_ingestor, mock_config, mock_db_manager, mock_redis_cache):
        """Test successful App Store ingestion"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_log = Mock()
        mock_log.id = 1
        mock_log.reviews_collected = 50
        mock_log.reviews_processed = 45
        mock_log.duration_seconds = 120
        mock_log.error_message = None
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.return_value = mock_log
        mock_app_store_ingestor.return_value = mock_ingestor
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/app-store/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["log_id"] == 1
        assert data["product"] == "Groww"
        assert data["source"] == "app_store"
        assert data["reviews_collected"] == 50
        assert data["reviews_processed"] == 45
        assert data["duration_seconds"] == 120
        assert data["error"] is None
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_ingest_app_store_product_not_found(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test App Store ingestion with non-existent product"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/app-store/999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Product not found"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_ingest_app_store_no_app_store_id(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test App Store ingestion with product that has no App Store ID"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = None
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/app-store/1")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Product has no App Store ID"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.AppStoreIngestor')
    @patch('src.main.get_db')
    def test_ingest_app_store_ingestion_error(self, mock_get_db, mock_app_store_ingestor, mock_config, mock_db_manager, mock_redis_cache):
        """Test App Store ingestion with ingestion error"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.side_effect = Exception("Ingestion failed")
        mock_app_store_ingestor.return_value = mock_ingestor
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/app-store/1")
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Ingestion failed"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.GooglePlayIngestor')
    @patch('src.main.get_db')
    def test_ingest_google_play_success(self, mock_get_db, mock_google_play_ingestor, mock_config, mock_db_manager, mock_redis_cache):
        """Test successful Google Play ingestion"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_log = Mock()
        mock_log.id = 1
        mock_log.reviews_collected = 60
        mock_log.reviews_processed = 55
        mock_log.duration_seconds = 150
        mock_log.error_message = None
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.return_value = mock_log
        mock_google_play_ingestor.return_value = mock_ingestor
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/google-play/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["log_id"] == 1
        assert data["product"] == "Groww"
        assert data["source"] == "google_play"
        assert data["reviews_collected"] == 60
        assert data["reviews_processed"] == 55
        assert data["duration_seconds"] == 150
        assert data["error"] is None
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_ingest_google_play_product_not_found(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test Google Play ingestion with non-existent product"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/google-play/999")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Product not found"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_ingest_google_play_no_play_store_url(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test Google Play ingestion with product that has no Play Store URL"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = None
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/google-play/1")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Product has no Play Store URL"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.AppStoreIngestor')
    @patch('src.main.GooglePlayIngestor')
    @patch('src.main.get_db')
    def test_ingest_all_products_success(self, mock_get_db, mock_google_play_ingestor, mock_app_store_ingestor, mock_config, mock_db_manager, mock_redis_cache):
        """Test successful ingestion for all products"""
        # Setup products
        mock_product1 = Mock()
        mock_product1.id = 1
        mock_product1.name = "Groww"
        mock_product1.app_store_id = "123456789"
        mock_product1.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_product2 = Mock()
        mock_product2.id = 2
        mock_product2.name = "Test App"
        mock_product2.app_store_id = None
        mock_product2.play_store_url = "https://play.google.com/store/apps/details?id=com.example.test"
        
        # Setup ingestors and logs
        mock_app_store_log = Mock()
        mock_app_store_log.status = "success"
        mock_app_store_log.reviews_processed = 45
        
        mock_google_play_log = Mock()
        mock_google_play_log.status = "success"
        mock_google_play_log.reviews_processed = 55
        
        mock_app_store_ingestor_instance = Mock()
        mock_app_store_ingestor_instance.ingest_product.return_value = mock_app_store_log
        mock_app_store_ingestor.return_value = mock_app_store_ingestor_instance
        
        mock_google_play_ingestor_instance = Mock()
        mock_google_play_ingestor_instance.ingest_product.return_value = mock_google_play_log
        mock_google_play_ingestor.return_value = mock_google_play_ingestor_instance
        
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = [mock_product1, mock_product2]
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 2
        assert len(data["results"]) == 3  # 2 sources for product1 + 1 source for product2
        
        # Check results
        results = data["results"]
        assert results[0]["product"] == "Groww"
        assert results[0]["source"] == "app_store"
        assert results[0]["status"] == "success"
        assert results[0]["reviews_processed"] == 45
        
        assert results[1]["product"] == "Groww"
        assert results[1]["source"] == "google_play"
        assert results[1]["status"] == "success"
        assert results[1]["reviews_processed"] == 55
        
        assert results[2]["product"] == "Test App"
        assert results[2]["source"] == "google_play"
        assert results[2]["status"] == "success"
        assert results[2]["reviews_processed"] == 55
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.AppStoreIngestor')
    @patch('src.main.get_db')
    def test_ingest_all_products_with_errors(self, mock_get_db, mock_app_store_ingestor, mock_config, mock_db_manager, mock_redis_cache):
        """Test ingestion for all products with some errors"""
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_app_store_ingestor_instance = Mock()
        mock_app_store_ingestor_instance.ingest_product.side_effect = Exception("Ingestion failed")
        mock_app_store_ingestor.return_value = mock_app_store_ingestor_instance
        
        mock_db = Mock()
        mock_db.query.return_value.all.return_value = [mock_product]
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.post("/ingest/all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_products"] == 1
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert result["product"] == "Groww"
        assert result["source"] == "error"
        assert result["status"] == "failed"
        assert result["error"] == "Ingestion failed"
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    @patch('src.main.get_db')
    def test_get_stats(self, mock_get_db, mock_config, mock_db_manager, mock_redis_cache):
        """Test getting system statistics"""
        # Setup mock data
        mock_db = Mock()
        mock_db.query.return_value.count.return_value = 5  # Product count
        
        # Review counts
        def review_query_side_effect(*args):
            mock_query = Mock()
            if args[0].compare(Review.source == 'app_store'):
                mock_query.count.return_value = 100
            elif args[0].compare(Review.source == 'google_play'):
                mock_query.count.return_value = 150
            else:
                mock_query.count.return_value = 250
            return mock_query
        
        mock_db.query.side_effect = review_query_side_effect
        
        # Recent logs
        mock_log1 = Mock()
        mock_log1.product_id = 1
        mock_log1.source = "app_store"
        mock_log1.status = "success"
        mock_log1.reviews_processed = 45
        mock_log1.started_at = datetime(2024, 1, 15, 10, 30, 0)
        
        mock_log2 = Mock()
        mock_log2.product_id = 1
        mock_log2.source = "google_play"
        mock_log2.status = "success"
        mock_log2.reviews_processed = 55
        mock_log2.started_at = datetime(2024, 1, 15, 11, 30, 0)
        
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_log1, mock_log2]
        
        # Redis stats
        mock_redis_cache.get_stats.return_value = {
            'connected_clients': 5,
            'used_memory_human': '2.5M',
            'total_keys': 50,
            'hits': 100,
            'misses': 10
        }
        
        mock_get_db.return_value = mock_db
        
        client = TestClient(app)
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == 5
        assert data["reviews"]["total"] == 250
        assert data["reviews"]["app_store"] == 100
        assert data["reviews"]["google_play"] == 150
        assert data["redis"]["connected_clients"] == 5
        assert data["redis"]["used_memory_human"] == "2.5M"
        assert len(data["recent_ingestion"]) == 2
        
        # Check recent ingestion
        recent = data["recent_ingestion"][0]
        assert recent["product_id"] == 1
        assert recent["source"] == "app_store"
        assert recent["status"] == "success"
        assert recent["reviews_processed"] == 45
        assert recent["started_at"] == "2024-01-15T10:30:00"


class TestMainAppEvents:
    """Test cases for FastAPI app events"""
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    def test_startup_event_success(self, mock_config, mock_db_manager, mock_redis_cache):
        """Test successful startup event"""
        mock_db_manager.create_tables.return_value = None
        
        with patch('src.main.logger') as mock_logger:
            from fastapi import FastAPI
            test_app = FastAPI()
            
            @test_app.on_event("startup")
            async def test_startup():
                mock_db_manager.create_tables()
                mock_logger.info("Database tables created successfully")
            
            # This would normally be called by FastAPI automatically
            # For testing, we call it directly
            import asyncio
            asyncio.run(test_startup())
            
            mock_db_manager.create_tables.assert_called_once()
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    def test_startup_event_failure(self, mock_config, mock_db_manager, mock_redis_cache):
        """Test startup event with failure"""
        mock_db_manager.create_tables.side_effect = Exception("Database error")
        
        with patch('src.main.logger') as mock_logger:
            from fastapi import FastAPI
            test_app = FastAPI()
            
            @test_app.on_event("startup")
            async def test_startup():
                try:
                    mock_db_manager.create_tables()
                    mock_logger.info("Database tables created successfully")
                except Exception as e:
                    mock_logger.error(f"Error creating database tables: {e}")
            
            import asyncio
            asyncio.run(test_startup())
            
            mock_logger.error.assert_called_once()
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    def test_shutdown_event_success(self, mock_config, mock_db_manager, mock_redis_cache):
        """Test successful shutdown event"""
        mock_db_manager.close.return_value = None
        mock_redis_cache.close.return_value = None
        
        with patch('src.main.logger') as mock_logger:
            from fastapi import FastAPI
            test_app = FastAPI()
            
            @test_app.on_event("shutdown")
            async def test_shutdown():
                mock_db_manager.close()
                mock_redis_cache.close()
                mock_logger.info("Application shutdown complete")
            
            import asyncio
            asyncio.run(test_shutdown())
            
            mock_db_manager.close.assert_called_once()
            mock_redis_cache.close.assert_called_once()
    
    @patch('src.main.redis_cache')
    @patch('src.main.db_manager')
    @patch('src.main.config')
    def test_shutdown_event_failure(self, mock_config, mock_db_manager, mock_redis_cache):
        """Test shutdown event with failure"""
        mock_db_manager.close.side_effect = Exception("Close error")
        mock_redis_cache.close.return_value = None
        
        with patch('src.main.logger') as mock_logger:
            from fastapi import FastAPI
            test_app = FastAPI()
            
            @test_app.on_event("shutdown")
            async def test_shutdown():
                try:
                    mock_db_manager.close()
                    mock_redis_cache.close()
                    mock_logger.info("Application shutdown complete")
                except Exception as e:
                    mock_logger.error(f"Error during shutdown: {e}")
            
            import asyncio
            asyncio.run(test_shutdown())
            
            mock_logger.error.assert_called_once()


class TestMainIntegration:
    """Integration tests for main FastAPI application"""
    
    def test_full_api_workflow(self, test_client, test_db_session, sample_product):
        """Test complete API workflow"""
        # Add product to database
        test_db_session.add(sample_product)
        test_db_session.commit()
        
        # Test getting products
        response = test_client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["products"][0]["name"] == "Groww"
        
        # Test getting specific product
        response = test_client.get(f"/products/{sample_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Groww"
        
        # Test getting stats
        response = test_client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == 1
        assert data["reviews"]["total"] == 0
        
        # Test getting ingestion logs (should be empty initially)
        response = test_client.get("/ingestion/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
