from __future__ import annotations
from typing import Sequence, Callable, Optional, Iterable, Dict, Any

from src.Config.Database.db import SessionLocal
from src.Services.spedLeitorService import ler_e_processar_arquivos
from src.Services.spedSalvarService import salvar_dados_sped
from src.Services.pos.spedPosProcessamento import SpedPosProcessamentoService


class SpedController:
    """
    Controlador de alto nível:
      - Importar arquivos SPED (leitura + inserção no banco)
      - Rodar pós-processamento em 2 fases:
         Fase A: preparação (pode retornar 'needs_input' para abrir janela no Flet)
         Fase B: finalização (clone + alíquotas + simples + resultado)
    """

    def __init__(self, on_progress: Optional[Callable[[int], None]] = None):
        # Garante que o callback seja seguro
        self.on_progress = self._safe_progress_callback(on_progress)

    def _safe_progress_callback(self, callback):
        """Wrapper para evitar erros no callback"""
        if callback is None:
            return lambda _: None
        
        def safe_callback(pct: int):
            try:
                callback(pct)
            except Exception:
                # Ignora erros no callback para não quebrar o processamento
                pass
        return safe_callback

    # -------------------------
    # Método principal para processamento completo
    # -------------------------
    def processar_sped_completo(self, caminho_arquivo: str, empresa_id: int) -> Dict[str, Any]:
        """
        Método completo que importa um SPED e executa pós-processamento até o ponto onde precisa de alíquotas.
        Se há alíquotas pendentes, retorna 'needs_input' e PARA o processamento.
        O processamento deve ser continuado chamando pos_finalizar() após resolver as pendências.
        """
        try:
            print(f"[DEBUG] Iniciando processamento do arquivo: {caminho_arquivo}")
            self.on_progress(5)
            
            # Importa o arquivo SPED
            resultado_importacao = self.importar_speds(empresa_id, [caminho_arquivo])
            print(f"[DEBUG] Resultado importação: {resultado_importacao}")
            
            if resultado_importacao.get("status") != "ok":
                return {
                    "status": "erro",
                    "mensagem": "Erro durante importação do SPED"
                }
            
            # Extrai o período do resultado da importação
            periodo = resultado_importacao.get("periodo", "")
            print(f"[DEBUG] Período extraído: {periodo}")
            
            self.on_progress(40)
            
            # Executa preparação do pós-processamento
            resultado_pos = self.pos_preparar(
                empresa_id, 
                periodos=[periodo] if periodo else None
            )
            print(f"[DEBUG] Resultado pós-preparação: {resultado_pos}")
            
            self.on_progress(80)
            
            # Verifica se há alíquotas faltantes - SE SIM, PARA AQUI
            if resultado_pos.get("status") == "needs_input":
                faltantes_lista = resultado_pos.get("faltantes", [])
                faltantes_count = len(faltantes_lista)
                print(f"[DEBUG] Encontradas {faltantes_count} alíquotas faltantes - PARANDO processamento")
                
                self.on_progress(80)  # Mantém em 80% até resolver pendências
                return {
                    "status": "ok",
                    "needs_user_input": True,  # Flag indicando que precisa de input do usuário
                    "aliquotas_faltantes": faltantes_count,
                    "faltantes_lista": faltantes_lista,
                    "periodo": periodo,
                    "mensagem": f"Importação concluída. {faltantes_count} alíquotas pendentes."
                }
            
            # Se não há pendências, finaliza automaticamente
            print("[DEBUG] Sem pendências, finalizando automaticamente...")
            resultado_final = self.pos_finalizar(
                empresa_id, 
                periodos=[periodo] if periodo else None
            )
            
            self.on_progress(100)
            
            if resultado_final.get("status") == "ok":
                return {
                    "status": "ok",
                    "aliquotas_faltantes": 0,
                    "periodo": periodo,
                    "mensagem": "Importação e processamento concluídos com sucesso."
                }
            else:
                return {
                    "status": "erro",
                    "mensagem": "Erro durante finalização do processamento"
                }
            
        except Exception as e:
            print(f"[DEBUG ERRO] Erro durante processamento: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "erro",
                "mensagem": f"Erro durante processamento: {str(e)}"
            }

    # -------------------------
    # Fase 0 — Importação
    # -------------------------
    def importar_speds(self, empresa_id: int, caminhos: Sequence[str]) -> Dict[str, Any]:
        """
        Lê os .txt, normaliza e salva em lote nos Models.
        Retorna contadores por registro e o período.
        """
        self.on_progress(5)
        linhas = ler_e_processar_arquivos(list(caminhos))

        self.on_progress(25)
        resumo = salvar_dados_sped(empresa_id, linhas)

        self.on_progress(35)
        return {"status": "ok", **resumo}

    # -------------------------
    # Fase A — Preparação
    # -------------------------
    def pos_preparar(
        self,
        empresa_id: int,
        *,
        periodos: Optional[Iterable[str]] = None,
        limit_ui: int = 300,
    ) -> Dict[str, Any]:
        """
        Executa a fase A do pós-processamento.
        Se houver alíquotas pendentes, retorna {"status": "needs_input", "faltantes": [...]}
        Caso contrário, {"status": "ready_to_finalize"}.
        """
        svc = SpedPosProcessamentoService(empresa_id, on_progress=self.on_progress)
        return svc.run(periodos=periodos, limit_ui=limit_ui)

    # -------------------------
    # Fase B — Finalização
    # -------------------------
    def pos_finalizar(
        self,
        empresa_id: int,
        *,
        periodos: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executa a fase B (clone + alíquotas + simples + resultado).
        Use depois que o usuário preencher as alíquotas faltantes na UI do Flet.
        """
        svc = SpedPosProcessamentoService(empresa_id, on_progress=self.on_progress)
        return svc.finalizar(periodos=periodos)

    # -------------------------
    # Pipeline completo (opcional)
    # -------------------------
    def importar_e_pos(
        self,
        empresa_id: int,
        caminhos: Sequence[str],
        *,
        periodos: Optional[Iterable[str]] = None,
        limit_ui: int = 300,
    ) -> Dict[str, Any]:
        """
        Atalho: importa os SPEDs e dispara a fase A do pós.
        Se voltar 'needs_input', o Controller de UI abre a janela e,
        depois do salvamento, chame pos_finalizar().
        """
        imp = self.importar_speds(empresa_id, caminhos)
        pos = self.pos_preparar(empresa_id, periodos=periodos, limit_ui=limit_ui)
        return {"importacao": imp, "pos": pos}