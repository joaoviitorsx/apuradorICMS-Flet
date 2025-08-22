import traceback
from sqlalchemy.orm import aliased

from src.Models.c170novaModel import C170Nova
from src.Models.c170Model import C170
from src.Models.c100Model import C100
from src.Models._0200Model import Registro0200
from src.Models.fornecedorModel import CadastroFornecedor

class C170NovaService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def preencherC170Nova(self, empresa_id: int, lote_tamanho: int = 3000):
        print(f"[INÍCIO] Preenchendo c170nova para empresa_id={empresa_id}")
        session = self.session_factory()
        total_inseridos = 0
        offset = 0

        try:
            # Parte 1: Carregar fornecedores CE com decreto = 'Não'
            print("[Parte 1] Carregando fornecedores CE com decreto='Não'")
            fornecedores_rows = session.query(CadastroFornecedor.cod_part, CadastroFornecedor.empresa_id).filter(
                CadastroFornecedor.empresa_id == empresa_id,
                CadastroFornecedor.uf == 'CE',
                CadastroFornecedor.decreto == 'Não'
            ).all()
            fornecedores_validos = {f"{f.cod_part}_{f.empresa_id}" for f in fornecedores_rows}

            # Parte 2: Carregar dados da 0200
            print("[Parte 2] Carregando dados da tabela 0200")
            registros_0200 = session.query(Registro0200).filter(
                Registro0200.empresa_id == empresa_id
            ).all()
            dados_0200 = {
                f"{r.cod_item}_{r.empresa_id}": {
                    "descr_item": r.descr_item,
                    "cod_ncm": r.cod_ncm
                }
                for r in registros_0200
            }

            print("[Parte 3] Iniciando processamento em lotes")
            while True:
                c100_alias = aliased(C100)
                linhas = session.query(
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

                if not linhas:
                    break

                dados_insercao = []
                for row in linhas:
                    chave_forn = f"{row.cod_part}_{empresa_id}"
                    if chave_forn not in fornecedores_validos:
                        continue

                    chave_0200 = f"{row.cod_item}_{empresa_id}"
                    ref_0200 = dados_0200.get(chave_0200, {})
                    descricao = ref_0200.get("descr_item") or row.descr_compl
                    cod_ncm = ref_0200.get("cod_ncm")

                    dados_insercao.append(C170Nova(
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

                if dados_insercao:
                    session.bulk_save_objects(dados_insercao)
                    session.commit()
                    total_inseridos += len(dados_insercao)

                if len(linhas) < lote_tamanho:
                    break

                offset += lote_tamanho

            print(f"[FINALIZADO] Total de {total_inseridos} registros inseridos em c170nova.")

        except Exception as e:
            session.rollback()
            print(f"[ERRO] Falha ao preencher c170nova: {e}")
            traceback.print_exc()

        finally:
            session.close()
            print("[FIM] Conexão encerrada.")