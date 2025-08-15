from .aliquotaUI import criar_dialogo_aliquota

def abrir_dialogo_aliquotas(page, empresa_id, itens=None, page_size=200, finalizar_apos_salvar=False, callback_continuacao=None):
    dlg = criar_dialogo_aliquota(
        page=page,
        empresa_id=empresa_id,
        itens=itens,
        page_size=page_size,
        finalizar_apos_salvar=finalizar_apos_salvar,
        callback_continuacao=callback_continuacao,
    )
    page.overlay.insert(0, dlg)
    dlg.open = True
    page.update()