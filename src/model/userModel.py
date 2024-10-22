# Referencia: https://fastapi.tiangolo.com/tutorial/sql-databases/#create-the-database-models

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from  database.database import Base

class User(Base):
  __tablename__ = "users"
  __table_args__ = {'extend_existing': True}

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, nullable=False)
  connection = Column(String, nullable=False)
  role = Column(String, default="USER")
  email = Column(String, unique=True, index=True, nullable=False)
  password = Column(String, nullable=True)
  is_active = Column(Boolean, default=False)
  activation_code = Column(Integer, nullable=True)
  password_reset_code = Column(Integer, nullable=True)


