import pandas as pd
from sqlalchemy import text
from src.Models.c170Model import C170
from src.Utils.sanitizacao import (
    truncar, corrigirUnidade, corrigirIndMov, corrigirCstIcms,
    calcularPeriodo, validarEstruturaC170, TAMANHOS_MAXIMOS
)

class RegistroC170Repository:
    def __init__(self, session):
        self.session = session

    def salvamento(self, registros: list[dict]):
        if not registros:
            return

        df = pd.DataFrame(registros)
        df.to_sql('c170', self.session.bind, if_exists='append', index=False, method='multi', chunksize=5000)

class RegistroC170Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.repository = RegistroC170Repository(session)
        self.periodo = None
        self.filial = None
        self.mapa_documentos = {}
        self.raw_dados = []
        self.lote = []
        self.tabela = "C170"

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

        if not num_doc or len(partes) < 10:
            print(f"[DEBUG] Linha C170 inválida. Ignorando.")
            return

        doc_info = self.mapa_documentos.get(num_doc)
        if not doc_info:
            print(f"[WARN] Documento {num_doc} não encontrado. Ignorando C170.")
            return

        try:
            num_item = str(int(partes[1])).zfill(3)[:3]
        except:
            print(f"[ERRO] num_item inválido para num_doc={num_doc}. Ignorando.")
            return

        # cod_item = partes[2]
        # if cod_item is not None:
        #     cod_item = cod_item.lstrip("0") or "0"

        dados = {
            "periodo": self.periodo,
            "reg": "C170",
            "num_item": num_item,
            #"cod_item": truncar(cod_item, TAMANHOS_MAXIMOS['cod_item']),
            "cod_item": truncar(partes[2], TAMANHOS_MAXIMOS['cod_item']),
            "descr_compl": truncar(partes[3], TAMANHOS_MAXIMOS['descr_compl']),
            "qtd": partes[4],
            "unid": truncar(corrigirUnidade(partes[5]), TAMANHOS_MAXIMOS['unid']),
            "vl_item": partes[6],
            "vl_desc": partes[7],
            "ind_mov": corrigirIndMov(partes[8]),
            "cst_icms": corrigirCstIcms(partes[9]),
            "cfop": partes[10],
            "cod_nat": truncar(partes[11], TAMANHOS_MAXIMOS['cod_nat']),
            "vl_bc_icms": partes[12],
            "aliq_icms": partes[13],
            "vl_icms": partes[14],
            "vl_bc_icms_st": partes[15],
            "aliq_st": partes[16],
            "vl_icms_st": partes[17],
            "ind_apur": partes[18],
            "cst_ipi": partes[19],
            "cod_enq": partes[20],
            "vl_bc_ipi": partes[21],
            "aliq_ipi": partes[22],
            "vl_ipi": partes[23],
            "cst_pis": partes[24],
            "vl_bc_pis": partes[25],
            "aliq_pis": partes[26],
            "quant_bc_pis": partes[27],
            "aliq_pis_reais": partes[28],
            "vl_pis": partes[29],
            "cst_cofins": partes[30],
            "vl_bc_cofins": partes[31],
            "aliq_cofins": partes[32],
            "quant_bc_cofins": partes[33],
            "aliq_cofins_reais": partes[34],
            "vl_cofins": partes[35],
            "cod_cta": truncar(partes[36], TAMANHOS_MAXIMOS['cod_cta']),
            "vl_abat_nt": partes[37],
            "id_c100": doc_info.get("id_c100"),
            "filial": self.filial,
            "ind_oper": doc_info.get("ind_oper"),
            "cod_part": doc_info.get("cod_part"),
            "num_doc": num_doc,
            "chv_nfe": doc_info.get("chv_nfe"),
            "empresa_id": self.empresa_id,
            "is_active": True
        }

        if not validarEstruturaC170(list(dados.values())):
            print(f"[WARN] Estrutura inválida do C170 para num_doc={num_doc}. Ignorado.")
            return

        self.lote.append(dados)

    def salvar(self):
        if not self.lote:
            print("[DEBUG] Nenhum registro C170 válido para salvar.")
            return

        try:
            self.repository.salvamento(self.lote)
            print(f"[C170] {len(self.lote)} registro(s) inserido(s) com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar registros C170: {e}")

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.lote)
        #self.lote.clear()
        return df
