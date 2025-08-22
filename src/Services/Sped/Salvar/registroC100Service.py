from src.Models.c100Model import C100
from src.Utils.sanitizacao import calcularPeriodo

class RegistroC100Service:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.lote = []
        self.periodo = None
        self.filial = None
        self.mapa_documentos = {}

    def set_context(self, dt_ini, filial):
        self.periodo = calcularPeriodo(dt_ini)
        self.filial = filial

    def sanitizar_partes(self, partes: list[str]) -> list[str]:
        partes = (partes + [None] * 29)[:29]

        ind_pgto = (partes[12] or "").strip()
        if ind_pgto not in {"0", "1", "2"}:
            if ind_pgto:
                print(f"[WARN] ind_pgto inválido: '{ind_pgto}' — valor será limpo.")
            partes[12] = None

        return partes

    def processar(self, partes: list[str]):
        partes = self.sanitizar_partes(partes)

        registro = C100(
            periodo=self.periodo,
            reg=partes[0],
            ind_oper=partes[1],
            ind_emit=partes[2],
            cod_part=partes[3],
            cod_mod=partes[4],
            cod_sit=partes[5],
            ser=partes[6],
            num_doc=partes[7],
            chv_nfe=partes[8],
            dt_doc=partes[9],
            dt_e_s=partes[10],
            vl_doc=partes[11],
            ind_pgto=partes[12],
            vl_desc=partes[13],
            vl_abat_nt=partes[14],
            vl_merc=partes[15],
            ind_frt=partes[16],
            vl_frt=partes[17],
            vl_seg=partes[18],
            vl_out_da=partes[19],
            vl_bc_icms=partes[20],
            vl_icms=partes[21],
            vl_bc_icms_st=partes[22],
            vl_icms_st=partes[23],
            vl_ipi=partes[24],
            vl_pis=partes[25],
            vl_cofins=partes[26],
            vl_pis_st=partes[27],
            vl_cofins_st=partes[28],
            filial=self.filial,
            empresa_id=self.empresa_id,
            is_active=True
        )
        self.lote.append(registro)

        num_doc = partes[7]
        if num_doc:
            self.mapa_documentos[num_doc] = {
                "ind_oper": partes[1],
                "cod_part": partes[3],
                "chv_nfe": partes[8],
                "temp_index": len(self.lote) - 1
            }

    def salvar(self):
        if self.lote:
            self.session.bulk_save_objects(self.lote)
            self.session.flush()

            for obj in self.lote:
                num_doc = obj.num_doc
                if num_doc in self.mapa_documentos:
                    self.mapa_documentos[num_doc]["id_c100"] = obj.id

            print(f"[C100] {len(self.lote)} registro(s) inserido(s) com sucesso.")

    def getDocumentos(self) -> dict:
        return self.mapa_documentos
