from src.Models._0000Model import Registro0000

def obterPeriodo(session, empresa_id: int) -> str:
    try:
        registro = (
            session.query(Registro0000)
            .filter(Registro0000.empresa_id == empresa_id)
            .order_by(Registro0000.id.desc())
            .first()
        )

        if registro and registro.dt_ini and len(registro.dt_ini) >= 6:
            return f"{registro.dt_ini[2:4]}/{registro.dt_ini[4:]}"  # mm/yyyy
    except Exception as e:
        print(f"[ERRO] Falha ao obter período do SPED (ORM): {e}")

    return "00/0000"
