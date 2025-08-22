from src.Models._0000Model import Registro0000
from src.Utils.sanitizacao import calcularPeriodo

class Registro0000Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.lote = []
        self.periodo = None
        self.filial = None

    def set_context(self, dt_ini, filial=None):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial

    def processar(self, partes: list[str]):
        partes = (partes + [None] * 15)[:15]

        dt_ini = partes[3]
        cnpj = partes[6]
        self.filial = cnpj[8:12] if cnpj and len(cnpj) >= 12 else "0000"
        self.periodo = calcularPeriodo(dt_ini)

        registro = Registro0000(
            reg=partes[0],
            cod_ver=partes[1],
            cod_fin=partes[2],
            dt_ini=dt_ini,
            dt_fin=partes[4],
            nome=partes[5],
            cnpj=cnpj,
            cpf=partes[7],
            uf=partes[8],
            ie=partes[9],
            cod_num=partes[10],
            im=partes[11],
            suframa=partes[12],
            ind_perfil=partes[13],
            ind_ativ=partes[14],
            filial=self.filial,
            periodo=self.periodo,
            empresa_id=self.empresa_id,
            is_active=True
        )

        self.lote.append(registro)

    def salvar(self):
        if self.lote:
            self.session.bulk_save_objects(self.lote)
            print(f"[0000] {len(self.lote)} registro(s) inserido(s) com sucesso.")
