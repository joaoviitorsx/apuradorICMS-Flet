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
        atualizados = 0
        grupos_processados = set()

        def chunked(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        grouped_edits = {}
        for edit in edits:
            item_id = edit.get("id")
            aliquota = edit.get("aliquota")
            categoria = edit.get("categoriaFiscal")

            row = db.query(CadastroTributacao).filter_by(id=item_id, empresa_id=empresa_id).first()
            if not row:
                continue

            produto_ref = (row.produto or "").strip()
            ncm_ref = (row.ncm or "").strip()
            grupo_key = (produto_ref, ncm_ref)

            if grupo_key in grupos_processados:
                continue

            grupos_processados.add(grupo_key)
            grouped_edits[grupo_key] = {
                "aliquota": aliquota,
                "categoriaFiscal": categoria,
                "produto": produto_ref,
                "ncm": ncm_ref
            }

        grouped_list = list(grouped_edits.values())
        for batch in chunked(grouped_list, batch_size):
            for edit in batch:
                resultado = (
                    db.query(CadastroTributacao)
                    .filter_by(empresa_id=empresa_id, produto=edit["produto"], ncm=edit["ncm"])
                    .update({
                        "aliquota": edit["aliquota"],
                        "categoriaFiscal": edit["categoriaFiscal"]
                    })
                )
                if resultado:
                    atualizados += resultado
            db.commit()

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
