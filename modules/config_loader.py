"""
Configuration loader for identity card detection settings.
"""

import json
import os
from typing import Dict, List, Any, Tuple


class Config:
    """Configuration manager for identity card detection."""
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config_data is None:
            self.load_config()
    
    def load_config(self, config_path: str = None):
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file (default: config.json in project root)
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file has invalid JSON
        """
        if config_path is None:
            # Default to config.json in project root
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config.json'
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found at: {config_path}\n"
                f"Please create config.json with required document types and settings."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def get_document_types(self) -> Dict[str, Dict]:
        """Get all configured document types."""
        return self._config_data.get('document_types', {})
    
    def get_enabled_document_types(self) -> Dict[str, Dict]:
        """Get only enabled document types."""
        return {
            key: data for key, data in self.get_document_types().items()
            if data.get('enabled', True)
        }
    
    def get_document_type_config(self, doc_type: str) -> Dict:
        """
        Get full configuration for a specific document type.
        
        Args:
            doc_type: Document type key (e.g., 'national_id', 'driver_license')
            
        Returns:
            Full configuration dictionary for the document type
        """
        doc_types = self.get_document_types()
        return doc_types.get(doc_type, {})
    
    def get_document_type_label(self, doc_type: str) -> str:
        """
        Get unique label for a document type (for display in bounding boxes).
        
        Args:
            doc_type: Document type key
            
        Returns:
            Unique label string
        """
        config = self.get_document_type_config(doc_type)
        return config.get('label', doc_type.upper())
    
    def get_document_type_name(self, doc_type: str) -> str:
        """
        Get display name for a document type.
        
        Args:
            doc_type: Document type key
            
        Returns:
            Display name (falls back to key if not found)
        """
        config = self.get_document_type_config(doc_type)
        return config.get('display_name', config.get('name', doc_type))
    
    def get_document_type_color(self, doc_type: str) -> Tuple[int, int, int]:
        """
        Get color for a document type.
        
        Args:
            doc_type: Document type key
            
        Returns:
            RGB color tuple
        """
        config = self.get_document_type_config(doc_type)
        color = config.get('color', [128, 128, 128])
        return tuple(color) if isinstance(color, list) else (128, 128, 128)
    
    def get_document_type_keywords(self, doc_type: str) -> Dict[str, List[str]]:
        """
        Get keywords for a specific document type.
        
        Args:
            doc_type: Document type key
            
        Returns:
            Dictionary of language to keywords mapping
        """
        config = self.get_document_type_config(doc_type)
        return config.get('keywords', {})
    
    def get_document_type_aliases(self, doc_type: str) -> List[str]:
        """
        Get aliases for a specific document type.
        
        Args:
            doc_type: Document type key
            
        Returns:
            List of aliases
        """
        config = self.get_document_type_config(doc_type)
        return config.get('aliases', [])
    
    def get_all_document_type_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Get keywords for all document types."""
        return {
            doc_type: data.get('keywords', {})
            for doc_type, data in self.get_document_types().items()
        }
    
    def get_document_sides(self) -> Dict[str, Dict]:
        """Get all configured document sides."""
        return self._config_data.get('document_sides', {})
    
    def get_enabled_document_sides(self) -> Dict[str, Dict]:
        """Get only enabled document sides."""
        return {
            key: data for key, data in self.get_document_sides().items()
            if data.get('enabled', True)
        }
    
    def get_document_side_config(self, side: str) -> Dict:
        """
        Get full configuration for a specific document side.
        
        Args:
            side: Side key (e.g., 'front', 'back')
            
        Returns:
            Full configuration dictionary for the side
        """
        sides = self.get_document_sides()
        return sides.get(side, {})
    
    def get_document_side_label(self, side: str) -> str:
        """
        Get unique label for a document side (for display in bounding boxes).
        
        Args:
            side: Side key
            
        Returns:
            Unique label string
        """
        config = self.get_document_side_config(side)
        return config.get('label', side[0].upper())
    
    def get_document_side_name(self, side: str) -> str:
        """
        Get display name for a document side.
        
        Args:
            side: Side key
            
        Returns:
            Display name
        """
        config = self.get_document_side_config(side)
        return config.get('display_name', config.get('name', side))
    
    def get_document_side_short_code(self, side: str) -> str:
        """
        Get short code for a document side (e.g., 'F' for front).
        
        Args:
            side: Side key
            
        Returns:
            Short code
        """
        config = self.get_document_side_config(side)
        return config.get('short_code', side[0].upper())
    
    def get_document_side_keywords(self, side: str) -> Dict[str, List[str]]:
        """
        Get keywords for a specific document side.
        
        Args:
            side: Side key
            
        Returns:
            Dictionary of language to keywords mapping
        """
        config = self.get_document_side_config(side)
        return config.get('keywords', {})
    
    def get_all_document_side_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Get keywords for all document sides."""
        return {
            side: data.get('keywords', {})
            for side, data in self.get_document_sides().items()
        }
    
    def get_document_side_aliases(self, side: str) -> List[str]:
        """
        Get aliases for a specific document side.
        
        Args:
            side: Side key
            
        Returns:
            List of aliases
        """
        config = self.get_document_side_config(side)
        return config.get('aliases', [])
    
    def get(self, key: str, default: any = None) -> any:
        """
        Get a config value by key (supports nested keys with dot notation).
        
        Args:
            key: Config key (e.g., 'detection_settings' or 'confidence_boost_settings.single_match_boost')
            default: Default value if key not found
            
        Returns:
            Config value
        """
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_detection_settings(self) -> Dict[str, float]:
        """Get detection settings."""
        return self._config_data.get('detection_settings', {})
    
    def get_setting(self, key: str, default: float = None) -> float:
        """
        Get a specific detection setting.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value
        """
        settings = self.get_detection_settings()
        return settings.get(key, default)
    
    def reload_config(self, config_path: str = None):
        """Reload configuration from file."""
        self._config_data = None
        self.load_config(config_path)
    
    def get_all_keywords_flat(self) -> Dict[str, List[str]]:
        """
        Get all keywords flattened by category.
        
        Returns:
            Dictionary with 'document_types' and 'document_sides' keys
        """
        return {
            'document_types': self.get_all_document_type_keywords(),
            'document_sides': {
                side: data.get('keywords', {})
                for side, data in self.get_document_sides().items()
            }
        }


# Global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config
