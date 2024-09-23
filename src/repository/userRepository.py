# Referencia: https://fastapi.tiangolo.com/tutorial/sql-databases/#crud-utils
from sqlalchemy import or_
from sqlalchemy.orm import Session

from  domain import userSchema
from  model import userModel

# Obtem usuario a partir do seu ID
def get_user(db: Session, user_id: int):
  return db.query(userModel.User).filter(userModel.User.id == user_id).first()

# Obtem usuario a partir do Email
def get_user_by_email(db: Session, email: str):
  return db.query(userModel.User).filter(userModel.User.email == email).first()

'''
Obtem lista de usuarios. Possui filtragem:
Filtros:
name: filtrar por nome do usuario
email: filtrar por email do usuario
name_or_email: filtragem que aceita tanto nome quanto email (OR)
connection: filtragem pelo vinculo do usuario

Também aceita offset e limit. Para offset pula a quantidade informada, 
para o limit, controla a quantidade de usuarios retornada 
'''
def get_users(db: Session, users_filter: userSchema.UserListFilter):
  query = db.query(userModel.User)

  if (users_filter.name):
    query = query.filter(userModel.User.name == users_filter.name)
  elif (users_filter.email):
    query = query.filter(userModel.User.email == users_filter.email)
  elif (users_filter.name_or_email):
    query = query.filter(or_(userModel.User.name.ilike(f'%{users_filter.name_or_email}%'), userModel.User.email.ilike(f'%{users_filter.name_or_email}%')))

  if (users_filter.connection):
    query = query.filter(userModel.User.connection == users_filter.connection)

  # Realiza o count para retornar para o front para realizar paginação
  total_count = query.count()
  # Ordena a lista de usuarios por ordem alfabetica pelo nome
  query = query.order_by(userModel.User.name.asc())

  # Realiza a delimitação por offset
  if (users_filter.offset):
    query = query.offset(users_filter.offset)

  # Realiza a limitação por quantidade retornada
  if (users_filter.limit):
    query = query.limit(users_filter.limit)

  # Retorna todos os usuarios filtrados, dentro de eventuais limitações (offset ou limit) e o total (geral)
  return { "users": query.all(), "total": total_count }

def create_user(db: Session, name, connection, email, password, activation_code):
  db_user = userModel.User(name=name, connection=connection, email=email, password=password, activation_code=activation_code,)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

# Cria um usuario por login social. Essa criação é especial pois o usuario criado por rede social não possui SENHA
def create_user_social(db: Session, name, email):
  db_user = userModel.User(
  name=name,
  connection="ESTUDANTE",
  role="USER",
  email=email,
  is_active=True,)

  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def update_user(db: Session, db_user: userSchema.User, user: userSchema.UserUpdate):
  user_data = user.dict(exclude_unset=True)
  for key, value in user_data.items():
    setattr(db_user, key, value)

  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def update_user_role(db: Session, db_user: userSchema.User, role: str):
  db_user.role = role

  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def update_password(db: Session, db_user: userSchema.User, new_password: str):
  db_user.password = new_password
  db_user.password_reset_code = None

  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def activate_account(db: Session, db_user: userSchema.User):
  db_user.is_active = True
  db_user.activation_code = None
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def set_user_reset_pass_code(db: Session, db_user: userSchema.User, code: int):
  db_user.password_reset_code = code
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def delete_user(db: Session, db_user: userSchema.User):
  db.delete(db_user)
  db.commit()