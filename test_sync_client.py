# test_sync_client.py
"""Test wallet generation with synchronous client"""

from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from app.config import settings

def test_with_sync_client():
    """Test using synchronous JsonRpcClient"""
    
    print("Testing with Synchronous JsonRpcClient...")
    print("=" * 50)
    
    try:
        # Create synchronous client
        print(f"\n1. Creating sync client for: {settings.XRPL_NETWORK_URL}")
        client = JsonRpcClient(settings.XRPL_NETWORK_URL)
        print("   ✓ Client created")
        
        # Test connection
        print("\n2. Testing connection...")
        response = client.request({"command": "server_info"})
        if response.is_successful():
            print("   ✓ Connected to XRPL")
        else:
            print(f"   ✗ Connection failed: {response}")
            return None
        
        # Generate wallet
        print("\n3. Generating funded wallet...")
        wallet = generate_faucet_wallet(client, debug=True)
        print(f"   ✓ Wallet created: {wallet.address}")
        print(f"   ✓ Seed: {wallet.seed}")
        
        return wallet
        
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    wallet = test_with_sync_client()
    if wallet:
        print("\n✅ Success! Wallet generation works with sync client")
    else:
        print("\n❌ Failed to generate wallet")