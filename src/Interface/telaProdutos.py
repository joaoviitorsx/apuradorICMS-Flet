import flet as ft
from src.Config.theme import apply_theme
from src.Components.Produtos.headerProdutos import headerProdutos
from src.Components.Produtos.tabelaProdutos import cardTabelaProdutos

def TelaProdutos(page: ft.Page, empresa_id: int, empresa_nome: str = "") -> ft.View:
    theme = apply_theme(page)
    refs = {}
    
    return ft.View(
        route="/produtos",
        bgcolor=theme["BACKGROUNDSCREEN"],
        scroll=ft.ScrollMode.AUTO,
        controls=[
            # Botão de voltar
            ft.Container(
                padding=ft.padding.only(left=20, top=20),
                content=ft.ElevatedButton(
                    text="Voltar",
                    icon="ARROW_BACK",
                    bgcolor=theme["BORDER"],
                    color=theme["TEXT"],
                    on_click=lambda e: page.go(f"/principal?id={empresa_id}&nome={empresa_nome}") if empresa_id else page.go("/empresa")
                )
            ),
            
            ft.Container(
                padding=20,
                content=ft.Column(
                    spacing=24,
                    controls=[
                        headerProdutos(page, refs, theme, empresa_id, empresa_nome),
                        cardTabelaProdutos(page, refs, theme, empresa_id)
                    ]
                )
            )
        ]
    )