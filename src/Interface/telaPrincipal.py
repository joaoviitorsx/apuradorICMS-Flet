import flet as ft
from src.Config.theme import apply_theme
from src.Components.Principal.headerPrincipal import headerPrincipal
from src.Components.Principal.tributacaoAction import enviarTributacao
from src.Components.Principal.spedAction import inserirSped
from src.Components.Principal.downloadAction import baixarAction
from src.Components.Principal.cardPrincipal import cardPrincipal

def TelaPrincipal(page: ft.Page, empresa_nome: str, empresa_id: int) -> ft.View:
    theme = apply_theme(page)

    produtos_qtd = "1231"
    refs = {
        "nome_arquivo": ft.Ref[ft.Text](),
        "status_envio": ft.Ref[ft.Text](),
        "mes_dropdown": ft.Ref[ft.Dropdown](),
        "ano_dropdown": ft.Ref[ft.Dropdown](),
        "area_download": ft.Ref[ft.Container](),
        "arquivos_sped": [],
    }

    picker_planilha = ft.FilePicker()
    picker_sped = ft.FilePicker()
    picker_tabela = ft.FilePicker()

    page.overlay.extend([picker_planilha, picker_sped, picker_tabela])
    page.update()

    refs["file_picker"] = picker_planilha

    return ft.View(
        route="/principal",
        bgcolor=theme["BACKGROUNDSCREEN"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[
            headerPrincipal(
                on_voltar=lambda e: page.go("/empresa"),
                on_gerenciar_produtos=lambda e: page.go("/produtos"),
                theme=theme,
                empresa_nome=empresa_nome,
                produtos_qtd=produtos_qtd
            ),
            ft.Container(height=24),  
            ft.Container(
                alignment=ft.alignment.center,
                content=cardPrincipal(
                    theme,
                    empresa_nome,
                    empresa_id,
                    refs,
                    lambda e: enviarTributacao(page, empresa_id, refs, picker_planilha),
                    lambda e: inserirSped(page, empresa_id, refs, picker_sped),
                    lambda e: baixarAction(page,empresa_id,refs['mes_dropdown'].current.value,refs['ano_dropdown'].current.value,empresa_nome,picker_tabela) 
                )
            )
        ]
    )