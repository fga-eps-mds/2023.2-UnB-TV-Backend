from typing import List
from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
  email: str
  password: str

class UserCreate(BaseModel):
  name: str
  connection: str
  email: str
  password: str

class UserSocial(BaseModel):
  name: str
  email:str

class Token(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str
  
class RefreshTokenResponse(BaseModel):
  access_token: str
  token_type: str

class SendNewCode(BaseModel):
  email: str

class AccountValidation(BaseModel):
  email: str
  code: int

class ResetPasswordRequest(BaseModel):
  email: str

class ResetPasswordVerify(BaseModel):
  email: str
  code: int

class ResetPasswordUpdate(BaseModel):
  email: str
  password: str
  code: int

class Connections(BaseModel):
  vinculos: List[str]

class AdminSetup(BaseModel):
  email: EmailStr