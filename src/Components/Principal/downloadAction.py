import os
import flet as ft
from flet import FilePickerResultEvent
from src.Components.notificao import notificacao
from src.Controllers.exportarController import ExportarController

def baixarAction(page: ft.Page, empresa_id: int, mes, ano, empresa_nome, file_picker: ft.FilePicker):
    print("🚀 Iniciando download...")

    meses = {
        "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
        "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
        "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
    }

    if not mes or not ano:
        notificacao(page, "Período não informado", "Selecione o mês e ano antes de prosseguir.", tipo="alerta")
        return

    mes_num = meses.get(mes)
    if not mes_num:
        notificacao(page, "Mês inválido", "Selecione um mês válido.", tipo="erro")
        return

    periodo = f"{mes_num}/{ano}"
    print(f"[DEBUG] Período montado: {periodo}")

    def on_save(e: FilePickerResultEvent):
        if not e.path:
            print("[DEBUG] Caminho de salvamento não selecionado.")
            return
        
        caminho = e.path if e.path.lower().endswith(".xlsx") else e.path + ".xlsx"

        async def run():
            resultado = await ExportarController.exportarPlanilha(page, empresa_id, periodo, caminho)

            if resultado["status"] == "ok":
                def abrir_planilha(e):
                    os.startfile(resultado["caminho_arquivo"])
                    dialog.open = False
                    page.update()

                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Exportação concluída"),
                    content=ft.Text(f"Planilha exportada com sucesso!\nAbrir agora?"),
                    actions=[
                        ft.TextButton("Abrir", on_click=abrir_planilha),
                        ft.TextButton("Fechar", on_click=lambda e: (setattr(dialog, "open", False), page.update()))
                    ],
                    open=True
                )
                page.dialog.append(dialog)
                page.dialog = dialog
                dialog.open = True
                page.update()

            elif resultado["status"] == "vazio":
                notificacao(page, "Sem dados", resultado["mensagem"], tipo="alerta")
            else:
                notificacao(page, "Erro", resultado["mensagem"], tipo="erro")

        page.run_task(run)

    nomeArquivo = f"Tributação da {empresa_nome}.xlsx"

    file_picker.on_result = on_save
    file_picker.save_file(dialog_title="Salvar planilha de exportação",file_name=nomeArquivo,allowed_extensions=["xlsx"])
        
        
        
    