"""
Motores fiscales para la arquitectura multi-motor.

Este paquete contiene las implementaciones de motores fiscales para diferentes
países y autoridades fiscales.
"""

from app.services.fiscal.engines.base import (
    IFiscalEngine,
    FiscalEngineError,
    ValidationError,
    DocumentNotFoundError,
    TransmissionError
)
from app.services.fiscal.engines.registry import (
    FiscalEngineRegistry,
    get_fiscal_engine_registry,
    reset_fiscal_engine_registry
)
from app.services.fiscal.engines.dgi_uruguay import DGIUruguayEngine
from app.services.fiscal.engines.mock_engine import MockFiscalEngine

__all__ = [
    "IFiscalEngine",
    "FiscalEngineError",
    "ValidationError",
    "DocumentNotFoundError",
    "TransmissionError",
    "FiscalEngineRegistry",
    "get_fiscal_engine_registry",
    "reset_fiscal_engine_registry",
    "DGIUruguayEngine",
    "MockFiscalEngine",
]