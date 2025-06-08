from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import xrpl
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
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.asyncio.clients import AsyncJsonRpcClient

class DistributeRequest(BaseModel):
    disaster_area: str

router = APIRouter()
load_dotenv()

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
        amount=float(amount),
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
        user.balance += float(amount)
        db.commit()

async def send_xrp_to_user(
    central_wallet: xrpl.wallet.Wallet,
    receiver_address: str,
    amount: str,
    user_id: str,
    client: AsyncJsonRpcClient,
    db: Session
):
    """
    Send XRP from central wallet to a user and record the transaction
    
    Args:
        central_wallet: Central wallet to send XRP from
        receiver_address: User's wallet address to receive XRP
        amount: Amount of XRP to send
        user_id: Receiver's user ID
        client: XRPL client instance
        db: Database session
    """
    try:
        # Send XRP
        payment_tx = xrpl.models.Payment(
            account=central_wallet.address,
            amount=amount,
            destination=receiver_address,
        )
        await submit_and_wait(payment_tx, client, central_wallet)
        
        # Update user's balance and record the transaction
        update_user_balance(db, user_id, amount)
        create_transaction_record(db, user_id, amount)
        
        return True
    except Exception as e:
        print(f"Error sending XRP to user {user_id}: {str(e)}")
        return False

async def process_distribution(
    central_wallet: xrpl.wallet.Wallet,
    affected_users: List[Dict[str, str]],
    amount: str,
    client: AsyncJsonRpcClient,
    db: Session
) -> float:
    """Process XRP distribution to all affected users"""
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
    return float(amount) * successful_count

@router.post("/distribute")
async def distribute_fund(
    request: DistributeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    central_wallet_seed = os.getenv('CENTRAL_WALLET_SEED')
    if not central_wallet_seed:
        raise HTTPException(
            status_code=500,
            detail="CENTRAL_WALLET_SEED environment variable is not set"
        )
    
    try:
        central_wallet = xrpl.wallet.Wallet.from_seed(central_wallet_seed)
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
    
    # Calculate total amount to be distributed
    amount = "10" # temporary amount
    total_distribution = float(amount) * len(affected_users)
    
    # Check if we have enough funds
    summary = db.query(DonationSummary).filter(DonationSummary.id == 1).first()
    if not summary or summary.total < total_distribution:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds in donation pool"
        )
    
    # Start the distribution process in the background
    background_tasks.add_task(
        process_distribution,
        central_wallet,
        affected_users,
        amount,
        client,
        db
    )
    
    return {
        "message": "Distribution process started",
        "affected_users_count": len(affected_users),
        "area": request.disaster_area,
        "estimated_total": total_distribution
    }

# import asyncio
# from xrpl.asyncio.transaction import sign, submit_and_wait
# from xrpl.asyncio.ledger import get_latest_validated_ledger_sequence
# from xrpl.asyncio.account import get_next_valid_seq_number
# from xrpl.asyncio.clients import AsyncJsonRpcClient
# async_client = AsyncJsonRpcClient(JSON_RPC_URL)
# async def submit_sample_transaction():
#     current_validated_ledger = await get_latest_validated_ledger_sequence(async_client)

#     # prepare the transaction
#     # the amount is expressed in drops, not XRP
#     # see https://xrpl.org/basic-data-types.html#specifying-currency-amounts
#     my_tx_payment = Payment(
#         account=test_wallet.address,
#         amount="2200000",
#         destination="rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe",
#         last_ledger_sequence=current_validated_ledger + 20,
#         sequence=await get_next_valid_seq_number(test_wallet.address, async_client),
#         fee="10",
#     )
#     # sign and submit the transaction
#     tx_response = await submit_and_wait(my_tx_payment_signed, async_client, test_wallet)

# asyncio.run(submit_sample_transaction())
