from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.Models.c170cloneModel import C170Clone
from src.Models.tributacaoModel import CadastroTributacao

LOTE_TAMANHO = 5000

class AtualizarAliquotaRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarDtInit(self, empresa_id: int):
        from src.Models._0000Model import Registro0000

        registro = (
            self.db.query(Registro0000)
            .filter(Registro0000.empresa_id == empresa_id,
                    Registro0000.is_active == True)
            .order_by(Registro0000.id.desc())
            .first()
        )

        return registro.dt_ini if registro else None

    def buscarRegistros(self, empresa_id: int):
        query = (
            select(
                C170Clone.id.label("id_c170"),
                CadastroTributacao.aliquota.label("nova_aliquota"),
                C170Clone.descr_compl,
                C170Clone.ncm
            )
            .join(
                CadastroTributacao,
                (CadastroTributacao.empresa_id == C170Clone.empresa_id) &
                (CadastroTributacao.produto == C170Clone.descr_compl) &
                (CadastroTributacao.ncm == C170Clone.ncm)
            )
            .where(
                C170Clone.empresa_id == empresa_id,
                C170Clone.is_active == True,
                (C170Clone.aliquota == None) | (C170Clone.aliquota == ''),
                (CadastroTributacao.aliquota != None),
                (CadastroTributacao.aliquota != '')
            )
        )
        return self.db.execute(query).fetchall()

    def atualizarDados(self, dados_lote: list):
        for nova_aliquota, id_c170 in dados_lote:
            stmt = (
                update(C170Clone)
                .where(C170Clone.id == id_c170)
                .values(aliquota=nova_aliquota[:10])
            )
            self.db.execute(stmt)
        self.db.commit()

class AtualizarAliquotaService:
    def __init__(self, repository: AtualizarAliquotaRepository):
        self.repository = repository

    def atualizar(self, empresa_id: int, lote_tamanho: int = LOTE_TAMANHO):
        print("[INÍCIO] Atualizando alíquotas em c170_clone por lotes...")

        try:
            dt_ini = self.repository.buscarDtInit(empresa_id)
            print(f"[DEBUG] Resultado dt_ini: {dt_ini}")
            if not dt_ini:
                print("[AVISO] Nenhum dt_ini encontrado. Cancelando.")
                return

            print("[DEBUG] Buscando registros para atualização...")
            registros = self.repository.buscarRegistros(empresa_id)
            total = len(registros)
            print(f"[INFO] {total} registros a atualizar...")

            if total == 0:
                print("[DEBUG] Nenhum registro encontrado para atualização.")
            else:
                print(f"[DEBUG] Exemplo de registro para atualizar: {registros[0] if registros else 'Nenhum'}")

            for i in range(0, total, lote_tamanho):
                lote = registros[i:i + lote_tamanho]
                dados = [(r.nova_aliquota[:10], r.id_c170) for r in lote]

                print(f"[DEBUG] Atualizando lote {i//lote_tamanho + 1} com {len(lote)} itens.")
                if len(lote) > 0:
                    print(f"[DEBUG] Primeiro item do lote: {lote[0]}")
                self.repository.atualizarDados(dados)
                print(f"[OK] Lote {i//lote_tamanho + 1} atualizado com {len(lote)} itens.")

            print(f"[FINALIZADO] Alíquotas atualizadas em {total} registros para empresa {empresa_id}.")

        except Exception as err:
            self.repository.db.rollback()
            print(f"[ERRO] ao atualizar alíquotas: {err}")