from sqlalchemy import Column, Integer, String
from Config.Database.db import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(20), nullable=False)
    razao_social = Column(String(100), nullable=False)