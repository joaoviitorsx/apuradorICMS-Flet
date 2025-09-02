import flet as ft
from src.Config.Database.db import SessionLocal
from src.Controllers.exportarController import ExportarController
from src.Services.Produto.produtoService import ProdutosService
from src.Components.notificao import notificacao

def buscarProdutos(empresa_id: int, pagina=1, limite=50, filtro_nome="", categoria_fiscal=""):
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        resultado = loop.run_until_complete(
            ExportarController.buscarProdutos(empresa_id, pagina, limite, filtro_nome, categoria_fiscal)
        )
        
        loop.close()
        return resultado
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar produtos: {e}")
        return {"produtos": [], "total": 0, "pagina": 1, "total_paginas": 0}

def buscarCategoriasFiscais(empresa_id: int = None):
    try:
        if not empresa_id:
            return ["regraGeral", "7CestaBasica", "12CestaBasica", "20RegraGeral", "28BebidaAlcoolica"]
        
        categorias = ExportarController.buscarCategoriasFiscais(empresa_id)
        
        if not categorias:
            return ["regraGeral", "7CestaBasica", "12CestaBasica", "20RegraGeral", "28BebidaAlcoolica"]
        
        return categorias
        
    except Exception as e:
        print(f"[ERRO] Erro ao buscar categorias: {e}")
        return ["regraGeral", "7CestaBasica", "12CestaBasica", "20RegraGeral", "28BebidaAlcoolica"]

def adicionarProduto(page: ft.Page, theme: dict, empresa_id: int, refs: dict):
    def fechar_modal(e):
        page.dialog.open = False
        page.update()
    
    def salvar_produto(e):
        if not codigo_field.value or not nome_field.value:
            notificacao(page, "Erro", "Código e Nome são obrigatórios", tipo="erro")
            return
        
        dados = {
            "codigo": codigo_field.value.strip(),
            "nome": nome_field.value.strip(),
            "ncm": ncm_field.value.strip() if ncm_field.value else "",
            "aliquota": aliquota_field.value.strip() if aliquota_field.value else "",
            "categoria_fiscal": categoria_dropdown.value if categoria_dropdown.value else ""
        }
        
        session = SessionLocal()
        try:
            service = ProdutosService(session)
            resultado = service.adicionarProduto(empresa_id, dados)
            
            if resultado["status"] == "sucesso":
                notificacao(page, "Sucesso", resultado["mensagem"], tipo="sucesso")
                fechar_modal(e)
                # Atualizar tabela se a função estiver disponível
                if "atualizar_tabela" in refs:
                    refs["atualizar_tabela"]()
            else:
                notificacao(page, "Erro", resultado["mensagem"], tipo="erro")
                
        except Exception as error:
            notificacao(page, "Erro", f"Erro inesperado: {str(error)}", tipo="erro")
        finally:
            session.close()
    
    # Campos do formulário
    codigo_field = ft.TextField(
        label="Código *",
        width=300,
        hint_text="Código único do produto"
    )
    nome_field = ft.TextField(
        label="Nome do Produto *",
        width=300,
        hint_text="Descrição do produto"
    )
    ncm_field = ft.TextField(
        label="NCM",
        width=300,
        hint_text="Nomenclatura Comum do Mercosul"
    )
    aliquota_field = ft.TextField(
        label="Alíquota (%)",
        width=300,
        hint_text="Ex: 18.00"
    )
    
    categorias = buscarCategoriasFiscais(empresa_id)
    opcoes_categoria = [ft.dropdown.Option("", "Selecione uma categoria")]
    opcoes_categoria.extend([ft.dropdown.Option(cat, cat) for cat in categorias])
    
    categoria_dropdown = ft.Dropdown(
        label="Categoria Fiscal",
        width=300,
        options=opcoes_categoria
    )
    
    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Adicionar Produto", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=400,
            content=ft.Column([
                ft.Text("* Campos obrigatórios", size=12, color=theme.get("TEXT_SECONDARY", "gray")),
                codigo_field,
                nome_field,
                ncm_field,
                aliquota_field,
                categoria_dropdown
            ], spacing=16, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.ElevatedButton(
                "Salvar",
                on_click=salvar_produto,
                bgcolor=theme.get("PRIMARY_COLOR", "blue"),
                color=theme.get("ON_PRIMARY", "white")
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    # ✅ CORREÇÃO: Usar page.overlay.append() em vez de page.append()
    page.overlay.append(modal)
    page.dialog = modal
    modal.open = True
    page.update()

def editarProduto(page: ft.Page, theme: dict, empresa_id: int, produto_id: int, refs: dict):
    session = SessionLocal()
    try:
        service = ProdutosService(session)
        resultado = service.buscarProdutoPorId(produto_id)
        
        if resultado["status"] != "sucesso":
            notificacao(page, "Erro", resultado["mensagem"], tipo="erro")
            return
        
        produto = resultado["produto"]
        
    except Exception as e:
        notificacao(page, "Erro", f"Erro ao buscar produto: {str(e)}", tipo="erro")
        return
    finally:
        session.close()
    
    def fechar_modal(e):
        page.dialog.open = False
        page.update()
    
    def salvar_edicao(e):
        if not codigo_field.value or not nome_field.value:
            notificacao(page, "Erro", "Código e Nome são obrigatórios", tipo="erro")
            return
        
        dados = {
            "codigo": codigo_field.value.strip(),
            "nome": nome_field.value.strip(),
            "ncm": ncm_field.value.strip() if ncm_field.value else "",
            "aliquota": aliquota_field.value.strip() if aliquota_field.value else "",
            "categoria_fiscal": categoria_dropdown.value if categoria_dropdown.value else ""
        }
        
        session = SessionLocal()
        try:
            service = ProdutosService(session)
            resultado = service.editarProduto(produto_id, dados)
            
            if resultado["status"] == "sucesso":
                notificacao(page, "Sucesso", resultado["mensagem"], tipo="sucesso")
                fechar_modal(e)
                # Atualizar tabela
                if "atualizar_tabela" in refs:
                    refs["atualizar_tabela"]()
            else:
                notificacao(page, "Erro", resultado["mensagem"], tipo="erro")
                
        except Exception as error:
            notificacao(page, "Erro", f"Erro inesperado: {str(error)}", tipo="erro")
        finally:
            session.close()
    
    # Campos do formulário preenchidos
    codigo_field = ft.TextField(
        label="Código *",
        width=300,
        value=produto["codigo"]
    )
    nome_field = ft.TextField(
        label="Nome do Produto *",
        width=300,
        value=produto["nome"]
    )
    ncm_field = ft.TextField(
        label="NCM",
        width=300,
        value=produto["ncm"]
    )
    aliquota_field = ft.TextField(
        label="Alíquota (%)",
        width=300,
        value=produto["aliquota"]
    )
    
    categorias = buscarCategoriasFiscais(empresa_id)
    opcoes_categoria = [ft.dropdown.Option("", "Selecione uma categoria")]
    opcoes_categoria.extend([ft.dropdown.Option(cat, cat) for cat in categorias])
    
    categoria_dropdown = ft.Dropdown(
        label="Categoria Fiscal",
        width=300,
        options=opcoes_categoria,
        value=produto["categoria_fiscal"] if produto["categoria_fiscal"] else None
    )
    
    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Editar Produto", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=400,
            content=ft.Column([
                ft.Text("* Campos obrigatórios", size=12, color=theme.get("TEXT_SECONDARY", "gray")),
                codigo_field,
                nome_field,
                ncm_field,
                aliquota_field,
                categoria_dropdown
            ], spacing=16, scroll=ft.ScrollMode.AUTO)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.ElevatedButton(
                "Salvar",
                on_click=salvar_edicao,
                bgcolor=theme.get("PRIMARY_COLOR", "blue"),
                color=theme.get("ON_PRIMARY", "white")
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    # ✅ CORRETO: page.overlay.append()
    page.overlay.append(modal)
    page.dialog = modal
    modal.open = True
    page.update()

def excluirProduto(page: ft.Page, theme: dict, produto_id: int, produto_nome: str, refs: dict):
    def confirmar_exclusao(e):
        session = SessionLocal()
        try:
            service = ProdutosService(session)
            resultado = service.excluirProduto(produto_id)
            
            if resultado["status"] == "sucesso":
                notificacao(page, "Sucesso", resultado["mensagem"], tipo="sucesso")
                if "atualizar_tabela" in refs:
                    refs["atualizar_tabela"]()
            else:
                notificacao(page, "Erro", resultado["mensagem"], tipo="erro")
                
        except Exception as error:
            notificacao(page, "Erro", f"Erro inesperado: {str(error)}", tipo="erro")
        finally:
            session.close()
        
        page.dialog.open = False
        page.update()
    
    def cancelar_exclusao(e):
        page.dialog.open = False
        page.update()
    
    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Exclusão", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            width=500,  
            height=200, 
            content=ft.Column([
                ft.Text("Tem certeza que deseja excluir este produto?"),
                ft.Text(f"Produto:", weight=ft.FontWeight.BOLD),
                ft.Text(f"{produto_nome}", size=16),
                ft.Text("Esta ação não pode ser desfeita.", color="red", size=12)
            ], spacing=8)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar_exclusao),
            ft.ElevatedButton("Excluir", on_click=confirmar_exclusao, bgcolor="red", color="white")
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.overlay.append(modal)
    page.dialog = modal
    modal.open = True
    page.update()