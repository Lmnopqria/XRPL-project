from sqlalchemy import Column, Integer, BigInteger, String, Enum, ForeignKey
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class EscrowStatus(str, enum.Enum):
    REGISTERED = "Registered"
    PROCESSING = "Processing"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

class EscrowRecord(Base):
    __tablename__ = "escrow_records"

    escrow_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    from_wallet_address = Column(String(255), nullable=False)
    tx_sequence = Column(String(100), nullable=False)
    secret_key = Column(String(200), nullable=False)
    cancel_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(Enum(EscrowStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EscrowRecord(escrow_id={self.escrow_id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>" 