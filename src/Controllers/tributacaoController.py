from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional

from sqlalchemy import update, select, func

from src.Config.Database.db import SessionLocal
from src.Services.Sped.Pos.Etapas.tributacaoService import TributacaoService
from src.Services.Planilhas.planilhaService import importar_planilha_tributacao
from src.Models.tributacaoModel import CadastroTributacao
from src.Utils.aliquota import formatarAliquota
from src.Services.Planilhas.planilhaService import categoria_por_aliquota


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
        CORRIGIDO: Salva as alíquotas editadas pelo usuário no banco de dados
        Propaga a alíquota para TODOS os registros com mesmo produto+NCM (resolve duplicatas)
        """
        atualizados = 0
        grupos_processados = set()
        
        print(f"[DEBUG] Salvando {len(edits)} alíquotas para empresa {empresa_id}")
        
        try:
            with SessionLocal() as db:
                for edit in edits:
                    item_id = edit.get("id")
                    aliquota = edit.get("aliquota")
                    categoria_fiscal = edit.get("categoriaFiscal")
                    
                    print(f"[DEBUG] Processando ID {item_id}: aliquota='{aliquota}', categoria='{categoria_fiscal}'")
                    
                    # CORREÇÃO: Busca o produto+NCM do ID para propagar para duplicatas
                    row = db.execute(
                        select(CadastroTributacao.produto, CadastroTributacao.ncm)
                        .where(
                            CadastroTributacao.id == item_id,
                            CadastroTributacao.empresa_id == empresa_id,
                        )
                    ).one_or_none()

                    if not row:
                        print(f"[DEBUG] ERRO: ID {item_id} não encontrado")
                        continue

                    produto_ref = (row[0] or "").strip()
                    ncm_ref = (row[1] or "").strip()
                    
                    # Evita processar o mesmo grupo várias vezes
                    grupo_key = (produto_ref, ncm_ref)
                    if grupo_key in grupos_processados:
                        print(f"[DEBUG] Grupo (produto='{produto_ref}', ncm='{ncm_ref}') já processado")
                        continue
                    
                    grupos_processados.add(grupo_key)
                    print(f"[DEBUG] Propagando grupo (produto='{produto_ref}', ncm='{ncm_ref}')")

                    # CORREÇÃO: Atualiza TODOS os registros com mesmo produto+NCM (usar string direta)
                    resultado = db.execute(
                        update(CadastroTributacao)
                        .where(CadastroTributacao.empresa_id == empresa_id)
                        .where(func.trim(CadastroTributacao.produto) == produto_ref)
                        .where(func.trim(CadastroTributacao.ncm) == ncm_ref)
                        .values(
                            aliquota=aliquota,
                            categoriaFiscal=categoria_fiscal
                        )
                    )
                    
                    if resultado.rowcount > 0:
                        atualizados += resultado.rowcount
                        print(f"[DEBUG] Grupo atualizado: {resultado.rowcount} registros")
                    else:
                        print(f"[DEBUG] AVISO: Nenhum registro encontrado para o grupo")
                
                # Confirma as alterações
                db.commit()
                print(f"[DEBUG] Commit executado - {atualizados} registros atualizados total")

            # OPCIONAL: Atualiza imediatamente a c170_clone para que sumam da tela
            try:
                from src.Services.Sped.Pos.Etapas.Calculo.calculoService import CalculoService
                with SessionLocal() as db2:
                    calc_svc = CalculoService(db2)
                    calc_svc.atualizar_aliquota_da_clone(empresa_id)
                    print("[DEBUG] Alíquotas propagadas para c170_clone")
            except Exception as e:
                print(f"[DEBUG] Erro ao atualizar clone (não crítico): {e}")

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