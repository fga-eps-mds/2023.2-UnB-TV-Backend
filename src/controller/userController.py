from fastapi import APIRouter, HTTPException, Response, status, Depends, Header
from  database.database import get_db
from sqlalchemy.orm import Session

from constants import errorMessages
from domain import userSchema
from repository import userRepository
from utils import security, enumeration
from domain.userSchema import RoleUpdate

from fastapi_filter import FilterDepends

user = APIRouter(
  prefix="/users"
)

@user.get("/", response_model=list[userSchema.User])
def read_users(
  response: Response,
  users_filter: userSchema.UserListFilter = FilterDepends(userSchema.UserListFilter),
  db: Session = Depends(get_db), 
  _: dict = Depends(security.verify_token),
):
  result = userRepository.get_users(db, users_filter)

  users = result['users']
  total = result['total']

  response.headers['X-Total-Count'] = str(total)
  return users

@user.get("/{user_id}", response_model=userSchema.User)
async def read_user(user_id: int, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
  user = userRepository.get_user(db, user_id)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  return user

@user.get("/email/{user_email}", response_model=userSchema.User)
async def read_user_by_email(user_email: str, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
  user = userRepository.get_user_by_email(db, user_email)
  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  return user

@user.patch("/{user_id}", response_model=userSchema.User)
async def partial_update_user(user_id: int, data: userSchema.UserUpdate, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
  # Validação do valor de connection
  if data.connection and not enumeration.UserConnection.has_value(data.connection):
    raise HTTPException(status_code=400, detail=errorMessages.INVALID_CONNECTION)
    
  db_user = userRepository.get_user(db, user_id)
  if not db_user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

  if data.email and data.email != db_user.email:
    user = userRepository.get_user_by_email(db, data.email)
    if user: 
      raise HTTPException(status_code=404, detail=errorMessages.EMAIL_ALREADY_REGISTERED)

  updated_user = userRepository.update_user(db, db_user, data)
  return updated_user

@user.delete("/{user_id}", response_model=userSchema.User)
async def delete_user(user_id: int, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
  db_user = userRepository.get_user(db, user_id)
  if not db_user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

  userRepository.delete_user(db, db_user)
  return db_user

@user.patch("/role/{user_id}", response_model=userSchema.User)
def update_role(user_id: int, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
  # Obtem email do usuario a partir de token.
  # Verifica se o usuário é ADMIN
  user = userRepository.get_user_by_email(db, email=token['email'])
  if user.role != enumeration.UserRole.ADMIN.value:
    raise HTTPException(status_code=401, detail=errorMessages.NO_PERMISSION)

  # Verificar se o usuario existe
  user = userRepository.get_user(db, user_id)

  if not user:
    raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)
  
  # Obtem o valor da outra role e atribui a outra role para o usuario. Caso ele seja um USER => ADMIN, caso seja ADMIN => USER
  new_role = enumeration.UserRole.ADMIN.value if user.role == enumeration.UserRole.USER.value else enumeration.UserRole.USER.value
  user = userRepository.update_user_role(db, db_user=user, role=new_role)

  return user

@user.patch("/role/superAdmin/{user_id}", response_model=userSchema.User)
def update_role_superAdmin(user_id: int, role_update: RoleUpdate, db: Session = Depends(get_db), token: dict = Depends(security.verify_token)):
    # Obtem email do usuario a partir do token.
    # Verifica se o usuário é ADMIN
    requesting_user = userRepository.get_user_by_email(db, email=token['email'])
    if requesting_user.role != enumeration.UserRole.ADMIN.value:
        raise HTTPException(status_code=401, detail=errorMessages.NO_PERMISSION)

    # Verificar se o usuario a ser modificado existe
    user = userRepository.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=errorMessages.USER_NOT_FOUND)

    new_role = role_update.role
    # Verifica se a nova role é ADMIN ou COADMIN e se o email contém "unb"
    if new_role in [enumeration.UserRole.ADMIN.value, enumeration.UserRole.COADMIN.value]:
        if "unb" not in user.email:
            raise HTTPException(status_code=400, detail="Usuários com roles ADMIN ou COADMIN devem ter um email contendo 'unb'.")

    # Atualiza a role do usuário
    user = userRepository.update_user_role(db, db_user=user, role=new_role)

    return user