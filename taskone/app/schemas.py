# app/schemas.py

from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class VerifyOtpRequest(BaseModel):
    email: str
    email_otp: str
    sms_otp: str



class LoginRequest(BaseModel):
    email: EmailStr
    password: str
