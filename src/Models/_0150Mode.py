from sqlalchemy import Column, Integer, String, Boolean
from src.Config.Database.db import Base

class Registro0150(Base):
    __tablename__ = "0150"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    reg = Column(String(10))
    cod_part = Column(String(60))
    nome = Column(String(100))
    cod_pais = Column(String(10))
    cnpj = Column(String(20))
    cpf = Column(String(20))
    ie = Column(String(20))
    cod_mun = Column(String(20))
    suframa = Column(String(20))
    ende = Column(String(100))
    num = Column(String(20))
    compl = Column(String(20))
    bairro = Column(String(50))
    cod_uf = Column(String(10))
    uf = Column(String(5))
    pj_pf = Column(String(5))
    periodo = Column(String(10))
    batch_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)