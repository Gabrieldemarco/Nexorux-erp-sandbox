"""
Registro de motores fiscales disponibles.

Este componente gestiona el registro y recuperación de motores fiscales,
permitiendo que el sistema soporte múltiples proveedores fiscales de manera dinámica.
"""

import structlog
from typing import Dict, Optional, Type
from app.services.fiscal.engines.base import IFiscalEngine, FiscalEngineError

logger = structlog.get_logger(__name__)


class FiscalEngineRegistry:
    """
    Registro centralizado de motores fiscales.
    
    Este registry permite:
    - Registrar múltiples motores fiscales
    - Recuperar motores por ID
    - Listar motores disponibles con sus capacidades
    - Validar configuración de motores
    """
    
    def __init__(self):
        """Inicializa el registro de motores."""
        self._engines: Dict[str, IFiscalEngine] = {}
        self._engine_classes: Dict[str, Type[IFiscalEngine]] = {}
        logger.info("fiscal_engine_registry_initialized")
    
    def register_engine(
        self, 
        engine_id: str, 
        engine: IFiscalEngine,
        replace: bool = False
    ) -> None:
        """
        Registra una instancia de motor fiscal.
        
        Args:
            engine_id: Identificador único del motor
            engine: Instancia del motor fiscal
            replace: Si True, reemplaza motor existente con mismo ID
            
        Raises:
            FiscalEngineError: Si el ID ya existe y replace=False
        """
        if engine_id in self._engines and not replace:
            raise FiscalEngineError(
                f"Engine '{engine_id}' already registered. Use replace=True to override."
            )
        
        self._engines[engine_id] = engine
        logger.info(
            "fiscal_engine_registered",
            engine_id=engine_id,
            engine_name=engine.engine_info.engine_name,
            replaced=replace
        )
    
    def register_engine_class(
        self, 
        engine_id: str, 
        engine_class: Type[IFiscalEngine],
        replace: bool = False
    ) -> None:
        """
        Registra una clase de motor fiscal para instanciación lazy.
        
        Args:
            engine_id: Identificador único del motor
            engine_class: Clase del motor fiscal (debe heredar de IFiscalEngine)
            replace: Si True, reemplaza clase existente con mismo ID
            
        Raises:
            FiscalEngineError: Si el ID ya existe y replace=False
        """
        if engine_id in self._engine_classes and not replace:
            raise FiscalEngineError(
                f"Engine class '{engine_id}' already registered. Use replace=True to override."
            )
        
        if not issubclass(engine_class, IFiscalEngine):
            raise FiscalEngineError(
                f"Engine class must inherit from IFiscalEngine"
            )
        
        self._engine_classes[engine_id] = engine_class
        logger.info(
            "fiscal_engine_class_registered",
            engine_id=engine_id,
            engine_class=engine_class.__name__,
            replaced=replace
        )
    
    def get_engine(self, engine_id: str) -> IFiscalEngine:
        """
        Obtiene una instancia de motor fiscal por ID.
        
        Primero busca instancias registradas, luego clases registradas.
        Si encuentra una clase, la instancia automáticamente.
        
        Args:
            engine_id: Identificador del motor
            
        Returns:
            Instancia de IFiscalEngine
            
        Raises:
            FiscalEngineError: Si el motor no está registrado
        """
        # Primero buscar instancia registrada
        if engine_id in self._engines:
            return self._engines[engine_id]
        
        # Luego buscar clase registrada y instanciar
        if engine_id in self._engine_classes:
            engine_class = self._engine_classes[engine_id]
            engine_instance = engine_class()
            self._engines[engine_id] = engine_instance
            logger.info(
                "fiscal_engine_instantiated",
                engine_id=engine_id,
                engine_class=engine_class.__name__
            )
            return engine_instance
        
        raise FiscalEngineError(f"Engine '{engine_id}' not found in registry")
    
    def has_engine(self, engine_id: str) -> bool:
        """
        Verifica si un motor está registrado.
        
        Args:
            engine_id: Identificador del motor
            
        Returns:
            bool indicando si el motor existe
        """
        return engine_id in self._engines or engine_id in self._engine_classes
    
    def list_engines(self) -> Dict[str, Dict]:
        """
        Lista todos los motores disponibles con sus capacidades.
        
        Returns:
            Dict mapping engine_id a engine_info
        """
        engines_info = {}
        
        # Instancias registradas
        for engine_id, engine in self._engines.items():
            engines_info[engine_id] = engine.engine_info.model_dump()
        
        # Clases registradas (instanciar temporalmente para obtener info)
        for engine_id, engine_class in self._engine_classes.items():
            if engine_id not in engines_info:
                temp_instance = engine_class()
                engines_info[engine_id] = temp_instance.engine_info.model_dump()
        
        return engines_info
    
    def get_engine_info(self, engine_id: str) -> Optional[Dict]:
        """
        Obtiene información de capacidades de un motor específico.
        
        Args:
            engine_id: Identificador del motor
            
        Returns:
            Dict con capacidades del motor o None si no existe
        """
        try:
            engine = self.get_engine(engine_id)
            return engine.engine_info.model_dump()
        except FiscalEngineError:
            return None
    
    def remove_engine(self, engine_id: str) -> bool:
        """
        Remueve un motor del registro.
        
        Args:
            engine_id: Identificador del motor
            
        Returns:
            bool indicando si se removió correctamente
        """
        removed = False
        
        if engine_id in self._engines:
            del self._engines[engine_id]
            removed = True
            logger.info("fiscal_engine_instance_removed", engine_id=engine_id)
        
        if engine_id in self._engine_classes:
            del self._engine_classes[engine_id]
            removed = True
            logger.info("fiscal_engine_class_removed", engine_id=engine_id)
        
        return removed
    
    def clear(self) -> None:
        """Limpia todos los motores registrados."""
        self._engines.clear()
        self._engine_classes.clear()
        logger.info("fiscal_engine_registry_cleared")
    
    def get_engine_for_country(self, country_code: str) -> Optional[IFiscalEngine]:
        """
        Obtiene un motor fiscal para un país específico.
        
        Args:
            country_code: Código de país (ISO 3166-1 alpha-2)
            
        Returns:
            Primer motor encontrado para el país o None
        """
        for engine_id in list(self._engines.keys()) + list(self._engine_classes.keys()):
            try:
                engine = self.get_engine(engine_id)
                if engine.engine_info.country == country_code:
                    return engine
            except FiscalEngineError:
                continue
        
        return None
    
    def get_engines_for_country(self, country_code: str) -> list:
        """
        Obtiene todos los motores fiscales para un país específico.
        
        Args:
            country_code: Código de país (ISO 3166-1 alpha-2)
            
        Returns:
            Lista de motores para el país
        """
        engines = []
        
        for engine_id in list(self._engines.keys()) + list(self._engine_classes.keys()):
            try:
                engine = self.get_engine(engine_id)
                if engine.engine_info.country == country_code:
                    engines.append(engine)
            except FiscalEngineError:
                continue
        
        return engines


# Instancia global del registro
_global_registry: Optional[FiscalEngineRegistry] = None


def get_fiscal_engine_registry() -> FiscalEngineRegistry:
    """
    Obtiene la instancia global del registro de motores fiscales.
    
    Returns:
        Instancia singleton de FiscalEngineRegistry
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = FiscalEngineRegistry()
    return _global_registry


def reset_fiscal_engine_registry() -> None:
    """Resetea la instancia global del registro (útil para tests)."""
    global _global_registry
    _global_registry = None