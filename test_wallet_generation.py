# test_wallet_generation.py
"""Test to determine the correct wallet generation method"""

import asyncio
import inspect
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from app.config import settings

async def test_wallet_generation():
    """Test different wallet generation methods"""
    
    print("Testing Wallet Generation Methods...")
    print("=" * 50)
    
    client = AsyncJsonRpcClient(settings.XRPL_NETWORK_URL)
    
    # Method 1: Try sync generation with URL
    print("\n1. Testing sync generation with URL...")
    try:
        wallet = generate_faucet_wallet(settings.XRPL_NETWORK_URL, debug=True)
        print(f"   ✓ SUCCESS! Wallet created: {wallet.address}")
        print("   → Use sync generation with URL string")
        return wallet
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Method 2: Try sync generation with client object
    print("\n2. Testing sync generation with client...")
    try:
        wallet = generate_faucet_wallet(client, debug=True)
        print(f"   ✓ SUCCESS! Wallet created: {wallet.address}")
        print("   → Use sync generation with client object")
        return wallet
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Method 3: Try async generation
    print("\n3. Testing async generation...")
    try:
        # Check if it's actually an async function
        if inspect.iscoroutinefunction(generate_faucet_wallet):
            wallet = await generate_faucet_wallet(client, debug=True)
            print(f"   ✓ SUCCESS! Wallet created: {wallet.address}")
            print("   → Use async generation")
            return wallet
        else:
            print("   ✗ generate_faucet_wallet is not async")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n❌ All methods failed!")
    return None

if __name__ == "__main__":
    result = asyncio.run(test_wallet_generation())
    if result:
        print(f"\n✅ Working method found! Wallet: {result.address}")