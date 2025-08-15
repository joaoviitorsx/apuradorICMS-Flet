import flet as ft
from src.Components.Aliquota.aliquotaDialog import abrir_dialogo_aliquotas

def mostrar_tela_popup_aliquota(page: ft.Page, empresa_id: int):
    abrir_dialogo_aliquotas(page, empresa_id)
