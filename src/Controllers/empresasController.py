from sqlalchemy.exc import SQLAlchemyError
from src.Services.empresaService import obter_ou_cadastrar_empresa_por_cnpj, listar_empresas
from src.Config.Database.db import SessionLocal

def cadastrar_empresa(cnpj: str) -> dict:
    session = SessionLocal()
    try:
        return obter_ou_cadastrar_empresa_por_cnpj(session, cnpj)
    except SQLAlchemyError as e:
        session.rollback()
        return {"status": "erro", "mensagem": str(e)}
    finally:
        session.close()

def obter_lista_empresas():
    try:
        return listar_empresas()
    except Exception as e:
        print(f"[Erro] Falha ao listar empresas: {e}")
        return []