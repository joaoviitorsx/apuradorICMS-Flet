import flet as ft

def headerPrincipal(on_voltar, on_gerenciar_produtos, theme, empresa_nome: str, produtos_qtd: int):
    return ft.Container(
        width=680,
        padding=25,
        bgcolor=theme["ON_PRIMARY"],
        border_radius=8,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=30,
            color=theme["BORDER"],
            offset=ft.Offset(0, 4)
        ),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,  # Menor spacing
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(
                            icon="ARROW_BACK",
                            icon_color=theme["PRIMARY_COLOR"],
                            on_click=on_voltar,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                        ),
                        ft.Column(
                            spacing=0,  # Sem spacing extra
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Text(empresa_nome, weight=ft.FontWeight.W_600, size=16),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Row([
                                            ft.Icon(name="inventory_2", size=14, color=theme["TEXT_SECONDARY"]),
                                            ft.Text(f"{produtos_qtd} produtos cadastrados", size=12, color=theme["TEXT_SECONDARY"])
                                        ])
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                ft.ElevatedButton(
                    text="Produtos",
                    icon="INVENTORY_2",
                    icon_color=theme["PRIMARY_COLOR"],
                    color=theme["PRIMARY_COLOR"],
                    bgcolor=theme["ON_PRIMARY"],
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        shape=ft.RoundedRectangleBorder(radius=6),
                        side=ft.BorderSide(1, theme["PRIMARY_COLOR"])
                    ),
                    on_click=on_gerenciar_produtos
                )
            ]
        )
    )