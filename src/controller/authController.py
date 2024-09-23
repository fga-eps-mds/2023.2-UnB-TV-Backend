import os
import re 
from typing import List
from fastapi import APIRouter, HTTPException, Response, status, Depends
from  utils import security, enumeration, send_mail
from  database.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from  constants import errorMessages
from starlette.responses import JSONResponse
from utils import security, enumeration

from  domain import userSchema, authSchema
from  repository import userRepository

auth = APIRouter(
  prefix="/auth"
)

  # Retorna conexões disponíveis 
@auth.get("/vinculo", response_model=authSchema.Connections)
def get_connection():
    connections = [member.value for member in enumeration.UserConnection]
    return JSONResponse(status_code=200, content=connections)

@auth.post('/register')
async def register(data: authSchema.UserCreate, db: Session = Depends(get_db)):
  # Verifica se connection é valido
  if (not enumeration.UserConnection.has_value(data.connection)):
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_CONNECTION)

  # Validação de senha
  is_valid = security.validate_password(data.password.strip()) 
  if (not is_valid):
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_PASSWORD)

  # Verifica se já existe um usuário com o email informado
  user = userRepository.get_user_by_email(db, data.email)
  if user:
    raise HTTPException(status_code=400, detail=errorMessages.EMAIL_ALREADY_REGISTERED)
  
  hashed_password = security.get_password_hash(data.password)
  
  activation_code = security.generate_six_digit_number_code()

  userRepository.create_user(db, name=data.name, connection=data.connection, email=data.email, password=hashed_password, activation_code=activation_code)
  
  if re.search(r"unb", data.email):
    await send_mail.send_verification_code(email=data.email, code=activation_code, is_unb=True)
  else:
    await send_mail.send_verification_code(email=data.email, code=activation_code)

  return JSONResponse(status_code=201, content={ "status": "success" })

  # Recebe os dados de login
@auth.post("/login", response_model=authSchema.Token)
async def login(data: authSchema.UserLogin, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  
  password_match = security.verify_password(data.password, user.password)
  if not password_match:
    raise HTTPException(status_code=404, detail=errorMessages.PASSWORD_NO_MATCH)

  if not user.is_active:
    raise HTTPException(status_code=401, detail=errorMessages.ACCOUNT_IS_NOT_ACTIVE)
  
  access_token = security.create_access_token(data={ "id": user.id, "email": user.email, "role": user.role })
  refresh_token = security.create_refresh_token(data={ "id": user.id })

  return JSONResponse(status_code=200, content={ "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer" })

  # Recebe os dados do usuário provenientes de uma autenticação social
@auth.post("/login/social")
async def login_social(user: authSchema.UserSocial, db: Session = Depends(get_db)):
  existing_user = userRepository.get_user_by_email(db, user.email)
  
  if existing_user is None:
    new_user = userRepository.create_user_social(db, user.name, user.email)
    user_id = new_user.id
    is_new_user = True
  else:
    user_id = existing_user.id
    is_new_user = False

  access_token = security.create_access_token(data={"id": user_id, "email": user.email, "role": "user"})
  refresh_token = security.create_refresh_token(data={"id": user_id})

  return JSONResponse(status_code=200, content={
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer",
    "is_new_user": is_new_user,
    "user_id": user_id
  })

  # trata da renovação de tokens de acesso      
@auth.post("/refresh", response_model=authSchema.RefreshTokenResponse)
def refresh_token(token: dict = Depends(security.verify_token)):
  access_token=security.create_access_token(token)
  return JSONResponse(status_code=200, content={ "access_token": access_token, "token_type": "bearer" })

@auth.post('/resend-code')
async def send_new_code(data: authSchema.SendNewCode, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

  if user.is_active:
    return JSONResponse(status_code=400, content={ "status": "error", "message": errorMessages.ACCOUNT_ALREADY_ACTIVE })

  return JSONResponse(status_code=201, content={ "status": "success" })

  # Recebe dados de validação de conta
@auth.patch('/activate-account')
async def validate_account(data: authSchema.AccountValidation, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

  if user.is_active:
    return JSONResponse(status_code=200, content={ "status": "error", "message": errorMessages.ACCOUNT_ALREADY_ACTIVE })
  
  if user.activation_code != data.code:
    raise HTTPException(status_code=404, detail=errorMessages.INVALID_CODE)

  userRepository.activate_account(db, user)
  return JSONResponse(status_code=200, content={ "status": "success" })

 # cadastro da senha de admin / role do admin
@auth.post('/admin-setup')
async def admin_setup(data: authSchema.AdminSetup, db: Session = Depends(get_db), token: dict = Depends(security.verify_token_admin)):
    user = userRepository.get_user_by_email(db, data.email)
    if not user:
      raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

    if not user.is_active:
      raise HTTPException(status_code=400, detail="Account is not active")

    if not re.search(r"unb", data.email):
      raise HTTPException(status_code=400, detail="Account is not @unb")
    
    userRepository.update_user_role(db, user, "COADMIN")

    return JSONResponse(status_code=200, content={"status": "success"})

@auth.post('/super-admin-setup')
async def super_admin_setup(data: authSchema.AdminSetup, db: Session = Depends(get_db), token: dict = Depends(security.verify_token_admin)):
    user = userRepository.get_user_by_email(db, data.email)
    if not user:
      raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

    if not user.is_active:
      raise HTTPException(status_code=400, detail="Account is not active")

    if not re.search(r"unb", data.email):
      raise HTTPException(status_code=400, detail="Account is not @unb")
    
    userRepository.update_user_role(db, user, "ADMIN")

    return JSONResponse(status_code=200, content={"status": "success"})

@auth.post('/reset-password/request')
async def request_password_(data: authSchema.ResetPasswordRequest, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

  if not user.is_active:
    raise HTTPException(status_code=404, detail=errorMessages.ACCOUNT_IS_NOT_ACTIVE)
  
  code = security.generate_six_digit_number_code()

  userRepository.set_user_reset_pass_code(db, user, code)
  await send_mail.send_reset_password_code(data.email, code)
  return JSONResponse(status_code=200, content={ "status": "success" })

@auth.post('/reset-password/verify')
async def verify_reset_code(data: authSchema.ResetPasswordVerify, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  
  if not user.password_reset_code:
    raise HTTPException(status_code=404, detail=errorMessages.NO_RESET_PASSWORD_CODE)

  if user.password_reset_code != data.code:
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_RESET_PASSWORD_CODE)

  return JSONResponse(status_code=200, content={ "status": "success" })

  # Atualizar senha de um usuário após uma solicitação de redefinição
@auth.patch('/reset-password/change', response_model=userSchema.User)
async def update_user_password(data: authSchema.ResetPasswordUpdate, db: Session = Depends(get_db)):
  user = userRepository.get_user_by_email(db, data.email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  
  # Valida a senha informada
  if data.password and not security.validate_password(data.password):
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_PASSWORD)

  # Verifica se o usuario possui um reset code. Se não possuir, a solicitação é invalida e deve ser bloqueada
  if not user.password_reset_code:
    raise HTTPException(status_code=401, detail=errorMessages.INVALID_REQUEST)
  
  # Verifica se o código corresponde
  if data.code != user.password_reset_code:
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_RESET_PASSWORD_CODE)
    
  # Faz procedimento de hash da senha e atualiza usuario
  hashed_password = security.get_password_hash(data.password)
  updated_user = userRepository.update_password(db, user, hashed_password)

  return updated_user
