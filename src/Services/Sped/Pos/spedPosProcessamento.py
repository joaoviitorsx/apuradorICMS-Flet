import asyncio

from .Etapas.fornecedorService import FornecedorService, FornecedorRepository
from .Etapas.c170NovaService import C170NovaService, C170NovaRepository
from .Etapas.tributacaoService import TributacaoService, TributacaoRepository
from .Etapas.aliquotaService import AliquotaService
from .Etapas.cloneService import ClonagemService

from .Etapas.Calculo.atualizarAliquotaService import AtualizarAliquotaRepository, AtualizarAliquotaService
from .Etapas.Calculo.aliquotaSimplesService import AliquotaSimplesService, AliquotaSimplesRepository
from .Etapas.Calculo.calculoResultadoService import CalculoResultadoService, CalculoResultadoRepository


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

        # 4 - Alíquotas
        aliquotaService = AliquotaService(lambda: self.session)
        if aliquotaService.verificarPopupAliquota(self.empresa_id):
            print("[POS] Existem alíquotas nulas, popup deve ser exibido.")
        else:
            print("[POS] Nenhuma alíquota nula encontrada.")

        # 5 - Clonagem
        clonagemService = ClonagemService(lambda: self.session)
        clonagemService.clonarC170Nova(self.empresa_id)
        print("[POS] Tabela c170_clone criada com sucesso.")

        # 6 - Atualizar aliquotas
        repo = AtualizarAliquotaRepository(self.session)
        service = AtualizarAliquotaService(repo)
        service.atualizar(self.empresa_id)
        print("[POS] Alíquotas atualizadas com sucesso.")

        # 7 - Atualizar aliquota simples
        repo = AliquotaSimplesRepository(self.session)
        service = AliquotaSimplesService(repo)
        service.atualizar(self.empresa_id)
        print("[POS] Alíquotas Simples Nacional atualizadas com sucesso.")

        # 8 - Calculo Resultado
        repo = CalculoResultadoRepository(self.session)
        service = CalculoResultadoService(repo)
        service.calcular(self.empresa_id)
        print("[POS] Cálculo de resultados finalizado.")
