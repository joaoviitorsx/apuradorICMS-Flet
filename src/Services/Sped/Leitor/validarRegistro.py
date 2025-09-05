from pathlib import Path
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.Models import _0000Model, _0150Model, _0200Model, c100Model, c170Model, c170novaModel, c170cloneModel
    
class ValidadorPeriodoRepository:
    def __init__(self, session):
        self.session = session

        self.modelos = [
            _0000Model.Registro0000,
            _0150Model.Registro0150,
            _0200Model.Registro0200,
            c100Model.C100,
            c170Model.C170,
            c170novaModel.C170Nova,
            c170cloneModel.C170Clone
        ]

    def softDelete(self, periodo: str, empresa_id: int):
        for modelo in self.modelos:
            table_name = modelo.__tablename__ 
            query = text(f"""
                UPDATE `{table_name}`
                SET is_active = 0
                WHERE empresa_id = :empresa_id
                  AND periodo = :periodo
                  AND is_active = 1
            """)
            self.session.execute(query, {
                "empresa_id": empresa_id,
                "periodo": periodo
            })

    def verificarRegistroPeriodoAtivo(self, periodo: str, empresa_id: int) -> bool:
        for modelo in self.modelos:
            table_name = modelo.__tablename__
            query = text(f"""
                SELECT 1
                FROM `{table_name}`
                WHERE empresa_id = :empresa_id
                  AND periodo = :periodo
                  AND is_active = 1
                LIMIT 1
            """)
            resultado = self.session.execute(query, {
                "empresa_id": empresa_id,
                "periodo": periodo
            }).first()

            if resultado:
                return True
        return False

class ValidadorPeriodoService:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id
        self.repository = ValidadorPeriodoRepository(session)

        self.modelos_por_periodo = [
            _0000Model.Registro0000,
            _0150Model.Registro0150,
            _0200Model.Registro0200,
            c100Model.C100,
            c170Model.C170,
            c170novaModel.C170Nova,
            c170cloneModel.C170Clone
        ]

    def validarArquivos(self, caminhos: list[str], aplicar_soft_delete=True, max_workers=4) -> dict[str, str | None]:
        resultados = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.extrairDataInicial, caminho): caminho
                for caminho in caminhos
            }

            for future in as_completed(futures):
                caminho, data = future.result()
                resultados[caminho] = data

                if data:
                    if self.repository.verificarRegistroPeriodoAtivo(data, self.empresa_id):
                        if aplicar_soft_delete:
                            self.repository.softDelete(data, self.empresa_id)
                            print(f"[INFO] Soft delete aplicado para período {data} do arquivo {Path(caminho).name}")
                        else:
                            print(f"[INFO] Período {data} já processado no arquivo {Path(caminho).name}")
                    else:
                        print(f"[OK] Período {data} ainda não processado para {Path(caminho).name}")
                else:
                    print(f"[AVISO] Não foi possível extrair data do arquivo: {Path(caminho).name}")

        return resultados

    def extrairDataInicial(self, caminho_arquivo: str) -> str | None:
        for encoding in ["utf-8", "latin1"]:
            try:
                with open(caminho_arquivo, 'r', encoding=encoding) as f:
                    for linha in f:
                        if linha.startswith("|0000|"):
                            partes = linha.strip().split("|")[1:-1]
                            return partes[3] if len(partes) > 3 else None
                break
            except Exception:
                continue
        return None
    
    # @staticmethod
    # def extrairDataInicial(caminho_arquivo: str) -> tuple[str, str | None]:
    #     for encoding in ["utf-8", "latin1"]:
    #         try:
    #             with open(caminho_arquivo, 'r', encoding=encoding) as f:
    #                 for linha in f:
    #                     if linha.startswith("|0000|"):
    #                         partes = linha.strip().split("|")[1:-1]
    #                         return caminho_arquivo, partes[3] if len(partes) > 3 else None
    #             break
    #         except Exception:
    #             continue
    #     return caminho_arquivo, None

    def periodoJaProcessado(self, periodo: str) -> bool:
        return self.repository.verificarRegistroPeriodoAtivo(periodo, self.empresa_id)

    def aplicarSoftDelete(self, periodo: str):
        self.repository.softDelete(periodo, self.empresa_id)
        print(f"[INFO] Soft delete aplicado para o período {periodo}.")
