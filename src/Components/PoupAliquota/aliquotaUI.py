import asyncio
import flet as ft
from src.Config.theme import apply_theme
from .aliquotaTable import construirTabela
from src.Utils.aliquota import stats, aplicarFiltro
from src.Controllers.tributacaoController import TributacaoController
from src.Controllers.poupController import AliquotaPopupController
from src.Utils.dialogo import fecharDialogo

def criarDialogoAliquota(page, empresa_id, itens, page_size, retornar_pos=False, etapa_pos=None):
    th = apply_theme(page)

    dados = itens[:] if itens else []
    valores = {}

    ref_busca = ft.Ref[ft.TextField]()
    ref_table_wrap = ft.Ref[ft.Container]()
    barra_ref = ft.Ref[ft.ProgressBar]()
    status_ref = ft.Ref[ft.Text]()

    lbl_resumo = ft.Text("", size=12, color=th["TEXT_SECONDARY"])

    paginaAtual = 1
    paginacao = 150

    def getPagina(base, pagina, tamanho):
        inicio = (pagina - 1) * tamanho
        fim = inicio + tamanho
        return base[inicio:fim]

    def atualizarResumo():
        total, preenchidos, pendentes, invalidos = stats(dados, valores)
        lbl_resumo.value = (
            f"{total} itens • {preenchidos} preenchidos • {pendentes} pendentes"
            + (f" • {invalidos} inválidos" if invalidos else "")
        )

    def onChangeValor(rid: int, valor: str):
        valor_str = str(valor or "").strip()
        valores[rid] = valor_str
        atualizarResumo()
        page.update()

    def rebuild():
        base = aplicarFiltro(dados, ref_busca.current.value)
        total_paginas = max(1, (len(base) + paginacao - 1) // paginacao)
        pagina_items = getPagina(base, paginaAtual, paginacao)
        ref_table_wrap.current.content = construirTabela(pagina_items, valores, onChangeValor, th)
        atualizarResumo()

        paginacao_text.value = f"Página {paginaAtual} de {total_paginas}"
        btn_prev.disabled = paginaAtual <= 1
        btn_next.disabled = paginaAtual >= total_paginas
        page.update()

    async def loadingInicial():
        barra_ref.current.visible = True
        status_ref.current.value = "Carregando itens pendentes..."
        page.update()
        try:
            if itens is None:
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(None, TributacaoController.listarFaltantes, empresa_id)
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

    paginacao_text = ft.Text(f"Página {paginaAtual}", size=12, color=th["TEXT_SECONDARY"])
    btn_prev = ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: mudarPagina(-1))
    btn_next = ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=lambda _: mudarPagina(1))

    def mudarPagina(delta):
        nonlocal paginaAtual
        base = aplicarFiltro(dados, ref_busca.current.value)
        total_paginas = max(1, (len(base) + paginacao - 1) // paginacao)
        paginaAtual = max(1, min(paginaAtual + delta, total_paginas))
        rebuild()

    botoes_paginacao = ft.Row(
        controls=[
            btn_prev,
            paginacao_text,
            btn_next,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    botoes = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(
                controls=[
                    ft.OutlinedButton(
                        "Gerar modelo",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda _: AliquotaPopupController.exportar(page, dados, ref_busca),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.OutlinedButton(
                        "Importar planilha",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: AliquotaPopupController.importar(
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
                        on_click=lambda _: AliquotaPopupController.salvar(
                            page,
                            dados,
                            valores,
                            empresa_id,
                            rebuild,
                            barra_ref,
                            status_ref,
                            retornar_pos
                        ),
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
                botoes_paginacao,
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

    page.run_task(loadingInicial)
    return dlg