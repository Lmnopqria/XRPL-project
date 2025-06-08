# test_foundation.py
"""Test script to verify our foundation is working"""

import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.wallet import generate_faucet_wallet

# Test our imports
from app.config import settings
from app.utils.crypto_conditions import crypto_condition_manager
from app.escrow.models import DisasterParams, DisasterType

async def test_foundation():
    """Test basic functionality"""
    
    print("Testing FarmShield Foundation...")
    print(f"XRPL Network: {settings.XRPL_NETWORK_URL}")
    print(f"Central Wallet: {settings.CENTRAL_WALLET_ADDRESS}")
    
    # Test crypto conditions
    print("\n1. Testing Crypto Conditions...")
    condition, fulfillment_key = crypto_condition_manager.create_condition_for_disaster(
        disaster_type="flood",
        region="maharashtra",
        threshold="200mm"
    )
    print(f"Created condition: {condition[:32]}...")
    print(f"Fulfillment key: {fulfillment_key}")
    
    # Verify it works
    fulfillment = crypto_condition_manager.get_fulfillment(fulfillment_key)
    is_valid = crypto_condition_manager.verify_condition(condition, fulfillment)
    print(f"Verification: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    
    # Test XRPL connection
    print("\n2. Testing XRPL Connection...")
    try:
        async with AsyncJsonRpcClient(settings.XRPL_NETWORK_URL) as client:
            # Test connection
            response = await client.request({
                "command": "server_info"
            })
            
            if response.is_successful():
                print("✓ Connected to XRPL")
                print(f"Ledger: {response.result.get('info', {}).get('validated_ledger', {}).get('seq', 'Unknown')}")
            else:
                print("✗ Failed to connect to XRPL")
                
    except Exception as e:
        print(f"✗ Connection error: {e}")
    
    # Test model creation
    print("\n3. Testing Models...")
    disaster_params = DisasterParams(
        disaster_type=DisasterType.FLOOD,
        region="maharashtra",
        threshold=200.0,
        threshold_unit="mm"
    )
    print(f"✓ Created disaster params: {disaster_params.dict()}")
    
    print("\n✅ Foundation tests complete!")

if __name__ == "__main__":
    asyncio.run(test_foundation())