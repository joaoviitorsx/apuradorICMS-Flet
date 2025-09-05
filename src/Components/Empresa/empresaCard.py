import flet as ft
from src.Config.theme import STYLE
from src.Utils.path import resourcePath

img = resourcePath("src/Assets/logo.png")

def cardEmpresa(theme, selected_empresa, btn_entrar, dropdown_options,on_empresa_change, on_entrar_click, on_cadastrar_click) -> ft.Container:     
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
                ft.Image(src=img, width=320, height=140, fit=ft.ImageFit.CONTAIN),
                ft.Text("Escolha ou cadastre uma empresa", size=16, color=theme["TEXT_SECONDARY"], text_align=ft.TextAlign.CENTER),
                ft.Divider(height=20, color=theme["BORDER"]),
                ft.Dropdown(
                    ref=selected_empresa,
                    width=400,
                    hint_text="Selecione uma empresa...",
                    options=dropdown_options,
                    on_change=on_empresa_change,
                    filled=True,
                    bgcolor=theme["INPUT_BG"],
                    border_color=theme["BORDER"],
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    color=theme["TEXT"],
                ),
                ft.ElevatedButton(
                    ref=btn_entrar,
                    text="Entrar",
                    width=400,
                    height=48,
                    disabled=True,
                    bgcolor=theme["PRIMARY_COLOR"],
                    color=theme["ON_PRIMARY"],
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=STYLE["BORDER_RADIUS_INPUT"]),
                        overlay_color=theme["PRIMARY_HOVER"]
                    ),
                    on_click=on_entrar_click
                ),
                ft.ElevatedButton(
                    text="Cadastrar Empresa",
                    width=400,
                    height=48,
                    bgcolor=theme["CARD"],
                    color=theme["PRIMARY_COLOR"],
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=STYLE["BORDER_RADIUS_INPUT"]),
                        side=ft.BorderSide(1, theme["PRIMARY_COLOR"])
                    ),
                    on_click=on_cadastrar_click
                )
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )
