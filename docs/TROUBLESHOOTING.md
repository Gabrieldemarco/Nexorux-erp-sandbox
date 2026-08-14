# NEXORUX ERP - Manual de Troubleshooting

**Versión:** 1.0  
**Fecha:** 2026-08-13  
**Para:** Administradores del sistema y soporte técnico

---

## Índice

1. [Problemas de Acceso](#1-problemas-de-acceso)
2. [Problemas de Rendimiento](#2-problemas-de-rendimiento)
3. [Problemas de Base de Datos](#3-problemas-de-base-de-datos)
4. [Problemas de Facturación Electrónica](#4-problemas-de-facturación-electrónica)
5. [Problemas de Inventario](#5-problemas-de-inventario)
6. [Problemas de Pagos](#6-problemas-de-pagos)
7. [Problemas de Certificados](#7-problemas-de-certificados)
8. [Problemas de Integración](#8-problemas-de-integración)
9. [Problemas de Despliegue](#9-problemas-de-despliegue)
10. [Recuperación de Desastres](#10-recuperación-de-desastres)

---

## 1. Problemas de Acceso

### 1.1 No puedo iniciar sesión

**Síntomas:**
- Mensaje "Credenciales inválidas"
- Login no responde
- Página blanca después del login

**Causas posibles:**
- Contraseña incorrecta
- Cuenta bloqueada
- Cuenta inactiva
- Problema de conexión a base de datos
- Problema con el servicio de autenticación

**Soluciones:**

1. **Verificar credenciales:**
   ```bash
   # Asegúrese de que el email y contraseña sean correctos
   # Resetear contraseña si es necesario
   ```

2. **Verificar estado de cuenta:**
   ```bash
   # Consultar en base de datos
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT email, status FROM user_account WHERE email='usuario@ejemplo.com';"
   ```

3. **Desbloquear cuenta:**
   ```bash
   # Reiniciar intentos fallidos
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "UPDATE user_account SET failed_attempts=0 WHERE email='usuario@ejemplo.com';"
   ```

4. **Verificar servicio backend:**
   ```bash
   # Verificar que el backend esté corriendo
   docker-compose ps backend
   
   # Verificar logs
   docker-compose logs backend
   ```

5. **Verificar conexión a base de datos:**
   ```bash
   # Verificar que PostgreSQL esté corriendo
   docker-compose ps postgres
   
   # Verificar conexión
   docker exec nexorux-postgres pg_isready -U nexorux
   ```

### 1.2 Recuperación de contraseña no funciona

**Síntomas:**
- Email de recuperación no llega
- Link de recuperación no funciona
- Error al restablecer contraseña

**Causas posibles:**
- Configuración SMTP incorrecta
- Email incorrecto en registro
- Link de recuperación expirado
- Problema con servicio de email

**Soluciones:**

1. **Verificar configuración SMTP:**
   ```bash
   # Verificar variables de entorno
   docker-compose exec backend env | grep SMTP
   
   # Probar envío de email manual
   docker-compose exec backend python scripts/test_smtp.py
   ```

2. **Verificar email registrado:**
   ```bash
   # Consultar email en base de datos
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT email FROM user_account WHERE email='usuario@ejemplo.com';"
   ```

3. **Verificar logs de email:**
   ```bash
   # Verificar logs de outbox
   docker-compose logs backend | grep -i email
   ```

4. **Reset manual por administrador:**
   ```bash
   # Generar nuevo hash de contraseña
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "UPDATE user_account SET password_hash='nuevo_hash' WHERE email='usuario@ejemplo.com';"
   ```

### 1.3 Cuenta bloqueada

**Síntomas:**
- Mensaje "Cuenta bloqueada por demasiados intentos fallidos"
- No puede iniciar sesión incluso con contraseña correcta

**Causas posibles:**
- 5 o más intentos fallidos de login
- Ataque de fuerza bruta

**Soluciones:**

1. **Desbloquear cuenta:**
   ```bash
   # Reiniciar intentos fallidos
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "UPDATE user_account SET failed_attempts=0, locked_until=NULL WHERE email='usuario@ejemplo.com';"
   ```

2. **Verificar actividad sospechosa:**
   ```bash
   # Consultar logs de auditoría
   docker-compose logs backend | grep "usuario@ejemplo.com"
   ```

### 1.4 Error de CORS

**Síntomas:**
- Error "CORS policy" en consola del navegador
- API no responde desde frontend

**Causas posibles:**
- Configuración CORS incorrecta
- Origen no permitido
- Proxy mal configurado

**Soluciones:**

1. **Verificar configuración CORS:**
   ```bash
   # Verificar variables de entorno
   docker-compose exec backend env | grep CORS
   ```

2. **Agregar origen a CORS_ORIGINS:**
   ```bash
   # En docker-compose.yml o .env
   CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","https://tu-dominio.com"]
   ```

3. **Reiniciar backend:**
   ```bash
   docker-compose restart backend
   ```

---

## 2. Problemas de Rendimiento

### 2.1 Sistema lento

**Síntomas:**
- Tiempos de respuesta lentos
- Páginas cargan lentamente
- Operaciones tardan mucho

**Causas posibles:**
- Alta carga en servidor
- Consultas de base de datos no optimizadas
- Falta de índices
- Problema de red
- Memoria insuficiente

**Soluciones:**

1. **Verificar uso de recursos:**
   ```bash
   # Uso de CPU y memoria
   docker stats
   
   # Uso de disco
   df -h
   ```

2. **Verificar logs de performance:**
   ```bash
   # Buscar queries lentas
   docker-compose logs backend | grep -i "slow query"
   ```

3. **Verificar conexiones a base de datos:**
   ```bash
   # Número de conexiones activas
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT count(*) FROM pg_stat_activity WHERE state='active';"
   ```

4. **Reiniciar servicios:**
   ```bash
   docker-compose restart backend
   docker-compose restart postgres
   ```

### 2.2 Timeouts en operaciones

**Síntomas:**
- Operaciones expiran antes de completar
- Error "timeout" en logs

**Causas posibles:**
- Timeout de base de datos
- Timeout de DGI
- Timeout de Redis
- Operación muy larga

**Soluciones:**

1. **Aumentar timeout de base de datos:**
   ```bash
   # En .env o docker-compose.yml
   DATABASE_POOL_TIMEOUT=30
   ```

2. **Aumentar timeout de DGI:**
   ```bash
   # En .env o docker-compose.yml
   DGI_TIMEOUT=30
   ```

3. **Verificar cola de tareas:**
   ```bash
   # Verificar tareas pendientes en Celery
   docker-compose exec backend celery -A app.celery inspect active
   ```

### 2.3 Alta memoria

**Síntomas:**
- Sistema consume mucha memoria
- Servicios se reinician
- Intercambio de disco alto

**Causas posibles:**
- Memory leak
- Muchas conexiones a base de datos
- Caché muy grande
- Tareas pendientes en cola

**Soluciones:**

1. **Verificar uso de memoria:**
   ```bash
   docker stats --no-stream
   ```

2. **Limpiar caché de Redis:**
   ```bash
   docker exec nexorux-redis redis-cli FLUSHALL
   ```

3. **Reiniciar servicios:**
   ```bash
   docker-compose restart backend
   docker-compose restart redis
   ```

---

## 3. Problemas de Base de Datos

### 3.1 No se puede conectar a la base de datos

**Síntomas:**
- Error "could not connect to database"
- Servicio no responde
- Timeout de conexión

**Causas posibles:**
- PostgreSQL no está corriendo
- Credenciales incorrectas
- Firewall bloqueando conexión
- Red no accesible

**Soluciones:**

1. **Verificar estado de PostgreSQL:**
   ```bash
   docker-compose ps postgres
   ```

2. **Reiniciar PostgreSQL:**
   ```bash
   docker-compose restart postgres
   ```

3. **Verificar credenciales:**
   ```bash
   # Verificar variables de entorno
   docker-compose exec backend env | grep DATABASE_URL
   ```

4. **Verificar logs de PostgreSQL:**
   ```bash
   docker-compose logs postgres
   ```

### 3.2 Error de migración

**Síntomas:**
- Error al ejecutar migraciones
- "Table already exists"
- "Column does not exist"

**Causas posibles:**
- Migración ya aplicada
- Conflicto con migración existente
- Versión de Alembic desincronizada

**Soluciones:**

1. **Verificar versión de Alembic:**
   ```bash
   docker-compose exec backend alembic current
   ```

2. **Verificar migraciones aplicadas:**
   ```bash
   docker-compose exec backend alembic history
   ```

3. **Forzar migración específica:**
   ```bash
   docker-compose exec backend alembic upgrade <revision>
   ```

4. **Rollback si es necesario:**
   ```bash
   docker-compose exec backend alembic downgrade -1
   ```

### 3.3 Conexiones agotadas

**Síntomas:**
- Error "too many connections"
- Nuevas conexiones rechazadas

**Causas posibles:**
- Pool de conexiones agotado
- Conexiones no cerradas
- Límite de PostgreSQL alcanzado

**Soluciones:**

1. **Verificar conexiones activas:**
   ```bash
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT count(*) FROM pg_stat_activity WHERE state='active';"
   ```

2. **Matar conexiones inactivas:**
   ```bash
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND query_start < now() - interval '5 minutes';"
   ```

3. **Aumentar pool de conexiones:**
   ```bash
   # En .env o docker-compose.yml
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=10
   ```

### 3.4 Disco lleno

**Síntomas:**
- Error "disk full"
- No se pueden crear archivos
- Backups fallan

**Causas posibles:**
- Disco lleno
- Muchos logs
- Backups antiguos no borrados

**Soluciones:**

1. **Verificar espacio en disco:**
   ```bash
   df -h
   ```

2. **Limpiar logs antiguos:**
   ```bash
   # Limpiar logs de Docker
   docker system prune -a
   
   # Limpiar logs de aplicación
   find ./backups -name "*.log" -mtime +30 -delete
   ```

3. **Limpiar backups antiguos:**
   ```bash
   # El script backup_postgres.sh ya limpia automáticamente
   # Pero puede limpiar manualmente:
   find ./backups -name "nexorux_prod_*.sql.gz" -mtime +30 -delete
   ```

---

## 4. Problemas de Facturación Electrónica

### 4.1 CFE rechazado por DGI

**Síntomas:**
- Estado "Rejected" en documento fiscal
- Motivo de rechazo en respuesta DGI

**Causas posibles:**
- Datos incorrectos en CFE
- Formato XML inválido
- Certificado inválido
- RUT incorrecto
- CAE no vigente o agotado

**Soluciones:**

1. **Verificar motivo de rechazo:**
   ```bash
   # Consultar respuesta DGI en documento fiscal
   docker exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT response_code, response_message FROM fiscal_response WHERE fiscal_document_id='uuid_del_cfe';"
   ```

2. **Validar datos del CFE:**
   - Verificar RUT del emisor
   - Verificar RUT del receptor
   - Verificar tipo de CFE
   - Verificar numeración dentro del rango CAE

3. **Verificar certificado:**
   ```bash
   # Verificar que el certificado esté configurado
   docker-compose exec backend env | grep DGI_CERT_PATH
   
   # Verificar que el archivo exista
   docker-compose exec backend ls -la /path/to/cert.pem
   ```

4. **Verificar CAE:**
   ```bash
   # Verificar que el CAE esté vigente
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT range_start, range_end, expiration_date, current_number FROM cae WHERE cfe_type='111' AND status='active';"
   ```

### 4.2 Error al firmar CFE

**Síntomas:**
- Error al firmar documento
- "Invalid certificate"
- "Private key not found"

**Causas posibles:**
- Certificado corrupto
- Clave privada incorrecta
- Contraseña de certificado incorrecta
- Formato de certificado incorrecto

**Soluciones:**

1. **Verificar archivos de certificado:**
   ```bash
   # Verificar que los archivos existan
   ls -la /path/to/cert.pem
   ls -la /path/to/key.pem
   ```

2. **Verificar formato de certificado:**
   ```bash
   # Verificar formato PEM
   openssl x509 -in /path/to/cert.pem -text -noout
   ```

3. **Reconfigurar certificado:**
   - Volver a subir el certificado desde la UI
   - Verificar contraseña
   - Verificar que sea el certificado correcto (nominado/innominado/avanzado)

### 4.3 Timeout al enviar a DGI

**Síntomas:**
- Error "timeout" al enviar CFE
- Estado "Sent" sin respuesta

**Causas posibles:**
- Servicio DGI no responde
- Problema de red
- Timeout muy corto
- TLS/SSL incorrecto

**Soluciones:**

1. **Verificar conectividad con DGI:**
   ```bash
   # Verificar que el puerto sea accesible
   curl -v https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba?wsdl
   ```

2. **Aumentar timeout:**
   ```bash
   # En .env o docker-compose.yml
   DGI_TIMEOUT=60
   ```

3. **Verificar configuración TLS:**
   ```bash
   # Verificar que se esté usando TLS 1.2+
   docker-compose exec backend python -c "import ssl; print(ssl.OPENSSL_VERSION)"
   ```

### 4.4 CAE agotado

**Síntomas:**
- Error "CAE range exhausted"
- No se pueden emitir más CFE de ese tipo

**Causas posibles:**
- Rango de numeración agotado
- CAE vencido
- Configuración incorrecta de numeración

**Soluciones:**

1. **Verificar estado del CAE:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT range_start, range_end, current_number, expiration_date, status FROM cae WHERE cfe_type='111';"
   ```

2. **Solicitar nuevo CAE:**
   - Ir al portal de DGI
   - Servicios en línea / Constancias
   - eFactura - Constancia Comprobante Fiscal Electrónico - Solicitud
   - Descargar nuevo CAE XML
   - Subir al sistema

3. **Configurar nuevo CAE:**
   - Vaya a "CAE" en el sistema
   - Haga clic en "Add CAE"
   - Suba el archivo CAE XML

---

## 5. Problemas de Inventario

### 5.1 Stock no se actualiza

**Síntomas:**
- Stock no cambia después de venta
- Stock incorrecto en consultas

**Causas posibles:**
- Estado de factura incorrecto
- Configuración de stock deshabilitada
- Error en trigger de stock
- Transacción no confirmada

**Soluciones:**

1. **Verificar estado de factura:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT id, status FROM invoice WHERE id='uuid_factura';"
   ```

2. **Verificar configuración de stock:**
   ```bash
   # Verificar flag de stock
   docker-compose exec backend env | grep STOCK_ALLOW_NEGATIVE
   ```

3. **Verificar movimientos de stock:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM stock_movement WHERE invoice_id='uuid_factura';"
   ```

### 5.2 Stock negativo

**Síntomas:**
- Stock en números negativos
- Error "insufficient stock" incorrecto

**Causas posibles:**
- Configuración permite stock negativo
- Error en cálculo de stock
- Movimientos de stock no registrados

**Soluciones:**

1. **Verificar configuración:**
   ```bash
   # Deshabilitar stock negativo en producción
   STOCK_ALLOW_NEGATIVE=false
   ```

2. **Recalcular stock:**
   ```bash
   # Recalcular stock desde movimientos
   docker-compose exec backend python scripts/recalc_stock.py
   ```

### 5.3 Entradas de proveedor no actualizan stock

**Síntomas:**
- Entrada de proveedor registrada pero stock no aumenta

**Causas posibles:**
- Estado de entrada incorrecto
- Depósito incorrecto
- Error en trigger de stock

**Soluciones:**

1. **Verificar estado de entrada:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT id, status FROM purchase_receipt WHERE id='uuid_entrada';"
   ```

2. **Verificar movimientos de stock:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM stock_movement WHERE reference_id='uuid_entrada';"
   ```

---

## 6. Problemas de Pagos

### 6.1 Pago no actualiza factura

**Síntomas:**
- Pago registrado pero factura sigue pendiente
- Cuenta corriente no actualizada

**Causas posibles:**
- Estado de pago incorrecto
- Error en trigger de cuenta corriente
- Factura no configurada para afectar cuenta corriente

**Soluciones:**

1. **Verificar estado de pago:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT id, status, counts_as_paid FROM payment WHERE id='uuid_pago';"
   ```

2. **Verificar configuración de factura:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT id, affects_receivable FROM invoice WHERE id='uuid_factura';"
   ```

3. **Verificar cuenta corriente:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM current_account WHERE customer_id='uuid_cliente';"
   ```

### 6.2 Saldo de cuenta corriente incorrecto

**Síntomas:**
- Saldo no coincide con cálculo esperado
- Vencido incorrecto

**Causas posibles:**
- Error en cálculo de saldo
- Facturas/pagos no considerados
- Notas de crédito no restadas

**Soluciones:**

1. **Recalcular saldo:**
   ```bash
   docker-compose exec backend python scripts/recalc_balance.py --customer_id uuid_cliente
   ```

2. **Verificar todas las transacciones:**
   ```bash
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM invoice WHERE customer_id='uuid_cliente' AND affects_receivable=true;"
   docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM payment WHERE customer_id='uuid_cliente' AND counts_as_paid=true;"
   ```

---

## 7. Problemas de Certificados

### 7.1 Certificado vencido

**Síntomas:**
- Error "certificate expired"
- DGI rechaza conexiones

**Causas posibles:**
- Certificado vencido
- Fecha del sistema incorrecta
- Certificado no válido para el ambiente

**Soluciones:**

1. **Verificar fecha de vencimiento:**
   ```bash
   # Verificar en sistema
   docker-compose exec backend python -c "from datetime import datetime; from cryptography import x509; cert = x509.load_pem_x509_certificate(open('/path/to/cert.pem', 'rb').read()); print(cert.not_valid_after)"
   ```

2. **Obtener nuevo certificado:**
   - Contactar proveedor autorizado (ABITAB, Correo, ANTEL)
   - Solicitar renovación
   - Subir nuevo certificado al sistema

### 7.2 Contraseña de certificado incorrecta

**Síntomas:**
- Error "incorrect password"
- No se puede leer clave privada

**Causas posibles:**
- Contraseña incorrecta al configurar
- Certificado corrupto
- Clave privada corrupta

**Soluciones:**

1. **Reconfigurar certificado:**
   - Volver a subir el certificado
   - Verificar contraseña
   - Verificar que sea el archivo correcto

2. **Verificar integridad de archivos:**
   ```bash
   # Verificar que los archivos no estén corruptos
   openssl x509 -in /path/to/cert.pem -text -noout
   openssl rsa -in /path/to/key.pem -check
   ```

---

## 8. Problemas de Integración

### 8.1 WooCommerce no sincroniza

**Síntomas:**
- Productos no se sincronizan
- Stock no se actualiza
- Webhook no funciona

**Causas posibles:**
- Webhook URL incorrecta
- Autenticación WooCommerce fallando
- Error en mapeo de datos

**Soluciones:**

1. **Verificar configuración WooCommerce:**
   ```bash
   # Verificar variables de entorno
   docker-compose exec backend env | grep WOO
   ```

2. **Verificar logs de integración:**
   ```bash
   docker-compose logs backend | grep -i woo
   ```

3. **Testear webhook manualmente:**
   ```bash
   # Enviar request manual al webhook
   curl -X POST https://tu-tienda.com/wc-api/nexorux/webhook -H "Content-Type: application/json" -d '{"test": true}'
   ```

---

## 9. Problemas de Despliegue

### 9.1 Docker Compose no levanta servicios

**Síntomas:**
- Error al ejecutar docker-compose up
- Servicios no inician

**Causas posibles:**
- Puertos ya en uso
- Imágenes no disponibles
- Errores en docker-compose.yml
- Recursos insuficientes

**Soluciones:**

1. **Verificar puertos en uso:**
   ```bash
   # En Linux
   netstat -tulpn | grep -E ':(8000|5432|6379|3000)'
   
   # En Windows
   netstat -ano | findstr :8000
   ```

2. **Limpiar y reconstruir:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Verificar imágenes:**
   ```bash
   docker images
   docker-compose pull
   ```

### 9.2 Error de migración en despliegue

**Síntomas:**
- Error al ejecutar migraciones en despliegue
- Servicio no inicia

**Causas posibles:**
- Migraciones no aplicadas en orden
- Conflicto con datos existentes
- Versión de base de datos incompatible

**Soluciones:**

1. **Verificar migraciones pendientes:**
   ```bash
   docker-compose exec backend alembic current
   docker-compose exec backend alembic heads
   ```

2. **Forzar migración:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Reiniciar servicio:**
   ```bash
   docker-compose restart backend
   ```

---

## 10. Recuperación de Desastres

### 10.1 Restauración desde backup

**Pasos:**

1. **Detener servicios:**
   ```bash
   docker-compose down
   ```

2. **Seleccionar backup a restaurar:**
   ```bash
   ls -lt ./backups/nexorux_prod_*.sql.gz | head -1
   ```

3. **Ejecutar restore:**
   ```bash
   # Linux
   ./scripts/restore_postgres.sh ./backups/nexorux_prod_YYYYMMDD_HHMMSS.sql.gz
   
   # Windows
   .\scripts\restore_postgres.ps1 .\backups\nexorux_prod_YYYYMMDD_HHMMSS.sql.gz
   ```

4. **Verificar restauración:**
   ```bash
   docker-compose up -d postgres
   docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM tenant;"
   ```

5. **Reiniciar servicios:**
   ```bash
   docker-compose up -d
   ```

### 10.2 Pérdida de certificados

**Pasos:**

1. **Contactar proveedor autorizado**
   - ABITAB, Correo Uruguayo, ANTEL
   - Solicitar reemisión de certificados

2. **Reconfigurar certificados:**
   - Vaya a "Certificados" en el sistema
   - Suba nuevos archivos de certificado
   - Verifique que funcionen correctamente

3. **Probar emisión de CFE:**
   - Emitir un CFE de prueba
   - Verificar que se firme correctamente
   - Verificar que DGI lo acepte

### 10.3 Pérdida de base de datos completa

**Pasos:**

1. **Último backup disponible:**
   - Identificar el backup más reciente
   - Verificar integridad del backup

2. **Restaurar desde backup:**
   - Seguir pasos de restauración

3. **Verificar datos:**
   - Verificar datos críticos
   - Verificar integridad de datos

4. **Investigar causa:**
   - Revisar logs
   - Identificar causa de pérdida
   - Implementar medidas preventivas

---

## Contacto de Soporte

Para soporte técnico avanzado:

- **Email:** soporte@nexorux.erp
- **Teléfono:** [número de teléfono]
- **Horario:** Lunes a viernes, 9:00 - 18:00

**Información requerida al reportar incidente:**
- Descripción detallada del problema
- Pasos para reproducir
- Mensajes de error exactos
- Logs relevantes
- Capturas de pantalla (si aplica)

---

**Versión del manual:** 1.0  
**Última actualización:** 2026-08-13  
**Sistema:** NEXORUX ERP v0.1.0
