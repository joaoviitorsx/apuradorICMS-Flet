import flet as ft
from src.Config.theme import apply_theme
from .aliquotaTable import construir_tabela
from .aliquotaUtils import stats, aplicar_filtro
from .aliquotaAction import salvarAliquotas, exportarModelo, importarModelo, fecharDialogo
from .aliquotaBackend import preparar_itens_backend

def criar_dialogo_aliquota(page, empresa_id, itens, page_size, finalizar_apos_salvar, callback_continuacao):
    th = apply_theme(page)

    dados = itens[:] if itens else []
    valores = {}

    ref_busca = ft.Ref[ft.TextField]()
    ref_table_wrap = ft.Ref[ft.Container]()
    barra_ref = ft.Ref[ft.ProgressBar]()
    status_ref = ft.Ref[ft.Text]()

    lbl_resumo = ft.Text("", size=12, color=th["TEXT_SECONDARY"])

    def atualizar_resumo():
        total, preenchidos, pendentes, invalidos = stats(dados, valores)
        lbl_resumo.value = (
            f"{total} itens • {preenchidos} preenchidos • {pendentes} pendentes"
            + (f" • {invalidos} inválidos" if invalidos else "")
        )

    def on_change_valor(rid: int, valor: str):
        valores[rid] = (valor or "").strip()
        atualizar_resumo()
        page.update()

    def rebuild():
        base = aplicar_filtro(dados, ref_busca.current.value)
        ref_table_wrap.current.content = construir_tabela(base, valores, on_change_valor, th)
        atualizar_resumo()
        page.update()

    async def carregar_inicial():
        barra_ref.current.visible = True
        status_ref.current.value = "Carregando itens pendentes..."
        page.update()
        try:
            if itens is None:
                import asyncio
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(None, preparar_itens_backend, empresa_id, 1000)
                dados.clear()
                dados.extend(res or [])
            rebuild()
        except Exception as e:
            print("[AliquotaUI] ERRO ao carregar:", e)
        finally:
            barra_ref.current.visible = False
            status_ref.current.value = "" if dados else "Nenhum item pendente."
            page.update()

    titulo = ft.Text(
        "Preencha as alíquotas pendentes:",
        size=16,
        weight=ft.FontWeight.BOLD,
        color=th["TEXT"],
    )

    busca = ft.TextField(
        ref=ref_busca,
        hint_text="Filtrar por produto, código ou NCM...",
        on_change=lambda e: rebuild(),
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        height=44,
        text_size=14,
        bgcolor=th["INPUT_BG"],
        color=th["TEXT"],
        border=ft.InputBorder.OUTLINE,
        border_color=th["BORDER"],
        border_radius=8,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
    )

    table_wrap = ft.Container(ref=ref_table_wrap, expand=True)

    status_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row([
                ft.ProgressBar(ref=barra_ref, width=220, visible=False),
                ft.Text(ref=status_ref, value="", size=12, color=th["TEXT_SECONDARY"]),
            ], spacing=10),
            lbl_resumo,
        ],
        height=32,
    )

    botoes = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(
                controls=[
                    ft.OutlinedButton(
                        "Gerar modelo",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda _: exportarModelo(page, dados, ref_busca, aplicar_filtro),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.OutlinedButton(
                        "Importar planilha",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: importarModelo(
                            page, dados, valores, rebuild, barra_ref, status_ref
                        ),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                ],
                spacing=8,
            ),
            ft.Row(
                controls=[
                    ft.ElevatedButton(
                        "Salvar",
                        icon=ft.Icons.SAVE,
                        on_click=lambda _: salvarAliquotas(
                            page,
                            dados,
                            valores,
                            empresa_id,
                            finalizar_apos_salvar,
                            callback_continuacao,
                            rebuild,
                            barra_ref,
                            status_ref
                        ),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.TextButton(
                        "Fechar",
                        on_click=lambda _: fecharDialogo(page, dlg),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                ],
                spacing=8,
            ),
        ],
    )

    content = ft.Container(
        width=min(850, page.width * 0.95) if page.width else 800,
        height=min(700, page.height * 0.9) if page.height else 650,
        padding=ft.padding.all(20),
        bgcolor=th["BACKGROUND"],
        border_radius=8,
        content=ft.Column(
            expand=True,
            spacing=14,
            controls=[
                titulo,
                busca,
                table_wrap,
                status_bar,
                botoes,
            ],
        ),
    )

    dlg = ft.AlertDialog(
        modal=True,
        title=None,
        content=content,
        on_dismiss=lambda _: fecharDialogo(page, dlg),
        bgcolor=th["BACKGROUND"],
    )

    page.run_task(carregar_inicial)
    return dlg
