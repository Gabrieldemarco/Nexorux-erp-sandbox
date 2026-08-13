# Requisitos DGI / Facturación Electrónica

> Última actualización: 2026-08-12
> Matriz detallada: [`DGI_COMPLIANCE_MATRIX.md`](../../DGI_COMPLIANCE_MATRIX.md)

## Fuentes oficiales

| # | Fuente | URL | Consulta |
|---|--------|-----|----------|
| 1 | Portal DGI | https://www.gub.uy/dgi | 2026-08-12 |
| 2 | Portal eFactura | http://www.efactura.dgi.gub.uy/ | 2026-08-12 |
| 3 | Documentos de interés | https://www.efactura.dgi.gub.uy/principal/ampliacion_de_contenido/documentos-de-interes | 2026-08-12 |
| 4 | XSD publicados (noticia) | https://www.gub.uy/direccion-general-impositiva/comunicacion/noticias/se-publican-formatos-xsd | 2026-08-12 |
| 5 | Estándar intercambio emisores | https://www.efactura.dgi.gub.uy/principal/ampliacion_de_contenido/-25465 | 2026-08-12 |

## Requisitos técnicos

### 1. Tipos de CFE

| Código | Tipo | Implementado | Verificado DGI |
|--------|------|--------------|----------------|
| 111 | e-Factura | Sí | Pendiente |
| 101 | e-Ticket | Sí | Pendiente |
| 112 | Nota de Crédito e-Factura | Sí | Pendiente |
| 113 | Nota de Débito e-Factura | Sí | Pendiente |
| 102 | Nota de Crédito e-Ticket | Sí | Pendiente |
| 103 | Nota de Débito e-Ticket | Sí | Pendiente |
| 211 | e-Factura Contingencia | Sí | Pendiente |
| 212 | Nota de Crédito e-Factura Contingencia | Sí | Pendiente |
| 213 | Nota de Débito e-Factura Contingencia | Sí | Pendiente |
| 201 | e-Ticket Contingencia | Sí | Pendiente |
| 202 | Nota de Crédito e-Ticket Contingencia | Sí | Pendiente |
| 203 | Nota de Débito e-Ticket Contingencia | Sí | Pendiente |

### 2. Formato XML / XSD

- Namespace: `http://cfe.dgi.gub.uy`
- XSD entrada: `compliance/dgi/evidence/xsd/CFEDGI.xsd` (paquete XSDs_FE v1.44.2)
- Validación estructural: `app/services/fiscal/xsd_validator.py`
- Validación XSD completa: se ejecuta **después de firmar** (el esquema exige `ds:Signature`)

### 3. Ambientes y endpoints

| Ambiente | URL WS | Implementado | Probado |
|----------|--------|--------------|---------|
| testing (ePrueba) | `https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba` | Sí | No |
| homologacion | `https://efactura.dgi.gub.uy:6443/eHomologacion/ws_ehomologacion` | Sí | No |
| produccion | `https://efactura.dgi.gub.uy:6443/eFactura/ws_efactura` | Sí | No |

### 4. Certificados y firma

- Certificado X.509 de CA autorizada
- Firma digital XML antes del envío
- Almacenamiento seguro de clave privada
- Estado: implementado en código, no verificado con DGI

### 5. Flujo de emisión

1. Crear factura en ERP
2. Crear documento fiscal vinculado a factura
3. Emitir (generar XML + firmar) — validación XSD antes de firmar
4. Enviar a DGI (SOAP, ambiente configurado)
5. Consultar estado
6. Reintentar si rechazado

### 6. Seguridad

- TLS 1.2+ para comunicaciones DGI
- WS-Security en envelope SOAP
- Separación de ambientes y credenciales
- Rate limiting y RBAC en API

### 7. Homologación

- Proceso oficial ante DGI: **no iniciado**
- Script de prueba ePrueba: `backend/scripts/dgi_eprueba_test.py`
- Evidencias de prueba: `compliance/dgi/test-cases/`

## Configuración del sistema

Variables en `backend/.env`:

```env
DGI_ENVIRONMENT=testing
CFE_XSD_PATH=../compliance/dgi/evidence/xsd/CFEDGI.xsd
CFE_XSD_VALIDATION_REQUIRED=false   # true en homologación/producción
```

## Pendiente de confirmación oficial

- Estructura XML exacta vs XSD real (requiere descarga y prueba)
- Códigos de respuesta DGI y mapeo de estados
- Procedimiento de homologación paso a paso
- Requisitos de retención de documentos fiscales
- Registro de proveedor habilitado

## Regla anti-alucinación

Ningún requisito se marca como VERIFICADO hasta tener evidencia en `compliance/dgi/evidence/` o respuesta real de ePrueba/homologación.
