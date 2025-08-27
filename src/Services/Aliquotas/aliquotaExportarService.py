import pandas as pd

class AliquotaExportarService:
    @staticmethod
    def gerarModelo(dados: list, termo_busca: str = "") -> pd.DataFrame:
        def filtrar(x):
            if not termo_busca:
                return True
            termo = termo_busca.lower()
            return termo in (x.get("produto") or "").lower() or termo in (x.get("codigo") or "")

        base = [x for x in dados if filtrar(x)]

        df = pd.DataFrame(
            [
                {
                    "codigo": x.get("codigo", ""),
                    "produto": x.get("produto", ""),
                    "ncm": x.get("ncm", ""),
                    "aliquota": "",
                }
                for x in base
            ],
            columns=["codigo", "produto", "ncm", "aliquota"]
        )

        return df
