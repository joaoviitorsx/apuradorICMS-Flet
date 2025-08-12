from __future__ import annotations
from typing import Callable, Optional, Iterable, Dict, Any, List

from src.Config.Database.db import SessionLocal
from .fornecedorService import FornecedorService
from .c170NovaService import C170NovaService
from .cloneService import CloneService
from .tributacaoService import TributacaoService
from .calculoService import CalculoService


class SpedPosProcessamentoService:
    """
    Orquestra o pós-processamento dos SPEDs seguindo o fluxo do sistema legado:

      Fase A (preparação):
        - Atualiza cadastro de fornecedores (via API/CNPJ)
        - Monta c170nova
        - Insere produtos do 0200 em cadastro_tributacao
        - Se houver itens com alíquota nula, retorna 'needs_input' + lista para a UI (Flet)

      Fase B (finalização) - APÓS popup salvar alíquotas:
        - Clona c170nova -> c170_clone
        - Preenche alíquotas na clone a partir de cadastro_tributacao
        - Ajusta alíquotas para fornecedores do Simples
        - Calcula 'resultado'
    """

    def __init__(self, empresa_id: int, on_progress: Optional[Callable[[int], None]] = None):
        self.empresa_id = empresa_id
        self.on_progress = on_progress or (lambda _: None)

    # ---------------------------
    # Fase A — preparação
    # ---------------------------
    def run(
        self,
        *,
        periodos: Optional[Iterable[str]] = None,
        limit_ui: int = 300,
    ) -> Dict[str, Any]:
        """
        Executa a fase de preparação. Se houver alíquotas pendentes, retorna:
          {"status": "needs_input", "faltantes": [...]}  (lista p/ UI)
        Caso contrário, vai direto para finalização.
        """
        try:
            print(f"[DEBUG SpedPos] === INICIANDO FASE A (PREPARAÇÃO) ===")
            print(f"[DEBUG SpedPos] Empresa ID: {self.empresa_id}")
            
            with SessionLocal() as db:
                # 40% — fornecedores
                print("[DEBUG SpedPos] 1. Atualizando fornecedores...")
                self.on_progress(40)
                FornecedorService(db).atualizar_fornecedores(self.empresa_id)
                print("[DEBUG SpedPos] Fornecedores atualizados.")

                # 50% — c170nova
                print("[DEBUG SpedPos] 2. Montando C170Nova...")
                self.on_progress(50)
                C170NovaService(db).montar(self.empresa_id, periodos=periodos)
                print("[DEBUG SpedPos] Tabela C170Nova criada e preenchida.")

                # 52% — cadastro_tributacao a partir do 0200
                print("[DEBUG SpedPos] 3. Preenchendo cadastro de tributação...")
                self.on_progress(52)
                itens_ui: List[Dict] = TributacaoService(db).inserir_do_0200_e_listar_para_ui(
                    self.empresa_id, limit=limit_ui
                )
                print(f"[DEBUG SpedPos] Cadastro de tributação preenchido. Itens pendentes: {len(itens_ui)}")

            # Se há itens para preencher, paramos aqui e deixamos a UI abrir o modal
            if itens_ui:
                print("[DEBUG SpedPos] === FASE A PAUSADA - AGUARDANDO POPUP ===")
                self.on_progress(54)
                return {"status": "needs_input", "faltantes": itens_ui}

            # Sem pendências — vai direto para finalização
            print("[DEBUG SpedPos] === FASE A CONCLUÍDA - INDO PARA FINALIZAÇÃO ===")
            return self.finalizar(periodos=periodos)
            
        except Exception as e:
            print(f"[DEBUG SpedPos] ERRO na Fase A: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "erro", "mensagem": f"Erro na preparação: {e}"}

    # ---------------------------
    # Fase B — finalização
    # (chamar APÓS a UI salvar as alíquotas faltantes)
    # ---------------------------
    def finalizar(
        self,
        *,
        periodos: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executa a fase de finalização seguindo o fluxo do legado:
        1. Clona c170nova -> c170_clone
        2. Atualiza alíquotas na clone (por CÓDIGO)
        3. Ajusta alíquotas para fornecedores Simples
        4. Calcula resultado
        """
        try:
            print(f"[DEBUG SpedPos] === INICIANDO FASE B (FINALIZAÇÃO) ===")
            
            with SessionLocal() as db:
                # 60% — clonar para c170_clone (seguindo o legado)
                print("[DEBUG SpedPos] 1. Clonando C170Nova -> C170Clone...")
                self.on_progress(60)
                clone_result = CloneService(db).clonar_c170nova_para_clone(
                    self.empresa_id, 
                    periodos=periodos, 
                    reuse_id_from_nova=True, 
                    replace_strategy=True
                )
                print(f"[DEBUG SpedPos] Tabela C170Clone criada. Inseridos: {clone_result}")

                # 75% — atualizar alíquotas na clone (CORRIGIDO para usar código)
                print("[DEBUG SpedPos] 2. Atualizando alíquotas na C170Clone...")
                self.on_progress(75)
                calc = CalculoService(db)
                calc.atualizar_aliquota_da_clone(self.empresa_id)
                print("[DEBUG SpedPos] Alíquotas atualizadas na tabela C170Clone.")

                # Obter período atual (seguindo o legado)
                periodo = calc.obter_periodo_atual(self.empresa_id)
                print(f"[DEBUG SpedPos] Período detectado: {periodo}")

                # 85% — ajustar Simples
                print("[DEBUG SpedPos] 3. Ajustando alíquotas do Simples Nacional...")
                self.on_progress(85)
                calc.ajustar_simples(self.empresa_id, periodo)
                print("[DEBUG SpedPos] Alíquotas do Simples Nacional ajustadas.")

                # 90% — calcular resultado
                print("[DEBUG SpedPos] 4. Calculando campo resultado...")
                self.on_progress(90)
                calc.atualizar_resultado(self.empresa_id)
                print("[DEBUG SpedPos] Campo resultado calculado com base em vl_item e aliquota.")

            self.on_progress(100)
            print("[DEBUG SpedPos] === FASE B CONCLUÍDA COM SUCESSO ===")
            
            return {
                "status": "ok",
                "mensagem": "Pós-processamento concluído.",
                "clone_inseridos": clone_result,
            }
            
        except Exception as e:
            print(f"[DEBUG SpedPos] ERRO na Fase B: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "erro", "mensagem": f"Erro na finalização: {e}"}