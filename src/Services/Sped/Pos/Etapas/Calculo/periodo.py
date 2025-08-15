from sqlalchemy import select
from sqlalchemy.orm import Session
from src.Models._0000Model import Registro0000


def obter_periodo_atual(db: Session, empresa_id: int) -> str:
    """
    Retorna MM/AAAA a partir do dt_ini mais recente em 0000.
    Aceita dt_ini AAAAMMDD ou AAAAMM.
    """
    dt_ini = db.execute(
        select(Registro0000.dt_ini)
        .where(Registro0000.empresa_id == empresa_id)
        .order_by(Registro0000.id.desc())
        .limit(1)
    ).scalar()

    if not dt_ini or len(dt_ini) < 6:
        return "00/0000"
    return f"{dt_ini[2:4]}/{dt_ini[4:]}"
