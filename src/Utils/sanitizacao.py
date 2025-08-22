import re
from typing import Optional

TAMANHOS_MAXIMOS = {
    "unid": 2,
    "cod_item": 60,
    "descr_item": 255,
    "descr_compl": 255,
    "cod_nat": 11,
    "cod_cta": 255,
    "cod_part": 60,
    "nome": 100,
}

def limparAliquota(valor):
    if not valor:
        return None
    valor = str(valor).strip().replace("%", "").replace(",", ".")
    try:
        num = float(valor)
        return "0%" if num == 0 else f"{num:.2f}%"
    except ValueError:
        v = valor.upper()
        if v in {"ST", "ISENTO", "PAUTA"}:
            return v
        return None

def truncar(valor, limite):
    if valor is None:
        return None
    s = str(valor)
    return s[:limite]

def corrigirUnidade(valor):
    if not valor:
        return "UN"
    s = str(valor)

    if re.match(r"^\d+[,\.]\d+$", s) or re.match(r"^\d+$", s):
        return "UN"

    m = re.match(r"^([A-Za-z]+)(\d+)", s)
    if m:
        return m.group(1)

    return s[:3] if len(s) > 3 else s

def corrigirCstIcms(valor):
    if not valor:
        return "00"
    s = str(valor).strip().replace(",", ".")
    if s.replace(".", "").isdigit():
        try:
            return str(int(float(s))).zfill(2)[:2]
        except ValueError:
            return "00"
    return s[:2]

def corrigirCfop(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    
    s = re.sub(r"\D", "", str(valor))
    if len(s) > 4:
        s = s[:4]
    if len(s) < 4:
        s = s.zfill(4)
    return s

def corrigirIndMov(valor):
    if not valor:
        return "0"
    s = str(valor)
    return s[:1] if len(s) > 1 else s

def validarEstruturaC170(dados: list) -> bool:
    try:
        if not dados or len(dados) < 45:
            return False
        periodo = dados[0]
        filial = dados[41]
        num_doc = dados[43]
        return bool(periodo and filial and num_doc)
    except Exception:
        return False

def _num_str(v):
    return str(v).replace(",", ".") if isinstance(v, str) else v

def sanitizarCampo(campo, valor):
    def _trunc(tam):
        return lambda v: truncar(v, tam)

    def _zfill2(v):
        return str(v).zfill(2)[:2] if v is not None else "00"

    def _numero(v):
        return str(v).replace(",", ".") if isinstance(v, str) else v

    regras = {
        "cod_item": _trunc(60),
        "descr_item": _trunc(255),
        "descr_compl": _trunc(255),
        "cod_cta": _trunc(255),
        "cod_nat": _trunc(11),
        "cod_part": _trunc(60),
        "nome": _trunc(100),
        "reg": _trunc(4),

        "unid": corrigirUnidade,
        "unid_inv": corrigirUnidade,
        "ind_mov": corrigirIndMov,
        "cod_mod": _zfill2,
        "cst_icms": corrigirCstIcms,
        "cfop": corrigirCfop,

        "vl_item": _numero,
        "vl_desc": _numero,
        "vl_merc": _numero,
        "aliq_icms": _numero,
        "aliq_ipi": _numero,
        "aliq_pis": _numero,
        "aliq_cofins": _numero,
        "vl_bc_icms": _numero,
        "vl_icms": _numero,
        "vl_bc_ipi": _numero,
        "vl_ipi": _numero,
        "vl_bc_pis": _numero,
        "vl_pis": _numero,
        "vl_bc_cofins": _numero,
        "vl_cofins": _numero,
        "vl_abat_nt": _numero,
        "quant_bc_pis": _numero,
        "quant_bc_cofins": _numero,
        "aliq_pis_reais": _numero,
        "aliq_cofins_reais": _numero,
    }

    try:
        return regras.get(campo, lambda v: v)(valor)
    except Exception:
        return valor

def sanitizarRegistro(registro_dict: dict) -> dict:
    return {campo: sanitizarCampo(campo, valor) for campo, valor in registro_dict.items()}

def calcularPeriodo(dt_ini_0000: str) -> str:
    if not dt_ini_0000 or len(dt_ini_0000) < 6:
        return "00/0000"
    return f"{dt_ini_0000[2:4]}/{dt_ini_0000[4:]}"
