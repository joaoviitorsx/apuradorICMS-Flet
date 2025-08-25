import asyncio

from .Etapas.fornecedorService import FornecedorService, FornecedorRepository
from .Etapas.c170NovaService import C170NovaService, C170NovaRepository
from .Etapas.tributacaoService import TributacaoService, TributacaoRepository
from .Etapas.aliquotaService import AliquotaService
from .Etapas.cloneService import ClonagemService

class PosProcessamentoService:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id

    async def executar(self):
        print(f"[POS] Iniciando pós-processamento para empresa_id={self.empresa_id}...")

        # 1 - Fornecedores
        repo = FornecedorRepository(self.session)
        fornecedorService = FornecedorService(repo)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, fornecedorService.processar, self.empresa_id)
        print("[POS] Fornecedores atualizados.")

        # 2 - Criar C170 nova
        repo = C170NovaRepository(self.session)
        service = C170NovaService(repo)
        service.preencher(self.empresa_id)
        print("[POS] Tabela c170nova criada e preenchida.")

        # 3 - Tributação
        repo = TributacaoRepository(self.session)
        service = TributacaoService(repo)
        service.preencher(self.empresa_id)
        print("[POS] Cadastro de tributação preenchido com base na tabela 0200.")

        # # 4 - Alíquotas
        # AliquotaService(self.session, self.empresa_id)
        # print("[POS] Popup de alíquotas verificado.")

        # # 4 - Clonagem
        # ClonagemService(self.session, self.empresa_id)
        # print("[POS] Tabela c170_clone criada com sucesso.")

