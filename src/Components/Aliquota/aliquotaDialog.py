from .aliquotaUI import criarDialogoAliquota

def abrirDialogoAliquotas(page, empresa_id, itens=None, page_size=200, finalizar_apos_salvar=False, callback_continuacao=None):
    janela = criarDialogoAliquota(
        page=page,
        empresa_id=empresa_id,
        itens=itens,
        page_size=page_size,
        finalizar_apos_salvar=finalizar_apos_salvar,
        callback_continuacao=callback_continuacao,
    )

    page.overlay.append(janela)
    page.update()