# test_wallet_sync.py
"""Test synchronous wallet generation"""

from xrpl.wallet import generate_faucet_wallet
from app.config import settings

def test_wallet_generation_sync():
    """Test wallet generation without async"""
    
    print("Testing Synchronous Wallet Generation...")
    print("=" * 50)
    
    # Method 1: Direct URL
    print("\n1. Testing with URL string...")
    try:
        wallet = generate_faucet_wallet(settings.XRPL_NETWORK_URL, debug=True)
        print(f"   ✓ SUCCESS! Wallet created: {wallet.address}")
        print(f"   ✓ Public key: {wallet.public_key}")
        print(f"   ✓ Seed: {wallet.seed}")
        return wallet
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    wallet = test_wallet_generation_sync()
    if wallet:
        print("\n✅ Wallet generation successful!")
    else:
        print("\n❌ Wallet generation failed!")