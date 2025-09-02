import flet as ft
import asyncio
import time
from typing import Dict, List, Optional, Union
from threading import Lock

class NotificationManager:
    def __init__(self):
        self.notifications: List[ft.Container] = []
        self.lock = Lock()
        self.notification_id = 0
    
    def get_next_id(self) -> int:
        self.notification_id += 1
        return self.notification_id

_notification_manager = NotificationManager()

def notificacao(page: ft.Page, titulo: str, mensagem: str, tipo: str = "info", duracao: int = 4):
    if not page:
        print("[ERRO] Page não fornecida para notificação")
        return
    
    tipos: Dict[str, Dict[str, Union[str, str]]] = {
        "sucesso": {"bg": "#1fb355", "text": "white", "icon": ft.Icons.CHECK_CIRCLE},
        "erro": {"bg": "#db3e3e", "text": "white", "icon": ft.Icons.ERROR},
        "info": {"bg": "#3474dc", "text": "white", "icon": ft.Icons.INFO},
        "alerta": {"bg": "#db8f0b", "text": "white", "icon": ft.Icons.WARNING},
    }
    
    estilo = tipos.get(tipo, tipos["info"])
    
    if not hasattr(page, 'overlay') or page.overlay is None:
        page.overlay = []
    
    try:
        async def wrapper():
            return await criarNotificacaoAsync(page, titulo, mensagem, estilo, duracao)
        
        page.run_task(wrapper)
    except Exception as e:
        print(f"[ERRO] Falha ao criar notificação: {e}")
        try:
            criarNotificacaoSync(page, titulo, mensagem, estilo, duracao)
        except Exception as e2:
            print(f"[ERRO] Fallback também falhou: {e2}")

async def criarNotificacaoAsync(page: ft.Page, titulo: str, mensagem: str, estilo: dict, duracao: int):
    try:
        with _notification_manager.lock:
            posicao_inicial = calcularProximaPosicao()
        
        notification = notificacaoContainer(page, titulo, mensagem, estilo, duracao, posicao_inicial)
        
        with _notification_manager.lock:
            _notification_manager.notifications.append(notification)
        
        page.overlay.append(notification)
        page.update()
        
        await asyncio.sleep(0.1)
        notification.opacity = 1
        notification.offset = ft.Offset(0, 0)
        page.update()
        
        await asyncio.sleep(duracao)
        await removerNotificacaoAsync(page, notification)
        
    except Exception as e:
        print(f"[ERRO] Erro na criação async da notificação: {e}")

def criarNotificacaoSync(page: ft.Page, titulo: str, mensagem: str, estilo: dict, duracao: int):
    try:
        with _notification_manager.lock:
            posicao_inicial = calcularProximaPosicao()
        
        notification = notificacaoContainer(page, titulo, mensagem, estilo, duracao, posicao_inicial)
        
        with _notification_manager.lock:
            _notification_manager.notifications.append(notification)
        
        page.overlay.append(notification)
        
        notification.opacity = 1
        notification.offset = ft.Offset(0, 0)
        page.update()
        
        def removerDepois():
            time.sleep(duracao)
            try:
                page.run_task(lambda: removerNotificacaoAsync(page, notification))
            except:
                removerNotificacaoSync(page, notification)
        
        import threading
        threading.Thread(target=removerDepois, daemon=True).start()
        
    except Exception as e:
        print(f"[ERRO] Erro na criação sync da notificação: {e}")

def calcularProximaPosicao() -> int:
    posicao = 20
    
    for notif in _notification_manager.notifications:
        if hasattr(notif, 'data') and notif.data:
            altura = notif.data.get("altura", 80)
            posicao += altura + 12
    
    return posicao

def notificacaoContainer(page: ft.Page, titulo: str, mensagem: str, estilo: dict, duracao: int, posicao_bottom: int = 20) -> ft.Container:
    altura_dinamica = calcularAltura(titulo, mensagem)
    notification_id = _notification_manager.get_next_id()
    
    def fecharNotificacao(e):
        try:
            async def fechar_async():
                await removerNotificacaoAsync(page, notification)
            page.run_task(fechar_async)
        except:
            removerNotificacaoSync(page, notification)
    
    btn_fechar = ft.IconButton(
        icon=ft.Icons.CLOSE,
        icon_size=16,
        icon_color=estilo["text"],
        tooltip="Fechar",
        on_click=fecharNotificacao
    )
    
    notification = ft.Container(
        content=ft.Card(
            elevation=8,
            shadow_color=ft.Colors.BLACK54,
            content=ft.Container(
                padding=ft.padding.all(16),
                bgcolor=estilo["bg"],
                border_radius=12,
                content=ft.Row(
                    controls=[
                        ft.Icon(estilo["icon"], color=estilo["text"], size=24),
                        ft.Column([
                            ft.Text(
                                titulo,
                                color=estilo["text"],
                                weight=ft.FontWeight.BOLD,
                                size=14,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(
                                mensagem,
                                color=estilo["text"],
                                size=12,
                                max_lines=3,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=4, expand=True),
                        btn_fechar
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            )
        ),
        width=400,
        height=altura_dinamica,
        right=20,
        bottom=posicao_bottom,
        opacity=0,
        offset=ft.Offset(0.3, 0),
        animate_opacity=ft.Animation(300, "easeOut"),
        animate_offset=ft.Animation(300, "easeOut"),
        animate_position=ft.Animation(300, "easeOut"),
        data={"id": notification_id, "altura": altura_dinamica} 
    )
    
    return notification

def calcularAltura(titulo: str, mensagem: str) -> int:
    altura_base = 60
    altura_por_linha = 20
    
    linhas_titulo = min(2, max(1, len(titulo) // 40 + (1 if len(titulo) % 40 > 0 else 0)))
    
    linhas_mensagem = min(3, max(1, len(mensagem) // 50 + (1 if len(mensagem) % 50 > 0 else 0)))
    
    altura_total = altura_base + (linhas_titulo + linhas_mensagem) * altura_por_linha
    return max(80, min(altura_total, 160))

def reposicionarNotificacao(page: ft.Page):
    try:
        notifications_validas = []
        for notif in _notification_manager.notifications:
            if hasattr(notif, 'data') and notif.data and notif in page.overlay:
                notifications_validas.append(notif)
        
        _notification_manager.notifications = notifications_validas
        
        posicao_atual = 20
        for notif in notifications_validas:
            notif.bottom = posicao_atual
            altura = notif.data.get("altura", 80) if notif.data else 80
            posicao_atual += altura + 12 
            
    except Exception as e:
        print(f"[ERRO] Erro ao reposicionar notificações: {e}")

async def removerNotificacaoAsync(page: ft.Page, notification: ft.Container):
    try:
        notification.opacity = 0
        notification.offset = ft.Offset(0.3, 0)
        page.update()
        
        await asyncio.sleep(0.3)
        
        with _notification_manager.lock:
            if notification in _notification_manager.notifications:
                _notification_manager.notifications.remove(notification)
            
            if notification in page.overlay:
                page.overlay.remove(notification)
            
            reposicionarNotificacao(page)
        
        page.update()
        
    except Exception as e:
        print(f"[ERRO] Erro ao remover notificação async: {e}")

def removerNotificacaoSync(page: ft.Page, notification: ft.Container):
    try:
        with _notification_manager.lock:
            if notification in _notification_manager.notifications:
                _notification_manager.notifications.remove(notification)
            
            if notification in page.overlay:
                page.overlay.remove(notification)
            
            reposicionarNotificacao(page)
        
        page.update()
        
    except Exception as e:
        print(f"[ERRO] Erro ao remover notificação sync: {e}")

def limparTodasNotificacoes(page: ft.Page):
    try:
        with _notification_manager.lock:
            for notification in _notification_manager.notifications.copy():
                if notification in page.overlay:
                    page.overlay.remove(notification)
            
            _notification_manager.notifications.clear()
        
        page.update()
        
    except Exception as e:
        print(f"[ERRO] Erro ao limpar notificações: {e}")