# src/Services/calculoService.py
from __future__ import annotations

from typing import List, Tuple, Optional

from sqlalchemy import select, update, tuple_, text, func, or_
from sqlalchemy.orm import Session

from src.Models._0000Model import Registro0000
from src.Models.c170cloneModel import C170Clone
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.conversao import Conversor


class CalculoService:
    """
    Executa as três etapas do antigo atualizacoes.py:
      1) Preencher c170_clone.aliquota a partir de cadastro_tributacao (coluna depende do ano)
      2) Ajustar alíquota para fornecedores do Simples (+3 p.p.)
      3) Calcular 'resultado' = (vl_item - vl_desc) * (aliquota/100)
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------------------
    def obter_periodo_atual(self, empresa_id: int) -> str:
        """
        Retorna MM/AAAA a partir do dt_ini mais recente em 0000.
        Aceita dt_ini AAAAMMDD ou AAAAMM.
        """
        dt_ini = self.db.execute(
            select(Registro0000.dt_ini)
            .where(Registro0000.empresa_id == empresa_id)
            .order_by(Registro0000.id.desc())
            .limit(1)
        ).scalar()
        if not dt_ini or len(dt_ini) < 6:
            return "00/0000"
        return f"{dt_ini[2:4]}/{dt_ini[4:]}"

    def _coluna_tributacao_por_ano(self, empresa_id: int):
        dt_ini = self.db.execute(
            select(Registro0000.dt_ini)
            .where(Registro0000.empresa_id == empresa_id)
            .order_by(Registro0000.id.desc())
            .limit(1)
        ).scalar()
        ano = int(dt_ini[4:]) if dt_ini and len(dt_ini) >= 6 else 0
        return CadastroTributacao.aliquota if ano >= 2024 else CadastroTributacao.aliquota_antiga, ("aliquota" if ano >= 2024 else "aliquota_antiga")

    # ---------------------------------------------------------------------
    # 1) Preencher c170_clone.aliquota a partir de cadastro_tributacao
    # ---------------------------------------------------------------------
    def atualizar_aliquota_da_clone(self, empresa_id: int, lote_tamanho: int = 5000) -> None:
        """
        CORRIGIDO: Replica exatamente o comportamento do legado.
        JOIN por produto=descr_compl AND ncm=ncm, processamento em lotes.
        """
        print("[DEBUG CalculoService] [INÍCIO] Atualizando alíquotas em c170_clone por lotes...")
        
        # Obter coluna correta baseada no ano
        coluna_expr, coluna_nome = self._coluna_tributacao_por_ano(empresa_id)
        print(f"[DEBUG CalculoService] Usando coluna: {coluna_nome}")

        # Caminho rápido: MySQL (replicando exatamente o legado)
        if self.db.bind and self.db.bind.dialect.name == "mysql":
            # Busca registros que precisam ser atualizados (igual ao legado)
            result = self.db.execute(
                text(f"""
                    SELECT n.id AS id_c170, c.{coluna_nome} AS nova_aliquota
                    FROM c170_clone n
                    JOIN cadastro_tributacao c
                      ON c.empresa_id = n.empresa_id
                     AND c.produto = n.descr_compl
                     AND c.ncm = n.ncm
                    WHERE n.empresa_id = :eid
                      AND (n.aliquota IS NULL OR n.aliquota = '')
                      AND c.{coluna_nome} IS NOT NULL AND c.{coluna_nome} != ''
                """),
                {"eid": empresa_id},
            )
            
            registros = result.fetchall()
            total = len(registros)
            print(f"[DEBUG CalculoService] [INFO] {total} registros a atualizar...")
            
            if total == 0:
                print("[DEBUG CalculoService] Nenhum registro para atualizar.")
                return

            # Processa em lotes (igual ao legado)
            for i in range(0, total, lote_tamanho):
                lote = registros[i:i + lote_tamanho]
                
                # Prepara dados do lote
                dados = []
                for r in lote:
                    nova_aliquota = str(r.nova_aliquota)[:10]  # Trunca em 10 caracteres
                    dados.append((nova_aliquota, r.id_c170))
                
                # Atualiza lote
                for aliquota, id_registro in dados:
                    self.db.execute(
                        text("UPDATE c170_clone SET aliquota = :aliq WHERE id = :id"),
                        {"aliq": aliquota, "id": id_registro}
                    )
                
                self.db.commit()
                print(f"[DEBUG CalculoService] [OK] Lote {i//lote_tamanho + 1} atualizado com {len(lote)} itens.")

            print(f"[DEBUG CalculoService] [FINALIZADO] Alíquotas atualizadas em {total} registros para empresa {empresa_id}.")
            return

        # Fallback portátil (mantém o código existente como backup)
        print("[DEBUG CalculoService] Usando fallback portátil...")
        pend = self.db.execute(
            select(C170Clone.id, C170Clone.descr_compl, C170Clone.ncm)
            .where(C170Clone.empresa_id == empresa_id)
            .where((C170Clone.aliquota.is_(None)) | (C170Clone.aliquota == ""))
        ).all()
        if not pend:
            print("[DEBUG CalculoService] Nenhum registro pendente encontrado.")
            return

        # Mapeia produto+ncm -> aliquota (coluna escolhida)
        chaves = {(p.descr_compl or "", p.ncm or "") for p in pend}
        aliqs = dict(
            self.db.execute(
                select(CadastroTributacao.produto, CadastroTributacao.ncm, coluna_expr)
                .where(
                    CadastroTributacao.empresa_id == empresa_id,
                    tuple_(CadastroTributacao.produto, CadastroTributacao.ncm).in_(list(chaves)),
                )
            ).all()
        )

        updates = []
        for r in pend:
            a = aliqs.get((r.descr_compl or "", r.ncm or ""))
            if a:
                updates.append((str(a)[:10], r.id))  # Trunca em 10 caracteres

        # Aplica em lotes
        for i in range(0, len(updates), lote_tamanho):
            fatia = updates[i : i + lote_tamanho]
            if not fatia:
                break
            self.db.bulk_update_mappings(
                C170Clone, [{"id": rid, "aliquota": aliq} for aliq, rid in fatia]
            )
            self.db.commit()

    # ---------------------------------------------------------------------
    # 2) Ajustar alíquota para fornecedores do Simples (+3 p.p.)
    # ---------------------------------------------------------------------
    def ajustar_simples(self, empresa_id: int, periodo: str) -> None:
        """
        CORRIGIDO: Replica exatamente o comportamento do legado.
        Para linhas do período e empresa indicados em c170_clone, quando fornecedor é do Simples,
        aumenta a alíquota numérica em 3 pontos percentuais.
        """
        print("[DEBUG CalculoService] [INÍCIO] Atualizando alíquotas Simples Nacional")
        
        # Busca registros de fornecedores Simples (igual ao legado)
        rows = self.db.execute(
            text("""
                SELECT c.id, c.aliquota, c.descr_compl, c.cod_part
                FROM c170_clone c
                JOIN cadastro_fornecedores f 
                    ON f.cod_part = c.cod_part AND f.empresa_id = :eid
                WHERE c.periodo = :per AND c.empresa_id = :eid
                  AND f.simples = 'Sim'
            """),
            {"eid": empresa_id, "per": periodo},
        ).fetchall()

        print(f"[DEBUG CalculoService] Encontrados {len(rows)} registros de fornecedores Simples")

        atualizacoes = []
        for row in rows:
            aliquota_str = str(getattr(row, "aliquota", None) or "").strip().upper()
            
            # Pula marcadores especiais (igual ao legado)
            if aliquota_str in ['ST', 'ISENTO', 'PAUTA', '']:
                continue

            try:
                # Converte usando Conversor (igual ao legado)
                aliquota = Conversor(row.aliquota)
                
                # Adiciona 3 pontos percentuais
                nova_aliquota = round(aliquota + 3, 2)

                # Formata com vírgula + % (igual ao legado)
                aliquota_str = f"{nova_aliquota:.2f}".replace('.', ',') + '%'

                atualizacoes.append((aliquota_str, row.id))
                
            except Exception as e:
                print(f"[DEBUG CalculoService] [AVISO] Erro ao processar registro {row.id}: {e}")

        # Aplica atualizações
        if atualizacoes:
            print(f"[DEBUG CalculoService] Aplicando {len(atualizacoes)} atualizações Simples...")
            for aliquota_str, id_registro in atualizacoes:
                self.db.execute(
                    text("UPDATE c170_clone SET aliquota = :aliq WHERE id = :id"),
                    {"aliq": aliquota_str, "id": id_registro}
                )
            self.db.commit()
            print(f"[DEBUG CalculoService] [OK] {len(atualizacoes)} alíquotas Simples atualizadas")
        else:
            print("[DEBUG CalculoService] Nenhuma alíquota Simples para atualizar")

        print("[DEBUG CalculoService] [FIM] Finalização da atualização de alíquota Simples.")

    # ---------------------------------------------------------------------
    # 3) Calcular 'resultado' = (vl_item - vl_desc) * (aliquota/100)
    # ---------------------------------------------------------------------
    def atualizar_resultado(self, empresa_id: int, lote_tamanho: int = 20000) -> None:
        """
        CORRIGIDO: Replica exatamente o comportamento do legado.
        Calcula 'resultado' para todas as linhas da empresa em c170_clone.
        Converte textos usando Conversor.
        """
        print("[DEBUG CalculoService] [INÍCIO] Atualizando resultado")

        # Busca todos os registros da empresa (igual ao legado)
        registros = self.db.execute(
            text("""
                SELECT id, vl_item, vl_desc, aliquota 
                FROM c170_clone
                WHERE empresa_id = :eid
            """),
            {"eid": empresa_id}
        ).fetchall()

        total = len(registros)
        print(f"[DEBUG CalculoService] Encontrados {total} registros para calcular resultado")

        if total == 0:
            print("[DEBUG CalculoService] Nenhum registro encontrado.")
            return

        atualizacoes = []

        # Processa todos os registros (igual ao legado)
        for row in registros:
            try:
                # Usa Conversor para todos os campos (igual ao legado)
                vl_item = Conversor(row.vl_item)
                vl_desc = Conversor(row.vl_desc) 
                aliquota = Conversor(row.aliquota)

                # Calcula resultado (igual ao legado)
                resultado = round((vl_item - vl_desc) * (aliquota / 100), 2)

                atualizacoes.append((resultado, row.id))

            except Exception as e:
                print(f"[DEBUG CalculoService] [AVISO] Erro ao processar registro {row.id}: {e}")
                # Continua processamento mesmo com erro

        # Aplica atualizações em lotes
        if atualizacoes:
            print(f"[DEBUG CalculoService] Aplicando {len(atualizacoes)} cálculos de resultado...")
            
            # Processa em lotes para não sobrecarregar
            for i in range(0, len(atualizacoes), lote_tamanho):
                lote = atualizacoes[i:i + lote_tamanho]
                
                for resultado, id_registro in lote:
                    self.db.execute(
                        text("UPDATE c170_clone SET resultado = :result WHERE id = :id"),
                        {"result": resultado, "id": id_registro}
                    )
                
                self.db.commit()
                print(f"[DEBUG CalculoService] [OK] Lote {i//lote_tamanho + 1} processado com {len(lote)} itens.")

            print(f"[DEBUG CalculoService] [OK] Resultado atualizado para {total} registros.")
        else:
            print("[DEBUG CalculoService] Nenhum resultado para atualizar")

        print("[DEBUG CalculoService] [FIM] Finalização da atualização de resultado.")

    # ---------------------------------------------------------------------
    # Método de conveniência para executar todas as etapas
    # ---------------------------------------------------------------------
    def calcular_resultado(self, empresa_id: int, periodos: Optional[List[str]] = None) -> dict:
        """
        Método principal que executa todas as 3 etapas seguindo o fluxo do legado:
        1. Atualizar alíquotas na clone
        2. Ajustar para fornecedores Simples
        3. Calcular resultado
        """
        print(f"[DEBUG CalculoService] === INICIANDO CÁLCULO COMPLETO ===")
        
        try:
            # 1. Atualizar alíquotas
            print(f"[DEBUG CalculoService] 1. Atualizando alíquotas da clone...")
            self.atualizar_aliquota_da_clone(empresa_id)
            
            # 2. Ajustar para fornecedores Simples 
            periodo = self.obter_periodo_atual(empresa_id)
            print(f"[DEBUG CalculoService] 2. Ajustando Simples para período {periodo}...")
            self.ajustar_simples(empresa_id, periodo)
            
            # 3. Calcular resultado
            print(f"[DEBUG CalculoService] 3. Calculando resultado...")
            self.atualizar_resultado(empresa_id)
            
            print(f"[DEBUG CalculoService] === CÁLCULO CONCLUÍDO COM SUCESSO ===")
            
            return {
                "status": "ok",
                "mensagem": "Cálculo realizado com sucesso"
            }
            
        except Exception as e:
            print(f"[DEBUG CalculoService] ERRO durante cálculo: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "erro", 
                "mensagem": f"Erro durante cálculo: {e}"
            }