import asyncio
import flet as ft
from src.Controllers.tributacaoController import TributacaoController
from src.Components.notificao import notificacao
from src.Interface.telaPopupAliquota import abrir_dialogo_aliquotas

def enviar_tributacao(page: ft.Page, empresa_id: int, refs: dict, file_picker: ft.FilePicker):
    def on_file_selected(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        caminho = e.files[0].path
        refs['nome_arquivo'].current.value = e.files[0].name
        refs['status_envio'].current.value = "Processando planilha..."
        refs['status_text'].current.value = "Lendo dados da planilha de tributação..."
        refs['progress'].current.visible = True
        page.update()

        async def importar():
            try:
                loop = asyncio.get_running_loop()
                notificacao(page, "Importando Planilha", "Iniciando importação da planilha...", tipo="info")

                resultado = await loop.run_in_executor(
                    None, TributacaoController.cadastrar_tributacao_por_planilha, caminho, empresa_id
                )

                refs['progress'].current.visible = False
                refs['status_text'].current.value = ""

                if resultado.get("status") == "ok":
                    cadastrados = resultado.get("cadastrados", 0)
                    ja_existiam = resultado.get("ja_existiam", 0)
                    faltantes_restantes = resultado.get("faltantes_restantes", 0)
                    erros = resultado.get("erros", [])

                    refs['status_envio'].current.value = f"{cadastrados} inseridos | {ja_existiam} já existiam"
                    notificacao(
                        page,
                        "Importação Concluída",
                        f"• {cadastrados} novos\n• {ja_existiam} já existiam\n• Faltantes de alíquota: {faltantes_restantes}",
                        tipo="sucesso" if cadastrados else "alerta",
                    )

                    if faltantes_restantes > 0:
                        abrir_dialogo_aliquotas(page, empresa_id, itens=None, finalizar_apos_salvar=True)

                    if erros:
                        resumo = "\n".join([f"• Linha {err['linha']}: {err['erro']}" for err in erros[:3]])
                        if len(erros) > 3:
                            resumo += f"\n• ... e mais {len(erros)-3} erro(s)"
                        notificacao(page, f"{len(erros)} Registro(s) Ignorado(s)", resumo, tipo="alerta")
                else:
                    refs['status_envio'].current.value = "❌ Erro ao processar planilha"
                    notificacao(page, "Erro no Processamento", resultado.get("mensagem", "Erro desconhecido"), tipo="erro")
            except Exception as ex:
                refs['progress'].current.visible = False
                refs['status_envio'].current.value = "❌ Falha inesperada"
                notificacao(page, "Erro Crítico", f"Erro inesperado: {ex}", tipo="erro")
            finally:
                page.update()

        page.run_task(importar)

    file_picker.on_result = on_file_selected
    file_picker.pick_files(allowed_extensions=["xlsx"], dialog_title="Selecionar planilha")