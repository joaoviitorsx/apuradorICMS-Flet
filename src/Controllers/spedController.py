from ..Services.Sped.Leitor.processarSped import ProcessadorSped
from ..Services.Sped.Leitor.validarRegistro import ValidadorPeriodoService
from src.Utils.sanitizacao import calcularPeriodo
from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService
from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService

class SpedController:
    def __init__(self, session):
        self.session = session

    async def processarSped(self, caminho_arquivo: str, empresa_id: int, forcar: bool = False) -> dict:
        try:
            validador = ValidadorPeriodoService(self.session, empresa_id)
            dt_ini = validador.extrairDataInicial(caminho_arquivo)
            if not dt_ini:
                return {"status": "erro", "mensagem": "Registro |0000| não encontrado ou incompleto."}

            periodo = calcularPeriodo(dt_ini)

            if validador.periodoJaProcessado(periodo):
                if not forcar:
                    return {
                        "status": "existe",
                        "periodo": periodo,
                        "mensagem": f"Já existem dados ativos para o período {periodo}. Deseja sobrescrever?"
                    }

                validador.aplicarSoftDelete(periodo)
                self.session.commit()

            processador = ProcessadorSped(self.session, empresa_id)
            await processador.executar(caminho_arquivo)

            pos_processamento = PosProcessamentoService(self.session, empresa_id)
            pendente_aliquota = await pos_processamento.executar()
            if pendente_aliquota:
                dados_pendentes = AliquotaPoupService(self.session).listarFaltantes(empresa_id)

                return {
                    "status": "pendente_aliquota",
                    "mensagem": "Existem produtos sem alíquota. Preencha antes de continuar.",
                    "empresa_id": empresa_id,
                    "periodo": periodo,
                    "dados": dados_pendentes
                }

            return {
                "status": "ok",
                "mensagem": f"SPED processado com sucesso para o período {periodo}.",
                "periodo": periodo
            }

        except Exception as e:
            self.session.rollback()
            return {"status": "erro", "mensagem": f"Erro durante o processamento: {str(e)}"}