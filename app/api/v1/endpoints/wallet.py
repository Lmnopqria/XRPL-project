from fastapi import APIRouter, Depends, HTTPException
import xrpl
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
import httpx
from app.core.security import get_current_active_user
from app.models.record import Record, TransactionType
from app.models.donation_summary import DonationSummary
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()
load_dotenv()

TESTNET_URL = os.getenv('TESTNET_URL', 'https://s.altnet.rippletest.net:51234/')
# Get Fernet key for decryption
FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

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
            detail="Failed to create wallet: " + str(e)
        )

@router.get("/balance")
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
    amount: float

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be higher than 0")
        if not isinstance(v, (int, float)):
            raise ValueError("Amount must be a number")
        return float(v)

@router.post("/donate")
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
    
    # Update donation summary
    summary = db.query(DonationSummary).filter(DonationSummary.id == 1).first()
    if not summary:
        summary = DonationSummary(id=1, total=request.amount)
        db.add(summary)
    else:
        summary.total += request.amount
    
    # Record the donation
    record = Record(
        user_id=current_user.user_id,
        amount=request.amount,
        type=TransactionType.DONATED.value
    )
    db.add(record)
    db.commit()
    
    return {
        "message": "Donation successful",
        "amount": request.amount,
        "remaining_balance": current_user.balance,
        "total_donations": summary.total
    }

    # wallet = get_user_wallet(current_user)
    # return {wallet}