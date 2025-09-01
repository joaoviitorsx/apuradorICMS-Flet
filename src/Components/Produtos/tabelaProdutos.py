import flet as ft
from .CrudAction import editarProduto, excluirProduto, buscarProdutos

PAGE_SIZE = 25

def cardTabelaProdutos(page: ft.Page, refs: dict, theme: dict, empresa_id: int):
    refs["pagina_atual"] = 1
    refs["dados_produtos"] = {"produtos": [], "total": 0, "total_paginas": 0}
    refs["empresa_id"] = empresa_id
    
    refs["tabela_ref"] = ft.Ref[ft.DataTable]()
    refs["info_paginacao"] = ft.Ref[ft.Text]()
    refs["btn_anterior"] = ft.Ref[ft.ElevatedButton]()
    refs["btn_proximo"] = ft.Ref[ft.ElevatedButton]()

    def obter_filtros():
        filtro_nome = ""
        categoria_fiscal = ""
        
        if "input_filtro" in refs and refs["input_filtro"].current:
            filtro_nome = refs["input_filtro"].current.value or ""
            filtro_nome = filtro_nome.strip()
        
        if "dropdown_categoria" in refs and refs["dropdown_categoria"].current:
            categoria_valor = refs["dropdown_categoria"].current.value
            
            if (categoria_valor and 
                categoria_valor.strip() != "" and 
                categoria_valor != "Todas as categorias"):
                categoria_fiscal = categoria_valor.strip()
            else:
                categoria_fiscal = ""
        
        print(f"[DEBUG] Filtros obtidos - Nome: '{filtro_nome}', Categoria: '{categoria_fiscal}'")
        print(f"[DEBUG] Filtro nome vazio: {filtro_nome == ''}, Filtro categoria vazio: {categoria_fiscal == ''}")
        
        return {"nome": filtro_nome, "categoria": categoria_fiscal}

    def atualizarTabela():
        try:
            filtros = obter_filtros()
            pagina = refs["pagina_atual"]
            
            print(f"[DEBUG] Atualizando tabela - Página {pagina}, Empresa {empresa_id}")
            print(f"[DEBUG] Filtros aplicados: {filtros}")
            
            resultado = buscarProdutos(
                empresa_id=empresa_id,
                pagina=pagina,
                limite=PAGE_SIZE,
                filtro_nome=filtros.get("nome", ""),
                categoria_fiscal=filtros.get("categoria", "")
            )
            
            print(f"[DEBUG] Resultado da busca: {resultado}")
            
            refs["dados_produtos"] = resultado
            
            # Atualizar tabela
            if refs["tabela_ref"].current:
                tabela = refs["tabela_ref"].current
                tabela.rows.clear()
                
                for produto in resultado["produtos"]:
                    linha = ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        produto["codigo"], 
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    width=80,
                                    padding=ft.padding.all(8)
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        produto["nome"], 
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    width=250,
                                    padding=ft.padding.all(8)
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        produto["ncm"], 
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    width=100,
                                    padding=ft.padding.all(8)
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        f"{produto['aliquota']}%", 
                                        size=11,
                                        text_align=ft.TextAlign.CENTER
                                    ),
                                    width=70,
                                    padding=ft.padding.all(8),
                                    alignment=ft.alignment.center
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        produto["categoria_fiscal"], 
                                        size=11,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    width=100,
                                    padding=ft.padding.all(8)
                                )
                            ),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Row([
                                        ft.IconButton(
                                            icon="EDIT",
                                            tooltip="Editar",
                                            icon_size=18,
                                            icon_color=theme.get("PRIMARY_COLOR", "blue"),
                                            on_click=lambda e, pid=produto["id"]: [
                                                editarProduto(page, pid),
                                                atualizarTabela()
                                            ]
                                        ),
                                        ft.IconButton(
                                            icon="DELETE",
                                            tooltip="Excluir",
                                            icon_size=18,
                                            icon_color="red",
                                            on_click=lambda e, pid=produto["id"]: [
                                                excluirProduto(page, pid),
                                                atualizarTabela()
                                            ]
                                        ),
                                    ], spacing=0, tight=True),
                                    width=80,
                                    padding=ft.padding.all(8),
                                    alignment=ft.alignment.center
                                )
                            )
                        ]
                    )
                    tabela.rows.append(linha)
            
            if refs["info_paginacao"].current:
                dados = refs["dados_produtos"]
                total_paginas = dados.get('total_paginas', 0)
                if total_paginas == 0:
                    refs["info_paginacao"].current.value = "Nenhum produto encontrado"
                else:
                    refs["info_paginacao"].current.value = f"Página {dados['pagina']} de {total_paginas} ({dados['total']} produtos)"
            
            if refs["btn_anterior"].current:
                refs["btn_anterior"].current.disabled = refs["pagina_atual"] <= 1
            
            if refs["btn_proximo"].current:
                refs["btn_proximo"].current.disabled = refs["pagina_atual"] >= refs["dados_produtos"]["total_paginas"]
            
            page.update()
            
        except Exception as e:
            print(f"[ERRO] Erro ao atualizar tabela: {e}")
            import traceback
            traceback.print_exc()

    def ir_para_pagina(pagina):
        refs["pagina_atual"] = pagina
        atualizarTabela()

    def aplicar_filtros():
        refs["pagina_atual"] = 1
        atualizarTabela()

    def pagina_anterior(e):
        if refs["pagina_atual"] > 1:
            ir_para_pagina(refs["pagina_atual"] - 1)

    def proxima_pagina(e):
        if refs["pagina_atual"] < refs["dados_produtos"]["total_paginas"]:
            ir_para_pagina(refs["pagina_atual"] + 1)

    refs["atualizar_tabela"] = atualizarTabela
    refs["ir_para_pagina"] = ir_para_pagina
    refs["aplicar_filtros"] = aplicar_filtros

    # Container principal
    container = ft.Container(
        bgcolor=theme["CARD"],
        padding=20,
        border_radius=8,
        expand=True,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=theme["BORDER"],
            offset=ft.Offset(0, 8),
            blur_style=ft.ShadowBlurStyle.NORMAL
        ),
        content=ft.Column(
            spacing=16,
            expand=True,
            controls=[
                # Cabeçalho da tabela
                ft.Row([
                    ft.Text("Lista de Produtos", size=16, weight=ft.FontWeight.W_600, color=theme["TEXT"]),
                    ft.Text(
                        ref=refs["info_paginacao"],
                        value="Carregando...",
                        size=12,
                        color=theme["TEXT_SECONDARY"]
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(
                    content=ft.ResponsiveRow([
                        ft.DataTable(
                            ref=refs["tabela_ref"],
                            columns=[
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("Código", weight=ft.FontWeight.BOLD, size=12),
                                        width=80,
                                        padding=ft.padding.all(8)
                                    )
                                ),
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("Produto", weight=ft.FontWeight.BOLD, size=12),
                                        width=250,
                                        padding=ft.padding.all(8)
                                    )
                                ),
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("NCM", weight=ft.FontWeight.BOLD, size=12),
                                        width=100,
                                        padding=ft.padding.all(8)
                                    )
                                ),
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("Alíquota", weight=ft.FontWeight.BOLD, size=12),
                                        width=70,
                                        padding=ft.padding.all(8),
                                        alignment=ft.alignment.center
                                    )
                                ),
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("Categoria", weight=ft.FontWeight.BOLD, size=12),
                                        width=100,
                                        padding=ft.padding.all(8)
                                    )
                                ),
                                ft.DataColumn(
                                    label=ft.Container(
                                        content=ft.Text("Ações", weight=ft.FontWeight.BOLD, size=12),
                                        width=80,
                                        padding=ft.padding.all(8),
                                        alignment=ft.alignment.center
                                    )
                                ),
                            ],
                            rows=[],
                            border=ft.border.all(1, theme["BORDER"]),
                            border_radius=8,
                            vertical_lines=ft.border.BorderSide(1, theme["BORDER"]),
                            horizontal_lines=ft.border.BorderSide(1, theme["BORDER"]),
                            heading_row_color=theme.get("CARD_SECONDARY", "#f5f5f5"),
                            show_checkbox_column=False,
                            column_spacing=0
                        )
                    ]),
                    expand=True,
                    bgcolor=theme.get("BACKGROUND", "white"),
                    border_radius=8,
                    border=ft.border.all(1, theme["BORDER"]),
                    padding=ft.padding.all(8)
                ),
                
                # Controles de paginação
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            ft.ElevatedButton(
                                ref=refs["btn_anterior"],
                                text="◀ Anterior",
                                on_click=pagina_anterior,
                                bgcolor=theme["BORDER"],
                                color=theme["TEXT"],
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6)
                                )
                            ),
                            ft.ElevatedButton(
                                ref=refs["btn_proximo"],
                                text="Próxima ▶",
                                on_click=proxima_pagina,
                                bgcolor=theme["BORDER"],
                                color=theme["TEXT"],
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6)
                                )
                            ),
                        ]
                    ),
                    padding=ft.padding.symmetric(vertical=8)
                )
            ]
        )
    )
    
    def carregar_inicial():
        print("[DEBUG] Iniciando carregamento inicial da tabela...")
        atualizarTabela()
    
    import threading
    threading.Timer(0.1, carregar_inicial).start()
    
    return container