import flet as ft

from src.Interface.telaEmpresa import TelaEmpresa
from src.Interface.telaCadastro import TelaCadastro
from src.Interface.telaPrincipal import TelaPrincipal
from src.Interface.telaPopupAliquota import abrirDialogoAliquotas
from src.Utils.path import resourcePath

def main(page: ft.Page):
    page.title = "Apurador de ICMS - Assertivus"

    page.window.width = 1280
    page.window.height = 850
    page.window.resizable = True
    page.window.icon = resourcePath("src/Assets/images/icone.ico")

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()

        if e.route == "/empresa":
            from src.Interface.telaEmpresa import TelaEmpresa
            page.views.append(TelaEmpresa(page))

        elif e.route == "/cadastro":
            from src.Interface.telaCadastro import TelaCadastro
            page.views.append(TelaCadastro(page))

        elif e.route.startswith("/principal"):
            from src.Interface.telaPrincipal import TelaPrincipal
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(e.route)
            params = parse_qs(parsed_url.query)

            empresa_id = int(params.get("id", [0])[0])
            empresa_nome = params.get("nome", [""])[0]

            page.views.append(TelaPrincipal(page, empresa_nome=empresa_nome, empresa_id=empresa_id))

        elif e.route.startswith("/produtos"):
            from src.Interface.telaProdutos import TelaProdutos
            from urllib.parse import urlparse, parse_qs

            parsed_url = urlparse(e.route)
            params = parse_qs(parsed_url.query)
            
            empresa_id = int(params.get("id", [0])[0])
            empresa_nome = params.get("nome", [""])[0]
            
            page.views.append(TelaProdutos(page, empresa_id=empresa_id, empresa_nome=empresa_nome))

        page.update()

    page.on_route_change = route_change
    page.go("/empresa")

ft.app(target=main, assets_dir="assets")