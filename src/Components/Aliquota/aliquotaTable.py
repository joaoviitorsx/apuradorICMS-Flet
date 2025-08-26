import flet as ft
from typing import List, Dict, Callable
from src.Utils.aliquota import validado

def construirTabela(base_items: List[Dict],valores: dict,on_change_valor: Callable[[int, str], None],th: dict) -> ft.Container:
    cols = [
        ft.DataColumn(
            label=ft.Container(
                content=ft.Text("Código", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                width=120,
                alignment=ft.alignment.center_left,
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                content=ft.Text("Produto", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                width=400,
                alignment=ft.alignment.center_left,
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                content=ft.Text("NCM", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                width=100,
                alignment=ft.alignment.center,
            )
        ),
        ft.DataColumn(
            label=ft.Container(
                content=ft.Text("Alíquota", size=12, weight=ft.FontWeight.BOLD, color=th["TEXT"]),
                width=120,
                alignment=ft.alignment.center,
            )
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

        if valor_atual and not validado(valor_atual):
            tf.border_color = th["ERROR"]

        row = ft.DataRow(
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
                        height=45,
                        padding=ft.padding.all(2),
                        alignment=ft.alignment.center,
                    )
                ),
            ]
        )

        rows.append(row)

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
