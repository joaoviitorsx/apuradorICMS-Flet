from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.Models.c170cloneModel import C170Clone

class CalculoResultadoRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarRegistros(self, empresa_id: int):
        query = (
            select(
                C170Clone.id,
                C170Clone.vl_item,
                C170Clone.vl_desc,
                C170Clone.aliquota
            )
            .where(C170Clone.empresa_id == empresa_id,
                     C170Clone.is_active == True)
        )
        return self.db.execute(query).fetchall()

    def atualizarDados(self, atualizacoes: list):
        for resultado, id_c170 in atualizacoes:
            stmt = (
                update(C170Clone)
                .where(C170Clone.id == id_c170)
                .values(resultado=resultado)
            )
            self.db.execute(stmt)
        self.db.commit()

class CalculoResultadoService:
    def __init__(self, repository: CalculoResultadoRepository):
        self.repository = repository

    def calcular(self, empresa_id: int, tamanho_lote: int = 5000):
        print("[INÍCIO] Atualizando resultado")
        try:
            registros = self.repository.buscarRegistros(empresa_id)
            total = len(registros)
            atualizacoes = []

            for idx, row in enumerate(registros, 1):
                try:
                    vl_item = float(str(row.vl_item).replace(',', '.'))
                    vl_desc = float(str(row.vl_desc).replace(',', '.')) if row.vl_desc else 0.0
                    aliquota_str = str(row.aliquota or '').strip().upper()

                    if aliquota_str in {"ST", "ISENTO"}:
                        resultado = 0.0
                    else:
                        try:
                            aliquota_val = float(aliquota_str.replace(',', '.').replace('%', ''))
                            resultado = round((vl_item - vl_desc) * (aliquota_val / 100), 2)
                        except ValueError:
                            continue
                    atualizacoes.append((resultado, row.id))
                except Exception as e:
                    print(f"[AVISO] Erro ao processar registro {row.id}: {e}")

                # Atualiza em lote
                if len(atualizacoes) >= tamanho_lote:
                    self.repository.atualizarDados(atualizacoes)
                    atualizacoes.clear()

            # Atualiza o restante
            if atualizacoes:
                self.repository.atualizarDados(atualizacoes)
            print(f"[OK] Resultado atualizado para {total} registros.")

        except Exception as err:
            self.repository.db.rollback()
            print(f"[ERRO] ao atualizar resultado: {err}")
