"""
Configuration management for Phase 1
Handles loading and accessing configuration from YAML files
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from YAML files"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Replace environment variables
            config = self._replace_env_vars(config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _replace_env_vars(self, config: Any) -> Any:
        """Recursively replace environment variable placeholders"""
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str):
            if config.startswith('${') and config.endswith('}'):
                env_var = config[2:-1]
                return os.getenv(env_var, config)
            return config
        return config
    
    def _validate_config(self) -> None:
        """Validate required configuration sections"""
        required_sections = ['database', 'redis', 'app_store', 'google_play', 'products']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        logger.info("Configuration validation passed")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config['database']
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return self.config['redis']
    
    def get_app_store_config(self) -> Dict[str, Any]:
        """Get App Store configuration"""
        return self.config['app_store']
    
    def get_google_play_config(self) -> Dict[str, Any]:
        """Get Google Play configuration"""
        return self.config['google_play']
    
    def get_products(self) -> list:
        """Get products configuration"""
        return self.config['products']
    
    def get_ingestion_config(self) -> Dict[str, Any]:
        """Get ingestion configuration"""
        return self.config.get('ingestion', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.config.get('api', {})
    
    def get_enabled_products(self) -> list:
        """Get only enabled products"""
        return [p for p in self.config['products'] if p.get('enabled', True)]
    
    def reload(self) -> None:
        """Reload configuration from file"""
        logger.info("Reloading configuration")
        self.config = self._load_config()
        self._validate_config()


# Global configuration manager instance
config_manager: Optional[ConfigManager] = None


def init_config(config_path: str = 'config/config.yaml') -> ConfigManager:
    """Initialize the global configuration manager"""
    global config_manager
    if config_manager is None:
        config_manager = ConfigManager(config_path)
    return config_manager
