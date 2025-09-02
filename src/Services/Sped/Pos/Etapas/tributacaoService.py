from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session, aliased

from src.Models.c170Model import C170
from src.Models.c100Model import C100
from src.Models._0200Model import Registro0200
from src.Models.fornecedorModel import CadastroFornecedor
from src.Models.tributacaoModel import CadastroTributacao

class TributacaoRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarProdutosValidos(self, empresa_id: int):
        c100Alias = aliased(C100)
        fonecedorAlias = aliased(CadastroFornecedor)
        registro0200Alias = aliased(Registro0200)

        return self.db.query(
            C170.empresa_id,
            C170.cod_item.label("codigo"),
            registro0200Alias.descr_item,
            C170.descr_compl,
            registro0200Alias.cod_ncm.label("ncm")
        ).join(
            c100Alias, C170.id_c100 == c100Alias.id
        ).join(
            fonecedorAlias,
            and_(
                c100Alias.cod_part == fonecedorAlias.cod_part,
                fonecedorAlias.empresa_id == C170.empresa_id
            )
        ).outerjoin(
            registro0200Alias,
            and_(
                C170.cod_item == registro0200Alias.cod_item,
                registro0200Alias.empresa_id == C170.empresa_id
            )
        ).filter(
            C170.empresa_id == empresa_id,
            C170.cfop.in_(['1101', '1401', '1102', '1403', '1910', '1116','2101', '2102', '2401', '2403', '2910', '2116']),
            or_(
                and_(
                    fonecedorAlias.uf == 'CE',
                    fonecedorAlias.decreto == False
                ),
                fonecedorAlias.uf != 'CE'
            )
        ).all()

    def buscarExistentes(self, empresa_id: int):
        return self.db.query(
            CadastroTributacao.codigo,
            CadastroTributacao.produto,
            CadastroTributacao.ncm
        ).filter(CadastroTributacao.empresa_id == empresa_id).all()

    def inserirDados(self, novos_registros: list):
        for obj in novos_registros:
            sql = text("""
                INSERT IGNORE INTO cadastro_tributacao (empresa_id, codigo, produto, ncm, aliquota)
                VALUES (:empresa_id, :codigo, :produto, :ncm, :aliquota)
            """)
            self.db.execute(sql, {
                "empresa_id": obj.empresa_id,
                "codigo": obj.codigo,
                "produto": obj.produto,
                "ncm": obj.ncm,
                "aliquota": obj.aliquota
            })
        self.db.commit()

class TributacaoService:
    def __init__(self, repository: TributacaoRepository):
        self.repository = repository

    def preencher(self, empresa_id: int):
        print(f"[VERIFICAÇÃO] Preenchendo cadastro_tributacao com produtos da empresa_id={empresa_id}")
        try:
            resultados = self.repository.buscarProdutosValidos(empresa_id)
            print(f"[PROCESSAMENTO] {len(resultados)} produtos encontrados para análise.")

            existentes = self.repository.buscarExistentes(empresa_id)
            set_existentes = {(e.codigo, e.produto, e.ncm) for e in existentes}

            novosRegistros = []
            chavesNovos = set()
            for row in resultados:
                produto = row.descr_item or row.descr_compl
                chave = (row.codigo, produto, row.ncm)
                if chave in set_existentes or chave in chavesNovos:
                    continue
                novosRegistros.append(CadastroTributacao(
                    empresa_id=row.empresa_id,
                    codigo=row.codigo,
                    produto=produto,
                    ncm=row.ncm,
                    aliquota=None
                ))
                chavesNovos.add(chave)

            if novosRegistros:
                self.repository.inserirDados(novosRegistros)
                print(f"[OK] {len(novosRegistros)} códigos únicos inseridos na tabela cadastro_tributacao.")
            else:
                print("[OK] Nenhum novo registro para inserir.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] Falha ao preencher cadastro_tributacao: {e}")
