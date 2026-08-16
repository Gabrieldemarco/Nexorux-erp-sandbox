"""
Interfaz base para motores fiscales.

Esta interfaz define el contrato que todos los motores fiscales deben implementar,
permitiendo que el ERP trabaje con diferentes proveedores fiscales de manera agnóstica.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import date

from app.services.fiscal.models import (
    FiscalDocumentData, 
    FiscalDocumentResponse, 
    FiscalEngineCapabilities
)


class FiscalEngineError(Exception):
    """Excepción base para errores de motores fiscales."""
    
    def __init__(self, message: str, engine_id: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.engine_id = engine_id
        self.error_code = error_code


class ValidationError(FiscalEngineError):
    """Excepción para errores de validación de documentos."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []


class DocumentNotFoundError(FiscalEngineError):
    """Excepción cuando un documento no es encontrado en el sistema fiscal."""
    pass


class TransmissionError(FiscalEngineError):
    """Excepción para errores de transmisión con la autoridad fiscal."""
    pass


class IFiscalEngine(ABC):
    """
    Interfaz base para motores fiscales.
    
    Todos los motores fiscales (DGI Uruguay, Partner, AFIP, etc.) deben implementar
    esta interfaz para garantizar compatibilidad con el Fiscal Core.
    """
    
    @abstractmethod
    async def validate_document(
        self, 
        document_data: Dict[str, Any]
    ) -> FiscalDocumentResponse:
        """
        Valida un documento fiscal según las reglas del motor.
        
        Args:
            document_data: Datos del documento en formato normalizado
            
        Returns:
            FiscalDocumentResponse con resultado de validación
            
        Raises:
            ValidationError: Si el documento no cumple las reglas del motor
        """
        pass
    
    @abstractmethod
    async def issue_document(
        self, 
        document_data: Dict[str, Any]
    ) -> FiscalDocumentResponse:
        """
        Emite un documento fiscal (genera XML, firma, etc.).
        
        Este método debe:
        - Convertir el documento normalizado al formato específico del motor
        - Generar el XML según especificación del motor
        - Aplicar firma digital si corresponde
        - Validar el documento generado
        - Retornar el documento listo para envío
        
        Args:
            document_data: Datos del documento en formato normalizado
            
        Returns:
            FiscalDocumentResponse con el documento emitido (XML, firma, etc.)
            
        Raises:
            ValidationError: Si el documento no puede ser emitido
            FiscalEngineError: Si hay error en el proceso de emisión
        """
        pass
    
    @abstractmethod
    async def send_document(
        self, 
        document_data: Dict[str, Any]
    ) -> FiscalDocumentResponse:
        """
        Envía un documento fiscal a la autoridad fiscal.
        
        Args:
            document_data: Datos del documento incluyendo XML firmado
            
        Returns:
            FiscalDocumentResponse con respuesta de la autoridad fiscal
            
        Raises:
            TransmissionError: Si hay error en la transmisión
            DocumentNotFoundError: Si el documento no existe
            FiscalEngineError: Para otros errores del motor
        """
        pass
    
    @abstractmethod
    async def query_status(
        self, 
        document_data: Dict[str, Any]
    ) -> FiscalDocumentResponse:
        """
        Consulta el estado de un documento fiscal en la autoridad.
        
        Args:
            document_data: Datos para identificar el documento (tipo, serie, número, etc.)
            
        Returns:
            FiscalDocumentResponse con estado actual del documento
            
        Raises:
            DocumentNotFoundError: Si el documento no existe
            TransmissionError: Si hay error en la consulta
            FiscalEngineError: Para otros errores del motor
        """
        pass
    
    @abstractmethod
    async def cancel_document(
        self, 
        document_data: Dict[str, Any]
    ) -> FiscalDocumentResponse:
        """
        Cancela un documento fiscal en la autoridad.
        
        Args:
            document_data: Datos del documento a cancelar
            
        Returns:
            FiscalDocumentResponse con resultado de la cancelación
            
        Raises:
            ValidationError: Si el documento no puede ser cancelado
            DocumentNotFoundError: Si el documento no existe
            TransmissionError: Si hay error en la cancelación
            FiscalEngineError: Para otros errores del motor
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la conectividad y estado del servicio fiscal.
        
        Returns:
            Dict con información de salud del motor:
            {
                "healthy": bool,
                "environment": str,
                "endpoint": str,
                "latency_ms": float,
                "error": str (si hay error)
            }
        """
        pass
    
    @property
    @abstractmethod
    def engine_info(self) -> FiscalEngineCapabilities:
        """
        Retorna información sobre las capacidades del motor.
        
        Returns:
            FiscalEngineCapabilities con metadatos del motor
        """
        pass
    
    def get_supported_document_types(self) -> list:
        """
        Retorna lista de tipos de documentos soportados por el motor.
        
        Returns:
            List[str] con tipos de documentos soportados
        """
        return self.engine_info.supported_document_types
    
    def supports_document_type(self, document_type: str) -> bool:
        """
        Verifica si el motor soporta un tipo de documento específico.
        
        Args:
            document_type: Tipo de documento a verificar
            
        Returns:
            bool indicando si el tipo es soportado
        """
        return document_type in self.get_supported_document_types()
    
    def supports_operation(self, operation: str) -> bool:
        """
        Verifica si el motor soporta una operación específica.
        
        Args:
            operation: Operación a verificar (issue, send, query, cancel, etc.)
            
        Returns:
            bool indicando si la operación es soportada
        """
        capabilities = self.engine_info
        
        operation_map = {
            "issue": True,  # Todos los motores deben soportar emisión
            "send": capabilities.supports_electronic_invoice,
            "query": capabilities.supports_query_status,
            "cancel": capabilities.supports_cancellation,
            "credit_note": capabilities.supports_credit_note,
            "debit_note": capabilities.supports_debit_note,
            "contingency": capabilities.supports_contingency,
        }
        
        return operation_map.get(operation, False)