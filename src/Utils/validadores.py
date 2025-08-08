import re

def removedorCaracteres(valor: str) -> str:
    return re.sub(r'\D', '', valor)

def validarCnpj(cnpj: str) -> bool:
    cnpj = removedorCaracteres(cnpj)
    return len(cnpj) == 14 and cnpj.isdigit()

def formatarCnpj(value):
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) <= 2:
            return digits
        elif len(digits) <= 5:
            return f"{digits[:2]}.{digits[2:]}"
        elif len(digits) <= 8:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
        elif len(digits) <= 12:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:]}"
        else:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
        
def validateCnpj(cnpj):
        digits = ''.join(filter(str.isdigit, cnpj))
        return len(digits) == 14

def formatador(valor):
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def formatarValor(value):
        cleaned = ''.join(c for c in value if c.isdigit() or c == ',')
        parts = cleaned.split(',')
        if len(parts) > 2:
            return parts[0] + ',' + ''.join(parts[1:])
        if len(parts) == 2 and len(parts[1]) > 2:
            return parts[0] + ',' + parts[1][:2]
        return cleaned

def formatarValorInput(value):
        cleaned = ''.join(c for c in value if c.isdigit() or c in '.,')
        
        if ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts) > 2:
                cleaned = parts[0] + ',' + ''.join(parts[1:])
            if len(parts) == 2 and len(parts[1]) > 2:
                cleaned = parts[0] + ',' + parts[1][:2]
        
        return cleaned

