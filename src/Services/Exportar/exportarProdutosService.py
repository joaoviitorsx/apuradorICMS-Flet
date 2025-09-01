from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session
from src.Models.tributacaoModel import CadastroTributacao

COLUNAS_PRODUTOS = [
    'empresa_id', 'codigo', 'produto', 'ncm', 'aliquota', 'categoriaFiscal'
]

class ExportarProdutosRepository:
    def __init__(self, session: Session):
        self.session = session

    def buscarProdutos(self, empresa_id: int):
        query = (
            self.session.query(CadastroTributacao)
            .filter(CadastroTributacao.empresa_id == empresa_id)
            .order_by(CadastroTributacao.codigo)
        )
        return query

class ExportarProdutosService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = ExportarProdutosRepository(session)

    def exportarProdutos(self, empresa_id: int, caminho_saida: str) -> dict:
        print(f"[DEBUG] exportarProdutos chamado: empresa_id={empresa_id}, caminho_saida={caminho_saida}")
        try:
            query = self.repository.buscarProdutos(empresa_id)
            total = query.count()
            print(f"[DEBUG] Total de produtos encontrados: {total}")
            
            if total == 0:
                return {"status": "vazio", "mensagem": "Nenhum produto encontrado para exportação."}

            wb = Workbook()
            ws = wb.active
            ws.title = "Produtos"

            cabecalho = ['Empresa ID', 'Código', 'Produto', 'NCM', 'Alíquota', 'Categoria Fiscal']
            ws.append(cabecalho)

            linhas_exportadas = 0
            for produto in query.yield_per(1000):
                linha = [
                    produto.id,
                    produto.empresa_id,
                    produto.codigo or "",
                    produto.produto or "",
                    produto.ncm or "",
                    produto.aliquota or "",
                    produto.categoriaFiscal or ""
                ]
                ws.append(linha)
                linhas_exportadas += 1
                
                if linhas_exportadas % 1000 == 0:
                    print(f"[DEBUG] {linhas_exportadas} produtos exportados...")

            print(f"[DEBUG] Total de produtos exportados: {linhas_exportadas}")

            for i, col in enumerate(cabecalho, start=1):
                ws.column_dimensions[get_column_letter(i)].width = max(15, len(col) + 2)

            wb.save(caminho_saida)
            print(f"[DEBUG] Planilha de produtos salva em: {caminho_saida}")
            
            return {
                "status": "ok", 
                "mensagem": f"Planilha de produtos exportada com sucesso! {linhas_exportadas} produtos exportados.",
                "total_produtos": linhas_exportadas,
                "caminho_arquivo": caminho_saida
            }

        except Exception as e:
            print(f"[DEBUG] Erro ao exportar produtos: {e}")
            return {"status": "erro", "mensagem": f"Erro ao exportar produtos: {str(e)}"}
