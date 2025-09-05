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
from src.Config.Database.db import SessionLocal  

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
        """Verificar se existem alíquotas pendentes"""
        print("[POS] 🔍 Verificando alíquotas pendentes...")
        
        try:
            # Verificação principal
            aliquotaService = AliquotaService(lambda: self.session)
            dadosPendentes = aliquotaService.verificarPopupAliquota(self.empresa_id)
            
            print(f"[POS] 📊 verificarPopupAliquota() retornou: {dadosPendentes}")
            
            if dadosPendentes:
                # ✅ Verificar se realmente há dados para listar
                from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService
                aliquota_poup = AliquotaPoupService(self.session)
                lista_faltantes = aliquota_poup.listarFaltantes(self.empresa_id)
                
                print(f"[POS] 📋 listarFaltantes() retornou: {len(lista_faltantes) if lista_faltantes else 0} itens")
                print(f"[POS] 🔍 Primeiros 3 itens: {lista_faltantes[:3] if lista_faltantes else 'Nenhum'}")
                
                # ✅ NOVA LÓGICA: Se não há dados para listar, continuar processamento
                if not lista_faltantes or len(lista_faltantes) == 0:
                    print("[POS] ⚠️ Inconsistência detectada: verificarPopupAliquota=True mas listarFaltantes=vazio")
                    print("[POS] ✅ Assumindo que não há alíquotas pendentes reais. Continuando processamento...")
                    return None
                
                print("[POS] ⚠️ Alíquotas pendentes encontradas. Intervenção do usuário necessária.")
                return "parar"
            
            print("[POS] ✅ Nenhuma alíquota pendente encontrada.")
            return None
            
        except Exception as e:
            print(f"[ERRO] ❌ Erro ao verificar alíquotas: {e}")
            import traceback
            traceback.print_exc()
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
        try:
            print("[POS] Iniciando cálculo de resultados ICMS...")
            
            repo = CalculoResultadoRepository(SessionLocal)
            service = CalculoResultadoService(repo, SessionLocal)

            resultado = await service.calcular(self.empresa_id, estrategia="lotes_paralelo")            
            print("[POS] ✅ Cálculo de resultados ICMS finalizado com sucesso.")
            return resultado
            
        except Exception as e:
            print(f"[ERRO] ❌ Falha no cálculo de resultados: {e}")
            import traceback
            traceback.print_exc()
            raise

