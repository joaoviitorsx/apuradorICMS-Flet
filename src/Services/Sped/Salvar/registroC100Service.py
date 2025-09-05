import pandas as pd
from src.Utils.sanitizacao import calcularPeriodo
from src.Models.c100Model import C100
from sqlalchemy import text

class RegistroC100Repository:
    def __init__(self, session):
        self.session = session

    def salvamento(self, registros: list[dict]):
        if not registros:
            return

        df = pd.DataFrame(registros)
        df.to_sql('c100', self.session.bind, if_exists='append', index=False, method='multi', chunksize=5000)

class RegistroC100Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.repository = RegistroC100Repository(session)
        self.lote = []
        self.periodo = None
        self.filial = None
        self.mapa_documentos = {}
        self.tabela = "C100"

    def set_context(self, dt_ini, filial):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial

    def sanitizarPartes(self, partes: list[str]) -> list[str]:
        return (partes + [None] * (29 - len(partes)))[:29]

    def processar(self, partes: list[str]):
        partes = self.sanitizarPartes(partes)

        registro = {
            "periodo": self.periodo,
            "reg": partes[0],
            "ind_oper": partes[1],
            "ind_emit": partes[2],
            "cod_part": partes[3],
            "cod_mod": partes[4],
            "cod_sit": partes[5],
            "ser": partes[6],
            "num_doc": partes[7],
            "chv_nfe": partes[8],
            "dt_doc": partes[9],
            "dt_e_s": partes[10],
            "vl_doc": partes[11],
            "ind_pgto": partes[12],
            "vl_desc": partes[13],
            "vl_abat_nt": partes[14],
            "vl_merc": partes[15],
            "ind_frt": partes[16],
            "vl_frt": partes[17],
            "vl_seg": partes[18],
            "vl_out_da": partes[19],
            "vl_bc_icms": partes[20],
            "vl_icms": partes[21],
            "vl_bc_icms_st": partes[22],
            "vl_icms_st": partes[23],
            "vl_ipi": partes[24],
            "vl_pis": partes[25],
            "vl_cofins": partes[26],
            "vl_pis_st": partes[27],
            "vl_cofins_st": partes[28],
            "filial": self.filial,
            "empresa_id": self.empresa_id,
            "is_active": True
        }

        num_doc = str(partes[7]).zfill(9)

        self.mapa_documentos[num_doc] = {
            "ind_oper": partes[1],
            "cod_part": partes[3],
            "chv_nfe": partes[8],
        }

        self.lote.append(registro)

    def salvar(self):
        if not self.lote:
            return

        try:
            self.repository.salvamento(self.lote)

            stmt = text("""
                SELECT id, num_doc FROM c100
                WHERE periodo = :periodo AND empresa_id = :empresa_id AND is_active = true
            """)

            result = self.session.execute(stmt, {
                "periodo": self.periodo,
                "empresa_id": self.empresa_id
            })

            for row in result:
                num_doc = str(row.num_doc).zfill(9)
                if num_doc in self.mapa_documentos:
                    self.mapa_documentos[num_doc]["id_c100"] = row.id

            print(f"[C100] {len(self.lote)} registro(s) inserido(s) com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar registros C100: {e}")
            raise

    def getDocumentos(self) -> dict:
        return self.mapa_documentos

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.lote)
        #self.lote.clear()
        return df
