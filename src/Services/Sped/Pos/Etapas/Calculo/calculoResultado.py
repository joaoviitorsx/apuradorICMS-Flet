from sqlalchemy import text
from sqlalchemy.orm import Session

from src.Utils.conversao import Conversor


def atualizar_resultado(db: Session, empresa_id: int, lote_tamanho: int = 20000):
    print("[DEBUG] Iniciando cálculo de resultado...")

    registros = db.execute(
        text("""
            SELECT id, vl_item, vl_desc, aliquota 
            FROM c170_clone
            WHERE empresa_id = :eid
        """),
        {"eid": empresa_id}
    ).fetchall()

    total = len(registros)
    print(f"[DEBUG] {total} registros encontrados.")

    if not registros:
        return

    atualizacoes = []

    for row in registros:
        try:
            vl_item = Conversor(row.vl_item)
            vl_desc = Conversor(row.vl_desc)
            aliquota = Conversor(row.aliquota)
            resultado = round((vl_item - vl_desc) * (aliquota / 100), 2)
            atualizacoes.append((resultado, row.id))
        except Exception as e:
            print(f"[DEBUG] Erro no registro {row.id}: {e}")

    for i in range(0, len(atualizacoes), lote_tamanho):
        lote = atualizacoes[i:i + lote_tamanho]
        for resultado, id_reg in lote:
            db.execute(
                text("UPDATE c170_clone SET resultado = :result WHERE id = :id"),
                {"result": resultado, "id": id_reg}
            )
        db.commit()
        print(f"[DEBUG] Lote {i//lote_tamanho + 1} de resultados atualizado.")

    print("[DEBUG] Cálculo de resultado concluído.")
