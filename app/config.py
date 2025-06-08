# app/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # XRPL Network Configuration
    XRPL_NETWORK_URL: str = "https://s.altnet.rippletest.net:51234"  # Testnet
    
    # Central Wallet (dummy for now - replace with actual)
    CENTRAL_WALLET_ADDRESS: str = "rN7n7otQDd6FczFgLdSqtcsAUxDkw6fzRH"
    
    # Oracle Configuration
    ORACLE_WALLET_SEED: Optional[str] = None  # Will be set in .env
    WEATHER_API_KEY: Optional[str] = None     # For weather monitoring
    ORACLE_POLL_INTERVAL: int = 60            # Seconds between weather checks
    
    # Escrow Configuration
    ESCROW_MIN_FINISH_AFTER: int = 3600       # 1 hour in seconds
    ESCROW_CANCEL_AFTER_DAYS: int = 90        # Days until escrow can be cancelled
    
    # Disaster Thresholds
    FLOOD_THRESHOLD_MM: float = 200.0         # mm of rain in 24 hours
    DROUGHT_THRESHOLD_DAYS: int = 30          # Days without significant rain
    CYCLONE_THRESHOLD_KMPH: float = 120.0     # Wind speed in km/h
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()