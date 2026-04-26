"""
Test cases for config_manager.py - Configuration management
"""

import pytest
from unittest.mock import patch, mock_open
import yaml
import os

from src.config_manager import ConfigManager, init_config, config_manager


class TestConfigManager:
    """Test cases for ConfigManager class"""
    
    def test_config_manager_initialization(self, config_manager):
        """Test ConfigManager initialization"""
        assert config_manager.config_path is not None
        assert config_manager.config is not None
        assert 'database' in config_manager.config
        assert 'redis' in config_manager.config
        assert 'app_store' in config_manager.config
        assert 'google_play' in config_manager.config
        assert 'products' in config_manager.config
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('yaml.safe_load')
    def test_load_config_success(self, mock_yaml_load, mock_exists, mock_file):
        """Test successful configuration loading"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'database': {'host': 'localhost'},
            'redis': {'port': 6379}
        }
        
        manager = ConfigManager('test_config.yaml')
        
        assert manager.config == {
            'database': {'host': 'localhost'},
            'redis': {'port': 6379}
        }
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
        mock_yaml_load.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_load_config_file_not_found(self, mock_exists):
        """Test configuration loading with missing file"""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ConfigManager('nonexistent_config.yaml')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('yaml.safe_load')
    def test_load_config_yaml_error(self, mock_yaml_load, mock_exists, mock_file):
        """Test configuration loading with YAML error"""
        mock_exists.return_value = True
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
        
        with pytest.raises(yaml.YAMLError):
            ConfigManager('invalid_config.yaml')
    
    def test_replace_env_vars_string(self, config_manager):
        """Test replacing environment variables in strings"""
        os.environ['TEST_VAR'] = 'test_value'
        
        result = config_manager._replace_env_vars('${TEST_VAR}')
        assert result == 'test_value'
        
        # Clean up
        del os.environ['TEST_VAR']
    
    def test_replace_env_vars_string_default(self, config_manager):
        """Test environment variable replacement with non-existent variable"""
        result = config_manager._replace_env_vars('${NONEXISTENT_VAR}')
        assert result == '${NONEXISTENT_VAR}'
    
    def test_replace_env_vars_dict(self, config_manager):
        """Test replacing environment variables in dictionary"""
        os.environ['TEST_VAR'] = 'test_value'
        
        config = {
            'database': {
                'host': '${TEST_VAR}',
                'port': 5432
            },
            'redis': {
                'host': 'localhost'
            }
        }
        
        result = config_manager._replace_env_vars(config)
        
        expected = {
            'database': {
                'host': 'test_value',
                'port': 5432
            },
            'redis': {
                'host': 'localhost'
            }
        }
        assert result == expected
        
        # Clean up
        del os.environ['TEST_VAR']
    
    def test_replace_env_vars_list(self, config_manager):
        """Test replacing environment variables in list"""
        os.environ['TEST_VAR'] = 'test_value'
        
        config = [
            '${TEST_VAR}',
            'normal_string',
            {'nested': '${TEST_VAR}'}
        ]
        
        result = config_manager._replace_env_vars(config)
        
        expected = [
            'test_value',
            'normal_string',
            {'nested': 'test_value'}
        ]
        assert result == expected
        
        # Clean up
        del os.environ['TEST_VAR']
    
    def test_replace_env_vars_other_types(self, config_manager):
        """Test replacing environment variables with non-string types"""
        result = config_manager._replace_env_vars(123)
        assert result == 123
        
        result = config_manager._replace_env_vars(True)
        assert result is True
        
        result = config_manager._replace_env_vars(None)
        assert result is None
    
    def test_validate_config_success(self, config_manager):
        """Test successful configuration validation"""
        # Should not raise an exception
        config_manager._validate_config()
    
    def test_validate_config_missing_section(self, config_manager):
        """Test configuration validation with missing section"""
        config_manager.config = {
            'database': {'host': 'localhost'},
            'redis': {'port': 6379}
            # Missing required sections
        }
        
        with pytest.raises(ValueError, match="Missing required configuration section"):
            config_manager._validate_config()
    
    def test_get_existing_key(self, config_manager):
        """Test getting an existing configuration key"""
        result = config_manager.get('database.host')
        assert result == 'localhost'
        
        result = config_manager.get('redis.port')
        assert result == 6379
    
    def test_get_nonexistent_key(self, config_manager):
        """Test getting a non-existent configuration key"""
        result = config_manager.get('nonexistent.key')
        assert result is None
        
        result = config.get('nonexistent.key', 'default_value')
        assert result == 'default_value'
    
    def test_get_nonexistent_key_with_default(self, config_manager):
        """Test getting a non-existent key with default value"""
        result = config_manager.get('nonexistent.key', 'default_value')
        assert result == 'default_value'
    
    def test_get_nested_key(self, config_manager):
        """Test getting nested configuration key"""
        result = config_manager.get('products.0.name')
        assert result == 'Groww'
    
    def test_get_database_config(self, config_manager):
        """Test getting database configuration"""
        db_config = config_manager.get_database_config()
        assert 'host' in db_config
        assert 'port' in db_config
        assert 'name' in db_config
        assert 'user' in db_config
        assert 'password' in db_config
    
    def test_get_redis_config(self, config_manager):
        """Test getting Redis configuration"""
        redis_config = config_manager.get_redis_config()
        assert 'host' in redis_config
        assert 'port' in redis_config
        assert 'db' in redis_config
        assert 'max_connections' in redis_config
    
    def test_get_app_store_config(self, config_manager):
        """Test getting App Store configuration"""
        app_store_config = config_manager.get_app_store_config()
        assert 'rss_feed_url' in app_store_config
        assert 'request_timeout' in app_store_config
        assert 'retry_attempts' in app_store_config
    
    def test_get_google_play_config(self, config_manager):
        """Test getting Google Play configuration"""
        google_play_config = config_manager.get_google_play_config()
        assert 'base_url' in google_play_config
        assert 'request_timeout' in google_play_config
        assert 'retry_attempts' in google_play_config
    
    def test_get_products(self, config_manager):
        """Test getting products configuration"""
        products = config_manager.get_products()
        assert isinstance(products, list)
        assert len(products) > 0
        assert 'name' in products[0]
        assert 'app_store_id' in products[0]
        assert 'play_store_url' in products[0]
    
    def test_get_ingestion_config(self, config_manager):
        """Test getting ingestion configuration"""
        ingestion_config = config_manager.get_ingestion_config()
        assert 'schedule' in ingestion_config
        assert 'batch_size' in ingestion_config
        assert 'max_reviews_per_run' in ingestion_config
    
    def test_get_logging_config(self, config_manager):
        """Test getting logging configuration"""
        logging_config = config_manager.get_logging_config()
        assert 'level' in logging_config
        assert 'format' in logging_config
    
    def test_get_api_config(self, config_manager):
        """Test getting API configuration"""
        api_config = config_manager.get_api_config()
        assert 'host' in api_config
        assert 'port' in api_config
        assert 'debug' in api_config
    
    def test_get_enabled_products(self, config_manager):
        """Test getting only enabled products"""
        enabled_products = config_manager.get_enabled_products()
        assert isinstance(enabled_products, list)
        
        for product in enabled_products:
            assert product.get('enabled', True) is True
    
    def test_get_enabled_products_with_disabled(self, config_manager):
        """Test getting enabled products when some are disabled"""
        config_manager.config['products'] = [
            {'name': 'Product 1', 'enabled': True},
            {'name': 'Product 2', 'enabled': False},
            {'name': 'Product 3', 'enabled': True}
        ]
        
        enabled_products = config_manager.get_enabled_products()
        assert len(enabled_products) == 2
        assert enabled_products[0]['name'] == 'Product 1'
        assert enabled_products[1]['name'] == 'Product 3'
    
    def test_get_enabled_products_no_enabled_field(self, config_manager):
        """Test getting enabled products when enabled field is missing"""
        config_manager.config['products'] = [
            {'name': 'Product 1'},
            {'name': 'Product 2'}
        ]
        
        enabled_products = config_manager.get_enabled_products()
        assert len(enabled_products) == 2  # All should be enabled by default
    
    @patch('src.config_manager.ConfigManager._load_config')
    @patch('src.config_manager.ConfigManager._validate_config')
    def test_reload(self, mock_validate, mock_load, config_manager):
        """Test reloading configuration"""
        new_config = {'database': {'host': 'new_host'}}
        mock_load.return_value = new_config
        
        config_manager.reload()
        
        assert config_manager.config == new_config
        mock_load.assert_called_once()
        mock_validate.assert_called_once()


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager"""
    
    def test_full_config_workflow(self, temp_dir):
        """Test complete configuration workflow"""
        # Create a test configuration file
        config_data = {
            'database': {
                'host': '${DB_HOST}',
                'port': 5432,
                'name': 'test_db',
                'user': 'test_user',
                'password': 'test_pass'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 1
            },
            'app_store': {
                'rss_feed_url': 'https://itunes.apple.com/rss',
                'request_timeout': 30
            },
            'google_play': {
                'base_url': 'https://play.google.com',
                'request_timeout': 30
            },
            'products': [
                {
                    'name': 'Test App',
                    'app_store_id': '123',
                    'play_store_url': 'https://play.google.com/apps/123',
                    'enabled': True
                },
                {
                    'name': 'Disabled App',
                    'app_store_id': '456',
                    'play_store_url': 'https://play.google.com/apps/456',
                    'enabled': False
                }
            ],
            'ingestion': {
                'schedule': '0 2 * * *',
                'batch_size': 100
            }
        }
        
        config_path = os.path.join(temp_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # Set environment variable
        os.environ['DB_HOST'] = 'env_host'
        
        try:
            # Load configuration
            manager = ConfigManager(config_path)
            
            # Test environment variable replacement
            assert manager.get('database.host') == 'env_host'
            
            # Test configuration access methods
            db_config = manager.get_database_config()
            assert db_config['name'] == 'test_db'
            
            redis_config = manager.get_redis_config()
            assert redis_config['host'] == 'localhost'
            
            products = manager.get_products()
            assert len(products) == 2
            
            enabled_products = manager.get_enabled_products()
            assert len(enabled_products) == 1
            assert enabled_products[0]['name'] == 'Test App'
            
            # Test nested key access
            assert manager.get('products.0.name') == 'Test App'
            assert manager.get('products.1.enabled') is False
            
            # Test default value for missing key
            assert manager.get('missing.key', 'default') == 'default'
            
        finally:
            # Clean up environment variable
            del os.environ['DB_HOST']


class TestConfigManagerModule:
    """Test cases for ConfigManager module functions"""
    
    @patch('src.config_manager.ConfigManager')
    @patch('src.config_manager.config_manager', None)
    def test_init_config_no_global_instance(self, mock_config_manager_class):
        """Test init_config when no global instance exists"""
        mock_manager = Mock()
        mock_config_manager_class.return_value = mock_manager
        
        result = init_config('test_config.yaml')
        
        assert result == mock_manager
        mock_config_manager_class.assert_called_once_with('test_config.yaml')
    
    @patch('src.config_manager.ConfigManager')
    @patch('src.config_manager.config_manager')
    def test_init_config_with_global_instance(self, mock_global_config, mock_config_manager_class):
        """Test init_config when global instance exists"""
        mock_global_config.return_value = Mock()
        
        result = init_config('test_config.yaml')
        
        assert result == mock_global_config.return_value
        mock_config_manager_class.assert_not_called()


class TestConfigManagerErrorHandling:
    """Test cases for ConfigManager error handling"""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('yaml.safe_load')
    def test_load_config_permission_error(self, mock_yaml_load, mock_exists, mock_file):
        """Test configuration loading with permission error"""
        mock_exists.return_value = True
        mock_file.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            ConfigManager('restricted_config.yaml')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('yaml.safe_load')
    def test_load_config_io_error(self, mock_yaml_load, mock_exists, mock_file):
        """Test configuration loading with IO error"""
        mock_exists.return_value = True
        mock_file.side_effect = IOError("IO error")
        
        with pytest.raises(IOError):
            ConfigManager('io_error_config.yaml')
    
    def test_get_key_with_none_config(self, config_manager):
        """Test getting key when config is None"""
        config_manager.config = None
        
        result = config_manager.get('any.key')
        assert result is None
    
    def test_validate_config_with_none_config(self, config_manager):
        """Test validation when config is None"""
        config_manager.config = None
        
        with pytest.raises(ValueError, match="Missing required configuration section"):
            config_manager._validate_config()
