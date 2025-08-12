from __future__ import annotations
from typing import Iterable, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete, literal, or_, text
from sqlalchemy.exc import SQLAlchemyError

from src.Models.c170novaModel import C170Nova
from src.Models.c170cloneModel import C170Clone


class CloneService:
    def __init__(self, db: Session):
        self.db = db

    def clonar_c170nova_para_clone(
        self,
        empresa_id: int,
        periodos: Optional[Iterable[str]] = None,
        reuse_id_from_nova: bool = True,
        replace_strategy: bool = True,
    ) -> int:
        """
        Clona registros de c170nova -> c170_clone.

        Params:
          - empresa_id: empresa alvo.
          - periodos: se informado, clona apenas esses períodos (evita apagar/reescrever tudo da empresa).
          - reuse_id_from_nova: se True, usa o mesmo 'id' de c170nova em c170_clone (como no legado).
                                Se o PK de c170_clone for autoincrement, defina False.
          - replace_strategy: se True, deleta os registros de destino (empresa/períodos) e re-insere.
                              Se False, apenas realiza insert (pode gerar duplicidade se não houver UNIQUE).

        Retorna: quantidade inserida.
        """
        
        print(f"[DEBUG CloneService] Iniciando clonagem C170Nova -> C170Clone")
        print(f"[DEBUG CloneService] Empresa ID: {empresa_id}")
        print(f"[DEBUG CloneService] Períodos: {list(periodos) if periodos else 'TODOS'}")
        print(f"[DEBUG CloneService] Reuse ID from Nova: {reuse_id_from_nova}")
        print(f"[DEBUG CloneService] Replace Strategy: {replace_strategy}")

        try:
            # ---------- 0) Verificar dados de origem ----------
            print(f"[DEBUG CloneService] Verificando dados de origem...")
            
            count_origem_query = self.db.query(C170Nova).filter(C170Nova.empresa_id == empresa_id)
            if periodos:
                count_origem_query = count_origem_query.filter(C170Nova.periodo.in_(list(periodos)))
            
            count_origem = count_origem_query.count()
            print(f"[DEBUG CloneService] Registros na origem (C170Nova): {count_origem}")
            
            if count_origem == 0:
                print(f"[DEBUG CloneService] AVISO: Nenhum registro encontrado na origem!")
                return 0
            
            # Verificar alguns registros de exemplo
            exemplos = count_origem_query.limit(3).all()
            print(f"[DEBUG CloneService] Primeiros registros da origem:")
            for i, ex in enumerate(exemplos):
                print(f"[DEBUG CloneService]   {i+1}. ID: {ex.id}, Cod_Item: {ex.cod_item}, Período: {ex.periodo}")

            # ---------- 1) WHERE base ----------
            print(f"[DEBUG CloneService] Construindo condições WHERE...")
            where_base = [C170Nova.empresa_id == empresa_id]
            if periodos:
                periodos_list = list(periodos)
                where_base.append(C170Nova.periodo.in_(periodos_list))
                print(f"[DEBUG CloneService] Filtro por períodos: {periodos_list}")

            # ---------- 2) Estratégia de replace ----------
            registros_deletados = 0
            if replace_strategy:
                print(f"[DEBUG CloneService] Executando estratégia de replace - deletando registros existentes...")
                
                # Verificar quantos registros existem no destino antes de deletar
                count_destino_query = self.db.query(C170Clone).filter(C170Clone.empresa_id == empresa_id)
                if periodos:
                    count_destino_query = count_destino_query.filter(C170Clone.periodo.in_(list(periodos)))
                
                count_destino_antes = count_destino_query.count()
                print(f"[DEBUG CloneService] Registros existentes no destino (C170Clone): {count_destino_antes}")
                
                if count_destino_antes > 0:
                    # Deletar registros existentes
                    q_del = self.db.query(C170Clone).filter(C170Clone.empresa_id == empresa_id)
                    if periodos:
                        q_del = q_del.filter(C170Clone.periodo.in_(list(periodos)))
                    
                    registros_deletados = q_del.delete(synchronize_session=False)
                    print(f"[DEBUG CloneService] Registros deletados: {registros_deletados}")
                else:
                    print(f"[DEBUG CloneService] Nenhum registro para deletar no destino")
            else:
                print(f"[DEBUG CloneService] Replace strategy = False, mantendo registros existentes")

            # ---------- 3) INSERT…SELECT (server-side, mais rápido) ----------
            print(f"[DEBUG CloneService] Construindo query INSERT...SELECT...")
            
            # Monte o SELECT de origem com os aliases que batem com as colunas do destino.
            select_cols = []

            if reuse_id_from_nova:
                select_cols.append(C170Nova.id.label("id"))
                print(f"[DEBUG CloneService] Reutilizando IDs da tabela origem")

            select_cols += [
                C170Nova.empresa_id.label("empresa_id"),
                C170Nova.cod_item.label("cod_item"),
                C170Nova.periodo.label("periodo"),
                C170Nova.reg.label("reg"),
                C170Nova.num_item.label("num_item"),
                C170Nova.descr_compl.label("descr_compl"),
                C170Nova.cod_ncm.label("ncm"),
                C170Nova.qtd.label("qtd"),
                C170Nova.unid.label("unid"),
                C170Nova.vl_item.label("vl_item"),
                C170Nova.vl_desc.label("vl_desc"),
                C170Nova.cst.label("cst"),
                C170Nova.cfop.label("cfop"),
                C170Nova.id_c100.label("id_c100"),
                C170Nova.filial.label("filial"),
                C170Nova.ind_oper.label("ind_oper"),
                C170Nova.cod_part.label("cod_part"),
                C170Nova.num_doc.label("num_doc"),
                C170Nova.chv_nfe.label("chv_nfe"),
                literal("").label("aliquota"),           # Alíquota vazia inicialmente
                literal(0).label("resultado"),           # Resultado zerado inicialmente
            ]

            print(f"[DEBUG CloneService] Colunas selecionadas: {len(select_cols)}")

            # Construir SELECT
            sel = select(*select_cols).where(*where_base)
            
            # Debug: mostrar a query SQL gerada
            try:
                sql_query = str(sel.compile(compile_kwargs={"literal_binds": True}))
                print(f"[DEBUG CloneService] Query SELECT gerada:")
                print(f"[DEBUG CloneService] {sql_query[:500]}{'...' if len(sql_query) > 500 else ''}")
            except Exception as e:
                print(f"[DEBUG CloneService] Erro ao compilar query para debug: {e}")

            # Nome das colunas do destino na mesma ordem do SELECT
            dest_cols = []
            if reuse_id_from_nova:
                dest_cols.append("id")
            dest_cols += [
                "empresa_id", "cod_item", "periodo", "reg", "num_item", "descr_compl", "ncm",
                "qtd", "unid", "vl_item", "vl_desc", "cst", "cfop", "id_c100", "filial",
                "ind_oper", "cod_part", "num_doc", "chv_nfe", "aliquota", "resultado"
            ]

            print(f"[DEBUG CloneService] Colunas de destino: {dest_cols}")

            # ---------- 4) Executar INSERT ----------
            print(f"[DEBUG CloneService] Executando INSERT...SELECT...")
            
            stmt = insert(C170Clone).from_select(dest_cols, sel)
            
            # Debug: tentar mostrar o INSERT SQL
            try:
                insert_sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
                print(f"[DEBUG CloneService] Query INSERT gerada:")
                print(f"[DEBUG CloneService] {insert_sql[:300]}{'...' if len(insert_sql) > 300 else ''}")
            except Exception as e:
                print(f"[DEBUG CloneService] Erro ao compilar INSERT para debug: {e}")

            result = self.db.execute(stmt)
            registros_inseridos = result.rowcount or 0
            
            print(f"[DEBUG CloneService] Registros inseridos: {registros_inseridos}")

            # ---------- 5) Commit da transação ----------
            print(f"[DEBUG CloneService] Commitando transação...")
            self.db.commit()
            print(f"[DEBUG CloneService] Commit realizado com sucesso")

            # ---------- 6) Verificação final ----------
            print(f"[DEBUG CloneService] Verificando resultado final...")
            
            count_final_query = self.db.query(C170Clone).filter(C170Clone.empresa_id == empresa_id)
            if periodos:
                count_final_query = count_final_query.filter(C170Clone.periodo.in_(list(periodos)))
            
            count_final = count_final_query.count()
            print(f"[DEBUG CloneService] Total de registros no destino após operação: {count_final}")
            
            # Verificar alguns registros inseridos
            exemplos_final = count_final_query.limit(3).all()
            print(f"[DEBUG CloneService] Primeiros registros no destino:")
            for i, ex in enumerate(exemplos_final):
                print(f"[DEBUG CloneService]   {i+1}. ID: {ex.id}, Cod_Item: {ex.cod_item}, Período: {ex.periodo}, Alíquota: '{ex.aliquota}', Resultado: {ex.resultado}")

            # ---------- 7) Resumo final ----------
            print(f"[DEBUG CloneService] === RESUMO DA OPERAÇÃO ===")
            print(f"[DEBUG CloneService] Empresa ID: {empresa_id}")
            print(f"[DEBUG CloneService] Períodos processados: {list(periodos) if periodos else 'TODOS'}")
            print(f"[DEBUG CloneService] Registros na origem: {count_origem}")
            print(f"[DEBUG CloneService] Registros deletados: {registros_deletados}")
            print(f"[DEBUG CloneService] Registros inseridos: {registros_inseridos}")
            print(f"[DEBUG CloneService] Total final no destino: {count_final}")
            print(f"[DEBUG CloneService] Status: SUCESSO")
            print(f"[DEBUG CloneService] ========================")

            return registros_inseridos

        except SQLAlchemyError as e:
            print(f"[DEBUG CloneService] ERRO SQLAlchemy durante clonagem: {e}")
            print(f"[DEBUG CloneService] Tipo do erro: {type(e).__name__}")
            try:
                self.db.rollback()
                print(f"[DEBUG CloneService] Rollback executado")
            except Exception as rollback_error:
                print(f"[DEBUG CloneService] Erro durante rollback: {rollback_error}")
            raise e

        except Exception as e:
            print(f"[DEBUG CloneService] ERRO GERAL durante clonagem: {e}")
            print(f"[DEBUG CloneService] Tipo do erro: {type(e).__name__}")
            import traceback
            print(f"[DEBUG CloneService] Stack trace:")
            traceback.print_exc()
            try:
                self.db.rollback()
                print(f"[DEBUG CloneService] Rollback executado")
            except Exception as rollback_error:
                print(f"[DEBUG CloneService] Erro durante rollback: {rollback_error}")
            raise e

    def verificar_estrutura_tabelas(self) -> dict:
        """
        Método auxiliar para verificar a estrutura das tabelas C170Nova e C170Clone.
        Útil para debugging.
        """
        print(f"[DEBUG CloneService] Verificando estrutura das tabelas...")
        
        resultado = {
            "c170nova": {},
            "c170_clone": {}
        }
        
        try:
            # Verificar C170Nova
            print(f"[DEBUG CloneService] Verificando tabela C170Nova...")
            query_nova = text("PRAGMA table_info(c170nova)")
            result_nova = self.db.execute(query_nova).fetchall()
            
            colunas_nova = []
            for row in result_nova:
                col_info = dict(row._asdict()) if hasattr(row, '_asdict') else dict(row)
                colunas_nova.append(col_info)
                print(f"[DEBUG CloneService]   C170Nova: {col_info}")
            
            resultado["c170nova"] = colunas_nova
            
            # Verificar C170Clone  
            print(f"[DEBUG CloneService] Verificando tabela C170Clone...")
            query_clone = text("PRAGMA table_info(c170_clone)")
            result_clone = self.db.execute(query_clone).fetchall()
            
            colunas_clone = []
            for row in result_clone:
                col_info = dict(row._asdict()) if hasattr(row, '_asdict') else dict(row)
                colunas_clone.append(col_info)
                print(f"[DEBUG CloneService]   C170Clone: {col_info}")
            
            resultado["c170_clone"] = colunas_clone
            
            print(f"[DEBUG CloneService] Estrutura das tabelas verificada com sucesso")
            
        except Exception as e:
            print(f"[DEBUG CloneService] Erro ao verificar estrutura das tabelas: {e}")
            resultado["erro"] = str(e)
        
        return resultado

    def contar_registros_por_empresa(self, empresa_id: int) -> dict:
        """
        Método auxiliar para contar registros nas duas tabelas por empresa.
        """
        print(f"[DEBUG CloneService] Contando registros para empresa {empresa_id}...")
        
        try:
            count_nova = self.db.query(C170Nova).filter(C170Nova.empresa_id == empresa_id).count()
            count_clone = self.db.query(C170Clone).filter(C170Clone.empresa_id == empresa_id).count()
            
            resultado = {
                "empresa_id": empresa_id,
                "c170nova": count_nova,
                "c170_clone": count_clone
            }
            
            print(f"[DEBUG CloneService] Contagem para empresa {empresa_id}:")
            print(f"[DEBUG CloneService]   C170Nova: {count_nova} registros")
            print(f"[DEBUG CloneService]   C170Clone: {count_clone} registros")
            
            return resultado
            
        except Exception as e:
            print(f"[DEBUG CloneService] Erro ao contar registros: {e}")
            return {"erro": str(e)}

    def limpar_clone_por_empresa(self, empresa_id: int, periodos: Optional[Iterable[str]] = None) -> int:
        """
        Método auxiliar para limpar registros da tabela C170Clone.
        """
        print(f"[DEBUG CloneService] Limpando registros de C170Clone...")
        print(f"[DEBUG CloneService] Empresa ID: {empresa_id}")
        print(f"[DEBUG CloneService] Períodos: {list(periodos) if periodos else 'TODOS'}")
        
        try:
            query = self.db.query(C170Clone).filter(C170Clone.empresa_id == empresa_id)
            
            if periodos:
                query = query.filter(C170Clone.periodo.in_(list(periodos)))
            
            count_antes = query.count()
            print(f"[DEBUG CloneService] Registros a serem deletados: {count_antes}")
            
            registros_deletados = query.delete(synchronize_session=False)
            self.db.commit()
            
            print(f"[DEBUG CloneService] Registros deletados: {registros_deletados}")
            return registros_deletados
            
        except Exception as e:
            print(f"[DEBUG CloneService] Erro ao limpar registros: {e}")
            self.db.rollback()
            raise e