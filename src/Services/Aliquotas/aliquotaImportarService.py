import unicodedata
import pandas as pd
from src.Utils.aliquota import validado

from multiprocessing import Process
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

class AliquotaImportarService:
    @staticmethod
    def importarPlanilha(df: pd.DataFrame, dados: list, valores: dict) -> dict:
        importadas = 0
        erros = []

        def norm(s: str) -> str:
            s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode()
            return s.strip().lower()

        cols = {norm(c): c for c in df.columns}
        col_codigo = cols.get("codigo")
        col_produto = cols.get("produto")
        col_ncm = cols.get("ncm")
        col_aliq = cols.get("aliquota") or cols.get("aliq") or cols.get("aliq_icms")

        if not col_codigo or not col_produto or not col_ncm or not col_aliq:
            return {
                "status": "erro",
                "mensagem": "A planilha deve conter as colunas: 'codigo', 'produto', 'ncm' e 'aliquota'.",
                "importadas": 0,
                "erros": []
            }

        for idx, row in df.iterrows():
            cod = str(row.get(col_codigo)).strip()
            prod = str(row.get(col_produto)).strip()
            ncm = str(row.get(col_ncm)).strip()
            aliq = str(row.get(col_aliq)).strip()

            if not cod or not prod or not ncm or not aliq:
                continue

            if not validado(aliq):
                erros.append(f"Linha {idx + 2}: alíquota inválida '{aliq}'")
                continue

            encontrado = False
            for d in dados:
                if (
                    str(d.get("codigo")).strip() == cod and
                    str(d.get("produto")).strip() == prod and
                    str(d.get("ncm")).strip() == ncm
                ):
                    valores[int(d["id"])] = aliq
                    importadas += 1
                    encontrado = True
                    break

            if not encontrado:
                erros.append(f"Linha {idx + 2}: código/produto/NCM não encontrado na listagem atual")

        return {
            "status": "ok",
            "importadas": importadas,
            "erros": erros
        }
    
    @staticmethod
    def abrirArquivo(caminho):
        root = tk.Tk()
        root.withdraw()

        resposta = messagebox.askyesno(
            title="Abrir planilha?",
            message="A planilha foi gerada com sucesso.\nDeseja abri-la agora?"
        )

        if not resposta:
            return

        if sys.platform == "win32":
            os.startfile(caminho)

    @staticmethod
    def abrirPlanilha(caminho):
        AliquotaImportarService.abrirArquivo(caminho)