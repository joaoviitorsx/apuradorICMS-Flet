from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from src.Models.fornecedorModel import CadastroFornecedor
from src.Utils.cnpj import processarCnpjs

BATCH_SIZE = 50

class FornecedorService:
    def init(self, db_session: AsyncSession):
        self.db = db_session

async def atualizar_fornecedores(self, empresa_id: int) -> None:
    try:
        print("⏳ Buscando fornecedores novos para inserção...")

        subquery = select(CadastroFornecedor.cod_part).where(
            CadastroFornecedor.empresa_id == empresa_id
        ).subquery()

        fornecedores_stmt = f"""
            SELECT f.cod_part, f.nome, f.cnpj
            FROM `0150` f
            LEFT JOIN cadastro_fornecedores cf
                ON TRIM(f.cod_part) = TRIM(cf.cod_part) AND f.empresa_id = cf.empresa_id
            WHERE cf.cod_part IS NULL
              AND f.cnpj IS NOT NULL AND f.cnpj != ''
              AND f.empresa_id = :empresa_id
        """
        result = await self.db.execute(fornecedores_stmt, {"empresa_id": empresa_id})
        novos_fornecedores = result.fetchall()

        if novos_fornecedores:
            print(f"📥 Inserindo {len(novos_fornecedores)} novos fornecedores...")
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
                for cod_part, nome, cnpj in novos_fornecedores
            ]
            await self.db.execute(insert(CadastroFornecedor), inserts)
            await self.db.commit()

        print("🔍 Buscando CNPJs pendentes de atualização...")
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
        result = await self.db.execute(query)
        cnpjs = [row[0] for row in result.fetchall()]

        if not cnpjs:
            print("✅ Nenhum CNPJ pendente de atualização.")
            return

        print(f"🌐 Consultando API externa para {len(cnpjs)} CNPJs...")
        resultados = await processarCnpjs(cnpjs)

        print("🛠 Atualizando registros em lotes...")
        for i in range(0, len(cnpjs), BATCH_SIZE):
            batch = cnpjs[i:i + BATCH_SIZE]
            for cnpj in batch:
                dados = resultados.get(cnpj)
                if not dados:
                    continue
                _, cnae, uf, simples, decreto = dados
                stmt = (
                    update(CadastroFornecedor)
                    .where(CadastroFornecedor.cnpj == cnpj,
                           CadastroFornecedor.empresa_id == empresa_id)
                    .values(
                        cnae=cnae or '',
                        uf=uf or '',
                        simples=str(simples),
                        decreto=str(decreto)
                    )
                )
                await self.db.execute(stmt)
            await self.db.commit()
            print(f"✅ Lote de {len(batch)} atualizado.")

        print("🏁 Atualização finalizada com sucesso.")

    except Exception as e:
        await self.db.rollback()
        print(f"[❌ ERRO] Falha na atualização de fornecedores: {e}")