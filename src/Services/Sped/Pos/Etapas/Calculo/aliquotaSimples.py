from sqlalchemy import text
from sqlalchemy.orm import Session
from src.Utils.conversao import Conversor


def ajustar_simples(db: Session, empresa_id: int, periodo: str):
    print("[DEBUG] Ajustando alíquotas para fornecedores do Simples...")

    rows = db.execute(
        text("""
            SELECT c.id, c.aliquota
            FROM c170_clone c
            JOIN cadastro_fornecedores f 
              ON f.cod_part = c.cod_part AND f.empresa_id = :eid
            WHERE c.periodo = :per AND c.empresa_id = :eid
              AND f.simples = 'Sim'
        """),
        {"eid": empresa_id, "per": periodo}
    ).fetchall()

    atualizacoes = []
    for row in rows:
        aliq = str(row.aliquota or "").strip().upper()
        if aliq in ["ST", "ISENTO", "PAUTA", ""]:
            continue
        try:
            nova = round(Conversor(row.aliquota) + 3, 2)
            nova_aliq = f"{nova:.2f}".replace('.', ',') + '%'
            atualizacoes.append((nova_aliq, row.id))
        except Exception as e:
            print(f"[DEBUG] Erro registro {row.id}: {e}")

    for nova, id_reg in atualizacoes:
        db.execute(
            text("UPDATE c170_clone SET aliquota = :aliq WHERE id = :id"),
            {"aliq": nova, "id": id_reg}
        )
    db.commit()
    print(f"[DEBUG] {len(atualizacoes)} alíquotas Simples ajustadas.")
