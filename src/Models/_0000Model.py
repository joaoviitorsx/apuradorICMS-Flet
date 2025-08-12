from sqlalchemy import Column, Integer, String, Boolean
from src.Config.Database.db import Base

class Registro0000(Base):
    __tablename__ = "0000"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    reg = Column(String(10))
    cod_ver = Column(String(10))
    cod_fin = Column(String(10))
    dt_ini = Column(String(10))
    dt_fin = Column(String(10))
    nome = Column(String(100))
    cnpj = Column(String(20))
    cpf = Column(String(20))
    uf = Column(String(5))
    ie = Column(String(20))
    cod_num = Column(String(20))
    im = Column(String(20))
    suframa = Column(String(20))
    ind_perfil = Column(String(10))
    ind_ativ = Column(String(10))
    filial = Column(String(10))
    periodo = Column(String(10))
    batch_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)