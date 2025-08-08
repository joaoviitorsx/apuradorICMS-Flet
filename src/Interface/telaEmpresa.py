import flet as ft
from src.Config.theme import get_theme, STYLE, apply_theme

def TelaEmpresa(page: ft.Page) -> ft.View:
    theme = apply_theme(page)

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    selected_empresa = ft.Ref[ft.Dropdown]()
    btn_entrar = ft.Ref[ft.ElevatedButton]()

    def on_empresa_change(e):
        btn_entrar.current.disabled = not bool(selected_empresa.current.value)
        page.update()

    def on_entrar_click(e):
        page.snack_bar = ft.SnackBar(ft.Text(f"Entrando na empresa: {selected_empresa.current.value}"))
        page.snack_bar.open = True
        page.update()
        page.go("/principal")

    def on_cadastrar_click(e):
        page.snack_bar = ft.SnackBar(ft.Text("Indo para o cadastro de nova empresa..."))
        page.snack_bar.open = True
        page.update()
        page.go("/cadastro")

    card_content = ft.Container(
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
                ft.Text("Escolha ou cadastre uma empresa", size=16,color=theme["TEXT_SECONDARY"], text_align=ft.TextAlign.CENTER),
                ft.Divider(height=20, color=theme["BORDER"]),
                    ft.Dropdown(
                        ref=selected_empresa,
                        width=400,
                        hint_text="Selecione uma empresa...",
                        options=[
                            ft.dropdown.Option("JM SUPERMERCADO LTDA"),
                            ft.dropdown.Option("CONTABILIDADE MEGA"),
                            ft.dropdown.Option("ASSERTIVUS HOLDING")
                        ],
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

    return ft.View(
        route="/empresa",
        controls=[card_content],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=theme["BACKGROUNDSCREEN"],
    )
