import flet as ft
from src.Config.theme import apply_theme
from src.Components.Principal.headerPrincipal import construir_header_principal
from src.Components.Principal.tributacaoAction import enviar_tributacao
from src.Components.Principal.spedAction import inserirSped
from src.Components.Principal.downloadAction import baixar_tabela
from src.Components.Principal.cardPrincipal import construir_card_principal

def TelaPrincipal(page: ft.Page, empresa_nome: str, empresa_id: int) -> ft.View:
    theme = apply_theme(page)

    refs = {
        "nome_arquivo": ft.Ref[ft.Text](),
        "status_envio": ft.Ref[ft.Text](),
        "progress": ft.Ref[ft.ProgressBar](),
        "mes_dropdown": ft.Ref[ft.Dropdown](),
        "ano_dropdown": ft.Ref[ft.Dropdown](),
        "status_text": ft.Ref[ft.Text]()
    }

    picker_planilha = ft.FilePicker()
    picker_sped = ft.FilePicker()
    page.overlay.extend([picker_planilha, picker_sped])

    return ft.View(
        route="/principal",
        bgcolor=theme["BACKGROUNDSCREEN"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[
            construir_header_principal(lambda e: page.go("/empresa"), lambda e: page.go("/produtos"), theme),
            ft.Container(
                alignment=ft.alignment.center,
                expand=True,
                content=construir_card_principal(
                    theme,
                    empresa_nome,
                    empresa_id,
                    refs,
                    lambda e: enviar_tributacao(page, empresa_id, refs, picker_planilha),
                    lambda e: inserirSped(page, empresa_id, refs, picker_sped),
                    lambda e: baixar_tabela(page, refs['mes_dropdown'].current.value, refs['ano_dropdown'].current.value, refs)
                )
            )
        ]
    )
