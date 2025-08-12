# src/Services/spedSalvarService.py
from __future__ import annotations

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from src.Config.Database.db import SessionLocal
from src.Models._0000Model import Registro0000
from src.Models._0150Mode import Registro0150
from src.Models._0200Model import Registro0200
from src.Models.c100Model import C100
from src.Models.c170Model import C170
from src.Utils.siglas import obterUF
from src.Utils.sanitizacao import (
    truncar, corrigirUnidade, corrigir_ind_mov, corrigir_cst_icms,
    TAMANHOS_MAXIMOS, calcular_periodo, validar_estrutura_c170
)

def _split(linha: str) -> List[str]:
    # corta a primeira e a última "|" e devolve apenas os campos
    try:
        resultado = linha.split("|")[1:-1]
        print(f"[DEBUG] _split linha: {linha[:50]}... -> {len(resultado)} campos")
        return resultado
    except Exception as e:
        print(f"[DEBUG ERRO] Falha em _split para linha: {linha[:50]}... - Erro: {e}")
        raise

def _verificar_periodo_duplicado(db: Session, empresa_id: int, periodo: str) -> None:
    print(f"[DEBUG] Verificando período duplicado: empresa_id={empresa_id}, periodo={periodo}")
    ja_existe = db.scalar(
        select(func.count(C170.id)).where(C170.empresa_id == empresa_id, C170.periodo == periodo)
    )
    print(f"[DEBUG] Registros existentes para o período: {ja_existe}")
    if ja_existe and ja_existe > 0:
        raise ValueError(f"SPED do período {periodo} já foi processado anteriormente.")

def salvar_dados_sped(empresa_id: int, linhas: List[str]) -> Dict[str, Any]:
    """
    Converte as 'linhas' do SPED em objetos SQLAlchemy e faz o commit em lotes.
    Corrige o mapeamento do C100 (SER/NUM_DOC/CHV_NFE) e aplica truncamentos defensivos.
    """
    print(f"[DEBUG] Iniciando salvamento para empresa_id={empresa_id}")
    print(f"[DEBUG] Total de linhas recebidas: {len(linhas)}")
    
    # 1) pegar o 0000 para obter o período-base
    dt_ini_0000 = None
    linha_0000 = None
    
    print("[DEBUG] Procurando registro 0000...")
    for i, linha in enumerate(linhas):
        if linha.startswith("|0000|"):
            print(f"[DEBUG] Registro 0000 encontrado na linha {i+1}: {linha}")
            linha_0000 = linha
            try:
                p = _split(linha)
                print(f"[DEBUG] Campos do 0000: {len(p)} campos")
                if len(p) >= 4:
                    dt_ini_0000 = p[3]
                    print(f"[DEBUG] Data inicial extraída: {dt_ini_0000}")
                else:
                    print(f"[DEBUG ERRO] Registro 0000 tem apenas {len(p)} campos, esperado pelo menos 4")
                break
            except Exception as e:
                print(f"[DEBUG ERRO] Falha ao processar registro 0000: {e}")
                raise
    
    if not dt_ini_0000:
        print("[DEBUG ERRO] Não foi possível encontrar o registro 0000")
        raise ValueError("Não foi possível encontrar o registro 0000 nos dados fornecidos.")

    try:
        periodo_base = calcular_periodo(dt_ini_0000)
        print(f"[DEBUG] Período calculado: {periodo_base}")
    except Exception as e:
        print(f"[DEBUG ERRO] Falha ao calcular período de {dt_ini_0000}: {e}")
        raise

    cont = {"0000": 0, "0150": 0, "0200": 0, "C100": 0, "C170": 0}

    with SessionLocal() as db:
        print("[DEBUG] Conexão com banco estabelecida")
        
        try:
            _verificar_periodo_duplicado(db, empresa_id, periodo_base)
        except Exception as e:
            print(f"[DEBUG ERRO] Falha na verificação de período duplicado: {e}")
            raise

        mapa_documentos: Dict[str, dict] = {}   # num_doc -> {id_c100, ind_oper, cod_part, chv_nfe}
        ultimo_num_doc: str | None = None
        filial_atual: str | None = None

        batch_0000, batch_0150, batch_0200, batch_c100, batch_c170 = [], [], [], [], []
        
        print("[DEBUG] Iniciando processamento linha por linha...")

        for i, linha in enumerate(linhas):
            if not linha or not linha.startswith("|"):
                continue

            tipo_registro = linha.split("|")[1] if "|" in linha else "UNKNOWN"
            
            try:
                # ---------------- 0000 ----------------
                if linha.startswith("|0000|"):
                    print(f"[DEBUG] Processando 0000 linha {i+1}")
                    p = _split(linha); p += [None] * (15 - len(p))
                    cnpj = p[6]
                    filial_atual = (cnpj[8:12] if cnpj else "0000")
                    print(f"[DEBUG] Filial atual definida: {filial_atual}")
                    
                    rec = Registro0000(
                        empresa_id=empresa_id, reg=p[0], cod_ver=p[1], cod_fin=p[2],
                        dt_ini=p[3], dt_fin=p[4], nome=p[5], cnpj=p[6], cpf=p[7],
                        uf=p[8], ie=p[9], cod_num=p[10], im=p[11], suframa=p[12],
                        ind_perfil=p[13], ind_ativ=p[14],
                        filial=filial_atual, periodo=periodo_base
                    )
                    batch_0000.append(rec); cont["0000"] += 1
                    continue

                # ---------------- 0150 ----------------
                if linha.startswith("|0150|"):
                    print(f"[DEBUG] Processando 0150 linha {i+1}")
                    p = _split(linha); p += [None] * (13 - len(p))
                    cod_mun = p[7]; cod_uf = (cod_mun[:2] if cod_mun else None)
                    uf = obterUF(cod_uf)
                    pj_pf = "PF" if p[4] is None else "PJ"
                    rec = Registro0150(
                        empresa_id=empresa_id, reg=p[0], cod_part=p[1], nome=p[2],
                        cod_pais=p[3], cnpj=p[4], cpf=p[5], ie=p[6], cod_mun=p[7],
                        suframa=p[8], ende=p[9], num=p[10], compl=p[11], bairro=p[12],
                        cod_uf=cod_uf, uf=uf, pj_pf=pj_pf, periodo=periodo_base
                    )
                    batch_0150.append(rec); cont["0150"] += 1
                    continue

                # ---------------- 0200 ----------------
                if linha.startswith("|0200|"):
                    print(f"[DEBUG] Processando 0200 linha {i+1}")
                    p = _split(linha); p += [None] * (13 - len(p))
                    rec = Registro0200(
                        empresa_id=empresa_id, reg=p[0],
                        cod_item=truncar(p[1], TAMANHOS_MAXIMOS["cod_item"]),
                        descr_item=truncar(p[2], TAMANHOS_MAXIMOS["descr_item"]),
                        cod_barra=p[3], cod_ant_item=p[4],
                        unid_inv=truncar(p[5], TAMANHOS_MAXIMOS["unid"]),
                        tipo_item=p[6], cod_ncm=p[7], ex_ipi=p[8], cod_gen=p[9],
                        cod_list=p[10], aliq_icms=p[11], cest=p[12],
                        periodo=periodo_base
                    )
                    batch_0200.append(rec); cont["0200"] += 1
                    continue

                # ---------------- C100 ----------------
                if linha.startswith("|C100|"):
                    print(f"[DEBUG] Processando C100 linha {i+1}")
                    p = _split(linha); p += [None] * (29 - len(p))
                    # Layout oficial...
                    ind_oper = p[1]
                    ind_emit = p[2]
                    cod_part = p[3]
                    cod_mod  = p[4]
                    cod_sit  = p[5]
                    ser      = truncar(p[6], 10) if p[6] else None
                    num_doc  = p[7]
                    chv_nfe  = p[8]
                    dt_doc   = p[9]
                    dt_e_s   = p[10]

                    rec = C100(
                        empresa_id=empresa_id, periodo=periodo_base, reg=p[0],
                        ind_oper=ind_oper, ind_emit=ind_emit, cod_part=cod_part,
                        cod_mod=cod_mod, cod_sit=cod_sit, ser=ser,
                        num_doc=num_doc, chv_nfe=chv_nfe,
                        dt_doc=dt_doc, dt_e_s=dt_e_s, vl_doc=p[11], ind_pgto=p[12],
                        vl_desc=p[13], vl_abat_nt=p[14], vl_merc=p[15],
                        ind_frt=p[16], vl_frt=p[17], vl_seg=p[18],
                        vl_out_da=p[19], vl_bc_icms=p[20], vl_icms=p[21],
                        vl_bc_icms_st=p[22], vl_icms_st=p[23], vl_ipi=p[24],
                        vl_pis=p[25], vl_cofins=p[26], vl_pis_st=p[27], vl_cofins_st=p[28],
                        filial=filial_atual
                    )
                    batch_c100.append((rec, num_doc, ind_oper, cod_part, chv_nfe))
                    ultimo_num_doc = num_doc
                    cont["C100"] += 1
                    print(f"[DEBUG] C100 processado: num_doc={num_doc}")
                    continue

                # ---------------- C170 ----------------
                if linha.startswith("|C170|"):
                    print(f"[DEBUG] Processando C170 linha {i+1}")
                    p = _split(linha); p += [None] * (39 - len(p))
                    if not ultimo_num_doc:
                        print("[DEBUG] C170 ignorado: nenhum C100 anterior")
                        continue

                    # garante C100 persistido para ter id
                    if mapa_documentos.get(ultimo_num_doc) is None and batch_c100:
                        print(f"[DEBUG] Persistindo {len(batch_c100)} registros C100")
                        for (c100_obj, _, _, _, _) in batch_c100:
                            db.add(c100_obj)
                        db.flush()
                        for (c100_obj, n_doc, iop, cpart, chave) in batch_c100:
                            mapa_documentos[n_doc] = {
                                "id_c100": c100_obj.id, "ind_oper": iop, "cod_part": cpart, "chv_nfe": chave
                            }
                        batch_c100.clear()

                    pai = mapa_documentos.get(ultimo_num_doc)
                    if not pai:
                        print(f"[DEBUG] C170 ignorado: documento pai {ultimo_num_doc} não encontrado")
                        continue

                    num_item    = p[2]
                    cod_item    = truncar(p[3], TAMANHOS_MAXIMOS["cod_item"])
                    descr_compl = truncar(p[4], TAMANHOS_MAXIMOS["descr_compl"])
                    unid        = truncar(corrigirUnidade(p[6]), TAMANHOS_MAXIMOS["unid"])
                    ind_mov     = corrigir_ind_mov(p[9])
                    cst_icms    = corrigir_cst_icms(p[10])

                    rec = C170(
                        empresa_id=empresa_id, periodo=periodo_base, reg="C170",
                        num_item=num_item, cod_item=cod_item, descr_compl=descr_compl,
                        qtd=p[5], unid=unid, vl_item=p[7], vl_desc=p[8],
                        ind_mov=ind_mov, cst_icms=cst_icms, cfop=p[11],
                        cod_nat=truncar(p[37], TAMANHOS_MAXIMOS["cod_nat"]),
                        vl_bc_icms=p[12], aliq_icms=p[13], vl_icms=p[14],
                        vl_bc_icms_st=p[15], aliq_st=p[16], vl_icms_st=p[17],
                        ind_apur=p[18], cst_ipi=p[19], cod_enq=p[20],
                        vl_bc_ipi=p[21], aliq_ipi=p[22], vl_ipi=p[23],
                        cst_pis=p[24], vl_bc_pis=p[25], aliq_pis=p[26],
                        quant_bc_pis=p[27], aliq_pis_reais=p[28], vl_pis=p[29],
                        cst_cofins=p[30], vl_bc_cofins=p[31], aliq_cofins=p[32],
                        quant_bc_cofins=p[33], aliq_cofins_reais=p[34], vl_cofins=p[35],
                        cod_cta=truncar(p[36], TAMANHOS_MAXIMOS["cod_cta"]),
                        vl_abat_nt=p[37],
                        id_c100=pai["id_c100"], filial=filial_atual,
                        ind_oper=pai["ind_oper"], cod_part=pai["cod_part"],
                        num_doc=ultimo_num_doc, chv_nfe=pai["chv_nfe"]
                    )

                    if validar_estrutura_c170([
                        periodo_base, "C170", num_item, cod_item, descr_compl, p[5], unid, p[7], p[8],
                        ind_mov, cst_icms, p[11], truncar(p[37], TAMANHOS_MAXIMOS["cod_nat"]),
                        p[12], p[13], p[14], p[15], p[16], p[17], p[18], p[19], p[20], p[21],
                        p[22], p[23], p[24], p[25], p[26], p[27], p[28], p[29], p[30], p[31],
                        p[32], p[33], p[34], p[35], truncar(p[36], TAMANHOS_MAXIMOS["cod_cta"]),
                        p[37], pai["id_c100"], filial_atual, pai["ind_oper"], pai["cod_part"],
                        ultimo_num_doc, pai["chv_nfe"], empresa_id
                    ]):
                        batch_c170.append(rec); cont["C170"] += 1
                        print(f"[DEBUG] C170 válido adicionado: item={num_item}")
                    else:
                        print(f"[DEBUG] C170 inválido ignorado: item={num_item}")

            except Exception as e:
                print(f"[DEBUG ERRO] Falha ao processar linha {i+1} (tipo {tipo_registro}): {e}")
                print(f"[DEBUG ERRO] Linha problemática: {linha}")
                raise

        print(f"[DEBUG] Finalizando processamento...")
        print(f"[DEBUG] Contadores: {cont}")

        # Finaliza buffers
        if batch_c100:
            print(f"[DEBUG] Persistindo {len(batch_c100)} registros C100 finais")
            for (c100_obj, _, _, _, _) in batch_c100:
                db.add(c100_obj)
            db.flush()

        todos_registros = batch_0000 + batch_0150 + batch_0200 + batch_c170
        print(f"[DEBUG] Adicionando {len(todos_registros)} registros ao banco")
        
        db.add_all(todos_registros)
        
        print("[DEBUG] Fazendo commit...")
        db.commit()
        print("[DEBUG] Commit realizado com sucesso!")

        return {
            "mensagem": f"Processamento concluído para {periodo_base}.", 
            "contadores": cont,
            "periodo": periodo_base
        }