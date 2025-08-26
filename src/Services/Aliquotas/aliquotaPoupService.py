from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.aliquota import validado, tratarAliquota, categoriaAliquota

class AliquotaPoupService:
    def __init__(self, db_session):
        self.db = db_session

    def listarFaltantes(self, empresa_id: int, limit: int = 300):
        resultados = (
            self.db.query(CadastroTributacao)
            .filter(
                CadastroTributacao.empresa_id == empresa_id,
                (CadastroTributacao.aliquota == None) | (CadastroTributacao.aliquota == "")
            )
            .limit(limit).all() 
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

    def salvarAliquotasPoup(self, empresa_id: int, edits: list):
        atualizados = 0
        grupos_processados = set()
        for edit in edits:
            item_id = edit.get("id")
            aliquota_raw = edit.get("aliquota")
            aliquota = tratarAliquota(aliquota_raw)
            if not validado(aliquota):
                continue
            categoria_fiscal = categoriaAliquota(aliquota)

            row = self.db.query(CadastroTributacao).filter_by(
                id=item_id, empresa_id=empresa_id
            ).first()
            if not row:
                continue

            produto_ref = (row.produto or "").strip()
            ncm_ref = (row.ncm or "").strip()
            grupo_key = (produto_ref, ncm_ref)
            if grupo_key in grupos_processados:
                continue
            grupos_processados.add(grupo_key)

            resultado = self.db.query(CadastroTributacao).filter_by(
                empresa_id=empresa_id, produto=produto_ref, ncm=ncm_ref
            ).update({
                "aliquota": aliquota,
                "categoriaFiscal": categoria_fiscal
            })
            if resultado:
                atualizados += resultado
        self.db.commit()
        return atualizados

    def contarFaltantesPoup(self, empresa_id: int):
        return (
            self.db.query(CadastroTributacao)
            .filter(
                CadastroTributacao.empresa_id == empresa_id,
                (CadastroTributacao.aliquota == None) | (CadastroTributacao.aliquota == "")
            )
            .count()
        )