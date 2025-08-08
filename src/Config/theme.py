import flet as ft

_LIGHT_THEME = {
    "MODE": "light",
    "PRIMARY_COLOR": "#2563EB",         # Azul institucional (botões principais)
    "PRIMARY_HOVER": "#1D4ED8",         # Hover do botão
    "BACKGROUND": "#FFFFFF",            # Fundo padrão de tela / containers
    "BACKGROUNDSCREEN": "#F5F7FA",      # Fundo da janela inteira (cinza muito claro)
    "CARD": "#F9FAFB",                  # Fundo de cards
    "CARD_DARK": "#2D2D2D",             # Reservado para futuro modo escuro
    "BORDER": "#D1D5DB",                # Borda suave (inputs, cards)
    "ON_PRIMARY": "#FFFFFF",            # Texto sobre botões
    "TEXT": "#1F2937",                  # Texto principal
    "TEXT_SECONDARY": "#6B7280",        # Texto secundário
    "ERROR": "#DC2626",                 # Cor de erro
    "BLACK": "#000000",
    "INPUT_BG": "#FFFFFF",              # Fundo dos inputs
    "FOLDER_ICON": "#F5CC18",          # Cor do ícone de pasta
    "ASSETS_ICON": "#4073E0",          # Cor do ícone de assets
}

STYLE = {
    "CARD_RADIUS": 12,
    "CARD_ELEVATION": 8,
    "BORDER_RADIUS_INPUT": 8,
    "FONT_FAMILY": "Segoe UI"
}

__current_theme = _LIGHT_THEME

def get_theme() -> dict:
    return __current_theme

def apply_theme(page: ft.Page):
    th = get_theme()
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = th["BACKGROUNDSCREEN"]
    page.window_bgcolor = th["BACKGROUNDSCREEN"]
    page.fonts = {"default": STYLE["FONT_FAMILY"]}
    return th
