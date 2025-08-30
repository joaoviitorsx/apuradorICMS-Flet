import asyncio
import flet as ft

from ...Controllers.spedController import SpedController
from ...Components.notificao import notificacao
from ...Config.Database.db import getSession
from ...Components.Dialogs.confirmacao import confirmacao

def inserirSped(page: ft.Page, empresa_id: int, refs: dict, file_picker: ft.FilePicker):
    def on_file_result(e: ft.FilePickerResultEvent):

        if not e.files:
            notificacao(page, "Arquivo não selecionado", "Por favor, selecione um arquivo SPED.", tipo="alerta")
            return

        refs['arquivos_sped'] = [f.name for f in e.files]
        page.update()

        caminho_arquivo = e.files[0].path

        async def run():
            await processarSped(caminho_arquivo, empresa_id, page, refs)

        page.run_task(run)

    async def processarSped(caminho_arquivo: str, empresa_id: int, page: ft.Page, refs: dict, forcar=False):
        session = getSession()
        controller = SpedController(session)

        try:
            refs['progress'].current.visible = True
            refs['status_text'].current.value = "Processando SPED..."
            page.update()

            resultado = await controller.processarSped(caminho_arquivo, empresa_id, forcar)

            print(f"[DEBUG] Resultado do processamento: {resultado}")

            if resultado.get("status") == "existe":
                periodo = resultado.get("periodo", "desconhecido")
                mensagem = resultado.get("mensagem", f"Já existem dados para o período {periodo}.")

                def ao_confirmar():
                    async def run():
                        await processarSped(caminho_arquivo, empresa_id, page, refs, forcar=True)
                    page.run_task(run)

                confirmacao(
                    page=page,
                    titulo="Período já processado",
                    mensagem=mensagem,
                    ao_confirmar=ao_confirmar
                )
                return
            
            if resultado.get("status") == "pendente_aliquota":
                notificacao(page, "Ação necessária", "Existem produtos sem alíquota. Preencha antes de continuar.", tipo="alerta")
                from src.Interface.telaPopupAliquota import mostrarTelaPoupAliquota
                mostrarTelaPoupAliquota(
                    page,
                    resultado["empresa_id"],
                    resultado["dados"],
                    resultado["etapa_pos"]
                )
                return

            if resultado.get("status") == "ok":
                notificacao(page, "Sucesso", resultado.get("mensagem", "SPED importado com sucesso."), tipo="sucesso")
            else:
                notificacao(page, "Erro", resultado.get("mensagem", "Erro ao importar SPED."), tipo="erro")

        except Exception as e:
            print(f"[DEBUG] Exceção no processamento: {e}")
            notificacao(page, "Erro crítico", str(e), tipo="erro")

        finally:
            refs['progress'].current.visible = False
            refs['status_text'].current.value = ""
            page.update()

    file_picker.on_result = on_file_result
    file_picker.pick_files(allow_multiple=True, allowed_extensions=["txt"], dialog_title="Selecionar SPED")