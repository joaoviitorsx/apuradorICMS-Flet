import pandas as pd
import re
from sqlalchemy.orm import Session
from src.Config.Database.db import SessionLocal
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.validadores import removedorCaracteres

def categoria_por_aliquota(aliquota):
    """Determina categoria fiscal baseada na alíquota com validação robusta"""
    if not aliquota:
        return 'regraGeral'
        
    # Normaliza a string da alíquota
    aliquota_str = str(aliquota).upper().strip()
    aliquota_str = re.sub(r'[^\d.,A-Z]', '', aliquota_str)  # Remove caracteres especiais exceto vírgula, ponto e letras
    
    # Tokens especiais
    tokens_st = {"ISENTO", "ST", "SUBSTITUICAO", "PAUTA", "0", "0,00", "0.00"}
    if aliquota_str in tokens_st:
        return 'ST'
    
    try:
        # Converte vírgula para ponto e tenta converter para float
        aliquota_normalizada = aliquota_str.replace(',', '.')
        aliquota_num = float(aliquota_normalizada)
        
        # Categorias específicas com tolerância
        if abs(aliquota_num - 17.00) <= 0.01 or abs(aliquota_num - 12.00) <= 0.01 or abs(aliquota_num - 4.00) <= 0.01:
            return '20RegraGeral'
        elif abs(aliquota_num - 5.95) <= 0.01 or abs(aliquota_num - 4.20) <= 0.01 or abs(aliquota_num - 1.54) <= 0.01:
            return '7CestaBasica'
        elif abs(aliquota_num - 10.20) <= 0.01 or abs(aliquota_num - 7.20) <= 0.01 or abs(aliquota_num - 2.63) <= 0.01:
            return '12CestaBasica'
        elif abs(aliquota_num - 37.80) <= 0.01 or abs(aliquota_num - 30.39) <= 0.01 or abs(aliquota_num - 8.13) <= 0.01:
            return '28BebidaAlcoolica'
        else:
            return 'regraGeral'
    except (ValueError, TypeError):
        return 'regraGeral'

def validar_aliquota(aliquota_str: str) -> bool:
    """Valida se a alíquota está em formato correto"""
    if not aliquota_str:
        return False
        
    aliquota_clean = str(aliquota_str).upper().strip()
    
    # Tokens válidos
    tokens_validos = {"ST", "ISENTO", "PAUTA", "SUBSTITUICAO"}
    if aliquota_clean in tokens_validos:
        return True
    
    # Regex para validar formato numérico: até 100%, com até 2 casas decimais
    pattern = r'^(100([.,]0{1,2})?%?|[0-9]{1,2}([.,][0-9]{1,2})?%?)$'
    return bool(re.match(pattern, aliquota_clean))

def normalizar_dados_linha(row, index: int) -> dict:
    """Normaliza e valida uma linha da planilha"""
    try:
        # Extração com fallbacks seguros
        codigo_raw = row.get('codigo', '') or row.get('cod_item', '') or row.get('cod', '')
        produto_raw = row.get('produto', '') or row.get('descricao', '') or row.get('desc', '')
        ncm_raw = row.get('ncm', '') or row.get('cod_ncm', '')
        aliquota_raw = row.get('aliquota', '') or row.get('aliq', '') or row.get('aliq_icms', '')
        
        # Tratamento de valores NaN/None
        codigo = str(codigo_raw).strip() if pd.notna(codigo_raw) else ''
        produto = str(produto_raw).strip() if pd.notna(produto_raw) else ''
        ncm = str(ncm_raw).strip() if pd.notna(ncm_raw) else ''
        aliquota = str(aliquota_raw).strip() if pd.notna(aliquota_raw) else ''
        
        # Normalização avançada do código - CORRIGIDA
        # Preserva códigos numéricos e adiciona zeros à esquerda se necessário
        if codigo:
            # Remove apenas caracteres especiais indesejados, preservando alfanuméricos
            codigo = re.sub(r'[^\w.-]', '', codigo).strip()
            
            # Se for um número puro e tiver menos de 3 dígitos, adiciona zeros à esquerda
            if codigo.isdigit() and len(codigo) < 3:
                codigo = codigo.zfill(3)  # Preenche com zeros à esquerda até 3 dígitos
        
        produto = re.sub(r'\s+', ' ', produto).strip()[:500]  # Limita tamanho e remove espaços extras
        ncm = removedorCaracteres(ncm) if ncm else ''
        
        # Validações específicas - CORRIGIDAS
        erros = []
        
        # CORREÇÃO: Aceita qualquer código não vazio (mesmo com 1 ou 2 caracteres)
        if not codigo:
            erros.append("Código é obrigatório")
        elif len(codigo.strip()) == 0:
            erros.append("Código não pode ser apenas espaços")
            
        if not produto or len(produto) < 5:
            erros.append("Produto deve ter pelo menos 5 caracteres")
            
        if ncm and len(ncm) not in [8, 10]:  # NCM pode ter 8 ou 10 dígitos
            erros.append(f"NCM deve ter 8 ou 10 dígitos, encontrado: {len(ncm)}")
            
        if not aliquota:
            erros.append("Alíquota é obrigatória")
        elif not validar_aliquota(aliquota):
            erros.append(f"Alíquota inválida: '{aliquota}'")
        
        if erros:
            raise ValueError("; ".join(erros))
            
        categoria = categoria_por_aliquota(aliquota)
        
        return {
            "codigo": codigo,
            "produto": produto,
            "ncm": ncm,
            "aliquota": aliquota,
            "categoria": categoria,
            "linha_origem": index + 2  # +2 porque pandas é 0-based e planilha tem header
        }
        
    except Exception as e:
        raise ValueError(f"Erro na linha {index + 2}: {str(e)}")

def importar_planilha_tributacao(path_planilha: str, empresa_id: int) -> dict:
    """
    Importa tributação de planilha Excel com validação robusta
    """
    session = None
    try:
        print(f"[DEBUG] Iniciando importação da planilha: {path_planilha}")
        
        # Leitura da planilha com tratamento de encoding
        try:
            df = pd.read_excel(path_planilha, dtype=str, na_filter=False)
        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro ao ler planilha: {str(e)}"}
        
        if df.empty:
            return {"status": "erro", "mensagem": "Planilha está vazia"}
        
        print(f"[DEBUG] Planilha carregada: {len(df)} linhas, colunas: {list(df.columns)}")
        
        # Normalização das colunas
        df.columns = [str(col).lower().strip().replace(' ', '_') for col in df.columns]
        
        # Verificação de colunas obrigatórias (com flexibilidade)
        colunas_disponiveis = set(df.columns)
        colunas_codigo = {'codigo', 'cod_item', 'cod'}
        colunas_produto = {'produto', 'descricao', 'desc'}
        colunas_aliquota = {'aliquota', 'aliq', 'aliq_icms'}
        
        if not (colunas_codigo & colunas_disponiveis):
            return {"status": "erro", "mensagem": "Coluna de código não encontrada. Colunas aceitas: codigo, cod_item, cod"}
        
        if not (colunas_produto & colunas_disponiveis):
            return {"status": "erro", "mensagem": "Coluna de produto não encontrada. Colunas aceitas: produto, descricao, desc"}
            
        if not (colunas_aliquota & colunas_disponiveis):
            return {"status": "erro", "mensagem": "Coluna de alíquota não encontrada. Colunas aceitas: aliquota, aliq, aliq_icms"}
        
        # Processamento das linhas
        registros_validos = []
        ja_existentes = 0
        erros_detalhados = []
        
        # Usar SessionLocal para garantir gestão correta
        with SessionLocal() as session:
            print(f"[DEBUG] Processando {len(df)} linhas...")
            
            for index, row in df.iterrows():
                try:
                    # Pula linhas completamente vazias
                    if all(str(val).strip() == '' for val in row.values):
                        continue
                        
                    dados_normalizados = normalizar_dados_linha(row, index)
                    
                    # Verifica duplicata por código na empresa
                    existente = session.query(CadastroTributacao).filter_by(
                        empresa_id=empresa_id, 
                        codigo=dados_normalizados["codigo"]
                    ).first()
                    
                    if existente:
                        ja_existentes += 1
                        print(f"[DEBUG] Código já existe: {dados_normalizados['codigo']}")
                        continue
                    
                    # Cria registro
                    registro = CadastroTributacao(
                        empresa_id=empresa_id,
                        codigo=dados_normalizados["codigo"],
                        produto=dados_normalizados["produto"],
                        ncm=dados_normalizados["ncm"],
                        aliquota=dados_normalizados["aliquota"],
                        categoriaFiscal=dados_normalizados["categoria"]
                    )
                    registros_validos.append(registro)
                    
                except Exception as erro_linha:
                    erro_detalhado = {
                        "linha": index + 2,
                        "dados_linha": dict(row),
                        "erro": str(erro_linha)
                    }
                    erros_detalhados.append(erro_detalhado)
                    print(f"[DEBUG] Erro na linha {index + 2}: {erro_linha}")
            
            # Inserção em lote
            if registros_validos:
                print(f"[DEBUG] Inserindo {len(registros_validos)} registros...")
                session.add_all(registros_validos)
                session.commit()
                print("[DEBUG] Inserção concluída com sucesso")
        
        # Resultado consolidado
        total_processadas = len(df) - sum(1 for row in df.itertuples() if all(str(val).strip() == '' for val in row[1:]))
        sucesso = len(registros_validos)
        
        resultado = {
            "status": "ok" if sucesso > 0 else "alerta",
            "total_linhas": len(df),
            "processadas": total_processadas,
            "cadastrados": sucesso,
            "ja_existentes": ja_existentes,
            "com_erro": len(erros_detalhados),
            "erros": erros_detalhados[:10],  # Limita para não sobrecarregar
            "mensagem": f"Importação concluída: {sucesso} cadastrados, {ja_existentes} já existentes, {len(erros_detalhados)} com erro"
        }
        
        if len(erros_detalhados) > 10:
            resultado["mensagem"] += f" (mostrando apenas os primeiros 10 erros)"
        
        return resultado
        
    except Exception as e:
        print(f"[DEBUG] Erro geral na importação: {str(e)}")
        return {"status": "erro", "mensagem": f"Erro durante importação: {str(e)}"}
    finally:
        # Garante que a sessão seja fechada
        if session:
            session.close()