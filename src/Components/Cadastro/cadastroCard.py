import flet as ft
from src.Config.theme import STYLE
from src.Utils.validadores import formatarCnpj

def cardCadastro(theme, input_cnpj,on_voltar, on_cadastrar):

    def on_cnpj_change(e):
        valor_digitado = e.control.value
        valor_formatado = formatarCnpj(valor_digitado)
        e.control.value = valor_formatado
        e.control.update()

    return ft.Container(
        width=470,
        padding=20,
        bgcolor=theme["CARD"],
        border_radius=STYLE["CARD_RADIUS"],
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=64,
            color=theme["TEXT_SECONDARY"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            controls=[
                ft.Image(src="src/Assets/images/logo.png", width=320, height=140, fit=ft.ImageFit.CONTAIN),
                ft.Text("Cadastro de Empresa", size=18, weight=ft.FontWeight.BOLD,
                        color=theme["TEXT"], text_align=ft.TextAlign.CENTER),
                ft.Divider(height=20, color=theme["BORDER"]),

                ft.TextField(
                    ref=input_cnpj,
                    label="CNPJ",
                    hint_text="Digite o CNPJ da empresa",
                    width=400,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    bgcolor=theme["INPUT_BG"],
                    border_color=theme["BORDER"],
                    color=theme["TEXT"],
                    text_style=ft.TextStyle(size=14),
                    max_length=18,
                    on_change=on_cnpj_change
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Voltar",
                            width=120,
                            height=42,
                            bgcolor=theme["CARD_SECONDARY"],
                            color=theme["TEXT"],
                            on_click=on_voltar,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=STYLE["BORDER_RADIUS_INPUT"])
                            )
                        ),
                        ft.ElevatedButton(
                            text="Cadastrar",
                            bgcolor=theme["PRIMARY_COLOR"],
                            color=theme["ON_PRIMARY"],
                            width=120,
                            height=42,
                            on_click=on_cadastrar,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=STYLE["BORDER_RADIUS_INPUT"]),
                                overlay_color=theme["PRIMARY_HOVER"]
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )
