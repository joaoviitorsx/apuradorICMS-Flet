from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional

from sqlalchemy import update

from src.Config.Database.db import SessionLocal
from src.Services.pos.tributacaoService import TributacaoService
from src.Services.planilhaService import importar_planilha_tributacao
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.aliquota import formatarAliquota
from src.Services.planilhaService import categoria_por_aliquota


class TributacaoController:
    """
    Controller voltado à gestão de alíquotas na UI (Flet):
      - inserir do 0200 e listar faltantes para abrir o diálogo
      - listar faltantes
      - salvar alíquotas digitadas
      - importar alíquotas por planilha .xlsx
    """

    # ---------- Inserção + listagem para a UI ----------
    @staticmethod
    def preparar_listagem_para_ui(empresa_id: int, limit: int = 300) -> List[Dict]:
        with SessionLocal() as db:
            svc = TributacaoService(db)
            return svc.inserir_do_0200_e_listar_para_ui(empresa_id, limit=limit)

    @staticmethod
    def listar_faltantes(empresa_id: int, limit: int = 300) -> List[Dict]:
        with SessionLocal() as db:
            svc = TributacaoService(db)
            return svc.listar_faltantes(empresa_id, limit=limit)

    # ---------- Salvar edições feitas pelo usuário ----------
    @staticmethod
    def salvar_aliquotas(empresa_id: int, edits: List[Dict]) -> Dict[str, int]:
        """
        Salva as alíquotas editadas pelo usuário no banco de dados
        """
        atualizados = 0
        
        print(f"[DEBUG] Salvando {len(edits)} alíquotas para empresa {empresa_id}")
        
        try:
            with SessionLocal() as db:
                for edit in edits:
                    item_id = edit.get("id")
                    aliquota = edit.get("aliquota")
                    categoria_fiscal = edit.get("categoriaFiscal")
                    
                    print(f"[DEBUG] Atualizando ID {item_id}: aliquota='{aliquota}', categoria='{categoria_fiscal}'")
                    
                    # Executa o update usando SQLAlchemy
                    resultado = db.execute(
                        update(CadastroTributacao)
                        .where(
                            CadastroTributacao.id == item_id,
                            CadastroTributacao.empresa_id == empresa_id
                        )
                        .values(
                            aliquota=aliquota,
                            categoriaFiscal=categoria_fiscal
                        )
                    )
                    
                    if resultado.rowcount > 0:
                        atualizados += 1
                        print(f"[DEBUG] ID {item_id} atualizado com sucesso")
                    else:
                        print(f"[DEBUG] ERRO: ID {item_id} não foi encontrado ou não pertence à empresa {empresa_id}")
                
                # Confirma as alterações
                db.commit()
                print(f"[DEBUG] Commit executado - {atualizados} registros atualizados")

            # Conta quantos itens ainda estão sem alíquota
            with SessionLocal() as db:
                svc = TributacaoService(db)
                restantes = svc.contar_faltantes(empresa_id)
                print(f"[DEBUG] Restam {restantes} itens sem alíquota")

            return {"atualizados": atualizados, "faltantes_restantes": restantes}
            
        except Exception as e:
            print(f"[DEBUG] ERRO ao salvar alíquotas: {e}")
            import traceback
            traceback.print_exc()
            return {"atualizados": 0, "faltantes_restantes": -1, "erro": str(e)}

    # ---------- Importação por planilha (.xlsx) ----------
    @staticmethod
    def cadastrar_tributacao_por_planilha(path_planilha: str, empresa_id: int) -> dict:
        """
        Importa alíquotas por planilha .xlsx (mapeamento feito no Service de planilha).
        Ao final, adiciona 'faltantes_restantes' para a UI decidir se ainda deve abrir o diálogo.
        """
        p = Path(path_planilha)
        if p.suffix.lower() != ".xlsx":
            return {"status": "erro", "mensagem": "O arquivo deve ser um .xlsx"}
        if not p.is_file():
            return {"status": "erro", "mensagem": "Arquivo não encontrado"}

        resultado = importar_planilha_tributacao(str(p), empresa_id)

        # pós-checagem: quantos ainda faltam?
        with SessionLocal() as db:
            faltantes_restantes = TributacaoService(db).contar_faltantes(empresa_id)

        if isinstance(resultado, dict):
            resultado.setdefault("faltantes_restantes", faltantes_restantes)
        else:
            resultado = {"status": "ok", "resultado": resultado, "faltantes_restantes": faltantes_restantes}

        return resultado
