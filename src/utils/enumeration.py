from enum import Enum

class UserConnection(Enum):
  ESTUDANTE = "ESTUDANTE"
  PROFESSOR = "PROFESSOR"
  SERVIDOR = "SERVIDOR"
  TERCEIRIZADO = "TERCEIRIZADO"
  ESTAGIARIO = "ESTAGIARIO"
  COMUNIDADE_EXTERNA = "COMUNIDADE EXTERNA"

  @classmethod
  def has_value(cls, value):
    return value in cls._value2member_map_
  
class UserRole(Enum):
  ADMIN = "ADMIN"
  USER = "USER"
  COADMIN = "COADMIN"