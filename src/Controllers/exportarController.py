from src.Config.Database.db import SessionLocal
from src.Services.Exportar.exportarPlanilhaService import ExportarPlanilhaService
from src.Services.Exportar.exportarProdutosService import ExportarProdutosService
from src.Services.Produto.produtoService import ProdutosService

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
        
    @staticmethod
    async def exportarProdutos(empresa_id: int, caminho: str) -> dict:
        try:
            print(f"[DEBUG] Exportar produtos: empresa_id={empresa_id}, caminho={caminho}")
            with SessionLocal() as session:
                service = ExportarProdutosService(session)
                resultado = service.exportarProdutos(empresa_id, caminho)
                return resultado
        except Exception as e:
            print(f"[DEBUG] Erro inesperado ao exportar produtos: {e}")
            return {"status": "erro", "mensagem": f"Erro ao exportar produtos: {str(e)}"}
        
    @staticmethod
    async def buscarProdutos(empresa_id: int, pagina: int = 1, limite: int = 200, filtro_nome: str = "", categoria_fiscal: str = "") -> dict:
        try:
            print(f"[DEBUG] Buscar produtos: empresa_id={empresa_id}, pagina={pagina}, limite={limite}")
            
            with SessionLocal() as session:
                service = ProdutosService(session)
                return service.buscarProdutos(empresa_id, pagina, limite, filtro_nome, categoria_fiscal)
                
        except Exception as e:
            print(f"[DEBUG] Erro inesperado ao buscar produtos: {e}")
            return {"status": "erro", "mensagem": f"Erro ao buscar produtos: {str(e)}"}
    
    @staticmethod
    def buscarCategoriasFiscais(empresa_id: int) -> list:
        try:
            with SessionLocal() as session:
                service = ProdutosService(session)
                return service.buscarCategoriasFiscais(empresa_id)
        except Exception as e:
            print(f"[DEBUG] Erro ao buscar categorias: {e}")
            return []
    
    @staticmethod
    def contarProdutos(empresa_id: int) -> int:
        try:
            with SessionLocal() as session:
                service = ProdutosService(session)
                return service.contarProdutos(empresa_id)
        except Exception as e:
            print(f"[DEBUG] Erro ao contar produtos: {e}")
            return 0