import flet as ft
from src.Config.Database.db import SessionLocal
from src.Controllers.exportarController import ExportarController

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
        

def adicionarProduto(page, theme):
    def fechar_modal(e):
        page.dialog.open = False
        page.update()
    
    def salvar_produto(e):
        # Aqui você implementaria a lógica de salvar no banco
        print("Salvando produto...")
        fechar_modal(e)
    
    # Campos do formulário
    codigo_field = ft.TextField(label="Código", width=300)
    nome_field = ft.TextField(label="Nome do Produto", width=300)
    ncm_field = ft.TextField(label="NCM", width=300)
    aliquota_field = ft.TextField(label="Alíquota (%)", width=300)
    categoria_dropdown = ft.Dropdown(
        label="Categoria Fiscal",
        width=300,
        options=[
            ft.dropdown.Option("ST", "Substituição Tributária"),
            ft.dropdown.Option("NORMAL", "Normal"),
            ft.dropdown.Option("ISENTO", "Isento"),
            ft.dropdown.Option("DIFERIDO", "Diferido")
        ]
    )
    
    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Adicionar Produto"),
        content=ft.Container(
            width=400,
            content=ft.Column([
                codigo_field,
                nome_field,
                ncm_field,
                aliquota_field,
                categoria_dropdown
            ], spacing=16)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.ElevatedButton("Salvar", on_click=salvar_produto)
        ]
    )
    
    page.dialog = modal
    modal.open = True
    page.update()

def editarProduto(page, produto_id):
    """Modal para editar produto"""
    print(f"Editando produto {produto_id}")
    # Implementar modal de edição similar ao de adicionar

def excluirProduto(page, produto_id):
    """Confirmar exclusão do produto"""
    def confirmar_exclusao(e):
        # Implementar exclusão no banco
        print(f"Excluindo produto {produto_id}")
        page.dialog.open = False
        page.update()
    
    def cancelar_exclusao(e):
        page.dialog.open = False
        page.update()
    
    modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Exclusão"),
        content=ft.Text("Tem certeza que deseja excluir este produto?"),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar_exclusao),
            ft.ElevatedButton("Excluir", on_click=confirmar_exclusao, color="red")
        ]
    )
    
    page.dialog = modal
    modal.open = True
    page.update()