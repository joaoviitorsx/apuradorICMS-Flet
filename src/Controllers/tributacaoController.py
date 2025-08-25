from pathlib import Path
from src.Config.Database.db import SessionLocal
from src.Services.Planilhas.planilhaService import PlanilhaTributacaoRepository, PlanilhaTributacaoService, contarFaltantes
from src.Services.Sped.Pos.Etapas.tributacaoService import TributacaoService
from src.Models.tributacaoModel import CadastroTributacao

class TributacaoController:
    @staticmethod
    def importarPlanilhaTributacao(path_planilha: str, empresa_id: int) -> dict:
        p = Path(path_planilha)
        if p.suffix.lower() != ".xlsx":
            print(f"[ERRO] Extensão inválida: {p.suffix}")
            return {"status": "erro", "mensagem": "O arquivo deve ser um .xlsx"}
        if not p.is_file():
            print(f"[ERRO] Arquivo não encontrado: {path_planilha}")
            return {"status": "erro", "mensagem": "Arquivo não encontrado"}

        try:
            with SessionLocal() as db:
                print(f"[DEBUG] Tentando ler planilha: {path_planilha}")
                repo = PlanilhaTributacaoRepository(db)
                service = PlanilhaTributacaoService(repo)
                resultado = service.importarPlanilha(str(p), empresa_id)
                print(f"[DEBUG] Resultado da importação: {resultado}")
                faltantesRestantes = contarFaltantes(db, empresa_id)
        except Exception as e:
            print(f"[ERRO] Falha inesperada ao importar planilha: {e}")
            return {"status": "erro", "mensagem": f"Falha inesperada: {e}"}

        if isinstance(resultado, dict):
            resultado.setdefault("faltantes_restantes", faltantesRestantes)
        else:
            resultado = {"status": "ok", "resultado": resultado, "faltantes_restantes": faltantesRestantes}

        return resultado

    @staticmethod
    def listarFaltantes(empresa_id: int, limit: int = 300) -> list:
        with SessionLocal() as db:
            svc = TributacaoService(db)
            return svc.listar_faltantes(empresa_id, limit=limit)

    @staticmethod
    def salvarAliquotasEditadas(empresa_id: int, edits: list) -> dict:
        atualizados = 0
        grupos_processados = set()
        try:
            with SessionLocal() as db:
                for edit in edits:
                    item_id = edit.get("id")
                    aliquota = edit.get("aliquota")
                    categoria_fiscal = edit.get("categoriaFiscal")

                    row = db.query(CadastroTributacao).filter_by(
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

                    resultado = db.query(CadastroTributacao).filter_by(
                        empresa_id=empresa_id, produto=produto_ref, ncm=ncm_ref
                    ).update({
                        "aliquota": aliquota,
                        "categoriaFiscal": categoria_fiscal
                    })
                    if resultado:
                        atualizados += resultado
                db.commit()

            # Conta quantos itens ainda estão sem alíquota
            with SessionLocal() as db:
                svc = TributacaoService(db)
                restantes = svc.contar_faltantes(empresa_id)

            return {"atualizados": atualizados, "faltantes_restantes": restantes}
        except Exception as e:
            return {"atualizados": 0, "faltantes_restantes": -1, "erro": str(e)}