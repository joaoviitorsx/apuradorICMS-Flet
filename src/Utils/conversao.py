import re

def Conversor(valor_str):
    """
    Converte textos variados (com %, vírgula, ponto, 'ISENTO', 'ST', etc.) em float.
    Retorna 0.0 quando não for número.
    Ex.: '1,23' → 1.23 ; '2%' → 2.0 ; 'ISENTO' → 0.0
    """
    try:
        if valor_str is None:
            return 0.0

        valor = str(valor_str).strip().upper()

        if valor in {"ISENTO", "ST", "N/A", "PAUTA", ""}:
            return 0.0

        valor = re.sub(r"[^0-9.,]", "", valor)
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        return round(float(valor), 4)
    except (ValueError, TypeError):
        return 0.0
