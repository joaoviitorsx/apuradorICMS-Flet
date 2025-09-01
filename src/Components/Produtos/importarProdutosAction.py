import flet as ft
from src.Controllers.tributacaoController import TributacaoController
from src.Components.notificao import notificacao

def importarProdutos(page: ft.Page, empresa_id: int = None, refs: dict = None):
    if not empresa_id:
        notificacao(page, "Erro", "ID da empresa não informado.", tipo="erro")
        return
    
    def processar_importacao(result):
        if not result.files:
            notificacao(page, "Aviso", "Nenhum arquivo selecionado.", tipo="aviso")
            return
        
        caminho_arquivo = result.files[0].path
        nome_arquivo = result.files[0].name
        
        print(f"[DEBUG] Iniciando importação: {nome_arquivo}")
        
        try:
            notificacao(page, "Processando", f"Importando planilha: {nome_arquivo}...", tipo="info")
            
            resultado = TributacaoController.importarPlanilhaTributacao(caminho_arquivo, empresa_id)
            
            print(f"[DEBUG] Resultado recebido: {resultado}")
            
            if resultado.get("status") == "ok":
                cadastrados = resultado.get("cadastrados", 0)
                ja_existiam = resultado.get("ja_existiam", 0) 
                atualizados = resultado.get("atualizados", 0)
                faltantes_restantes = resultado.get("faltantes_restantes", 0)
                erros = resultado.get("erros", [])
                total_processados = resultado.get("total_processados", 0)
                
                # Criar mensagem de sucesso detalhada
                if cadastrados > 0 or atualizados > 0:
                    mensagem_sucesso = []
                    
                    if cadastrados > 0:
                        mensagem_sucesso.append(f"• {cadastrados} produtos novos cadastrados")
                    
                    if atualizados > 0:
                        mensagem_sucesso.append(f"• {atualizados} produtos atualizados")
                        
                    if ja_existiam > 0:
                        mensagem_sucesso.append(f"• {ja_existiam} produtos já existiam")
                    
                    if faltantes_restantes > 0:
                        mensagem_sucesso.append(f"• {faltantes_restantes} produtos precisam de configuração de alíquota")
                    
                    if total_processados > 0:
                        mensagem_sucesso.append(f"• Total de {total_processados} linhas processadas")
                    
                    notificacao(page,"Importação Concluída com Sucesso!","\n".join(mensagem_sucesso),tipo="sucesso")
                           
                else:
                    notificacao(
                        page,
                        "Importação Finalizada",
                        "Nenhum produto novo foi adicionado. Todos os produtos já existiam no banco de dados.",
                        tipo="aviso"
                    )
                
                # Mostrar erros se houver
                if erros and len(erros) > 0:
                    resumo_erros = []
                    
                    for i, erro in enumerate(erros[:3]):
                        if isinstance(erro, dict):
                            linha = erro.get('linha', 'N/A')
                            descricao = erro.get('erro', str(erro))
                            resumo_erros.append(f"• Linha {linha}: {descricao}")
                        else:
                            resumo_erros.append(f"• {str(erro)}")
                    
                    if len(erros) > 3:
                        resumo_erros.append(f"• ... e mais {len(erros)-3} problema(s)")
                    
                    notificacao(
                        page, 
                        f"{len(erros)} Registro(s) com Problema", 
                        "\n".join(resumo_erros), 
                        tipo="alerta"
                    )
                
                # ATUALIZAR A TABELA APÓS IMPORTAÇÃO BEM-SUCEDIDA
                if refs and "atualizar_tabela" in refs:
                    print("[DEBUG] Atualizando tabela após importação...")
                    try:
                        refs["atualizar_tabela"]()
                        print("[DEBUG] Tabela atualizada com sucesso!")
                    except Exception as update_error:
                        print(f"[DEBUG] Erro ao atualizar tabela: {update_error}")
                
                print(f"[DEBUG] Importação concluída com sucesso")
                
            elif resultado.get("status") == "erro":
                mensagem_erro = resultado.get("mensagem", "Erro desconhecido durante a importação.")
                print(f"[DEBUG] Erro na importação: {mensagem_erro}")
                
                notificacao(
                    page, 
                    "Erro na Importação", 
                    mensagem_erro, 
                    tipo="erro"
                )
                
            else:
                print(f"[DEBUG] Status desconhecido: {resultado}")
                notificacao(
                    page, 
                    "Resultado Inesperado", 
                    f"Status retornado: {resultado.get('status', 'indefinido')}", 
                    tipo="alerta"
                )
                
        except Exception as e:
            print(f"[DEBUG] Exceção durante importação: {e}")
            import traceback
            traceback.print_exc()
            notificacao(
                page, 
                "Erro Crítico", 
                f"Erro inesperado durante a importação: {str(e)}", 
                tipo="erro"
            )
    
    def on_file_picker_result(e: ft.FilePickerResultEvent):
        processar_importacao(e)
    
    try:
        picker = ft.FilePicker(on_result=on_file_picker_result)
        page.overlay.append(picker)
        page.update()
        
        picker.pick_files(
            dialog_title="Selecionar planilha de produtos para importação",
            allowed_extensions=["xlsx"],
            allow_multiple=False
        )
        
        print(f"[DEBUG] FilePicker aberto para empresa {empresa_id}")
        
    except Exception as e:
        print(f"[DEBUG] Erro ao abrir FilePicker: {e}")
        notificacao(page, "Erro", f"Erro ao abrir seletor de arquivo: {str(e)}", tipo="erro")