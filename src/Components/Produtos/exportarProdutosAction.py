import os
import subprocess
import flet as ft

from ...Controllers.exportarController import ExportarController
from ...Components.notificao import notificacao

def exportarProdutos(page: ft.Page, empresa_id: int = None):
    if not empresa_id:
        notificacao(page, "Erro", "ID da empresa não informado.", tipo="erro")
        return
    
    async def processar_exportacao(result):
        if result.path:
            try:
                notificacao(page, "Processando", "Gerando planilha de produtos...", tipo="info")
                
                resultado = await ExportarController.exportarProdutos(
                    empresa_id=empresa_id,
                    caminho=result.path
                )
                
                if resultado.get("status") == "ok":
                    notificacao(
                        page, 
                        "Sucesso", 
                        resultado.get("mensagem", "Planilha de produtos gerada com sucesso!"), 
                        tipo="sucesso"
                    )
                    
                    abrirModal(result.path)
                    
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
                notificacao(page, "Erro", f"Erro durante exportação: {str(e)}", tipo="erro")
    
    def abrirModal(caminho_arquivo):
        def abrir_arquivo(e):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(caminho_arquivo)
                elif os.name == 'posix':  # macOS e Linux
                    subprocess.run(['open', caminho_arquivo], check=True)
                else:
                    subprocess.run(['xdg-open', caminho_arquivo], check=True)
                
                fecharModal(e)
                
            except Exception as ex:
                notificacao(page, "Erro", f"Erro ao abrir arquivo: {str(ex)}", tipo="erro")
                fecharModal(e)
        
        def abrir_pasta(e):
            try:
                pasta = os.path.dirname(caminho_arquivo)
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', caminho_arquivo], check=True)
                elif os.name == 'posix':  # macOS e Linux
                    subprocess.run(['open', '-R', caminho_arquivo], check=True)
                else:
                    subprocess.run(['xdg-open', pasta], check=True)
                
                fecharModal(e)
                
            except Exception as ex:
                notificacao(page, "Erro", f"Erro ao abrir pasta: {str(ex)}", tipo="erro")
                fecharModal(e)
        
        def fecharModal(e):
            page.dialog.open = False
            page.update()
        
        nome_arquivo = os.path.basename(caminho_arquivo)
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Planilha Gerada com Sucesso!"),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Text(f"Arquivo: {nome_arquivo}"),
                    ft.Text(f"Local: {os.path.dirname(caminho_arquivo)}", size=12, color="grey"),
                    ft.Container(height=10),
                    ft.Text("O que você gostaria de fazer?")
                ], spacing=8)
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fecharModal),
                ft.ElevatedButton(
                    text="Abrir Pasta",
                    icon="FOLDER_OPEN",
                    on_click=abrir_pasta
                ),
                ft.ElevatedButton(
                    text="Abrir Arquivo",
                    icon="OPEN_IN_NEW",
                    on_click=abrir_arquivo
                )
            ]
        )
        
        page.dialog = modal
        modal.open = True
        page.update()
    
    try:
        picker = ft.FilePicker(on_result=processar_exportacao)
        page.overlay.append(picker)
        page.update()
        
        picker.save_file(
            dialog_title="Salvar planilha de produtos",
            file_name=f"produtos_empresa_{empresa_id}.xlsx",
            allowed_extensions=["xlsx"]
        )
        
    except Exception as e:
        notificacao(page, "Erro", f"Erro ao abrir diálogo: {str(e)}", tipo="erro")