from sqlalchemy.orm import Session
from sqlalchemy import text
from src.Models.c170cloneModel import C170Clone

import pandas as pd


class AliquotaSimplesRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarRegistroSimples(self, empresa_id: int, periodo: str) -> pd.DataFrame:
        query = text("""
            SELECT 
                c.id,
                c.aliquota,
                c.descr_compl,
                c.cod_part
            FROM c170_clone c
            JOIN cadastro_fornecedores f
              ON f.cod_part = c.cod_part
             AND f.empresa_id = c.empresa_id
            WHERE 
                c.periodo = :periodo
                AND c.empresa_id = :empresa_id
                AND c.is_active = 1
                AND f.simples = 1
        """)
        return pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id, "periodo": periodo})

    def atualizarDados(self, df: pd.DataFrame):
        if df.empty:
            print("[INFO] Nenhuma alíquota válida para atualizar.")
            return

        updates = df[["id", "aliquota"]].to_dict(orient="records")
        with self.db.begin():
            self.db.bulk_update_mappings(C170Clone, updates)
        print(f"[OK] {len(updates)} registros atualizados com sucesso.")


class AliquotaSimplesService:
    def __init__(self, repository: AliquotaSimplesRepository):
        self.repository = repository

    def atualizar(self, empresa_id: int, periodo: str):
        print("[INÍCIO] Atualizando alíquotas Simples Nacional")
        try:
            df = self.repository.buscarRegistroSimples(empresa_id, periodo)
            total = len(df)
            print(f"[INFO] {total} registros carregados.")

            if df.empty:
                print("[OK] Nenhum registro para processar.")
                return

            # Limpeza
            df["aliquota_str"] = df["aliquota"].astype(str).str.strip().str.upper()

            def calcular_nova_aliquota(row):
                aliq = row["aliquota_str"]
                if aliq in ["ST", "ISENTO", "PAUTA", ""]:
                    return None
                try:
                    valor = float(aliq.replace(",", ".").replace("%", ""))
                    nova = round(valor + 3, 2)
                    return f"{nova:.2f}".replace(".", ",") + "%"
                except Exception as e:
                    print(f"[AVISO] Erro ao processar registro {row['id']}: {e}")
                    return None

            df["nova_aliquota"] = df.apply(calcular_nova_aliquota, axis=1)
            df_resultado = df[df["nova_aliquota"].notnull()][["id", "nova_aliquota"]].copy()
            df_resultado.rename(columns={"nova_aliquota": "aliquota"}, inplace=True)

            if not df_resultado.empty:
                self.repository.atualizarDados(df_resultado)
            else:
                print("[OK] Nenhuma alíquota foi considerada válida para atualização.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] ao atualizar alíquota Simples: {e}")
