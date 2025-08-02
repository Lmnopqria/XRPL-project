from sqlalchemy import Column, Integer, BigInteger, String, Enum, ForeignKey
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class TransactionStatus(str, enum.Enum):
    SUCCESS = "Success"
    FAILED = "Failed"

class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    from_wallet_address = Column(String(255), nullable=False)
    to_wallet_address = Column(String(255), nullable=False)
    tx_hash = Column(String(100), nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(Enum(TransactionStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<TransactionRecord(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"