import pandas as pd
from sqlalchemy import text
from src.Models.c170cloneModel import C170Clone
from src.Models._0000Model import Registro0000

LOTE_TAMANHO = 50000

class AtualizarAliquotaRepository:
    def __init__(self, db_session):
        self.db = db_session

    def buscarDtInit(self, empresa_id: int):
        query = """
            SELECT dt_ini 
            FROM `0000` 
            WHERE empresa_id = :empresa_id 
            AND is_active = 1
            ORDER BY id DESC
            LIMIT 1
        """
        
        df = pd.read_sql(text(query), self.db.bind, params={"empresa_id": empresa_id})
        return df.iloc[0]['dt_ini'] if not df.empty else None

    def buscarRegistrosPandas(self, empresa_id: int) -> pd.DataFrame:
        query = """
            SELECT 
                c.id AS id_c170,
                t.aliquota AS nova_aliquota,
                c.descr_compl,
                c.ncm
            FROM c170_clone c
            INNER JOIN cadastro_tributacao t
              ON t.empresa_id = c.empresa_id
             AND t.produto = c.descr_compl
             AND t.ncm = c.ncm
            WHERE c.empresa_id = :empresa_id
              AND c.is_active = 1
              AND (c.aliquota IS NULL OR TRIM(c.aliquota) = '')
              AND t.aliquota IS NOT NULL
              AND TRIM(t.aliquota) != ''
        """
        return pd.read_sql(text(query), self.db.bind, params={"empresa_id": empresa_id})

    def atualizarPorLoteViaTempTable(self, df_lote: pd.DataFrame):
        if df_lote.empty:
            return

        print(f"[DEBUG] Preparando {len(df_lote)} registros para atualização via tabela temporária...")

        # Criar tabela temporária
        temp_table = "temp_atualiza_aliquota"
        df_temp = df_lote[["id_c170", "nova_aliquota"]].copy()
        df_temp.columns = ["id", "aliquota"]
        df_temp["aliquota"] = df_temp["aliquota"].astype(str).str[:10]

        df_temp.to_sql(temp_table, self.db.bind, index=False, if_exists="replace")
        self.db.commit()

        dialeto = self.db.bind.dialect.name
        print(f"[DEBUG] Dialeto do banco: {dialeto}")

        if dialeto == "mysql":
            update_query = f"""
                UPDATE c170_clone
                JOIN {temp_table} AS tmp ON tmp.id = c170_clone.id
                SET c170_clone.aliquota = tmp.aliquota
                WHERE c170_clone.is_active = 1
            """
        else:
            raise NotImplementedError(f"UPDATE JOIN não implementado para {dialeto}")

        self.db.execute(text(update_query))
        self.db.commit()

        print(f"[OK] {len(df_temp)} registros atualizados via tabela temporária.")

class AtualizarAliquotaService:
    def __init__(self, repository: AtualizarAliquotaRepository):
        self.repository = repository

    def atualizar(self, empresa_id: int, lote_tamanho: int = LOTE_TAMANHO):
        print("[INÍCIO] Atualizando alíquotas em c170_clone por lotes...")

        try:
            dt_ini = self.repository.buscarDtInit(empresa_id)
            print(f"[DEBUG] Resultado dt_ini: {dt_ini}")
            if not dt_ini:
                print("[AVISO] Nenhum dt_ini encontrado. Cancelando.")
                return

            df = self.repository.buscarRegistrosPandas(empresa_id)
            total = len(df)
            print(f"[INFO] {total} registros a atualizar...")

            if total == 0:
                print("[DEBUG] Nenhum registro encontrado para atualização.")
                return

            print(f"[DEBUG] Exemplo de registro para atualizar: {df.iloc[0].to_dict()}")

            for i in range(0, total, lote_tamanho):
                df_lote = df.iloc[i:i + lote_tamanho]
                print(f"[DEBUG] Atualizando lote {i//lote_tamanho + 1} com {len(df_lote)} itens.")
                self.repository.atualizarPorLoteViaTempTable(df_lote)
                print(f"[OK] Lote {i//lote_tamanho + 1} atualizado com {len(df_lote)} itens.")

            print(f"[FINALIZADO] Alíquotas atualizadas em {total} registros para empresa {empresa_id}.")

        except Exception as err:
            self.repository.db.rollback()
            print(f"[ERRO] ao atualizar alíquotas: {err}")
