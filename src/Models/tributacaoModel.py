from sqlalchemy import Column, Integer, String
from src.Config.Database.db import Base

class CadastroTributacao(Base):
    __tablename__ = "cadastro_tributacao"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    codigo = Column(String(60))
    produto = Column(String(255))
    ncm = Column(String(20))
    aliquota = Column(String(10))
    categoriaFiscal = Column(String(40))