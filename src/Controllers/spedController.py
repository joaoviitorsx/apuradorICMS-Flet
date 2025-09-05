from ..Services.Sped.Leitor.processarSpedService import ProcessadorSped
from ..Services.Sped.Leitor.validarRegistro import ValidadorPeriodoService
from src.Utils.sanitizacao import calcularPeriodo
from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService
from src.Services.Aliquotas.aliquotaPoupService import AliquotaPoupService

class SpedController:
    def __init__(self, session):
        self.session = session

    async def processarSped(self, caminhos_arquivos: list[str], empresa_id: int, forcar: bool = False) -> dict:
        validador = ValidadorPeriodoService(self.session, empresa_id)

        try:
            # 1. Obter períodos por arquivo
            periodos_por_arquivo = self._extrairPeriodosArquivos(validador, caminhos_arquivos)
            if "erro" in periodos_por_arquivo:
                return periodos_por_arquivo

            periodos_unicos = list(set(periodos_por_arquivo.values()))

            # 2. Verificar se já existem períodos processados
            periodos_existentes = [p for p in periodos_unicos if validador.periodoJaProcessado(p)]

            if periodos_existentes and not forcar:
                return {
                    "status": "existe",
                    "periodos": periodos_existentes,
                    "mensagem": f"Já existem dados ativos para os períodos: {', '.join(periodos_existentes)}. Deseja sobrescrever todos?"
                }

            # 3. Apagar registros antigos (soft delete)
            for periodo in set(periodos_existentes):
                validador.aplicarSoftDelete(periodo)
            self.session.commit()

            # 4. Processar arquivos
            processador = ProcessadorSped(self.session, empresa_id)
            await processador.executar(caminhos_arquivos)

            # 5. Pós-processamento (pré-alíquota)
            pos = PosProcessamentoService(self.session, empresa_id)
            resultado_pre = await pos.executarPre()
            print(f"[DEBUG] Resultado do pré-processamento de alíquotas: {resultado_pre}")

            if resultado_pre["status"] == "pendente_aliquota":
                print("[AVISO] Alíquotas pendentes. Aguardando preenchimento.")
                dados_pendentes = AliquotaPoupService(self.session).listarFaltantes(empresa_id)
                return {
                    "status": "pendente_aliquota",
                    "mensagem": "Existem produtos sem alíquota. Preencha antes de continuar.",
                    "empresa_id": empresa_id,
                    "periodos": periodos_unicos,
                    "dados": dados_pendentes,
                    "etapa_pos": resultado_pre.get("etapa_pos")
                }

            # 6. Pós-processamento final
            await pos.executarPos()

            return {
                "status": "ok",
                "mensagem": f"SPED processado com sucesso para os períodos: {', '.join(periodos_unicos)}.",
                "periodos": periodos_unicos
            }

        except Exception as e:
            self.session.rollback()
            return {"status": "erro", "mensagem": f"Erro durante o processamento: {str(e)}"}            

    def _extrairPeriodosArquivos(self, validador, caminhos: list[str]) -> dict:
        periodos = {}
        for caminho in caminhos:
            dt_ini = validador.extrairDataInicial(caminho)
            if not dt_ini:
                return {
                    "erro": True,
                    "status": "erro",
                    "mensagem": f"Registro |0000| não encontrado ou incompleto no arquivo {caminho}."
                }
            periodo = calcularPeriodo(dt_ini)
            periodos[caminho] = periodo
        return periodos
