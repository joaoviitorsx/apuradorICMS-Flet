import asyncio
import flet as ft
from src.Controllers.spedController import SpedController
from src.Components.notificao import notificacao
from src.Interface.telaPopupAliquota import abrir_dialogo_aliquotas

def inserir_sped(page: ft.Page, empresa_id: int, refs: dict, file_picker: ft.FilePicker):
    def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            notificacao(page, "Arquivo não selecionado", "Por favor, selecione um arquivo SPED.", tipo="alerta")
            return
        caminho = e.files[0].path
        processar_sped(caminho)

    def processar_sped(caminho: str):
        async def _run():
            try:
                refs['progress'].current.visible = True
                refs['status_text'].current.value = "Importando SPED..."
                page.update()
                loop = asyncio.get_running_loop()

                def processar():
                    ctrl = SpedController()
                    return ctrl.processar_sped_completo(caminho, empresa_id)

                resultado = await loop.run_in_executor(None, processar)

                periodo = resultado.get("periodo", "")
                faltantes = resultado.get("aliquotas_faltantes", 0)

                if resultado.get("status") == "ok":
                    if faltantes > 0:
                        faltantes_lista = resultado.get("faltantes_lista", [])
                        notificacao(page, "SPED importado com pendências",
                                    f"{faltantes} alíquotas pendentes para o período {periodo}", tipo="alerta")

                        async def continuar():
                            refs['status_text'].current.value = "Finalizando processamento..."
                            page.update()
                            def finalizar():
                                ctrl = SpedController()
                                return ctrl.pos_finalizar(empresa_id, [periodo])
                            resultado_final = await loop.run_in_executor(None, finalizar)
                            if resultado_final.get("status") == "ok":
                                notificacao(page, "Concluído", f"Finalizado com sucesso para {periodo}", tipo="sucesso")
                            else:
                                notificacao(page, "Erro", resultado_final.get("mensagem", "Erro na finalização"), tipo="erro")
                            refs['progress'].current.visible = False
                            refs['status_text'].current.value = ""
                            page.update()

                        abrir_dialogo_aliquotas(page, empresa_id, faltantes_lista, True, continuar)
                        return
                    else:
                        def finalizar():
                            ctrl = SpedController()
                            return ctrl.pos_finalizar(empresa_id, [periodo])
                        resultado_final = await loop.run_in_executor(None, finalizar)
                        if resultado_final.get("status") == "ok":
                            notificacao(page, "Concluído", f"SPED finalizado com sucesso para {periodo}", tipo="sucesso")
                        else:
                            notificacao(page, "Erro", resultado_final.get("mensagem", "Erro ao finalizar"), tipo="erro")
                else:
                    notificacao(page, "Erro", resultado.get("mensagem", "Erro na importação"), tipo="erro")
            except Exception as e:
                notificacao(page, "Erro crítico", str(e), tipo="erro")
            finally:
                refs['progress'].current.visible = False
                refs['status_text'].current.value = ""
                page.update()

        page.run_task(_run)

    file_picker.on_result = on_file_result
    file_picker.pick_files(allowed_extensions=["txt"], dialog_title="Selecionar SPED")