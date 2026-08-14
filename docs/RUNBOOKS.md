# NEXORUX ERP - Runbooks de Incidentes

**Versión:** 1.0  
**Fecha:** 2026-08-13  
**Para:** Equipo de operaciones y soporte técnico

---

## Índice

1. [Runbook: Servicio Caido](#runbook-servicio-caido)
2. [Runbook: Base de Datos Caida](#runbook-base-de-datos-caida)
3. [Runbook: DGI No Responde](#runbook-dgi-no-responde)
4. [Runbook: Certificado Vencido](#runbook-certificado-vencido)
5. [Runbook: CAE Agotado](#runbook-cae-agotado)
6. [Runbook: Pérdida de Datos](#runbook-pérdida-de-datos)
7. [Runbook: Ataque de Seguridad](#runbook-ataque-de-seguridad)
8. [Runbook: Performance Degradation](#runbook-performance-degradation)
9. [Runbook: Backup Falló](#runbook-backup-falló)
10. [Runbook: Deploy Falló](#runbook-deploy-falló)

---

## Runbook: Servicio Caido

### Severidad: CRÍTICA
### Tiempo de respuesta objetivo: 15 minutos

### Síntomas
- Health check falla (`/health` no responde)
- Backend no responde
- Frontend muestra errores de conexión
- Usuarios no pueden acceder al sistema

### Impacto
- **Usuarios:** No pueden acceder al sistema
- **Operaciones:** Facturación, ventas, inventario afectados
- **Negocio:** Pérdida de productividad

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-5 minutos)

**Verificar health check:**
```bash
curl http://localhost:8000/health
curl https://tu-dominio.com/health
```

**Verificar contenedores Docker:**
```bash
docker-compose ps
```

**Verificar logs de backend:**
```bash
docker-compose logs backend --tail=50
```

**Verificar recursos del servidor:**
```bash
# CPU y memoria
docker stats

# Disco
df -h
```

#### 2. Acciones Inmediatas (5-10 minutos)

**Si backend no está corriendo:**
```bash
# Reiniciar backend
docker-compose restart backend

# Si no responde, forzar recreación
docker-compose up -d --force-recreate backend
```

**Si PostgreSQL no está corriendo:**
```bash
# Reiniciar PostgreSQL
docker-compose restart postgres

# Verificar datos
docker-compose exec postgres pg_isready -U nexorux
```

**Si Redis no está corriendo:**
```bash
# Reiniciar Redis
docker-compose restart redis

# Verificar conexión
docker-compose exec redis redis-cli ping
```

**Si todos los servicios están caídos:**
```bash
# Reiniciar todo
docker-compose down
docker-compose up -d
```

#### 3. Verificación (10-15 minutos)

**Verificar health check:**
```bash
curl http://localhost:8000/health
```

**Verificar acceso a sistema:**
- Abrir navegador en localhost:3000
- Intentar login
- Verificar que carga dashboard

**Verificar operaciones críticas:**
- Intentar crear una factura de prueba
- Verificar que se puede guardar

#### 4. Comunicación (15 minutos)

**Notificar a stakeholders:**
- "NEXORUX ERP experimentando interrupción de servicio"
- "Estamos trabajando en restaurar el servicio"
- "Tiempo estimado: 15 minutos"

**Actualizar monitoreo:**
- Marcar incidente en sistema de tickets
- Actualizar estado en Slack/Teams si está configurado

#### 5. Resolución

**Una vez restaurado:**
- Verificar que todos los servicios estén funcionando
- Ejecutar health check completo
- Verificar que los datos estén intactos
- Comunicar restauración a stakeholders

#### 6. Post-Incidente

**Investigar causa raíz:**
- Revisar logs de Docker
- Revisar logs de aplicación
- Identificar causa del fallo
- Implementar medidas preventivas

**Documentar incidente:**
- Crear entrada en runbook de incidentes
- Documentar tiempo de resolución
- Documentar causa raíz

---

## Runbook: Base de Datos Caida

### Severidad: CRÍTICA
### Tiempo de respuesta objetivo: 30 minutos

### Síntomas
- Error "could not connect to database"
- PostgreSQL no responde
- Queries fallan con timeout
- Conexiones agotadas

### Impacto
- **Usuarios:** No pueden acceder al sistema
- **Operaciones:** Todas las operaciones afectadas
- **Datos:** Riesgo de pérdida de datos si no hay backup reciente

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-5 minutos)

**Verificar estado de PostgreSQL:**
```bash
docker-compose ps postgres
```

**Verificar logs de PostgreSQL:**
```bash
docker-compose logs postgres --tail=50
```

**Verificar conectividad:**
```bash
docker-compose exec postgres pg_isready -U nexorux
```

**Verificar espacio en disco:**
```bash
df -h
```

#### 2. Acciones Inmediatas (5-15 minutos)

**Si PostgreSQL no está corriendo:**
```bash
# Intentar reiniciar
docker-compose restart postgres

# Si no responde, verificar datos
docker volume ls
```

**Si disco está lleno:**
```bash
# Limpiar logs antiguos
docker system prune -a

# Limpiar backups antiguos (manual)
find ./backups -name "nexorux_prod_*.sql.gz" -mtime +30 -delete
```

**Si conexiones agotadas:**
```bash
# Matar conexiones inactivas
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND query_start < now() - interval '5 minutes';"
```

**Si hay corrupción de datos:**
```bash
# Verificar con pg_dump
docker-compose exec postgres pg_dump -U nexorux -d nexorux_prod --schema-only > /tmp/schema.sql
```

#### 3. Restauración desde Backup (15-30 minutos)

**SI los datos están corruptos o perdidos:**

1. **Detener servicios:**
```bash
docker-compose down
```

2. **Seleccionar backup más reciente:**
```bash
ls -lt ./backups/nexorux_prod_*.sql.gz | head -1
```

3. **Restaurar backup:**
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

#### 4. Verificación (30 minutos)

**Verificar datos críticos:**
```bash
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM tenant;"
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM company;"
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM invoice;"
```

**Verificar health check:**
```bash
curl http://localhost:8000/health
```

**Verificar acceso al sistema:**
- Intentar login
- Verificar dashboard
- Verificar que carguen datos

#### 5. Comunicación

**Notificar a stakeholders:**
- "Base de datos experimentando interrupción"
- "Estamos restaurando desde backup"
- "Tiempo estimado: 30 minutos"

#### 6. Post-Incidente

**Investigar causa raíz:**
- Revisar logs de PostgreSQL
- Verificar uso de recursos
- Identificar causa de la caída

**Implementar medidas preventivas:**
- Aumentar monitoreo de base de datos
- Configurar alertas de espacio en disco
- Implementar backups más frecuentes
- Considerar PostgreSQL de alta disponibilidad

---

## Runbook: DGI No Responde

### Severidad: ALTA
### Tiempo de respuesta objetivo: 1 hora

### Síntomas
- Error "timeout" al enviar CFE a DGI
- Estado "Sent" sin respuesta
- CFE rechazados por timeout

### Impacto
- **Usuarios:** No pueden emitir facturas electrónicas
- **Operaciones:** Facturación electrónica afectada
- **Negocio:** Impacto en operaciones de venta

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar conectividad con DGI:**
```bash
# Verificar que el puerto sea accesible
curl -v https://efactura.dgi.gub.uy:6443/ePrueba/ws_eprueba?wsdl
```

**Verificar configuración DGI:**
```bash
docker-compose exec backend env | grep DGI
```

**Verificar certificado:**
```bash
docker-compose exec backend ls -la /path/to/cert.pem
docker-compose exec backend ls -la /path/to/key.pem
```

**Verificar logs de DGI:**
```bash
docker-compose logs backend | grep -i dgi
```

#### 2. Acciones Inmediatas (10-30 minutos)

**Si DGI no responde (contingencia):**
- Informar a usuarios que la facturación electrónica está en contingencia
- Habilitar modo de contingencia en el sistema
- Documentar todas las operaciones en contingencia

**Si es problema de red local:**
- Verificar conexión a internet
- Verificar firewall
- Verificar configuración DNS

**Si es problema de certificado:**
- Verificar que el certificado sea válido
- Verificar que la clave privada sea correcta
- Reconfigurar certificado si es necesario

**Si es problema de timeout:**
- Aumentar timeout de DGI
- Reintentar envío de CFE
- Verificar que no esté generando duplicados

#### 3. Contingencia (30-60 minutos)

**Activar modo de contingencia:**
- En configuración fiscal, habilitar modo contingencia
- Emitir comprobantes de contingencia (CFC)
- Documentar motivo de contingencia

**Informar a usuarios:**
- "DGI no responde, activando contingencia"
- "Se emitirán comprobantes de contingencia"
- "Cuando DGI restable, se procesarán los CFE pendientes"

#### 4. Verificación (60 minutos)

**Verificar que contingencia funcione:**
- Emitir comprobante de contingencia de prueba
- Verificar que se genere correctamente
- Verificar que se pueda imprimir

**Monitorear estado de DGI:**
- Verificar periódicamente si DGI responde
- Continuar checks hasta que restable

#### 5. Normalización

**Cuando DGI restable:**
- Desactivar modo de contingencia
- Procesar CFE en cola
- Verificar que se envíen correctamente
- Verificar respuestas de DGI

**Convertir CFC a CFE:**
- Para comprobantes emitidos en contingencia
- Procesar según normativa DGI
- Regularizar situación fiscal

#### 6. Comunicación

**Notificar a stakeholders:**
- "DGI ha restablecido"
- "Procesando CFE en cola"
- "Tiempo estimado para normalización"

**Notificar a DGI:**
- Reportar incidente técnico si es necesario
- Usar herramienta de reporte de incidentes DGI

#### 7. Post-Incidente

**Documentar incidente:**
- Registrar en runbook de incidentes
- Documentar duración de interrupción DGI
- Documentar CFE emitidos en contingencia
- Documentar proceso de regularización

**Implementar medidas preventivas:**
- Mejorar monitoreo de DGI
- Implementar alertas de caída de DGI
- Optimizar proceso de contingencia

---

## Runbook: Certificado Vencido

### Severidad: ALTA
### Tiempo de respuesta objetivo: 4 horas

### Síntomas
- Error "certificate expired"
- DGI rechaza conexiones
- No se pueden firmar CFE

### Impacto
- **Usuarios:** No pueden emitir facturas electrónicas
- **Operaciones:** Facturación electrónica completamente afectada
- **Negocio:** Impacto severo en operaciones de venta

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar fecha de vencimiento:**
```bash
docker-compose exec backend python -c "from datetime import datetime; from cryptography import x509; cert = x509.load_pem_x509_certificate(open('/path/to/cert.pem', 'rb').read()); print(cert.not_valid_after)"
```

**Verificar configuración de certificado:**
```bash
docker-compose exec backend env | grep DGI_CERT
```

**Verificar ambiente:**
```bash
docker-compose exec backend env | grep DGI_ENVIRONMENT
```

#### 2. Acciones Inmediatas (10-30 minutos)

**Contactar proveedor de certificados:**
- ABITAB: https://iddigital.com.uy/es/solicitud-de-certificado/
- Correo Uruguayo: https://www.correo.com.uy/sel/index.asp
- ANTEL: https://www.tuid.uy/user/auth

**Solicitar nuevo certificado:**
- Especificar tipo (nominado/innominado/avanzado)
- Especificar vigencia (1 o 2 años)
- Especificar razón social de la empresa

**Mientras se obtiene nuevo certificado:**
- Informar a usuarios que la facturación electrónica está temporalmente suspendida
- Considerar alternativas (contingencia) si es crítico

#### 3. Instalación de Nuevo Certificado (30-120 minutos)

**Una vez obtenido el nuevo certificado:**

1. **Descargar archivos:**
   - Certificado (.pem o .crt)
   - Clave privada (.key)
   - Contraseña

2. **Configurar en sistema:**
   - Vaya a "Certificados"
   - Haga clic en "Add Certificate"
   - Suba los archivos
   - Ingrese la contraseña
   - Seleccione el ambiente (Testing/Homologación/Producción)

3. **Verificar configuración:**
   - Verificar que los archivos estén correctamente cargados
   - Verificar que el certificado sea válido
   - Verificar que la clave privada sea correcta

#### 4. Pruebas (120-240 minutos)

**Probar emisión de CFE:**
- Emitir CFE de prueba
- Verificar que se firme correctamente
- Verificar que DGI lo acepte

**Verificar que funcione en ambiente correcto:**
- Si es producción, probar en producción
- Si es homologación, probar en homologación

#### 5. Normalización (240 minutos)

**Una vez verificado:**
- Informar a usuarios que la facturación electrónica está restaurada
- Retomar operaciones normales
- Verificar que todo funcione correctamente

#### 6. Comunicación

**Notificar a stakeholders:**
- "Certificado digital ha vencido"
- "Hemos solicitado nuevo certificado"
- "Tiempo estimado: 4 horas"

**Actualizar estado:**
- Actualizar cuando se obtenga nuevo certificado
- Actualizar cuando esté configurado
- Actualizar cuando esté verificado

#### 7. Post-Incidente

**Documentar incidente:**
- Registrar fecha de vencimiento
- Documentar fecha de renovación
- Documentar proceso de renovación
- Implementar alertas de vencimiento futuro

**Implementar medidas preventivas:**
- Configurar alertas 30 días antes del vencimiento
- Automatizar proceso de renovación si es posible
- Calendario de renovación anual

---

## Runbook: CAE Agotado

### Severidad: ALTA
### Tiempo de respuesta objetivo: 2 horas

### Síntomas
- Error "CAE range exhausted"
- No se pueden emitir más CFE de ese tipo
- Mensaje "no CAE available" en sistema

### Impacto
- **Usuarios:** No pueden emitir facturas de ese tipo
- **Operaciones:** Facturación parcialmente afectada
- **Negocio:** Impacto moderado en operaciones de venta

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-5 minutos)

**Verificar estado del CAE:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT cfe_type, range_start, range_end, current_number, expiration_date, status FROM cae WHERE cfe_type='111';"
```

**Verificar que tipo de CFE está agotado:**
- e-Factura (111)
- e-Ticket (101)
- Notas de crédito/débito

**Verificar fecha de vencimiento:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT expiration_date FROM cae WHERE cfe_type='111';"
```

#### 2. Acciones Inmediatas (5-30 minutos)

**Informar a usuarios:**
- "CAE para e-Factura está agotado"
- "No se pueden emitir e-Facturas temporalmente"
- "Otros tipos de CFE siguen disponibles"

**Habilitar alternativas:**
- Si solo e-Factura está agotado, usar e-Ticket cuando sea posible
- Verificar qué tipos de CFE aún tienen CAE disponible

#### 3. Solicitar Nuevo CAE (30-120 minutos)

**Ir al portal de DGI:**
1. Acceder a https://servicios.dgi.gub.uy/serviciosenlinea
2. Iniciar sesión con Usuario DGI
3. Ir a "eFactura - Constancia Comprobante Fiscal Electrónico - Solicitud"
4. Seleccionar tipo de CFE (ej. e-Factura)
5. Ingresar cantidad deseada (mínimo 100, máximo 1,000,000)
6. Descargar archivo CAE XML

#### 4. Configurar Nuevo CAE (120-150 minutos)

**Subir al sistema:**
1. Vaya a "CAE"
2. Haga clic en "Add CAE"
3. Suba el archivo CAE XML
4. El sistema validará y configurará automáticamente

**Verificar configuración:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT range_start, range_end, current_number, expiration_date, status FROM cae WHERE cfe_type='111';"
```

#### 5. Verificación (150-180 minutos)

**Probar emisión de CFE:**
- Emitir e-Factura de prueba
- Verificar que se use el nuevo rango de numeración
- Verificar que se envíe a DGI correctamente

**Verificar respuestas DGI:**
- Verificar que DGI acepte el CFE
- Verificar que se reciba CAE de respuesta

#### 6. Normalización (180 minutos)

**Una vez verificado:**
- Informar a usuarios que la emisión de e-Factura está restaurada
- Retomar operaciones normales
- Verificar que todo funcione correctamente

#### 7. Comunicación

**Notificar a stakeholders:**
- "CAE para e-Factura ha sido agotado"
- "Hemos solicitado nuevo CAE a DGI"
- "Tiempo estimado: 2 horas"

**Actualizar estado:**
- Actualizar cuando se solicite nuevo CAE
- Actualizar cuando se configure
- Actualizar cuando esté verificado

#### 8. Post-Incidente

**Documentar incidente:**
- Registrar fecha de agotamiento
- Documentar fecha de solicitud de nuevo CAE
- Documentar proceso de obtención
- Implementar alertas de agotamiento

**Implementar medidas preventivas:**
- Configurar alertas cuando current_number esté al 80% del rango
- Configurar alertas 30 días antes del vencimiento
- Implementar proceso automático de solicitud de nuevo CAE

---

## Runbook: Pérdida de Datos

### Severidad: CRÍTICA
### Tiempo de respuesta objetivo: 2 horas

### Síntomas
- Datos corruptos o perdidos
- Tablas dañadas
- Registros eliminados accidentalmente

### Impacto
- **Usuarios:** Sistema no funciona o datos incorrectos
- **Operaciones:** Todas las operaciones afectadas
- **Negocio:** Impacto severo en operaciones

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Identificar alcance de pérdida:**
- ¿Qué datos están afectados?
- ¿Cuándo ocurrió la pérdida?
- ¿Cuál es la causa probable?

**Verificar estado de base de datos:**
```bash
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM tenant;"
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM company;"
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT COUNT(*) FROM invoice;"
```

**Verificar integridad de datos:**
```bash
# Verificar si hay errores de corrupción
docker-compose exec postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM pg_stat_database;"
```

#### 2. Decisión Crítica (10-20 minutos)

**¿Hay backup reciente?**
- Verificar último backup disponible
- Verificar integridad del backup
- Estimar pérdida de datos desde el backup

**¿Se puede recuperar desde backup?**
- SÍ: Restaurar desde backup
- NO: Investigar opciones de recuperación

#### 3. Restauración desde Backup (20-60 minutos)

**SI hay backup viable:**

1. **Detener servicios:**
```bash
docker-compose down
```

2. **Seleccionar backup:**
```bash
ls -lt ./backups/nexorux_prod_*.sql.gz | head -1
```

3. **Restaurar:**
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

#### 4. Investigación de Causa (60-120 minutos)

**SI no hay backup o backup está corrupto:**

**Investigar logs:**
```bash
docker-compose logs backend | grep -i error
docker-compose logs postgres | grep -i error
```

**Investigar auditoría:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC LIMIT 100;"
```

**Identificar causa:**
- ¿Fue una eliminación accidental?
- ¿Fue un error de migración?
- ¿Fue un ataque de seguridad?
- ¿Fue un error de aplicación?

#### 5. Recuperación Especializada (120-240 minutos)

**SI es posible recuperar datos:**

**Recuperación de tablas específicas:**
- Si solo algunas tablas están afectadas
- Considerar restaurar solo esas tablas
- Tener cuidado con foreign keys

**Recuperación de transacciones:**
- Si hay logs de auditoría detallados
- Considerar reconstruir operaciones desde logs
- Tener cuidado con integridad fiscal

#### 6. Comunicación

**Notificar a stakeholders:**
- "Hemos detectado una pérdida de datos"
- "Estamos investigando causa y opciones de recuperación"
- "Tiempo estimado: 2 horas"

**Actualizar estado:**
- Actualizar si se puede recuperar desde backup
- Actualizar si se necesitan medidas especiales
- Actualizar cuando se haya restaurado

#### 7. Post-Incidente

**Documentar incidente:**
- Registrar causa raíz
- Documentar datos perdidos
- Documentar datos recuperados
- Documentar tiempo de recuperación

**Implementar medidas preventivas:**
- Mejorar frecuencia de backups
- Implementar backups off-site
- Implementar logs más detallados
- Implementar alertas de anomalías

---

## Runbook: Ataque de Seguridad

### Severidad: CRÍTICA
### Tiempo de respuesta objetivo: 30 minutos

### Síntomas
- Actividad sospechosa en logs
- Usuarios reportan acceso no autorizado
- Cambios no autorizados en datos
- Ransomware o malware detectado

### Impacto
- **Usuarios:** Sistema no seguro, puede haber compromiso de datos
- **Operaciones:** Sistema puede necesitar desconexión
- **Negocio:** Impacto severo en confianza y cumplimiento

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar logs de auditoría:**
```bash
docker-compose logs backend | grep -i "unauthorized"
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC LIMIT 50;"
```

**Verificar usuarios activos:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT email, last_login FROM user_account WHERE last_login > NOW() - INTERVAL '1 hour';"
```

**Verificar intentos fallidos de login:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT email, failed_attempts FROM user_account WHERE failed_attempts > 0;"
```

#### 2. Acciones Inmediatas (10-20 minutos)

**SI hay evidencia de compromiso:**

1. **Desconectar sistema:**
```bash
docker-compose down
```

2. **Cambiar todas las contraseñas:**
- Contraseñas de base de datos
- Contraseñas de usuarios
- Contraseñas de servicios externos
- Contraseñas de certificados

3. **Cambiar secretos:**
- SECRET_KEY
- Contraseñas SMTP
- API keys

4. **Notificar a stakeholders:**
- "Hemos detectado una posible brecha de seguridad"
- "Hemos desconectado el sistema"
- "Estamos investigando y tomando medidas"

#### 3. Investigación (20-60 minutos)

**Analizar logs:**
- Identificar IP del atacante
- Identificar acciones realizadas
- Identificar datos accedidos

**Verificar integridad de datos:**
- Verificar que no haya cambios no autorizados
- Verificar que no haya datos eliminados
- Verificar que no haya datos sensibles expuestos

**Verificar malware:**
- Escanear servidores
- Verificar que no haya ransomware
- Verificar que no haya malware en backups

#### 4. Recuperación (60-120 minutos)

**Restaurar desde backup limpio:**
1. Restaurar desde backup anterior al incidente
2. Verificar que el backup esté limpio
3. Verificar que no hay rastros del atacante

**Reinstalar sistema:**
1. Considerar reinstalar desde cero
2. Usar imágenes Docker limpias
3. Verificar que no hay backdoors

**Cambiar todas las credenciales:**
- Nuevas contraseñas para todos los usuarios
- Nuevos certificados digitales
- Nuevas API keys

#### 5. Fortalecimiento (120-240 minutos)

**Implementar medidas de seguridad adicionales:**
- Habilitar 2FA para todos los usuarios
- Aumentar requisitos de contraseña
- Reducir sesiones concurrentes
- Implementar IP whitelisting

**Mejorar monitoreo:**
- Alertas en tiempo real de actividad sospechosa
- Alertas de cambios en configuración
- Alertas de acceso desde IPs no habituales

#### 6. Comunicación

**Notificar a stakeholders:**
- "Hemos contenido la brecha de seguridad"
- "Hemos tomado las siguientes medidas..."
- "El sistema está seguro nuevamente"
- "Deben cambiar sus contraseñas"

**Notificar a autoridades:**
- Si hay compromiso de datos personales
- Si hay impacto fiscal significativo
- Según regulación uruguaya aplicable

#### 7. Post-Incidente

**Documentar incidente:**
- Registrar causa del ataque
- Documentar datos comprometidos
- Documentar medidas tomadas
- Documentar tiempo de recuperación

**Implementar medidas preventivas:**
- Mejorar seguridad de contraseñas
- Implementar seguridad de red
- Implementar seguridad de aplicaciones
- Implementar educación de usuarios

---

## Runbook: Performance Degradation

### Severidad: MEDIA
### Tiempo de respuesta objetivo: 1 hora

### Síntomas
- Sistema lento
- Tiempos de respuesta altos
- Timeouts en operaciones
- Usuarios reportan lentitud

### Impacto
- **Usuarios:** Sistema usable pero lento
- **Operaciones:** Operaciones lentas pero funcionales
- **Negocio:** Impacto moderado en productividad

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar uso de recursos:**
```bash
docker stats
df -h
```

**Verificar queries lentas:**
```bash
docker-compose logs backend | grep -i "slow query"
```

**Verificar conexiones a base de datos:**
```bash
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT count(*) FROM pg_stat_activity WHERE state='active';"
```

**Verificar cola de tareas:**
```bash
docker-compose exec backend celery -A app.celery inspect active
```

#### 2. Acciones Inmediatas (10-30 minutos)

**Si CPU alta:**
```bash
# Identificar proceso consumidor
docker top

# Reiniciar servicio si es necesario
docker-compose restart backend
```

**Si memoria alta:**
```bash
# Limpiar caché de Redis
docker-compose exec redis redis-cli FLUSHALL

# Reiniciar servicios
docker-compose restart backend
docker-compose restart redis
```

**Si disco lleno:**
```bash
# Limpiar logs
docker system prune -a

# Limpiar backups antiguos
find ./backups -name "nexorux_prod_*.sql.gz" -mtime +30 -delete
```

**Si conexiones agotadas:**
```bash
# Matar conexiones inactivas
docker-compose exec nexorux-postgres psql -U nexorux -d nexorux_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND query_start < now() - interval '5 minutes';"
```

#### 3. Optimización (30-60 minutos)

**Verificar índices de base de datos:**
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add missing indexes"
```

**Aumentar pool de conexiones:**
```bash
# En .env o docker-compose.yml
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Habilitar cache:**
- Verificar que Redis esté configurado
- Verificar que el cache esté funcionando

#### 4. Verificación (60 minutos)

**Verificar que el sistema esté más rápido:**
- Probar operaciones críticas
- Verificar tiempos de respuesta
- Verificar que usuarios reporten mejora

#### 5. Comunicación

**Notificar a stakeholders:**
- "Sistema experimentando degradación de performance"
- "Estamos optimizando el sistema"
- "Tiempo estimado: 1 hora"

**Actualizar estado:**
- Actualizar cuando se haya mejorado
- Actualizar si se necesitan más medidas

#### 6. Post-Incidente

**Documentar incidente:**
- Registrar causa de degradación
- Documentar medidas tomadas
- Documentar mejora observada

**Implementar medidas preventivas:**
- Implementar alertas de uso de recursos
- Implementar monitoreo de performance
- Implementar optimizaciones preventivas

---

## Runbook: Backup Falló

### Severidad: ALTA
### Tiempo de respuesta objetivo: 2 horas

### Síntomas
- Error al ejecutar backup
- Backup no se crea
- Backup está corrupto

### Impacto
- **Usuarios:** Sistema funciona pero sin protección contra pérdida de datos
- **Operaciones:** Operaciones normales pero sin backup reciente
- **Negocio:** Riesgo severo si hay pérdida de datos

### Pasos de mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar script de backup:**
```bash
./scripts/backup_postgres.sh
```

**Verificar logs de backup:**
```bash
tail -f ./backups/backup.log
```

**Verificar espacio en disco:**
```bash
df -h
```

**Verificar conexión a base de datos:**
```bash
docker-compose exec postgres pg_isready -U nexorux
```

#### 2. Acciones Inmediatas (10-30 minutos)

**Si hay error de script:**
- Verificar que el script sea ejecutable
- Verificar permisos
- Verificar variables de entorno

**Si no hay espacio en disco:**
- Limpiar backups antiguos
- Limpiar logs de Docker
- Liberar espacio

**Si PostgreSQL no responde:**
- Reiniciar PostgreSQL
- Verificar conexión
- Verificar credenciales

#### 3. Backup Manual (30-60 minutos)

**Mientras se arregla el script:**

**Backup manual:**
```bash
docker exec nexorux-postgres pg_dump -U nexorux -d nexorux_prod --no-owner --no-acl | gzip > ./backups/nexorux_prod_manual_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Verificar backup:**
```bash
# Verificar que el archivo se creó
ls -lh ./backups/nexorux_prod_manual_*.sql.gz

# Verificar que no esté corrupto
gunzip -t ./backups/nexorux_prod_manual_YYYYMMDD_HHMMSS.sql.gz
```

#### 4. Reparación de Script (60-120 minutos)

**Investigar causa del error:**
- Revisar logs
- Verificar script
- Probar manualmente

**Reparar script:**
- Corregir error en script
- Verificar que funcione correctamente
- Probar ejecución manual

#### 5. Verificación (120 minutos)

**Probar script reparado:**
```bash
./scripts/backup_postgres.sh
```

**Verificar que se cree backup:**
```bash
ls -lh ./backs/nexorux_prod_*.sql.gz
```

#### 6. Comunicación

**Notificar a stakeholders:**
- "El proceso de backup automático ha fallado"
- "Hemos realizado backup manual"
- "Estamos reparando el script automático"

**Actualizar estado:**
- Actualizar cuando script esté reparado
- Actualizar cuando backup automático funcione

#### 7. Post-Incidente

**Documentar incidente:**
- Registrar causa del fallo
- Documentar reparación
- Documentar backup manual realizado

**Implementar medidas preventivas:**
- Implementar alertas de fallo de backup
- Implementar monitoreo de espacio en disco
- Implementar verificación de integridad de backup

---

## Runbook: Deploy Falló

### Severidad: ALTA
### Tiempo de respuesta objetivo: 1 hora

### Síntomas
- Error al ejecutar docker-compose up
- Error al ejecutar migraciones
- Servicio no inicia después de deploy
- Rollback necesario

### Impacto
- **Usuarios:** Sistema no actualizado o no disponible
- **Operaciones:** Sistema no actualizado o no disponible
- **Negocio:** Impacto en acceso a nuevas funcionalidades

### Pasos de Mitigación

#### 1. Diagnóstico Inicial (0-10 minutos)

**Verificar estado anterior:**
```bash
# Verificar versión anterior
git log --oneline -10
```

**Verificar Docker Compose:**
```bash
docker-compose config
docker-compose ps
```

**Verificar migraciones:**
```bash
docker-compose exec backend alembic current
docker-compose exec backend alembic heads
```

**Verificar logs:**
```bash
docker-compose logs backend
docker-compose logs postgres
```

#### 2. Rollback (10-30 minutos)

**SI es posible rollback:**
```bash
# Rollback a versión anterior
git checkout <commit-anterior>
docker-compose down
docker-compose up -d
```

**Verificar que funcione:**
```bash
curl http://localhost:8000/health
```

#### 3. Investigación (30-60 minutos)

**SI rollback no es posible:**

**Verificar cambios en código:**
```bash
git diff HEAD~1
```

**Verificar cambios en migraciones:**
```bash
git diff HEAD~1 alembic/versions/
```

**Identificar causa del fallo:**
- ¿Cambio en código rompió algo?
- ¿Migración incompatible?
- ¿Cambio en configuración?

#### 4. Reparación (60-120 minutos)

**Corregir error en código:**
- Revertir cambio problemático
- Probar fix localmente
- Ejecutar tests

**Corregir migración:**
- Crear nueva migración
- Revertir migración problemática
- Probar en desarrollo

**Corregir configuración:**
- Revertir cambio problemático
- Verificar variables de entorno
- Probar con configuración anterior

#### 5. Redeploy (120-240 minutos)

**Una vez corregido:**
```bash
git add .
git commit -m "Fix deploy issue"
git push

# CI/CD se ejecutará automáticamente
# O deploy manual
docker-compose down
docker-compose pull
docker-compose up -d
```

**Verificar deploy:**
```bash
curl http://localhost:8000/health
```

#### 6. Verificación (240 minutos)

**Verificar funcionalidad:**
- Probar login
- Probar operaciones críticas
- Verificar que todo funcione

**Verificar datos:**
- Verificar que datos estén intactos
- Verificar que no haya pérdida de datos

#### 7. Comunicación

**Notificar a stakeholders:**
- "El deploy ha fallado"
- "Estamos investigando y corrigiendo"
- "Tiempo estimado: 1 hora"

**Actualizar estado:**
- Actualizar cuando se haya identificado la causa
- Actualizar cuando se haya corregido
- Actualizar cuando se haya redeployado

#### 8. Post-Incidente

**Documentar incidente:**
- Registrar causa del fallo
- Documentar corrección aplicada
- Documentar tiempo de resolución

**Implementar medidas preventivas:**
- Mejorar pruebas en CI/CD
- Implementar más tests de integración
- Implementar staging environment
- Implementar canary deployments

---

## Conclusión

Los runbooks de incidentes deben revisarse y actualizados regularmente para reflejar:
- Cambios en la arquitectura
- Nuevos tipos de incidentes
- Lecciones aprendidas de incidentes pasados
- Mejoras en procesos de mitigación

**Contacto de emergencia:**
- **Email:** emergency@nexorux.erp
- **Teléfono:** [número de teléfono]
- **Slack:** #incidents

---

**Versión de los runbooks:** 1.0  
**Última actualización:** 2026-08-13  
**Sistema:** NEXORUX ERP v0.1.0
