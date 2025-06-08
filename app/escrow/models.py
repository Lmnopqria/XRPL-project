# app/escrow/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class DisasterType(str, Enum):
    """Supported disaster types"""
    FLOOD = "flood"
    DROUGHT = "drought"
    CYCLONE = "cyclone"

class EscrowStatus(str, Enum):
    """Escrow lifecycle states"""
    CREATED = "created"
    PENDING = "pending"
    RELEASED = "released"
    CANCELLED = "cancelled"
    FAILED = "failed"

class DisasterParams(BaseModel):
    """Parameters for disaster-specific escrow"""
    disaster_type: DisasterType
    region: str
    threshold: float
    threshold_unit: str  # e.g., "mm", "days", "kmph"

class CreateEscrowRequest(BaseModel):
    """Request model for creating an escrow"""
    donor_address: str
    amount_drops: str  # Amount in drops (1 XRP = 1,000,000 drops)
    disaster_params: DisasterParams

class EscrowRecord(BaseModel):
    """Complete escrow record"""
    escrow_id: str  # Format: "address:sequence"
    donor_address: str
    amount_drops: str
    destination: str
    condition: str
    fulfillment_key: str
    disaster_params: DisasterParams
    status: EscrowStatus
    created_at: datetime
    finish_after: datetime
    cancel_after: datetime
    tx_hash: Optional[str] = None
    release_tx_hash: Optional[str] = None
    error_message: Optional[str] = None

class EscrowResponse(BaseModel):
    """Response after escrow creation"""
    success: bool
    escrow_id: Optional[str] = None
    tx_hash: Optional[str] = None
    condition: Optional[str] = None
    error: Optional[str] = None
    
class BulkReleaseResponse(BaseModel):
    """Response after releasing multiple escrows"""
    total_escrows: int
    successful_releases: int
    failed_releases: int
    total_amount_released: str
    errors: list[dict] = []