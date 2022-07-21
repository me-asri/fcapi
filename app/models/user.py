from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmailIn(BaseModel):
    email: EmailStr = Field(..., example='info@example.com')


class TokenIn(BaseModel):
    token: str = Field(..., example='token')


class LoginInfo(BaseModel):
    email: EmailStr = Field(..., example='info@example.com')
    password: str = Field(..., example='password')


class PassIn(BaseModel):
    password: str = Field(..., example='password')


class UserBase(BaseModel):
    email: EmailStr = Field(..., example='info@example.com')


class UserIn(UserBase):
    password: str = Field(..., example='password')


class UserOut(UserBase):
    id: int = Field(..., example=1)
    active: bool = Field(..., example=True)
    premium: bool = Field(..., example=False)

    class Config:
        orm_mode = True


class UserDb(UserOut):
    hashed_password: str


class UserUpdate(BaseModel):
    current_password: Optional[str] = Field(None, example='password')
    new_password: Optional[str] = Field(None, example='password')
