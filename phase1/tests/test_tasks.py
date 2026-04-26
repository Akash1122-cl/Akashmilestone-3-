"""
Test cases for tasks.py - Celery background tasks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from celery.exceptions import Retry

from src.tasks import (
    celery_app, ingest_app_store_task, ingest_google_play_task,
    ingest_all_products_task, health_check_task
)
from src.database import Product, IngestionLog


class TestCeleryApp:
    """Test cases for Celery app configuration"""
    
    def test_celery_app_configuration(self):
        """Test Celery app is properly configured"""
        assert celery_app is not None
        assert celery_app.main == 'review_pulse'
        
        # Check broker configuration
        assert 'broker_url' in celery_app.conf
        assert 'result_backend' in celery_app.conf
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.timezone == 'UTC'
        assert celery_app.conf.enable_utc is True
    
    def test_beat_schedule_configuration(self):
        """Test Celery beat schedule configuration"""
        assert 'beat_schedule' in celery_app.conf
        
        beat_schedule = celery_app.conf.beat_schedule
        assert 'ingest-all-products-daily' in beat_schedule
        assert 'health-check-every-5-minutes' in beat_schedule
        
        # Check daily ingestion schedule
        daily_task = beat_schedule['ingest-all-products-daily']
        assert daily_task['task'] == 'tasks.ingest_all_products_task'
        assert hasattr(daily_task['schedule'], '__celery_expression__')  # crontab object
        
        # Check health check schedule
        health_task = beat_schedule['health-check-every-5-minutes']
        assert health_task['task'] == 'tasks.health_check_task'
        assert hasattr(health_task['schedule'], '__celery_expression__')  # crontab object


class TestIngestAppStoreTask:
    """Test cases for ingest_app_store_task"""
    
    @patch('src.tasks.AppStoreIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_app_store_task_success(self, mock_config, mock_db_manager, mock_app_store_ingestor):
        """Test successful App Store ingestion task"""
        # Setup mocks
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_log = Mock()
        mock_log.status = "success"
        mock_log.reviews_collected = 50
        mock_log.reviews_processed = 45
        mock_log.duration_seconds = 120
        mock_log.error_message = None
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.return_value = mock_log
        mock_app_store_ingestor.return_value = mock_ingestor
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        # Create task mock
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_app_store_task', task_mock):
            result = ingest_app_store_task(1)
        
        assert result["status"] == "success"
        assert result["product_id"] == 1
        assert result["product_name"] == "Groww"
        assert result["source"] == "app_store"
        assert result["reviews_collected"] == 50
        assert result["reviews_processed"] == 45
        assert result["duration_seconds"] == 120
        assert result["error"] is None
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_app_store_task_product_not_found(self, mock_config, mock_db_manager):
        """Test App Store ingestion task with non-existent product"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_app_store_task', task_mock):
            result = ingest_app_store_task(999)
        
        assert result["status"] == "error"
        assert result["message"] == "Product not found"
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_app_store_task_no_app_store_id(self, mock_config, mock_db_manager):
        """Test App Store ingestion task with product that has no App Store ID"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = None
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_app_store_task', task_mock):
            result = ingest_app_store_task(1)
        
        assert result["status"] == "error"
        assert result["message"] == "No App Store ID"
    
    @patch('src.tasks.AppStoreIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_app_store_task_ingestion_failure(self, mock_config, mock_db_manager, mock_app_store_ingestor):
        """Test App Store ingestion task with ingestion failure"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.side_effect = Exception("Ingestion failed")
        mock_app_store_ingestor.return_value = mock_ingestor
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        task_mock = Mock()
        task_mock.request.retries = 0
        task_mock.retry.side_effect = Retry("Task retry")
        
        with patch('src.tasks.ingest_app_store_task', task_mock):
            with pytest.raises(Retry):
                ingest_app_store_task(1)
        
        # Verify retry was called
        task_mock.retry.assert_called_once()
        assert mock_db.rollback.called
        assert mock_db.close.called
    
    @patch('src.tasks.AppStoreIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_app_store_task_retry_logic(self, mock_config, mock_db_manager, mock_app_store_ingestor):
        """Test App Store ingestion task retry logic"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.side_effect = Exception("Ingestion failed")
        mock_app_store_ingestor.return_value = mock_ingestor
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        # Test with existing retries
        task_mock = Mock()
        task_mock.request.retries = 2  # Already retried twice
        task_mock.retry.side_effect = Retry("Task retry")
        
        with patch('src.tasks.ingest_app_store_task', task_mock):
            with pytest.raises(Retry):
                ingest_app_store_task(1)
        
        # Verify retry was called with exponential backoff
        task_mock.retry.assert_called_once()
        # The countdown should be 60 * (retries + 1) = 60 * 3 = 180
        call_args = task_mock.retry.call_args
        assert call_args[1]['countdown'] == 180


class TestIngestGooglePlayTask:
    """Test cases for ingest_google_play_task"""
    
    @patch('src.tasks.GooglePlayIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_google_play_task_success(self, mock_config, mock_db_manager, mock_google_play_ingestor):
        """Test successful Google Play ingestion task"""
        # Setup mocks
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_log = Mock()
        mock_log.status = "success"
        mock_log.reviews_collected = 60
        mock_log.reviews_processed = 55
        mock_log.duration_seconds = 150
        mock_log.error_message = None
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.return_value = mock_log
        mock_google_play_ingestor.return_value = mock_ingestor
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        # Create task mock
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_google_play_task', task_mock):
            result = ingest_google_play_task(1)
        
        assert result["status"] == "success"
        assert result["product_id"] == 1
        assert result["product_name"] == "Groww"
        assert result["source"] == "google_play"
        assert result["reviews_collected"] == 60
        assert result["reviews_processed"] == 55
        assert result["duration_seconds"] == 150
        assert result["error"] is None
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_google_play_task_product_not_found(self, mock_config, mock_db_manager):
        """Test Google Play ingestion task with non-existent product"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_google_play_task', task_mock):
            result = ingest_google_play_task(999)
        
        assert result["status"] == "error"
        assert result["message"] == "Product not found"
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_google_play_task_no_play_store_url(self, mock_config, mock_db_manager):
        """Test Google Play ingestion task with product that has no Play Store URL"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        task_mock = Mock()
        task_mock.request.retries = 0
        
        with patch('src.tasks.ingest_google_play_task', task_mock):
            result = ingest_google_play_task(1)
        
        assert result["status"] == "error"
        assert result["message"] == "No Play Store URL"
    
    @patch('src.tasks.GooglePlayIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_google_play_task_ingestion_failure(self, mock_config, mock_db_manager, mock_google_play_ingestor):
        """Test Google Play ingestion task with ingestion failure"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_ingestor = Mock()
        mock_ingestor.ingest_product.side_effect = Exception("Ingestion failed")
        mock_google_play_ingestor.return_value = mock_ingestor
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        task_mock = Mock()
        task_mock.request.retries = 0
        task_mock.retry.side_effect = Retry("Task retry")
        
        with patch('src.tasks.ingest_google_play_task', task_mock):
            with pytest.raises(Retry):
                ingest_google_play_task(1)
        
        # Verify retry was called
        task_mock.retry.assert_called_once()
        assert mock_db.rollback.called
        assert mock_db.close.called


class TestIngestAllProductsTask:
    """Test cases for ingest_all_products_task"""
    
    @patch('src.tasks.ingest_google_play_task')
    @patch('src.tasks.ingest_app_store_task')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_all_products_task_success(self, mock_config, mock_db_manager, mock_app_store_task, mock_google_play_task):
        """Test successful ingestion of all products"""
        # Setup mocks
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
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
        
        mock_db.query.return_value.all.return_value = [mock_product1, mock_product2]
        
        # Mock task results
        mock_app_store_result = Mock()
        mock_app_store_result.id = "app_store_task_123"
        mock_app_store_task.delay.return_value = mock_app_store_result
        
        mock_google_play_result = Mock()
        mock_google_play_result.id = "google_play_task_456"
        mock_google_play_task.delay.return_value = mock_google_play_result
        
        result = ingest_all_products_task()
        
        assert result["status"] == "triggered"
        assert len(result["tasks"]) == 3  # 2 sources for product1 + 1 source for product2
        
        # Verify tasks were triggered
        assert mock_app_store_task.delay.call_count == 1
        assert mock_google_play_task.delay.call_count == 2
        
        # Check task IDs
        tasks = result["tasks"]
        task_ids = [task["task_id"] for task in tasks]
        assert "app_store_task_123" in task_ids
        assert "google_play_task_456" in task_ids
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_all_products_task_no_products(self, mock_config, mock_db_manager):
        """Test ingestion of all products when no products exist"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        mock_db.query.return_value.all.return_value = []
        
        result = ingest_all_products_task()
        
        assert result["status"] == "triggered"
        assert len(result["tasks"]) == 0
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_all_products_task_database_error(self, mock_config, mock_db_manager):
        """Test ingestion of all products with database error"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")
        
        result = ingest_all_products_task()
        
        assert result["status"] == "error"
        assert "Database error" in result["message"]
        assert mock_db.close.called
    
    @patch('src.tasks.ingest_app_store_task')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_ingest_all_products_task_partial_sources(self, mock_config, mock_db_manager, mock_app_store_task):
        """Test ingestion of products with only some sources configured"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        # Product with only App Store
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "App Store Only"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = None
        
        mock_db.query.return_value.all.return_value = [mock_product]
        
        mock_task_result = Mock()
        mock_task_result.id = "app_store_task_123"
        mock_app_store_task.delay.return_value = mock_task_result
        
        result = ingest_all_products_task()
        
        assert result["status"] == "triggered"
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["source"] == "app_store"
        assert result["tasks"][0]["task_id"] == "app_store_task_123"
        
        # Only App Store task should be called
        mock_app_store_task.delay.assert_called_once_with(1)


class TestHealthCheckTask:
    """Test cases for health_check_task"""
    
    @patch('src.tasks.init_redis_cache')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_health_check_task_success(self, mock_config, mock_db_manager, mock_redis_cache_init):
        """Test successful health check"""
        # Setup mocks
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_redis_cache = Mock()
        mock_redis_cache.client.ping.return_value = True
        mock_redis_cache_init.return_value = mock_redis_cache
        
        result = health_check_task()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        
        # Verify checks were performed
        mock_redis_cache.client.ping.assert_called_once()
        mock_db.execute.assert_called_once_with("SELECT 1")
        mock_db.close.assert_called_once()
    
    @patch('src.tasks.init_redis_cache')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_health_check_task_redis_failure(self, mock_config, mock_db_manager, mock_redis_cache_init):
        """Test health check with Redis failure"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_redis_cache = Mock()
        mock_redis_cache.client.ping.side_effect = Exception("Redis connection failed")
        mock_redis_cache_init.return_value = mock_redis_cache
        
        result = health_check_task()
        
        assert result["status"] == "unhealthy"
        assert "Redis connection failed" in result["error"]
    
    @patch('src.tasks.init_redis_cache')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_health_check_task_database_failure(self, mock_config, mock_db_manager, mock_redis_cache_init):
        """Test health check with database failure"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        mock_redis_cache = Mock()
        mock_redis_cache.client.ping.return_value = True
        mock_redis_cache_init.return_value = mock_redis_cache
        
        result = health_check_task()
        
        assert result["status"] == "unhealthy"
        assert "Database connection failed" in result["error"]
    
    @patch('src.tasks.init_redis_cache')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_health_check_task_redis_init_failure(self, mock_config, mock_db_manager, mock_redis_cache_init):
        """Test health check with Redis initialization failure"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_redis_cache_init.side_effect = Exception("Redis initialization failed")
        
        result = health_check_task()
        
        assert result["status"] == "unhealthy"
        assert "Redis initialization failed" in result["error"]


class TestTasksIntegration:
    """Integration tests for Celery tasks"""
    
    @patch('src.tasks.AppStoreIngestor')
    @patch('src.tasks.GooglePlayIngestor')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_task_workflow_integration(self, mock_config, mock_db_manager, mock_google_play_ingestor, mock_app_store_ingestor):
        """Test integration between different tasks"""
        # Setup mocks for ingest_all_products_task
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        mock_product.play_store_url = "https://play.google.com/store/apps/details?id=com.example.groww"
        
        mock_db.query.return_value.all.return_value = [mock_product]
        
        # Mock task results
        mock_app_store_result = Mock()
        mock_app_store_result.id = "app_store_task_123"
        mock_google_play_result = Mock()
        mock_google_play_result.id = "google_play_task_456"
        
        with patch('src.tasks.ingest_app_store_task') as mock_app_store_task:
            with patch('src.tasks.ingest_google_play_task') as mock_google_play_task:
                mock_app_store_task.delay.return_value = mock_app_store_result
                mock_google_play_task.delay.return_value = mock_google_play_result
                
                # Run ingest all products task
                result = ingest_all_products_task()
                
                assert result["status"] == "triggered"
                assert len(result["tasks"]) == 2
                
                # Verify both tasks were triggered
                mock_app_store_task.delay.assert_called_once_with(1)
                mock_google_play_task.delay.assert_called_once_with(1)
    
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_task_database_session_lifecycle(self, mock_config, mock_db_manager):
        """Test proper database session lifecycle in tasks"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Groww"
        mock_product.app_store_id = "123456789"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_product
        
        task_mock = Mock()
        task_mock.request.retries = 0
        
        # Test that database session is properly closed even on error
        with patch('src.tasks.AppStoreIngestor') as mock_ingestor:
            mock_ingestor.return_value.ingest_product.side_effect = Exception("Test error")
            
            with patch('src.tasks.ingest_app_store_task', task_mock):
                try:
                    ingest_app_store_task(1)
                except Retry:
                    pass  # Expected to retry
        
        # Verify database session was closed
        assert mock_db.close.called
    
    @patch('src.tasks.init_redis_cache')
    @patch('src.tasks.init_database')
    @patch('src.tasks.init_config')
    def test_health_check_task_session_cleanup(self, mock_config, mock_db_manager, mock_redis_cache_init):
        """Test health check properly cleans up database session"""
        mock_db = Mock()
        mock_db_manager.get_session.return_value = mock_db
        
        mock_redis_cache = Mock()
        mock_redis_cache.client.ping.return_value = True
        mock_redis_cache_init.return_value = mock_redis_cache
        
        result = health_check_task()
        
        assert result["status"] == "healthy"
        assert mock_db.close.called
