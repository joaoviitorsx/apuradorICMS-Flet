from ..Salvar import registro0000Service, registro0150Service, registro0200Service, registroC100Service, registroC170Service
    
class LeitorService:
    def __init__(self, empresa_id, session):
        self.empresa_id = empresa_id
        self.session = session
        self.filial = None
        self.dt_ini_0000 = None
        self.ultimo_num_doc = None

        self.servicos = {
            "0000": registro0000Service.Registro0000Service(session, empresa_id),
            "0150": registro0150Service.Registro0150Service(session, empresa_id),
            "0200": registro0200Service.Registro0200Service(session, empresa_id),
            "C100": registroC100Service.RegistroC100Service(session, empresa_id),
            "C170": registroC170Service.RegistroC170Service(session, empresa_id),
        }

    def executar(self, caminho_arquivo: str, tamanho_lote: int = 5000):
        linhas = self.leitor(caminho_arquivo)
        buffer = []

        for linha in linhas:
            buffer.append(linha.strip())
            if len(buffer) >= tamanho_lote:
                self.processarLote(buffer)
                buffer.clear()

        if buffer:
            self.processarLote(buffer)

        self.salvar()
        self.session.commit()
        print("[DEBUG] Processamento finalizado com sucesso.")

    def leitor(self, caminho_arquivo: str) -> list[str]:
        for encoding in ["latin1"]:
            try:
                with open(caminho_arquivo, 'r', encoding=encoding) as arquivo:
                    return arquivo.readlines()
            except UnicodeDecodeError as e:
                print(f"[DEBUG] Erro com encoding {encoding}: {e}")
                continue
        raise ValueError("Não foi possível ler o arquivo com os encodings disponíveis.")

    def processarLote(self, linhas: list[str]):
        c100_linhas = []
        outras_linhas = []

        for linha in linhas:
            partes = self.pipes(linha)
            if not partes:
                continue
            if partes[0] == "C100":
                c100_linhas.append(partes)
            else:
                outras_linhas.append((linha, partes))

        for partes in c100_linhas:
            self.servicos["C100"].set_context(self.dt_ini_0000, self.filial)
            self.servicos["C100"].processar(partes)
            self.ultimo_num_doc = partes[7]

        self.servicos["C100"].salvar()
        self.servicos["C170"].setDocumentos(self.servicos["C100"].getDocumentos())

        for linha, partes in outras_linhas:
            tipo_registro = partes[0]

            if tipo_registro == "0000":
                self.registro0000(partes)

            if tipo_registro not in self.servicos:
                continue

            servico = self.servicos[tipo_registro]
            servico.set_context(self.dt_ini_0000, self.filial)

            if tipo_registro == "C170":
                self.registroC170(partes)
            else:
                self.registroPadrao(servico, partes)

    def processarLinhas(self, linha: str):
        if not linha.strip():
            return

        partes = self.pipes(linha)
        if not partes:
            return

        tipo_registro = partes[0]

        if tipo_registro == "0000":
            self.registro0000(partes)

        if tipo_registro not in self.servicos:
            return

        servico = self.servicos[tipo_registro]
        servico.set_context(self.dt_ini_0000, self.filial)

        if tipo_registro == "C100":
            self.registroPadrao(servico, partes)
            self.ultimo_num_doc = partes[7]

            self.servicos["C170"].setDocumentos(
                self.servicos["C100"].getDocumentos()
            )

        elif tipo_registro == "C170":
            self.registroC170(partes)

        else:
            self.registroPadrao(servico, partes)

    def pipes(self, linha: str) -> list[str]:
        return linha.split("|")[1:-1]

    def registro0000(self, partes: list[str]):
        self.dt_ini_0000 = partes[3]
        cnpj = partes[6] if len(partes) > 6 else ''
        self.filial = cnpj[8:12] if cnpj else "0000"

    def registroPadrao(self, servico, partes: list[str]):
        servico.processar(partes)

    def registroC170(self, partes: list[str]):
        if not self.ultimo_num_doc:
            print("[DEBUG] num_doc ausente para o C170. Ignorando linha.")
            return

        self.servicos["C170"].processar(partes, self.ultimo_num_doc)

    def salvar(self):
        # Salva os registros C100 primeiro (obrigatório, pois fornece os id_c100)
        self.servicos["C100"].salvar()

        # Depuração: Verifica se os id_c100 foram atribuídos corretamente
        print("[DEBUG] Verificando mapa de documentos para C170:")
        mapa = self.servicos["C100"].getDocumentos()
        for num_doc, info in mapa.items():
            if not info.get("id_c100"):
                print(f"[AVISO] num_doc={num_doc} ainda sem id_c100.")
            else:
                print(f"[OK] num_doc={num_doc} -> id_c100={info['id_c100']}")

        # Atualiza o mapa de documentos do C170 após salvar os C100
        self.servicos["C170"].setDocumentos(mapa)

        # Salva os demais registros na ordem apropriada
        for chave in ["0000", "0150", "0200", "C170"]:
            self.servicos[chave].salvar()


