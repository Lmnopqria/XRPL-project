from fastapi import APIRouter, Depends, HTTPException
import xrpl
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import httpx
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from app.core.security import get_current_active_user
from app.core.database import get_db
from app.models.user import User as UserModel
from app.models.record import Record, TransactionType
from app.models.donation_summary import DonationSummary
from app.models.escrow_record import EscrowRecord, EscrowStatus
from app.escrow.escrow_sample import make_escrow


router = APIRouter()
load_dotenv()

TESTNET_URL = os.getenv('TESTNET_URL', 'https://s.altnet.rippletest.net:51234/')
# Get Fernet key for decryption
FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

# To be used for future implementation (ex. Check balance with DB)
def get_user_wallet(user: UserModel) -> xrpl.wallet.Wallet:
    """
    Decrypt user's seed and create XRPL wallet
    
    Args:
        user (UserModel): Logged in user model instance
        
    Returns:
        xrpl.wallet.Wallet: XRPL wallet instance
    """
    try:
        # Decrypt the seed
        decrypted_seed = fernet.decrypt(user.seed.encode()).decode()
        # Create and return wallet
        return xrpl.wallet.Wallet.from_seed(decrypted_seed)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve wallet: " + str(e)
        )

@router.get(
    "/balance",
    responses={
        401: {"description": "Unauthorized"},
        503: {"description": "XRPL network is temporarily unavailable."},
        500: {"description": "Failed to get balance."}
    }
)
def get_balance(current_user: UserModel = Depends(get_current_active_user)):
    try:
        client = xrpl.clients.JsonRpcClient(TESTNET_URL)
        balance = xrpl.account.get_balance(current_user.wallet_address, client)
        return {"balance": balance}
    except (httpx.ConnectTimeout, httpx.ConnectError) as e:
        raise HTTPException(
            status_code=503,
            detail="XRPL network is temporarily unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get balance: " + str(e)
        )

class DonateRequest(BaseModel):
    amount: int
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be higher than 0")
        return int(v)

@router.post(
    "/donate",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Insufficient balance or invalid request"},
        500: {"description": "Failed to process donation"}
    }
)
def donate_fund(
    request: DonateRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Donate XRP to the central fund
    
    Args:
        request: Contains the amount to donate
        current_user: Currently authenticated user
        db: Database session
    """
    # Check if user has sufficient balance
    if current_user.balance < request.amount:
        raise HTTPException(
            status_code=400,
            detail="insufficient balance"
        )
    
    # Update user's balance
    current_user.balance -= request.amount
    db.add(current_user)
    
    # Update donation summary
    summary = db.query(DonationSummary).filter(DonationSummary.id == 1).first()
    if not summary:
        raise HTTPException(status_code=500, detail="Donation summary record does not exist.")
    else:
        summary.total += request.amount

    # Record the donation
    record = Record(
        user_id=current_user.user_id,
        amount=request.amount,
        type=TransactionType.DONATED.value
    )
    db.add(record)

    # Make Escorw
    CANCEL_AFTER_DAYS = int(os.getenv('CANCEL_AFTER_DAYS', 365))
    cancel_date = datetime.now() + timedelta(days=CANCEL_AFTER_DAYS)
    secret_key = secrets.token_urlsafe(32)
    try:
        tx_sequence = make_escrow(current_user.wallet_address, secret_key, request.amount, cancel_date)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

    # Record the escrow transaction
    encrypted_secret_key = fernet.encrypt(secret_key.encode()).decode()
    escrow_record = EscrowRecord(
        user_id=current_user.user_id,
        from_wallet_address=current_user.wallet_address,
        tx_sequence=tx_sequence,
        secret_key=encrypted_secret_key,
        cancel_date=cancel_date,
        amount=request.amount,
        status=EscrowStatus.REGISTERED
    )
    db.add(escrow_record)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail='failed to write db:' + str(e))

    return {
        "message": "Donation successful",
        "amount": request.amount,
        "remaining_balance": current_user.balance,
        "total_donations": summary.total
    }