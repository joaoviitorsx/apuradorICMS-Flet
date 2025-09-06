import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from threading import Lock, Event
import threading
import queue
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, deque
import time
import logging
from dataclasses import dataclass, field
import multiprocessing as mp
from functools import lru_cache
import gc
import os

from ..Salvar import (
    registro0000Service,
    registro0150Service,
    registro0200Service,
    registroC100Service,
    registroC170Service,
)

@dataclass
class ProcessingMetrics:
    """Métricas de processamento para monitoramento"""
    registros_processados: int = 0
    tempo_inicio: float = field(default_factory=time.time)
    ultimo_checkpoint: float = field(default_factory=time.time)
    
    def registrar_progresso(self, count: int):
        self.registros_processados += count
        agora = time.time()
        if agora - self.ultimo_checkpoint > 10:  # Log a cada 10 segundos
            velocidade = self.registros_processados / (agora - self.tempo_inicio)
            print(f"[METRICS] Processados: {self.registros_processados:,} registros "
                  f"({velocidade:.0f} reg/s)")
            self.ultimo_checkpoint = agora

class OptimizedBufferManager:
    """Gerenciador de buffer otimizado com flush automático"""
    
    def __init__(self, limite_buffer: int = 15000):
        self.buffers = defaultdict(deque)
        self.limite_buffer = limite_buffer
        self._lock = Lock()
        self._total_registros = 0
        
    def adicionar(self, tipo: str, registros: List[Any]):
        with self._lock:
            self.buffers[tipo].extend(registros)
            self._total_registros += len(registros)
            
    def precisa_flush(self) -> bool:
        return self._total_registros >= self.limite_buffer
        
    def extrair_todos(self) -> Dict[str, List]:
        with self._lock:
            resultado = {}
            for tipo, buffer in self.buffers.items():
                if buffer:
                    resultado[tipo] = list(buffer)
                    buffer.clear()
            self._total_registros = 0
            return resultado
            
    def tamanho_total(self) -> int:
        return self._total_registros

class LeitorService:
    def __init__(self, empresa_id, session):
        self.empresa_id = empresa_id
        self.session = session
        self.filial = None
        self.dt_ini_0000 = None
        self.ultimo_num_doc = None
        
        # Configurações otimizadas
        self.cpu_count = min(mp.cpu_count(), 8)  # Limitar para evitar overhead
        self.io_workers = min(4, self.cpu_count)  # Workers para I/O
        self.processing_workers = self.cpu_count  # Workers para processamento
        
        # Buffer manager otimizado
        self.buffer_manager = OptimizedBufferManager(limite_buffer=20000)
        self.metrics = ProcessingMetrics()
        
        # Lock otimizado
        self._main_lock = Lock()
        
        # Cache para extrairCampos
        self._cache_extração = {}
        self._cache_size_limit = 10000
        
        # Event para controle de parada
        self._stop_event = Event()
        
        # Inicialização de serviços (lazy loading)
        self._servicos = None
        
    @property
    def servicos(self):
        """Lazy loading dos serviços para economizar memória"""
        if self._servicos is None:
            self._servicos = {
                "0000": registro0000Service.Registro0000Service(self.session, self.empresa_id),
                "0150": registro0150Service.Registro0150Service(self.session, self.empresa_id),
                "0200": registro0200Service.Registro0200Service(self.session, self.empresa_id),
                "C100": registroC100Service.RegistroC100Service(self.session, self.empresa_id),
                "C170": registroC170Service.RegistroC170Service(self.session, self.empresa_id),
            }
        return self._servicos

    def executar(self, caminhos_arquivos: List[str], tamanho_lote: int = 10000):
        """Execução principal otimizada com melhor tratamento de erros"""
        if not caminhos_arquivos:
            print("[WARNING] Nenhum arquivo para processar")
            return
            
        try:
            print(f"[INFO] Iniciando processamento de {len(caminhos_arquivos)} arquivo(s)")
            print(f"[INFO] Configuração: {self.processing_workers} workers de processamento, "
                  f"lotes de {tamanho_lote:,} registros")
            
            inicio = time.time()
            self.pipeline_otimizado(caminhos_arquivos, tamanho_lote)
            
            # Flush final
            if self.buffer_manager.tamanho_total() > 0:
                self.salvamento_otimizado()
                
            fim = time.time()
            tempo_total = fim - inicio
            
            print(f"[SUCCESS] Processamento finalizado em {tempo_total:.1f}s")
            print(f"[SUCCESS] Total processado: {self.metrics.registros_processados:,} registros")
            print(f"[SUCCESS] Velocidade média: {self.metrics.registros_processados/tempo_total:.0f} reg/s")
            
        except Exception as e:
            self._stop_event.set()
            self.session.rollback()
            print(f"[ERROR] Erro no processamento: {e}")
            raise e
        finally:
            self._cleanup()

    def pipeline_otimizado(self, caminhos_arquivos: List[str], tamanho_lote: int):
        """Pipeline otimizado com melhor balanceamento de carga"""
        
        # Fila otimizada com tamanho dinâmico
        max_queue_size = max(20, min(100, len(caminhos_arquivos) * 2))
        fila_lotes = queue.Queue(maxsize=max_queue_size)
        
        # Thread de leitura otimizada
        leitor_thread = threading.Thread(
            target=self.leitor_otimizado, 
            args=(caminhos_arquivos, tamanho_lote, fila_lotes),
            daemon=False
        )
        leitor_thread.start()
        
        # Thread de salvamento automático
        salvamento_thread = threading.Thread(
            target=self.salvamento_automatico,
            daemon=True
        )
        salvamento_thread.start()
        
        # Pool de processamento otimizado
        with ThreadPoolExecutor(
            max_workers=self.processing_workers,
            thread_name_prefix="Parser"
        ) as executor:
            futures = deque()
            lotes_submetidos = 0
            
            while not self._stop_event.is_set():
                try:
                    # Controlar número de futures pendentes
                    self._limpar_futures_concluidos(futures)
                    
                    # Limitar futures pendentes para evitar uso excessivo de memória
                    if len(futures) >= self.processing_workers * 3:
                        time.sleep(0.01)
                        continue
                    
                    lote = fila_lotes.get(timeout=0.5)
                    if lote is None:  # Sinal de fim
                        break
                        
                    future = executor.submit(self.parser_otimizado, lote, lotes_submetidos)
                    futures.append(future)
                    lotes_submetidos += 1
                    
                except queue.Empty:
                    if not leitor_thread.is_alive():
                        break
                    continue
                except Exception as e:
                    print(f"[ERROR] Erro no pipeline: {e}")
                    self._stop_event.set()
                    break
            
            # Aguardar conclusão de todos os futures
            self._aguardar_futures(futures)
        
        leitor_thread.join(timeout=30)
        if leitor_thread.is_alive():
            print("[WARNING] Thread de leitura não finalizou no tempo esperado")

    def leitor_otimizado(self, caminhos_arquivos: List[str], tamanho_lote: int, fila_lotes: queue.Queue):
        """Leitor otimizado com melhor gerenciamento de memória"""
        try:
            buffer_linhas = []
            buffer_size = 0
            max_buffer_memory = tamanho_lote * 200  # Estimativa de bytes
            
            for i, caminho in enumerate(caminhos_arquivos):
                if self._stop_event.is_set():
                    break
                    
                print(f"[INFO] Processando arquivo {i+1}/{len(caminhos_arquivos)}: {os.path.basename(caminho)}")
                
                try:
                    # Determinar encoding automaticamente se necessário
                    with open(caminho, 'r', encoding="latin1", buffering=8192*2) as arquivo:
                        for linha in arquivo:
                            linha = linha.strip()
                            if linha and not self._stop_event.is_set():
                                buffer_linhas.append(linha)
                                buffer_size += len(linha)
                                
                                # Flush baseado em tamanho ou memória
                                if (len(buffer_linhas) >= tamanho_lote or 
                                    buffer_size >= max_buffer_memory):
                                    
                                    fila_lotes.put(buffer_linhas.copy())
                                    buffer_linhas.clear()
                                    buffer_size = 0
                                    
                except IOError as e:
                    print(f"[ERROR] Erro ao ler arquivo {caminho}: {e}")
                    continue
                    
            # Flush final
            if buffer_linhas and not self._stop_event.is_set():
                fila_lotes.put(buffer_linhas)
                
        except Exception as e:
            print(f"[ERROR] Erro no leitor: {e}")
            self._stop_event.set()
        finally:
            fila_lotes.put(None)  # Sinal de fim

    def parser_otimizado(self, linhas: List[str], lote_id: int) -> Dict[str, Any]:
        """Parser otimizado com melhor cache e processamento"""
        try:
            inicio = time.time()
            registros_processados = self.processamento_otimizado(linhas)
            
            # Adicionar ao buffer de forma thread-safe
            for tipo, registros in registros_processados.items():
                if registros:
                    self.buffer_manager.adicionar(tipo, registros)
            
            # Atualizar métricas
            self.metrics.registrar_progresso(len(linhas))
            
            tempo_processamento = time.time() - inicio
            
            return {
                "lote_id": lote_id,
                "processados": len(linhas),
                "tempo": tempo_processamento,
                "tipos_encontrados": len(registros_processados)
            }
            
        except Exception as e:
            print(f"[ERROR] Erro no parser (lote {lote_id}): {e}")
            return {"lote_id": lote_id, "erro": str(e)}

    def processamento_otimizado(self, linhas: List[str]) -> Dict[str, List]:
        """Processamento otimizado com cache melhorado"""
        registros_por_tipo = defaultdict(list)
        
        # Processamento em lote para melhor localidade de cache
        for linha in linhas:
            partes = self.extrair_campos_cached(linha)
            if partes and len(partes) > 0:
                tipo_registro = partes[0]
                registros_por_tipo[tipo_registro].append(partes)
        
        return registros_por_tipo

    @lru_cache(maxsize=5000)
    def extrair_campos_cached(self, linha: str) -> Tuple[str, ...]:
        """Extração de campos com cache LRU otimizado"""
        if not linha.strip():
            return tuple()
        
        campos = linha.split("|")[1:-1]
        return tuple(campos) if campos else tuple()

    def salvamento_automatico(self):
        """Thread de salvamento automático baseado em buffer"""
        while not self._stop_event.is_set():
            try:
                if self.buffer_manager.precisa_flush():
                    self.salvamento_otimizado()
                time.sleep(1)  # Check a cada segundo
            except Exception as e:
                print(f"[ERROR] Erro no salvamento automático: {e}")
                time.sleep(5)  # Esperar mais em caso de erro

    def salvamento_otimizado(self):
        """Salvamento otimizado com melhor paralelização"""
        with self._main_lock:  # Garantir que apenas um salvamento ocorra por vez
            try:
                registros_buffer = self.buffer_manager.extrair_todos()
                if not registros_buffer:
                    return
                    
                total_registros = sum(len(regs) for regs in registros_buffer.values())
                print(f"[DEBUG] Salvando {total_registros:,} registros de {len(registros_buffer)} tipos")
                
                inicio_salvamento = time.time()
                
                # Processar registros críticos primeiro (0000, C100)
                self._processar_registros_criticos(registros_buffer)
                
                # Processar outros registros em paralelo
                self._processar_registros_paralelo(registros_buffer)
                
                # Commit otimizado
                self.session.commit()
                
                # Limpeza
                self._limpar_lotes_servicos()
                
                tempo_salvamento = time.time() - inicio_salvamento
                print(f"[DEBUG] Salvamento concluído em {tempo_salvamento:.2f}s "
                      f"({total_registros/tempo_salvamento:.0f} reg/s)")
                
                # Garbage collection periódico
                if self.metrics.registros_processados % 50000 == 0:
                    gc.collect()
                
            except Exception as e:
                print(f"[ERROR] Erro no salvamento: {e}")
                self.session.rollback()
                self._limpar_lotes_servicos()
                raise

    def _processar_registros_criticos(self, registros_buffer: Dict[str, List]):
        """Processa registros críticos que outros dependem"""
        # Processar 0000 primeiro
        if "0000" in registros_buffer:
            for partes in registros_buffer["0000"]:
                self.processar_registro0000(list(partes))
            del registros_buffer["0000"]
        
        # Processar C100 e obter mapeamento
        if "C100" in registros_buffer:
            for partes in registros_buffer["C100"]:
                self.processar_registro_c100(list(partes))
            self.servicos["C100"].salvar()
            
            # Configurar C170 com documentos
            mapa_documentos = self.servicos["C100"].getDocumentos()
            self.servicos["C170"].setDocumentos(mapa_documentos)
            del registros_buffer["C100"]

    def _processar_registros_paralelo(self, registros_buffer: Dict[str, List]):
        """Processa registros restantes em paralelo"""
        # Processar registros restantes
        for tipo, registros in registros_buffer.items():
            if tipo in self.servicos:
                servico = self.servicos[tipo]
                servico.set_context(self.dt_ini_0000, self.filial)
                
                for partes in registros:
                    if tipo == "C170" and self.ultimo_num_doc:
                        servico.processar(list(partes), self.ultimo_num_doc)
                    else:
                        servico.processar(list(partes))
        
        # Salvar em paralelo (exceto C100 que já foi salvo)
        tipos_para_salvar = ["0000", "0150", "0200", "C170"]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for tipo in tipos_para_salvar:
                if tipo in self.servicos:
                    future = executor.submit(self.servicos[tipo].salvar)
                    futures.append(future)
            
            # Aguardar conclusão
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[ERROR] Erro ao salvar serviço: {e}")
                    raise

    def processar_registro0000(self, partes: List[str]):
        """Processamento otimizado do registro 0000"""
        if len(partes) > 3:
            self.dt_ini_0000 = partes[3]
        
        cnpj = partes[6] if len(partes) > 6 else ''
        self.filial = cnpj[8:12] if len(cnpj) >= 12 else "0000"
        
        self.servicos["0000"].set_context(self.dt_ini_0000, self.filial)
        self.servicos["0000"].processar(partes)

    def processar_registro_c100(self, partes: List[str]):
        """Processamento otimizado do registro C100"""
        self.servicos["C100"].set_context(self.dt_ini_0000, self.filial)
        self.servicos["C100"].processar(partes)
        
        if len(partes) > 7:
            self.ultimo_num_doc = partes[7]

    def _limpar_futures_concluidos(self, futures: deque):
        """Remove futures concluídos da deque"""
        while futures and futures[0].done():
            future = futures.popleft()
            try:
                future.result()  # Capturar exceções
            except Exception as e:
                print(f"[ERROR] Erro em future: {e}")

    def _aguardar_futures(self, futures: deque):
        """Aguarda conclusão de todos os futures"""
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Erro ao finalizar future: {e}")

    def _limpar_lotes_servicos(self):
        """Limpa lotes de todos os serviços"""
        for servico in self.servicos.values():
            if hasattr(servico, 'lote'):
                servico.lote.clear()

    def _cleanup(self):
        """Limpeza final de recursos"""
        self._stop_event.set()
        
        # Limpar cache
        self.extrair_campos_cached.cache_clear()
        
        # Garbage collection final
        gc.collect()

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do processamento"""
        tempo_decorrido = time.time() - self.metrics.tempo_inicio
        return {
            "registros_processados": self.metrics.registros_processados,
            "tempo_decorrido": tempo_decorrido,
            "velocidade_media": self.metrics.registros_processados / tempo_decorrido if tempo_decorrido > 0 else 0,
            "buffer_atual": self.buffer_manager.tamanho_total(),
            "workers_configurados": self.processing_workers
        }