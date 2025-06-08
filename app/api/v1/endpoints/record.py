from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
from app.models.record import Record, TransactionType
from app.models.donation_summary import DonationSummary
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class RecordResponse(BaseModel):
    record_id: int
    amount: float
    type: TransactionType
    created_at: datetime

    class Config:
        from_attributes = True

class TotalResponse(BaseModel):
    total_pool: float

@router.get("/me", response_model=List[RecordResponse])
def get_my_records(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all transaction records for the current user
    """
    records = db.query(Record).filter(
        Record.user_id == current_user.user_id
    ).order_by(Record.created_at.desc()).all()
    
    return records

@router.get("/total", response_model=TotalResponse)
def get_total_statistics(db: Session = Depends(get_db)):
    """
    Get current total amount in donation pool
    """
    donation_pool = db.query(DonationSummary).filter(
        DonationSummary.id == 1
    ).first()
    current_pool = donation_pool.total if donation_pool else 0.0
    
    return TotalResponse(total_pool=current_pool) 