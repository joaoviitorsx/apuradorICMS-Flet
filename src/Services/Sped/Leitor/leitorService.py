from ..Salvar import registro0000Service, registro0150Service, registro0200Service, registroC100Service, registroC170Service

class LeitorService:
    def __init__(self, empresa_id, session):
        self.empresa_id = empresa_id
        self.session = session
        self.filial = None
        self.dt_ini_0000 = None

        self.servicos = {
            "0000": registro0000Service.Registro0000Service(session, empresa_id),
            "0150": registro0150Service.Registro0150Service(session, empresa_id),
            "0200": registro0200Service.Registro0200Service(session, empresa_id),
            "C100": registroC100Service.RegistroC100Service(session, empresa_id),
            "C170": registroC170Service.RegistroC170Service(session, empresa_id),
        }

    def executar(self, caminho_arquivo: str, tamanho_lote: int = 5000):
        buffer = []

        for encoding in ["latin1"]:
            try:
                with open(caminho_arquivo, 'r', encoding=encoding) as arquivo:
                    for linha in arquivo:
                        buffer.append(linha.strip())

                        if len(buffer) >= tamanho_lote:
                            self.processar(buffer)
                            buffer.clear()

                    if buffer:
                        self.processar(buffer)

                self.salvar()
                print(f"[DEBUG] Arquivo processado com sucesso com encoding {encoding}")
                return

            except UnicodeDecodeError as e:
                print(f"[DEBUG] Falha ao tentar encoding {encoding}: {e}")
                continue

        raise ValueError("Não foi possível ler o arquivo SPED com nenhuma codificação compatível.")

    def processar(self, linhas: list[str]):
        for linha in linhas:
            self.processarLinhas(linha)

    def processarLinhas(self, linha: str):
        if not linha.strip():
            return

        partes = linha.split("|")[1:-1]
        if not partes:
            return

        tipo_registro = partes[0]

        if tipo_registro == "0000":
            self.dt_ini_0000 = partes[3]
            cnpj = partes[6] if len(partes) > 6 else ''
            self.filial = cnpj[8:12] if cnpj else "0000"

        if tipo_registro in self.servicos:
            self.servicos[tipo_registro].set_context(
                dt_ini=self.dt_ini_0000,
                filial=self.filial
            )
            self.servicos[tipo_registro].processar(partes)

    def salvar(self):
        for servico in self.servicos.values():
            servico.salvar()