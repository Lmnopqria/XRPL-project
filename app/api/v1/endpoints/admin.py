from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User as UserModel
from app.models.record import Record, TransactionType
from app.models.donation_summary import DonationSummary
from typing import List, Dict
from pydantic import BaseModel

import asyncio
from xrpl.wallet import Wallet
from xrpl.asyncio.clients import AsyncJsonRpcClient
from xrpl.asyncio.account import get_balance
from app.core.xrpl_transaction import send_xrp_to_user

class DistributeRequest(BaseModel):
    disaster_area: str
    amount: str

router = APIRouter()
load_dotenv()

# DB related functions
def create_transaction_record(
    db: Session,
    user_id: str,
    amount: str,
    transaction_type: TransactionType = TransactionType.RECEIVED
):
    """
    Create a transaction record in the database
    
    Args:
        db: Database session
        user_id: User ID who received/sent XRP
        amount: Amount of XRP
        transaction_type: Type of transaction (default: RECEIVED)
    """
    record = Record(
        user_id=int(user_id),
        amount=int(amount),
        type=transaction_type.value  # Using Enum value
    )
    db.add(record)
    db.commit()

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

def update_user_balance(db: Session, user_id: str, amount: str):
    """
    Update user's balance in the database
    
    Args:
        db: Database session
        user_id: User ID whose balance needs to be updated
        amount: Amount to add to the balance
    """
    user = db.query(UserModel).filter(UserModel.user_id == int(user_id)).first()
    if user:
        user.balance += int(amount)
        db.commit()

# Background Function
async def process_distribution(
    central_wallet: Wallet,
    affected_users: List[Dict[str, str]],
    amount: str,
    client: AsyncJsonRpcClient,
    db: Session
):
    # Register tasks to be done
    print(f"[Distribution Process Start] Starting distribution of {amount} XRP each to {len(affected_users)} users.")
    tasks = []
    for user in affected_users:
        task = send_xrp_to_user(
            central_wallet=central_wallet,
            receiver_address=user["wallet_address"],
            amount=amount,
            user_id=user["user_id"],
            client=client,
            db=db
        )
        tasks.append(task)
    
    # Start all transfers concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
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

    # Check central wallet balance and verify the wallet
    balance = await check_central_wallet_balance(central_wallet, client)

    # Get all users in the disaster area
    affected_users = get_users_by_area(db, request.disaster_area)
    if not affected_users:
        raise HTTPException(
            status_code=404,
            detail="No users found in the specified disaster area"
        )
    
    if int(request.amoun) >= balance:
        raise HTTPException(
            status_code=400,
            detail="Amount Exceed the Balance"
        )
    # Calculate total amount to be distributed
    distibute_amount = int(request.amount) // len(affected_users) 

    print(f"[Distribution Request] disaster_area={request.disaster_area}, number of users={len(affected_users)}, amount per user={distibute_amount}")
    # Start the distribution process in the background
    background_tasks.add_task(
        process_distribution,
        central_wallet,
        affected_users,
        str(distibute_amount),
        client,
        db
    )
    
    return {
        "message": "Distribution process started",
        "affected_users_count": len(affected_users),
        "area": request.disaster_area,
        "estimated_total": request.amount
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