from typing import Callable, Optional, Iterable, Dict, Any, List

from src.Config.Database.db import SessionLocal
from src.Services.Sped.Pos.Etapas.fornecedorService import FornecedorService
from src.Services.Sped.Pos.Etapas.c170NovaService import C170NovaService
from src.Services.Sped.Pos.Etapas.cloneService import CloneService
from src.Services.Tributacao.cadastroService import TributacaoService
from src.Services.Sped.Pos.Etapas.Calculo.calculoService import CalculoService


class PosProcessamentoService:
    def posProcessar():
        print("[INFO] Iniciando pós-processamento do SPED...")
        return