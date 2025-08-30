import flet as ft
from src.Components.PoupAliquota.aliquotaDialog import abrirDialogoAliquotas

def mostrarTelaPoupAliquota(page, empresa_id, itens, etapa_pos):
    abrirDialogoAliquotas(
        page=page,
        empresa_id=empresa_id,
        itens=itens,
        etapa_pos=etapa_pos,
        retornar_pos=True
    )