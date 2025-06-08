# app/escrow/escrow_manager.py
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.models import (
    EscrowCreate, EscrowFinish, AccountObjects,
    IssuedCurrencyAmount
)
from xrpl.utils import datetime_to_ripple_time, drops_to_xrp
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.wallet import Wallet

from app.config import settings
from app.utils.crypto_conditions import crypto_condition_manager
from app.escrow.models import (
    EscrowRecord, EscrowStatus, DisasterParams,
    EscrowResponse, BulkReleaseResponse
)

class EscrowManager:
    """Manages multiple escrows for disaster relief donations"""
    
    def __init__(self):
        self.client_url = settings.XRPL_NETWORK_URL
        self.destination = settings.CENTRAL_WALLET_ADDRESS
        # In-memory storage (in production, use a database)
        self.escrows: Dict[str, List[EscrowRecord]] = {}
        
    async def create_escrow(
        self,
        donor_wallet: Wallet,
        amount_drops: str,
        disaster_params: DisasterParams
    ) -> EscrowResponse:
        """
        Create a new conditional escrow for disaster relief
        
        Args:
            donor_wallet: The donor's XRPL wallet
            amount_drops: Amount to escrow in drops
            disaster_params: Disaster-specific parameters
            
        Returns:
            EscrowResponse with transaction details
        """
        try:
            # Create client instance
            client = AsyncJsonRpcClient(self.client_url)
            
            # Create unique condition for this disaster scenario
            condition, fulfillment_key = crypto_condition_manager.create_condition_for_disaster(
                disaster_type=disaster_params.disaster_type,
                region=disaster_params.region,
                threshold=str(disaster_params.threshold)
            )
            
            # Calculate time boundaries
            now = datetime.utcnow()
            finish_after = now + timedelta(seconds=settings.ESCROW_MIN_FINISH_AFTER)
            cancel_after = now + timedelta(days=settings.ESCROW_CANCEL_AFTER_DAYS)
            
            # Create escrow transaction
            escrow_tx = EscrowCreate(
                account=donor_wallet.address,
                destination=self.destination,
                amount=amount_drops,
                condition=condition,
                finish_after=datetime_to_ripple_time(finish_after),
                cancel_after=datetime_to_ripple_time(cancel_after)
            )
            
            # Submit transaction
            response = await submit_and_wait(
                transaction=escrow_tx,
                client=client,
                wallet=donor_wallet
            )
            
            if response.is_successful():
                # Extract sequence number for escrow ID
                sequence = response.result.get("Sequence", 0)
                escrow_id = f"{donor_wallet.address}:{sequence}"
                
                # Store escrow record
                escrow_record = EscrowRecord(
                    escrow_id=escrow_id,
                    donor_address=donor_wallet.address,
                    amount_drops=amount_drops,
                    destination=self.destination,
                    condition=condition,
                    fulfillment_key=fulfillment_key,
                    disaster_params=disaster_params,
                    status=EscrowStatus.CREATED,
                    created_at=now,
                    finish_after=finish_after,
                    cancel_after=cancel_after,
                    tx_hash=response.result.get("hash")
                )
                
                # Index by disaster type and region for easy lookup
                storage_key = f"{disaster_params.disaster_type}:{disaster_params.region}"
                if storage_key not in self.escrows:
                    self.escrows[storage_key] = []
                self.escrows[storage_key].append(escrow_record)
                
                return EscrowResponse(
                    success=True,
                    escrow_id=escrow_id,
                    tx_hash=response.result.get("hash"),
                    condition=condition
                )
            else:
                return EscrowResponse(
                    success=False,
                    error=f"Transaction failed: {response.result}"
                )
                    
        except Exception as e:
            return EscrowResponse(
                success=False,
                error=f"Error creating escrow: {str(e)}"
            )
    
    async def get_escrows_for_disaster(
        self,
        disaster_type: str,
        region: str
    ) -> List[EscrowRecord]:
        """
        Get all escrows matching a disaster type and region
        
        Args:
            disaster_type: Type of disaster
            region: Geographic region
            
        Returns:
            List of matching escrow records
        """
        key = f"{disaster_type}:{region}"
        return self.escrows.get(key, [])
    
    async def release_escrows_for_disaster(
        self,
        oracle_wallet: Wallet,
        disaster_type: str,
        region: str
    ) -> BulkReleaseResponse:
        """
        Release all escrows matching a disaster event
        
        Args:
            oracle_wallet: The oracle's wallet (pays fees)
            disaster_type: Type of disaster detected
            region: Affected region
            
        Returns:
            Summary of releases
        """
        # Get all matching escrows
        escrows = await self.get_escrows_for_disaster(disaster_type, region)
        active_escrows = [e for e in escrows if e.status == EscrowStatus.CREATED]
        
        if not active_escrows:
            return BulkReleaseResponse(
                total_escrows=0,
                successful_releases=0,
                failed_releases=0,
                total_amount_released="0"
            )
        
        successful = 0
        failed = 0
        total_released = 0
        errors = []
        
        # Create client instance
        client = AsyncJsonRpcClient(self.client_url)
        
        for escrow in active_escrows:
            try:
                # Get fulfillment for this escrow
                fulfillment = crypto_condition_manager.get_fulfillment(
                    escrow.fulfillment_key
                )
                
                # Parse escrow ID to get owner and sequence
                owner, sequence = escrow.escrow_id.split(":")
                
                # Create finish transaction
                finish_tx = EscrowFinish(
                    account=oracle_wallet.address,
                    owner=owner,
                    offer_sequence=int(sequence),
                    condition=escrow.condition,
                    fulfillment=fulfillment.upper()
                )
                
                # Submit transaction
                response = await submit_and_wait(
                    transaction=finish_tx,
                    client=client,
                    wallet=oracle_wallet
                )
                
                if response.is_successful():
                    escrow.status = EscrowStatus.RELEASED
                    escrow.release_tx_hash = response.result.get("hash")
                    successful += 1
                    total_released += int(escrow.amount_drops)
                else:
                    escrow.status = EscrowStatus.FAILED
                    escrow.error_message = str(response.result)
                    failed += 1
                    errors.append({
                        "escrow_id": escrow.escrow_id,
                        "error": str(response.result)
                    })
                    
            except Exception as e:
                escrow.status = EscrowStatus.FAILED
                escrow.error_message = str(e)
                failed += 1
                errors.append({
                    "escrow_id": escrow.escrow_id,
                    "error": str(e)
                })
        
        return BulkReleaseResponse(
            total_escrows=len(active_escrows),
            successful_releases=successful,
            failed_releases=failed,
            total_amount_released=str(total_released),
            errors=errors
        )
    
    async def find_escrows_on_ledger(
        self,
        destination_address: Optional[str] = None
    ) -> List[dict]:
        """
        Find all escrows on the ledger for a destination
        
        Args:
            destination_address: Address to check (defaults to central wallet)
            
        Returns:
            List of escrow objects from ledger
        """
        if not destination_address:
            destination_address = self.destination
            
        client = AsyncJsonRpcClient(self.client_url)
        
        # Get all objects for the destination account
        response = await client.request(
            AccountObjects(
                account=destination_address,
                ledger_index="validated",
                type="escrow"
            )
        )
        
        if response.is_successful():
            return response.result.get("account_objects", [])
        else:
            return []
    
    def get_escrow_summary(self) -> dict:
        """Get summary statistics of all escrows"""
        total_escrows = 0
        total_amount = 0
        by_status = {}
        by_disaster = {}
        
        for key, escrows in self.escrows.items():
            disaster_type, region = key.split(":")
            
            for escrow in escrows:
                total_escrows += 1
                total_amount += int(escrow.amount_drops)
                
                # Count by status
                status = escrow.status.value
                by_status[status] = by_status.get(status, 0) + 1
                
                # Count by disaster type
                if disaster_type not in by_disaster:
                    by_disaster[disaster_type] = {
                        "count": 0,
                        "amount_drops": 0,
                        "regions": set()
                    }
                
                by_disaster[disaster_type]["count"] += 1
                by_disaster[disaster_type]["amount_drops"] += int(escrow.amount_drops)
                by_disaster[disaster_type]["regions"].add(region)
        
        # Convert sets to lists for JSON serialization
        for disaster in by_disaster.values():
            disaster["regions"] = list(disaster["regions"])
        
        return {
            "total_escrows": total_escrows,
            "total_amount_xrp": drops_to_xrp(str(total_amount)) if total_amount > 0 else "0",
            "by_status": by_status,
            "by_disaster_type": by_disaster
        }

# Global instance
escrow_manager = EscrowManager()