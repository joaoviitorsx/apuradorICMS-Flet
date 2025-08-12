# src/Interface/telaPrincipal.py
from __future__ import annotations

import asyncio
import flet as ft

from src.Config.theme import STYLE, apply_theme
from src.Components.notificao import notificacao
from src.Controllers.tributacaoController import TributacaoController
from src.Controllers.spedController import SpedController
from src.Interface.telaPopupAliquota import abrir_dialogo_aliquotas


def TelaPrincipal(page: ft.Page, empresa_nome: str, empresa_id: int) -> ft.View:
    theme = apply_theme(page)

    nome_arquivo = ft.Ref[ft.Text]()
    status_envio = ft.Ref[ft.Text]()
    progress = ft.Ref[ft.ProgressBar]()
    mes_dropdown = ft.Ref[ft.Dropdown]()
    ano_dropdown = ft.Ref[ft.Dropdown]()
    status_text = ft.Ref[ft.Text]()

    # FilePickers únicos no overlay (reutilizáveis)
    file_picker_planilha = ft.FilePicker()
    file_picker_sped = ft.FilePicker()
    page.overlay.extend([file_picker_planilha, file_picker_sped])
    page.update()

    # ---------------- helpers UI ----------------
    def set_progress(pct: int, msg: str | None = None):
        progress.current.visible = True
        progress.current.value = max(0.0, min(1.0, pct / 100.0))
        if msg is not None:
            status_text.current.value = msg
        page.update()

    def clear_progress():
        progress.current.visible = False
        progress.current.value = 0
        status_text.current.value = ""
        page.update()

    # callback chamado pelo SpedController em thread separada
    def on_progress_cb(pct: int):
        pass

    def voltar(_):
        page.go("/empresa")

    def abrir_configuracoes(_):
        from src.Interface.telaProdutos import get_produtos_dialog
        page.open(get_produtos_dialog(page))

    # ---------------- importar planilha de tributação ----------------
    def enviar_tributacao(_):
        def on_file_selected(e: ft.FilePickerResultEvent):
            if not e.files:
                return

            caminho = e.files[0].path
            nome_arquivo.current.value = e.files[0].name
            status_envio.current.value = "Processando planilha..."
            status_text.current.value = "Lendo dados da planilha de tributação..."
            progress.current.visible = True
            page.update()

            async def importar_e_processar():
                try:
                    loop = asyncio.get_running_loop()
                    notificacao(page, "Importando Planilha", "Iniciando importação da planilha...", tipo="info")

                    resultado = await loop.run_in_executor(
                        None, TributacaoController.cadastrar_tributacao_por_planilha, caminho, empresa_id
                    )

                    clear_progress()

                    if isinstance(resultado, dict) and resultado.get("status") == "ok":
                        cadastrados = resultado.get("cadastrados", 0)
                        ja_existiam = resultado.get("ja_existiam", 0)
                        faltantes_restantes = resultado.get("faltantes_restantes", 0)
                        erros = resultado.get("erros", [])

                        if cadastrados and ja_existiam:
                            status_envio.current.value = f"{cadastrados} inseridos | {ja_existiam} já existiam"
                        elif cadastrados:
                            status_envio.current.value = f"{cadastrados} registros inseridos"
                        elif ja_existiam:
                            status_envio.current.value = f"Todos os {ja_existiam} já existiam"
                        else:
                            status_envio.current.value = "Nenhum registro processado"

                        notificacao(
                            page,
                            "Importação Concluída",
                            f"• {cadastrados} novos\n• {ja_existiam} já existiam\n"
                            f"• Faltantes de alíquota: {faltantes_restantes}",
                            tipo="sucesso" if cadastrados else "alerta",
                        )

                        if faltantes_restantes > 0:
                            # abre popup; ele buscará os itens faltantes e pode finalizar após salvar
                            abrir_dialogo_aliquotas(page, empresa_id, itens=None, finalizar_apos_salvar=True)

                        if erros:
                            resumo = "\n".join([f"• Linha {err['linha']}: {err['erro']}" for err in erros[:3]])
                            if len(erros) > 3:
                                resumo += f"\n• ... e mais {len(erros)-3} erro(s)"
                            notificacao(page, f"{len(erros)} Registro(s) Ignorado(s)", resumo, tipo="alerta")
                    else:
                        status_envio.current.value = "❌ Erro ao processar planilha"
                        notificacao(
                            page,
                            "Erro no Processamento",
                            (resultado or {}).get("mensagem", "Erro desconhecido ao processar a planilha"),
                            tipo="erro",
                        )

                except Exception as ex:
                    clear_progress()
                    status_envio.current.value = "❌ Falha inesperada"
                    notificacao(page, "Erro Crítico", f"Ocorreu um erro inesperado: {ex}", tipo="erro")
                finally:
                    page.update()

            page.run_task(importar_e_processar)

        file_picker_planilha.on_result = on_file_selected
        file_picker_planilha.pick_files(
            allowed_extensions=["xlsx"],
            dialog_title="Selecionar planilha de tributação"
        )

    # ---------------- importar e processar SPED ----------------
    def inserir_sped(_):
        def on_file_result(e: ft.FilePickerResultEvent):
            if not e.files:
                notificacao(page, "Arquivo não selecionado", "Por favor, selecione um arquivo SPED primeiro.", tipo="alerta")
                return
            
            caminho = e.files[0].path
            processar_arquivo_sped(caminho)

        def processar_arquivo_sped(caminho: str):
            async def _run():
                set_progress(0, "Iniciando importação do SPED...")
                try:
                    loop = asyncio.get_running_loop()
                    
                    def processar_sped_simples():
                        ctrl = SpedController()
                        return ctrl.processar_sped_completo(caminho, empresa_id)

                    resultado = await loop.run_in_executor(None, processar_sped_simples)
                    
                    print(f"[DEBUG] Resultado do processamento: {resultado}")
                    
                    if resultado.get("status") == "ok":
                        faltantes = resultado.get("aliquotas_faltantes", 0)
                        periodo_extraido = resultado.get("periodo", "")
                        
                        print(f"[DEBUG] Faltantes: {faltantes}")
                        
                        if faltantes > 0:
                            faltantes_lista = resultado.get("faltantes_lista", [])
                            print(f"[DEBUG] Lista de faltantes: {len(faltantes_lista) if faltantes_lista else 0}")
                            
                            notificacao(
                                page,
                                "SPED importado com pendências",
                                f"Importação concluída para o período {periodo_extraido}.\nHá {faltantes} alíquotas pendentes.",
                                tipo="alerta"
                            )
                            
                            # Define o callback de continuação
                            async def continuar_processamento():
                                print("[DEBUG] Continuando processamento após preenchimento de alíquotas...")
                                set_progress(85, "Finalizando processamento...")
                                try:
                                    def finalizar_sped():
                                        ctrl = SpedController()
                                        return ctrl.pos_finalizar(empresa_id, periodos=[periodo_extraido] if periodo_extraido else None)

                                    resultado_final = await loop.run_in_executor(None, finalizar_sped)
                                    
                                    if resultado_final.get("status") == "ok":
                                        set_progress(100, "Processamento concluído!")
                                        notificacao(
                                            page, 
                                            "Processamento concluído", 
                                            f"Apuração finalizada com sucesso para o período {periodo_extraido}!", 
                                            tipo="sucesso"
                                        )
                                    else:
                                        notificacao(
                                            page, 
                                            "Erro na finalização", 
                                            resultado_final.get("mensagem", "Erro ao finalizar"), 
                                            tipo="erro"
                                        )
                                except Exception as e:
                                    print(f"[DEBUG ERRO] Erro na continuação: {e}")
                                    notificacao(page, "Erro na finalização", f"Erro ao finalizar: {e}", tipo="erro")
                                finally:
                                    clear_progress()
                            
                            print("[DEBUG] Abrindo diálogo de alíquotas com callback...")
                            
                            # Abre diálogo de alíquotas com callback de continuação
                            abrir_dialogo_aliquotas(
                                page, 
                                empresa_id, 
                                itens=faltantes_lista, 
                                finalizar_apos_salvar=True,
                                callback_continuacao=continuar_processamento  # Passa o callback
                            )
                            
                            # Não limpa o progresso aqui, será limpo no callback
                            return
                        else:
                            # Se não há pendências, finaliza normalmente
                            set_progress(85, "Finalizando processamento...")
                            
                            def finalizar_sped():
                                ctrl = SpedController()
                                return ctrl.pos_finalizar(empresa_id, periodos=[periodo_extraido] if periodo_extraido else None)

                            resultado_final = await loop.run_in_executor(None, finalizar_sped)
                            
                            set_progress(100, "Processamento concluído!")
                            
                            if resultado_final.get("status") == "ok":
                                notificacao(
                                    page, 
                                    "SPED importado", 
                                    f"Importação e processamento concluídos com sucesso para o período {periodo_extraido}!", 
                                    tipo="sucesso"
                                )
                            else:
                                notificacao(
                                    page, 
                                    "Erro na finalização", 
                                    resultado_final.get("mensagem", "Erro ao finalizar"), 
                                    tipo="erro"
                                )
                    else:
                        notificacao(page, "Erro na importação", resultado.get("mensagem", "Erro desconhecido"), tipo="erro")
                
                except Exception as ex:
                    print(f"[DEBUG ERRO] Falha geral: {ex}")
                    import traceback
                    traceback.print_exc()
                    notificacao(page, "Erro inesperado", f"Falha durante importação: {ex}", tipo="erro")
                finally:
                    # Só limpa o progresso se não há alíquotas pendentes
                    if not hasattr(_run, '_tem_pendencias'):
                        clear_progress()

            page.run_task(_run)

        # Configurar o file picker para arquivos .txt
        file_picker_sped.on_result = on_file_result
        file_picker_sped.pick_files(
            dialog_title="Selecionar arquivo SPED (.txt)",
            allowed_extensions=["txt"],
            allow_multiple=False
        )

    # ---------------- baixar tabela ----------------
    def baixar_tabela(_):
        mes_selecionado = mes_dropdown.current.value
        ano_selecionado = ano_dropdown.current.value
        
        if not mes_selecionado or not ano_selecionado:
            notificacao(page, "Período não informado", "Selecione o mês e ano antes de prosseguir.", tipo="alerta")
            return
        
        # Converte mês para número
        meses = {
            "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04", 
            "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
            "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
        }
        
        periodo = f"{ano_selecionado}{meses[mes_selecionado]}"
        
        async def _baixar():
            set_progress(0, "Verificando dados para download...")
            try:
                loop = asyncio.get_running_loop()
                
                # Função que verifica se existem dados para o período e gera planilha
                def verificar_e_gerar_planilha():
                    # Aqui você implementaria a lógica para:
                    # 1. Verificar se existem dados processados para o período
                    # 2. Gerar a planilha de resultado
                    # 3. Retornar o caminho do arquivo gerado
                    return {
                        "status": "ok",
                        "arquivo_gerado": f"resultado_ICMS_{periodo}.xlsx",
                        "mensagem": f"Planilha gerada para {mes_selecionado}/{ano_selecionado}"
                    }
                
                resultado = await loop.run_in_executor(None, verificar_e_gerar_planilha)
                
                if resultado.get("status") == "ok":
                    notificacao(
                        page, 
                        "Download concluído", 
                        resultado.get("mensagem", "Planilha gerada com sucesso!"), 
                        tipo="sucesso"
                    )
                else:
                    notificacao(
                        page, 
                        "Dados não encontrados", 
                        f"Não foram encontrados dados processados para {mes_selecionado}/{ano_selecionado}.", 
                        tipo="alerta"
                    )
            
            except Exception as ex:
                notificacao(page, "Erro no download", f"Falha ao gerar planilha: {ex}", tipo="erro")
            finally:
                clear_progress()

        page.run_task(_baixar)

    # ---------------- UI ----------------
    header = ft.Container(
        padding=ft.Padding(0, 8, 0, 8),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon="ARROW_BACK", on_click=voltar, icon_color=theme["PRIMARY_COLOR"]),
                ft.IconButton(icon="SETTINGS", on_click=abrir_configuracoes, icon_color=theme["PRIMARY_COLOR"])
            ]
        )
    )

    card = ft.Container(
        width=680,
        height=650,
        padding=30,
        bgcolor=theme["CARD"],
        border_radius=STYLE["CARD_RADIUS"],
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            spacing=30,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Info da empresa
                ft.Container(
                    padding=ft.Padding(0, 0, 0, 8),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                bgcolor=theme["PRIMARY_COLOR"],
                                border_radius=24,
                                alignment=ft.alignment.center,
                                content=ft.Icon(name="business", color=theme["ON_PRIMARY"], size=28)
                            ),
                            ft.Column(
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(empresa_nome, size=22, weight=ft.FontWeight.BOLD, color=theme["PRIMARY_COLOR"]),
                                    ft.Text(f"ID: {empresa_id}", size=14, color=theme["TEXT_SECONDARY"])
                                ]
                            )
                        ]
                    )
                ),
                # Área de arquivos
                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    width=620,
                    padding=20,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=theme["BORDER"],
                        offset=ft.Offset(0, 8),
                        blur_style=ft.ShadowBlurStyle.NORMAL
                    ),
                    content=ft.Column(
                        spacing=18,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(name="folder_open", size=32, color=theme["FOLDER_ICON"]),
                                    ft.Text("Arquivos da empresa", size=16, weight=ft.FontWeight.W_600, color=theme["TEXT_SECONDARY"]),
                                ]
                            ),
                            ft.ElevatedButton(
                                text="Enviar Tributação (.xlsx)", icon="UPLOAD_FILE",
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"],
                                on_click=enviar_tributacao, width=260, height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                            ),
                            ft.Text(ref=nome_arquivo, value="Nenhum arquivo enviado", color=theme["TEXT"], size=14, italic=True),
                            ft.ElevatedButton(
                                text="Importar SPED (.txt)", icon="INSERT_DRIVE_FILE",
                                bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"],
                                on_click=inserir_sped, width=220, height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                            ),
                            ft.Text(ref=status_envio, value="Aguardando ação", color=theme["TEXT"], size=14, italic=True),
                        ]
                    )
                ),
                # Área de apuração
                ft.Container(
                    bgcolor=theme["BACKGROUND"],
                    padding=20,
                    border_radius=STYLE["BORDER_RADIUS_INPUT"],
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=theme["BORDER"],
                        offset=ft.Offset(0, 8),
                        blur_style=ft.ShadowBlurStyle.NORMAL
                    ),
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Row(
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(name="ASSESSMENT", size=32, color=theme["ASSETS_ICON"]),
                                    ft.Text("Apuração de ICMS", size=16, weight=ft.FontWeight.W_600, color=theme["TEXT_SECONDARY"]),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    ft.Dropdown(
                                        ref=mes_dropdown,
                                        width=160,
                                        hint_text="Mês",
                                        options=[ft.dropdown.Option(m) for m in [
                                            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                                            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]],
                                        bgcolor=theme["INPUT_BG"],
                                        border_color=theme["BORDER"],
                                        border_radius=8,
                                        color=theme["TEXT"]
                                    ),
                                    ft.Dropdown(
                                        ref=ano_dropdown,
                                        width=120,
                                        hint_text="Ano",
                                        options=[ft.dropdown.Option(str(y)) for y in range(2020, 2026)],
                                        bgcolor=theme["INPUT_BG"],
                                        border_color=theme["BORDER"],
                                        border_radius=8,
                                        color=theme["TEXT"]
                                    ),
                                    ft.ElevatedButton(
                                        text="Baixar Tabela", icon="DOWNLOAD",
                                        bgcolor=theme["PRIMARY_COLOR"], color=theme["ON_PRIMARY"],
                                        on_click=baixar_tabela, width=220, height=48,
                                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ]
                    )
                ),
                # Status / progresso
                ft.Container(
                    content=ft.Column(
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(ref=status_text, value="", color=theme["TEXT_SECONDARY"], size=14),
                            ft.ProgressBar(ref=progress, width=460, visible=False)
                        ]
                    )
                )
            ]
        )
    )

    return ft.View(
        route="/principal",
        bgcolor=theme["BACKGROUNDSCREEN"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
        controls=[
            header,
            ft.Container(content=card, alignment=ft.alignment.center, expand=True)
        ]
    )
