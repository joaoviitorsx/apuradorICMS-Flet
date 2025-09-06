import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class ClonagemRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarC170Nova(self, empresa_id: int) -> pd.DataFrame:
        query = text("""
            SELECT 
                empresa_id, cod_item, periodo, reg, num_item, descr_compl, cod_ncm, qtd,
                unid, vl_item, vl_desc, cst, cfop, id_c100, filial, ind_oper, cod_part,
                num_doc, chv_nfe
            FROM c170nova
            WHERE empresa_id = :empresa_id AND is_active = 1
        """)
        return pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})

    def inserirC170Clone(self, df: pd.DataFrame, num_threads: int = 4, chunk_size: int = 10000):
        if df.empty:
            print("[INFO] Nenhum dado para inserir em c170_clone.")
            return

        print(f"[INFO] Inserindo {len(df)} registros com {num_threads} thread(s)...")

        # Preparar DataFrame
        df['aliquota'] = ''
        df['resultado'] = ''
        df['is_active'] = True
        df.rename(columns={"cod_ncm": "ncm"}, inplace=True)

        colunas_ordenadas = [
            'empresa_id', 'cod_item', 'periodo', 'reg', 'num_item', 'descr_compl',
            'ncm', 'qtd', 'unid', 'vl_item', 'vl_desc', 'cst', 'cfop', 'id_c100',
            'filial', 'ind_oper', 'cod_part', 'num_doc', 'chv_nfe',
            'aliquota', 'resultado', 'is_active'
        ]
        df = df[colunas_ordenadas]

        # Dividir em partes
        num_lotes = int(np.ceil(len(df) / chunk_size))
        df_chunks = [df.iloc[i*chunk_size:(i+1)*chunk_size].copy() for i in range(num_lotes)]

        def inserir_lote(df_lote):
            try:
                df_lote.to_sql(
                    name="c170_clone",
                    con=self.db.bind,
                    if_exists="append",
                    index=False,
                    method="multi"
                )
                return len(df_lote)
            except Exception as e:
                print(f"[ERRO] Falha ao inserir lote: {e}")
                return 0

        inseridos = 0
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            results = list(executor.map(inserir_lote, df_chunks))

        total = sum(results)
        print(f"[OK] {total} registros clonados com sucesso em c170_clone.")

class ClonagemService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def clonarC170Nova(self, empresa_id: int):
        print(f"[INÍCIO] Clonagem da c170nova para c170_clone (empresa_id={empresa_id})")
        session: Session = self.session_factory()

        try:
            repo = ClonagemRepository(session)

            print("[SELECT] Lendo dados da c170nova...")
            df = repo.buscarC170Nova(empresa_id)

            if not df.empty:
                print(f"[PROCESSAMENTO] {len(df)} registros serão clonados.")
                repo.inserirC170Clone(df, num_threads=4, chunk_size=10000)
            else:
                print("[INFO] Nenhum registro encontrado para clonar.")

        except Exception as e:
            session.rollback()
            print(f"[ERRO] Falha durante a clonagem da c170nova: {e}")

        finally:
            session.close()
            print("[FIM] Clonagem finalizada.")
