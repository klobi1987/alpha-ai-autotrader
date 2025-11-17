"""
Settings API Routes
Handles API key management through dashboard
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from loguru import logger

from backend.core.settings_manager import get_settings_manager

router = APIRouter(prefix="/api/settings", tags=["settings"])


class APIKeyUpdate(BaseModel):
    """API key update request"""
    key_name: str
    key_value: str


class SettingUpdate(BaseModel):
    """General setting update"""
    key: str
    value: str


class APIKeyResponse(BaseModel):
    """API key response (masked)"""
    key_name: str
    masked_value: Optional[str]
    is_set: bool
    status: str  # "valid", "invalid", "not_set"


@router.get("/api-keys")
async def get_api_keys() -> Dict[str, APIKeyResponse]:
    """Get all API keys (masked values)"""
    try:
        settings = get_settings_manager()
        
        keys = [
            "ANTHROPIC_API_KEY",
            "LUNARCRUSH_API_KEY",
            "MEXC_API_KEY",
            "MEXC_SECRET_KEY",
            "OPENROUTER_API_KEY"
        ]
        
        result = {}
        for key_name in keys:
            value = settings.get(key_name)
            masked = settings.get_masked(key_name)
            
            result[key_name] = APIKeyResponse(
                key_name=key_name,
                masked_value=masked,
                is_set=value is not None,
                status="valid" if value else "not_set"
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys")
async def update_api_key(update: APIKeyUpdate) -> Dict[str, any]:
    """Update API key with validation"""
    try:
        settings = get_settings_manager()
        
        # Validate API key
        is_valid, message = settings.validate_api_key(update.key_name, update.key_value)
        
        if not is_valid:
            return {
                "success": False,
                "message": message,
                "key_name": update.key_name
            }
        
        # Save API key
        success = settings.set(update.key_name, update.key_value)
        
        if success:
            logger.info(f"API key '{update.key_name}' updated successfully")
            return {
                "success": True,
                "message": message,
                "key_name": update.key_name,
                "masked_value": settings.get_masked(update.key_name)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save API key")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{key_name}")
async def delete_api_key(key_name: str) -> Dict[str, any]:
    """Delete API key"""
    try:
        settings = get_settings_manager()
        success = settings.delete(key_name)
        
        if success:
            logger.info(f"API key '{key_name}' deleted")
            return {
                "success": True,
                "message": f"API key '{key_name}' deleted",
                "key_name": key_name
            }
        else:
            return {
                "success": False,
                "message": f"API key '{key_name}' not found",
                "key_name": key_name
            }
    
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trading")
async def get_trading_settings() -> Dict[str, any]:
    """Get trading configuration settings"""
    try:
        settings = get_settings_manager()
        
        return {
            "trading_mode": settings.get("TRADING_MODE", "testing"),
            "auto_trading_enabled": settings.get("AUTO_TRADING_ENABLED", "false") == "true",
            "max_position_size": float(settings.get("MAX_POSITION_SIZE", "500")),
            "max_leverage": int(settings.get("MAX_LEVERAGE", "5")),
            "max_concurrent_positions": int(settings.get("MAX_CONCURRENT_POSITIONS", "3")),
            "stop_loss_default": float(settings.get("STOP_LOSS_DEFAULT", "2.0")),
            "min_confidence": float(settings.get("MIN_CONFIDENCE", "7.5")),
            "enable_spot_trading": settings.get("ENABLE_SPOT_TRADING", "true") == "true",
            "enable_futures_trading": settings.get("ENABLE_FUTURES_TRADING", "true") == "true",
            "auto_compound_profits": settings.get("AUTO_COMPOUND_PROFITS", "false") == "true",
        }
    
    except Exception as e:
        logger.error(f"Failed to get trading settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trading")
async def update_trading_settings(settings_data: Dict[str, any]) -> Dict[str, any]:
    """Update trading configuration settings"""
    try:
        settings = get_settings_manager()
        
        # Update each setting
        for key, value in settings_data.items():
            # Convert to string for storage
            str_value = str(value).lower() if isinstance(value, bool) else str(value)
            settings.set(key.upper(), str_value)
        
        logger.info(f"Trading settings updated: {list(settings_data.keys())}")
        
        return {
            "success": True,
            "message": "Trading settings updated successfully",
            "settings": await get_trading_settings()
        }
    
    except Exception as e:
        logger.error(f"Failed to update trading settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection/{key_name}")
async def test_api_connection(key_name: str) -> Dict[str, any]:
    """Test API key connection"""
    try:
        settings = get_settings_manager()
        key_value = settings.get(key_name)
        
        if not key_value:
            return {
                "success": False,
                "message": f"API key '{key_name}' not set"
            }
        
        is_valid, message = settings.validate_api_key(key_name, key_value)
        
        return {
            "success": is_valid,
            "message": message,
            "key_name": key_name
        }
    
    except Exception as e:
        logger.error(f"Failed to test API connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
