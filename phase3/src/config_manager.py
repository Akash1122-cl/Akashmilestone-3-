"""
Configuration Manager for Phase 3
Handles loading and managing configuration from YAML files
"""

import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for Phase 3"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/config.yaml relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, '..', 'config', 'config.yaml')
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in configuration"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            env_var = config[2:-1]
            value = os.getenv(env_var)
            if value is None:
                logger.warning(f"Environment variable {env_var} not found, using placeholder")
                return f"${{{env_var}}}"
            return value
        else:
            return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)"""
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
        return self.config.get('database', {})
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return self.config.get('redis', {})
    
    def get_clustering_config(self) -> Dict[str, Any]:
        """Get clustering configuration"""
        return self.config.get('clustering', {})
    
    def get_theme_analyzer_config(self) -> Dict[str, Any]:
        """Get theme analyzer configuration"""
        return self.config.get('theme_analyzer', {})
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration"""
        return self.config.get('validation', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.config.get('api', {})
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        logger.info("Configuration reloaded")
