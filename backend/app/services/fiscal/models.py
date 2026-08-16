"""
Modelos fiscales normalizados para la arquitectura multi-motor.

Estos modelos son independientes del proveedor fiscal específico y sirven
como contrato entre el ERP y los motores fiscales.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime


class FiscalDocumentItem(BaseModel):
    """Item de línea en un documento fiscal normalizado."""
    
    description: str = Field(..., description="Descripción del item")
    quantity: Decimal = Field(..., gt=0, description="Cantidad")
    unit_price: Decimal = Field(..., gt=0, description="Precio unitario")
    discount: Optional[Decimal] = Field(default=Decimal("0"), ge=0, description="Descuento por línea")
    tax_amount: Optional[Decimal] = Field(default=Decimal("0"), ge=0, description="Monto de impuesto")
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, description="Tasa de impuesto (ej: 22.000 para IVA básico)")
    
    # Metadatos adicionales para motores específicos
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos específicos del motor")


class FiscalCustomer(BaseModel):
    """Cliente/Receptor normalizado para documentos fiscales."""
    
    rut: Optional[str] = Field(default=None, description="Identificación fiscal (RUT, CUIT, etc.)")
    legal_name: Optional[str] = Field(default=None, description="Razón social")
    address: Optional[str] = Field(default=None, description="Dirección")
    city: Optional[str] = Field(default=None, description="Ciudad")
    department: Optional[str] = Field(default=None, description="Departamento/Provincia")
    email: Optional[str] = Field(default=None, description="Correo electrónico")
    phone: Optional[str] = Field(default=None, description="Teléfono")
    
    # Tipo de documento fiscal según el país
    document_type: Optional[str] = Field(default=None, description="Tipo de documento (RUT, CUIT, etc.)")
    
    # Metadatos adicionales
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos específicos del motor")


class FiscalCompany(BaseModel):
    """Empresa/Emisor normalizado para documentos fiscales."""
    
    rut: str = Field(..., description="Identificación fiscal del emisor")
    legal_name: str = Field(..., description="Razón social")
    trade_name: Optional[str] = Field(default=None, description="Nombre comercial")
    business_activity: Optional[str] = Field(default=None, description="Actividad económica/Giro")
    address: Optional[str] = Field(default=None, description="Dirección fiscal")
    city: Optional[str] = Field(default=None, description="Ciudad")
    department: Optional[str] = Field(default=None, description="Departamento/Provincia")
    email: Optional[str] = Field(default=None, description="Correo electrónico")
    phone: Optional[str] = Field(default=None, description="Teléfono")
    
    # Datos específicos para configuración fiscal
    fiscal_address: Optional[str] = Field(default=None, description="Dirección fiscal específica")
    branch_code: Optional[int] = Field(default=None, description="Código de sucursal")
    
    # Metadatos adicionales
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos específicos del motor")


class ReferenceDocument(BaseModel):
    """Documento de referencia para notas de crédito/débito."""
    
    document_type: str = Field(..., description="Tipo de documento referenciado")
    series: str = Field(..., description="Serie del documento")
    number: str = Field(..., description="Número del documento")
    cfe_number: Optional[str] = Field(default=None, description="Número completo (serie+número)")
    issue_date: date = Field(..., description="Fecha de emisión")
    reason: Optional[str] = Field(default=None, description="Motivo de la referencia")
    
    # Metadatos adicionales
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos específicos del motor")


class FiscalDocumentData(BaseModel):
    """
    Modelo de documento fiscal normalizado.
    
    Este modelo es independiente del proveedor fiscal y sirve como contrato
    entre el ERP y los motores fiscales implementados.
    """
    
    # Identificación del documento
    document_type: str = Field(..., description="Tipo de documento (invoice, credit_note, debit_note)")
    series: str = Field(..., description="Serie del documento")
    number: str = Field(..., description="Número del documento")
    issue_date: date = Field(..., description="Fecha de emisión")
    
    # Partes involucradas
    company: FiscalCompany = Field(..., description="Datos del emisor")
    customer: Optional[FiscalCustomer] = Field(default=None, description="Datos del receptor")
    
    # Items y montos
    items: List[FiscalDocumentItem] = Field(..., min_items=1, description="Items del documento")
    currency: str = Field(default="UYU", description="Código de moneda (ISO 4217)")
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0, description="Tipo de cambio")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal neto")
    tax_total: Decimal = Field(..., ge=0, description="Total de impuestos")
    discount_total: Decimal = Field(default=Decimal("0"), ge=0, description="Total descuentos")
    total: Decimal = Field(..., ge=0, description="Total a pagar")
    
    # Metadatos fiscales
    payment_method: int = Field(default=1, description="Método de pago")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Notas adicionales")
    reference_document: Optional[ReferenceDocument] = Field(default=None, description="Documento de referencia")
    
    # Configuración específica del motor
    engine_config: Optional[Dict[str, Any]] = Field(default=None, description="Configuración específica del motor fiscal")
    
    # Metadatos generales
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos adicionales")
    
    # Identificadores del sistema
    invoice_id: Optional[str] = Field(default=None, description="ID de la factura en el ERP")
    tenant_id: Optional[str] = Field(default=None, description="ID del tenant")
    company_id: Optional[str] = Field(default=None, description="ID de la compañía en el ERP")


class FiscalDocumentResponse(BaseModel):
    """Respuesta normalizada de operaciones fiscales."""
    
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    document_id: Optional[str] = Field(default=None, description="ID del documento fiscal generado")
    document_type: Optional[str] = Field(default=None, description="Tipo de documento")
    series: Optional[str] = Field(default=None, description="Serie del documento")
    number: Optional[str] = Field(default=None, description="Número del documento")
    
    # Respuesta específica del motor
    engine_response: Optional[Dict[str, Any]] = Field(default=None, description="Respuesta cruda del motor fiscal")
    
    # Datos generados
    generated_xml: Optional[str] = Field(default=None, description="XML generado (si aplica)")
    signed_xml: Optional[str] = Field(default=None, description="XML firmado (si aplica)")
    
    # Estado y validación
    status: Optional[str] = Field(default=None, description="Estado del documento")
    validation_errors: Optional[List[str]] = Field(default=None, description="Errores de validación")
    
    # Metadatos
    engine_used: Optional[str] = Field(default=None, description="ID del motor utilizado")
    operation: Optional[str] = Field(default=None, description="Operación realizada")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la operación")
    
    # Errores
    error_code: Optional[str] = Field(default=None, description="Código de error (si aplica)")
    error_message: Optional[str] = Field(default=None, description="Mensaje de error (si aplica)")


class FiscalEngineCapabilities(BaseModel):
    """Capacidades de un motor fiscal."""
    
    engine_id: str = Field(..., description="ID único del motor")
    engine_name: str = Field(..., description="Nombre del motor")
    country: str = Field(..., description="Código de país (ISO 3166-1 alpha-2)")
    fiscal_authority: str = Field(..., description="Autoridad fiscal")
    version: str = Field(..., description="Versión del motor")
    
    # Capacidades soportadas
    supports_electronic_invoice: bool = Field(default=False, description="Soporta facturación electrónica")
    supports_credit_note: bool = Field(default=False, description="Soporta notas de crédito")
    supports_debit_note: bool = Field(default=False, description="Soporta notas de débito")
    supports_contingency: bool = Field(default=False, description="Soporta contingencia")
    supports_cancellation: bool = Field(default=False, description="Soporta cancelación")
    supports_query_status: bool = Field(default=False, description="Soporta consulta de estado")
    
    # Tipos de documentos soportados
    supported_document_types: List[str] = Field(default_factory=list, description="Tipos de documentos soportados")
    
    # Metadatos adicionales
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadatos adicionales del motor")