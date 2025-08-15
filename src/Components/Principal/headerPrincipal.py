import flet as ft

def construir_header_principal(on_voltar, on_configurar, theme):
    return ft.Container(
        padding=ft.Padding(0, 8, 0, 8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon="ARROW_BACK", on_click=on_voltar, icon_color=theme["PRIMARY_COLOR"]),
                ft.IconButton(icon="SETTINGS", on_click=on_configurar, icon_color=theme["PRIMARY_COLOR"]),
            ]
        )
    )