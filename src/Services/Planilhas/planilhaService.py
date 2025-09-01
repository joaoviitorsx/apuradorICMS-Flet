import re
import pandas as pd
import unicodedata
from sqlalchemy.orm import Session

from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.validadores import removedorCaracteres
from src.Utils.aliquota import categoriaAliquota, tratarAliquota

COLUNAS_SINONIMAS = {
    'CODIGO': ['codigo', 'código', 'cod', 'cod_produto', 'id', 'codigo_item', 'cod_item'],
    'PRODUTO': ['produto', 'descricao', 'descrição', 'desc', 'produto_nome', 'produto_descricao', 'produto_desc'],
    'NCM': ['ncm', 'cod_ncm', 'ncm_code', 'ncm_codigo'],
    'ALIQUOTA': ['aliquota', 'alíquota', 'aliq', 'aliq_icms', 'aliquota_icms'],
}
COLUNAS_NECESSARIAS = ['CODIGO', 'PRODUTO', 'NCM', 'ALIQUOTA']

def contarFaltantes(db_session, empresa_id: int) -> int:
    return db_session.query(CadastroTributacao).filter(
        CadastroTributacao.empresa_id == empresa_id,
        (CadastroTributacao.aliquota == None) | (CadastroTributacao.aliquota == "")
    ).count()

def normalizarColunas(col):
    col = str(col).lower().strip().replace(' ', '_')
    col = unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode()
    return col

def mapearColunas(df):
    colunas_encontradas = {}
    cols_norm = [normalizarColunas(col) for col in df.columns]
    for coluna_padrao, sinonimos in COLUNAS_SINONIMAS.items():
        for nome in sinonimos:
            nome_norm = normalizarColunas(nome)
            for idx, col in enumerate(cols_norm):
                if col == nome_norm:
                    colunas_encontradas[coluna_padrao] = df.columns[idx]
                    break
            if coluna_padrao in colunas_encontradas:
                break
    if all(col in colunas_encontradas for col in COLUNAS_NECESSARIAS):
        return colunas_encontradas
    raise ValueError(f"Colunas obrigatórias não encontradas. Colunas atuais: {df.columns.tolist()}")

class PlanilhaTributacaoRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def verificarDuplicidade(self, empresa_id: int, codigo: str, produto: str, ncm: str) -> CadastroTributacao:
        return self.db.query(CadastroTributacao).filter_by(
            empresa_id=empresa_id, codigo=codigo, produto=produto, ncm=ncm
        ).first()

    def inserirDados(self, registros: list):
        self.db.add_all(registros)
        self.db.commit()

    def atualizarRegistro(self, empresa_id, codigo, produto, ncm, aliquota, categoria):
        self.db.query(CadastroTributacao).filter_by(
            empresa_id=empresa_id, codigo=codigo, produto=produto, ncm=ncm
        ).update({
            "aliquota": aliquota,
            "categoriaFiscal": categoria
        })
        self.db.commit()

class PlanilhaTributacaoService:
    def __init__(self, repository: PlanilhaTributacaoRepository):
        self.repository = repository

    def validarAliquota(self, aliquota_str: str) -> bool:
        if not aliquota_str:
            return False
        aliquota_clean = str(aliquota_str).upper().strip()
        tokens_validos = {"ST", "ISENTO", "PAUTA", "SUBSTITUICAO"}
        if aliquota_clean in tokens_validos:
            return True
        pattern = r'^(100([.,]0{1,2})?%?|[0-9]{1,2}([.,][0-9]{1,2})?%?)$'
        return bool(re.match(pattern, aliquota_clean))

    def importarPlanilha(self, path_planilha: str, empresa_id: int) -> dict:
        try:
            print(f"[DEBUG] Iniciando importação da planilha: {path_planilha}")
            df = pd.read_excel(path_planilha, dtype=str, na_filter=False)
            if df.empty:
                return {"status": "erro", "mensagem": "Planilha está vazia"}

            mapeamento = mapearColunas(df)
            df = df.rename(columns=mapeamento)

            registros_validos = []
            ja_existentes = 0
            atualizados = 0
            erros_detalhados = []

            for index, row in df.iterrows():
                try:
                    codigo = str(row[mapeamento['CODIGO']]).strip()
                    produto = str(row[mapeamento['PRODUTO']]).strip()
                    ncm = removedorCaracteres(str(row[mapeamento['NCM']]).strip())
                    aliquota = tratarAliquota(str(row[mapeamento['ALIQUOTA']]).strip())

                    #print(f"[DEBUG] aliquota original: '{row[mapeamento['ALIQUOTA']]}' -> formatada: '{aliquota}'")

                    if codigo.isdigit() and len(codigo) < 3:
                        codigo = codigo.zfill(3)
                    produto = re.sub(r'\s+', ' ', produto).strip()[:500]

                    erros = []
                    if not codigo:
                        erros.append("Código é obrigatório")
                    if not produto or len(produto) < 5:
                        erros.append("Produto deve ter pelo menos 5 caracteres")
                    if ncm and len(ncm) not in [8, 10]:
                        erros.append(f"NCM deve ter 8 ou 10 dígitos, encontrado: {len(ncm)}")
                    if not aliquota:
                        erros.append("Alíquota é obrigatória")
                    if erros:
                        raise ValueError("; ".join(erros))

                    categoria = categoriaAliquota(aliquota)
                    registro_existente = self.repository.verificarDuplicidade(
                        empresa_id, codigo, produto, ncm
                    )
                    if registro_existente:
                        ja_existentes += 1
                        if (registro_existente.aliquota != aliquota or
                            getattr(registro_existente, "categoriaFiscal", None) != categoria):
                            self.repository.atualizarRegistro(
                                empresa_id, codigo, produto, ncm, aliquota, categoria
                            )
                            atualizados += 1
                        continue
                    registro = CadastroTributacao(
                        empresa_id=empresa_id,
                        codigo=codigo,
                        produto=produto,
                        ncm=ncm,
                        aliquota=aliquota,
                        categoriaFiscal=categoria
                    )
                    registros_validos.append(registro)
                except Exception as erro_linha:
                    erros_detalhados.append({
                        "linha": index + 2,
                        "dados_linha": dict(row),
                        "erro": str(erro_linha)
                    })

            if registros_validos:
                self.repository.inserirDados(registros_validos)

            sucesso = len(registros_validos)
            resultado = {
                "status": "ok" if sucesso > 0 or atualizados > 0 else "alerta",
                "total_linhas": len(df),
                "cadastrados": sucesso,
                "ja_existentes": ja_existentes,
                "atualizados": atualizados,
                "com_erro": len(erros_detalhados),
                "erros": erros_detalhados[:10],
                "mensagem": f"Importação concluída: {sucesso} cadastrados, {atualizados} atualizados, {ja_existentes} já existentes, {len(erros_detalhados)} com erro"
            }
            if len(erros_detalhados) > 10:
                resultado["mensagem"] += " (mostrando apenas os primeiros 10 erros)"
            return resultado

        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro durante importação: {str(e)}"}