import flet as ft

def construir_card_principal(theme, empresa_nome: str, empresa_id: int, refs: dict, enviar_tributacao_fn, inserir_sped_fn, baixar_tabela_fn):
    return ft.Container(
        width=680,
        height=650,
        padding=30,
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
                                    ft.Text(empresa_nome, size=22, weight=ft.FontWeight.BOLD, color=theme["PRIMARY_COLOR"]),
                                    ft.Text(f"ID: {empresa_id}", size=14, color=theme["TEXT_SECONDARY"])
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    width=620,
                    padding=20,
                    border_radius=8,
                    content=ft.Column(
                        spacing=18,
                        controls=[
                            ft.Row([
                                ft.Icon(name="folder_open", size=32, color=theme["FOLDER_ICON"]),
                                ft.Text("Arquivos da empresa", size=16, weight=ft.FontWeight.W_600)
                            ]),
                            ft.ElevatedButton(
                                text="Enviar Tributação (.xlsx)", on_click=enviar_tributacao_fn,
                                icon="UPLOAD_FILE", width=260, height=48,
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"]
                            ),
                            ft.Text(ref=refs['nome_arquivo'], value="Nenhum arquivo enviado", italic=True),
                            ft.ElevatedButton(
                                text="Importar SPED (.txt)", on_click=inserir_sped_fn,
                                icon="INSERT_DRIVE_FILE", width=220, height=48,
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"]
                            ),
                            ft.Text(ref=refs['status_envio'], value="Aguardando ação", italic=True),
                        ]
                    )
                ),
                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    padding=20,
                    border_radius=8,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(name="ASSESSMENT", size=32, color=theme["ASSETS_ICON"]),
                            ft.Text("Apuração de ICMS", size=16, weight=ft.FontWeight.W_600)
                        ]),
                        ft.Row([
                            ft.Dropdown(ref=refs['mes_dropdown'], width=160, hint_text="Mês", options=[
                                ft.dropdown.Option(m) for m in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                                                                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                            ]),
                            ft.Dropdown(ref=refs['ano_dropdown'], width=120, hint_text="Ano", options=[
                                ft.dropdown.Option(str(y)) for y in range(2020, 2026)
                            ]),
                            ft.ElevatedButton(
                                text="Baixar Tabela", on_click=baixar_tabela_fn,
                                icon="DOWNLOAD", width=220, height=48,
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"]
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ])
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(ref=refs['status_text'], value="", color=theme["TEXT_SECONDARY"]),
                        ft.ProgressBar(ref=refs['progress'], width=460, visible=False)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ]
        )
    )