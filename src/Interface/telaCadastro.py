import flet as ft
from src.Config.theme import apply_theme
from src.Components.Cadastro.cadastroCard import cardCadastro
from src.Components.Cadastro.cadastroAction import validarCadastro, voltar

def TelaCadastro(page: ft.Page) -> ft.View:
    theme = apply_theme(page)
    page.scroll = ft.ScrollMode.ADAPTIVE

    input_cnpj = ft.Ref[ft.TextField]()

    card = cardCadastro(
        theme=theme,
        input_cnpj=input_cnpj,
        on_voltar=lambda e: voltar(page),
        on_cadastrar=lambda e: validarCadastro(input_cnpj, page)
    )

    return ft.View(
        route="/cadastro",
        controls=[
            ft.Column(
                controls=[card],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=theme["BACKGROUNDSCREEN"]
    )
