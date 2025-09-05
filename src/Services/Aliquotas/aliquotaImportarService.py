import unicodedata
import pandas as pd
from src.Utils.aliquota import validado

class AliquotaImportarService:
    @staticmethod
    def importarPlanilha(df: pd.DataFrame, dados: list, valores: dict) -> dict:
        def norm(s: str) -> str:
            s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode()
            return s.strip().lower()

        # Mapeamento de colunas
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

        # Normalização vetorizada
        df_import = pd.DataFrame({
            "codigo": df[col_codigo].astype(str).str.strip(),
            "produto": df[col_produto].astype(str).str.strip(),
            "ncm": df[col_ncm].astype(str).str.strip(),
            "aliquota": df[col_aliq].astype(str).str.strip()
        })

        # Remove linhas com campos obrigatórios vazios
        df_import = df_import.replace("", pd.NA).dropna(subset=["codigo", "produto", "ncm", "aliquota"])

        # Validação vetorizada de alíquota
        df_import["linha_excel"] = df_import.index + 2
        df_import["valida"] = df_import["aliquota"].apply(validado)

        erros = [
            f"Linha {row.linha_excel}: alíquota inválida '{row.aliquota}'"
            for _, row in df_import.loc[~df_import["valida"]].iterrows()
        ]

        df_validos = df_import[df_import["valida"]].copy()

        # Convertendo 'dados' (list[dict]) para DataFrame para usar merge
        df_base = pd.DataFrame(dados)
        df_base["codigo"] = df_base["codigo"].astype(str).str.strip()
        df_base["produto"] = df_base["produto"].astype(str).str.strip()
        df_base["ncm"] = df_base["ncm"].astype(str).str.strip()

        # Faz o merge para encontrar registros existentes
        df_merge = df_validos.merge(
            df_base,
            on=["codigo", "produto", "ncm"],
            how="left",
            suffixes=("", "_base")
        )

        nao_encontrados = df_merge[df_merge["id"].isnull()]
        encontrados = df_merge[df_merge["id"].notnull()]

        erros += [
            f"Linha {row.linha_excel}: código/produto/NCM não encontrado na listagem atual"
            for _, row in nao_encontrados.iterrows()
        ]

        importadas = 0
        for _, row in encontrados.iterrows():
            valores[int(row["id"])] = row["aliquota"]
            importadas += 1

        return {
            "status": "ok",
            "importadas": importadas,
            "erros": erros
        }

    @staticmethod
    def abrirArquivo(caminho):
        import os, sys
        import tkinter as tk
        from tkinter import messagebox

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
        elif sys.platform == "darwin":
            subprocess.call(["open", caminho])
        else:
            subprocess.call(["xdg-open", caminho])

    @staticmethod
    def abrirPlanilha(caminho):
        AliquotaImportarService.abrirArquivo(caminho)
