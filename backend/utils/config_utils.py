import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("visualize-it")

class ConfigUtils:
    """
    Utility class for configuration management
    """
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self.config = self._load_config()
        
        logger.info(f"ConfigUtils initialized with config_file={self.config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                logger.info(f"Config file {self.config_file} not found, using default configuration")
                return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
    
    def save_config(self) -> bool:
        """
        Save configuration to file
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        """
        self.config[key] = value
        
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update multiple configuration values
        """
        self.config.update(config_dict)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values
        """
        return self.config.copy()
