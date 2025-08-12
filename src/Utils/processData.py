from typing import Iterable

def process_data(data: str) -> str:
    """
    Ajusta o fluxo C100→C170:
    - Mantém |0000|, |0150|, |0200| como vieram;
    - Para cada |C170|, injeta o id_c100 (nº do C100 atual) logo após o código do registro,
      se um C100 tiver sido visto anteriormente.
    Retorna uma única string com linhas separadas por \n.
    """
    linhas = data.strip().splitlines()
    resultado: list[str] = []
    id_c100_atual: str | None = None

    for i, linha in enumerate(linhas):
        linha = linha.strip()
        if not linha.startswith("|"):
            continue

        partes = linha.split("|")
        if len(partes) < 2:
            # linha malformada: ignora de forma defensiva
            continue

        tipo_registro = partes[1]

        if tipo_registro == "C100":
            # normalmente o campo 3 é o num_doc; preservamos o comportamento do legado
            id_c100_atual = partes[2] if len(partes) > 2 else None
            resultado.append(linha)

        elif tipo_registro == "C170":
            if id_c100_atual:
                nova_linha = "|".join(partes[:2] + [id_c100_atual] + partes[2:])
                resultado.append(nova_linha)
            else:
                # sem C100 anterior — mantém como está
                resultado.append(linha)

        elif tipo_registro in ("0000", "0150", "0200"):
            resultado.append(linha)

        else:
            # outros registros: ignorar (não usados na fase 1)
            pass

    return "\n".join(resultado)
