# Guía para Crear Motores Fiscales en NEXORUX ERP

Esta guía explica cómo crear un nuevo motor fiscal para integrar con la arquitectura multi-motor del NEXORUX ERP.

## Arquitectura

```
NEXORUX ERP
    ↓
FiscalCore (Servicio central)
    ↓
IFiscalEngine (Interfaz abstracta)
    ↓
Tu Nuevo Motor
    ↓
Autoridad Fiscal Externa
```

## Requisitos Previos

1. **Conocimiento del API fiscal**: Entender la documentación técnica de la autoridad fiscal
2. **Stack Python**: Familiaridad con FastAPI, asyncio, Pydantic
3. **Formatos de datos**: XML, JSON, SOAP, REST según corresponda
4. **Seguridad**: Certificados digitales, firmas, autenticación

## Paso 1: Crear la Clase del Motor

Crea un nuevo archivo en `backend/app/services/fiscal/engines/`:

```python
# backend/app/services/fiscal/engines/tu_motor.py
import structlog
from typing import Dict, Any
from datetime import date

from app.services.fiscal.engines.base import (
    IFiscalEngine,
    FiscalEngineError,
    ValidationError,
    DocumentNotFoundError,
    TransmissionError
)
from app.services.fiscal.models import (
    FiscalDocumentResponse,
    FiscalEngineCapabilities
)

logger = structlog.get_logger(__name__)


class TuMotorFiscal(IFiscalEngine):
    """
    Implementación del motor fiscal para [Tu Autoridad Fiscal].
    
    Descripción breve de qué hace este motor y para qué autoridad fiscal sirve.
    """
    
    def __init__(self, environment: str = "testing"):
        """
        Inicializa el motor fiscal.
        
        Args:
            environment: Entorno (testing, production, etc.)
        """
        self.environment = environment
        logger.info("tu_motor_fiscal_initialized", environment=environment)
    
    @property
    def engine_info(self) -> FiscalEngineCapabilities:
        """Retorna información sobre las capacidades del motor."""
        return FiscalEngineCapabilities(
            engine_id="tu_motor_id",  # ID único del motor
            engine_name="Nombre de Tu Motor",
            country="XX",  # Código de país (ISO 3166-1 alpha-2)
            fiscal_authority="Nombre Autoridad Fiscal",
            version="1.0",
            supports_electronic_invoice=True,  # ¿Soporta facturación electrónica?
            supports_credit_note=True,  # ¿Soporta notas de crédito?
            supports_debit_note=True,  # ¿Soporta notas de débito?
            supports_contingency=False,  # ¿Soporta contingencia?
            supports_cancellation=False,  # ¿Soporta cancelación directa?
            supports_query_status=True,  # ¿Soporta consulta de estado?
            supported_document_types=[
                # Lista de tipos de documentos soportados
                "invoice",
                "credit_note",
                "debit_note"
            ]
        )
    
    async def validate_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Valida un documento según las reglas de tu autoridad fiscal.
        
        Args:
            document_data: Datos del documento en formato normalizado
            
        Returns:
            FiscalDocumentResponse con resultado de validación
        """
        logger.info("tu_motor_validate_document", document_type=document_data.get("document_type"))
        
        validation_errors = []
        
        # Implementar validaciones específicas de tu autoridad
        company = document_data.get("company", {})
        if not company.get("rut"):
            validation_errors.append("Company RUT is required")
        
        # Agregar más validaciones según requerimientos de tu autoridad
        
        is_valid = len(validation_errors) == 0
        
        return FiscalDocumentResponse(
            success=is_valid,
            validation_errors=validation_errors if not is_valid else None,
            status="valid" if is_valid else "invalid",
            engine_used="tu_motor_id",
            operation="validate"
        )
    
    async def issue_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Emite un documento fiscal.
        
        Este método debe:
        1. Convertir el documento normalizado al formato específico de tu autoridad
        2. Generar el archivo según especificación (XML, JSON, etc.)
        3. Aplicar firma digital si corresponde
        4. Validar el documento generado
        5. Retornar el documento listo para envío
        
        Args:
            document_data: Datos del documento en formato normalizado
            
        Returns:
            FiscalDocumentResponse con el documento emitido
        """
        logger.info("tu_motor_issue_document", document_type=document_data.get("document_type"))
        
        # Validar primero
        validation = await self.validate_document(document_data)
        if not validation.success:
            raise ValidationError(
                f"Document validation failed: {validation.validation_errors}",
                validation_errors=validation.validation_errors
            )
        
        # 1. Convertir a formato específico de tu autoridad
        # 2. Generar archivo (XML, JSON, etc.)
        # 3. Aplicar firma digital si corresponde
        # 4. Validar documento generado
        
        # Ejemplo de generación (ajustar según tu autoridad)
        generated_file = self._generate_fiscal_file(document_data)
        
        logger.info("tu_motor_issue_document_success")
        
        return FiscalDocumentResponse(
            success=True,
            document_type=document_data.get("document_type"),
            series=document_data.get("series"),
            number=document_data.get("number"),
            generated_xml=generated_file,  # XML generado
            signed_xml=generated_file,     # XML firmado (si aplica)
            status="ready_to_send",
            engine_used="tu_motor_id",
            operation="issue"
        )
    
    async def send_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Envía un documento fiscal a la autoridad.
        
        Args:
            document_data: Datos del documento incluyendo archivo generado
            
        Returns:
            FiscalDocumentResponse con respuesta de la autoridad
        """
        logger.info("tu_motor_send_document")
        
        # 1. Obtener archivo generado
        generated_file = document_data.get("signed_xml") or document_data.get("generated_xml")
        
        # 2. Enviar a autoridad fiscal (SOAP, REST, etc.)
        response = await self._send_to_authority(generated_file)
        
        # 3. Procesar respuesta
        is_accepted = self._process_response(response)
        
        logger.info("tu_motor_send_document_success", accepted=is_accepted)
        
        return FiscalDocumentResponse(
            success=is_accepted,
            status="accepted" if is_accepted else "rejected",
            engine_response=response,
            engine_used="tu_motor_id",
            operation="send"
        )
    
    async def query_status(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Consulta el estado de un documento en la autoridad.
        
        Args:
            document_data: Datos para identificar el documento
            
        Returns:
            FiscalDocumentResponse con estado del documento
        """
        logger.info("tu_motor_query_status")
        
        # 1. Preparar parámetros de consulta
        # 2. Consultar a autoridad
        # 3. Procesar respuesta
        
        response = await self._query_authority_status(document_data)
        
        return FiscalDocumentResponse(
            success=True,
            engine_response=response,
            engine_used="tu_motor_id",
            operation="query"
        )
    
    async def cancel_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Cancela un documento fiscal.
        
        Si tu autoridad no soporta cancelación directa, lanza FiscalEngineError.
        
        Args:
            document_data: Datos del documento a cancelar
            
        Returns:
            FiscalDocumentResponse con resultado de cancelación
        """
        logger.warning("tu_motor_cancel_document_not_implemented")
        raise FiscalEngineError(
            "Cancellation not implemented for this fiscal authority. "
            "Use credit notes instead."
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la conectividad con el servicio fiscal.
        
        Returns:
            Dict con información de salud del servicio
        """
        logger.info("tu_motor_health_check")
        
        try:
            # Intentar conectar con el servicio
            # Si la conexión es exitosa:
            return {
                "healthy": True,
                "environment": self.environment,
                "endpoint": "https://api.tu-autoridad.fiscal",
                "engine_id": "tu_motor_id",
                "message": "Service is reachable"
            }
        except Exception as e:
            logger.error("tu_motor_health_check_failed", error=str(e))
            return {
                "healthy": False,
                "environment": self.environment,
                "engine_id": "tu_motor_id",
                "error": str(e)
            }
    
    # Métodos auxiliares privados
    
    def _generate_fiscal_file(self, document_data: Dict[str, Any]) -> str:
        """Genera el archivo fiscal según especificación de tu autoridad."""
        # Implementar generación específica
        pass
    
    async def _send_to_authority(self, file_content: str) -> Dict[str, Any]:
        """Envía el archivo a la autoridad fiscal."""
        # Implementar envío específico (SOAP, REST, etc.)
        pass
    
    def _process_response(self, response: Dict[str, Any]) -> bool:
        """Procesa la respuesta de la autoridad."""
        # Implementar procesamiento específico
        pass
    
    async def _query_authority_status(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta el estado a la autoridad."""
        # Implementar consulta específica
        pass
```

## Paso 2: Registrar el Motor

Agrega tu motor al registro en `backend/app/services/fiscal/engines/initialization.py`:

```python
from app.services.fiscal.engines.tu_motor import TuMotorFiscal

def initialize_fiscal_engines():
    registry = get_fiscal_engine_registry()
    
    # ... motores existentes ...
    
    # Registrar tu nuevo motor
    try:
        tu_motor = TuMotorFiscal(environment="testing")
        registry.register_engine("tu_motor_id", tu_motor)
        logger.info("tu_motor_registered")
    except Exception as e:
        logger.error("failed_to_register_tu_motor", error=str(e))
```

## Paso 3: Exportar el Motor

Agrega tu motor a `backend/app/services/fiscal/engines/__init__.py`:

```python
from app.services.fiscal.engines.tu_motor import TuMotorFiscal

__all__ = [
    # ... otros motores ...
    "TuMotorFiscal",
]
```

## Paso 4: Configurar en Tenant

Para usar tu motor, configura el tenant en la base de datos:

```sql
UPDATE tenant 
SET fiscal_engine_id = 'tu_motor_id',
    fiscal_config = '{"environment": "production"}'
WHERE id = 'tu-tenant-id';
```

## Paso 5: Crear Pruebas

Crea pruebas para tu motor en `backend/tests/test_tu_motor.py`:

```python
import pytest
from app.services.fiscal.engines.tu_motor import TuMotorFiscal

class TestTuMotorFiscal:
    """Pruebas para TuMotorFiscal."""
    
    @pytest.fixture
    def motor(self):
        return TuMotorFiscal(environment="testing")
    
    def test_engine_info(self, motor):
        """Test que engine_info retorna capacidades correctas."""
        info = motor.engine_info
        assert info.engine_id == "tu_motor_id"
        assert info.country == "XX"
    
    @pytest.mark.asyncio
    async def test_validate_document(self, motor):
        """Test validación de documentos."""
        document_data = {
            "document_type": "invoice",
            "company": {"rut": "123456789012", "legal_name": "Test"},
            "items": [{"description": "Item", "quantity": 1, "unit_price": 100}],
            "total": 100
        }
        
        response = await motor.validate_document(document_data)
        assert response.success is True
    
    # Agregar más pruebas según tu implementación
```

## Ejemplos de Referencia

### Motor DGI Uruguay
- Ubicación: `backend/app/services/fiscal/engines/dgi_uruguay.py`
- Características: XML CFE, firma X.509, SOAP, validación XSD
- Referencia: Útil para motores que usan XML y SOAP

### Motor Mock
- Ubicación: `backend/app/services/fiscal/engines/mock_engine.py`
- Características: JSON, en memoria, para testing
- Referencia: Útil como template inicial

## Consideraciones Importantes

### Seguridad
- **Certificados**: Manejar certificados digitales de forma segura
- **Secretos**: Nunca hardcodear credenciales
- **Validación**: Validar todas las entradas y salidas

### Error Handling
- **Excepciones específicas**: Usar excepciones del base module
- **Logging**: Registrar todos los errores y operaciones importantes
- **Reintentos**: Implementar lógica de reintentos para transacciones

### Performance
- **Async**: Usar async/await para operaciones I/O
- **Caching**: Considerar caché para consultas frecuentes
- **Batching**: Procesar documentos en lotes cuando sea posible

### Testing
- **Unit tests**: Probar cada método individualmente
- **Integration tests**: Probar con servicios de testing de la autoridad
- **Mock tests**: Usar mocks para testing sin dependencias externas

## Troubleshooting

### Problema: Motor no se registra
**Solución**: Verificar que `initialize_fiscal_engines()` se llame durante el inicio de la app.

### Problema: Validación falla
**Solución**: Revisar que los datos de entrada cumplan con el formato `FiscalDocumentData`.

### Problema: Error de conexión
**Solución**: Verificar configuración de red, certificados y credenciales.

### Problema: Respuesta no reconocida
**Solución**: Implementar parsing robusto para diferentes formatos de respuesta.

## Soporte

Para questions o problemas:
1. Revisa el código de motores existentes como referencia
2. Consulta la documentación de IFiscalEngine
3. Revisa las pruebas de motores existentes
4. Contacta al equipo de desarrollo

## Checklist

- [ ] Implementar todos los métodos de IFiscalEngine
- [ ] Registrar el motor en initialization.py
- [ ] Exportar en __init__.py
- [ ] Crear pruebas unitarias
- [ ] Crear pruebas de integración
- [ ] Documentar configuración requerida
- [ ] Probar en ambiente de testing
- [ ] Validar con autoridad fiscal (sandbox)
- [ ] Actualizar documentación del proyecto