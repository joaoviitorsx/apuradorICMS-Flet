import traceback
from sqlalchemy.orm import Session, aliased

from src.Models.c170novaModel import C170Nova
from src.Models.c170Model import C170
from src.Models.c100Model import C100
from src.Models._0200Model import Registro0200
from src.Models.fornecedorModel import CadastroFornecedor

class C170NovaRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def fornecedorValidos(self, empresa_id: int):
        rows = self.db.query(CadastroFornecedor.cod_part, CadastroFornecedor.empresa_id).filter(
            CadastroFornecedor.empresa_id == empresa_id,
            CadastroFornecedor.uf == 'CE',
            CadastroFornecedor.decreto == False
        ).all()
        return {f"{row.cod_part}_{row.empresa_id}" for row in rows}

    def dados0200(self, empresa_id: int):
        registros = self.db.query(Registro0200).filter(
            Registro0200.empresa_id == empresa_id
        ).all()
        return {
            f"{r.cod_item}_{r.empresa_id}": {
                "descr_item": r.descr_item,
                "cod_ncm": r.cod_ncm
            }
            for r in registros
        }

    def buscarDados(self, empresa_id: int, lote_tamanho: int, offset: int):
        c100_alias = aliased(C100)
        return self.db.query(
            C170.cod_item, C170.periodo, C170.reg, C170.num_item, C170.descr_compl,
            C170.qtd, C170.unid, C170.vl_item, C170.vl_desc, C170.cfop,
            C170.cst_icms, C170.id_c100, C170.filial, C170.ind_oper,
            c100_alias.cod_part, c100_alias.num_doc, c100_alias.chv_nfe,
            C170.empresa_id
        ).join(
            c100_alias, C170.id_c100 == c100_alias.id
        ).filter(
            C170.empresa_id == empresa_id,
            C170.cfop.in_(['1101', '1401', '1102', '1403', '1910', '1116'])
        ).limit(lote_tamanho).offset(offset).all()

    def inserirDados(self, dados_insercao: list):
        self.db.bulk_save_objects(dados_insercao)
        self.db.commit()

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
                if not linhas:
                    break

                dadosInsercao = []
                for row in linhas:
                    chave_forn = f"{row.cod_part}_{empresa_id}"
                    if chave_forn not in fornecedores_validos:
                        continue

                    chave_0200 = f"{row.cod_item}_{empresa_id}"
                    ref_0200 = dados_0200.get(chave_0200, {})
                    descricao = ref_0200.get("descr_item") or row.descr_compl
                    cod_ncm = ref_0200.get("cod_ncm")

                    dadosInsercao.append(C170Nova(
                        cod_item=row.cod_item,
                        periodo=row.periodo,
                        reg=row.reg,
                        num_item=row.num_item,
                        descr_compl=descricao,
                        qtd=row.qtd,
                        unid=row.unid,
                        vl_item=row.vl_item,
                        vl_desc=row.vl_desc,
                        cfop=row.cfop,
                        cst=row.cst_icms,
                        id_c100=row.id_c100,
                        filial=row.filial,
                        ind_oper=row.ind_oper,
                        cod_part=row.cod_part,
                        num_doc=row.num_doc,
                        chv_nfe=row.chv_nfe,
                        empresa_id=empresa_id,
                        cod_ncm=cod_ncm
                    ))

                if dadosInsercao:
                    self.repository.inserirDados(dadosInsercao)
                    totalInseridos += len(dadosInsercao)

                if len(linhas) < lote_tamanho:
                    break

                offset += lote_tamanho

            print(f"[FINALIZADO] Total de {totalInseridos} registros inseridos em c170nova.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] Falha ao preencher c170nova: {e}")
