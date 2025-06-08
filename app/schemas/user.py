from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    address: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    user_id: int
    balance: float
    wallet_address: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str 