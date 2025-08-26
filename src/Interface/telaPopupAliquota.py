import flet as ft
from src.Components.Aliquota.aliquotaDialog import abrirDialogoAliquotas

def mostrarTelaPoupAliquota(page: ft.Page, empresa_id: int):
    abrirDialogoAliquotas(page, empresa_id)
