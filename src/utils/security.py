import os, secrets
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from  constants import errorMessages 

SECRET_KEY = os.getenv("SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", default=7)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password) -> bool:
  return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password) -> str:
  return pwd_context.hash(password)

def validate_password(password: str) -> bool:
  return (len(password) == 6 and not any(not ch.isdigit() for ch in password))

def create_access_token(data: dict):
  access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))

  to_encode = data.copy()
  expire = datetime.now(timezone.utc) + access_token_expires
  
  to_encode.update({ "exp": expire, **data })
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # print(payload["role"])
    return payload
  except JWTError:
    raise HTTPException(status_code=401, detail=errorMessages.INVALID_TOKEN)
  
def verify_token_admin(token: str = Depends(oauth2_scheme)):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload["role"] == "ADMIN":
      return payload
    else:
      raise HTTPException(status_code=401, detail=errorMessages.INVALID_TOKEN)
  except JWTError:
    raise HTTPException(status_code=401, detail=errorMessages.INVALID_TOKEN)

def generate_six_digit_number_code():
  return secrets.randbelow(900000) + 100000

def create_refresh_token(data:dict):
  access_token_expires = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))

  to_encode = data.copy()
  if access_token_expires:
    expire = datetime.now(timezone.utc) + access_token_expires

  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt