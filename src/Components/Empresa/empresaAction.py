def on_empresa_change(ref_button, ref_dropdown, page):
    ref_button.current.disabled = not bool(ref_dropdown.current.value)
    page.update()

def on_entrar_click(ref_dropdown, page):
    empresa_id = ref_dropdown.current.value
    empresa_nome = next(
        (opt.text for opt in ref_dropdown.current.options if opt.key == empresa_id),
        "Empresa"
    )
    page.go(f"/principal?id={empresa_id}&nome={empresa_nome}")

def on_cadastrar_click(page):
    page.go("/cadastro")
