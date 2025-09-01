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
        from ...Components.Principal.cardPrincipal import atualizarListaArquivos
        atualizarListaArquivos(refs, refs['arquivos_sped'])
        page.update()

        refs['caminho_arquivo'] = e.files[0].path

    file_picker.on_result = on_file_result
    file_picker.pick_files(allow_multiple=True, allowed_extensions=["txt"], dialog_title="Selecionar SPED")

async def processarSped(page: ft.Page, empresa_id: int, refs: dict):
    if not refs.get('caminho_arquivo'):
        notificacao(page, "Erro", "Nenhum arquivo selecionado para processamento.", tipo="erro")
        return

    session = getSession()
    controller = SpedController(session)

    try:
        if refs.get('progress') and refs['progress'].current:
            refs['progress'].current.visible = True
        if refs.get('status_text') and refs['status_text'].current:
            refs['status_text'].current.value = "Processando SPED..."
        page.update()

        resultado = await controller.processarSped(refs['caminho_arquivo'], empresa_id, False)

        print(f"[DEBUG] Resultado do processamento: {resultado}")

        if resultado.get("status") == "existe":
            def confirmar_sobrescrever(e):
                async def processar_forcado():
                    resultado_forcado = await controller.processarSped(refs['caminho_arquivo'], empresa_id, True)
                    await processoFinalizado(resultado_forcado, page, refs)
                
                page.run_task(processar_forcado)
                page.dialog.open = False
                page.update()
            
            confirmacao(
                page,
                "Período já processado",
                resultado.get("mensagem", "Já existem dados para este período."),
                confirmar_sobrescrever
            )
            return

        if resultado.get("status") == "pendente_aliquota":
            notificacao(
                page, 
                "Alíquotas pendentes", 
                "Existem produtos sem alíquota definida. Configure as alíquotas antes de continuar.", 
                tipo="alerta"
            )
            return

        await processoFinalizado(resultado, page, refs)

    except Exception as e:
        print(f"[DEBUG] Exceção no processamento: {e}")
        notificacao(page, "Erro", f"Erro durante o processamento: {str(e)}", tipo="erro")
    
    finally:
        # Esconder progress bar
        if refs.get('progress') and refs['progress'].current:
            refs['progress'].current.visible = False
        if refs.get('status_text') and refs['status_text'].current:
            refs['status_text'].current.value = ""
        page.update()
        session.close()

async def processoFinalizado(resultado, page, refs):
    from ...Components.Principal.cardPrincipal import atualizarListaArquivos
    if resultado.get("status") == "ok":
        notificacao(
            page,
            "Sucesso",
            f"SPED processado com sucesso! {resultado.get('mensagem', '')}",
            tipo="sucesso"
        )
        refs['arquivos_sped'] = []
        atualizarListaArquivos(refs, [])
    else:
        notificacao(
            page,
            "Erro",
            resultado.get("mensagem", "Erro desconhecido durante o processamento."),
            tipo="erro"
        )