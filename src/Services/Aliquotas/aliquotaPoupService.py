from src.Services.Aliquotas.aliquotaSalvarService import AliquotaSalvarService
from src.Services.Aliquotas.aliquotaImportarService import AliquotaImportarService
from src.Services.Aliquotas.aliquotaExportarService import AliquotaExportarService

class AliquotaPoupService:
    def __init__(self, db_session):
        self.db = db_session

    # SALVAR
    def salvar(self, empresa_id: int, dados: list, valores: dict):
        edits, vazios, invalidos = AliquotaSalvarService.validarAliquotas(dados, valores)
        return AliquotaSalvarService.executar(self.db, empresa_id, dados, valores)

    async def pos_processar(self, empresa_id: int):
        return await AliquotaSalvarService.retornarProcessamento(self.db, empresa_id)

    # IMPORTAR
    def importar_planilha(self, df, dados: list, valores: dict):
        return AliquotaImportarService.importarPlanilha(df, dados, valores)

    # EXPORTAR
    def exportar_modelo(self, dados: list, termo_busca: str):
        return AliquotaExportarService.gerarModelo(dados, termo_busca)

    # FALTANTES
    def listarFaltantes(self, empresa_id: int, limit: int = 300):
        return AliquotaSalvarService.listarFaltantes(self.db, empresa_id, limit)

    def contarFaltantes(self, empresa_id: int):
        return AliquotaSalvarService.contarFaltantes(self.db, empresa_id)
