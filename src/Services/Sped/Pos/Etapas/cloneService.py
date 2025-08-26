from sqlalchemy.orm import Session
from src.Models.c170novaModel import C170Nova
from src.Models.c170cloneModel import C170Clone
import traceback

class ClonagemService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def clonarC170Nova(self, empresa_id: int):
        print(f"[INÍCIO] Clonagem completa da c170nova para c170_clone (empresa_id={empresa_id})")
        session: Session = self.session_factory()

        try:
            # Etapa 1: Buscar dados da c170nova
            print("[SELECT] Buscando dados da c170nova...")
            registros = session.query(C170Nova).filter(C170Nova.empresa_id == empresa_id).all()

            # Etapa 2: Mapear para instâncias de C170Clone
            novos_registros = []
            for c in registros:
                novos_registros.append(C170Clone(
                    empresa_id=c.empresa_id,
                    cod_item=c.cod_item,
                    periodo=c.periodo,
                    reg=c.reg,
                    num_item=c.num_item,
                    descr_compl=c.descr_compl,
                    ncm=c.cod_ncm,
                    qtd=c.qtd,
                    unid=c.unid,
                    vl_item=c.vl_item,
                    vl_desc=c.vl_desc,
                    cst=c.cst,
                    cfop=c.cfop,
                    id_c100=c.id_c100,
                    filial=c.filial,
                    ind_oper=c.ind_oper,
                    cod_part=c.cod_part,
                    num_doc=c.num_doc,
                    chv_nfe=c.chv_nfe,
                    aliquota='',
                    resultado='',
                    is_active=True
                ))

            # Etapa 3: Inserir na tabela c170_clone
            if novos_registros:
                print(f"[INSERT] Inserindo {len(novos_registros)} registros...")
                session.bulk_save_objects(novos_registros)
                session.commit()
                print(f"[OK] {len(novos_registros)} registros clonados com sucesso.")
            else:
                print("[INFO] Nenhum registro encontrado para clonar.")

        except Exception as e:
            session.rollback()
            print(f"[ERRO] Falha durante a clonagem da c170nova: {e}")
            traceback.print_exc()

        finally:
            session.close()
            print("[FIM] Clonagem finalizada.")