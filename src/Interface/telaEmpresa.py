import flet as ft
from src.Config.theme import get_theme, STYLE, apply_theme
from src.Services.empresaService import listar_empresas
from src.Components.notificao import notificacao

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
        empresa_id = selected_empresa.current.value
        empresa_nome = next(
            (opt.text for opt in selected_empresa.current.options if opt.key == empresa_id),
            "Empresa"
        )
        page.go(f"/principal?id={empresa_id}&nome={empresa_nome}")

    def on_cadastrar_click(e):
        page.go("/cadastro")
        
    try:
        empresas = listar_empresas()
        dropdown_options = [
            ft.dropdown.Option(key=str(emp["id"]), text=emp["razao_social"])
            for emp in empresas
        ]
    except Exception as erro:
        dropdown_options = []
        notificacao(page, "Erro ao buscar empresas", str(erro), tipo="erro")

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

    return ft.View(
        route="/empresa",
        controls=[card_content],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=theme["BACKGROUNDSCREEN"],
    )
