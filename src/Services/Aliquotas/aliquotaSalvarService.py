import pandas as pd
from sqlalchemy import text
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.aliquota import tratarAliquotaPoupAliquota, categoriaAliquota
from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService

class AliquotaSalvarService:

    @staticmethod
    def validarAliquotas(dados: list, valores: dict):
        edits = []
        vazios = []
        invalidos = []

        for item in dados:
            _id = int(item["id"])
            valor_bruto = (valores.get(_id) or "").strip()

            if not valor_bruto:
                vazios.append(item.get("produto", f"ID {_id}"))
                continue

            valor_formatado = tratarAliquotaPoupAliquota(valor_bruto)
            if valor_formatado is None:
                invalidos.append(item.get("produto", f"ID {_id}"))
                continue

            edits.append({
                "id": _id,
                "aliquota": valor_formatado,
                "categoriaFiscal": categoriaAliquota(valor_formatado),
            })

        return edits, vazios, invalidos

    @staticmethod
    def salvarDados(db, empresa_id: int, edits: list, batch_size: int = 5000) -> int:
        if not edits:
            return 0

        engine = db.get_bind()
        atualizados = 0

        edits_df = pd.DataFrame(edits)
        if edits_df.empty:
            return 0

        query = """
            SELECT id, produto, ncm
            FROM cadastro_tributacao
            WHERE empresa_id = :empresa_id
        """
        db_df = pd.read_sql(text(query), engine, params={"empresa_id": empresa_id})
        merged = pd.merge(edits_df, db_df, on="id", how="inner")

        if merged.empty:
            return 0

        update_data = merged[["id", "aliquota", "categoriaFiscal"]].to_dict(orient="records")

        for i in range(0, len(update_data), batch_size):
            batch = update_data[i:i + batch_size]
            db.bulk_update_mappings(CadastroTributacao, batch)
            db.commit()
            atualizados += len(batch)

        return atualizados

    @staticmethod
    def contarFaltantes(db, empresa_id: int) -> int:
        return (
            db.query(CadastroTributacao)
            .filter(
                CadastroTributacao.empresa_id == empresa_id,
                (CadastroTributacao.aliquota == None) | (CadastroTributacao.aliquota == "")
            )
            .count()
        )

    @staticmethod
    def listarFaltantes(db, empresa_id: int):
        resultados = (
            db.query(CadastroTributacao)
            .filter(
                CadastroTributacao.empresa_id == empresa_id,
                (CadastroTributacao.aliquota == None) | (CadastroTributacao.aliquota == "")
            )
            .all()
        )

        return [
            {
                "id": r.id,
                "codigo": r.codigo,
                "produto": r.produto,
                "ncm": r.ncm,
                "aliquota": r.aliquota
            }
            for r in resultados
        ]

    @staticmethod
    def executar(db, empresa_id: int, dados: list, valores: dict):
        edits, vazios, invalidos = AliquotaSalvarService.validarAliquotas(dados, valores)

        if vazios or invalidos or not edits:
            return {
                "status": "erro",
                "vazios": vazios,
                "invalidos": invalidos,
                "edits": edits
            }

        atualizados = AliquotaSalvarService.salvarDados(db, empresa_id, edits)
        faltantes = AliquotaSalvarService.contarFaltantes(db, empresa_id)

        return {
            "status": "ok",
            "atualizados": atualizados,
            "faltantes_restantes": faltantes,
            "edits": edits
        }