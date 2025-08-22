import asyncio
import flet as ft
import pandas as pd
from src.Components.notificao import notificacao
from src.Services.Planilhas.planilhaService import categoria_por_aliquota
from flet import FilePicker, FilePickerResultEvent

from .aliquotaUtils import eh_valida
from .aliquotaBackend import salvar_aliquotas_backend, listar_faltantes_backend

def salvarAliquotas(page, dados, valores, empresa_id, finalizar_apos_salvar, callback_continuacao, rebuild, barra_ref, status_ref):
    async def _run():
        edits, invalidos = [], []

        for item in dados:
            _id = int(item["id"])
            v = (valores.get(_id) or "").strip()

            if not v:
                continue
            if not eh_valida(v):
                invalidos.append(item.get("produto", f"ID {_id}"))
                continue

            edits.append({
                "id": _id,
                "aliquota": v,
                "categoriaFiscal": categoria_por_aliquota(v),
            })

        if invalidos:
            notificacao(
                page,
                "Alíquotas inválidas",
                "Corrija:\n- " + "\n- ".join(invalidos[:8]) + (f"\n... e mais {len(invalidos) - 8}" if len(invalidos) > 8 else ""),
                tipo="alerta"
            )
            return

        if not edits:
            notificacao(page, "Nenhuma alteração", "Nenhuma alíquota foi preenchida.", tipo="alerta")
            return

        barra = barra_ref.current
        lbl_status = status_ref.current

        barra.visible = True
        lbl_status.value = "Salvando alterações..."
        page.update()

        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, salvar_aliquotas_backend, empresa_id, edits)

            if "erro" in res:
                notificacao(page, "Erro", f"Erro ao salvar: {res['erro']}", tipo="erro")
                return

            atualizados = res.get("atualizados", 0)
            notificacao(page, "Sucesso", f"{atualizados} registros atualizados (incluindo duplicatas)!", tipo="sucesso")

            await asyncio.sleep(1.5)

            # Verificar se ainda há alíquotas faltantes
            faltantes_restantes = res.get("faltantes_restantes", -1)
            if faltantes_restantes < 0:
                faltas = await loop.run_in_executor(None, listar_faltantes_backend, empresa_id, 1)
                faltantes_restantes = len(faltas or [])

            # Se não há mais faltantes, executar callback e finalizar
            if faltantes_restantes == 0:
                if callback_continuacao:
                    await callback_continuacao()
                    fecharDialogo(page)
                    return
                
                if finalizar_apos_salvar:
                    fecharDialogo(page)
                    return
                
                notificacao(page, "Concluído", "Todas as alíquotas foram preenchidas!", tipo="sucesso")
                await asyncio.sleep(1)
                fecharDialogo(page)
            else:
                # Ainda há faltantes - continuar no popup ou finalizar conforme solicitado
                if finalizar_apos_salvar or callback_continuacao:
                    # Se foi solicitado para finalizar após salvar ou há callback, 
                    # mesmo com faltantes, respeitar essa solicitação
                    if callback_continuacao:
                        await callback_continuacao()
                    fecharDialogo(page)
                    return
                
                # Caso contrário, carregar próximos faltantes no popup
                novos = await loop.run_in_executor(None, listar_faltantes_backend, empresa_id, 1000)
                dados.clear()
                dados.extend(novos or [])
                valores.clear()
                rebuild()

                if len(novos or []) == 0:
                    fecharDialogo(page)

        except Exception as e:
            import traceback
            traceback.print_exc()
            notificacao(page, "Erro", f"Erro ao salvar: {e}", tipo="erro")
        finally:
            barra.visible = False
            lbl_status.value = ""
            page.update()

    page.run_task(_run)

def exportarModelo(page, dados, ref_busca, aplicar_filtro_func):
    picker_save = FilePicker()

    def on_save(ev: FilePickerResultEvent):
        if not ev.path:
            return
        caminho = ev.path if ev.path.lower().endswith(".xlsx") else ev.path + ".xlsx"
        base = aplicar_filtro_func(dados, ref_busca.current.value)
        df = pd.DataFrame(
            [
                {
                    "codigo": x.get("codigo") or "",
                    "produto": x.get("produto") or "",
                    "ncm": (x.get("ncm") or ""),
                    "aliquota": "",
                }
                for x in base
            ],
            columns=["codigo", "produto", "ncm", "aliquota"],
        )
        try:
            with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="aliquotas_pendentes")
            notificacao(page, "Planilha gerada", f"Planilha modelo salva em:\n{caminho}", tipo="sucesso")
        except Exception as ex:
            notificacao(page, "Erro ao gerar planilha", f"Falha: {ex}", tipo="erro")

    picker_save.on_result = on_save
    page.overlay.append(picker_save)
    page.update()
    picker_save.save_file(
        file_name="Aliquotas Pendentes.xlsx",
        allowed_extensions=["xlsx"],
        dialog_title="Salvar planilha modelo",
    )

def importarModelo(page, dados, valores, rebuild, barra_ref, status_ref):
    picker_open = FilePicker()

    def on_open(ev: FilePickerResultEvent):
        if not ev.files:
            return

        caminho = ev.files[0].path

        async def _run():
            barra = barra_ref.current
            lbl_status = status_ref.current

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
                col_codigo = cols.get("codigo")
                col_produto = cols.get("produto")
                col_ncm = cols.get("ncm")
                col_aliq = cols.get("aliquota") or cols.get("aliq") or cols.get("aliq_icms")

                if not col_codigo or not col_produto or not col_ncm or not col_aliq:
                    notificacao(page, "Erro na planilha",
                        "A planilha deve conter as colunas: 'codigo', 'produto', 'ncm' e 'aliquota'.",
                        tipo="erro")
                    return

                for idx, row in df.iterrows():
                    cod = str(row.get(col_codigo)).strip()
                    prod = str(row.get(col_produto)).strip()
                    ncm = str(row.get(col_ncm)).strip()
                    aliq = str(row.get(col_aliq)).strip()

                    if not cod or not prod or not ncm or not aliq:
                        continue

                    if not eh_valida(aliq):
                        erros.append(f"Linha {idx + 2}: alíquota inválida '{aliq}'")
                        continue

                    encontrado = False
                    for d in dados:
                        if (
                            str(d.get("codigo")).strip() == cod and
                            str(d.get("produto")).strip() == prod and
                            str(d.get("ncm")).strip() == ncm
                        ):
                            valores[int(d["id"])] = aliq
                            importadas += 1
                            encontrado = True
                            break

                    if not encontrado:
                        erros.append(f"Linha {idx + 2}: código/produto/NCM não encontrado na listagem atual")

                rebuild()

                if importadas > 0:
                    msg = f"{importadas} alíquotas importadas da planilha."
                    if erros:
                        msg += f"\n\nAvisos/erros ({len(erros)}):\n" + "\n".join(erros[:6])
                        if len(erros) > 6:
                            msg += f"\n... e mais {len(erros) - 6}."
                    notificacao(page, "Importação concluída", msg, tipo="sucesso")
                else:
                    msg = "Nenhuma alíquota válida foi importada."
                    if erros:
                        msg += "\n\n" + "\n".join(erros[:6])
                    notificacao(page, "Importação incompleta", msg, tipo="alerta")

            except Exception as e:
                import traceback
                traceback.print_exc()
                notificacao(page, "Erro na importação", f"Erro ao processar planilha: {e}", tipo="erro")
            finally:
                barra.visible = False
                lbl_status.value = ""
                page.update()

        page.run_task(_run)

    picker_open.on_result = on_open
    page.overlay.append(picker_open)
    page.update()
    picker_open.pick_files(allowed_extensions=["xlsx"], dialog_title="Selecionar planilha preenchida")

def fecharDialogo(page, dialog=None):
    if dialog:
        dialog.open = False
    else:
        for o in page.overlay:
            if isinstance(o, ft.AlertDialog):
                o.open = False
    page.update()
