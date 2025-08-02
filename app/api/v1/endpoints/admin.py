from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
import asyncio
from xrpl.wallet import Wallet
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.account import get_balance
from app.core.database import get_db
from app.core.xrpl_transaction import send_xrp_to_user
from app.core.escrow_processor import process_escrow_results
from app.models.user import User as UserModel
from app.models.donation_summary import DonationSummary
from app.models.escrow_record import EscrowRecord, EscrowStatus
from app.escrow.escrow_sample import release_escrow

from cryptography.fernet import Fernet
FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

class DistributeRequest(BaseModel):
    disaster_area: str

router = APIRouter()
load_dotenv()


def get_users_by_area(db: Session, area: str) -> List[Dict[str, str]]:
    """
    Get user IDs and wallet addresses for users in a specific area
    
    Args:
        db (Session): Database session
        area (str): Area to search for    
    Returns:
        List[Dict[str, str]]: List of dictionaries containing user_id and wallet_address
    """
    users = db.query(
        UserModel.user_id,
        UserModel.wallet_address
    ).filter(
        UserModel.address == area
    ).all()
    
    return [
        {"user_id": str(user.user_id), "wallet_address": user.wallet_address}
        for user in users
    ]

# Background Function
async def process_distribution(
    central_wallet: Wallet,
    affected_users: List[Dict[str, str]],
    client: AsyncJsonRpcClient,
    db: Session
):
    # Procss All the Escrows
    escrows = db.query(EscrowRecord).filter(EscrowRecord.status == EscrowStatus.REGISTERED).all()
    for escrow in escrows:
        escrow.status = EscrowStatus.PROCESSING
    db.commit()
    print(f"[Start Releasing Escrows] Started to release {len(escrows)} registered escrows.")
    tasks = []
   
    for escrow in escrows:
        decrypted_secret_key = fernet.decrypt(escrow.secret_key.encode()).decode()
        task = release_escrow(
            escrow_id=escrow.escrow_id,
            tx_sequence=escrow.tx_sequence,
            from_address=escrow.from_wallet_address,
            secret_key=decrypted_secret_key
        )
        tasks.append(task)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful_count, total_escrows, released_sum = process_escrow_results(db, results)
    
    print(f"[Escrow Release Summary] Successfully released {successful_count}/{total_escrows} escrows. \nTotal amount released: {released_sum}")
    if released_sum == 0 or total_escrows == 0:
        print("[Escrow Release Error] No Escrow released")
        return

    # Check central wallet balance and verify the wallet
    balance = await check_central_wallet_balance(central_wallet, client)
    print(f"central_wallet balance:{balance}, Released amount{released_sum}")
    if balance < released_sum:
        print("[Escrow Release Error] Central wallet balance not enough.")
        return
    # Calculate total amount to be distributed
    distibute_amount = released_sum // len(affected_users) 

    # Register tasks to be done
    print(f"[Distribution Process Start] Starting distribution of {distibute_amount} XRP each to {len(affected_users)} users.")
    results = []
    for user in affected_users:
        result = await send_xrp_to_user(
            central_wallet=central_wallet,
            receiver_address=user["wallet_address"],
            amount=str(distibute_amount),
            user_id=user["user_id"],
            client=client,
            db=db
        )
        results.append(result)

    # Calculate total successful distributions
    successful_count = sum(1 for result in results if result is True)
    print(f"[Distribution Process Complete] Number of users successfully distributed: {successful_count}/{len(affected_users)}")

async def check_central_wallet_balance(central_wallet, client):
    """
    Check central balance
    """
    try:
        central_wallet_address = central_wallet.classic_address
        balance = await get_balance(central_wallet_address, client)
        if balance is None or int(balance) == 0:
            raise HTTPException(
                status_code=500,
                detail="Central wallet balance is zero or could not be retrieved."
            )
        return balance
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check central wallet balance: {str(e)}"
        )

@router.post("/distribute")
async def distribute_fund(
    request: DistributeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create wallet object and client from seed
    central_wallet_seed = os.getenv('CENTRAL_WALLET_SEED')
    if not central_wallet_seed:
        raise HTTPException(
            status_code=500,
            detail="CENTRAL_WALLET_SEED environment variable is not set"
        )
    try:
        central_wallet = Wallet.from_seed(central_wallet_seed)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid CENTRAL_WALLET_SEED format: {str(e)}"
        )
    client = AsyncJsonRpcClient(os.getenv('TESTNET_URL'))

    # Get all users in the disaster area
    affected_users = get_users_by_area(db, request.disaster_area)
    if not affected_users:
        raise HTTPException(
            status_code=404,
            detail="No users found in the specified disaster area"
        )
    
    summary = db.query(DonationSummary).filter(DonationSummary.id == 1).first()
    if not summary:
        raise HTTPException(status_code=500, detail="Donation summary record does not exist.")
    pool_balance = summary.total
    print(f"[Distribution Request] disaster_area={request.disaster_area}, number of users={len(affected_users)}, amount per user={pool_balance}")
    
    # Start the distribution process in the background
    background_tasks.add_task(
        process_distribution,
        central_wallet,
        affected_users,
        client,
        db
    )
    
    return {
        "message": "Distribution process started",
        "affected_users_count": len(affected_users),
        "area": request.disaster_area,
        "estimated_total": pool_balance
    }

@router.get("/pool-balance")
async def get_pool_balance():
    central_wallet_seed = os.getenv('CENTRAL_WALLET_SEED')
    if not central_wallet_seed:
        raise HTTPException(
            status_code=500,
            detail="CENTRAL_WALLET_SEED environment variable is not set"
        )
    try:
        central_wallet = Wallet.from_seed(central_wallet_seed)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid CENTRAL_WALLET_SEED format: {str(e)}"
        )
    client = AsyncJsonRpcClient(os.getenv('TESTNET_URL'))
    try:
        balance = await check_central_wallet_balance(central_wallet, client)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check central wallet balance: {str(e)}")
    return {"pool_balance": balance}