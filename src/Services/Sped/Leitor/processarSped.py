import asyncio
from ..Leitor.leitorService import LeitorService
from src.Services.Sped.Pos.spedPosProcessamento import PosProcessamentoService

class ProcessadorSped:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id

    async def executar(self, caminho_arquivo: str):
        try:
            leitor = LeitorService(self.empresa_id, self.session)
            leitor.executar(caminho_arquivo)

            self.session.commit()
            print("[INFO] Leitura e salvamento dos dados concluído com sucesso.")

            pos = PosProcessamentoService(self.session, self.empresa_id)
            await pos.executar()

            print("[INFO] Pós-processamento concluído.")
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"[ERRO] Falha no processamento do SPED: {str(e)}")