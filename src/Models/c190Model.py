from sqlalchemy import Column, Integer, String, Boolean
from src.Config.Database.db import Base

class Registroc190(Base):
    __tablename__ = "c190"

    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, index=True, nullable=False)
    id_c100 = Column(Integer, index=True)
    periodo = Column(String(10))
    reg = Column(String(10))
    cst_icms = Column(String(10))
    cfop = Column(String(60))
    aliq_icms = Column(String(255))
    vl_opr = Column(String(20))
    vl_bc_icms = Column(String(20))
    vl_icms = Column(String(20))
    vl_bc_icms_st = Column(String(20))
    vl_icms_st = Column(String(20))
    vl_red_bc = Column(String(20))
    cod_obs = Column(String(10))
    batch_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)