import pandas as pd
import traceback
from sqlalchemy import text
from sqlalchemy.orm import Session

class TributacaoRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarProdutosValidos(self, empresa_id: int) -> pd.DataFrame:
        try:
            empresa_id = int(empresa_id)
            query = text("""
                SELECT 
                    c170.empresa_id,
                    c170.cod_item AS codigo,
                    COALESCE(r0200.descr_item, c170.descr_compl) AS produto,
                    r0200.cod_ncm AS ncm
                FROM c170
                JOIN c100 ON c170.id_c100 = c100.id
                JOIN cadastro_fornecedores f 
                    ON f.cod_part = c100.cod_part
                    AND f.empresa_id = c170.empresa_id
                LEFT JOIN `0200` r0200 
                    ON r0200.cod_item = c170.cod_item
                    AND r0200.empresa_id = c170.empresa_id
                    AND r0200.is_active = 1
                WHERE 
                    c170.empresa_id = :empresa_id
                    AND c170.is_active = 1
                    AND c100.is_active = 1
                    AND c170.cfop IN (
                        '1101', '1401', '1102', '1403', '1910', '1116',
                        '2101', '2102', '2401', '2403', '2910', '2116'
                    )
                    AND (
                        (f.uf = 'CE' AND f.decreto = 0)
                        OR f.uf != 'CE'
                    )
            """)
            df = pd.read_sql(query, con=self.db.bind, params={"empresa_id": empresa_id})
            return df

        except Exception as e:
            print(f"[ERRO] Falha ao buscar produtos válidos: {e}")
            raise

    def buscarExistentes(self, empresa_id: int) -> pd.DataFrame:
        try:
            empresa_id = int(empresa_id)
            query = text("""
                SELECT codigo, produto, ncm
                FROM cadastro_tributacao
                WHERE empresa_id = :empresa_id
            """)
            df = pd.read_sql(query, con=self.db.bind, params={"empresa_id": empresa_id})
            return df

        except Exception as e:
            print(f"[ERRO] Falha ao buscar registros existentes: {e}")
            raise

    def inserirDados(self, df_novos: pd.DataFrame):
        if df_novos.empty:
            print("[INFO] Nenhum dado novo a ser inserido.")
            return

        try:
            if 'empresa_id' not in df_novos.columns or df_novos['empresa_id'].isnull().all():
                raise ValueError("empresa_id não encontrado nos dados")

            # Remove duplicados
            df_filtrado = df_novos.drop_duplicates(subset=['empresa_id', 'codigo', 'produto', 'ncm']).copy()
            df_filtrado = df_filtrado[['empresa_id', 'codigo', 'produto', 'ncm']]
            df_filtrado['aliquota'] = None

            # Inserção via to_sql (em lote)
            df_filtrado.to_sql(
                name="cadastro_tributacao",
                con=self.db.bind,
                if_exists="append",
                index=False,
                method="multi"  # Usa executemany por trás
            )

            self.db.commit()
            print(f"[OK] {len(df_filtrado)} registros únicos inseridos com sucesso.")

        except Exception as e:
            print(f"[ERRO] Falha na inserção em lote: {e}")
            self.db.rollback()
            raise


class TributacaoService:
    def __init__(self, repository: TributacaoRepository):
        self.repository = repository

    def preencher(self, empresa_id: int):
        try:
            empresa_id = int(empresa_id)

            print(f"[VERIFICAÇÃO] Preenchendo cadastro_tributacao com produtos da empresa_id={empresa_id}")

            df_produtos = self.repository.buscarProdutosValidos(empresa_id)
            print(f"[PROCESSAMENTO] {len(df_produtos)} produtos encontrados para análise.")

            df_existentes = self.repository.buscarExistentes(empresa_id)
            set_existentes = set(zip(df_existentes['codigo'], df_existentes['produto'], df_existentes['ncm']))
            print(f"[INFO] {len(set_existentes)} registros já existem na tabela.")

            df_produtos.dropna(subset=['produto', 'ncm'], inplace=True)
            df_produtos['produto'] = df_produtos['produto'].str.strip()
            df_produtos = df_produtos[df_produtos['produto'] != '']
            df_produtos.drop_duplicates(subset=['codigo', 'produto', 'ncm'], inplace=True)

            df_produtos['chave'] = list(zip(df_produtos['codigo'], df_produtos['produto'], df_produtos['ncm']))
            df_novos = df_produtos[~df_produtos['chave'].isin(set_existentes)].copy()

            if not df_novos.empty:
                print(f"[INFO] Preparando para inserir {len(df_novos)} novos registros...")
                df_novos.drop(columns=['chave'], inplace=True)
                self.repository.inserirDados(df_novos)
            else:
                print("[OK] Nenhum novo registro para inserir.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] Falha ao preencher cadastro_tributacao: {e}")
            traceback.print_exc()
            raise
