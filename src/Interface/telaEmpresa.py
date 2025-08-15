import flet as ft
from src.Config.theme import apply_theme
from src.Components.Empresa.empresaCard import construir_card_empresa
from src.Components.Empresa.empresaAction import on_empresa_change, on_entrar_click, on_cadastrar_click
from src.Components.Empresa.empresaServiceUI import obter_dropdown_options

def TelaEmpresa(page: ft.Page) -> ft.View:
    theme = apply_theme(page)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    selected_empresa = ft.Ref[ft.Dropdown]()
    btn_entrar = ft.Ref[ft.ElevatedButton]()
    dropdown_options = obter_dropdown_options(page)

    card = construir_card_empresa(
        theme=theme,
        selected_empresa=selected_empresa,
        btn_entrar=btn_entrar,
        dropdown_options=dropdown_options,
        on_empresa_change=lambda e: on_empresa_change(btn_entrar, selected_empresa, page),
        on_entrar_click=lambda e: on_entrar_click(selected_empresa, page),
        on_cadastrar_click=lambda e: on_cadastrar_click(page)
    )

    return ft.View(
        route="/empresa",
        controls=[card],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=theme["BACKGROUNDSCREEN"],
    )
