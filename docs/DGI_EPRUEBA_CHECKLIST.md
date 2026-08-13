# Checklist DGI ePrueba (Nexorux)

Objetivo: llegar al **primer envío real** al sandbox ePrueba de DGI.

> El sistema **no está homologado**. ePrueba es prueba técnica, no habilita producción.

---

## Estado actual en código

| Pieza | Estado |
|-------|--------|
| XML CFE + XSD oficial | Listo (tests locales) |
| Firma X.509 | Listo (necesita cert real para DGI) |
| Cliente SOAP → ePrueba | Listo |
| Script readiness | `backend/scripts/dgi_eprueba_test.py` |
| Envío live a DGI | **Bloqueado hasta tener certificado ePrueba** |

Endpoint testing:

`https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba`

---

## Pasos

### 1. Prerrequisitos locales

```bash
cd backend
.venv311\Scripts\python.exe scripts/dgi_eprueba_test.py --dry-run
.venv311\Scripts\python.exe scripts/dgi_eprueba_test.py --dry-run --probe-network
```

Interpretación de `readiness`:

| Valor | Significado |
|-------|-------------|
| `ready_for_live_send` | XSD + cert + red OK → podés emitir y `--send` |
| `ready_except_network_or_skipped` | Falta probe de red o la red está bloqueada |
| `blocked` | Falta XSD y/o certificado |

El reporte JSON queda en `compliance/dgi/test-cases/`.

### 2. Obtener certificado de prueba

1. Gestioná con tu proveedor de firma electrónica / CA habilitada para e-Factura (Abitab, Correo, etc.).
2. Pedí material para ambiente de **prueba / ePrueba** (no el de producción).
3. Exportá:
   - certificado público → `cert.pem`
   - clave privada → `key.pem` (passphrase opcional)

**No subas PEM al git.** Guardalos fuera del repo o en una ruta local ignorada.

### 3. Configurar Nexorux

En `backend/.env`:

```env
DGI_ENVIRONMENT=testing
DGI_CERT_PATH=C:\ruta\segura\cert.pem
DGI_KEY_PATH=C:\ruta\segura\key.pem
# DGI_KEY_PASSWORD=si_aplica
```

Opcional en la tabla `certificate` (UI/API): crear un certificado activo con

```json
{ "cert_path": "...", "key_path": "..." }
```

en `metadata` (el motor de emisión lo usa al **Emitir**).

### 4. Emitir un CFE firmado

1. Creá factura + documento fiscal en la UI (o API).
2. **Emitir** eligiendo el certificado (genera `signed_xml` en `raw_payload`).
3. Anotá el `fiscal_document_id` (UUID).

### 5. Enviar a ePrueba

```bash
cd backend
.venv311\Scripts\python.exe scripts/dgi_eprueba_test.py --send --fiscal-document-id <UUID>
```

O desde la UI: acción **Enviar** del documento fiscal (ambiente `testing`).

### 6. Guardar evidencia

- Copiá el JSON de `compliance/dgi/test-cases/eprueba_send_*.json`
- Anotá código DGI (`Estado` / `Mensaje` / `IdTransaccion`)
- Actualizá `DGI_COMPLIANCE_MATRIX.md` → fila ePrueba a `IN_PROGRESS` / `VERIFIED` según resultado

---

## Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| `certificate` missing | `DGI_CERT_PATH` / `DGI_KEY_PATH` |
| `unreachable` / timeout | Firewall salida al puerto **6443** |
| `no signed_xml` | Falta paso **Emitir** antes de enviar |
| SOAP fault DGI | RUT emisor, CAE/números de prueba, ambiente incorrecto |
| Cert expired | Renovar material ePrueba |

---

## Después de ePrueba OK

1. Homologación (`DGI_ENVIRONMENT=homologacion`)
2. CAE real / rangos de numeración
3. `CFE_XSD_VALIDATION_REQUIRED=true` en no-dev
4. Producción solo con aprobación DGI
