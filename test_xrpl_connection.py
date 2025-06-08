# test_xrpl_connection.py
"""Test basic XRPL connection and wallet generation"""

import asyncio
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models import ServerInfo
from app.config import settings

async def test_connection():
    """Test XRPL connection"""
    
    print("Testing XRPL Connection...")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n1. Testing basic connection to XRPL...")
    print(f"   URL: {settings.XRPL_NETWORK_URL}")
    
    client = AsyncJsonRpcClient(settings.XRPL_NETWORK_URL)
    
    try:
        # Test server info
        request = ServerInfo()
        response = await client.request(request)
        
        if response.is_successful():
            print("   ✓ Connected successfully!")
            info = response.result.get("info", {})
            print(f"   ✓ Network: {info.get('build_version', 'Unknown')}")
            print(f"   ✓ Ledger: {info.get('validated_ledger', {}).get('seq', 'Unknown')}")
        else:
            print(f"   ✗ Connection failed: {response}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Wallet generation
    print("\n2. Testing wallet generation...")
    try:
        # Check if generate_faucet_wallet is async or sync
        import inspect
        if inspect.iscoroutinefunction(generate_faucet_wallet):
            print("   Using async generate_faucet_wallet...")
            wallet = await generate_faucet_wallet(client, debug=True)
        else:
            print("   Using sync generate_faucet_wallet...")
            wallet = generate_faucet_wallet(client.url, debug=True)
            
        print(f"   ✓ Wallet created: {wallet.address}")
        print(f"   ✓ Public key: {wallet.public_key}")
        print(f"   ✓ Seed: {wallet.seed}")
        
    except Exception as e:
        print(f"   ✗ Wallet generation failed: {e}")
        print("   Note: Faucet might be rate-limited or unavailable")
    
    print("\n✅ Connection test complete!")

if __name__ == "__main__":
    asyncio.run(test_connection())