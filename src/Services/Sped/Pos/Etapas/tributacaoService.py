from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_
import traceback

from src.Models.c170Model import C170
from src.Models.c100Model import C100
from src.Models.fornecedorModel import CadastroFornecedor
from src.Models._0200Model import Registro0200
from src.Models.tributacaoModel import CadastroTributacao

class TributacaoService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def preencherTributacao(self, empresa_id: int):
        print(f"[VERIFICAÇÃO] Preenchendo cadastro_tributacao com produtos da empresa_id={empresa_id}")
        session = self.session_factory()

        try:
            c100_alias = aliased(C100)
            fornecedor_alias = aliased(CadastroFornecedor)
            registro0200_alias = aliased(Registro0200)

            print("[BUSCA] Buscando produtos válidos para tributação...")
            resultados = session.query(
                C170.empresa_id,
                C170.cod_item.label("codigo"),
                registro0200_alias.descr_item,
                C170.descr_compl,
                registro0200_alias.cod_ncm.label("ncm")
            ).join(
                c100_alias, C170.id_c100 == c100_alias.id
            ).join(
                fornecedor_alias,
                and_(
                    c100_alias.cod_part == fornecedor_alias.cod_part,
                    fornecedor_alias.empresa_id == C170.empresa_id
                )
            ).outerjoin(
                registro0200_alias,
                and_(
                    C170.cod_item == registro0200_alias.cod_item,
                    registro0200_alias.empresa_id == C170.empresa_id
                )
            ).filter(
                C170.empresa_id == empresa_id,
                C170.cfop.in_([
                    '1101', '1401', '1102', '1403', '1910', '1116',
                    '2101', '2102', '2401', '2403', '2910', '2116'
                ]),
                or_(
                    and_(
                        fornecedor_alias.uf == 'CE',
                        fornecedor_alias.decreto == 'Não'
                    ),
                    fornecedor_alias.uf != 'CE'
                )
            ).all()

            print(f"[PROCESSAMENTO] {len(resultados)} produtos encontrados para análise.")

            # Buscar existentes
            existentes = session.query(
                CadastroTributacao.codigo,
                CadastroTributacao.produto,
                CadastroTributacao.ncm
            ).filter(CadastroTributacao.empresa_id == empresa_id).all()

            set_existentes = {
                (e.codigo, e.produto, e.ncm) for e in existentes
            }

            novos_registros = []

            for row in resultados:
                produto = row.descr_item or row.descr_compl
                chave = (row.codigo, produto, row.ncm)

                if chave in set_existentes:
                    continue

                novos_registros.append(CadastroTributacao(
                    empresa_id=row.empresa_id,
                    codigo=row.codigo,
                    produto=produto,
                    ncm=row.ncm,
                    aliquota=None
                ))

            if novos_registros:
                session.bulk_save_objects(novos_registros)
                session.commit()
                print(f"[OK] {len(novos_registros)} códigos únicos inseridos na tabela cadastro_tributacao.")
            else:
                print("[OK] Nenhum novo registro para inserir.")

        except Exception as e:
            session.rollback()
            print(f"[ERRO] Falha ao preencher cadastro_tributacao: {e}")
            traceback.print_exc()

        finally:
            session.close()
            print("[FIM] Preenchimento de cadastro_tributacao concluído.")
