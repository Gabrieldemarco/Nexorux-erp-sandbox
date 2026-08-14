# NEXORUX ERP — Bitácora de construcción (~42 horas)

> Diario de desarrollo intensivo del producto.  
> Fuentes: sesiones Cursor (UTC−3), migraciones Alembic, `STATUS.md`, commits locales.  
> **No incluye secretos** (tokens, app passwords, etc.).

**Ventana aproximada:** ~11 ago 2026 (tarde) → 13 ago 2026 (~18:30 UTC−3)  
**Ritmo:** ~42 horas de trabajo concentrado (no 42 h calendario continuas sin pausas).

---

## Veredicto — cómo venimos

**En una frase:** para ~42 horas, el avance es **excepcional en producto operable**; el freno real ya no es “falta de ERP”, sino **cerrar DGI en vivo y go-live ops**.

| Pregunta | Respuesta |
|----------|-----------|
| ¿Se puede demostrar a un cliente / piloto interno? | **Sí** — caja, stock, facturas, pagos/CC, recovery, marca. |
| ¿Se puede cobrar en caja sin romper? | **Sí** (post-fix RLS en cobro POS). |
| ¿Se puede emitir CFE reales a DGI hoy? | **No** — falta certificado de firma + homologación. |
| ¿Está listo para producción comercial? | **No todavía** (~78% ops; secrets, dominio TLS, backups programados, password demo). |
| ¿El código está “abandonable”? | **No** — hay repo privado, STATUS, handoff, docs, tests base. |
| ¿Vale la pena seguir en este ritmo? | **Sí**, pero el siguiente sprint debe priorizar **material DGI + un drill de deploy**, no más features cosméticas. |

### Nota del veredicto

- **Fortaleza:** en menos de dos días se pasó de shell/listas a un ERP con flujos de negocio reales (POS, proveedor→stock→venta, cuenta corriente). Eso suele llevar semanas en un equipo chico tradicional.
- **Deuda consciente:** FORCE RLS dejó una clase de bugs (`refresh` post-commit) que hay que cazar en más endpoints si aparecen errores raros al guardar.
- **Riesgo #1:** confundir “motor fiscal implementado” con “aprobado por DGI”. El producto **no** está homologado.
- **Riesgo #2:** credenciales demo y cualquier secreto que haya circulado en chat deben rotarse antes de exponer el sistema.
- **Score honestidad (sobre 10):** producto demo **8.5/10** · fiscal vivo **3/10** · producción dura **6/10** · documentación **8/10**.

Estado vivo del día a día: `STATUS.md`. Esta bitácora es **historia**.

---

## Resumen ejecutivo

En ~42 horas se pasó de un esqueleto ERP Uruguay a una aplicación operable día a día:

| Área | Al inicio (aprox.) | Al cierre de esta bitácora |
|------|--------------------|----------------------------|
| Backend | API base + fiscal en código | ~96% — CRUD, stock, Woo MVP, SMTP, RLS endurecido |
| Frontend | Listas / shell limitado (~30%) | ~98% — CRUD, POS kiosk, CC, detalle por fila |
| Fiscal DGI | Código sin validación viva (~30%) | Código + XSD + red ePrueba; **sin envío firmado** (~88% código) |
| Ops / Git | Local | Compose prod, backups, health, **GitHub privado** (~78% prod) |

---

## Día 0 — 11 ago 2026 (T−42 → T−24)

### ~16:00 — Fundación del esquema
- Migración Alembic inicial (`bc221d501185_initial_schema`): tenants, companies, productos, clientes, facturas, ítems, pagos, stock, documentos fiscales, certificados, impuestos, roles/permisos, etc.
- Stack definido: FastAPI + React/Vite + PostgreSQL + Redis/Celery.
- Nombre y foco de producto: **NEXORUX ERP** con CFE Uruguay.

### 16:00–~03:00 (noche) — Bootstrap previo a la sesión larga
- Armado de entorno local (venv 3.11, compose, seeds demo).
- Primera API usable y frontend base (aún lejos del POS/CC actuales).
- *(Detalle fino de cada hora de esta franja no está en el transcript principal; es el “día cero” del repo.)*

---

## Día 1 — 12 ago 2026

### 03:25 — Diagnóstico
- Pedido: leer todos los MD, no mirar el proyecto “así nomás”.
- Foto inicial: backend relativamente maduro; frontend más bien listas; fiscal en código sin certificar.

### 03:31–03:34 — Tests + prioridades
- Arreglo de tests rotos.
- “¿Qué sigue para mejorar?” → priorización.
- Arranque prioridad 1 (“vamos con todo”).
- Nace / se endurece `STATUS.md` como fuente de verdad.

### 03:39–03:52 — Prioridades 2 y 3
- Ejecución prioridad 2 con foco en eficiencia.
- Completar Tenants / Invoices primero (CRUD real, no solo listar).
- Prioridad 3: pista DGI (matriz de cumplimiento, validación XSD, evidencias).

### 04:02–04:20 — Material CFE oficial
- Usuario coloca CFE v25 en `docs/`.
- Integración de evidencias / XSDs al compliance folder.
- Script ePrueba + checklist; cuidado con sintaxis PowerShell (`<uuid>`).

### 04:23–04:41 — Prioridad 4 + infra local
- RLS por tenant (policies ENABLE/FORCE en camino).
- “A ver” / smoke manual.
- Redis no instalado → impacto en lockout/colas.
- Error 500: revisión de comportamiento real (no solo logs).

### 04:51–05:00 — Empuje fiscal en código
- Pedido: “arreglalo todo, dejalo DGI 10 de 10”.
- Interpretación correcta: **máxima calidad del motor + tests + docs**, sin inventar homologación.
- Trabajo en background; pausa humana hasta la tarde.

### 14:11–14:16 — Reencuentro / estado
- “¿Arreglaste todo?” / “fijate en qué condiciones está el proyecto”.
- Retoma UX de facturación real.

### 14:16–14:50 — Primeros dolores de usuario real
- Facturar a consumidor final es incómodo → datos de prueba (1 producto, 1 cliente, 1 factura, 1 proveedor).
- Registro de usuario falla (“No se pudo registrar”).
- Login OK pero **Network Error** en panel (API/proxy/CORS/puerto).
- Usuario `pedro`: falta `tenants.read` → fricción de permisos en seed/roles.

### 15:10–15:20 — Factura multi-ítem + CRUD
- Queja clave: la factura parece un formulario, no una grilla → varias líneas / varios productos.
- “NO ELIMINA LAS FACTURAS” → auditoría de deletes en CRUD (tenant delete / permisos / RLS).

### 16:33–16:42 — Permisos y túnel
- Debate: demasiados permisos vs usabilidad.
- Cloudflare tunnel: `erp.nexo-dev.com` bloqueado por Vite `allowedHosts`.
- Segunda iteración: sigue fallando desde afuera → ajuste host/proxy.

### 17:43 — Documentos fiscales
- UI: Internal server error al agregar documento fiscal.
- Diagnóstico create path (factura vinculada, validaciones, RLS).

### 18:39–19:02 — Scanner + Woo
- Factura: alta de productos por lector / texto / SKU.
- “¿Puedo integrar a Ucommerce?” → aclaración de valor.
- Corrección: el target es **WooCommerce**.
- Pedido de doc MD → `docs/WOOCOMMERCE_CONNECTOR_MVP.md`.

### 19:04–19:38 — Frontend wave
- “Empezá a trabajar el frontend y actualizá STATUS”.
- Más tests frontend.
- STATUS refresca madurez UI.

### 20:09–20:27 — Roadmap post-firma
- Pautas de mejora mientras llega el certificado.
- “Dale realizalo todo” en ítems no bloqueantes.
- Qué se puede avanzar sin DGI live.

### 20:35–20:53 — Menú + POS decisión
- WooCommerce: cómo probar / cuenta.
- Menú demasiado largo → agrupar.
- Ajuste: agrupación no debe meter todo en un “marco” raro.
- Pregunta DGI: ¿caja rápida tipo supermercado es válida? → **sí, e-Ticket + modo POS dedicado**, manteniendo factura clásica.

### 21:05–21:34 — POS + stock de verdad
- Implementación modo POS dedicado.
- Facturas: fechas + ordenar.
- Regla de inventario: **entrada proveedor suma; venta resta**.
- “Dale perfecto hacelo” → purchase receipts + movimientos.

### 21:34–22:00 — Optimización continua
- “¿Qué nos queda?”
- Prioridades 2 y 3 del backlog corto.
- Filtros/búsqueda/paginación facturas.
- Woo: stock Nexorux→Woo; refunds→NC.

### 22:00–22:25 — Perfil, tests, prod baseline
- UX perfil / cambio de contraseña.
- Tests de entradas + baja de stock.
- Producción: backup, compose prod, monitoreo (baseline ~40%+).
- “Hacé todo lo que puedas que quede bien”.
- STATUS: qué falta para producción (lista bloqueante vs diferible).

### 22:29–23:00 — Recovery por correo (diseño)
- Flujo: correo registrado → token → nueva contraseña.
- Aún sin SMTP Gmail real (Mailpit / local).

### 23:01–23:41 — POS profesional + fullscreen
- Caja rápida más profesional (ticket, medios de pago, vuelto, espera, atajos).
- Botón **modo caja**: pantalla completa, desaparece el menú, solo facturación rápida.
- Confirmación: ¿actualizaste recovery? → sí en código; entrega de mail pendiente de SMTP real.

### 23:44–23:53 — API en Windows
- Uvicorn falla en `:8000` (WinError 10013).
- Arranque estable en **`:8002`**.
- Mail de recovery “nunca llega” a Gmail → falta SMTP externo.

---

## Día 2 — 13 ago 2026

### 00:13–00:30 — SMTP Gmail
- Prueba `test_smtp.py`; Mailpit no sirve para Gmail real.
- Config SMTP Gmail + app password (no documentar el secreto aquí).
- Recovery UI aún falla → iterar backend/from/env hasta envío OK.

### 00:48–01:05 — Logo + STATUS
- Logo desde `docs` en login y lugares convenientes.
- Error al agregar certificados (Internal server error).
- Pedido: actualizar `STATUS.md`.

### 01:12–01:29 — GitHub
- Intención: subir la app a GitHub.
- Dec **privado** (suite, no público).
- Push a `main` cuando auth queda lista.
- *(Cualquier PAT pegado en chat debe considerarse comprometido y rotarse.)*

### 01:37–02:42 — Certificados e impuestos
- Siguen fallando creates (cert + tax).
- Root cause: FORCE RLS + `db.refresh` + alias `metadata` / `effective_from`.
- Subagents: tests de schema + restart API + verify creates.
- “Seguí” hasta create 200.

### 03:29–03:34 — Cierre madrugada
- “¿Cómo venimos?” + STATUS/README coherentes con la app real.

### 11:56–12:19 — Inventario UX + español
- Entradas de proveedor: sumar stock era complicado → UX (mismo depósito que caja, saldos, buscador).
- Actualizar estado en documento.
- Labels de facturas en español (producto Uruguay).

### 12:23–12:58 — Catálogo + cuenta corriente
- “Nada hardcodeado” → `/api/v1/catalog/` como fuente de labels/flags.
- **Pagos + cuentas corrientes** (saldo, vencido, límite, abiertas, cobros).
- STATUS otra vez.

### 13:11–15:12 — UX + ops no bloqueantes + push
- Mejorar experiencia visual sin reescribir.
- “¿Qué queda al 100%?” → separar bloqueantes DGI vs ops.
- Ejecutar no-bloqueantes: compose flags, health, backup/restore, CI `tsc`, PRODUCTION.md.
- Push a GitHub.

### 15:45–16:04 — Logo azul + tests
- Nuevo logo azul en docs; fix 5 tests; push.
- Brief de marca (colores N / botones / texto).

### 16:14–16:31 — Branding corregido
- No generar logo: usar **`Nexorux-erp.png`** de docs.
- Botones de login invisibles → CSS explícito.
- Logo más grande; menos padding del marco del sidebar.

### 16:37–17:20 — Cobro caja rápida
- Error al cobrar: `Could not refresh instance '<Invoice…>'`.
- Fix `reload_after_commit` en invoices, invoice_items, payments.
- Smoke: crear factura + ítem + pago por API OK.

### 17:18–17:50 — F1 nueva venta
- Atajo libre para **nueva venta** en POS (F1).
- Hint en UI + botón en ticket / banner post-cobro.

### 17:50–18:30 — Click → formulario
- Listas: click en registro abre el formulario/detalle que corresponde.
- `EntityListRow` en productos, clientes, facturas, pagos, proveedores, fiscal, entradas, etc.
- Producto: más campos (descripción, tipo, unidad).
- STATUS actualizado.
- Pedido de bitácora 42 h → este archivo.

---

## Entregables concretos (checklist)

### Backend
- [x] CRUD ERP + inventory (purchase receipts / stock in-out)
- [x] Current accounts + payments sync
- [x] Catalog API
- [x] SMTP recovery
- [x] RLS + `reload_after_commit` en paths críticos (cert, tax, invoice, items, payments)
- [x] WooCommerce MVP (webhook / sync / NC)
- [ ] Envío SOAP DGI firmado en ePrueba/producción

### Frontend
- [x] CRUD editable + click fila → detalle
- [x] POS profesional + modo caja + F1
- [x] Pagos / cuenta corriente
- [x] Labels ES vía catálogo
- [x] Branding logo oficial
- [x] Entradas proveedor UX

### Ops / docs
- [x] `STATUS.md`, `USER_HANDOFF.md`, PRODUCTION / EMAIL / RLS / Woo / **esta bitácora**
- [x] Compose prod, backups, health scripts, CI endurecido
- [x] GitHub privado `main`
- [ ] Cron backups off-host + drill restore en prod real
- [ ] Dominio + TLS público definitivo

---

## Lecciones de estas 42 h

1. **FORCE RLS** obliga a re-setear GUC tras `COMMIT`; `session.refresh()` falla → `reload_after_commit`.
2. En Windows, `:8000` a veces bloqueado → API/proxy en **`:8002`**.
3. Recovery real necesita **SMTP externo** (Mailpit ≠ Gmail).
4. DGI “10/10 en código” ≠ homologado: bloqueante = **certificado de firma**.
5. El valor salió de **flujos reales** (caja, proveedor→stock, CC), no solo CRUD.
6. La marca y los botones se rompen fácil si se inventa logo/colores en vez de usar el asset oficial.
7. Documentar la carrera (`BUILD_LOG` + `STATUS`) evita perder el hilo en el próximo handoff.

---

## Próximo hito (fuera de estas 42 h)

1. Material PEM firma DGI (`DGI_CERT_PATH` / `DGI_KEY_PATH`)
2. Primer envío firmado a ePrueba
3. Homologación DGI
4. Go-live ops (secrets rotados, dominio TLS, password demo cambiada, backups programados)

Detalle operativo: `STATUS.md` y `docs/PRODUCTION.md`.

---

## Mantenimiento de esta bitácora

- Agregar filas con hora exacta cuando haya más evidencia (commits, tickets).
- No pegar secretos; rotar cualquier credencial que haya circulado en chat.
- Mantener `STATUS.md` como estado actual; este archivo es **historia**.
