from ..Services.Sped.Leitor.processarSpedService import ProcessadorSped
from ..Services.Sped.Leitor.validarRegistro import ValidadorPeriodoService
from src.Utils.sanitizacao import calcularPeriodo
from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService
from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService

class SpedController:
    def __init__(self, session):
        self.session = session

    async def processarSped(self, caminhos_arquivos: list[str], empresa_id: int, forcar: bool = False) -> dict:
        try:
            periodos = {}
            validador = ValidadorPeriodoService(self.session, empresa_id)
            # 1. Levanta todos os períodos dos arquivos
            for caminho_arquivo in caminhos_arquivos:
                dt_ini = validador.extrairDataInicial(caminho_arquivo)
                if not dt_ini:
                    return {"status": "erro", "mensagem": f"Registro |0000| não encontrado ou incompleto no arquivo {caminho_arquivo}."}
                periodo = calcularPeriodo(dt_ini)
                periodos[caminho_arquivo] = periodo

            # 2. Verifica se algum período já existe
            periodos_existentes = [p for p in periodos.values() if validador.periodoJaProcessado(p)]
            if periodos_existentes and not forcar:
                return {
                    "status": "existe",
                    "periodos": list(set(periodos_existentes)),
                    "mensagem": f"Já existem dados ativos para os períodos: {', '.join(set(periodos_existentes))}. Deseja sobrescrever todos?"
                }

            # 3. Aplica soft delete para todos os períodos existentes
            for p in set(periodos_existentes):
                validador.aplicarSoftDelete(p)
            self.session.commit()

            # 4. Processa todos os arquivos juntos
            processador = ProcessadorSped(self.session, empresa_id)
            await processador.executar(caminhos_arquivos)

            # Pós-processamento igual...
            posProcessamento = PosProcessamentoService(self.session, empresa_id)
            resultadoPos = await posProcessamento.executarPre()

            print(f"[DEBUG] Resultado do pré-processamento de alíquotas: {resultadoPos}")

            if resultadoPos["status"] == "pendente_aliquota":
                dados_pendentes = AliquotaPoupService(self.session).listarFaltantes(empresa_id)
                return {
                    "status": "pendente_aliquota",
                    "mensagem": "Existem produtos sem alíquota. Preencha antes de continuar.",
                    "empresa_id": empresa_id,
                    "periodos": list(set(periodos.values())),
                    "dados": dados_pendentes,
                    "etapa_pos": resultadoPos["etapa_pos"]
                }

            await posProcessamento.executarPos()

            return {
                "status": "ok",
                "mensagem": f"SPED processado com sucesso para os períodos: {', '.join(set(periodos.values()))}.",
                "periodos": list(set(periodos.values()))
            }

        except Exception as e:
            self.session.rollback()
            return {"status": "erro", "mensagem": f"Erro durante o processamento: {str(e)}"}