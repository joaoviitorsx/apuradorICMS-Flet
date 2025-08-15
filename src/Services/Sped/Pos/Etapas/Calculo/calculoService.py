from __future__ import annotations
from typing import Optional, List
from sqlalchemy.orm import Session

from .periodo import obter_periodo_atual
from .atualizarAliquota import atualizar_aliquota_da_clone
from .aliquotaSimples import ajustar_simples
from .calculoResultado import atualizar_resultado


class CalculoService:
    """
    Orquestra todas as etapas do cálculo de ICMS:
      1) Atualizar alíquotas em c170_clone
      2) Ajustar Simples Nacional
      3) Calcular campo resultado
    """

    def __init__(self, db: Session):
        self.db = db

    def calcular_resultado(self, empresa_id: int, periodos: Optional[List[str]] = None) -> dict:
        print(f"[CalculoService] === INICIANDO CÁLCULO COMPLETO PARA EMPRESA {empresa_id} ===")

        try:
            # Etapa 1: Atualizar alíquotas
            print("[CalculoService] 1. Atualizando alíquotas...")
            atualizar_aliquota_da_clone(self.db, empresa_id)

            # Etapa 2: Ajustar Simples
            print("[CalculoService] 2. Ajustando fornecedores do Simples Nacional...")
            periodo = obter_periodo_atual(self.db, empresa_id)
            ajustar_simples(self.db, empresa_id, periodo)

            # Etapa 3: Calcular resultado
            print("[CalculoService] 3. Calculando resultado...")
            atualizar_resultado(self.db, empresa_id)

            print("[CalculoService] === CÁLCULO CONCLUÍDO COM SUCESSO ===")
            return {
                "status": "ok",
                "mensagem": "Cálculo realizado com sucesso"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "erro",
                "mensagem": f"Erro durante cálculo: {e}"
            }
