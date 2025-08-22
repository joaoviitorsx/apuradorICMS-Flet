from src.Models._0200Model import Registro0200
from src.Utils.sanitizacao import truncar, calcularPeriodo, TAMANHOS_MAXIMOS, sanitizarCampo
    
class Registro0200Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.lote = []
        self.periodo = None

    def set_context(self, dt_ini, filial=None):
        self.periodo = calcularPeriodo(dt_ini)

    def processar(self, partes: list[str]):
        if not self.periodo:
            raise ValueError("Contexto de período não definido para registro 0200.")

        partes = (partes + [None] * 13)[:13]

        registro = Registro0200(
            reg=partes[0],
            cod_item=sanitizarCampo("cod_item", partes[1]),
            descr_item=sanitizarCampo("descr_item", partes[2]),
            cod_barra=partes[3],
            cod_ant_item=partes[4],
            unid_inv=sanitizarCampo("unid_inv", partes[5]),
            tipo_item=partes[6],
            cod_ncm=partes[7],
            ex_ipi=partes[8],
            cod_gen=partes[9],
            cod_list=partes[10],
            aliq_icms=partes[11],
            cest=partes[12],
            periodo=self.periodo,
            empresa_id=self.empresa_id,
            is_active=True
        )

        self.lote.append(registro)

    def salvar(self):
        if self.lote:
            self.session.bulk_save_objects(self.lote)
            print(f"[0200] {len(self.lote)} registro(s) inserido(s) com sucesso.")
