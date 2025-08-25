import asyncio
from sqlalchemy.orm import Session
from src.Config.Database.db import SessionLocal
from src.Models.empresasModel import Empresa
from src.Utils.cnpj import buscarInformacoesApi

def obterCadastrarEmpresa(session: Session, cnpj: str) -> dict:
    empresa_existente = session.query(Empresa).filter_by(cnpj=cnpj).first()
    if empresa_existente:
        return {
            "status": "erro",
            "mensagem": "Empresa com esse CNPJ já está cadastrada.",
            "empresa_id": empresa_existente.id,
            "razao_social": empresa_existente.razao_social
        }

    razao_social, *_ = asyncio.run(buscarInformacoesApi(cnpj))

    if not razao_social:
        return {"status": "erro", "mensagem": "Não foi possível consultar a razão social via API."}

    nova_empresa = Empresa(cnpj=cnpj, razao_social=razao_social)
    session.add(nova_empresa)
    session.commit()

    return {
        "status": "ok",
        "empresa_id": nova_empresa.id,
        "razao_social": nova_empresa.razao_social
    }

def listarEmpresas():
    with SessionLocal() as db:
        empresas = db.query(Empresa).all()
        return [{"id": e.id, "razao_social": e.razao_social} for e in empresas]