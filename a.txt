import re
import asyncio
from typing import List, Dict, Optional, Callable

import flet as ft
import pandas as pd

from src.Config.theme import apply_theme

from src.Components.notificao import notificacao
from src.Controllers.tributacaoController import TributacaoController
from Services.planilhas.planilhaService import categoria_por_aliquota

VALID_TOKENS = {"ST", "ISENTO", "PAUTA"} 
VALID_NUM_RE = re.compile(r"^(100([.,]0{1,2})?%?|[0-9]{1,2}([.,][0-9]{1,2})?%?)$")

def preparar_itens_backend(empresa_id: int, limit: int = 300):
    return TributacaoController.preparar_listagem_para_ui(empresa_id, limit)


def listar_faltantes_backend(empresa_id: int, limit: int = 300):
    return TributacaoController.listar_faltantes(empresa_id, limit)


def salvar_aliquotas_backend(empresa_id: int, edits: list):
    return TributacaoController.salvar_aliquotas(empresa_id, edits)


def importar_planilha_backend(caminho: str, empresa_id: int):
    return TributacaoController.cadastrar_tributacao_por_planilha(caminho, empresa_id)

def abrir_dialogo_aliquotas(page: ft.Page,empresa_id: int,itens: Optional[List[Dict]] = None,page_size: int = 200,
                            finalizar_apos_salvar: bool = False,callback_continuacao: Optional[Callable] = None,):
    
    th = apply_theme(page)
    dados: List[Dict] = itens[:] if itens else []
    valores: dict[int, str] = {} 
    ref_busca = ft.Ref[ft.TextField]()
    ref_table_wrap = ft.Ref[ft.Container]()
    lbl_status = ft.Text("", size=12, color=th["TEXT_SECONDARY"])
    barra = ft.ProgressBar(width=220, visible=False)
    lbl_resumo = ft.Text("", size=12, color=th["TEXT_SECONDARY"])

    # ---------- Utils ----------
    def eh_valida(aliq: str) -> bool:
        s = (aliq or "").strip().upper()
        return s in VALID_TOKENS or bool(VALID_NUM_RE.fullmatch(s)) or s == ""
    
    def stats():
        total = len(dados)
        preenchidos = sum(1 for it in dados if (valores.get(int(it["id"])) or "").strip())
        invalidos = sum(
            1
            for it in dados
            if (valores.get(int(it["id"])) or "").strip()
            and not eh_valida(valores[int(it["id"])])
        )
        pendentes = total - preenchidos
        return total, preenchidos, pendentes, invalidos

    def atualizar_resumo():
        total, preenchidos, pendentes, invalidos = stats()
        lbl_resumo.value = (
            f"{total} itens • {preenchidos} preenchidos • {pendentes} pendentes"
            + (f" • {invalidos} inválidos" if invalidos else "")
        )

    def construir_tabela(base_items: List[Dict]) -> ft.Container:
        cols = [
            ft.DataColumn(
                label=ft.Container(
                    content=ft.Text("Código", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                    width=120,
                    alignment=ft.alignment.center_left,
                ),
                numeric=False,
            ),
            ft.DataColumn(
                label=ft.Container(
                    content=ft.Text("Produto", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                    width=400,
                    alignment=ft.alignment.center_left,
                ),
                numeric=False,
            ),
            ft.DataColumn(
                label=ft.Container(
                    content=ft.Text("NCM", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                    width=100,
                    alignment=ft.alignment.center,
                ),
                numeric=False,
            ),
            ft.DataColumn(
                label=ft.Container(
                    content=ft.Text("Alíquota", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                    width=120,
                    alignment=ft.alignment.center,
                ),
                numeric=False,
            ),
        ]

        rows: List[ft.DataRow] = []

        for item in base_items:
            _id = int(item["id"])
            cod = item.get("codigo", "") or ""
            prod = item.get("produto", "") or ""
            ncm = (item.get("ncm", "") or "").strip()

            valor_atual = valores.get(_id, "")

            tf = ft.TextField(
                value=valor_atual,
                hint_text="ex.: 1,54%",
                dense=True,
                expand=True,
                text_size=12,
                text_align=ft.TextAlign.CENTER,
                bgcolor=th["INPUT_BG"],
                color=th["TEXT"],
                border=ft.InputBorder.OUTLINE,
                border_color=th["BORDER"],
                border_radius=6,
                content_padding=ft.padding.symmetric(horizontal=6, vertical=4),
                input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,%A-Za-z]*$"),
                on_change=lambda e, rid=_id: on_change_valor(rid, e.control.value),
            )
            if valor_atual and not eh_valida(valor_atual):
                tf.border_color = th["ERROR"]

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    cod,
                                    size=11,
                                    color=th["TEXT"],
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                width=120,
                                height=45,
                                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                alignment=ft.alignment.center_left,
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    prod,
                                    size=11,
                                    color=th["TEXT"],
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                width=400,
                                height=45,
                                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                alignment=ft.alignment.center_left,
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    ncm,
                                    size=11,
                                    color=th["TEXT"],
                                    text_align=ft.TextAlign.CENTER,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                width=100,
                                height=45,
                                padding=ft.padding.symmetric(horizontal=4, vertical=2),
                                alignment=ft.alignment.center,
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=tf,
                                width=120,
                                height=120,
                                padding=ft.padding.all(2),
                                alignment=ft.alignment.center,
                            )
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=cols,
            rows=rows,
            column_spacing=5,
            heading_row_height=48,
            data_row_min_height=50,
            data_row_max_height=50,
            divider_thickness=0.5,
            heading_row_color=th["CARD"],
            horizontal_lines=ft.border.BorderSide(0.3, th["BORDER"]),
            vertical_lines=ft.border.BorderSide(0.3, th["BORDER"]),
            show_checkbox_column=False,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=table,
                        width=960,
                        alignment=ft.alignment.center,
                    )
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            bgcolor=th["BACKGROUND"],
            border=ft.border.all(1, th["BORDER"]),
            border_radius=8,
            padding=ft.padding.all(12),
        )

    def on_change_valor(rid: int, valor: str):
        valores[rid] = (valor or "").strip()
        atualizar_resumo()
        page.update()

    def aplicar_filtro() -> List[Dict]:
        texto = (ref_busca.current.value or "").strip().lower()
        if not texto:
            return list(dados)
        return [
            it
            for it in dados
            if texto in (it.get("produto") or "").lower()
            or texto in (it.get("codigo") or "").lower()
            or texto in (it.get("ncm") or "").lower()
        ]

    def rebuild():
        base = aplicar_filtro()
        ref_table_wrap.current.content = construir_tabela(base)
        atualizar_resumo()
        page.update()

    # ---------- Carga inicial ----------
    async def carregar_inicial():
        barra.visible = True
        lbl_status.value = "Carregando itens pendentes..."
        page.update()
        try:
            if itens is None:
                loop = asyncio.get_running_loop()
                res = await loop.run_in_executor(None, preparar_itens_backend, empresa_id, 1000)
                dados.clear()
                dados.extend(res or [])
            rebuild()
        except Exception as e:
            print("[PopupAliquota] ERRO ao carregar:", e)
        finally:
            barra.visible = False
            lbl_status.value = "" if dados else "Nenhum item pendente."
            page.update()

    # ---------- Ações ----------
    async def salvar(_):
        edits, invalidos = [], []
        for item in dados:
            _id = int(item["id"])
            v = (valores.get(_id) or "").strip()
            if not v:
                continue
            if not eh_valida(v):
                invalidos.append(item.get("produto", f"ID {_id}"))
                continue
            # CORREÇÃO: Usar categoria_por_aliquota corretamente
            edits.append({
                "id": _id, 
                "aliquota": v, 
                "categoriaFiscal": categoria_por_aliquota(v)
            })

        if invalidos:
            notificacao(page, "Alíquotas inválidas",
                        "Corrija:\n- " + "\n- ".join(invalidos[:8]) + (f"\n... e mais {len(invalidos)-8}" if len(invalidos)>8 else ""),
                        tipo="alerta")
            return
        if not edits:
            notificacao(page, "Nenhuma alteração", "Nenhuma alíquota foi preenchida.", tipo="alerta")
            return

        barra.visible = True
        lbl_status.value = "Salvando alterações..."
        page.update()
        
        try:
            loop = asyncio.get_running_loop()
            
            # CORREÇÃO: Usar Controller em vez de gravação direta
            print(f"[DEBUG] Salvando {len(edits)} edições via Controller...")
            res = await loop.run_in_executor(None, salvar_aliquotas_backend, empresa_id, edits)
            
            print(f"[DEBUG] Resultado salvamento: {res}")
            
            # Verifica se houve erro
            if "erro" in res:
                notificacao(page, "Erro", f"Erro ao salvar: {res['erro']}", tipo="erro")
                return
            
            # Mostra notificação de sucesso
            atualizados = res.get("atualizados", 0)
            notificacao(page, "Sucesso", f"{atualizados} registros atualizados (incluindo duplicatas)!", tipo="sucesso")

            # DEBUG: Log dos valores importantes
            faltantes_restantes = res.get("faltantes_restantes", -1)
            print(f"[DEBUG] Faltantes restantes: {faltantes_restantes}")
            print(f"[DEBUG] Callback existe: {callback_continuacao is not None}")
            print(f"[DEBUG] finalizar_apos_salvar: {finalizar_apos_salvar}")

            # Aguarda para o usuário ver a notificação
            await asyncio.sleep(1.5)

            # Se há callback, executa e fecha
            if callback_continuacao:
                try:
                    print("[DEBUG] Executando callback de continuação...")
                    await callback_continuacao()
                    print("[DEBUG] Callback executado com sucesso")
                    
                    fechar(None)
                    return
                    
                except Exception as e:
                    print(f"[DEBUG] Erro no callback: {e}")
                    notificacao(page, "Erro", f"Erro ao continuar processamento: {e}", tipo="erro")
                    return  # Não fecha em caso de erro
            
            # Se deve finalizar automaticamente, fecha
            if finalizar_apos_salvar:
                print("[DEBUG] Finalizando automaticamente...")
                fechar(None)
                return

            # Lógica para recarregar se ainda há faltantes
            if faltantes_restantes < 0:
                # Se não conseguiu contar, tenta buscar novamente
                print("[DEBUG] Recontando faltantes...")
                faltas = await loop.run_in_executor(None, listar_faltantes_backend, empresa_id, 1)
                faltantes_restantes = len(faltas or [])
                print(f"[DEBUG] Faltantes após recontagem: {faltantes_restantes}")

            if faltantes_restantes == 0:
                print("[DEBUG] Não há mais faltantes, fechando popup")
                notificacao(page, "Concluído", "Todas as alíquotas foram preenchidas!", tipo="sucesso")
                await asyncio.sleep(1)
                fechar(None)
            else:
                # Recarrega com novos dados faltantes
                print(f"[DEBUG] Recarregando popup com {faltantes_restantes} faltantes...")
                novos = await loop.run_in_executor(None, listar_faltantes_backend, empresa_id, 1000)
                dados.clear()
                dados.extend(novos or [])
                valores.clear()
                rebuild()
                
                if len(novos or []) == 0:
                    print("[DEBUG] Nenhum dado novo encontrado, fechando")
                    fechar(None)
                else:
                    print(f"[DEBUG] {len(novos)} novos itens carregados")

        except Exception as e:
            print(f"[DEBUG] Erro ao salvar: {e}")
            import traceback
            traceback.print_exc()
            notificacao(page, "Erro", f"Erro ao salvar: {e}", tipo="erro")
        finally:
            barra.visible = False
            lbl_status.value = ""
            page.update()

    picker_save = ft.FilePicker()
    picker_open = ft.FilePicker()
    page.overlay.extend([picker_save, picker_open])

    def exportar_modelo(_):
        def on_save(ev: ft.FilePickerResultEvent):
            if not ev.path:
                return
            caminho = ev.path if ev.path.lower().endswith(".xlsx") else ev.path + ".xlsx"

            base = aplicar_filtro()
            df = pd.DataFrame(
                [
                    {
                        "id": x.get("id"),
                        "codigo": x.get("codigo") or "",
                        "produto": x.get("produto") or "",
                        "ncm": (x.get("ncm") or ""),
                        "aliquota": "",
                    }
                    for x in base
                ],
                columns=["id", "codigo", "produto", "ncm", "aliquota"],
            )
            try:
                with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="aliquotas_pendentes")
                notificacao(page, "Planilha gerada", f"Planilha modelo salva em:\n{caminho}", tipo="sucesso")
            except Exception as ex:
                notificacao(page, "Erro ao gerar planilha", f"Falha: {ex}", tipo="erro")

        picker_save.on_result = on_save
        picker_save.save_file(
            file_name="Aliquotas Pendentes.xlsx",
            allowed_extensions=["xlsx"],
            dialog_title="Salvar planilha modelo",
        )

    def importar_modelo(_):
        def on_open(ev: ft.FilePickerResultEvent):
            if not ev.files:
                return
            caminho = ev.files[0].path

            async def _run():
                barra.visible = True
                lbl_status.value = "Importando planilha..."
                page.update()
                try:
                    df = pd.read_excel(caminho, dtype=str)
                    importadas = 0
                    erros = []

                    def norm(s: str) -> str:
                        import unicodedata

                        s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode()
                        return s.strip().lower()

                    cols = {norm(c): c for c in df.columns}
                    col_id = cols.get("id")
                    col_aliq = cols.get("aliquota") or cols.get("aliq") or cols.get("aliq_icms")

                    if not col_id or not col_aliq:
                        erros.append("Planilha deve conter as colunas 'id' e 'aliquota'.")
                    else:
                        for idx, row in df.iterrows():
                            raw_id = row.get(col_id)
                            raw_aliq = row.get(col_aliq)

                            if pd.isna(raw_id) or pd.isna(raw_aliq):
                                continue

                            try:
                                item_id = int(str(raw_id).strip())
                            except Exception:
                                erros.append(f"Linha {idx + 2}: ID inválido '{raw_id}'")
                                continue

                            aliquota = str(raw_aliq).strip()
                            if not aliquota:
                                continue

                            if not eh_valida(aliquota):
                                erros.append(f"Linha {idx + 2}: alíquota inválida '{aliquota}'")
                                continue

                            if any(int(d["id"]) == item_id for d in dados):
                                valores[item_id] = aliquota
                                importadas += 1
                            else:
                                erros.append(f"Linha {idx + 2}: ID {item_id} não encontrado na listagem atual")

                    rebuild()

                    if importadas > 0:
                        msg = f"{importadas} alíquotas importadas da planilha."
                        if erros:
                            msg += f"\n\nAvisos/erros ({len(erros)}):\n" + "\n".join(erros[:6])
                            if len(erros) > 6:
                                msg += f"\n... e mais {len(erros) - 6}."
                        notificacao(page, "Importação concluída", msg, tipo="sucesso")
                    else:
                        msg = "Nenhuma alíquota válida foi encontrada para importar."
                        if erros:
                            msg += "\n\n" + "\n".join(erros[:6])
                        notificacao(page, "Importação", msg, tipo="alerta")

                except Exception as e:
                    print(f"[DEBUG] Erro geral na importação: {e}")
                    notificacao(page, "Erro na importação", f"Erro ao processar planilha: {e}", tipo="erro")
                finally:
                    barra.visible = False
                    lbl_status.value = ""
                    page.update()

            page.run_task(_run)

        picker_open.on_result = on_open
        picker_open.pick_files(allowed_extensions=["xlsx"], dialog_title="Selecionar planilha preenchida")

    def fechar(_):
        nonlocal dlg
        if dlg:
            dlg.open = False
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
            ft.Row([barra, lbl_status], spacing=10),
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
                        on_click=exportar_modelo,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.OutlinedButton(
                        "Importar planilha",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=importar_modelo,
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
                        on_click=salvar,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.TextButton(
                        "Fechar",
                        on_click=fechar,
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

    dlg = ft.AlertDialog(modal=True, title=None, content=content, on_dismiss=fechar, bgcolor=th["BACKGROUND"])

    page.overlay.insert(0, dlg)
    dlg.open = True
    page.update()

    page.run_task(carregar_inicial)
