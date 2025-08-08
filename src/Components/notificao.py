import flet as ft
import threading
import time

def notificacao(page: ft.Page, titulo: str, mensagem: str, tipo: str = "info"):
    tipos = {
        "sucesso": {"bg": "#1fb355", "text": "white", "icon": "check_circle"},
        "erro": {"bg": "#db3e3e", "text": "white", "icon": "error"},
        "info": {"bg": "#3474dc", "text": "white", "icon": "info"},
        "alerta": {"bg": "#db8f0b", "text": "white", "icon": "warning"},
    }

    estilo = tipos.get(tipo, tipos["info"])

    if not hasattr(page, "overlay"):
        page.overlay = []

    def notificaoDinamica(titulo, mensagem):
        altura_base = 32  
        altura_icone = 26
        
        chars_por_linha_titulo = 45  
        linhas_titulo = max(1, len(titulo) // chars_por_linha_titulo + (1 if len(titulo) % chars_por_linha_titulo > 0 else 0))
        altura_titulo = linhas_titulo * 18  
        
        chars_por_linha_mensagem = 50  
        linhas_mensagem = max(1, len(mensagem) // chars_por_linha_mensagem + (1 if len(mensagem) % chars_por_linha_mensagem > 0 else 0))
        altura_mensagem = linhas_mensagem * 16  
        
        spacing_interno = 2 
        spacing_row = 12  
        
        altura_conteudo = altura_titulo + altura_mensagem + spacing_interno
        altura_final = max(altura_icone, altura_conteudo) + altura_base + 16  
        
        return max(80, min(altura_final, 200))

    altura_dinamica = notificaoDinamica(titulo, mensagem)

    notificacoes_existentes = []
    for item in page.overlay:
        if isinstance(item, ft.Container) and hasattr(item, 'content') and isinstance(item.content, ft.Card):
            notificacoes_existentes.append(item)

   
    posicao_acumulada = 20 + altura_dinamica + 10 
    for notif in notificacoes_existentes:
        notif.bottom = posicao_acumulada
        notif.animate_position = ft.Animation(400, "easeOut")
        altura_existente = getattr(notif, 'altura_notificacao', 80)
        posicao_acumulada += altura_existente + 10

    texto_titulo = ft.Text(
        titulo, 
        color=estilo["text"], 
        weight="bold", 
        size=15,
        max_lines=3,
        overflow=ft.TextOverflow.ELLIPSIS
    )
    
    texto_mensagem = ft.Text(
        mensagem, 
        color=estilo["text"], 
        size=13,
        max_lines=5,
        overflow=ft.TextOverflow.ELLIPSIS
    )

    card = ft.Container(
        content=ft.Card(
            elevation=6,
            content=ft.Container(
                padding=16,
                bgcolor=estilo["bg"],
                border_radius=12,
                content=ft.Row(
                    controls=[
                        ft.Icon(estilo["icon"], color=estilo["text"], size=26),
                        ft.Column([
                            texto_titulo,
                            texto_mensagem
                        ], spacing=2, expand=True)
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            )
        ),
        width=420,
        height=altura_dinamica,
        right=20,
        bottom=20,
        opacity=0,
        animate_opacity=ft.Animation(400, "easeOut"),
        animate_offset=ft.Animation(400, "easeOut"),
        animate_position=ft.Animation(400, "easeOut"),
        offset=ft.Offset(0.5, 0)
    )
    
    card.altura_notificacao = altura_dinamica

    page.overlay.append(card)
    page.update()

    def animar_entrada():
        time.sleep(0.1)
        card.opacity = 1
        card.offset = ft.Offset(0, 0)
        page.update()

    def animar_saida():
        time.sleep(4)
        card.opacity = 0
        card.offset = ft.Offset(0.5, 0) 
        page.update()
        time.sleep(0.5)
        try:
            if card in page.overlay:
                page.overlay.remove(card)
                
                notificacoes_restantes = []
                for item in page.overlay:
                    if isinstance(item, ft.Container) and hasattr(item, 'content') and isinstance(item.content, ft.Card):
                        notificacoes_restantes.append(item)
                
                posicao_atual = 20
                for notif in notificacoes_restantes:
                    notif.bottom = posicao_atual
                    altura_notif = getattr(notif, 'altura_notificacao', 80)
                    posicao_atual += altura_notif + 10
                    
                page.update()
        except:
            pass

    threading.Thread(target=animar_entrada).start()
    threading.Thread(target=animar_saida).start()