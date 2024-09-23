from typing import Optional
from pydantic import BaseModel, ConfigDict
from fastapi_filter import FilterDepends, with_prefix
from sqlalchemy import or_
from fastapi_filter.contrib.sqlalchemy import Filter
from  model import userModel

class UserUpdate(BaseModel):
  name: str = None
  email: str = None
  connection: str = None

class User(BaseModel):
  model_config = ConfigDict(from_attributes = True)
  id: int
  name: str
  connection: str
  email: str
  role: str
  is_active: bool

class UserListFilter(Filter):
  name: Optional[str] = None
  name__like: Optional[str] = None
  email: Optional[str] = None
  email__like: Optional[str] = None
  connection: Optional[str] = None
  name_or_email: Optional[str] = None
  offset: Optional[int] = 0
  limit: Optional[int] = 100

class Constants(Filter.Constants):
  model = userModel.User
  search_model_fields = ["name", "email"]

class RoleUpdate(BaseModel):
  role: str  