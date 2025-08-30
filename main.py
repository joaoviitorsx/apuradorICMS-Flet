import flet as ft

def main(page: ft.Page):
    picker = ft.FilePicker()

    def salvar_arquivo(e):
        picker.save_file(dialog_title="Salvar",file_name="teste.xlsx",allowed_extensions=["xlsx"])
            
    picker.on_result = lambda e: print(f"Caminho escolhido: {e.path}")
    page.overlay.append(picker)
    page.controls.append(ft.ElevatedButton("Salvar Arquivo", on_click=salvar_arquivo))
    page.controls.append(picker)
    page.update()

ft.app(target=main)
