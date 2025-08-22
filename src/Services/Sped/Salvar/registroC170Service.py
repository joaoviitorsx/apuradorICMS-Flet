from src.Models.c170Model import C170
from src.Utils.sanitizacao import truncar, corrigirUnidade, corrigirIndMov, corrigirCstIcms, TAMANHOS_MAXIMOS, calcularPeriodo, validarEstruturaC170
    
class RegistroC170Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.lote = []
        self.periodo = None
        self.filial = None
        self.mapa_documentos = {}
        self.registros_processados = set()

    def set_context(self, dt_ini, filial):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial
        print(f"[DEBUG] Contexto setado — Período: {self.periodo}, Filial: {self.filial}")

    def setDocumentos(self, mapa_documentos: dict):
        self.mapa_documentos = mapa_documentos
        print(f"[DEBUG] {len(mapa_documentos)} documentos carregados no mapa.")

    def processar(self, partes: list[str]):
        partes = (partes + [None] * 39)[:39]

        num_doc = partes[-3]
        if not num_doc:
            print(f"[DEBUG] num_doc ausente em partes[-3]: {partes}")
            return

        doc_info = self.mapa_documentos.get(num_doc)
        if not doc_info:
            print(f"[DEBUG] Documento não encontrado em mapa_documentos: {num_doc}")
            return

        id_c100 = doc_info.get("id_c100")
        if not id_c100:
            print(f"[DEBUG] id_c100 ausente para num_doc: {num_doc}")
            return

        num_item = partes[2]
        cod_item = truncar(partes[3], TAMANHOS_MAXIMOS['cod_item'])
        registro_id = f"{self.filial}_{num_doc}_{num_item}"
        
        if registro_id in self.registros_processados:
            print(f"[DEBUG] Registro C170 duplicado ignorado: {registro_id}")
            return

        vl_item = partes[7] or "0"

        print(f"[DEBUG] Processando C170 - num_doc: {num_doc}, num_item: {num_item}, cod_item: {cod_item}, vl_item: {vl_item}")

        registro = C170(
            periodo=self.periodo,
            reg="C170",
            num_item=num_item,
            cod_item=cod_item,
            descr_compl=truncar(partes[4], TAMANHOS_MAXIMOS['descr_compl']),
            qtd=partes[5],
            unid=truncar(corrigirUnidade(partes[6]), TAMANHOS_MAXIMOS['unid']),
            vl_item=vl_item,
            vl_desc=partes[8],
            ind_mov=corrigirIndMov(partes[9]),
            cst_icms=corrigirCstIcms(partes[10]),
            cfop=partes[11],
            cod_nat=truncar(partes[37], TAMANHOS_MAXIMOS['cod_nat']),
            vl_bc_icms=partes[12],
            aliq_icms=partes[13],
            vl_icms=partes[14],
            vl_bc_icms_st=partes[15],
            aliq_st=partes[16],
            vl_icms_st=partes[17],
            ind_apur=partes[18],
            cst_ipi=partes[19],
            cod_enq=partes[20],
            vl_bc_ipi=partes[21],
            aliq_ipi=partes[22],
            vl_ipi=partes[23],
            cst_pis=partes[24],
            vl_bc_pis=partes[25],
            aliq_pis=partes[26],
            quant_bc_pis=partes[27],
            aliq_pis_reais=partes[28],
            vl_pis=partes[29],
            cst_cofins=partes[30],
            vl_bc_cofins=partes[31],
            aliq_cofins=partes[32],
            quant_bc_cofins=partes[33],
            aliq_cofins_reais=partes[34],
            vl_cofins=partes[35],
            cod_cta=truncar(partes[36], TAMANHOS_MAXIMOS['cod_cta']),
            vl_abat_nt=partes[38],
            id_c100=id_c100,
            filial=self.filial,
            ind_oper=doc_info.get("ind_oper"),
            cod_part=doc_info.get("cod_part"),
            num_doc=num_doc,
            chv_nfe=doc_info.get("chv_nfe"),
            empresa_id=self.empresa_id,
            is_active=True
        )

        if not validarEstruturaC170(registro):
            print(f"[DEBUG] Registro C170 inválido (estrutura) - registro_id: {registro_id}")
            return

        self.lote.append(registro)
        self.registros_processados.add(registro_id)
        print(f"[DEBUG] Registro C170 adicionado com sucesso: {registro_id}")

    def salvar(self):
        if self.lote:
            try:
                self.session.bulk_save_objects(self.lote)
                print(f"[C170] {len(self.lote)} registro(s) inserido(s) com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao inserir registros C170: {e}")
        else:
            print("[DEBUG] Nenhum registro C170 para salvar.")
