"""
Client Context Management System
Handles multi-client support by managing current client context throughout the application.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ClientContext:
    """
    Manages the current client context for the application.
    Provides a centralized way to handle multi-client operations.
    """
    
    _instance = None
    _current_client_id: Optional[str] = None
    _client_cache: Dict[str, Dict[str, Any]] = {}
    _config_file = Path.home() / '.cfo_forecast' / 'client_context.json'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientContext, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the client context on first use."""
        # Ensure config directory exists
        self._config_file.parent.mkdir(exist_ok=True)
        
        # Load last used client if available
        self._load_context()
        
        # Set default client if none is set
        if not self._current_client_id:
            default_client = os.getenv('DEFAULT_CLIENT_ID', 'demo')
            self._current_client_id = default_client
            logger.info(f"No client context found, using default: {default_client}")
    
    def _load_context(self):
        """Load client context from disk."""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r') as f:
                    data = json.load(f)
                    self._current_client_id = data.get('current_client_id')
                    self._client_cache = data.get('client_cache', {})
                    logger.debug(f"Loaded client context: {self._current_client_id}")
        except Exception as e:
            logger.warning(f"Could not load client context: {e}")
    
    def _save_context(self):
        """Save client context to disk."""
        try:
            data = {
                'current_client_id': self._current_client_id,
                'client_cache': self._client_cache
            }
            with open(self._config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved client context: {self._current_client_id}")
        except Exception as e:
            logger.warning(f"Could not save client context: {e}")
    
    def set_client(self, client_id: str) -> bool:
        """
        Set the current client context.
        
        Args:
            client_id: The client ID to set as current
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not client_id or not isinstance(client_id, str):
                raise ValueError("Client ID must be a non-empty string")
            
            # Validate client exists (you might want to check database here)
            if self._validate_client(client_id):
                old_client = self._current_client_id
                self._current_client_id = client_id
                self._save_context()
                
                logger.info(f"Client context changed: {old_client} → {client_id}")
                return True
            else:
                logger.error(f"Invalid client ID: {client_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting client context: {e}")
            return False
    
    def get_client(self) -> str:
        """
        Get the current client ID.
        
        Returns:
            str: Current client ID
        """
        if not self._current_client_id:
            # Fallback to environment variable or default
            default_client = os.getenv('DEFAULT_CLIENT_ID', 'demo')
            self._current_client_id = default_client
            logger.warning(f"No client context set, using default: {default_client}")
        
        return self._current_client_id
    
    def get_client_config(self, key: str = None) -> Any:
        """
        Get client-specific configuration.
        
        Args:
            key: Specific config key to retrieve, or None for all config
            
        Returns:
            Client configuration value or dict
        """
        client_id = self.get_client()
        
        if client_id not in self._client_cache:
            self._client_cache[client_id] = self._load_client_config(client_id)
        
        config = self._client_cache[client_id]
        
        if key:
            return config.get(key)
        return config
    
    def set_client_config(self, key: str, value: Any) -> bool:
        """
        Set client-specific configuration.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            bool: True if successful
        """
        try:
            client_id = self.get_client()
            
            if client_id not in self._client_cache:
                self._client_cache[client_id] = {}
            
            self._client_cache[client_id][key] = value
            self._save_context()
            
            logger.debug(f"Set client config for {client_id}: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting client config: {e}")
            return False
    
    def _validate_client(self, client_id: str) -> bool:
        """
        Validate that a client ID is valid.
        
        Args:
            client_id: Client ID to validate
            
        Returns:
            bool: True if valid
        """
        # For now, accept any non-empty string
        # In the future, this could check against a database
        return bool(client_id and client_id.strip())
    
    def _load_client_config(self, client_id: str) -> Dict[str, Any]:
        """
        Load client-specific configuration.
        
        Args:
            client_id: Client ID
            
        Returns:
            dict: Client configuration
        """
        # Default configuration
        config = {
            'client_id': client_id,
            'name': client_id.title(),
            'forecast_weeks': 13,
            'minimum_balance_threshold': 10000,
            'confidence_threshold': 0.7,
            'currency': 'USD',
            'timezone': 'America/New_York'
        }
        
        # TODO: Load from database or config file
        # This is where you'd fetch client-specific settings
        
        return config
    
    def list_available_clients(self) -> list:
        """
        Get list of available clients.
        
        Returns:
            list: Available client IDs
        """
        # TODO: Query database for available clients
        # For now, return cached clients plus some defaults
        clients = list(self._client_cache.keys())
        
        # Add some default clients if none exist
        if not clients:
            clients = ['demo', 'acme_corp', 'beta_llc']
        
        return sorted(set(clients))
    
    def create_client(self, client_id: str, name: str = None, config: Dict[str, Any] = None) -> bool:
        """
        Create a new client.
        
        Args:
            client_id: Unique client identifier
            name: Display name for the client
            config: Optional client-specific configuration
            
        Returns:
            bool: True if successful
        """
        try:
            if not self._validate_client(client_id):
                return False
            
            # Create client configuration
            client_config = {
                'client_id': client_id,
                'name': name or client_id.title(),
                'created_at': str(datetime.now()),
                'forecast_weeks': 13,
                'minimum_balance_threshold': 10000,
                'confidence_threshold': 0.7,
                'currency': 'USD',
                'timezone': 'America/New_York'
            }
            
            if config:
                client_config.update(config)
            
            self._client_cache[client_id] = client_config
            self._save_context()
            
            logger.info(f"Created new client: {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return False


# Global instance for easy access
_context_instance = None

def get_client_context() -> ClientContext:
    """Get the global client context instance."""
    global _context_instance
    if _context_instance is None:
        _context_instance = ClientContext()
    return _context_instance

def get_current_client() -> str:
    """Convenience function to get current client ID."""
    return get_client_context().get_client()

def set_current_client(client_id: str) -> bool:
    """Convenience function to set current client."""
    return get_client_context().set_client(client_id)

def get_client_config(key: str = None) -> Any:
    """Convenience function to get client configuration."""
    return get_client_context().get_client_config(key)


if __name__ == "__main__":
    # Test the client context system
    import sys
    logging.basicConfig(level=logging.DEBUG)
    
    context = ClientContext()
    
    print(f"Current client: {context.get_client()}")
    print(f"Available clients: {context.list_available_clients()}")
    
    # Test setting client
    context.set_client("test_client")
    print(f"After setting: {context.get_client()}")
    
    # Test client config
    context.set_client_config("test_key", "test_value")
    print(f"Config: {context.get_client_config('test_key')}")
    
    print("✅ Client context system working!")