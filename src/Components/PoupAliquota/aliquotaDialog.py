import flet as ft
from .aliquotaUI import criarDialogoAliquota

def abrirDialogoAliquotas(page, empresa_id, itens=None, page_size=350, finalizar_apos_salvar=False, callback_continuacao=None, retornar_pos=False):
    janela = criarDialogoAliquota(
        page=page,
        empresa_id=empresa_id,
        itens=itens,
        page_size=page_size,
        finalizar_apos_salvar=finalizar_apos_salvar,
        callback_continuacao=callback_continuacao,
        retornar_pos=retornar_pos
    )

    page.overlay.append(janela)
    page.dialog = janela
    janela.open = True
    page.update()

