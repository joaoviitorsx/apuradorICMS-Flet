from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.aliquota import tratarAliquota

class ProdutosService:
    def __init__(self, session: Session):
        self.session = session
    
    def buscarProdutos(self, empresa_id: int, pagina: int = 1, limite: int = 200, filtro_nome: str = "", categoria_fiscal: str = "") -> dict:
        try:
            query = self.session.query(CadastroTributacao).filter(
                CadastroTributacao.empresa_id == empresa_id
            )
            
            if filtro_nome.strip():
                filtro_like = f"%{filtro_nome.strip().lower()}%"
                query = query.filter(
                    or_(
                        func.lower(CadastroTributacao.produto).like(filtro_like),
                        func.lower(CadastroTributacao.codigo).like(filtro_like),
                        func.lower(CadastroTributacao.ncm).like(filtro_like)
                    )
                )
            
            if categoria_fiscal.strip():
                query = query.filter(CadastroTributacao.categoriaFiscal == categoria_fiscal)
            
            total = query.count()
            
            offset = (pagina - 1) * limite
            produtos_db = query.offset(offset).limit(limite).all()
            
            produtos = []
            for produto in produtos_db:
                produtos.append({
                    "id": produto.id,
                    "codigo": produto.codigo or "",
                    "nome": produto.produto or "",
                    "ncm": produto.ncm or "",
                    "aliquota": tratarAliquota(produto.aliquota),  # Usar a função importada
                    "categoria_fiscal": produto.categoriaFiscal or ""
                })
            
            total_paginas = (total + limite - 1) // limite if total > 0 else 1
            
            return {
                "produtos": produtos,
                "total": total,
                "pagina": pagina,
                "total_paginas": total_paginas,
                "status": "sucesso"
            }
            
        except Exception as e:
            print(f"[ERRO] Erro ao buscar produtos: {e}")
            import traceback
            traceback.print_exc()  # Para ver o stack completo
            return {
                "produtos": [],
                "total": 0,
                "pagina": 1,
                "total_paginas": 0,
                "status": "erro",
                "mensagem": f"Erro ao buscar produtos: {str(e)}"
            }
    
    def buscarCategoriasFiscais(self, empresa_id: int) -> list:
        try:
            categorias = self.session.query(CadastroTributacao.categoriaFiscal)\
                .filter(CadastroTributacao.empresa_id == empresa_id)\
                .filter(CadastroTributacao.categoriaFiscal.isnot(None))\
                .filter(CadastroTributacao.categoriaFiscal != "")\
                .distinct()\
                .order_by(CadastroTributacao.categoriaFiscal)\
                .all()
            
            return [cat[0] for cat in categorias if cat[0]]
            
        except Exception as e:
            print(f"[ERRO] Erro ao buscar categorias: {e}")
            return []
    
    def contarProdutos(self, empresa_id: int) -> int:
        try:
            return self.session.query(CadastroTributacao)\
                .filter(CadastroTributacao.empresa_id == empresa_id)\
                .count()
        except Exception as e:
            print(f"[ERRO] Erro ao contar produtos: {e}")
            return 0