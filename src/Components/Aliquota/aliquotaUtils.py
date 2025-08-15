import re
from typing import List, Dict

VALID_TOKENS = {"ST", "ISENTO", "PAUTA"}
VALID_NUM_RE = re.compile(r"^(100([.,]0{1,2})?%?|[0-9]{1,2}([.,][0-9]{1,2})?%?)$")

def eh_valida(aliq: str) -> bool:
    s = (aliq or "").strip().upper()
    return s in VALID_TOKENS or bool(VALID_NUM_RE.fullmatch(s)) or s == ""


def stats(dados: List[Dict], valores: Dict[int, str]):
    total = len(dados)
    preenchidos = sum(1 for it in dados if (valores.get(int(it["id"])) or "").strip())
    invalidos = sum(
        1
        for it in dados
        if (valores.get(int(it["id"])) or "").strip()
        and not eh_valida(valores[int(it["id"])])
    )
    pendentes = total - preenchidos
    return total, preenchidos, pendentes, invalidos


def aplicar_filtro(dados: List[Dict], texto: str) -> List[Dict]:
    texto = (texto or "").strip().lower()
    if not texto:
        return list(dados)
    return [
        it
        for it in dados
        if texto in (it.get("produto") or "").lower()
        or texto in (it.get("codigo") or "").lower()
        or texto in (it.get("ncm") or "").lower()
    ]
