import flet as ft
from src.Config.theme import get_theme, STYLE, apply_theme
from src.Controllers.empresasController import cadastrar_empresa
from src.Components.notificao import notificacao

def TelaCadastro(page: ft.Page) -> ft.View:
    theme = apply_theme(page)

    page.scroll = ft.ScrollMode.ADAPTIVE

    input_cnpj = ft.Ref[ft.TextField]()
    input_razao = ft.Ref[ft.TextField]()

    def validar_e_cadastrar(e):
        cnpj = input_cnpj.current.value.strip()

        if len(cnpj) != 14 or not cnpj.isdigit():
            notificacao(page, "Erro", "CNPJ inválido. Deve conter 14 dígitos numéricos.", tipo="erro")
            return

        resultado = cadastrar_empresa(cnpj)

        if resultado["status"] == "ok":
            input_razao.current.value = resultado["razao_social"]
            page.update()
            notificacao(page, "Sucesso", "Empresa cadastrada com sucesso!", tipo="sucesso")
            page.go("/empresa")
        else:
            notificacao(page, "Erro", resultado["mensagem"], tipo="erro")

    def voltar(e):
        page.go("/empresa")

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
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon="ARROW_BACK",
                            icon_color=theme["PRIMARY_COLOR"],
                            on_click=voltar,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START
                ),

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
                ),
                ft.TextField(
                    ref=input_razao,
                    label="Razão Social",
                    hint_text="Será preenchido automaticamente pela API",
                    width=400,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    bgcolor=theme["INPUT_BG"],
                    border_color=theme["BORDER"],
                    color=theme["TEXT"],
                    text_style=ft.TextStyle(size=14),
                    read_only=True,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="Cadastrar",
                            bgcolor=theme["PRIMARY_COLOR"],
                            color=theme["ON_PRIMARY"],
                            on_click=validar_e_cadastrar,
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

    # View com centralização total
    return ft.View(
        route="/cadastro",
        controls=[
            ft.Column(
                controls=[card_content],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor=theme["BACKGROUNDSCREEN"]
    )
