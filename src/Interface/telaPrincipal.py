import flet as ft
from src.Config.theme import get_theme, STYLE, apply_theme
from src.Interface.telaProdutos import get_produtos_dialog
from src.Components.notificao import notificacao

def TelaPrincipal(page: ft.Page, empresa_nome: str, empresa_id: int) -> ft.View:
    theme = apply_theme(page)

    nome_arquivo = ft.Ref[ft.Text]()
    status_envio = ft.Ref[ft.Text]()
    progress = ft.Ref[ft.ProgressBar]()
    mes_dropdown = ft.Ref[ft.Dropdown]()
    ano_dropdown = ft.Ref[ft.Dropdown]()
    status_text = ft.Ref[ft.Text]()

    def voltar(e):
        page.go("/empresa")

    def abrir_configuracoes(e):
        dialog = get_produtos_dialog(page)
        page.open(dialog)

    def enviar_tributacao(e):
        nome_arquivo.current.value = "tributacao_julho2024.txt"
        status_envio.current.value = "Enviando..."
        progress.current.visible = True
        status_text.current.value = "Inserindo dados da tabela C100..."
        page.update()

        async def finalizar_upload_async(_):
            finalizar_upload("tributacao_julho2024.txt")

        page.run_task(lambda: page.sleep(2), finalizar_upload_async)

    def inserir_sped(e):
        nome_arquivo.current.value = "sped_julho2024.txt"
        status_envio.current.value = "Enviando..."
        progress.current.visible = True
        status_text.current.value = "Inserindo dados da tabela C190..."
        page.update()
        page.run_task(lambda: page.sleep(2), lambda _: finalizar_upload("sped_julho2024.txt"))

    def finalizar_upload(nome):
        status_envio.current.value = f"✅ {nome} enviado com sucesso"
        progress.current.visible = False
        status_text.current.value = "Processo concluído."
        notificacao(page, "Sucesso", f"O arquivo {nome} foi enviado com sucesso!", tipo="sucesso")
        page.update()

    def baixar_tabela(e):
        if not mes_dropdown.current.value or not ano_dropdown.current.value:
            notificacao(page, "Atenção", "Selecione mês e ano!", tipo="alerta")
            return
        notificacao(page, "Download", f"Baixando tabela de {mes_dropdown.current.value}/{ano_dropdown.current.value}", tipo="info")

    # Cabeçalho com ícones alinhados
    header = ft.Container(
        padding=ft.Padding(0, 8, 0, 8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon="ARROW_BACK", on_click=voltar, icon_color=theme["PRIMARY_COLOR"]),
                ft.IconButton(icon="SETTINGS", on_click=abrir_configuracoes, icon_color=theme["PRIMARY_COLOR"])
            ]
        )
    )

    card = ft.Container(
        width=680,
        height=650,
        padding=30,
        bgcolor=theme["CARD"],
        border_radius=STYLE["CARD_RADIUS"],
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            spacing=30,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[

                ft.Container(
                    padding=ft.Padding(0, 0, 0, 8),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                bgcolor=theme["PRIMARY_COLOR"],
                                border_radius=24,
                                alignment=ft.alignment.center,
                                content=ft.Icon(name="business", color=theme["ON_PRIMARY"], size=28)
                            ),
                            ft.Column(
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        empresa_nome,
                                        size=22,
                                        weight=ft.FontWeight.BOLD,
                                        color=theme["PRIMARY_COLOR"]
                                    ),
                                    ft.Text(
                                        f"ID: {empresa_id}",
                                        size=14,
                                        color=theme["TEXT_SECONDARY"]
                                    )
                                ]
                            )
                        ]
                    )
                ),

                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    width=620,
                    padding=20,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=theme["BORDER"],
                        offset=ft.Offset(0, 8),
                        blur_style=ft.ShadowBlurStyle.NORMAL
                    ),
                    content=ft.Column(
                        spacing=18,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(name="folder_open", size=32, color=theme["FOLDER_ICON"]),
                                    ft.Text("Arquivos da empresa", size=16, weight=ft.FontWeight.W_600, color=theme["TEXT_SECONDARY"]),
                                ]
                            ),
                            ft.ElevatedButton(
                                text="Enviar Tributação",
                                icon="UPLOAD_FILE",
                                bgcolor=theme["PRIMARY_COLOR"],
                                color=theme["ON_PRIMARY"],
                                on_click=enviar_tributacao,
                                width=220,
                                height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),padding=ft.Padding(0, 0, 0, 0))   
                            ),
                            ft.Text(ref=nome_arquivo, value="Nenhum arquivo enviado", color=theme["TEXT"], size=14, italic=True),
                            ft.ElevatedButton(
                                text="Inserir SPED", icon="INSERT_DRIVE_FILE",
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"],
                                on_click=inserir_sped,
                                width=220,
                                height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=ft.Padding(16, 8, 16, 8))
                            ),
                            ft.Text(ref=status_envio, value="Nenhum arquivo enviado", color=theme["TEXT"], size=14, italic=True),
                        ]
                    )
                ),

                # Seção de Apuração de ICMS
                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    padding=20,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=theme["BORDER"],
                        offset=ft.Offset(0, 8),
                        blur_style=ft.ShadowBlurStyle.NORMAL
                    ),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(name="ASSESSMENT", size=32, color=theme["ASSETS_ICON"]),
                                    ft.Text("Arquivos da empresa", size=16, weight=ft.FontWeight.W_600, color=theme["TEXT_SECONDARY"]),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    ft.Dropdown(
                                        ref=mes_dropdown,
                                        width=160,
                                        hint_text="Mês",
                                        options=[ft.dropdown.Option(m) for m in [
                                            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                                            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]],
                                        bgcolor=theme["INPUT_BG"],
                                        border_color=theme["BORDER"],
                                        border_radius=8,
                                        color=theme["TEXT"]
                                    ),
                                    ft.Dropdown(
                                        ref=ano_dropdown,
                                        width=120,
                                        hint_text="Ano",
                                        options=[ft.dropdown.Option(str(y)) for y in range(2020, 2026)],
                                        bgcolor=theme["INPUT_BG"],
                                        border_color=theme["BORDER"],
                                        border_radius=8,
                                        color=theme["TEXT"]
                                    ),
                                    ft.ElevatedButton(
                                        text="Baixar Tabela", icon="DOWNLOAD",
                                        bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"],
                                        on_click=baixar_tabela,
                                        width=220,
                                        height=48,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ]
                    )
                ),

                ft.Container(
                    content=ft.Column(
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(ref=status_text, value="", color=theme["TEXT_SECONDARY"], size=14),
                            ft.ProgressBar(ref=progress, width=460, visible=False)
                        ]
                    )
                )
            ]
        )
    )

    return ft.View(
        route="/principal",
        bgcolor=theme["BACKGROUNDSCREEN"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[
            header,
            ft.Container(
                content=card,
                alignment=ft.alignment.center,
                expand=True
            )
        ]
    )