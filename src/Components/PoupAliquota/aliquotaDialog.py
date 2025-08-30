import flet as ft
from .aliquotaUI import criarDialogoAliquota

def abrirDialogoAliquotas(page, empresa_id, itens=None, page_size=350, retornar_pos=False, etapa_pos=None):
    janela = criarDialogoAliquota(
        page=page,
        empresa_id=empresa_id,
        itens=itens,
        page_size=page_size,
        retornar_pos=retornar_pos,
        etapa_pos=etapa_pos
    )

    page.overlay.append(janela)
    page.dialog = janela
    janela.open = True
    page.update()