from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import xrpl
import httpx
import os
from dotenv import load_dotenv

from app.core.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import User, UserCreate, UserLogin, Token
from app.core.security import (
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
load_dotenv()

TESTNET_URL = os.getenv('TESTNET_URL','https://s.altnet.rippletest.net:51234/')

# Settings for hasing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Create Fernet_Key for encrypting Seed
FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def encrypt_seed(seed: str) -> str:
    return fernet.encrypt(seed.encode()).decode()

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # Verify User
    user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify Password
    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check Duplication
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        # Create Wallet
        client = xrpl.clients.JsonRpcClient(TESTNET_URL)
        wallet = xrpl.wallet.generate_faucet_wallet(client)
        
        # Save new user
        db_user = UserModel(
            email=user.email,
            password=get_password_hash(user.password),
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            balance=10000000,
            wallet_address=wallet.address,
            seed=encrypt_seed(wallet.seed)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Return data without sensitive data
        return User(
            user_id=db_user.user_id,
            email=db_user.email,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            address=db_user.address,
            balance=db_user.balance,
            wallet_address=db_user.wallet_address
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            raise HTTPException(
                status_code=503,
                detail="XRPL Testnet Faucet service is temporarily unavailable. Please try again later."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create XRPL wallet: {str(e)}"
        )
    except httpx.ConnectTimeout:
        raise HTTPException(
            status_code=503,
            detail="Connection to XRPL Testnet timed out. Please try again later."
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to XRPL Testnet. Please try again later."
        )
    except Exception as e:
        # If any database operation fails, we need to rollback
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user 