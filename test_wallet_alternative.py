# test_wallet_alternative.py
"""Test alternative wallet creation methods"""

from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.core import keypairs
from app.config import settings
import requests

def test_wallet_methods():
    """Test different wallet creation methods"""
    
    print("Testing Alternative Wallet Methods...")
    print("=" * 50)
    
    # Method 1: Create a wallet without funding (for testing structure)
    print("\n1. Creating unfunded wallet...")
    try:
        # Generate a random wallet
        wallet = Wallet.create()
        print(f"   ✓ Wallet created: {wallet.address}")
        print(f"   ✓ Public key: {wallet.public_key}")
        print(f"   ✓ Seed: {wallet.seed}")
        print("   ⚠️  Note: This wallet has no XRP (unfunded)")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Method 2: Try direct faucet API call
    print("\n2. Testing direct faucet API...")
    try:
        # Create a wallet first
        new_wallet = Wallet.create()
        
        # Try to fund it via faucet API
        faucet_url = "https://faucet.altnet.rippletest.net/accounts"
        response = requests.post(faucet_url, json={
            "destination": new_wallet.address
        })
        
        if response.status_code == 200:
            print(f"   ✓ Funded wallet: {new_wallet.address}")
            print(f"   ✓ Response: {response.json()}")
        else:
            print(f"   ✗ Faucet failed: Status {response.status_code}")
            print(f"   ✗ Response: {response.text}")
    except Exception as e:
        print(f"   ✗ API call failed: {e}")
    
    # Method 3: Check if we can connect to testnet at all
    print("\n3. Testing testnet connectivity...")
    try:
        response = requests.get(settings.XRPL_NETWORK_URL, timeout=5)
        print(f"   ✓ Testnet reachable: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Cannot reach testnet: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_wallet_methods()