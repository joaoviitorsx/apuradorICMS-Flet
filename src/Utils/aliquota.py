import re

def tratarAliquota(aliquota: str) -> str:
    if aliquota is None:
        return ""
    s = str(aliquota).strip().upper()
    if not s:
        return ""
    if s in {"ST", "ISENTO", "PAUTA", "SUBSTITUICAO"}:
        return s
    s = s.replace('%', '').replace(',', '.')
    try:
        valor = float(s)

        if valor < 1:
            valor *= 100
            
        if 0.01 <= valor <= 100.00:
            return f"{valor:.2f}"
        else:
            return ""
    except ValueError:
        return ""
    
def categoriaAliquota(aliquota):
        if not aliquota:
            return 'regraGeral'
        aliquota_str = str(aliquota).upper().strip()
        aliquota_str = re.sub(r'[^\d.,A-Z]', '', aliquota_str)
        tokens_st = {"ISENTO", "ST", "SUBSTITUICAO", "PAUTA", "0", "0,00", "0.00"}
        if aliquota_str in tokens_st:
            return 'ST'
        try:
            aliquota_normalizada = aliquota_str.replace(',', '.')
            aliquota_num = float(aliquota_normalizada)
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
        
def contarFaltantes(dados: list, valores: dict) -> int:
    faltantes = 0
    for d in dados:
        if not valores.get(int(d["id"])):
            faltantes += 1
    return faltantes    