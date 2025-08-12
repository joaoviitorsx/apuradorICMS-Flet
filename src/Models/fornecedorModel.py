from sqlalchemy import Column, Integer, String
from src.Config.Database.db import Base

class CadastroFornecedor(Base):
    __tablename__ = "cadastro_fornecedores"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, index=True)
    cod_part = Column(String(60))
    nome = Column(String(100))
    cnpj = Column(String(20))
    uf = Column(String(5))
    cnae = Column(String(20))
    decreto = Column(String(10))
    simples = Column(String(10))