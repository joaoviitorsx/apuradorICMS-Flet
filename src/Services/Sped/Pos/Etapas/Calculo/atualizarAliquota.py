from sqlalchemy import select, text, tuple_
from sqlalchemy.orm import Session

from src.Models._0000Model import Registro0000
from src.Models.tributacaoModel import CadastroTributacao
from src.Models.c170cloneModel import C170Clone


def _coluna_por_ano(db: Session, empresa_id: int):
    dt_ini = db.execute(
        select(Registro0000.dt_ini)
        .where(Registro0000.empresa_id == empresa_id)
        .order_by(Registro0000.id.desc())
        .limit(1)
    ).scalar()
    ano = int(dt_ini[4:]) if dt_ini and len(dt_ini) >= 6 else 0
    return CadastroTributacao.aliquota if ano >= 2024 else CadastroTributacao.aliquota_antiga, ("aliquota" if ano >= 2024 else "aliquota_antiga")

def atualizar_aliquota_da_clone(db: Session, empresa_id: int, lote_tamanho: int = 5000):
    print("[DEBUG] Atualizando alíquotas em c170_clone...")

    coluna_expr, coluna_nome = _coluna_por_ano(db, empresa_id)

    if db.bind and db.bind.dialect.name == "mysql":
        result = db.execute(
            text(f"""
                SELECT n.id AS id_c170, c.{coluna_nome} AS nova_aliquota
                FROM c170_clone n
                JOIN cadastro_tributacao c
                  ON c.empresa_id = n.empresa_id
                 AND c.produto = n.descr_compl
                 AND c.ncm = n.ncm
                WHERE n.empresa_id = :eid
                  AND (n.aliquota IS NULL OR n.aliquota = '')
                  AND c.{coluna_nome} IS NOT NULL AND c.{coluna_nome} != ''
            """),
            {"eid": empresa_id}
        )
        registros = result.fetchall()
        if not registros:
            print("[DEBUG] Nenhum registro para atualizar.")
            return

        for i in range(0, len(registros), lote_tamanho):
            lote = registros[i:i + lote_tamanho]
            for r in lote:
                db.execute(
                    text("UPDATE c170_clone SET aliquota = :aliq WHERE id = :id"),
                    {"aliq": str(r.nova_aliquota)[:10], "id": r.id_c170}
                )
            db.commit()

        print(f"[DEBUG] {len(registros)} alíquotas atualizadas via MySQL.")
        return

    # Fallback para outros bancos
    pend = db.execute(
        select(C170Clone.id, C170Clone.descr_compl, C170Clone.ncm)
        .where(C170Clone.empresa_id == empresa_id)
        .where((C170Clone.aliquota.is_(None)) | (C170Clone.aliquota == ""))
    ).all()
    if not pend:
        print("[DEBUG] Nenhum registro pendente.")
        return

    chaves = {(p.descr_compl or "", p.ncm or "") for p in pend}
    aliqs = dict(
        db.execute(
            select(CadastroTributacao.produto, CadastroTributacao.ncm, coluna_expr)
            .where(
                CadastroTributacao.empresa_id == empresa_id,
                tuple_(CadastroTributacao.produto, CadastroTributacao.ncm).in_(list(chaves)),
            )
        ).all()
    )

    updates = [(str(aliqs.get((r.descr_compl or "", r.ncm or "")))[:10], r.id)
               for r in pend if aliqs.get((r.descr_compl or "", r.ncm or ""))]

    for i in range(0, len(updates), lote_tamanho):
        fatia = updates[i:i + lote_tamanho]
        db.bulk_update_mappings(C170Clone, [{"id": rid, "aliquota": aliquota} for aliquota, rid in fatia])
        db.commit()

    print(f"[DEBUG] {len(updates)} alíquotas atualizadas (fallback).")
