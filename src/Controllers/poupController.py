import asyncio
import traceback
import pandas as pd
from flet import FilePicker, FilePickerResultEvent

from src.Config.Database.db import SessionLocal
from src.Components.notificao import notificacao

from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService
from src.Services.Aliquotas.aliquotaImportarService import AliquotaImportarService
from src.Utils.dialogo import fecharDialogo

class AliquotaPopupController:

    @staticmethod
    def salvar(page, dados, valores, empresa_id, rebuild, barra_ref, status_ref, retornarPos=False, etapa_pos=None):
        async def _run():
            barra = barra_ref.current
            status = status_ref.current

            barra.visible = True
            status.value = "Salvando alterações..."
            page.update()

            try:
                with SessionLocal() as db:
                    service = AliquotaPoupService(db)
                    resultado = service.salvar(empresa_id, dados, valores)

                    if resultado["status"] == "erro":
                        if resultado["vazios"]:
                            notificacao(
                                page, "Preenchimento obrigatório",
                                "Faltando:\n- " + "\n- ".join(resultado["vazios"][:8]) +
                                (f"\n... e mais {len(resultado['vazios']) - 8}" if len(resultado["vazios"]) > 8 else ""),
                                tipo="alerta"
                            )
                        elif resultado["invalidos"]:
                            notificacao(
                                page, "Alíquotas inválidas",
                                "Corrija:\n- " + "\n- ".join(resultado["invalidos"][:8]) +
                                (f"\n... e mais {len(resultado['invalidos']) - 8}" if len(resultado["invalidos"]) > 8 else ""),
                                tipo="alerta"
                            )
                        elif not resultado["edits"]:
                            notificacao(page, "Nenhuma alteração", "Nenhuma alíquota válida foi preenchida.", tipo="alerta")
                        return

                    notificacao(page, "Sucesso", f"{resultado['atualizados']} registros atualizados!", tipo="sucesso")

                    if resultado["faltantes_restantes"] == 0:
                        if retornarPos:
                            from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService
                            posService = PosProcessamentoService(db, empresa_id)
                            await posService.executarPos()
                        fecharDialogo(page)
                    else:
                        notificacao(page, "Atenção", "Ainda existem produtos sem alíquota!", tipo="alerta")

            except Exception as e:
                traceback.print_exc()
                notificacao(page, "Erro", f"Erro ao salvar: {e}", tipo="erro")

            finally:
                barra.visible = False
                status.value = ""
                page.update()

        page.run_task(_run)

    @staticmethod
    def importar(page, dados, valores, rebuild, barra_ref, status_ref):
        picker = FilePicker()

        def on_open(ev: FilePickerResultEvent):
            if not ev.files:
                return

            caminho = ev.files[0].path

            async def _run():
                barra = barra_ref.current
                status = status_ref.current

                barra.visible = True
                status.value = "Importando planilha..."
                page.update()

                try:
                    df = pd.read_excel(caminho, dtype=str)

                    with SessionLocal() as db:
                        resultado = AliquotaPoupService(db).importar_planilha(df, dados, valores)
                    rebuild()

                    if resultado["importadas"] > 0:
                        msg = f"{resultado['importadas']} alíquotas importadas da planilha."
                        if resultado["erros"]:
                            msg += "\n\nErros/Avisos:\n" + "\n".join(resultado["erros"][:6])
                            if len(resultado["erros"]) > 6:
                                msg += f"\n... e mais {len(resultado['erros']) - 6}."
                        notificacao(page, "Importação concluída", msg, tipo="sucesso")
                    else:
                        msg = "Nenhuma alíquota válida foi importada."
                        if resultado["erros"]:
                            msg += "\n\n" + "\n".join(resultado["erros"][:6])
                        notificacao(page, "Importação incompleta", msg, tipo="alerta")

                except Exception as e:
                    traceback.print_exc()
                    notificacao(page, "Erro na importação", f"Erro ao processar planilha: {e}", tipo="erro")
                finally:
                    barra.visible = False
                    status.value = ""
                    page.update()

            page.run_task(_run)

        picker.on_result = on_open
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allowed_extensions=["xlsx"], dialog_title="Selecionar planilha preenchida")

    @staticmethod
    def exportar(page, dados, ref_busca):
        picker = FilePicker()

        def on_save(ev: FilePickerResultEvent):
            if not ev.path:
                return

            caminho = ev.path if ev.path.lower().endswith(".xlsx") else ev.path + ".xlsx"
            termo_busca = ref_busca.current.value

            try:
                df = AliquotaPoupService(None).exportar_modelo(dados, termo_busca)
                with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Aliquotas Pendentes")
                notificacao(page, "Planilha gerada", f"Planilha modelo salva em:\n{caminho}", tipo="sucesso")
                AliquotaImportarService.abrirPlanilha(caminho)
            except Exception as ex:
                traceback.print_exc()
                notificacao(page, "Erro ao gerar planilha", f"Falha: {ex}", tipo="erro")

        picker.on_result = on_save
        page.overlay.append(picker)
        page.update()
        picker.save_file(
            file_name="Aliquotas Pendentes.xlsx",
            allowed_extensions=["xlsx"],
            dialog_title="Salvar planilha modelo"
        )
