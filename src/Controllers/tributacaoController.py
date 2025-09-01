from pathlib import Path
from src.Config.Database.db import SessionLocal
from src.Services.Planilhas.planilhaService import PlanilhaTributacaoRepository, PlanilhaTributacaoService, contarFaltantes
from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService

class TributacaoController:
    @staticmethod
    def importarPlanilhaTributacao(path_planilha: str, empresa_id: int) -> dict:
        print(f"[DEBUG] Importando planilha: {path_planilha} para empresa {empresa_id}")
        
        p = Path(path_planilha)
        if p.suffix.lower() != ".xlsx":
            print(f"[ERRO] Extensão inválida: {p.suffix}")
            return {"status": "erro", "mensagem": "O arquivo deve ser um .xlsx"}
        
        if not p.is_file():
            print(f"[ERRO] Arquivo não encontrado: {path_planilha}")
            return {"status": "erro", "mensagem": "Arquivo não encontrado"}

        try:
            with SessionLocal() as db:
                print(f"[DEBUG] Processando planilha: {path_planilha}")
                repo = PlanilhaTributacaoRepository(db)
                service = PlanilhaTributacaoService(repo)
                
                resultado = service.importarPlanilha(str(p), empresa_id)
                print(f"[DEBUG] Resultado da importação: {resultado}")
                
                faltantes_restantes = contarFaltantes(db, empresa_id)
                print(f"[DEBUG] Faltantes restantes: {faltantes_restantes}")
                
        except Exception as e:
            print(f"[ERRO] Falha inesperada ao importar planilha: {e}")
            return {"status": "erro", "mensagem": f"Falha inesperada: {str(e)}"}

        if isinstance(resultado, dict):
            resultado.setdefault("faltantes_restantes", faltantes_restantes)
            if "status" not in resultado:
                resultado["status"] = "ok"
        else:
            resultado = {
                "status": "ok", 
                "resultado": resultado, 
                "faltantes_restantes": faltantes_restantes,
                "cadastrados": 0,
                "ja_existiam": 0,
                "erros": []
            }

        print(f"[DEBUG] Resultado final: {resultado}")
        return resultado

    @staticmethod
    def listarFaltantes(empresa_id: int):
        with SessionLocal() as db:
            service = AliquotaPoupService(db)
            return service.listarFaltantes(empresa_id)
