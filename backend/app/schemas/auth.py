from pydantic import BaseModel, Field
try:
    import email_validator
    from pydantic import EmailStr
except Exception:
    EmailStr = str


from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user" # "user" or "admin"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
