import flet as ft
from src.Components.PoupAliquota.aliquotaDialog import abrirDialogoAliquotas

def mostrarTelaPoupAliquota(page: ft.Page, empresa_id: int):
    abrirDialogoAliquotas(page, empresa_id)

