import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.Models.c170novaModel import C170Nova

class C170NovaRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def fornecedorValidos(self, empresa_id: int) -> set:
        query = text("""
            SELECT cod_part, empresa_id
            FROM cadastro_fornecedores
            WHERE empresa_id = :empresa_id AND uf = 'CE' AND decreto = 0
        """)
        df = pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})
        return set(f"{row['cod_part']}_{row['empresa_id']}" for _, row in df.iterrows())

    def dados0200(self, empresa_id: int) -> dict:
        query = text("""
            SELECT cod_item, empresa_id, descr_item, cod_ncm
            FROM `0200`
            WHERE empresa_id = :empresa_id AND is_active = 1
        """)
        df = pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})
        return {
            f"{row['cod_item']}_{row['empresa_id']}": {
                "descr_item": row['descr_item'],
                "cod_ncm": row['cod_ncm']
            }
            for _, row in df.iterrows()
        }

    def buscarDados(self, empresa_id: int, lote_tamanho: int, offset: int) -> pd.DataFrame:
        query = text(f"""
            SELECT 
                c170.cod_item, c170.periodo, c170.reg, c170.num_item, c170.descr_compl,
                c170.qtd, c170.unid, c170.vl_item, c170.vl_desc, c170.cfop,
                c170.cst_icms, c170.id_c100, c170.filial, c170.ind_oper,
                c100.cod_part, c100.num_doc, c100.chv_nfe, c170.empresa_id
            FROM c170
            JOIN c100 ON c170.id_c100 = c100.id
            WHERE c170.empresa_id = :empresa_id
              AND c170.is_active = 1
              AND c100.is_active = 1
              AND c170.cfop IN ('1101', '1401', '1102', '1403', '1910', '1116')
            LIMIT {lote_tamanho} OFFSET {offset}
        """)
        return pd.read_sql(query, self.db.bind, params={"empresa_id": empresa_id})

    def inserirDados(self, df: pd.DataFrame):
        if df.empty:
            return
        df.to_sql(
            name="c170nova",
            con=self.db.bind,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000
        )

class C170NovaService:
    def __init__(self, repository: C170NovaRepository):
        self.repository = repository

    def preencher(self, empresa_id: int, lote_tamanho: int = 3000):
        print(f"[INÍCIO] Preenchendo c170nova para empresa_id={empresa_id}")
        totalInseridos = 0
        offset = 0

        try:
            print("[Parte 1] Carregando fornecedores CE com decreto=False")
            fornecedores_validos = self.repository.fornecedorValidos(empresa_id)

            print("[Parte 2] Carregando dados da tabela 0200")
            dados_0200 = self.repository.dados0200(empresa_id)

            print("[Parte 3] Iniciando processamento em lotes")
            while True:
                linhas = self.repository.buscarDados(empresa_id, lote_tamanho, offset)
                if linhas.empty:
                    break

                dadosInsercao = []
                for _, row in linhas.iterrows():
                    chave_forn = f"{row['cod_part']}_{empresa_id}"
                    if chave_forn not in fornecedores_validos:
                        continue

                    chave_0200 = f"{row['cod_item']}_{empresa_id}"
                    ref_0200 = dados_0200.get(chave_0200, {})
                    descricao = ref_0200.get("descr_item") or row['descr_compl']
                    cod_ncm = ref_0200.get("cod_ncm")

                    dadosInsercao.append({
                        'cod_item': row['cod_item'],
                        'periodo': row['periodo'],
                        'reg': row['reg'],
                        'num_item': row['num_item'],
                        'descr_compl': descricao,
                        'qtd': row['qtd'],
                        'unid': row['unid'],
                        'vl_item': row['vl_item'],
                        'vl_desc': row['vl_desc'],
                        'cfop': row['cfop'],
                        'cst': row['cst_icms'],
                        'id_c100': row['id_c100'],
                        'filial': row['filial'],
                        'ind_oper': row['ind_oper'],
                        'cod_part': row['cod_part'],
                        'num_doc': row['num_doc'],
                        'chv_nfe': row['chv_nfe'],
                        'empresa_id': empresa_id,
                        'cod_ncm': cod_ncm
                    })

                if dadosInsercao:
                    df_insercao = pd.DataFrame(dadosInsercao)
                    self.repository.inserirDados(df_insercao)
                    totalInseridos += len(dadosInsercao)
                    print(f"[INFO] Lote processado: {len(dadosInsercao)} registros inseridos")
                    if len(linhas) < lote_tamanho:
                        break
                if len(linhas) < lote_tamanho:
                    break

                offset += lote_tamanho

            print(f"[FINALIZADO] Total de {totalInseridos} registros inseridos em c170nova.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] Falha ao preencher c170nova: {e}")
            raise
