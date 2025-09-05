import pandas as pd
import asyncio
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
from src.Models.c170cloneModel import C170Clone
import numpy as np
import time

class CalculoResultadoRepository:
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def buscarRegistros(self, db: Session, empresa_id: int) -> pd.DataFrame:
        query = text("""
            SELECT id, vl_item, vl_desc, aliquota
            FROM c170_clone
            WHERE empresa_id = :empresa_id
              AND is_active = 1
        """)
        return pd.read_sql(query, con=db.bind, params={"empresa_id": empresa_id})

    def atualizarLoteComVerificacao(self, df_lote: pd.DataFrame):
        """✅ Atualização com verificação is_active"""
        if df_lote.empty:
            return 0
            
        session = self.session_factory()
        try:
            rows_affected = 0
            
            # Para lotes grandes, usar tabela temporária ou batch updates
            if len(df_lote) > 1000:
                try:
                    rows_affected = self._atualizarViaTempTable(session, df_lote)
                except Exception as temp_table_error:
                    print(f"[AVISO] Erro com tabela temporária, tentando batch update: {temp_table_error}")
                    # Fallback para batch update se tabela temporária falhar
                    rows_affected = self._atualizarViaBatch(session, df_lote)
            else:
                # Para lotes pequenos, usar UPDATE individual
                for _, row in df_lote.iterrows():
                    result = session.execute(
                        text("""
                            UPDATE c170_clone 
                            SET resultado = :resultado 
                            WHERE id = :id AND is_active = 1
                        """),
                        {"id": int(row["id"]), "resultado": float(row["resultado"])}
                    )
                    rows_affected += result.rowcount
                
                session.commit()
            
            return rows_affected
            
        except Exception as e:
            session.rollback()
            print(f"[ERRO] Erro ao atualizar lote: {e}")
            raise
        finally:
            session.close()

    def _atualizarViaTempTable(self, session, df_lote):
        """Método otimizado com tabela temporária"""
        import random
        import threading
        
        # Gerar nome único usando thread ID, timestamp e random
        thread_id = threading.get_ident()
        timestamp = int(time.time() * 1000000)  # microsegundos
        random_suffix = random.randint(10000, 99999)
        temp_table = f"temp_calc_resultado_{thread_id}_{timestamp}_{random_suffix}"
        
        try:
            # Primeiro, garantir que a tabela não existe
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
                session.commit()
            except:
                pass
            
            # Criar tabela temporária com nome único
            df_temp = df_lote[["id", "resultado"]].copy()
            df_temp.to_sql(temp_table, session.bind, index=False, if_exists="fail")
            
            # Update via JOIN
            dialeto = session.bind.dialect.name
            
            if dialeto == "mysql":
                update_query = f"""
                    UPDATE c170_clone c
                    JOIN {temp_table} tmp ON tmp.id = c.id
                    SET c.resultado = tmp.resultado
                    WHERE c.is_active = 1
                """
            elif dialeto in ("postgresql", "postgres"):
                update_query = f"""
                    UPDATE c170_clone
                    SET resultado = tmp.resultado
                    FROM {temp_table} tmp
                    WHERE tmp.id = c170_clone.id
                      AND c170_clone.is_active = 1
                """
            else:
                raise NotImplementedError(f"Dialeto {dialeto} não suportado")
            
            result = session.execute(text(update_query))
            rows_affected = result.rowcount
            session.commit()
            
            return rows_affected
            
        except Exception as e:
            session.rollback()
            print(f"[ERRO] Erro ao atualizar lote: {e}")
            raise
        finally:
            # Limpar tabela temporária de forma segura
            try:
                session.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
                session.commit()
            except Exception as cleanup_error:
                print(f"[AVISO] Erro ao limpar tabela temporária {temp_table}: {cleanup_error}")
                # Tentar rollback se ainda não commitou
                try:
                    session.rollback()
                except:
                    pass

    def _atualizarViaBatch(self, session, df_lote, batch_size: int = 500):
        """Método alternativo usando batch updates (fallback)"""
        print(f"[CALC] 🔄 Executando batch update para {len(df_lote)} registros...")
        
        try:
            rows_affected = 0
            
            # Processar em batches menores para evitar timeout
            for i in range(0, len(df_lote), batch_size):
                batch = df_lote.iloc[i:i + batch_size]
                
                # Usar executemany para eficiência
                batch_data = [
                    {"id": int(row["id"]), "resultado": float(row["resultado"])}
                    for _, row in batch.iterrows()
                ]
                
                result = session.execute(
                    text("""
                        UPDATE c170_clone 
                        SET resultado = :resultado 
                        WHERE id = :id AND is_active = 1
                    """),
                    batch_data
                )
                rows_affected += result.rowcount
                
                # Commit a cada batch para liberar locks
                session.commit()
            
            return rows_affected
            
        except Exception as e:
            session.rollback()
            print(f"[ERRO] Erro no batch update: {e}")
            raise


class CalculoResultadoService:
    def __init__(self, repository: CalculoResultadoRepository, session_factory):
        self.repository = repository
        self.session_factory = session_factory

    async def calcular(self, empresa_id: int, estrategia: str = "lote_unico"):
        """
        ✅ MÉTODO PRINCIPAL ASYNC
        
        Estratégias:
        - "lote_unico": Uma única atualização (mais rápido)
        - "lotes_async": Múltiplos lotes processados async
        - "lotes_paralelo": Múltiplos lotes em paralelo limitado
        """
        print(f"[CALC] 🚀 Iniciando cálculo async para empresa_id={empresa_id} (estratégia: {estrategia})")
        start_time = time.time()

        try:
            # 1. Buscar e processar dados em thread separada
            df_resultados = await asyncio.to_thread(self._buscar_e_processar, empresa_id)
            
            if df_resultados.empty:
                print("[CALC] ⚠️ Nenhum resultado válido encontrado.")
                return {"status": "vazio", "total": 0}

            # 2. Escolher estratégia de atualização
            if estrategia == "lote_unico":
                total_atualizados = await self._atualizar_lote_unico(df_resultados)
            elif estrategia == "lotes_async":
                total_atualizados = await self._atualizar_lotes_async(df_resultados)
            elif estrategia == "lotes_paralelo":
                total_atualizados = await self._atualizar_lotes_paralelo(df_resultados)
            else:
                raise ValueError(f"Estratégia '{estrategia}' não reconhecida")

            total_time = time.time() - start_time
            
            print(f"[CALC] ✅ Processo concluído em {total_time:.2f}s")
            print(f"[CALC] 📊 {total_atualizados} registros atualizados")
            print(f"[CALC] ⚡ Performance: {total_atualizados/total_time:.0f} registros/segundo")
            
            return {
                "status": "sucesso", 
                "total": len(df_resultados), 
                "atualizados": total_atualizados,
                "tempo": round(total_time, 2),
                "performance": round(total_atualizados/total_time, 0)
            }

        except Exception as err:
            print(f"[CALC] ❌ ERRO durante o processamento: {err}")
            import traceback
            traceback.print_exc()
            raise

    async def _atualizar_lote_unico(self, df_resultados: pd.DataFrame):
        """✅ ESTRATÉGIA 1: Lote único (mais rápido)"""
        print(f"[CALC] 💾 Atualizando {len(df_resultados)} registros em lote único...")
        
        total_atualizados = await asyncio.to_thread(
            self.repository.atualizarLoteComVerificacao, 
            df_resultados
        )
        
        return total_atualizados

    async def _atualizar_lotes_async(self, df_resultados: pd.DataFrame, tamanho_lote: int = 5000):
        """✅ ESTRATÉGIA 2: Múltiplos lotes processados sequencialmente async"""
        print(f"[CALC] 💾 Atualizando {len(df_resultados)} registros em lotes async...")
        
        # Dividir em lotes
        lotes = [
            df_resultados.iloc[i:i + tamanho_lote] 
            for i in range(0, len(df_resultados), tamanho_lote)
        ]
        
        print(f"[CALC] 📦 Processando {len(lotes)} lotes sequencialmente...")
        
        total_atualizados = 0
        for i, lote in enumerate(lotes, 1):
            print(f"[CALC] 📦 Processando lote {i}/{len(lotes)} ({len(lote)} registros)...")
            
            rows_affected = await asyncio.to_thread(
                self.repository.atualizarLoteComVerificacao, 
                lote
            )
            
            total_atualizados += rows_affected
            print(f"[CALC] ✅ Lote {i} concluído: {rows_affected} registros atualizados")
        
        return total_atualizados

    async def _atualizar_lotes_paralelo(self, df_resultados: pd.DataFrame, tamanho_lote: int = 5000, max_concurrent: int = 2):
        """✅ ESTRATÉGIA 3: Múltiplos lotes em paralelo limitado - REDUZIDO para evitar conflitos"""
        print(f"[CALC] 💾 Atualizando {len(df_resultados)} registros em lotes paralelos...")
        
        # Dividir em lotes
        lotes = [
            df_resultados.iloc[i:i + tamanho_lote] 
            for i in range(0, len(df_resultados), tamanho_lote)
        ]
        
        print(f"[CALC] 🔄 Processando {len(lotes)} lotes com máximo {max_concurrent} paralelos...")
        
        # Semáforo para limitar concorrência - REDUZIDO para evitar conflitos
        semaforo = asyncio.Semaphore(max_concurrent)
        
        async def processar_lote_com_limite(lote, indice):
            async with semaforo:
                print(f"[CALC] 📦 Iniciando lote {indice + 1}/{len(lotes)}...")
                
                # Adicionar delay pequeno para evitar conflitos de timestamp
                if indice > 0:
                    await asyncio.sleep(0.1)
                
                rows_affected = await asyncio.to_thread(
                    self.repository.atualizarLoteComVerificacao, 
                    lote
                )
                print(f"[CALC] ✅ Lote {indice + 1} concluído: {rows_affected} registros")
                return rows_affected
        
        # Executar lotes em paralelo limitado
        tasks = [
            processar_lote_com_limite(lote, i) 
            for i, lote in enumerate(lotes)
        ]
        
        resultados = await asyncio.gather(*tasks)
        total_atualizados = sum(resultados)
        
        return total_atualizados

    def _buscar_e_processar(self, empresa_id: int) -> pd.DataFrame:
        """Busca dados e processa (executa em thread separada)"""
        db = self.session_factory()
        
        try:
            # 1. Buscar dados
            df = self.repository.buscarRegistros(db, empresa_id)
            
            if df.empty:
                return df
                
            print(f"[CALC] 📋 {len(df)} registros carregados para processamento.")
            
            # 2. Processamento vetorizado
            df_processado = self._processar_dados_vetorizado(df)
            
            return df_processado
            
        finally:
            db.close()

    def _processar_dados_vetorizado(self, df: pd.DataFrame) -> pd.DataFrame:
        """✅ Processamento vetorizado otimizado"""
        print("[CALC] ⚙️ Iniciando processamento vetorizado...")
        
        # Conversões otimizadas
        df["vl_item"] = pd.to_numeric(
            df["vl_item"].astype(str).str.replace(",", ".", regex=False), 
            errors="coerce"
        ).fillna(0.0)
        
        df["vl_desc"] = pd.to_numeric(
            df["vl_desc"].astype(str).str.replace(",", ".", regex=False), 
            errors="coerce"
        ).fillna(0.0)
        
        df["aliquota_str"] = df["aliquota"].astype(str).str.strip().str.upper()
        df["resultado"] = 0.0

        # Processamento de isentos
        mask_isento = df["aliquota_str"].isin(["ISENTO", "ST"])
        df.loc[mask_isento, "resultado"] = 0.00
        
        # Processamento de não-isentos
        df_nao_isento = df[~mask_isento].copy()
        if not df_nao_isento.empty:
            aliquotas_clean = (df_nao_isento["aliquota_str"]
                              .str.replace(",", ".", regex=False)
                              .str.replace("%", "", regex=False))
            
            aliquotas_numeric = pd.to_numeric(aliquotas_clean, errors="coerce")
            base = (df_nao_isento["vl_item"] - df_nao_isento["vl_desc"]).clip(lower=0)
            resultado_calculado = (base * (aliquotas_numeric / 100)).round(2)
            mask_valido = aliquotas_numeric.notnull()
            df.loc[df_nao_isento[mask_valido].index, "resultado"] = resultado_calculado[mask_valido]

        # Filtrar registros válidos
        df_validos = df[mask_isento | (df["resultado"] > 0)].copy()
        
        print(f"[CALC] ✅ Processamento concluído: {len(df_validos)} registros válidos")
        
        return df_validos[["id", "resultado"]]

    # ✅ MÉTODO LEGADO MANTIDO PARA COMPATIBILIDADE
    def calcularLegado(self, empresa_id: int, tamanho_lote: int = 5000, max_threads: int = 4):
        """Método original com threading (mantido como backup)"""
        print("[INÍCIO] Atualizando resultado em paralelo (método legado)")
        # ... código original aqui ...