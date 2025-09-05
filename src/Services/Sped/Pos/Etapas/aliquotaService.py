import traceback
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

class AliquotaService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def verificarPopupAliquota(self, empresa_id: int) -> bool:
        print(f"[INFO] Verificando alíquotas nulas para empresa_id={empresa_id}...")

        session: Session = self.session_factory()

        try:
            query = text("""
                SELECT COUNT(*) 
                FROM cadastro_tributacao 
                WHERE empresa_id = :empresa_id 
                AND COALESCE(aliquota, 0) = 0
            """)

            result = session.execute(query, {"empresa_id": empresa_id})
            count = result.scalar()

            if count > 0:
                print(f"[INFO] Existem {count} alíquotas nulas/zeradas. Deve exibir popup.")
                return True
            else:
                print("[INFO] Nenhuma alíquota nula encontrada.")
                return False

        except Exception as e:
            print(f"[ERRO] Falha ao verificar popup de alíquota: {e}")
            traceback.print_exc()
            return False

        finally:
            session.close()
            print("[INFO] Sessão encerrada.")
