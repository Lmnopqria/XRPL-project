# test_escrow_manager.py
"""Test the EscrowManager functionality"""

import asyncio
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.utils import xrp_to_drops

from app.escrow.escrow_manager import escrow_manager
from app.escrow.models import DisasterParams, DisasterType
from app.config import settings

async def test_escrow_manager():
    """Test escrow creation and management"""
    
    print("Testing EscrowManager...")
    print("=" * 50)
    
    # Create test wallets
    print("\n1. Creating test wallets...")
    try:
        # Create client for wallet generation
        client = AsyncJsonRpcClient(settings.XRPL_NETWORK_URL)
        
        # Create donor wallet
        print("   Creating donor wallet...")
        donor_wallet = await generate_faucet_wallet(client, debug=True)
        print(f"   ✓ Donor wallet: {donor_wallet.address}")
        
        # Create oracle wallet (for releases)
        print("   Creating oracle wallet...")
        oracle_wallet = await generate_faucet_wallet(client, debug=True)
        print(f"   ✓ Oracle wallet: {oracle_wallet.address}")
        
    except Exception as e:
        print(f"   ✗ Error creating wallets: {e}")
        print("   Make sure you're connected to the XRPL testnet")
        return
    
    # Test parameters
    disaster_params = DisasterParams(
        disaster_type=DisasterType.FLOOD,
        region="maharashtra",
        threshold=200.0,
        threshold_unit="mm"
    )
    
    # Create multiple escrows
    print("\n2. Creating multiple escrows for flood relief...")
    escrow_amounts = [100, 50, 200]  # XRP amounts
    created_escrows = []
    
    for i, amount_xrp in enumerate(escrow_amounts):
        print(f"\n   Donation {i+1}: {amount_xrp} XRP")
        amount_drops = xrp_to_drops(amount_xrp)
        
        result = await escrow_manager.create_escrow(
            donor_wallet=donor_wallet,
            amount_drops=amount_drops,
            disaster_params=disaster_params
        )
        
        if result.success:
            print(f"   ✓ Escrow created: {result.escrow_id}")
            print(f"   ✓ Condition: {result.condition[:32]}...")
            print(f"   ✓ TX Hash: {result.tx_hash}")
            created_escrows.append(result)
        else:
            print(f"   ✗ Failed: {result.error}")
    
    # Check escrow summary
    print("\n3. Escrow Summary:")
    summary = escrow_manager.get_escrow_summary()
    print(f"   Total escrows: {summary['total_escrows']}")
    print(f"   Total amount: {summary['total_amount_xrp']} XRP")
    print(f"   By status: {summary['by_status']}")
    print(f"   By disaster: {summary['by_disaster_type']}")
    
    # Find escrows for disaster
    print("\n4. Finding escrows for Maharashtra flood...")
    escrows = await escrow_manager.get_escrows_for_disaster(
        disaster_type="flood",
        region="maharashtra"
    )
    print(f"   Found {len(escrows)} escrows")
    
    # Simulate oracle release (commented out to not actually release)
    print("\n5. Simulating oracle release...")
    print("   (In real scenario, oracle would detect flood and trigger this)")
    print("   Ready to release all escrows when disaster threshold is met")
    
    # Show how release would work
    print("\n   Example release code:")
    print("   ```")
    print("   response = await escrow_manager.release_escrows_for_disaster(")
    print("       oracle_wallet=oracle_wallet,")
    print("       disaster_type='flood',")
    print("       region='maharashtra'")
    print("   )")
    print("   ```")
    
    print("\n✅ EscrowManager test complete!")
    print("\nNext steps:")
    print("- Implement Oracle service to monitor weather")
    print("- Create API endpoints for integration")
    print("- Test actual release mechanism")

if __name__ == "__main__":
    asyncio.run(test_escrow_manager())