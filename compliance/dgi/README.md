# Compliance / DGI

Artefactos de cumplimiento fiscal para la integración DGI de Nexorux ERP.

## Estructura

```
compliance/dgi/
├── requirements.md      # Requisitos normativos con referencias oficiales
├── evidence/            # XSD, PDFs y documentos descargados de DGI
│   └── README.md        # Instrucciones de descarga del XSD
├── test-cases/          # Reportes JSON de pruebas ePrueba/homologación
└── versions/            # Registro de versiones de documentación DGI
    └── CHANGELOG.md
```

## Documentos relacionados (raíz del proyecto)

- [`DGI_DISCOVERY.md`](../../DGI_DISCOVERY.md) — Investigación inicial
- [`DGI_COMPLIANCE_MATRIX.md`](../../DGI_COMPLIANCE_MATRIX.md) — Matriz de cumplimiento
- [`STATUS.md`](../../STATUS.md) — Estado verificado del proyecto

## Próximos pasos

1. Ejecutar `backend/scripts/dgi_eprueba_test.py --dry-run` (XSD y PDF ya presentes)
2. Obtener certificado de prueba DGI
3. Ejecutar primera prueba real: `--send --fiscal-document-id <uuid>`
4. Solicitar homologación oficial
