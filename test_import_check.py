# test_import_check.py
"""Check what's available in xrpl library"""

import inspect

print("Checking XRPL Library Structure...")
print("=" * 50)

# Check wallet module
print("\n1. Checking xrpl.wallet module:")
try:
    from xrpl import wallet
    print("   Available functions:")
    for name, obj in inspect.getmembers(wallet):
        if not name.startswith('_'):
            print(f"   - {name}: {type(obj)}")
except Exception as e:
    print(f"   Error: {e}")

# Check generate_faucet_wallet specifically
print("\n2. Checking generate_faucet_wallet:")
try:
    from xrpl.wallet import generate_faucet_wallet
    print(f"   Type: {type(generate_faucet_wallet)}")
    print(f"   Signature: {inspect.signature(generate_faucet_wallet)}")
    print(f"   Is coroutine: {inspect.iscoroutinefunction(generate_faucet_wallet)}")
    
    # Check docstring
    if generate_faucet_wallet.__doc__:
        print(f"   Docstring: {generate_faucet_wallet.__doc__[:200]}...")
except Exception as e:
    print(f"   Error: {e}")

# Check for alternative faucet functions
print("\n3. Checking xrpl.account module:")
try:
    from xrpl import account
    print("   Available functions:")
    for name, obj in inspect.getmembers(account):
        if not name.startswith('_') and callable(obj):
            print(f"   - {name}")
except Exception as e:
    print(f"   Error: {e}")

# Check clients
print("\n4. Checking client types:")
try:
    from xrpl.clients import JsonRpcClient, WebsocketClient
    print("   ✓ JsonRpcClient available")
    print("   ✓ WebsocketClient available")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 50)