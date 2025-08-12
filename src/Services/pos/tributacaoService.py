from __future__ import annotations
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, insert, func, literal, exists, and_, or_, tuple_, text
from sqlalchemy.dialects.mysql import insert as mysql_insert

from src.Models._0200Model import Registro0200
from src.Models.tributacaoModel import CadastroTributacao


class TributacaoService:
    """
    Serviço responsável por:
      1) Inserir em cadastro_tributacao os produtos vindos do 0200 que ainda não existem;
      2) Listar/contar itens com alíquota nula para que a UI (Controller/Flet) abra o diálogo de preenchimento.
      3) Gerenciar duplicatas na base de tributação.

    Observações:
      - Não envolve UI: service apenas insere/consulta e retorna dados.
      - Requer UNIQUE no banco para idempotência: (empresa_id, codigo, produto(255), ncm).
      - Usa normalização (TRIM/IFNULL) nos lados da comparação para evitar duplicatas por espaços/nulos.
    """

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # 1) Inserir produtos faltantes SOMENTE a partir do 0200 (anti-join server)
    # -------------------------------------------------------------------------
    def inserir_faltantes_do_0200(self, empresa_id: int) -> int:
        """
        Insere (empresa_id, codigo, produto, ncm) em cadastro_tributacao vindos do 0200
        que ainda não existem para a empresa (anti-join no servidor).
        Retorna a quantidade inserida.

        Este método é portátil (não depende de MySQL ON DUPLICATE KEY).
        """
        # Base 0200 normalizada
        base_0200 = (
            select(
                literal(empresa_id).label("empresa_id"),
                func.trim(func.ifnull(Registro0200.cod_item, "")).label("codigo"),
                func.trim(func.ifnull(Registro0200.descr_item, "")).label("produto"),
                func.trim(func.ifnull(Registro0200.cod_ncm, "")).label("ncm"),
            )
            .where(Registro0200.empresa_id == empresa_id)
            .subquery("b")
        )

        # Anti-join contra cadastro_tributacao
        exists_ct = exists(
            select(literal(1)).where(
                and_(
                    CadastroTributacao.empresa_id == base_0200.c.empresa_id,
                    func.trim(func.ifnull(CadastroTributacao.codigo, "")) == base_0200.c.codigo,
                    func.trim(func.ifnull(CadastroTributacao.produto, "")) == base_0200.c.produto,
                    func.trim(func.ifnull(CadastroTributacao.ncm, "")) == base_0200.c.ncm,
                )
            )
        )

        candidatos = (
            select(
                base_0200.c.empresa_id,
                base_0200.c.codigo,
                base_0200.c.produto,
                base_0200.c.ncm,
                literal(None, type_=CadastroTributacao.aliquota.type),         # aliquota
            )
            .where(~exists_ct)
            .where(base_0200.c.codigo != "")
            .where(base_0200.c.produto != "")
        )

        stmt = insert(CadastroTributacao).from_select(
            ["empresa_id", "codigo", "produto", "ncm", "aliquota"],
            candidatos,
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    # ------------------------------------------------------------------------------------------------
    # 2) Inserir do 0200 e já retornar para a UI os itens (com id) que seguem com alíquota nula
    #    - Usa ON DUPLICATE KEY UPDATE (MySQL) para ser idempotente e robusto sob concorrência.
    # ------------------------------------------------------------------------------------------------
    def inserir_do_0200_e_listar_para_ui(self, empresa_id: int, limit: int = 300) -> List[Dict]:
        """
        1) Determina os (codigo, produto, ncm) do 0200 para a empresa;
        2) Insere todos idempotentemente em cadastro_tributacao (ON DUPLICATE KEY UPDATE no-op);
        3) Retorna até 'limit' itens desse conjunto com alíquota nula para a UI abrir o diálogo.
        """
        print(f"[DEBUG TributacaoService] === INÍCIO inserir_do_0200_e_listar_para_ui ===")
        print(f"[DEBUG TributacaoService] Empresa: {empresa_id}, Limit: {limit}")
        
        # VERIFICAR ESTADO INICIAL
        total_antes = self.db.execute(
            select(func.count()).select_from(CadastroTributacao)
            .where(CadastroTributacao.empresa_id == empresa_id)
        ).scalar() or 0
        print(f"[DEBUG TributacaoService] Registros ANTES da inserção: {total_antes}")
        
        # Verificar duplicatas ANTES
        duplicatas_antes = self._contar_duplicatas_rapido(empresa_id)
        print(f"[DEBUG TributacaoService] Duplicatas ANTES: {duplicatas_antes}")
        
        # Coletar chaves do 0200 (normalizadas)
        rows_0200 = self.db.execute(
            select(
                func.trim(func.ifnull(Registro0200.cod_item, "")).label("codigo"),
                func.trim(func.ifnull(Registro0200.descr_item, "")).label("produto"),
                func.trim(func.ifnull(Registro0200.cod_ncm, "")).label("ncm"),
            ).where(Registro0200.empresa_id == empresa_id)
        ).all()

        print(f"[DEBUG TributacaoService] Produtos encontrados no 0200: {len(rows_0200)}")

        if not rows_0200:
            print(f"[DEBUG TributacaoService] Nenhum produto no 0200, retornando faltantes existentes")
            return self.listar_faltantes(empresa_id, limit=limit)

        payload = []
        for r in rows_0200:
            codigo = r.codigo or ""
            produto = r.produto or ""
            ncm = r.ncm or ""
            if not codigo or not produto:
                continue
            payload.append(
                dict(
                    empresa_id=empresa_id,
                    codigo=codigo,
                    produto=produto,
                    ncm=ncm,
                    aliquota=None,
                )
            )

        print(f"[DEBUG TributacaoService] Payload preparado: {len(payload)} itens")

        if payload:
            # VERIFICAR SE JÁ EXISTEM ANTES DE INSERIR
            print(f"[DEBUG TributacaoService] Verificando existência antes da inserção...")
            
            # Contar quantos já existem
            keys = [(p["codigo"], p["produto"], p["ncm"]) for p in payload]
            existentes = self.db.execute(
                select(func.count())
                .select_from(CadastroTributacao)
                .where(CadastroTributacao.empresa_id == empresa_id)
                .where(
                    tuple_(CadastroTributacao.codigo, CadastroTributacao.produto, CadastroTributacao.ncm).in_(keys)
                )
            ).scalar() or 0
            
            print(f"[DEBUG TributacaoService] Itens que JÁ EXISTEM: {existentes}")
            print(f"[DEBUG TributacaoService] Itens NOVOS para inserir: {len(payload) - existentes}")
            
            # Executar inserção com ON DUPLICATE KEY UPDATE
            try:
                stmt = mysql_insert(CadastroTributacao).values(payload)
                stmt = stmt.on_duplicate_key_update(empresa_id=stmt.inserted.empresa_id)
                resultado = self.db.execute(stmt)
                self.db.commit()
                
                print(f"[DEBUG TributacaoService] Inserção executada. Rows affected: {resultado.rowcount}")
                
            except Exception as e:
                print(f"[DEBUG TributacaoService] ERRO na inserção: {e}")
                import traceback
                traceback.print_exc()
                self.db.rollback()
        
        # VERIFICAR ESTADO FINAL
        total_depois = self.db.execute(
            select(func.count()).select_from(CadastroTributacao)
            .where(CadastroTributacao.empresa_id == empresa_id)
        ).scalar() or 0
        print(f"[DEBUG TributacaoService] Registros DEPOIS da inserção: {total_depois}")
        print(f"[DEBUG TributacaoService] Diferença: +{total_depois - total_antes}")
        
        # Verificar duplicatas DEPOIS
        duplicatas_depois = self._contar_duplicatas_rapido(empresa_id)
        print(f"[DEBUG TributacaoService] Duplicatas DEPOIS: {duplicatas_depois}")
        
        if duplicatas_depois > duplicatas_antes:
            print(f"[DEBUG TributacaoService] ⚠️ ALERTA: Duplicatas AUMENTARAM em {duplicatas_depois - duplicatas_antes}!")
        
        # Retorna os itens desse conjunto com alíquota nula
        keys = list({(p["codigo"], p["produto"], p["ncm"]) for p in payload})
        if not keys:
            return self.listar_faltantes(empresa_id, limit=limit)

        rows = self.db.execute(
            select(
                CadastroTributacao.id,
                CadastroTributacao.codigo,
                CadastroTributacao.produto,
                CadastroTributacao.ncm,
            )
            .where(CadastroTributacao.empresa_id == empresa_id)
            .where(
                tuple_(CadastroTributacao.codigo, CadastroTributacao.produto, CadastroTributacao.ncm).in_(keys)
            )
            .where(or_(CadastroTributacao.aliquota.is_(None), func.trim(CadastroTributacao.aliquota) == ""))
            .limit(limit)
        ).all()

        resultado_final = [
            {"id": r.id, "codigo": r.codigo or "", "produto": r.produto or "", "ncm": r.ncm or ""}
            for r in rows
        ]
        
        print(f"[DEBUG TributacaoService] Retornando {len(resultado_final)} itens faltantes")
        print(f"[DEBUG TributacaoService] === FIM inserir_do_0200_e_listar_para_ui ===")
        
        return resultado_final

    # -------------------------------------------------------------------------
    # 3) Listar/contar faltantes (para o Controller decidir abrir o diálogo)
    # -------------------------------------------------------------------------
    def listar_faltantes(self, empresa_id: int, limit: int = 300) -> List[Dict]:
        """
        Lista produtos que estão no período atual e precisam de alíquota
        """
        # Pega o período atual
        periodo_query = text("""
            SELECT CONCAT(
                SUBSTRING(dt_ini, 5, 2), '/', 
                SUBSTRING(dt_ini, 1, 4)
            ) as periodo
            FROM `0000` 
            WHERE empresa_id = :empresa_id 
            ORDER BY id DESC 
            LIMIT 1
        """)
        periodo_result = self.db.execute(periodo_query, {"empresa_id": empresa_id}).fetchone()
        periodo_atual = periodo_result[0] if periodo_result else "00/0000"
        
        print(f"[DEBUG TributacaoService] Listando faltantes para período: {periodo_atual}")
        
        # Busca apenas produtos que estão na C170Clone SEM alíquota
        query = text("""
            SELECT t.id, t.codigo, t.produto, t.ncm
            FROM cadastro_tributacao t
            INNER JOIN c170_clone c ON (
                c.empresa_id = t.empresa_id
                AND c.descr_compl = t.produto  
                AND c.ncm = t.ncm
                AND c.periodo = :periodo
            )
            WHERE t.empresa_id = :empresa_id
              AND (t.aliquota IS NULL OR TRIM(t.aliquota) = '')
              AND (c.aliquota IS NULL OR TRIM(c.aliquota) = '')
            LIMIT :limit
        """)
        
        rows = self.db.execute(query, {
            "empresa_id": empresa_id, 
            "periodo": periodo_atual,
            "limit": limit
        }).fetchall()
        
        resultado = [
            {"id": r[0], "codigo": r[1] or "", "produto": r[2] or "", "ncm": r[3] or ""}
            for r in rows
        ]
        
        print(f"[DEBUG TributacaoService] Faltantes encontrados no período {periodo_atual}: {len(resultado)}")
        return resultado

    def contar_faltantes(self, empresa_id: int) -> int:
        """
        CORRIGIDO: Conta apenas produtos do período atual que precisam de alíquota
        """
        # Pega o período atual
        periodo_query = text("""
            SELECT CONCAT(
                SUBSTRING(dt_ini, 5, 2), '/', 
                SUBSTRING(dt_ini, 1, 4)
            ) as periodo
            FROM `0000` 
            WHERE empresa_id = :empresa_id 
            ORDER BY id DESC 
            LIMIT 1
        """)
        periodo_result = self.db.execute(periodo_query, {"empresa_id": empresa_id}).fetchone()
        periodo_atual = periodo_result[0] if periodo_result else "00/0000"
        
        print(f"[DEBUG TributacaoService] Contando faltantes para período: {periodo_atual}")
        
        # CORREÇÃO: Conta apenas produtos que estão na C170Clone SEM alíquota
        query = text("""
            SELECT COUNT(DISTINCT t.id) as total
            FROM cadastro_tributacao t
            INNER JOIN c170_clone c ON (
                c.empresa_id = t.empresa_id
                AND c.descr_compl = t.produto  
                AND c.ncm = t.ncm
                AND c.periodo = :periodo
            )
            WHERE t.empresa_id = :empresa_id
              AND (t.aliquota IS NULL OR TRIM(t.aliquota) = '')
              AND (c.aliquota IS NULL OR TRIM(c.aliquota) = '')
        """)
        
        result = self.db.execute(query, {
            "empresa_id": empresa_id, 
            "periodo": periodo_atual
        }).fetchone()
        
        total = result[0] if result else 0
        print(f"[DEBUG TributacaoService] Total de faltantes no período {periodo_atual}: {total}")
        return total

    # -------------------------------------------------------------------------
    # 4) Métodos auxiliares para gerenciamento de duplicatas
    # -------------------------------------------------------------------------
    def _contar_duplicatas_rapido(self, empresa_id: int) -> int:
        """
        Método auxiliar para contar duplicatas rapidamente
        """
        query = text("""
            SELECT COALESCE(SUM(quantidade - 1), 0) as duplicatas
            FROM (
                SELECT COUNT(*) as quantidade
                FROM cadastro_tributacao 
                WHERE empresa_id = :empresa_id
                GROUP BY produto, ncm
                HAVING COUNT(*) > 1
            ) as dups
        """)
        
        resultado = self.db.execute(query, {"empresa_id": empresa_id}).scalar()
        return resultado or 0

    def verificar_duplicatas(self, empresa_id: int) -> Dict:
        """
        Verifica quantos produtos duplicados existem na base de tributação
        """
        # Conta produtos com duplicatas
        query_produtos = text("""
            SELECT COUNT(*) as produtos_com_duplicatas
            FROM (
                SELECT produto, ncm
                FROM cadastro_tributacao 
                WHERE empresa_id = :empresa_id
                GROUP BY produto, ncm
                HAVING COUNT(*) > 1
            ) as duplicados
        """)
        
        # Conta total de registros duplicados
        query_registros = text("""
            SELECT 
                COALESCE(SUM(quantidade_duplicatas - 1), 0) as total_registros_duplicados
            FROM (
                SELECT COUNT(*) as quantidade_duplicatas
                FROM cadastro_tributacao 
                WHERE empresa_id = :empresa_id
                GROUP BY produto, ncm
                HAVING COUNT(*) > 1
            ) as duplicados
        """)
        
        # Detalhes dos duplicados (máximo 10)
        query_detalhes = text("""
            SELECT 
                produto,
                ncm,
                COUNT(*) as quantidade,
                GROUP_CONCAT(DISTINCT aliquota) as aliquotas,
                GROUP_CONCAT(id) as ids
            FROM cadastro_tributacao 
            WHERE empresa_id = :empresa_id
            GROUP BY produto, ncm
            HAVING COUNT(*) > 1
            ORDER BY quantidade DESC
            LIMIT 10
        """)
        
        produtos_result = self.db.execute(query_produtos, {"empresa_id": empresa_id}).fetchone()
        registros_result = self.db.execute(query_registros, {"empresa_id": empresa_id}).fetchone()
        detalhes_result = self.db.execute(query_detalhes, {"empresa_id": empresa_id}).fetchall()
        
        produtos_com_duplicatas = produtos_result[0] if produtos_result else 0
        total_registros_duplicados = registros_result[0] if registros_result else 0
        
        detalhes = []
        if detalhes_result:
            detalhes = [
                {
                    "produto": row[0],
                    "ncm": row[1], 
                    "quantidade": row[2],
                    "aliquotas": row[3],
                    "ids": row[4]
                }
                for row in detalhes_result
            ]
        
        print(f"[DEBUG TributacaoService] Produtos com duplicatas: {produtos_com_duplicatas}")
        print(f"[DEBUG TributacaoService] Total de registros duplicados: {total_registros_duplicados}")
        
        return {
            "produtos_com_duplicatas": produtos_com_duplicatas,
            "total_registros_duplicados": total_registros_duplicados,
            "detalhes": detalhes
        }

    def limpar_duplicatas(self, empresa_id: int) -> Dict:
        """
        Remove duplicatas mantendo apenas o registro mais recente de cada produto+ncm
        """
        print(f"[DEBUG TributacaoService] Iniciando limpeza de duplicatas para empresa {empresa_id}")
        
        # Identifica duplicatas
        duplicatas_antes = self.verificar_duplicatas(empresa_id)
        print(f"[DEBUG TributacaoService] Duplicatas encontradas: {duplicatas_antes['total_registros_duplicados']}")
        
        if duplicatas_antes['total_registros_duplicados'] == 0:
            return {"removidas": 0, "mensagem": "Nenhuma duplicata encontrada"}
        
        # Remove duplicatas mantendo apenas o ID maior (mais recente) de cada grupo
        query_delete = text("""
            DELETE t1 FROM cadastro_tributacao t1
            INNER JOIN cadastro_tributacao t2 
            WHERE t1.empresa_id = :empresa_id
              AND t2.empresa_id = :empresa_id  
              AND t1.produto = t2.produto
              AND t1.ncm = t2.ncm
              AND t1.id < t2.id
        """)
        
        resultado = self.db.execute(query_delete, {"empresa_id": empresa_id})
        removidas = resultado.rowcount
        
        self.db.commit()
        
        print(f"[DEBUG TributacaoService] Duplicatas removidas: {removidas}")
        
        # Verifica resultado
        duplicatas_depois = self.verificar_duplicatas(empresa_id)
        print(f"[DEBUG TributacaoService] Duplicatas restantes: {duplicatas_depois['total_registros_duplicados']}")
        
        return {
            "removidas": removidas,
            "duplicatas_antes": duplicatas_antes['total_registros_duplicados'],
            "duplicatas_depois": duplicatas_depois['total_registros_duplicados'],
            "mensagem": f"Removidas {removidas} duplicatas"
        }

    # -------------------------------------------------------------------------
    # 5) Métodos de estatísticas e debug
    # -------------------------------------------------------------------------
    def obter_estatisticas(self, empresa_id: int) -> Dict:
        """
        Retorna estatísticas gerais da base de tributação
        """
        # Total de produtos
        total_produtos = self.db.execute(
            select(func.count()).select_from(CadastroTributacao)
            .where(CadastroTributacao.empresa_id == empresa_id)
        ).scalar() or 0
        
        # Produtos com alíquota
        com_aliquota = self.db.execute(
            select(func.count()).select_from(CadastroTributacao)
            .where(CadastroTributacao.empresa_id == empresa_id)
            .where(and_(
                CadastroTributacao.aliquota.isnot(None),
                func.trim(CadastroTributacao.aliquota) != ""
            ))
        ).scalar() or 0
        
        # Produtos sem alíquota
        sem_aliquota = total_produtos - com_aliquota
        
        # Duplicatas
        duplicatas_info = self.verificar_duplicatas(empresa_id)
        
        return {
            "total_produtos": total_produtos,
            "com_aliquota": com_aliquota,
            "sem_aliquota": sem_aliquota,
            "produtos_com_duplicatas": duplicatas_info["produtos_com_duplicatas"],
            "total_registros_duplicados": duplicatas_info["total_registros_duplicados"],
            "percentual_preenchido": round((com_aliquota / total_produtos * 100) if total_produtos > 0 else 0, 2)
        }