import asyncio
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.Utils.cnpj import processarCnpjs

LOTE = 50

class FornecedorRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def novosFornecedores(self, empresa_id: int) -> pd.DataFrame:
        query = text("""
            SELECT r.cod_part, r.nome, r.cnpj
            FROM `0150` r
            WHERE r.empresa_id = :empresa_id
              AND r.cnpj IS NOT NULL AND r.cnpj != ''
              AND r.cod_part NOT IN (
                  SELECT cod_part FROM cadastro_fornecedores WHERE empresa_id = :empresa_id
              )
        """)
        return pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})

    def inserirFornecedores(self, empresa_id: int, df: pd.DataFrame) -> int:
        if df.empty:
            return 0

        df_insert = df.copy()
        df_insert["empresa_id"] = empresa_id
        df_insert["uf"] = ""
        df_insert["cnae"] = ""
        df_insert["decreto"] = ""
        df_insert["simples"] = ""

        df_insert = df_insert[[
            "empresa_id", "cod_part", "nome", "cnpj", "uf", "cnae", "decreto", "simples"
        ]]

        df_insert.to_sql(
            name="cadastro_fornecedores",
            con=self.db.bind,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000
        )
        return len(df_insert)

    def cnpjsPendentes(self, empresa_id: int) -> list[str]:
        query = text("""
            SELECT cnpj
            FROM cadastro_fornecedores
            WHERE empresa_id = :empresa_id
              AND cnpj IS NOT NULL AND cnpj != ''
              AND (
                  cnae IS NULL OR cnae = '' OR
                  uf IS NULL OR uf = '' OR
                  decreto IS NULL OR decreto = '' OR
                  simples IS NULL OR simples = ''
              )
        """)
        df = pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})
        return df["cnpj"].drop_duplicates().tolist()

    def atualizarFornecedores(self, empresa_id: int, resultados: dict, lote_cnpjs: list[str]):
        updates = []
        for cnpj in lote_cnpjs:
            dados = resultados.get(cnpj)
            if not dados or all(x is None for x in dados):
                continue
            razao_social, cnae, uf, simples, decreto = dados
            updates.append({
                "cnpj": cnpj,
                "empresa_id": empresa_id,
                "cnae": cnae or '',
                "uf": uf or '',
                "simples": str(simples) if simples is not None else '',
                "decreto": str(decreto) if decreto is not None else ''
            })

        if not updates:
            return

        for row in updates:
            stmt = text("""
                UPDATE cadastro_fornecedores
                SET cnae = :cnae,
                    uf = :uf,
                    simples = :simples,
                    decreto = :decreto
                WHERE empresa_id = :empresa_id AND cnpj = :cnpj
            """)
            self.db.execute(stmt, row)

        self.db.commit()

class FornecedorService:
    def __init__(self, repository: FornecedorRepository):
        self.repository = repository

    def processar(self, empresa_id: int):
        try:
            print("⏳ Buscando fornecedores novos para inserção...")
            df_novos = self.repository.novosFornecedores(empresa_id)
            print(f"Novos fornecedores encontrados: {len(df_novos)}")
            inseridos = self.repository.inserirFornecedores(empresa_id, df_novos)
            print(f"{inseridos} fornecedores inseridos.")

            print("🔍 Atualizando fornecedores com dados externos...")
            cnpjs = self.repository.cnpjsPendentes(empresa_id)
            print(f"CNPJs pendentes: {len(cnpjs)}")

            if not cnpjs:
                print("✅ Nenhum CNPJ pendente de atualização.")
                return

            print(f"🌐 Consultando API externa para {len(cnpjs)} CNPJs...")
            resultados = asyncio.run(processarCnpjs(cnpjs))

            print("📥 Atualizando cadastro_fornecedores")
            for i in range(0, len(cnpjs), LOTE):
                batch = cnpjs[i:i + LOTE]
                self.repository.atualizarFornecedores(empresa_id, resultados, batch)
                print(f"✅ Lote de {len(batch)} CNPJs atualizado.")

            print("🏁 Atualização finalizada com sucesso.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[❌ ERRO] Falha na atualização de fornecedores: {e}")