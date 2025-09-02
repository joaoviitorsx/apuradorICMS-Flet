from src.Controllers.empresasController import cadastrarEmpresa
from src.Components.notificao import notificacao

def validarCadastro(input_cnpj, page):
    cnpj = ''.join(filter(str.isdigit, input_cnpj.current.value.strip()))

    if len(cnpj) != 14 or not cnpj.isdigit():
        notificacao(page, "Erro", "CNPJ inválido. Deve conter 14 dígitos numéricos.", tipo="erro")
        return

    resultado = cadastrarEmpresa(cnpj)

    if resultado["status"] == "ok":
        page.update()
        notificacao(page, "Sucesso", "Empresa cadastrada com sucesso!", tipo="sucesso")
        page.go("/empresa")
    else:
        notificacao(page, "Erro", resultado["mensagem"], tipo="erro")

def voltar(page):
    page.go("/empresa")
