import os
import subprocess
import flet as ft
from ...Controllers.exportarController import ExportarController
from ...Components.notificao import notificacao

def exportarProdutos(page: ft.Page, empresa_id: int = None):
    if not empresa_id:
        notificacao(page, "Erro", "ID da empresa não informado.", tipo="erro")
        return
    
    async def processarExportacao(caminho: str):
        try:
            print(f"[DEBUG] Iniciando exportação para: {caminho}")
        
            notificacao(page, "Processando", "Gerando planilha de produtos...", tipo="info")
            
            resultado = await ExportarController.exportarProdutos(empresa_id, caminho)
            
            print(f"[DEBUG] Resultado da exportação: {resultado}")
            
            if resultado.get("status") == "ok":
                notificacao(
                    page, 
                    "Sucesso", 
                    resultado.get("mensagem", "Planilha de produtos gerada com sucesso!"), 
                    tipo="sucesso"
                )
                
                abrirModalConfirmacao(caminho)
                
            elif resultado.get("status") == "vazio":
                notificacao(
                    page, 
                    "Aviso", 
                    resultado.get("mensagem", "Nenhum produto encontrado para exportação."), 
                    tipo="alerta"
                )
            else:
                notificacao(
                    page, 
                    "Erro", 
                    resultado.get("mensagem", "Erro ao gerar planilha de produtos."), 
                    tipo="erro"
                )
                
        except Exception as e:
            print(f"[ERRO] Erro na exportação: {e}")
            import traceback
            traceback.print_exc()
            notificacao(page, "Erro", f"Erro durante exportação: {str(e)}", tipo="erro")
    
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            async def wrapper():
                return await processarExportacao(e.path)
            
            page.run_task(wrapper)
    
    def abrirModalConfirmacao(caminho_arquivo: str):
        def abrir_arquivo(e):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(caminho_arquivo)
                
                fechar_modal(e)
                
            except Exception as ex:
                print(f"[ERRO] Erro ao abrir arquivo: {ex}")
                notificacao(page, "Erro", f"Erro ao abrir arquivo: {str(ex)}", tipo="erro")
                fechar_modal(e)
                
                fechar_modal(e)
                
            except Exception as ex:
                print(f"[ERRO] Erro ao abrir pasta: {ex}")
                notificacao(page, "Erro", f"Erro ao abrir pasta: {str(ex)}", tipo="erro")
                fechar_modal(e)
        
        def fechar_modal(e):
            page.dialog.open = False
            page.update()
        
        nome_arquivo = os.path.basename(caminho_arquivo)
        pasta = os.path.dirname(caminho_arquivo)
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Exportação Concluída", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text("Planilha de produtos gerada com sucesso!", size=16),
                    ft.Container(height=15),
                    ft.Text("O que você gostaria de fazer?", weight=ft.FontWeight.BOLD)
                ], spacing=4, tight=True)
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar_modal),
                ft.ElevatedButton(
                    text="Abrir Arquivo",
                    icon="OPEN_IN_NEW",
                    on_click=abrir_arquivo,
                    bgcolor="#4CAF50",
                    color="white"
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.overlay.append(modal)
        page.dialog = modal
        modal.open = True
        page.update()
    
    try:
        picker = ft.FilePicker(on_result=on_file_result)
        page.overlay.append(picker)
        page.update()
        
        picker.save_file(
            dialog_title="Salvar planilha de produtos",
            file_name=f"produtos_empresa_{empresa_id}.xlsx",
            allowed_extensions=["xlsx"]
        )
        
    except Exception as e:
        print(f"[ERRO] Erro ao abrir diálogo: {e}")
        notificacao(page, "Erro", f"Erro ao abrir diálogo: {str(e)}", tipo="erro")