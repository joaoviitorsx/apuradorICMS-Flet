from src.Models.c170Model import C170
from src.Utils.sanitizacao import truncar, corrigirUnidade, corrigirIndMov, corrigirCstIcms, calcularPeriodo, validarEstruturaC170, TAMANHOS_MAXIMOS
    
class RegistroC170Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.periodo = None
        self.filial = None
        self.mapa_documentos = {}
        self.raw_dados = []
        self.lote = []

    def set_context(self, dt_ini, filial):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial

    def setDocumentos(self, mapa_documentos: dict):
        self.mapa_documentos = mapa_documentos

    def sanitizarPartes(self, partes: list[str]) -> list[str]:
        return (partes + [None] * (39 - len(partes)))[:39]

    def processar(self, partes: list[str], num_doc: str):
        partes = self.sanitizarPartes(partes)
        num_doc = str(num_doc).zfill(9)

        if len(partes) < 10 or not num_doc:
            print(f"[DEBUG] Linha C170 inválida ou num_doc ausente. Ignorando.")
            return

        doc_info = self.mapa_documentos.get(num_doc)
        if not doc_info:
            print(f"[WARN] Documento {num_doc} não encontrado no mapa. Ignorando C170.")
            return

        ind_oper = doc_info.get("ind_oper")
        cod_part = doc_info.get("cod_part")
        chv_nfe = doc_info.get("chv_nfe")

        try:
            num_item = str(int(partes[1])).zfill(3)[:3]
        except:
            print(f"[ERRO] num_item inválido para num_doc={num_doc}. Ignorando C170.")
            return

        cod_item = truncar(partes[2], TAMANHOS_MAXIMOS['cod_item'])
        descr_compl = truncar(partes[3], TAMANHOS_MAXIMOS['descr_compl'])
        qtd = partes[4]
        unid = truncar(corrigirUnidade(partes[5]), TAMANHOS_MAXIMOS['unid'])
        vl_item = partes[6]
        vl_desc = partes[7]
        ind_mov = corrigirIndMov(partes[8])
        cst_icms = corrigirCstIcms(partes[9])
        cfop = partes[10]
        cod_nat = truncar(partes[11], TAMANHOS_MAXIMOS['cod_nat'])

        dados = [
            self.periodo, "C170", num_item, cod_item, descr_compl, qtd, unid, vl_item, vl_desc,
            ind_mov, cst_icms, cfop, cod_nat,
            partes[12], partes[13], partes[14], partes[15], partes[16], partes[17], partes[18],
            partes[19], partes[20], partes[21], partes[22], partes[23],
            partes[24], partes[25], partes[26], partes[27], partes[28], partes[29],
            partes[30], partes[31], partes[32], partes[33], partes[34], partes[35],
            truncar(partes[36], TAMANHOS_MAXIMOS['cod_cta']),
            partes[37],
            num_doc, ind_oper, cod_part, chv_nfe
        ]

        if not validarEstruturaC170(dados):
            print(f"[WARN] Estrutura inválida do C170 para num_doc={num_doc}. Ignorado.")
            return

        self.raw_dados.append(dados)

    def salvar(self):
        for dados in self.raw_dados:
            num_doc = str(dados[39]).zfill(9)
            doc_info = self.mapa_documentos.get(num_doc)
            id_c100 = doc_info.get("id_c100") if doc_info else None

            if not id_c100:
                continue

            try:
                registro = C170(
                    periodo=dados[0],
                    reg=dados[1],
                    num_item=dados[2],
                    cod_item=dados[3],
                    descr_compl=dados[4],
                    qtd=dados[5],
                    unid=dados[6],
                    vl_item=dados[7],
                    vl_desc=dados[8],
                    ind_mov=dados[9],
                    cst_icms=dados[10],
                    cfop=dados[11],
                    cod_nat=dados[12],
                    vl_bc_icms=dados[13],
                    aliq_icms=dados[14],
                    vl_icms=dados[15],
                    vl_bc_icms_st=dados[16],
                    aliq_st=dados[17],
                    vl_icms_st=dados[18],
                    ind_apur=dados[19],
                    cst_ipi=dados[20],
                    cod_enq=dados[21],
                    vl_bc_ipi=dados[22],
                    aliq_ipi=dados[23],
                    vl_ipi=dados[24],
                    cst_pis=dados[25],
                    vl_bc_pis=dados[26],
                    aliq_pis=dados[27],
                    quant_bc_pis=dados[28],
                    aliq_pis_reais=dados[29],
                    vl_pis=dados[30],
                    cst_cofins=dados[31],
                    vl_bc_cofins=dados[32],
                    aliq_cofins=dados[33],
                    quant_bc_cofins=dados[34],
                    aliq_cofins_reais=dados[35],
                    vl_cofins=dados[36],
                    cod_cta=dados[37],
                    vl_abat_nt=dados[38],
                    id_c100=id_c100,
                    filial=self.filial,
                    ind_oper=dados[40],
                    cod_part=dados[41],
                    num_doc=dados[39],
                    chv_nfe=dados[42],
                    empresa_id=self.empresa_id,
                    is_active=True
                )
                self.lote.append(registro)

            except Exception as e:
                print(f"[ERRO] Erro ao montar registro C170 para num_doc={num_doc}: {e}")

        if self.lote:
            try:
                self.session.bulk_save_objects(self.lote)
            except Exception as e:
                print(f"[ERRO] Falha ao salvar registros C170: {e}")
        else:
            print("[DEBUG] Nenhum registro C170 válido para salvar.")
