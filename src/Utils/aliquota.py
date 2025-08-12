def formatarAliquota(aliquota: str) -> str:
    """
    Padroniza alíquota em string percentual:
    - '0.12' → '12.00%'
    - '12'   → '12.00%'
    Mantém valores não-numéricos (ex.: 'ST', 'ISENTO').
    """
    if aliquota is None:
        return ""
    s = str(aliquota).strip()
    if not s:
        return ""
    if s[0].isdigit():
        try:
            return f"{float(s) * 100:.2f}%"
        except ValueError:
            return s
    return s
