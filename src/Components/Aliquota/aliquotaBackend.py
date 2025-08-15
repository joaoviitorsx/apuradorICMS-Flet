from src.Controllers.tributacaoController import TributacaoController

def preparar_itens_backend(empresa_id: int, limit: int = 300):
    """
    Consulta itens com alíquotas pendentes no backend.
    """
    return TributacaoController.preparar_listagem_para_ui(empresa_id, limit)

def listar_faltantes_backend(empresa_id: int, limit: int = 300):
    """
    Lista novamente os itens faltantes após salvar ou importar.
    """
    return TributacaoController.listar_faltantes(empresa_id, limit)

def salvar_aliquotas_backend(empresa_id: int, edits: list):
    """
    Persiste as alíquotas preenchidas no backend.
    """
    return TributacaoController.salvar_aliquotas(empresa_id, edits)

def importar_planilha_backend(caminho: str, empresa_id: int):
    """
    Faz o cadastro das alíquotas via planilha no backend.
    """
    return TributacaoController.cadastrar_tributacao_por_planilha(caminho, empresa_id)
