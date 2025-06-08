from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
import enum
from app.core.database import Base

class TransactionType(str, enum.Enum):
    RECEIVED = "received"
    REFUNDED = "refunded"
    DONATED = "donated"

class Record(Base):
    __tablename__ = "records"
    
    record_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Record(record_id={self.record_id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>" 