import flet as ft
from src.Config.theme import apply_theme
from src.Components.Cadastro.cadastroCard import construir_card_cadastro
from src.Components.Cadastro.cadastroAction import validar_e_cadastrar, voltar

def TelaCadastro(page: ft.Page) -> ft.View:
    theme = apply_theme(page)
    page.scroll = ft.ScrollMode.ADAPTIVE

    input_cnpj = ft.Ref[ft.TextField]()
    input_razao = ft.Ref[ft.TextField]()

    # Criação do card passando ações como lambdas
    card = construir_card_cadastro(
        theme=theme,
        input_cnpj=input_cnpj,
        input_razao=input_razao,
        on_voltar=lambda e: voltar(page),
        on_cadastrar=lambda e: validar_e_cadastrar(input_cnpj, input_razao, page)
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
