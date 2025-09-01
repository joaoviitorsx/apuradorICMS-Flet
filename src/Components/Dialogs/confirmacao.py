import flet as ft

def confirmacao(page: ft.Page,titulo: str,mensagem: str,ao_confirmar: callable,ao_cancelar: callable = None,texto_confirmar: str = "Sim",texto_cancelar: str = "Não"):
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo, weight=ft.FontWeight.BOLD, size=18),
        content=ft.Text(mensagem),
        actions=[
            ft.TextButton(
                texto_cancelar,
                on_click=lambda e: (
                    page.dialog.close(),
                    page.update(),
                    ao_cancelar() if ao_cancelar else None
                )
            ),
            ft.ElevatedButton(
                texto_confirmar,
                on_click=lambda e: (
                    page.dialog.close(),
                    page.update(),
                    ao_confirmar()
                )
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.dialog = dialog
    page.dialog.open = True
    page.update()

def dialogo_sucesso_com_arquivo(page: ft.Page, titulo: str, mensagem: str, caminho_arquivo: str, ao_abrir: callable = None, ao_fechar: callable = None):
    """Diálogo de sucesso com opção de abrir arquivo"""
    def abrir_arquivo(e):
        try:
            if ao_abrir:
                ao_abrir(caminho_arquivo)
            else:
                # Comportamento padrão: abrir arquivo
                import os
                os.startfile(caminho_arquivo)
        except Exception as ex:
            print(f"[DEBUG] Erro ao abrir arquivo: {ex}")
            from ..notificao import notificacao
            notificacao(page, "Erro", "Não foi possível abrir o arquivo automaticamente.", tipo="erro")
        finally:
            fechar_dialog(page)

    def apenas_fechar(e):
        fechar_dialog(page)
        if ao_fechar:
            ao_fechar()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo, weight=ft.FontWeight.BOLD, size=18),
        content=ft.Text(mensagem),
        actions=[
            ft.TextButton(
                "Fechar",
                on_click=apenas_fechar
            ),
            ft.ElevatedButton(
                "Abrir Arquivo",
                on_click=abrir_arquivo,
                icon="OPEN_IN_NEW"
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    abrir_dialog(page, dialog)

def abrir_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Abrir diálogo de forma consistente"""
    page.dialog = dialog
    page.dialog.open = True
    page.update()

def fechar_dialog(page: ft.Page):
    """Fechar diálogo de forma consistente"""
    if page.dialog:
        page.dialog.open = False
        page.update()