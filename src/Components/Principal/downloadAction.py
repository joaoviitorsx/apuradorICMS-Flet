import asyncio
import flet as ft
from src.Components.notificao import notificacao

def baixar_tabela(page: ft.Page, mes: str, ano: str, refs: dict):
    if not mes or not ano:
        notificacao(page, "Período não informado", "Selecione o mês e ano antes de prosseguir.", tipo="alerta")
        return

    meses = {
        "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
        "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
        "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
    }
    periodo = f"{ano}{meses[mes]}"

    async def _baixar():
        refs['progress'].current.visible = True
        refs['status_text'].current.value = "Verificando dados para download..."
        page.update()
        try:
            loop = asyncio.get_running_loop()
            def gerar_planilha():
                return {
                    "status": "ok",
                    "arquivo_gerado": f"resultado_ICMS_{periodo}.xlsx",
                    "mensagem": f"Planilha gerada para {mes}/{ano}"
                }
            resultado = await loop.run_in_executor(None, gerar_planilha)
            if resultado.get("status") == "ok":
                notificacao(page, "Download concluído", resultado["mensagem"], tipo="sucesso")
            else:
                notificacao(page, "Erro", "Não foi possível gerar a planilha.", tipo="erro")
        except Exception as e:
            notificacao(page, "Erro", f"Erro inesperado: {e}", tipo="erro")
        finally:
            refs['progress'].current.visible = False
            refs['status_text'].current.value = ""
            page.update()

    page.run_task(_baixar)