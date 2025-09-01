import flet as ft
from src.Config.theme import apply_theme

from ...Components.Principal.spedAction import inserirSped, processarSped
from ...Components.Principal.downloadAction import baixarAction

def cardPrincipal(theme, empresa_nome: str, empresa_id: int, refs: dict, picker_sped: ft.FilePicker, picker_tabela: ft.FilePicker, page: ft.Page):
    return ft.Container(
        width=720,
        height=600,
        padding=30, 
        bgcolor=theme["CARD"],
        border_radius=12,
        animate_size=True,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Título principal card
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        ft.Image(src="src/Assets/icone/folder.svg", width=32, height=32, color=theme["PRIMARY_COLOR"]),
                        ft.Text("Apurador de ICMS", size=24, weight=ft.FontWeight.BOLD, color=theme["PRIMARY_COLOR"])
                    ]
                ),
                
                # Área de processamento SPED
                ft.Container(
                    width=660,
                    padding=20,
                    border_radius=8,
                    bgcolor=theme["CARD_SECONDARY"],
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            # Título da seção de SPED
                            ft.Text("Processamento de Arquivo SPED", size=18, weight=ft.FontWeight.W_600, color=theme["TEXT"]),
                            ft.Text("Selecione arquivos e faça o processamento dos SPEDs", size=14, color=theme["TEXT_SECONDARY"]),
                            
                            # Botão de seleção/lista de arquivos
                            ft.Container(
                                ref=refs.get("container_arquivos"),
                                width=620,
                                bgcolor=theme["BACKGROUND_LIGHT"] if "BACKGROUND_LIGHT" in theme else theme["CARD"],
                                border_radius=8,
                                border=ft.border.all(1, theme["BORDER"]),
                                padding=16,
                                content=ft.ElevatedButton(
                                    ref=refs.get("botao_selecionar"),
                                    text="Selecionar Arquivo",
                                    on_click=lambda e: inserirSped(page, empresa_id, refs, picker_sped),
                                    icon="UPLOAD_FILE",
                                    width=580,
                                    height=48,
                                    bgcolor=theme["PRIMARY_COLOR"],
                                    color=theme["ON_PRIMARY"],
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=6)
                                    )
                                )
                            ),
                            
                            # Área de processamento
                            ft.Container(
                                ref=refs.get("area_processamento"),
                                visible=False,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.ElevatedButton(
                                            text="Processar SPED",
                                            icon="PLAY_ARROW",
                                            width=200,
                                            height=48,
                                            bgcolor=theme["SUCCESS_COLOR"] if "SUCCESS_COLOR" in theme else theme["PRIMARY_COLOR"],
                                            color=theme["ON_PRIMARY"],
                                            on_click=lambda e: page.run_task(processarSped, page, empresa_id, refs)
                                        ),
                                        ft.IconButton(
                                            icon="REFRESH",
                                            width=48,
                                            height=48,
                                            bgcolor=theme["BORDER"],
                                            on_click=lambda e: limparSelecaoArquivo(e, refs, picker_sped, theme, page, empresa_id),
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=2)
                                            )
                                        ),
                                        # Barra de progresso e status
                                        ft.Container(
                                            width=280,
                                            content=ft.Column(
                                                spacing=8,
                                                controls=[
                                                    ft.ProgressBar(
                                                        ref=refs.get("progress"),
                                                        width=280,
                                                        height=16,
                                                        border_radius=6,
                                                        color=theme["PRIMARY_COLOR"],
                                                        bgcolor=theme["BORDER"],
                                                        visible=False
                                                    ),
                                                    ft.Text(
                                                        ref=refs.get("status_text"),
                                                        value="",
                                                        size=12,
                                                        color=theme["TEXT_SECONDARY"]
                                                    )
                                                ]
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                ),
                
                ft.Divider(height=1, color=theme["BORDER"]),
                
                # Área de download
                ft.Container(
                    width=660,
                    padding=20,
                    border_radius=8,
                    bgcolor=theme["CARD_SECONDARY"],
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            ft.Text("Área de Download", size=18, weight=ft.FontWeight.W_600, color=theme["TEXT"]),
                            ft.Text("Escolha o mês e ano e clique no botão para baixar a planilha", size=14, color=theme["TEXT_SECONDARY"]),
                            
                            # Período
                            ft.Row(
                                spacing=24,
                                alignment=ft.MainAxisAlignment.START,
                                controls=[
                                    ft.Column(
                                        spacing=4,
                                        controls=[
                                            ft.Text("Mês", size=14, weight=ft.FontWeight.W_600, color=theme["TEXT"]),
                                            ft.Dropdown(
                                                ref=refs["mes_dropdown"],
                                                width=165,
                                                options=[
                                                    ft.dropdown.Option("Janeiro", "Janeiro"),
                                                    ft.dropdown.Option("Fevereiro", "Fevereiro"),
                                                    ft.dropdown.Option("Março", "Março"),
                                                    ft.dropdown.Option("Abril", "Abril"),
                                                    ft.dropdown.Option("Maio", "Maio"),
                                                    ft.dropdown.Option("Junho", "Junho"),
                                                    ft.dropdown.Option("Julho", "Julho"),
                                                    ft.dropdown.Option("Agosto", "Agosto"),
                                                    ft.dropdown.Option("Setembro", "Setembro"),
                                                    ft.dropdown.Option("Outubro", "Outubro"),
                                                    ft.dropdown.Option("Novembro", "Novembro"),
                                                    ft.dropdown.Option("Dezembro", "Dezembro"),
                                                ],
                                                hint_text="Selecione o mês"
                                            )
                                        ]
                                    ),
                                    ft.Column(
                                        spacing=4,
                                        controls=[
                                            ft.Text("Ano", size=14, weight=ft.FontWeight.W_600, color=theme["TEXT"]),
                                            ft.Dropdown(
                                                ref=refs["ano_dropdown"],
                                                width=165,
                                                options=[ft.dropdown.Option(str(y), str(y)) for y in range(2020, 2031)],
                                                hint_text="Selecione o ano"
                                            )
                                        ]
                                    ),
                                    ft.Container(
                                        content=ft.ElevatedButton(
                                            text="Baixar Planilha",
                                            icon="DOWNLOAD",
                                            width=180,
                                            height=48,
                                            bgcolor=theme["PRIMARY_COLOR"],
                                            color=theme["ON_PRIMARY"],
                                            on_click=lambda e: baixar_planilha_action(e, page, empresa_id, refs, empresa_nome, picker_tabela),
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=6)
                                            )
                                        ),
                                        margin=ft.margin.only(top=24, left=20)
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )
    )

def baixar_planilha_action(e, page, empresa_id, refs, empresa_nome, picker_tabela):
    mes = refs['mes_dropdown'].current.value if refs['mes_dropdown'].current else None
    ano = refs['ano_dropdown'].current.value if refs['ano_dropdown'].current else None
    baixarAction(page, empresa_id, mes, ano, empresa_nome, picker_tabela)

def limparSelecaoArquivo(e, refs, picker_sped, theme, page, empresa_id):
    refs['arquivos_sped'] = []
    
    atualizarListaArquivos(refs, [], lambda e: inserirSped(page, empresa_id, refs, picker_sped), theme)
    
    if "progress" in refs and refs["progress"].current:
        refs["progress"].current.visible = False
    
    if "status_text" in refs and refs["status_text"].current:
        refs["status_text"].current.value = ""
    
    e.page.update()

def atualizarListaArquivos(refs, arquivos, inserir_sped_fn=None, theme=None):
    if not refs.get("container_arquivos") or not refs["container_arquivos"].current:
        return
        
    container = refs["container_arquivos"].current
    
    if not arquivos:
        container.content = ft.ElevatedButton(
            ref=refs.get("botao_selecionar"),
            text="Selecionar Arquivo",
            on_click=inserir_sped_fn if inserir_sped_fn else lambda e: None,
            icon="UPLOAD_FILE",
            width=580,
            height=48,
            bgcolor=theme["PRIMARY_COLOR"] if theme else "#2563EB",
            color=theme["ON_PRIMARY"] if theme else "#FFFFFF",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6)
            )
        )
        if "area_processamento" in refs and refs["area_processamento"].current:
            refs["area_processamento"].current.visible = False
    else:
        arquivos_controles = []
        
        arquivos_para_mostrar = arquivos[:3]
        
        for i, arquivo in enumerate(arquivos_para_mostrar):
            nome_arquivo = arquivo.split("\\")[-1] if "\\" in arquivo else arquivo.split("/")[-1]
            
            arquivos_controles.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=theme.get("BACKGROUND_LIGHT", "#f8f9fa") if theme else "#f8f9fa",
                    border_radius=4,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                name="DESCRIPTION",
                                size=16,
                                color=theme.get("PRIMARY_COLOR", "#2563EB") if theme else "#2563EB"
                            ),
                            ft.Text(
                                nome_arquivo,
                                size=11,
                                weight=ft.FontWeight.W_500,
                                color=theme.get("TEXT", "#1f2937") if theme else "#1f2937",
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True
                            )
                        ]
                    )
                )
            )
        
        # Se houver mais de 3 arquivos, adicionar indicador
        if len(arquivos) > 3:
            arquivos_extras = len(arquivos) - 3
            arquivos_controles.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    content=ft.Text(
                        f"... e mais {arquivos_extras} arquivo{'s' if arquivos_extras > 1 else ''} será{'ão' if arquivos_extras > 1 else ''} processado{'s' if arquivos_extras > 1 else ''}",
                        size=11,
                        weight=ft.FontWeight.W_400,
                        color=theme.get("TEXT_SECONDARY", "#6b7280") if theme else "#6b7280",
                        italic=True
                    )
                )
            )
        
        # Container principal com a lista de arquivos
        container.content = ft.Container(
            width=580,
            padding=12,
            bgcolor="transparent",
            border_radius=6,
            content=ft.Column(
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
                controls=arquivos_controles
            )
        )
        
        if "area_processamento" in refs and refs["area_processamento"].current:
            refs["area_processamento"].current.visible = True
    
    container.update()