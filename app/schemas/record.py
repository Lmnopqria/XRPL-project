from pydantic import BaseModel
from datetime import datetime
from app.models.record import TransactionType

class RecordBase(BaseModel):
    user_id: int
    amount: int
    type: TransactionType

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    record_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 