import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update

from src.Utils.cnpj import processarCnpjs
from src.Models._0150Model import Registro0150
from src.Models.fornecedorModel import CadastroFornecedor

LOTE = 50

class FornecedorRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def novosFornecedores(self, empresa_id: int):
        subq = select(CadastroFornecedor.cod_part).where(
            CadastroFornecedor.empresa_id == empresa_id
        ).subquery()

        query = select(
            Registro0150.cod_part,
            Registro0150.nome,
            Registro0150.cnpj
        ).where(
            Registro0150.empresa_id == empresa_id,
            Registro0150.cnpj.isnot(None),
            Registro0150.cnpj != '',
            ~Registro0150.cod_part.in_(select(subq.c.cod_part))
        )
        result = self.db.execute(query)
        return result.fetchall()

    def inserirFornecedores(self, empresa_id: int, fornecedores: list):
        inserts = [
            {
                "empresa_id": empresa_id,
                "cod_part": cod_part,
                "nome": nome,
                "cnpj": cnpj,
                "uf": '',
                "cnae": '',
                "decreto": '',
                "simples": ''
            }
            for cod_part, nome, cnpj in fornecedores
        ]
        if inserts:
            self.db.execute(insert(CadastroFornecedor), inserts)
            self.db.commit()
        return len(inserts)

    def cnpjsPendentes(self, empresa_id: int):
        query = select(CadastroFornecedor.cnpj).where(
            CadastroFornecedor.empresa_id == empresa_id,
            CadastroFornecedor.cnpj.isnot(None),
            CadastroFornecedor.cnpj != '',
            (
                (CadastroFornecedor.cnae == None) |
                (CadastroFornecedor.cnae == '') |
                (CadastroFornecedor.uf == None) |
                (CadastroFornecedor.uf == '') |
                (CadastroFornecedor.decreto == None) |
                (CadastroFornecedor.decreto == '') |
                (CadastroFornecedor.simples == None) |
                (CadastroFornecedor.simples == '')
            )
        )
        result = self.db.execute(query)
        return [row[0] for row in result.fetchall()]

    def atualizarFornecedores(self, empresa_id: int, resultados: dict, lote_cnpjs: list):
        for cnpj in lote_cnpjs:
            dados = resultados.get(cnpj)
            if not dados or all(x is None for x in dados):
                continue
            razao_social, cnae, uf, simples, decreto = dados
            stmt = (
                update(CadastroFornecedor)
                .where(
                    CadastroFornecedor.cnpj == cnpj,
                    CadastroFornecedor.empresa_id == empresa_id
                )
                .values(
                    cnae=cnae or '',
                    decreto=str(decreto),
                    uf=uf or '',
                    simples=str(simples) if simples is not None else ''
                )
            )
            self.db.execute(stmt)
        self.db.commit()

class FornecedorService:
    def __init__(self, repository: FornecedorRepository):
        self.repository = repository

    def processar(self, empresa_id: int):
        try:
            print("⏳ Buscando fornecedores novos para inserção...")
            novos = self.repository.novosFornecedores(empresa_id)
            print(f"Novos fornecedores encontrados: {len(novos)}")
            inseridos = self.repository.inserirFornecedores(empresa_id, novos)
            print(f"{inseridos} fornecedores inseridos.")

            print("🔍 Atualizando fornecedores com dados externos...")
            cnpjs = self.repository.cnpjsPendentes(empresa_id)
            print(f"CNPJs pendentes: {len(cnpjs)}")
            if not cnpjs:
                print("✅ Nenhum CNPJ pendente de atualização.")
                return

            print(f"🌐 Consultando API externa para {len(cnpjs)} CNPJs...")
            resultados = asyncio.run(processarCnpjs(cnpjs))

            print("Atualizando cadastro_fornecedores")
            for i in range(0, len(cnpjs), LOTE):
                batch = cnpjs[i:i + LOTE]
                self.repository.atualizarFornecedores(empresa_id, resultados, batch)
                print(f"Lote de {len(batch)} CNPJs atualizado.")

            print("🏁 Atualização finalizada com sucesso.")
        except Exception as e:
            self.repository.db.rollback()
            print(f"[❌ ERRO] Falha na atualização de fornecedores: {e}")