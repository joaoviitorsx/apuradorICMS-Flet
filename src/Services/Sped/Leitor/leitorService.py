import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import threading
import queue
from typing import List, Dict, Any
from collections import defaultdict

from ..Salvar import (
    registro0000Service,
    registro0150Service,
    registro0200Service,
    registroC100Service,
    registroC170Service,
)

class LeitorService:
    def __init__(self, empresa_id, session):
        self.empresa_id = empresa_id
        self.session = session
        self.filial = None
        self.dt_ini_0000 = None
        self.ultimo_num_doc = None

        self._lock = Lock()
        self._contador_registros = 0
        self._limite_persistencia = 10000
        self.bufferRegistros = defaultdict(list)

        self.servicos = {
            "0000": registro0000Service.Registro0000Service(session, empresa_id),
            "0150": registro0150Service.Registro0150Service(session, empresa_id),
            "0200": registro0200Service.Registro0200Service(session, empresa_id),
            "C100": registroC100Service.RegistroC100Service(session, empresa_id),
            "C170": registroC170Service.RegistroC170Service(session, empresa_id),
        }

    def executar(self, caminhos_arquivos: list[str], tamanho_lote: int = 5000):
        try:
            print(f"[DEBUG] Iniciando processamento de {len(caminhos_arquivos)} arquivo(s)")
            self.pipeline(caminhos_arquivos, tamanho_lote)
            if self._contador_registros > 0:
                self.salvamento()
            print("[DEBUG] Processamento finalizado com sucesso para todos os arquivos.")
        except Exception as e:
            self.session.rollback()
            print(f"[ERROR] Erro no processamento: {e}")
            raise e

    def pipeline(self, caminhos_arquivos: list[str], tamanho_lote: int):
        fila_lotes = queue.Queue(maxsize=50)
        leitor_thread = threading.Thread(target=self.leitor, args=(caminhos_arquivos, tamanho_lote, fila_lotes))
        leitor_thread.start()

        with ThreadPoolExecutor(max_workers=min(4, len(caminhos_arquivos))) as executor:
            futures = []

            while True:
                try:
                    lote = fila_lotes.get(timeout=1)
                    if lote is None:
                        break
                    futures.append(executor.submit(self.parser, lote))
                    self.limpador(futures)
                except queue.Empty:
                    if not leitor_thread.is_alive():
                        break
                    continue

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[ERROR] Erro no parser: {e}")

        leitor_thread.join()

    def leitor(self, caminhos_arquivos: list[str], tamanho_lote: int, fila_lotes: queue.Queue):
        try:
            buffer_linhas = []
            for caminho in caminhos_arquivos:
                with open(caminho, 'r', encoding="latin1") as arquivo:
                    for linha in arquivo:
                        linha = linha.strip()
                        if linha:
                            buffer_linhas.append(linha)
                            if len(buffer_linhas) >= tamanho_lote:
                                fila_lotes.put(buffer_linhas.copy())
                                buffer_linhas.clear()
            if buffer_linhas:
                fila_lotes.put(buffer_linhas)
        except Exception as e:
            print(f"[ERROR] Erro no leitor: {e}")
        finally:
            fila_lotes.put(None)

    def parser(self, linhas: list[str]) -> Dict[str, Any]:
        try:
            registros_processados = self.processamento(linhas)
            self.adicionarBuffer(registros_processados)
            
            with self._lock:
                self.salvamento()

            return {"processados": len(linhas)}
        except Exception as e:
            print(f"[ERROR] Erro no parser: {e}")
            return {}

    def processamento(self, linhas: list[str]) -> Dict[str, List]:
        registros_por_tipo = defaultdict(list)
        for linha in linhas:
            partes = self.extrairCampos(linha)
            if partes:
                registros_por_tipo[partes[0]].append(partes)
        return registros_por_tipo

    def adicionarBuffer(self, registros_por_tipo: Dict[str, List]):
        with self._lock:
            if "0000" in registros_por_tipo:
                for partes in registros_por_tipo["0000"]:
                    self.processarRegistro0000(partes)
            if "C100" in registros_por_tipo:
                for partes in registros_por_tipo["C100"]:
                    self.processarRegistroC100(partes)
            for tipo, registros in registros_por_tipo.items():
                if tipo not in ["0000", "C100"]:
                    self.bufferRegistros[tipo].extend(registros)

    def processarRegistro0000(self, partes: list[str]):
        self.dt_ini_0000 = partes[3]
        cnpj = partes[6] if len(partes) > 6 else ''
        self.filial = cnpj[8:12] if cnpj else "0000"
        self.servicos["0000"].set_context(self.dt_ini_0000, self.filial)
        self.servicos["0000"].processar(partes)

    def processarRegistroC100(self, partes: list[str]):
        self.servicos["C100"].set_context(self.dt_ini_0000, self.filial)
        self.servicos["C100"].processar(partes)
        self.ultimo_num_doc = partes[7] if len(partes) > 7 else None

    def salvamento(self):
        try:
            print(f"[DEBUG] Salvando bloco de {self._contador_registros} registros")

            self.servicos["C100"].salvar()
            mapa_documentos = self.servicos["C100"].getDocumentos()
            self.servicos["C170"].setDocumentos(mapa_documentos)

            self.buffer()

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = []
                for tipo in ["0000", "0150", "0200", "C170"]:
                    if tipo in self.servicos:
                        futures.append(executor.submit(self.servicos[tipo].salvar))

                for f in futures:
                    f.result()

            self.session.commit()
            
            for servico in self.servicos.values():
                servico.lote.clear()
            
            self.bufferRegistros.clear()

        except Exception as e:
            print(f"[ERROR] Erro no processamento: {e}")
            self.session.rollback()
            # Limpar lotes em caso de erro também
            for servico in self.servicos.values():
                servico.lote.clear()
            self.bufferRegistros.clear()

    def buffer(self):
        for tipo, registros in self.bufferRegistros.items():
            if tipo in self.servicos:
                servico = self.servicos[tipo]
                servico.set_context(self.dt_ini_0000, self.filial)
                for partes in registros:
                    if tipo == "C170" and self.ultimo_num_doc:
                        servico.processar(partes, self.ultimo_num_doc)
                    else:
                        servico.processar(partes)

    def extrairCampos(self, linha: str) -> list[str]:
        return linha.split("|")[1:-1] if linha.strip() else []

    def limpador(self, futures: list):
        for f in futures[:]:
            if f.done():
                try:
                    f.result()
                except Exception as e:
                    print(f"[ERROR] Erro ao processar resultado: {e}")
                finally:
                    futures.remove(f)
