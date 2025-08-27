def fecharDialogo(page, dialog=None):
    if dialog:
        dialog.open = False
        page.dialog = None
    else:
        if page.dialog:
            page.dialog.open = False
            page.dialog = None
        else:
            for o in page.overlay:
                if hasattr(o, "open"):
                    o.open = False
    page.update()