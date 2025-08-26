from src.Services.Empresa.empresaService import listarEmpresas
from src.Components.notificao import notificacao
import flet as ft

def obter_dropdown_options(page: ft.Page) -> list:
    try:
        empresas = listarEmpresas()
        return [ft.dropdown.Option(key=str(emp["id"]), text=emp["razao_social"]) for emp in empresas]
    except Exception as erro:
        notificacao(page, "Erro ao buscar empresas", str(erro), tipo="erro")
        return []