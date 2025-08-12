from __future__ import annotations

from typing import List
from src.Utils.processData import process_data


def _strip_bom(texto: str) -> str:
    # remove BOM UTF-8 se houver
    if texto.startswith("\ufeff"):
        return texto.lstrip("\ufeff")
    return texto


def ler_e_processar_arquivos(caminhos: List[str]) -> List[str]:
    """
    Lê uma lista de arquivos SPED (.txt) e retorna uma única lista de linhas
    já normalizadas/ajustadas para o salvamento.
    """
    print(f"[DEBUG] Iniciando processamento de {len(caminhos)} arquivo(s)")
    
    linhas_gerais: List[str] = []
    
    for i, caminho in enumerate(caminhos):
        print(f"[DEBUG] Processando arquivo {i+1}/{len(caminhos)}: {caminho}")
        
        try:
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                bruto = _strip_bom(f.read().strip())
            
            print(f"[DEBUG] Arquivo lido: {len(bruto)} caracteres")
            
            # process_data é o normalizador herdado do legado
            try:
                print("[DEBUG] Chamando process_data...")
                resultado = process_data(bruto)
                print(f"[DEBUG] process_data retornou tipo: {type(resultado)}")
                
                if isinstance(resultado, str):
                    linhas = resultado.splitlines()
                    print(f"[DEBUG] String dividida em {len(linhas)} linhas")
                else:
                    # defensivo, caso a lib do legado retorne iterável
                    linhas = list(resultado)
                    print(f"[DEBUG] Iterável convertido em {len(linhas)} linhas")

                # limpa vazios e espaços
                linhas_limpas = [l.strip() for l in linhas if isinstance(l, str) and l.strip()]
                print(f"[DEBUG] Após limpeza: {len(linhas_limpas)} linhas válidas")
                
                linhas_gerais.extend(linhas_limpas)
                
            except Exception as e:
                print(f"[DEBUG ERRO] Falha em process_data: {e}")
                raise
                
        except Exception as e:
            print(f"[DEBUG ERRO] Falha ao processar arquivo {caminho}: {e}")
            raise

    print(f"[DEBUG] Total de linhas processadas: {len(linhas_gerais)}")
    
    # Mostra algumas linhas de exemplo
    if linhas_gerais:
        print(f"[DEBUG] Primeiras 3 linhas:")
        for i, linha in enumerate(linhas_gerais[:3]):
            print(f"  [{i+1}] {linha[:100]}...")
    
    return linhas_gerais