from pathlib import Path
from src.Config.Database.db import SessionLocal
from src.Services.Planilhas.planilhaService import PlanilhaTributacaoRepository, PlanilhaTributacaoService, contarFaltantes
from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService

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
    def listarFaltantes(empresa_id: int, limit: int = 300):
        with SessionLocal() as db:
            service = AliquotaPoupService(db)
            return service.listarFaltantes(empresa_id, limit)

    @staticmethod
    def salvarAliquotasEditadas(empresa_id: int, edits: list):
        try:
            with SessionLocal() as db:
                service = AliquotaPoupService(db)
                atualizados = service.salvarAliquotasPoup(empresa_id, edits)
                restantes = service.contarFaltantesPoup(empresa_id)
            return {"atualizados": atualizados, "faltantes_restantes": restantes}
        except Exception as e:
            return {"atualizados": 0, "faltantes_restantes": -1, "erro": str(e)}