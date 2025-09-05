import re
import pandas as pd
import unicodedata
from sqlalchemy.orm import Session
from sqlalchemy import text

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

            # Limpeza inicial
            df["CODIGO"] = df["CODIGO"].astype(str).str.strip().str.zfill(3)
            df["PRODUTO"] = df["PRODUTO"].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str[:500]
            df["NCM"] = df["NCM"].astype(str).apply(removedorCaracteres).str.strip()
            df["ALIQUOTA"] = df["ALIQUOTA"].astype(str).str.strip()

            # Validação básica vetorizada
            df["valido"] = True
            df["erros"] = ""

            df.loc[df["CODIGO"] == "", "erros"] += "Código é obrigatório; "
            df.loc[df["PRODUTO"].str.len() < 5, "erros"] += "Produto com menos de 5 caracteres; "
            df.loc[~df["NCM"].str.len().isin([8, 10]), "erros"] += "NCM inválido; "
            df.loc[df["ALIQUOTA"] == "", "erros"] += "Alíquota é obrigatória; "

            df["valido"] = df["erros"] == ""

            df_validos = df[df["valido"]].copy()
            df_invalidos = df[~df["valido"]].copy()

            # Aplicar tratamento de alíquota e categoria
            df_validos["ALIQUOTA_TRATADA"] = df_validos["ALIQUOTA"].apply(tratarAliquota)
            df_validos["CATEGORIA"] = df_validos["ALIQUOTA_TRATADA"].apply(categoriaAliquota)

            # Carregar existentes de uma vez (melhor desempenho)
            df_existentes = pd.read_sql(
                text("""SELECT codigo, produto, ncm, aliquota, categoriaFiscal
                        FROM cadastro_tributacao
                        WHERE empresa_id = :empresa_id"""),
                con=self.repository.db.bind,
                params={"empresa_id": empresa_id}
            )

            chaves_existentes = {
                (str(r["codigo"]).strip(), str(r["produto"]).strip(), str(r["ncm"]).strip()): (r["aliquota"], r.get("categoriaFiscal"))
                for _, r in df_existentes.iterrows()
            }

            dados_insercao = []
            dados_atualizacao = []
            ja_existentes = 0
            atualizados = 0

            for _, row in df_validos.iterrows():
                chave = (row["CODIGO"], row["PRODUTO"], row["NCM"])
                aliq = row["ALIQUOTA_TRATADA"]
                cat = row["CATEGORIA"]

                if chave in chaves_existentes:
                    ja_existentes += 1
                    aliq_existente, cat_existente = chaves_existentes[chave]
                    if aliq != aliq_existente or cat != cat_existente:
                        dados_atualizacao.append({
                            "empresa_id": empresa_id,
                            "codigo": row["CODIGO"],
                            "produto": row["PRODUTO"],
                            "ncm": row["NCM"],
                            "aliquota": aliq,
                            "categoriaFiscal": cat
                        })
                        atualizados += 1
                    continue

                dados_insercao.append({
                    "empresa_id": empresa_id,
                    "codigo": row["CODIGO"],
                    "produto": row["PRODUTO"],
                    "ncm": row["NCM"],
                    "aliquota": aliq,
                    "categoriaFiscal": cat
                })

            if dados_insercao:
                self.repository.db.bulk_insert_mappings(CadastroTributacao, dados_insercao)

            if dados_atualizacao:
                self.repository.db.bulk_update_mappings(CadastroTributacao, dados_atualizacao)

            self.repository.db.commit()

            resultado = {
                "status": "ok" if dados_insercao or dados_atualizacao else "alerta",
                "total_linhas": len(df),
                "cadastrados": len(dados_insercao),
                "ja_existentes": ja_existentes,
                "atualizados": atualizados,
                "com_erro": len(df_invalidos),
                "erros": df_invalidos[["CODIGO", "PRODUTO", "NCM", "ALIQUOTA", "erros"]].head(10).to_dict(orient="records"),
                "mensagem": f"Importação concluída: {len(dados_insercao)} cadastrados, {atualizados} atualizados, {ja_existentes} já existentes, {len(df_invalidos)} com erro"
            }

            if len(df_invalidos) > 10:
                resultado["mensagem"] += " (mostrando apenas os primeiros 10 erros)"

            return resultado

        except Exception as e:
            self.repository.db.rollback()
            return {"status": "erro", "mensagem": f"Erro durante importação: {str(e)}"}
