# Componentes existentes (compatibilidad hacia atrás)
from app.services.fiscal.cfe_types import CFEType, CFE_TYPE_INFO
from app.services.fiscal.xml_builder import build_cfe_xml
from app.services.fiscal.signer import load_certificate, load_private_key, sign_xml, CertificateError, SigningError
from app.services.fiscal.soap_envelope import build_soap_envelope
from app.services.fiscal.dgi_client import DGIClient, DGIError
from app.services.fiscal.state_machine import FiscalStateMachine, FiscalState, StateTransitionError
from app.services.fiscal.engine import FiscalEngine, FiscalEngineError, FiscalDocumentNotFoundError

# Nuevos componentes de arquitectura multi-motor
from app.services.fiscal.models import (
    FiscalDocumentData,
    FiscalDocumentResponse,
    FiscalDocumentItem,
    FiscalCustomer,
    FiscalCompany,
    ReferenceDocument,
    FiscalEngineCapabilities
)
from app.services.fiscal.engines.base import (
    IFiscalEngine,
    FiscalEngineError as BaseFiscalEngineError,
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
from app.services.fiscal.fiscal_core import FiscalCore, FiscalCoreError

# Inicializar motores fiscales automáticamente
from app.services.fiscal.engines.initialization import initialize_fiscal_engines

__all__ = [
    # Componentes existentes (compatibilidad hacia atrás)
    "CFEType",
    "CFE_TYPE_INFO",
    "build_cfe_xml",
    "load_certificate",
    "load_private_key",
    "sign_xml",
    "CertificateError",
    "SigningError",
    "build_soap_envelope",
    "DGIClient",
    "DGIError",
    "FiscalStateMachine",
    "FiscalState",
    "StateTransitionError",
    "FiscalEngine",
    "FiscalEngineError",
    "FiscalDocumentNotFoundError",
    
    # Nuevos componentes de arquitectura multi-motor
    "FiscalDocumentData",
    "FiscalDocumentResponse",
    "FiscalDocumentItem",
    "FiscalCustomer",
    "FiscalCompany",
    "ReferenceDocument",
    "FiscalEngineCapabilities",
    "IFiscalEngine",
    "BaseFiscalEngineError",
    "ValidationError",
    "DocumentNotFoundError",
    "TransmissionError",
    "FiscalEngineRegistry",
    "get_fiscal_engine_registry",
    "reset_fiscal_engine_registry",
    "DGIUruguayEngine",
    "FiscalCore",
    "FiscalCoreError",
]
