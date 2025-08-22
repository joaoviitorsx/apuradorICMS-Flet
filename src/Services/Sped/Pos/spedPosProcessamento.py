from .Etapas.fornecedorService import FornecedorService
from .Etapas.c170NovaService import C170NovaService
from .Etapas.tributacaoService import TributacaoService

class PosProcessamentoService:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id

    def executar(self):
        print(f"[POS] Iniciando pós-processamento para empresa_id={self.empresa_id}...")

        # 1 - Fornecedores
        FornecedorService(self.session, self.empresa_id)
        print("[POS] Fornecedores atualizados.")

        # 2 - Criar C170 nova
        C170NovaService(self.session, self.empresa_id)
        print("[POS] Tabela c170nova criada e preenchida.")

        # 3 - Tributação
        TributacaoService(self.session, self.empresa_id)
        print("[POS] Cadastro de tributação preenchido com base na tabela 0200.")

        verificar_popup_aliquota(self.session, self.empresa_id)
        print("[POS] Popup de alíquotas verificado.")

        # 4 - Clonagem
        clonar_c170nova(self.session, self.empresa_id)
        print("[POS] Tabela c170_clone criada com sucesso.")

