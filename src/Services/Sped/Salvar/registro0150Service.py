import pandas as pd
from sqlalchemy import text
from src.Models._0150Model import Registro0150
from src.Utils.siglas import obterUF
from src.Utils.sanitizacao import calcularPeriodo

class Registro0150Repository:
    def __init__(self, session):
        self.session = session

    def salvamento(self, registros: list[dict]):
        if not registros:
            return

        df = pd.DataFrame(registros)
        df.to_sql('0150', self.session.bind, if_exists='append', index=False, method='multi', chunksize=5000)
    
class Registro0150Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.repository = Registro0150Repository(session)
        self.lote = []
        self.periodo = None
        self.filial = None
        self.tabela="0150"

    def set_context(self, dt_ini, filial):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial

    def processar(self, partes: list[str]):
        if not self.periodo:
            raise ValueError("Contexto do período não definido para registro 0150.")

        partes = (partes + [None] * 13)[:13]

        cod_mun = partes[7]
        cod_uf = cod_mun[:2] if cod_mun and len(cod_mun) >= 2 else None
        uf = obterUF(cod_uf)
        cnpj = partes[4]
        pj_pf = "PF" if not cnpj else "PJ"

        registro = {
            "reg": partes[0],
            "cod_part": partes[1],
            "nome": partes[2],
            "cod_pais": partes[3],
            "cnpj": cnpj,
            "cpf": partes[5],
            "ie": partes[6],
            "cod_mun": cod_mun,
            "suframa": partes[8],
            "ende": partes[9],
            "num": partes[10],
            "compl": partes[11],
            "bairro": partes[12],
            "cod_uf": cod_uf,
            "uf": uf,
            "pj_pf": pj_pf,
            "periodo": self.periodo,
            "empresa_id": self.empresa_id,
            "is_active": True
        }

        self.lote.append(registro)

    def salvar(self):
        if self.lote:
            try:
                self.repository.salvamento(self.lote)
                print(f"[0150] {len(self.lote)} registro(s) inserido(s) com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao salvar registros 0150: {e}")

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.lote)
        #self.lote.clear()
        return df