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
