import re
from typing import Optional

# Limites para truncamento de campos antes de gravar no banco
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

def limpar_aliquota(valor):
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
    """
    Normaliza unidade:
    - Se vier número, assume 'UN';
    - Se vier 'KG10' → 'KG';
    - Limita a 3 caracteres quando extrapolar.
    """
    if not valor:
        return "UN"
    s = str(valor)

    if re.match(r"^\d+[,\.]\d+$", s) or re.match(r"^\d+$", s):
        return "UN"

    m = re.match(r"^([A-Za-z]+)(\d+)", s)
    if m:
        return m.group(1)

    return s[:3] if len(s) > 3 else s

def corrigir_cst_icms(valor):
    """
    Normaliza CST para 2 dígitos numéricos quando possível.
    """
    if not valor:
        return "00"
    s = str(valor).strip().replace(",", ".")
    if s.replace(".", "").isdigit():
        try:
            return str(int(float(s))).zfill(2)[:2]
        except ValueError:
            return "00"
    return s[:2]

def corrigir_cfop(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    
    s = re.sub(r"\D", "", str(valor))
    if len(s) > 4:
        s = s[:4]
    if len(s) < 4:
        s = s.zfill(4)
    return s

def corrigir_ind_mov(valor):
    if not valor:
        return "0"
    s = str(valor)
    return s[:1] if len(s) > 1 else s

def validar_estrutura_c170(dados: list) -> bool:
    """
    Valida estrutura mínima de um C170 já transformado para inserção:
    - Pelo menos 45-46 colunas (estrutura esperada);
    - Checa campos cruciais: período, filial, num_doc.
    """
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

def sanitizar_campo(campo, valor):
    regras = {
        "cod_item": lambda v: truncar(v, 60),
        "descr_item": lambda v: truncar(v, 255),
        "descr_compl": lambda v: truncar(v, 255),
        "unid_inv": corrigirUnidade,
        "unid": corrigirUnidade,
        "cod_part": lambda v: truncar(v, 60),
        "nome": lambda v: truncar(v, 100),
        "ind_mov": corrigir_ind_mov,
        "cod_mod": lambda v: str(v).zfill(2)[:2] if v is not None else "00",
        "cst_icms": corrigir_cst_icms,
        "cfop": corrigir_cfop,
        "cod_nat": lambda v: truncar(v, 11),
        "cod_cta": lambda v: truncar(v, 255),
        "reg": lambda v: truncar(v, 4),
        "vl_item": _num_str,
        "vl_desc": _num_str,
        "vl_merc": _num_str,
        "aliq_icms": _num_str,
        "aliq_ipi": _num_str,
        "aliq_pis": _num_str,
        "aliq_cofins": _num_str,
    }
    try:
        return regras.get(campo, lambda v: v)(valor)
    except Exception:
        return valor

def sanitizar_registro(registro_dict: dict) -> dict:
    return {campo: sanitizar_campo(campo, valor) for campo, valor in registro_dict.items()}

def calcular_periodo(dt_ini_0000: str) -> str:
    """
    Converte AAAAMMDD (ou AAAAMM) em MM/AAAA para chaves de período.
    """
    if not dt_ini_0000 or len(dt_ini_0000) < 6:
        return "00/0000"
    return f"{dt_ini_0000[2:4]}/{dt_ini_0000[4:]}"
