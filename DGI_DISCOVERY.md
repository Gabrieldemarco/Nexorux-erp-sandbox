# DGI Discovery

## Objetivo

Crear el primer entregable de FASE 0: `DGI_DISCOVERY.md`. Este documento registra el estado actual de investigación sobre la normativa oficial uruguaya de facturación electrónica, CFE y DGI, sin inventar requisitos ni asumir aprobaciones.

## Estado actual del proyecto

- Backend disponible: modelado inicial de `Tenant` y `Company`, configuración básica de FastAPI, endpoints `health`, `tenants` y `companies` con lógica de TODO.
- Frontend disponible: React + TypeScript + Vite con enrutamiento básico a `Dashboard`, `Tenants` y `Companies`.
- No existe aún implementación real de CFE, motor fiscal, DGI adapter, firma digital, auditoría fiscal ni flujo transaccional de documentos.
- La configuración de DGI en `backend/app/core/config.py` es una base de entorno, pero no hay integración con servicios fiscales.

## Fuentes oficiales encontradas

1. DGI portal principal
   - FUENTE OFICIAL: DGI / www.gub.uy
   - DOCUMENTO: Portal institucional de la Dirección General Impositiva
   - VERSIÓN: N/A
   - FECHA DE CONSULTA: 2026-08-11
   - URL: https://www.gub.uy/dgi

2. eFactura DGI
   - FUENTE OFICIAL: Portal de factura electrónica DGI
   - DOCUMENTO: Página de servicios de factura electrónica
   - VERSIÓN: N/A
   - FECHA DE CONSULTA: 2026-08-11
   - URL: http://www.efactura.dgi.gub.uy/

> Nota: los portales oficiales de DGI disponibles públicamente son la fuente primaria identificada. La documentación técnica específica de facturación electrónica, formatos CFE y servicios web suele requerir acceso directo a secciones especializadas o autenticadas del portal de DGI/eFactura.

## Información confirmada hasta ahora

- Existe un marco institucional para la Dirección General Impositiva en Uruguay.
- Existe un portal específico de factura electrónica (`efactura.dgi.gub.uy`).
- La normativa vigente debe investigarse en el portal oficial y en los documentos técnicos específicos provistos por DGI.
- No se dispone de documentación técnica específica de DGI CFE en el repositorio actual.

## Información pendiente de verificación

Los siguientes puntos necesitan confirmación directa en la documentación oficial de DGI antes de cualquier implementación fiscal:

- Tipos de CFE requeridos para emisión y recepción.
- Formatos XML vigentes y XSD oficiales.
- Endpoints de servicios DGI para sandbox/pruebas, homologación/certificación y producción.
- Requisitos exactos de certificados digitales y firma electrónica.
- Reglas de numeración, series y correlativas fiscales.
- Procedimiento oficial de homologación y certificación ante DGI.
- Regímenes de contingencia y mecanismos alternativos en caso de indisponibilidad DGI.
- Reglas de impuestos específicas, códigos tributarios y validaciones exigidas.
- Mensajes de respuesta oficiales y códigos de rechazo.
- Requisitos de seguridad aplicables a integración fiscal.
- Requisitos legales sobre almacenamiento de documentos fiscales y retención.

## Resultados de investigación preliminar

### 1. Marco actual de facturación electrónica

- Existe un servicio oficial de factura electrónica de DGI.
- El proyecto debe diseñarse para operar con tres ambientes separados: pruebas, homologación/certificación y producción.
- No se puede afirmar que el sistema está homologado o aprobado hasta completar el proceso oficial.

### 2. CFE aplicables

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: tipos de documentos fiscales, códigos y campos obligatorios.

### 3. Documentación técnica vigente

- FUENTE OFICIAL: portal DGI principal y portal eFactura.
- DOCUMENTO: no disponible públicamente en detalle desde la consulta actual.
- VERSIÓN: desconocida.

### 4. Formatos

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: estructuras XML, XSD y esquemas de CFE.

### 5. Servicios

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: rutas de envío, consulta de estado y autenticación.

### 6. Certificados

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: mecanismo de certificados digitales, almacenamiento seguro, y gestión de claves privadas.

### 7. Firma

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: formato de firma digital, algoritmos admitidos y puntos de firma en los CFE.

### 8. Ambiente de pruebas

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: URL y requisitos de credenciales para sandbox/pruebas.

### 9. Ambiente de homologación/certificación

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: URL y proceso de homologación.

### 10. Ambiente de producción

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: URL y requisitos de puesta en producción.

### 11. Requisitos de seguridad

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: controles específicos exigidos por DGI.

### 12. Procedimientos

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: procedimiento oficial de solicitud de homologación y pruebas con DGI.

### 13. Validaciones

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: validaciones de estructura, datos y cálculos fiscales.

### 14. Mensajes de respuesta

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: códigos de aceptación, rechazo, contingencia y errores.

### 15. Requisitos para proveedor/software

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: requisitos legales y técnicos para proveedores de software.

### 16. Requisitos para pasar a producción

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: checklist oficial de producción.

### 17. Documentación obligatoria

- POR VERIFICAR EN DOCUMENTACIÓN OFICIAL DGI: documentos que debe conservar el contribuyente y el software.

### 18. Información que necesita confirmación

- Cualquier dato relacionado con CFE, DGI o facturación electrónica que no se encuentre en la documentación oficial.

## Arquitectura fiscal propuesta

El diseño fiscal debe mantenerse desacoplado del ERP central:

- ERP Core
  - Fiscal Engine
    - CFE Engine
      - DGI Adapter
        - Servicios oficiales de DGI

Aspectos clave:

- Separar la generación de documento fiscal de la emisión al servicio DGI.
- Mantener el motor fiscal independiente de ventas, compras e inventario.
- Implementar un adaptador DGI intercambiable para sandbox/homologación/producción.
- Usar un state machine fiscal con estados transaccionales claros.
- Asegurar multitenancy en cada capa fiscal.

## Riesgos técnicos

1. Acceso público insuficiente a la documentación oficial de DGI.
2. Cambios en la normativa de facturación electrónica durante el desarrollo.
3. Requisitos de certificados y firma digital desconocidos.
4. Falta de un entorno de homologación DGI accesible para pruebas.
5. No disponer de datos de prueba oficiales que reproduzcan rechazos reales.
6. Implementar reglas fiscales sin verificación formal.

## Plan de homologación / certificación

1. Identificar y descargar documentación oficial de DGI/eFactura.
2. Registrar versiones, URLs y fechas de consulta.
3. Mapear requisitos fiscales en `DGI_COMPLIANCE_MATRIX.md`.
4. Diseñar arquitectura y modelo de datos fiscal.
5. Implementar motor fiscal mínimo y adaptador DGI.
6. Implementar pruebas de CFE con casos oficiales.
7. Solicitar acceso a ambiente de homologación DGI.
8. Ejecutar pruebas de homologación según el proceso oficial.
9. Documentar resultados y evidencias en `compliance/dgi/`.
10. No declarar homologación hasta recibir la aprobación oficial.

## Plan de desarrollo por fases

Basado en el MASTER PROMPT, la secuencia propuesta es:

- FASE 0: DGI Discovery
- FASE 1: Arquitectura
- FASE 2: Base de datos
- FASE 3: Autenticación y multitenancy
- FASE 4: Clientes/proveedores/productos
- FASE 5: Ventas
- FASE 6: Compras
- FASE 7: Inventario
- FASE 8: Caja
- FASE 9: Motor fiscal
- FASE 10: CFE
- FASE 11: Integración DGI
- FASE 12: Auditoría
- FASE 13: Reportes
- FASE 14: Testing
- FASE 15: Security hardening
- FASE 16: Staging
- FASE 17: Pruebas de homologación/certificación
- FASE 18: Producción

## Próximo paso recomendado

1. Obtener la documentación técnica completa de DGI/eFactura.
2. Crear el `DGI_COMPLIANCE_MATRIX.md` basado en requisitos oficiales.
3. Diseñar el modelo de datos fiscal sin asumir reglas específicas aún.
