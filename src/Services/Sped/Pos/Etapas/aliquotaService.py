import traceback
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.Models.tributacaoModel import CadastroTributacao

class AliquotaService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def deve_exibir_popup_aliquota(self, empresa_id: int) -> bool:
        print(f"[INFO] Verificando alíquotas nulas para empresa_id={empresa_id}...")

        session: Session = self.session_factory()

        try:
            subquery = (
                session.query(
                    func.min(CadastroTributacao.codigo).label("codigo"),
                    CadastroTributacao.produto,
                    CadastroTributacao.ncm
                )
                .filter(
                    CadastroTributacao.empresa_id == empresa_id,
                    or_(
                        CadastroTributacao.aliquota.is_(None),
                        func.trim(func.cast(CadastroTributacao.aliquota, str)) == ''
                    )
                )
                .group_by(CadastroTributacao.produto, CadastroTributacao.ncm)
                .subquery()
            )

            count_query = session.query(func.count()).select_from(subquery)
            count = count_query.scalar()

            if count > 0:
                print(f"[INFO] Existem {count} alíquotas nulas. Deve exibir popup.")
                return True
            else:
                print("[INFO] Nenhuma alíquota nula encontrada.")
                return False

        except Exception as e:
            print(f"[ERRO] Falha ao verificar popup de alíquota: {e}")
            traceback.print_exc()
            return False  # Por segurança, não exibe popup se falhar

        finally:
            session.close()
            print("[INFO] Sessão encerrada.")