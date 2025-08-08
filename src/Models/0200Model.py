from sqlalchemy import Column, Integer, String
from Config.Database.db import Base

class Registro0200(Base):
    __tablename__ = "0200"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    reg = Column(String(10))
    cod_item = Column(String(60))
    descr_item = Column(String(255))
    cod_barra = Column(String(60))
    cod_ant_item = Column(String(60))
    unid_inv = Column(String(10))
    tipo_item = Column(String(10))
    cod_ncm = Column(String(20))
    ex_ipi = Column(String(10))
    cod_gen = Column(String(10))
    cod_list = Column(String(10))
    aliq_icms = Column(String(10))
    cest = Column(String(10))
    periodo = Column(String(10))
