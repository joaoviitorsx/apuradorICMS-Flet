import asyncio
import flet as ft
from ...Controllers.spedController import SpedController
from ...Components.notificao import notificacao
from ...Config.Database.db import getSession
from ...Components.Dialogs.confirmacao import confirmacao
from src.Utils.event import EventBus

def estados(refs, estado: str, page: ft.Page):
    progress = refs.get("progress")
    status_text = refs.get("status_text")
    botao_processar = refs.get("botao_processar")
    botao_reload = refs.get("botao_reload")

    if estado == "iniciar":
        if progress and progress.current:
            progress.current.visible = True
            progress.current.value = None
            progress.current.update()
        if status_text and status_text.current:
            status_text.current.value = "Iniciando Leitura do SPED..."
            status_text.current.update()
        if botao_processar and botao_processar.current:
            botao_processar.current.disabled = True
            botao_processar.current.update()

        if botao_reload and botao_reload.current:
            botao_reload.current.disabled = True
            botao_reload.current.update()

    elif estado == "processando":
        if progress and progress.current:
            progress.current.value = None
            progress.current.update()
        if status_text and status_text.current:
            status_text.current.value = "Processando arquivos SPED..."
            status_text.current.update()

    elif estado == "aguardando_aliquotas":
        if status_text and status_text.current:
            status_text.current.value = "Aguardando configuração de alíquotas..."
            status_text.current.update()

    elif estado == "finalizado" or estado == "erro":
        if progress and progress.current:
            progress.current.visible = False
            progress.current.update()
        if status_text and status_text.current:
            status_text.current.value = ""
            status_text.current.update()
        if botao_processar and botao_processar.current:
            botao_processar.current.disabled = False
            botao_processar.current.update()

        if botao_reload and botao_reload.current:
            botao_reload.current.disabled = False
            botao_reload.current.update()

    page.update()

def inserirSped(page: ft.Page, empresa_id: int, refs: dict, file_picker: ft.FilePicker):
    def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            notificacao(page, "Arquivo não selecionado", "Por favor, selecione um arquivo SPED.", tipo="alerta")
            return

        refs['arquivos_sped'] = [f.name for f in e.files]
        refs['caminhos_arquivos'] = [f.path for f in e.files]

        from ...Components.Principal.cardPrincipal import atualizarListaArquivos
        atualizarListaArquivos(refs, refs['caminhos_arquivos'])
        page.update()

    file_picker.on_result = on_file_result
    file_picker.pick_files(allow_multiple=True, allowed_extensions=["txt"], dialog_title="Selecionar SPED")

async def processarResultado(resultado: dict, page: ft.Page, empresa_id: int, refs: dict):
    print(f"[DEBUG processarResultado] Processando resultado: {resultado}")
    print(f"[DEBUG processarResultado] Status: {resultado.get('status')}")
    
    if resultado.get("status") == "pendente_aliquota":
        print("[DEBUG processarResultado] ✅ Status é pendente_aliquota - iniciando tratamento")
        
        estados(refs, "aguardando_aliquotas", page)
        notificacao(page, "Alíquotas pendentes", "Configure as alíquotas para continuar.", tipo="info")

        def onAliquotasFinalizadas(data):
            print("[DEBUG processarResultado] Evento 'aliquotas_finalizadas' recebido:", data)
            EventBus.off('aliquotas_finalizadas', onAliquotasFinalizadas)
            sucesso = data.get('sucesso', False)
            mensagem = data.get('mensagem', '')

            if sucesso:
                print("[DEBUG processarResultado] Alíquotas finalizadas com sucesso.")
                notificacao(page, "Processamento concluído", "SPED processado com sucesso!", tipo="sucesso")
                from ...Components.Principal.cardPrincipal import atualizarListaArquivos
                atualizarListaArquivos(refs, [])

                async def finalizarProcesso():
                    await processoFinalizado(resultado, page, refs)
                    
                    page.run_task(finalizarProcesso)
                
            else:
                print("[DEBUG processarResultado] Falha no processamento final após alíquotas:", mensagem)
                notificacao(page, "Erro no processamento", mensagem, tipo="erro")

            estados(refs, "finalizado", page)

        EventBus.on('aliquotas_finalizadas', onAliquotasFinalizadas)

        dados_pendentes = resultado.get("dados", [])
        print(f"[DEBUG processarResultado] Dados pendentes: {len(dados_pendentes)} itens")
        
        if not dados_pendentes:
            print("[ERRO processarResultado] ❌ Nenhum dado pendente encontrado!")
            notificacao(page, "Erro", "Nenhum dado pendente encontrado.", tipo="erro")
            estados(refs, "finalizado", page)
            return

        try:
            from ...Components.PoupAliquota.aliquotaDialog import abrirDialogoAliquotas
            resultado_popup = abrirDialogoAliquotas(
                page=page,
                empresa_id=empresa_id,
                itens=dados_pendentes,
                retornar_pos=True,
                etapa_pos=resultado.get("etapa_pos", 4)
            )
            
        except ImportError as ie:
            notificacao(page, "Erro", "Erro ao carregar interface de alíquotas.", tipo="erro")
            estados(refs, "finalizado", page)
            
        except Exception as pe:
            import traceback
            traceback.print_exc()
            notificacao(page, "Erro", f"Erro ao abrir popup de alíquotas: {str(pe)}", tipo="erro")
            estados(refs, "finalizado", page)
            
    else:
        await processoFinalizado(resultado, page, refs)

async def processarSped(page: ft.Page, empresa_id: int, refs: dict):
    print("[DEBUG processarSped] Iniciando processarSped()")
    
    if not refs.get('caminhos_arquivos'):
        print("[DEBUG processarSped] Nenhum arquivo selecionado")
        notificacao(page, "Erro", "Nenhum arquivo selecionado para processamento.", tipo="erro")
        return

    estados(refs, "iniciar", page)
    notificacao(page, "Iniciando processamento", "O processamento do SPED foi iniciado.", tipo="info")
    await asyncio.sleep(0.1)
    page.update()
    
    print("[DEBUG processarSped] Criando sessão e controller")
    session = getSession()
    controller = SpedController(session)

    estados(refs, "processando", page)
    await asyncio.sleep(0.1)
    page.update()

    try:
        print("[DEBUG processarSped] Chamando controller.processarSped()")
        resultado = await controller.processarSped(refs['caminhos_arquivos'], empresa_id, False)
        print(f"[DEBUG processarSped] Resultado do processamento: {resultado}")

        if resultado.get("status") == "existe":
            print("[DEBUG processarSped] Resultado indicou dados existentes (soft delete).")
            return await tratarSoftDelete(page, controller, empresa_id, refs, resultado)

        await processarResultado(resultado, page, empresa_id, refs)

    except Exception as e:
        import traceback
        traceback.print_exc()
        notificacao(page, "Erro", f"Ocorreu um erro: {str(e)}", tipo="erro")

    finally:
        print("[DEBUG processarSped] Encerrando processamento com session.close()")
        estados(refs, "finalizado", page)
        if session:
            session.close()

async def processoFinalizado(resultado, page, refs):
    print(f"[DEBUG processoFinalizado] Chamado com status: {resultado.get('status')}")
    
    if resultado.get("status") == "ok":
        notificacao(page, "Sucesso", "SPED processado com sucesso!", tipo="sucesso")
        from ...Components.Principal.cardPrincipal import resetarSelecaoArquivos
        from src.Config.theme import apply_theme
        empresa_id = refs.get("empresa_id")
        picker_sped = refs.get("picker_sped")

        if empresa_id and picker_sped:
            resetarSelecaoArquivos(refs, page, empresa_id, picker_sped, apply_theme(page))
    else:
        notificacao(page, "Erro", resultado.get("mensagem", "Erro desconhecido."), tipo="erro")

async def tratarSoftDelete(page, controller, empresa_id, refs, resultado):
    print("[DEBUG tratarSoftDelete] tratarSoftDelete chamado")
    
    def confirmar(e):
        print("[DEBUG tratarSoftDelete] Usuário confirmou sobrescrita")
        page.dialog.open = False
        page.update()

        async def reprocessar():
            print("[DEBUG tratarSoftDelete] Iniciando reprocessamento")
            estados(refs, "iniciar", page)
            notificacao(page, "Reprocessando", "Sobrescrevendo dados antigos...", tipo="info")
            await asyncio.sleep(0.1)

            nova_sessao = getSession()
            novo_controller = SpedController(nova_sessao)
            
            try:
                print("[DEBUG tratarSoftDelete] Chamando reprocessamento com forcar=True")
                resultado_final = await novo_controller.processarSped(refs['caminhos_arquivos'], empresa_id, True)
                print(f"[DEBUG tratarSoftDelete] Resultado do reprocessamento: {resultado_final}")
                
                await processarResultado(resultado_final, page, empresa_id, refs)
                
            except Exception as e:
                print(f"[ERRO tratarSoftDelete] Erro no reprocessamento: {e}")
                notificacao(page, "Erro", f"Erro no reprocessamento: {str(e)}", tipo="erro")
                estados(refs, "finalizado", page)
            finally:
                nova_sessao.close()

        page.run_task(reprocessar)

    def cancelar(e):
        print("[DEBUG tratarSoftDelete] Usuário cancelou sobrescrita")
        page.dialog.open = False
        notificacao(page, "Cancelado", "Processamento interrompido.", tipo="alerta")
        estados(refs, "finalizado", page)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Dados já existentes"),
        content=ft.Text(resultado.get("mensagem", "Já existem dados para este período.")),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar),
            ft.ElevatedButton("Sobrescrever", on_click=confirmar)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.dialog = dialog
    page.overlay.append(dialog)
    dialog.open = True
    page.update()