"""
Settings Manager - Encrypted API Key Storage
Handles secure storage and retrieval of API keys from database
"""

import os
import json
from typing import Dict, Optional
from cryptography.fernet import Fernet
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

Base = declarative_base()


class EncryptedSettings(Base):
    """Database model for encrypted settings"""
    __tablename__ = "encrypted_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)  # Encrypted value


class SettingsManager:
    """Manages encrypted API keys and settings"""
    
    def __init__(self, db_path: str = "data/settings.db"):
        """Initialize settings manager with encryption"""
        self.db_path = db_path
        
        # Create data directory if not exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize database
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"Settings manager initialized with database: {db_path}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        key_file = "data/.encryption_key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key)
            # Secure the file (read-only for owner)
            os.chmod(key_file, 0o600)
            logger.info("Generated new encryption key")
            return key
    
    def set(self, key: str, value: str) -> bool:
        """Set encrypted value"""
        try:
            # Encrypt value
            encrypted_value = self.cipher.encrypt(value.encode()).decode()
            
            # Store in database
            session = self.Session()
            try:
                setting = session.query(EncryptedSettings).filter_by(key=key).first()
                if setting:
                    setting.value = encrypted_value
                else:
                    setting = EncryptedSettings(key=key, value=encrypted_value)
                    session.add(setting)
                session.commit()
                logger.info(f"Setting '{key}' saved (encrypted)")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to set '{key}': {e}")
            return False
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get decrypted value"""
        try:
            session = self.Session()
            try:
                setting = session.query(EncryptedSettings).filter_by(key=key).first()
                if setting:
                    # Decrypt value
                    decrypted_value = self.cipher.decrypt(setting.value.encode()).decode()
                    return decrypted_value
                else:
                    return default
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get '{key}': {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete setting"""
        try:
            session = self.Session()
            try:
                setting = session.query(EncryptedSettings).filter_by(key=key).first()
                if setting:
                    session.delete(setting)
                    session.commit()
                    logger.info(f"Setting '{key}' deleted")
                    return True
                return False
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to delete '{key}': {e}")
            return False
    
    def get_all(self) -> Dict[str, str]:
        """Get all settings (decrypted)"""
        try:
            session = self.Session()
            try:
                settings = session.query(EncryptedSettings).all()
                result = {}
                for setting in settings:
                    try:
                        decrypted_value = self.cipher.decrypt(setting.value.encode()).decode()
                        result[setting.key] = decrypted_value
                    except Exception as e:
                        logger.error(f"Failed to decrypt '{setting.key}': {e}")
                return result
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}
    
    def get_masked(self, key: str) -> Optional[str]:
        """Get masked value (for display in UI)"""
        value = self.get(key)
        if value:
            if len(value) > 8:
                return value[:4] + "•" * (len(value) - 8) + value[-4:]
            else:
                return "•" * len(value)
        return None
    
    def validate_api_key(self, key_name: str, key_value: str) -> tuple[bool, str]:
        """Validate API key by testing connection"""
        try:
            if key_name == "ANTHROPIC_API_KEY":
                # Test Claude API
                import anthropic
                client = anthropic.Anthropic(api_key=key_value)
                # Simple test call
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )
                return True, "Claude API key valid"
            
            elif key_name == "LUNARCRUSH_API_KEY":
                # Test LunarCrush API
                import requests
                headers = {"Authorization": f"Bearer {key_value}"}
                response = requests.get(
                    "https://lunarcrush.com/api4/public/coins/list/v1",
                    headers=headers,
                    params={"limit": 1}
                )
                if response.status_code == 200:
                    return True, "LunarCrush API key valid"
                else:
                    return False, f"LunarCrush API error: {response.status_code}"
            
            elif key_name == "MEXC_API_KEY":
                # MEXC validation requires both API key and secret
                # Just check format for now
                if len(key_value) > 10:
                    return True, "MEXC API key format valid"
                else:
                    return False, "MEXC API key too short"
            
            elif key_name == "MEXC_SECRET_KEY":
                # Just check format
                if len(key_value) > 10:
                    return True, "MEXC Secret key format valid"
                else:
                    return False, "MEXC Secret key too short"
            
            elif key_name == "OPENROUTER_API_KEY":
                # Test OpenRouter API
                import requests
                headers = {"Authorization": f"Bearer {key_value}"}
                response = requests.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers
                )
                if response.status_code == 200:
                    return True, "OpenRouter API key valid"
                else:
                    return False, f"OpenRouter API error: {response.status_code}"
            
            else:
                # Unknown key type, just save it
                return True, "API key saved (validation not available)"
        
        except Exception as e:
            logger.error(f"API key validation failed for {key_name}: {e}")
            return False, f"Validation error: {str(e)}"


# Global instance
_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
