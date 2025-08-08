from sqlalchemy import Column, Integer, String
from Config.Database.db import Base

class C170Clone(Base):
    __tablename__ = "c170_clone"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    periodo = Column(String(10))
    reg = Column(String(10))
    num_item = Column(String(10))
    cod_item = Column(String(60))
    descr_compl = Column(String(255))
    qtd = Column(String(20))
    unid = Column(String(10))
    vl_item = Column(String(20))
    vl_desc = Column(String(20))
    cfop = Column(String(10))
    cst = Column(String(3))
    ncm = Column(String(40))
    id_c100 = Column(Integer)
    filial = Column(String(10))
    ind_oper = Column(String(5))
    cod_part = Column(String(60))
    num_doc = Column(String(20))
    chv_nfe = Column(String(60))
    aliquota = Column(String(10))
    resultado = Column(String(20))

class C170Nova(Base):
    __tablename__ = "c170nova"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    cod_item = Column(String(60))
    periodo = Column(String(10))
    reg = Column(String(10))
    num_item = Column(String(10))
    descr_compl = Column(String(255))
    cod_ncm = Column(String(40))
    qtd = Column(String(20))
    unid = Column(String(10))
    vl_item = Column(String(20))
    vl_desc = Column(String(20))
    cst = Column(String(10))
    cfop = Column(String(10))
    id_c100 = Column(String(10))
    filial = Column(String(10))
    ind_oper = Column(String(5))
    cod_part = Column(String(60))
    num_doc = Column(String(20))
    chv_nfe = Column(String(60))