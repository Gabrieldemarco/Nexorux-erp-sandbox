# Evidencia DGI — Nexorux ERP

Documentación oficial, XSD y artefactos de prueba descargados de DGI.

## Archivos en este directorio

| Archivo / carpeta | Tipo | Estado |
|-------------------|------|--------|
| `Formato_CFE_v25-2.pdf` | Especificación normativa (PDF) | **Presente** (copiado desde `docs/`) |
| `xsd/CFEDGI.xsd` | Esquema XSD oficial (entrada) | **Presente** (paquete XSDs_FE v1.44.2) |
| `xsd/CFEType.xsd` + dependencias | Esquemas relacionados | **Presente** |
| `XSDs_FE_V1.44.2.zip` | Archivo fuente descargado | **Presente** |

## PDF vs XSD

- **PDF** (`Formato_CFE_v25-2.pdf`): describe campos, reglas y formatos. Es referencia para desarrollo.
- **XSD** (`xsd/CFEDGI.xsd`): es lo que usa el validador automático en `xsd_validator.py`.

Ambos son necesarios: el PDF para entender la norma, el XSD para validar el XML generado.

## Cómo actualizar los XSD

1. Ir a [Documentos de interés eFactura](https://www.efactura.dgi.gub.uy/principal/ampliacion_de_contenido/documentos-de-interes)
2. Descargar el ZIP más reciente de **XSDs_FE** (ej. `XSDs_FE_V1.44.2.zip`)
3. Extraer todos los `.xsd` en `evidence/xsd/` (mantener juntos por los `schemaLocation`)
4. Verificar con:

```bash
cd backend
.venv311\Scripts\python.exe scripts/dgi_eprueba_test.py --dry-run
```

## Nota sobre namespace

El `xml_builder.py` genera XML con namespace oficial `http://cfe.dgi.gub.uy`,
estructura `eFact`/`eTck`, y atributo `version="1.0"`.
La validación XSD completa se ejecuta **después de firmar** (el esquema exige `ds:Signature`).

Campos que requieren datos reales de DGI antes de producción:
- `CAEData` (CAE_ID, rango DNro/HNro, FecVenc)
- `CdgDGISucur` (código de sucursal DGI)

## Registro de versiones

Ver `../versions/CHANGELOG.md`.
