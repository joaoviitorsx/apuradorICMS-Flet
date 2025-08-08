import flet as ft

from src.Interface.telaEmpresa import TelaEmpresa
from src.Interface.telaCadastro import TelaCadastro
from src.Interface.telaPrincipal import TelaPrincipal
from src.Interface.telaPopupAliquota import TelaPopupAliquota 

def main(page: ft.Page):
    page.title = "Apurador de ICMS - Assertivus"

    page.window.width = 1000
    page.window.height = 950
    page.window.resizable = True
    page.window.icon = "images/icone.ico"

    # Roteamento
    def route_change(e):
        page.views.clear()
        rota = page.route
        print(f"[ROUTE] Navegando para: {rota}")

        if rota in ["/", "/empresa"]:
            page.views.append(TelaEmpresa(page))

        elif rota == "/cadastro":
            page.views.append(TelaCadastro(page))

        elif rota == "/principal":
            page.views.append(TelaPrincipal(page, empresa_nome="Assertivus Contábil", empresa_id=1))

        elif rota == "/aliquotas":
            page.views.append(TelaPopupAliquota(page, empresa_id=1))

        else:
            page.views.append(ft.View("/", controls=[
                ft.Text("Página não encontrada.", size=20, weight=ft.FontWeight.BOLD)
            ]))

        page.update()

    page.on_route_change = route_change
    page.go("/empresa")

ft.app(target=main, assets_dir="assets")
