from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.Models.c170cloneModel import C170Clone
from src.Models.fornecedorModel import CadastroFornecedor

class AliquotaSimplesRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def buscarRegistroSimples(self, empresa_id: int, periodo: str):
        query = (
            select(
                C170Clone.id,
                C170Clone.aliquota,
                C170Clone.descr_compl,
                C170Clone.cod_part
            )
            .join(
                CadastroFornecedor,
                (CadastroFornecedor.cod_part == C170Clone.cod_part) &
                (CadastroFornecedor.empresa_id == C170Clone.empresa_id)
            )
            .where(
                C170Clone.periodo == periodo,
                C170Clone.empresa_id == empresa_id,
                C170Clone.is_active == True,
                CadastroFornecedor.simples == True
            )
        )
        return self.db.execute(query).fetchall()

    def atualizarDados(self, atualizacoes: list):
        for aliquota_str, id_c170 in atualizacoes:
            stmt = (
                update(C170Clone)
                .where(C170Clone.id == id_c170)
                .values(aliquota=aliquota_str)
            )
            self.db.execute(stmt)
        self.db.commit()

class AliquotaSimplesService:
    def __init__(self, repository: AliquotaSimplesRepository):
        self.repository = repository

    def atualizar(self, empresa_id: int, periodo: str):
        print("[INÍCIO] Atualizando alíquotas Simples Nacional")
        try:
            registros = self.repository.buscarRegistroSimples(empresa_id, periodo)
            atualizacoes = []

            for row in registros:
                aliquota_str = str(row.aliquota or '').strip().upper()
                if aliquota_str in ['ST', 'ISENTO', 'PAUTA', '']:
                    continue
                try:
                    aliquota = float(aliquota_str.replace(',', '.').replace('%', ''))
                    nova_aliquota = round(aliquota + 3, 2)
                    aliquota_formatada = f"{nova_aliquota:.2f}".replace('.', ',') + '%'
                    atualizacoes.append((aliquota_formatada, row.id))
                except Exception as e:
                    print(f"[AVISO] Erro ao processar registro {row.id}: {e}")

            if atualizacoes:
                self.repository.atualizarDados(atualizacoes)
                print(f"[OK] {len(atualizacoes)} alíquotas atualizadas para Simples Nacional.")

        except Exception as e:
            self.repository.db.rollback()
            print(f"[ERRO] ao atualizar alíquota Simples: {e}")
