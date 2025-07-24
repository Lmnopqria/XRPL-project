from sqlalchemy import Column, Integer, String, BigInteger
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    balance = Column(BigInteger, default=0.0)
    wallet_address = Column(String(255), nullable=False)
    seed = Column(String(255), nullable=False) 