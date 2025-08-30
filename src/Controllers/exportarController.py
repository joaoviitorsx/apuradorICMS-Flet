from src.Config.Database.db import SessionLocal
from src.Services.Exportar.exportarPlanilhaService import ExportarPlanilhaService

class ExportarController:
    
    @staticmethod
    async def exportarPlanilha(page, empresa_id: int, periodo: str, caminho: str) -> dict:
        try:
            print(f"[DEBUG] Exportar planilha: empresa_id={empresa_id}, periodo={periodo}, caminho={caminho}")
            with SessionLocal() as session:
                service = ExportarPlanilhaService(session)
                resultado = service.exportarC170Clone(empresa_id, periodo, caminho)
                resultado["caminho_arquivo"] = caminho
                return resultado
        except Exception as e:
            print(f"[DEBUG] Erro inesperado: {e}")
            return {"status": "erro", "mensagem": f"Erro ao exportar planilha: {str(e)}"}