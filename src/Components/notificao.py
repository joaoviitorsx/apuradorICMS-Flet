import flet as ft
import threading
import time

def notificacao(page: ft.Page, titulo: str, mensagem: str, tipo: str = "info"):
    tipos = {
        "sucesso": {"bg": "#1fb355", "text": "white", "icon": ft.Icons.CHECK_CIRCLE},
        "erro": {"bg": "#db3e3e", "text": "white", "icon": ft.Icons.ERROR},
        "info": {"bg": "#3474dc", "text": "white", "icon": ft.Icons.INFO},
        "alerta": {"bg": "#db8f0b", "text": "white", "icon": ft.Icons.WARNING},
    }


    estilo = tipos.get(tipo, tipos["info"])

    def calcular_altura(titulo: str, mensagem: str) -> int:
        base = 32
        chars_linha_titulo = 45
        chars_linha_msg = 50
        linhas_titulo = (len(titulo) // chars_linha_titulo) + 1
        linhas_msg = (len(mensagem) // chars_linha_msg) + 1
        return min(200, base + (linhas_titulo * 18) + (linhas_msg * 16) + 20)

    altura_dinamica = calcular_altura(titulo, mensagem)

    # Criação do conteúdo da notificação
    conteudo = ft.Card(
        elevation=20,
        content=ft.Container(
            bgcolor=estilo["bg"],
            padding=16,
            border_radius=12,
            content=ft.Row(
                controls=[
                    ft.Icon(estilo["icon"], color=estilo["text"], size=26),
                    ft.Column([
                        ft.Text(titulo, color=estilo["text"], weight="bold", size=15),
                        ft.Text(mensagem, color=estilo["text"], size=13),
                    ], spacing=4, expand=True)
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        )
    )

    container = ft.Container(
        content=conteudo,
        width=420,
        height=altura_dinamica,
        right=20,
        bottom=20,
        opacity=0,
        offset=ft.Offset(0.5, 0),
        animate_opacity=ft.Animation(300, "easeOut"),
        animate_offset=ft.Animation(300, "easeOut"),
        animate_position=ft.Animation(300, "easeOut")
    )

    container.altura_notificacao = altura_dinamica  # Custom attr para empilhamento

    # Empilhamento: Reposiciona as notificações já existentes
    notificacoes_visiveis = [
        c for c in page.overlay
        if isinstance(c, ft.Container) and hasattr(c, "altura_notificacao")
    ]
    posicao = 20
    for n in notificacoes_visiveis:
        posicao += n.altura_notificacao + 10
    container.bottom = posicao

    # Adiciona e atualiza
    page.overlay.append(container)
    page.update()

    def mostrar():
        time.sleep(0.1)
        container.opacity = 1
        container.offset = ft.Offset(0, 0)
        try:
            page.run_async(lambda: page.update())
        except:
            pass

    def esconder():
        time.sleep(4)
        container.opacity = 0
        container.offset = ft.Offset(0.5, 0)
        try:
            page.run_async(lambda: page.update())
        except:
            pass
        time.sleep(0.4)
        try:
            if container in page.overlay:
                page.overlay.remove(container)
                # Reposiciona as notificações restantes
                novas = [
                    c for c in page.overlay
                    if isinstance(c, ft.Container) and hasattr(c, "altura_notificacao")
                ]
                nova_pos = 20
                for n in novas:
                    n.bottom = nova_pos
                    n.animate_position = ft.Animation(400, "easeOut")
                    nova_pos += n.altura_notificacao + 10
                page.run_async(lambda: page.update())
        except:
            pass

    threading.Thread(target=mostrar, daemon=True).start()
    threading.Thread(target=esconder, daemon=True).start()
