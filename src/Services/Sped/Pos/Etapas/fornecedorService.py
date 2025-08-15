import asyncio
from typing import Iterable, Dict, Tuple, Optional

from sqlalchemy import select, update, exists, literal, and_, func, or_
from sqlalchemy.orm import Session

from src.Models.fornecedorModel import CadastroFornecedor
from src.Models._0150Mode import Registro0150
from src.Utils.cnpj import processarCnpjs

SIM = "Sim"
NAO = "Não"

def _sn(flag: Optional[bool]) -> str:
    return SIM if flag else NAO

class FornecedorService:
    def __init__(self, db: Session):
        self.db = db

    # 1) Garante fornecedores na base (espelha comportamento do legado)
    def sync_from_0150(self, empresa_id: int) -> int:
        # 0150 que possuem CNPJ e ainda não existem em cadastro_fornecedores
        subq_existe = (
            select(literal(1))
            .select_from(CadastroFornecedor)
            .where(
                CadastroFornecedor.empresa_id == empresa_id,
                func.trim(CadastroFornecedor.cod_part) == func.trim(Registro0150.cod_part)
            )
            .limit(1)
        )
        q = (
            select(Registro0150.cod_part, Registro0150.nome, Registro0150.cnpj)
            .where(
                Registro0150.empresa_id == empresa_id,
                Registro0150.cnpj.is_not(None),
                Registro0150.cnpj != "",
                ~exists(subq_existe)
            )
        )
        rows = self.db.execute(q).all()

        if not rows:
            return 0

        novos = [
            CadastroFornecedor(
                empresa_id=empresa_id,
                cod_part=cod_part,
                nome=nome or "",
                cnpj=cnpj or "",
                uf="",
                cnae="",
                decreto="",
                simples=""
            )
            for (cod_part, nome, cnpj) in rows
        ]
        self.db.add_all(novos)
        self.db.commit()
        return len(novos)

    # 2) Quem está pendente de completar dados?
    def _pendentes(self, empresa_id: int) -> list[str]:
        q = (
            select(func.distinct(CadastroFornecedor.cnpj))
            .where(
                CadastroFornecedor.empresa_id == empresa_id,
                CadastroFornecedor.cnpj.is_not(None),
                CadastroFornecedor.cnpj != "",
                # falta qualquer um destes:
                or_(
                    CadastroFornecedor.cnae.is_(None),  CadastroFornecedor.cnae == "",
                    CadastroFornecedor.decreto.is_(None), CadastroFornecedor.decreto == "",
                    CadastroFornecedor.uf.is_(None),     CadastroFornecedor.uf == "",
                    CadastroFornecedor.simples.is_(None),CadastroFornecedor.simples == "",
                ),
            )
        )
        return [r[0] for r in self.db.execute(q).all()]

    # 3) Atualização assíncrona (para quem chamar de flows async)
    async def atualizar_fornecedores_async(self, empresa_id: int, lote: int = 100) -> None:
        # espelha fluxo do legado: primeiro garante inserção vinda do 0150
        self.sync_from_0150(empresa_id)

        cnpjs = self._pendentes(empresa_id)
        if not cnpjs:
            return

        # consulta API em paralelo (usa cache TTL do utilitário)
        resultados: Dict[str, Tuple[str, str, str, bool, bool]] = await processarCnpjs(cnpjs)

        for i in range(0, len(cnpjs), lote):
            fatia = cnpjs[i:i + lote]
            for cnpj in fatia:
                dados = resultados.get(cnpj)
                if not dados:
                    continue
                # util atual: (razao, cnae, uf, simples_bool, decreto_bool)
                _razao, cnae, uf, simples_b, decreto_b = dados
                self.db.execute(
                    update(CadastroFornecedor)
                    .where(
                        CadastroFornecedor.empresa_id == empresa_id,
                        CadastroFornecedor.cnpj == cnpj
                    )
                    .values(
                        cnae=cnae or "",
                        decreto=_sn(decreto_b),
                        uf=(uf or "").upper(),
                        simples=_sn(simples_b),
                    )
                )
            self.db.commit()

    # 4) Wrapper síncrono (para jobs/CLI). Evita estourar event loop ativo.
    def atualizar_fornecedores(self, empresa_id: int, lote: int = 100) -> None:
        try:
            loop = asyncio.get_running_loop()  # já estou num contexto async?
            # se sim, delega a quem chamou
            raise RuntimeError("Use atualizar_fornecedores_async() em contexto assíncrono.")
        except RuntimeError:
            asyncio.run(self.atualizar_fornecedores_async(empresa_id, lote))
