# app/utils/crypto_conditions.py
import hashlib
import secrets
from typing import Tuple, Dict
from datetime import datetime

class CryptoConditionManager:
    """Manages cryptographic conditions for XRPL escrows"""
    
    def __init__(self):
        # Store fulfillments securely (in production, use secure storage)
        self._fulfillments: Dict[str, str] = {}
    
    def create_condition_for_disaster(
        self, 
        disaster_type: str, 
        region: str, 
        threshold: str
    ) -> Tuple[str, str]:
        """
        Create a condition/fulfillment pair for a specific disaster scenario
        
        Args:
            disaster_type: Type of disaster (flood, drought, cyclone)
            region: Geographic region
            threshold: Trigger threshold value
            
        Returns:
            Tuple of (condition, fulfillment_key)
        """
        # Generate unique fulfillment
        timestamp = datetime.utcnow().isoformat()
        random_suffix = secrets.token_hex(8)
        
        fulfillment = f"FARMSHIELD:{disaster_type}:{region}:{threshold}:{timestamp}:{random_suffix}"
        
        # Create condition (SHA256 hash of fulfillment)
        condition_bytes = hashlib.sha256(fulfillment.encode('utf-8')).digest()
        # XRPL expects condition as uppercase hex string
        condition = condition_bytes.hex().upper()
        
        # Ensure it's exactly 64 characters (32 bytes)
        if len(condition) != 64:
            raise ValueError(f"Invalid condition length: {len(condition)}")
        
        # Store fulfillment with a key
        fulfillment_key = f"{disaster_type}:{region}"
        self._fulfillments[fulfillment_key] = fulfillment
        
        return condition, fulfillment_key
    
    def get_fulfillment(self, fulfillment_key: str) -> str:
        """
        Retrieve fulfillment for a given key
        
        Args:
            fulfillment_key: Key to identify the fulfillment
            
        Returns:
            The fulfillment string
            
        Raises:
            KeyError: If fulfillment not found
        """
        if fulfillment_key not in self._fulfillments:
            raise KeyError(f"No fulfillment found for key: {fulfillment_key}")
        
        return self._fulfillments[fulfillment_key]
    
    def verify_condition(self, condition: str, fulfillment: str) -> bool:
        """
        Verify that a fulfillment matches a condition
        
        Args:
            condition: The condition hex string
            fulfillment: The fulfillment to test
            
        Returns:
            True if fulfillment hashes to condition
        """
        calculated_condition = hashlib.sha256(
            fulfillment.encode('utf-8')
        ).hexdigest().upper()
        
        return calculated_condition == condition.upper()
    
    def get_all_fulfillments_for_disaster(
        self, 
        disaster_type: str, 
        region: str
    ) -> Dict[str, str]:
        """
        Get all fulfillments matching a disaster type and region
        
        Args:
            disaster_type: Type of disaster
            region: Geographic region
            
        Returns:
            Dictionary of matching fulfillments
        """
        key_prefix = f"{disaster_type}:{region}"
        return {
            k: v for k, v in self._fulfillments.items() 
            if k.startswith(key_prefix)
        }

# Global instance (in production, this would be more sophisticated)
crypto_condition_manager = CryptoConditionManager()