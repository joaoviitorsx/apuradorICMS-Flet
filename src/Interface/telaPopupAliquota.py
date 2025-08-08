import flet as ft
from src.Components.notificao import notificacao

# Dados simulados para carregar na tabela
mock_dados = [
    {"id": 1, "codigo": "1001", "produto": "Sabonete", "ncm": "34011190", "aliquota": ""},
    {"id": 2, "codigo": "1002", "produto": "Detergente", "ncm": "34022000", "aliquota": ""},
    {"id": 3, "codigo": "1003", "produto": "Shampoo", "ncm": "33051000", "aliquota": ""},
]

def TelaPopupAliquota(page: ft.Page, empresa_id: int):
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("ID")),
            ft.DataColumn(label=ft.Text("Código")),
            ft.DataColumn(label=ft.Text("Produto")),
            ft.DataColumn(label=ft.Text("NCM")),
            ft.DataColumn(label=ft.Text("Alíquota")),
        ],
        rows=[],
        border=ft.border.all(1, ft.colors.GREY_600),
        column_spacing=15,
        heading_row_color=ft.colors.BLUE_GREY_100,
        data_row_color={"hovered": ft.colors.BLUE_GREY_50},
    )

    def carregar_dados():
        tabela.rows.clear()
        for item in mock_dados:
            tabela.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(item["id"]))),
                    ft.DataCell(ft.Text(item["codigo"])),
                    ft.DataCell(ft.Text(item["produto"])),
                    ft.DataCell(ft.Text(item["ncm"])),
                    ft.DataCell(ft.TextField(value=item["aliquota"], width=80)),
                ]
            ))
        page.update()

    def salvar_dados(e):
        pendentes = []
        for idx, row in enumerate(tabela.rows):
            produto = row.cells[2].content.value
            aliquota = row.cells[4].content.value.strip()
            if not aliquota:
                pendentes.append(f"Linha {idx+1}: {produto}")

        if pendentes:
            detalhes = "\n".join(pendentes[:10])
            if len(pendentes) > 10:
                detalhes += f"\n... e mais {len(pendentes)-10} produtos."
            notificacao(page, "Campos obrigatórios", f"Preencha as alíquotas nas linhas abaixo:\n\n{detalhes}", tipo="alerta")
            return

        notificacao(page, "Sucesso", "Alíquotas salvas com sucesso.", tipo="sucesso")
        page.go("/principal")  # Simula retorno a tela principal

    btn_salvar = ft.ElevatedButton("Salvar Tudo", on_click=salvar_dados, bgcolor=ft.colors.GREEN)

    conteudo = ft.Column([
        ft.Text("Preencha as alíquotas nulas antes de prosseguir:", size=18, weight=ft.FontWeight.BOLD),
        tabela,
        btn_salvar
    ], spacing=25, scroll=ft.ScrollMode.AUTO)

    carregar_dados()

    return ft.View("/popup_aliquota", controls=[
        ft.Container(
            content=conteudo,
            padding=30,
            bgcolor=ft.colors.BLUE_GREY_900,
            alignment=ft.alignment.top_center
        )
    ])