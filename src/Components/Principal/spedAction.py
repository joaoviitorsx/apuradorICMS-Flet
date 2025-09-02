import flet as ft
from ...Controllers.spedController import SpedController
from ...Components.notificao import notificacao
from ...Config.Database.db import getSession
from ...Components.Dialogs.confirmacao import confirmacao
from src.Utils.event import EventBus

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

    def on_aliquotas_finalizadas(data):
        sucesso = data.get('sucesso', False)
        mensagem = data.get('mensagem', '')
        
        if sucesso:
            notificacao(page, "Processamento concluído", f"SPED processado com sucesso!", tipo="sucesso")
            refs['arquivos_sped'] = []
            refs['caminho_arquivo'] = None
            from ...Components.Principal.cardPrincipal import atualizarListaArquivos
            atualizarListaArquivos(refs, [])
        else:
            notificacao(page, "❌ Erro no processamento", mensagem, tipo="erro")
        
        if refs.get('progress') and refs['progress'].current:
            refs['progress'].current.visible = False
        if refs.get('status_text') and refs['status_text'].current:
            refs['status_text'].current.value = ""
        page.update()
        
        EventBus.off('aliquotas_finalizadas', on_aliquotas_finalizadas)

    try:
        if refs.get('progress') and refs['progress'].current:
            refs['progress'].current.visible = True
        if refs.get('status_text') and refs['status_text'].current:
            refs['status_text'].current.value = "Processando SPED..."
        page.update()

        notificacao(page, "Iniciando processamento", "O processamento do SPED foi iniciado.", tipo="info")
        resultado = await controller.processarSped(refs['caminho_arquivo'], empresa_id, False)
        print(f"[DEBUG] Resultado do processamento: {resultado}")

        if resultado.get("status") == "existe":
            def confirmar_softdelete(e):
                page.dialog.open = False
                page.update()
                async def processar_forcado():
                    resultado_forcado = await controller.processarSped(refs['caminho_arquivo'], empresa_id, True)
                    await processoFinalizado(resultado_forcado, page, refs)
                page.run_task(processar_forcado)

            def cancelar_softdelete(e):
                page.dialog.open = False
                page.update()
                notificacao(page, "Processamento cancelado", "Nenhuma alteração foi feita.", tipo="alerta")

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Dados já existentes"),
                content=ft.Text(
                    f"{resultado.get('mensagem', 'Já existem dados para este período.')}\n\n"
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_softdelete),
                    ft.ElevatedButton("Sobrescrever", on_click=confirmar_softdelete)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            page.overlay.append(dialog)
            page.dialog = dialog
            dialog.open = True
            page.update()
            return

        if resultado.get("status") == "pendente_aliquota":
            print("[DEBUG] Detectado alíquotas pendentes, abrindo popup...")
            
            EventBus.on('aliquotas_finalizadas', on_aliquotas_finalizadas)
            from ...Interface.telaPopupAliquota import mostrarTelaPoupAliquota
            
            mostrarTelaPoupAliquota(
                page=page,
                empresa_id=empresa_id,
                itens=resultado.get("dados", []),
                etapa_pos=resultado.get("etapa_pos", None)
            )
            
            notificacao(page,"Alíquotas pendentes", "Configure as alíquotas dos produtos para continuar o processamento.",tipo="alerta") 
            return

        await processoFinalizado(resultado, page, refs, session)

    except Exception as e:
        print(f"[DEBUG] Exceção no processamento: {e}")
        notificacao(page, "Erro", f"Erro durante o processamento: {str(e)}", tipo="erro")
    
    finally:
        if resultado.get("status") != "pendente_aliquota":
            if refs.get('progress') and refs['progress'].current:
                refs['progress'].current.visible = False
            if refs.get('status_text') and refs['status_text'].current:
                refs['status_text'].current.value = ""
            page.update()
        if session:
            session.close()

async def processoFinalizado(resultado, page, refs):
    from ...Components.Principal.cardPrincipal import atualizarListaArquivos
    
    if resultado.get("status") == "ok":
        notificacao(page, "Sucesso", f"SPED processado com sucesso!", tipo="sucesso")
        refs['arquivos_sped'] = []
        refs['caminho_arquivo'] = None
        atualizarListaArquivos(refs, [])
    else:
        notificacao(page, "❌ Erro", resultado.get("mensagem", "Erro desconhecido durante o processamento."), tipo="erro")