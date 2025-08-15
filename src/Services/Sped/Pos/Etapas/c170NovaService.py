from __future__ import annotations
from typing import Iterable, Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, or_
from sqlalchemy.dialects.mysql import insert as mysql_insert

from src.Models.c170novaModel import C170Nova
from src.Models.c170Model import C170
from src.Models.c100Model import C100
from src.Models._0200Model import Registro0200
from src.Models.fornecedorModel import CadastroFornecedor

CFOPS_PADRAO = ('1101','1401','1102','1403','1910','1116')

class C170NovaService:
    def __init__(self, db: Session):
        self.db = db

    def _limpar_destino(self, empresa_id: int, periodos: Optional[Iterable[str]]) -> None:
        q = self.db.query(C170Nova).filter(C170Nova.empresa_id == empresa_id)
        if periodos:
            q = q.filter(C170Nova.periodo.in_(list(periodos)))
        q.delete(synchronize_session=False)
        self.db.commit()

    def montar(
        self,
        empresa_id: int,
        periodos: Optional[Iterable[str]] = None,
        cfops: Iterable[str] = CFOPS_PADRAO,
        page_size: int = 5000,
    ) -> int:
        """
        Gera c170nova a partir de C170/C100/0200 para fornecedores CE com decreto='Não'.
        Retorna a quantidade inserida.
        """
        self._limpar_destino(empresa_id, periodos)

        total_inseridos = 0
        last_id: int = 0

        while True:
            # Paginação por "seek" na PK do C170 (melhor que OFFSET)
            q = (
                select(
                    C170.id,             # 0
                    C170.cod_item,       # 1
                    C170.periodo,        # 2
                    C170.reg,            # 3
                    C170.num_item,       # 4
                    C170.descr_compl,    # 5
                    C170.qtd,            # 6
                    C170.unid,           # 7
                    C170.vl_item,        # 8
                    C170.vl_desc,        # 9
                    C170.cfop,           # 10
                    C170.cst_icms,       # 11
                    C170.id_c100,        # 12
                    C170.filial,         # 13
                    C100.ind_oper,       # 14
                    C100.cod_part,       # 15
                    C100.num_doc,        # 16
                    C100.chv_nfe,        # 17
                    C170.empresa_id,     # 18
                )
                .join(C100, C100.id == C170.id_c100)
                .join(
                    CadastroFornecedor,
                    (CadastroFornecedor.cod_part == C100.cod_part)
                    & (CadastroFornecedor.empresa_id == C170.empresa_id),
                )
                .where(
                    C170.empresa_id == empresa_id,
                    C170.cfop.in_(tuple(cfops)),
                    CadastroFornecedor.uf == 'CE',
                    CadastroFornecedor.decreto == 'Não',
                    C170.id > last_id,
                )
                .order_by(C170.id)
                .limit(page_size)
            )

            # Se quiser limitar por período(s), aplique aqui:
            if periodos:
                q = q.where(C170.periodo.in_(list(periodos)))

            rows = self.db.execute(q).all()
            if not rows:
                break

            # --- Lookup 0200 (descrição e NCM) para os cod_item do lote ---
            cod_items_lote = sorted({r[1] for r in rows})
            ref_0200: Dict[str, Tuple[str, str]] = {}
            if cod_items_lote:
                q0200 = (
                    select(Registro0200.cod_item, Registro0200.descr_item, Registro0200.cod_ncm)
                    .where(
                        Registro0200.empresa_id == empresa_id,
                        Registro0200.cod_item.in_(cod_items_lote),
                    )
                )
                for r in self.db.execute(q0200).all():
                    # r é indexado: 0=cod_item, 1=descr_item, 2=cod_ncm
                    ref_0200[r[0]] = (r[1], r[2])

            # --- Monta payload para bulk insert ---
            payload: List[dict] = []
            for r in rows:
                (
                    c170_id, cod_item, periodo, reg, num_item, desc_compl, qtd, unid, vl_item, vl_desc,
                    cfop, cst_icms, id_c100, filial, ind_oper, cod_part, num_doc, chv_nfe, emp_id
                ) = r

                descr, ncm = ref_0200.get(cod_item, (desc_compl, None))
                payload.append(dict(
                    cod_item=cod_item,
                    periodo=periodo,
                    reg=reg,
                    num_item=num_item,
                    descr_compl=descr,
                    qtd=qtd,
                    unid=unid,
                    vl_item=vl_item,
                    vl_desc=vl_desc,
                    cfop=cfop,
                    cst=cst_icms,          # coluna destino é 'cst'
                    id_c100=id_c100,
                    filial=filial,
                    ind_oper=ind_oper,
                    cod_part=cod_part,
                    num_doc=num_doc,
                    chv_nfe=chv_nfe,
                    empresa_id=emp_id,
                    cod_ncm=ncm,
                ))
                last_id = c170_id  # avança o ponteiro do seek

            if payload:
                # Mais rápido em muitas linhas
                self.db.bulk_insert_mappings(C170Nova, payload)
                self.db.commit()
                total_inseridos += len(payload)

            if len(rows) < page_size:
                break

        return total_inseridos
