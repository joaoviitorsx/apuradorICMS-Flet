import flet as ft

def cardPrincipal(theme, empresa_nome: str, empresa_id: int, refs: dict, enviar_tributacao_fn, inserir_sped_fn, baixar_tabela_fn):
    return ft.Container(
        width=680,
        height=480,
        padding=25, 
        bgcolor=theme["CARD"],
        border_radius=8,
        animate_size=True,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=620,
                    padding=25,
                    border_radius=4,
                    content=ft.ResponsiveRow(
                        columns=12,
                        controls=[
                            ft.Column(
                                col={"xs": 12, "md": 12},
                                controls=[
                                    ft.Row([
                                        ft.Icon(name="folder_open", size=32, color=theme["FOLDER_ICON"]),
                                        ft.Text("Processamento de Arquivo SPED", size=16, weight=ft.FontWeight.W_600)
                                    ]),
                                    ft.Text("Selecione Arquivo SPED", size=14, weight=ft.FontWeight.W_600),
                                    ft.ElevatedButton(
                                        text="Escolher Arquivo",
                                        on_click=inserir_sped_fn,
                                        icon="UPLOAD",
                                        width=340,
                                        height=48,
                                        bgcolor=theme["PRIMARY_COLOR"],
                                        color=theme["ON_PRIMARY"],
                                    ),
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(
                    width=620,
                    padding=12,
                    border_radius=8,
                    bgcolor=theme["DOWNLOAD_OLD"],
                    content=ft.ResponsiveRow(
                        columns=12,
                        controls=[
                            ft.Column(
                                col={"xs": 8, "md": 8},
                                controls=[
                                    ft.Text("Baixar Arquivo Anterior", weight=ft.FontWeight.W_600, color=theme["PRIMARY_COLOR"]),
                                    ft.Text("Baixe arquivos processados anteriormente", size=12, color=theme["TEXT_SECONDARY"])
                                ]
                            ),
                            ft.Column(
                                col={"xs": 4, "md": 4},
                                controls=[
                                    ft.ElevatedButton(
                                        text="Baixar Arquivo",
                                        icon="DOWNLOAD",
                                        icon_color=theme["PRIMARY_COLOR"],
                                        color=theme["PRIMARY_COLOR"],
                                        bgcolor=theme["ON_PRIMARY"],
                                        style=ft.ButtonStyle(
                                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                                            shape=ft.RoundedRectangleBorder(radius=6),
                                            side=ft.BorderSide(1, theme["PRIMARY_COLOR"])
                                        ),
                                        on_click=lambda e: (
                                            setattr(refs["area_download"].current, "visible", True),
                                            refs["area_download"].current.update(),
                                            e.page.update()
                                        )
                                    )
                                ]
                            )
                        ]
                    )
                ),
                ft.Container(
                    ref=refs["area_download"],
                    visible=False,
                    width=620,
                    padding=12,
                    border_radius=8,
                    bgcolor=theme["DOWNLOAD_OLD"],
                    content=ft.ResponsiveRow(
                        columns=12,
                        controls=[
                            ft.Column(
                                col={"xs": 12, "md": 12},
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                        controls=[
                                            ft.Text("Selecionar Período para Download", weight=ft.FontWeight.W_600, color=theme["PRIMARY_COLOR"]),
                                            ft.TextButton(
                                                text="Cancelar",
                                                on_click=lambda e: (
                                                    setattr(refs["area_download"].current, "visible", False),
                                                    refs["area_download"].current.update(),
                                                    e.page.update()
                                                )
                                            )
                                        ]
                                    ),
                                    ft.Row(
                                        spacing=8,
                                        controls=[
                                            ft.Column(
                                                spacing=2,
                                                controls=[
                                                    ft.Text("Mês", size=12, weight=ft.FontWeight.W_600),
                                                    ft.Dropdown(
                                                        ref=refs["mes_dropdown"],
                                                        width=150,
                                                        options=[ft.dropdown.Option(str(m)) for m in range(1, 13)],
                                                        hint_text="Selecionar mês"
                                                    )
                                                ]
                                            ),
                                            ft.Column(
                                                spacing=2,
                                                controls=[
                                                    ft.Text("Ano", size=12, weight=ft.FontWeight.W_600),
                                                    ft.Dropdown(
                                                        ref=refs["ano_dropdown"],
                                                        width=150,
                                                        options=[ft.dropdown.Option(str(y)) for y in range(2024, 2028)],
                                                        hint_text="Selecionar ano"
                                                    )
                                                ]
                                            ),
                                            ft.Container(
                                                content=ft.ElevatedButton(
                                                    text="Baixar Arquivo",
                                                    icon="DOWNLOAD",
                                                    width=160,
                                                    height=48,
                                                    bgcolor=theme["PRIMARY_COLOR"],
                                                    color=theme["ON_PRIMARY"],
                                                    on_click=baixar_tabela_fn
                                                ),
                                                margin=ft.margin.only(top=8, left=16)
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )
    )