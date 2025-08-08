import flet as ft
from src.Config.theme import apply_theme, STYLE

def get_mock_produtos():
    return [
        {"id": 1, "codigo": "0000000000032", "nome": "EXT DE TOMATE FUGINI 300G", "ncm": "20021000", "aliquota": "4,00%", "categoria": "20% Regra Geral"},
        {"id": 2, "codigo": "0000000000079", "nome": "KAPO MORANGO 200ML", "ncm": "22021000", "aliquota": "4,00%", "categoria": "20% Regra Geral"},
        {"id": 3, "codigo": "0000000000112", "nome": "PAO DE LEITE ESP REAL PAN 400G", "ncm": "19052090", "aliquota": "ST", "categoria": "20% Regra Geral"},
        {"id": 4, "codigo": "0000000000493", "nome": "UVA PASSA KG", "ncm": "08062000", "aliquota": "ST", "categoria": "28% Bebida Alcoólica"},
        {"id": 5, "codigo": "0000000000495", "nome": "UVA ROXA KG", "ncm": "08061000", "aliquota": "ISENTO", "categoria": "12% Cesta Basica"},
    ]

def get_produtos_dialog(page):
    theme = apply_theme(page)
    produtos = get_mock_produtos()
    search = ft.Ref[ft.TextField]()
    categoria_filter = ft.Ref[ft.Dropdown]()
    produtos_list = ft.Ref[ft.DataTable]()

    def atualizar_lista(e=None):
        termo = (search.current.value or "").lower()
        categoria = categoria_filter.current.value

        produtos_filtrados = [
            p for p in produtos
            if termo in p["nome"].lower()
            and (categoria is None or p["categoria"] == categoria)
        ]

        produtos_list.current.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(p["codigo"])),
                    ft.DataCell(ft.Text(p["nome"])),
                    ft.DataCell(ft.Text(p["ncm"])),
                    ft.DataCell(ft.Text(p["aliquota"])),
                    ft.DataCell(ft.Text(p["categoria"]))
                ]
            ) for p in produtos_filtrados
        ]
        page.update()

    def fechar_dialogo(e=None):
        page.close(dialogo)

    dialogo = ft.AlertDialog(
        modal=True,
        content=ft.Container(
            width=900,
            height=600,
            padding=20,
            bgcolor=theme["CARD"],
            border_radius=STYLE["CARD_RADIUS"],
            content=ft.Column(
                expand=True,
                spacing=20,
                controls=[
                    ft.Text("Gerenciar Produtos e Tributação", size=18, weight=ft.FontWeight.BOLD, color=theme["TEXT"]),
                    ft.Row(
                        controls=[
                            ft.TextField(
                                ref=search,
                                hint_text="Buscar por produto...",
                                expand=True,
                                on_change=atualizar_lista,
                                bgcolor=theme["INPUT_BG"],
                                border_color=theme["BORDER"]
                            ),
                            ft.Dropdown(
                                ref=categoria_filter,
                                hint_text="Filtrar por categoria...",
                                options=[
                                    ft.dropdown.Option("20% Regra Geral"),
                                    ft.dropdown.Option("28% Bebida Alcoólica"),
                                    ft.dropdown.Option("12% Cesta Basica")
                                ],
                                on_change=atualizar_lista,
                                bgcolor=theme["INPUT_BG"],
                                border_color=theme["BORDER"]
                            )
                        ]
                    ),
                    ft.DataTable(
                        ref=produtos_list,
                        columns=[
                            ft.DataColumn(ft.Text("Código")),
                            ft.DataColumn(ft.Text("Produto")),
                            ft.DataColumn(ft.Text("NCM")),
                            ft.DataColumn(ft.Text("Alíquota")),
                            ft.DataColumn(ft.Text("Categoria"))
                        ],
                        rows=[],
                        expand=True
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        controls=[
                            ft.ElevatedButton(text="Adicionar", bgcolor="green", color="white", icon="ADD"),
                            ft.ElevatedButton(text="Editar", bgcolor="blue", color="white", icon="EDIT"),
                            ft.ElevatedButton(text="Excluir", bgcolor="red", color="white", icon="DELETE")
                        ]
                    )
                ]
            )
        ),
        actions=[ft.TextButton("Fechar", on_click=fechar_dialogo)],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    atualizar_lista()

    return dialogo
