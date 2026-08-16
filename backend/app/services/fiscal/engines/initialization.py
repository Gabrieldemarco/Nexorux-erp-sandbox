"""
Inicialización del registro de motores fiscales.

Este módulo se encarga de registrar los motores fiscales disponibles
al iniciar la aplicación.
"""

from app.services.fiscal.engines.registry import get_fiscal_engine_registry
from app.services.fiscal.engines.dgi_uruguay import DGIUruguayEngine
import structlog

logger = structlog.get_logger(__name__)


def initialize_fiscal_engines():
    """
    Inicializa el registro de motores fiscales con los motores disponibles.
    
    Esta función debe llamarse durante el inicio de la aplicación para
    registrar todos los motores fiscales disponibles.
    """
    registry = get_fiscal_engine_registry()
    
    # Registrar motor DGI Uruguay
    try:
        dgi_engine = DGIUruguayEngine(environment="testing")
        registry.register_engine("dgi_uruguay", dgi_engine)
        logger.info("dgi_uruguay_engine_registered")
    except Exception as e:
        logger.error("failed_to_register_dgi_uruguay_engine", error=str(e))
    
    # En el futuro, registrar otros motores aquí:
    # registry.register_engine("partner_uruguay", PartnerUruguayEngine())
    # registry.register_engine("afip_argentina", AFIPArgentinaEngine())
    
    logger.info("fiscal_engines_initialized", engines_count=len(registry.list_engines()))


def auto_initialize():
    """
    Inicialización automática que se ejecuta al importar el módulo.
    
    Esta función permite que los motores se registren automáticamente
    cuando se importa el módulo fiscal.
    """
    try:
        initialize_fiscal_engines()
    except Exception as e:
        logger.warning("auto_initialization_failed", error=str(e))


# Ejecutar inicialización automática al importar
auto_initialize()