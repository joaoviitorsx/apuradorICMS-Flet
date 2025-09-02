import flet as ft
from src.Config.theme import apply_theme
from src.Components.Principal.headerPrincipal import headerPrincipal
from src.Components.Principal.cardPrincipal import cardPrincipal
from src.Controllers.exportarController import ExportarController

def TelaPrincipal(page: ft.Page, empresa_nome: str, empresa_id: int) -> ft.View:
    theme = apply_theme(page)

    produtos_qtd = str(ExportarController.contarProdutos(empresa_id))
    refs = {
        "nome_arquivo": ft.Ref[ft.Text](),
        "status_envio": ft.Ref[ft.Text](),
        "mes_dropdown": ft.Ref[ft.Dropdown](),
        "ano_dropdown": ft.Ref[ft.Dropdown](),
        "area_download": ft.Ref[ft.Container](),
        "container_arquivos": ft.Ref[ft.Container](),
        "botao_selecionar": ft.Ref[ft.ElevatedButton](),
        "area_processamento": ft.Ref[ft.Container](),
        "progress": ft.Ref[ft.ProgressBar](),
        "status_text": ft.Ref[ft.Text](),
        "arquivos_sped": [],
    }

    picker_planilha = ft.FilePicker()
    picker_sped = ft.FilePicker()
    picker_tabela = ft.FilePicker()

    page.overlay.extend([picker_planilha, picker_sped, picker_tabela])
    page.update()

    refs["file_picker"] = picker_planilha
    refs['empresa_id'] = empresa_id
    refs['picker_sped'] = picker_sped

    return ft.View(
        route="/principal",
        bgcolor=theme["BACKGROUNDSCREEN"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[
            headerPrincipal(
                on_voltar=lambda e: page.go("/empresa"),
                on_gerenciar_produtos=lambda e: page.go(f"/produtos?id={empresa_id}&nome={empresa_nome}"), 
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
                    picker_sped,
                    picker_tabela,
                    page 
                )
            )
        ]
    )