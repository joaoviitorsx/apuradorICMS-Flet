import asyncio

from .Etapas.fornecedorService import FornecedorService, FornecedorRepository
from .Etapas.c170NovaService import C170NovaService, C170NovaRepository
from .Etapas.tributacaoService import TributacaoService, TributacaoRepository
from .Etapas.aliquotaService import AliquotaService
from .Etapas.cloneService import ClonagemService

from .Etapas.Calculo.atualizarAliquotaService import AtualizarAliquotaRepository, AtualizarAliquotaService
from .Etapas.Calculo.aliquotaSimplesService import AliquotaSimplesService, AliquotaSimplesRepository
from .Etapas.Calculo.calculoResultadoService import CalculoResultadoService, CalculoResultadoRepository

from src.Utils.periodo import obterPeriodo


class PosProcessamentoService:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id

    async def executarPre(self):
        print(f"[POS] Iniciando pré-processamento de alíquotas para empresa_id={self.empresa_id}...")

        etapas = [
            self.etapaFornecedor,
            self.etapaC170Nova,
            self.etapaTributacao,
            self.etapaAliquotas,
        ]

        for idx, etapa in enumerate(etapas, start=1):
            resultado = await etapa()
            if resultado == "parar":
                return {"status": "pendente_aliquota", "etapa_pos": idx}

        return {"status": "ok"}

    async def executarPos(self):
        print(f"[POS] Iniciando pós-processamento após preenchimento de alíquotas para empresa_id={self.empresa_id}...")

        etapas = [
            self.etapaClonagem,
            self.etapaAtualizarAliquotas,
            self.etapaAliquotaSimples,
            self.etapaCalculoResultado,
        ]

        for idx, etapa in enumerate(etapas, start=5):
            await etapa()

        print("[POS] Pós-processamento finalizado.")
        return {"status": "ok"}

    async def etapaFornecedor(self):
        repo = FornecedorRepository(self.session)
        fornecedorService = FornecedorService(repo)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, fornecedorService.processar, self.empresa_id)
        print("[POS] Fornecedores atualizados.")
        return None

    async def etapaC170Nova(self):
        repo = C170NovaRepository(self.session)
        service = C170NovaService(repo)
        service.preencher(self.empresa_id)
        print("[POS] Tabela c170nova criada e preenchida.")
        return None

    async def etapaTributacao(self):
        repo = TributacaoRepository(self.session)
        service = TributacaoService(repo)
        service.preencher(self.empresa_id)
        print("[POS] Cadastro de tributação preenchido com base na tabela 0200.")
        return None

    async def etapaAliquotas(self):
        aliquotaService = AliquotaService(lambda: self.session)
        if aliquotaService.verificarPopupAliquota(self.empresa_id):
            print("[POS] Existem alíquotas nulas, popup deve ser exibido.")
            return "parar"
        print("[POS] Nenhuma alíquota nula encontrada.")
        return None

    async def etapaClonagem(self):
        clonagemService = ClonagemService(lambda: self.session)
        clonagemService.clonarC170Nova(self.empresa_id)
        print("[POS] Tabela c170_clone criada com sucesso.")
        return None

    async def etapaAtualizarAliquotas(self):
        repo = AtualizarAliquotaRepository(self.session)
        service = AtualizarAliquotaService(repo)
        service.atualizar(self.empresa_id)
        print("[POS] Alíquotas atualizadas com sucesso.")
        return None

    async def etapaAliquotaSimples(self):
        repo = AliquotaSimplesRepository(self.session)
        service = AliquotaSimplesService(repo)
        print("[POS] Obtendo período atual...")
        periodo = obterPeriodo(self.session, self.empresa_id)
        print(f"[POS] Período obtido: {periodo}. Atualizando alíquotas Simples Nacional...")
        service.atualizar(self.empresa_id, periodo)
        print("[POS] Alíquotas Simples Nacional atualizadas com sucesso.")
        return None

    async def etapaCalculoResultado(self):
        repo = CalculoResultadoRepository(self.session)
        service = CalculoResultadoService(repo)
        service.calcular(self.empresa_id)
        print("[POS] Cálculo de resultados finalizado.")
        return None
