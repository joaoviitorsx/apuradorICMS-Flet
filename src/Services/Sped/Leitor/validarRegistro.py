from Models import _0150Model
from src.Models import _0000Model, _0200Model,c100Model, c170Model, c170novaModel, c170cloneModel

class ValidadorPeriodoService:
    def __init__(self, session, empresa_id):
        self.session = session
        self.empresa_id = empresa_id

        self.modelos_por_periodo = [_0000Model.Registro0000,_0150Model.Registro0150,_0200Model.Registro0200,c100Model.C100,c170Model.C170,c170novaModel.C170Nova,c170cloneModel.C170Clone]
            
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
        
    def periodoJaProcessado(self, periodo: str) -> bool:
        for modelo in self.modelos_por_periodo:
            existe = self.session.query(modelo).filter_by(
                empresa_id=self.empresa_id,
                periodo=periodo,
                is_active=True
            ).first()
            if existe:
                return True
        return False

    def aplicarSoftDelete(self, periodo: str):
        for modelo in self.modelos_por_periodo:
            self.session.query(modelo).filter_by(
                empresa_id=self.empresa_id,
                periodo=periodo,
                is_active=True
            ).update({modelo.is_active: False})
        print(f"[INFO] Soft delete aplicado para o período {periodo}.")