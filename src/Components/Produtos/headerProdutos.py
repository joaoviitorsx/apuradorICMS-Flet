import flet as ft
from .CrudAction import adicionarProduto, buscarCategoriasFiscais
from .importarProdutosAction import importarProdutos
from .exportarProdutosAction import exportarProdutos

def headerProdutos(page: ft.Page, refs: dict, theme: dict, empresa_id: int = None, empresa_nome: str = "") -> ft.Container:
    categorias = buscarCategoriasFiscais(empresa_id)
    opcoes_categoria = [ft.dropdown.Option("", "Todas as categorias")]
    opcoes_categoria.extend([ft.dropdown.Option(cat, cat) for cat in categorias])
    
    def aplicar_filtros(e):
        if "atualizar_tabela" in refs:
            refs["atualizar_tabela"]()
    
    def handleAdicionarProduto(e):
        adicionarProduto(page, theme, empresa_id, refs)
    
    def handleImportarProduto(e):
        importarProdutos(page, empresa_id, refs)
    
    def handleExportarProduto(e):
        exportarProdutos(page, empresa_id)

    return ft.Container(
        padding=20,
        bgcolor=theme["CARD"],
        border_radius=8,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            spacing=16,
            controls=[
                # Título e subtítulo
                ft.Column([
                    ft.Text("Gerenciador de Produtos", size=20, weight=ft.FontWeight.BOLD, color=theme["TEXT"]),
                    ft.Text("Empresa: " + (empresa_nome if empresa_nome else "Empresa"), size=14, color=theme["TEXT_SECONDARY"]),
                    ft.Text("Filtre e gerencie os produtos cadastrados no banco de dados", size=14, color=theme["TEXT_SECONDARY"])
                ]),
                
                # Filtros e botões
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # Filtros
                        ft.Row([
                            ft.TextField(
                                ref=refs.setdefault("input_filtro", ft.Ref[ft.TextField]()),
                                width=300,
                                hint_text="Filtrar por nome, código ou NCM",
                                on_change=aplicar_filtros
                            ),
                            ft.Container(width=8),
                            ft.Dropdown(
                                ref=refs.setdefault("dropdown_categoria", ft.Ref[ft.Dropdown]()),
                                width=250,
                                hint_text="Filtrar por categoria",
                                options=opcoes_categoria,
                                on_change=aplicar_filtros
                            )
                        ], spacing=12),
                        
                        # Botões de ação
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.ElevatedButton(
                                    text="Adicionar Produto",
                                    icon="ADD",
                                    width=160,
                                    height=48,
                                    bgcolor=theme["PRIMARY_COLOR"],
                                    color=theme["ON_PRIMARY"],
                                    on_click=handleAdicionarProduto,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=6)
                                    )
                                ),
                                ft.ElevatedButton(
                                    text="Exportar Tributação",
                                    icon="FILE_DOWNLOAD_OUTLINED",
                                    width=160,
                                    height=48,
                                    bgcolor=theme["SUCCESS_COLOR"] if "SUCCESS_COLOR" in theme else theme["PRIMARY_COLOR"],
                                    color=theme["ON_PRIMARY"],
                                    on_click=handleExportarProduto,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=6)
                                    )
                                ),
                                ft.ElevatedButton(
                                    text="Importar Tributação",
                                    icon="FILE_UPLOAD_OUTLINED",
                                    width=160,
                                    height=48,
                                    bgcolor=theme["WARNING_COLOR"] if "WARNING_COLOR" in theme else theme["PRIMARY_COLOR"],
                                    color=theme["ON_PRIMARY"],
                                    on_click=handleImportarProduto,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=6)
                                    ),
                                ),
                            ]
                        )
                    ]
                )
            ]
        )
    )