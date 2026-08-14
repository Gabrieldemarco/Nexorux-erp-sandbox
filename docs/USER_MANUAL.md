# NEXORUX ERP - Manual de Usuario

**Versión:** 1.0  
**Fecha:** 2026-08-13  
**Para:** Usuarios finales del sistema NEXORUX ERP

---

## Índice

1. [Introducción](#1-introducción)
2. [Primeros Pasos](#2-primeros-pasos)
3. [Dashboard](#3-dashboard)
4. [Gestión de Tenants](#4-gestión-de-tenants)
5. [Gestión de Empresas](#5-gestión-de-empresas)
6. [Gestión de Usuarios](#6-gestión-de-usuarios)
7. [Gestión de Clientes](#7-gestión-de-clientes)
8. [Gestión de Proveedores](#8-gestión-de-proveedores)
9. [Gestión de Productos](#9-gestión-de-productos)
10. [Gestión de Inventario](#10-gestión-de-inventario)
11. [Punto de Venta (POS)](#11-punto-de-venta-pos)
12. [Facturación](#12-facturación)
13. [Pagos y Cuenta Corriente](#13-pagos-y-cuenta-corriente)
14. [Reportes](#14-reportes)
15. [Configuración Fiscal](#15-configuración-fiscal)
16. [Certificados Digitales](#16-certificados-digitales)
17. [Configuración de Impuestos](#17-configuración-de-impuestos)
18. [Auditoría](#18-auditoría)
19. [Solución de Problemas](#19-solución-de-problemas)
20. [Preguntas Frecuentes](#20-preguntas-frecuentes)

---

## 1. Introducción

### 1.1 ¿Qué es NEXORUX ERP?

NEXORUX ERP es un sistema de planificación de recursos empresariales multiempresa diseñado específicamente para el mercado uruguayo. Incluye:

- **Gestión multiempresa:** Administre múltiples empresas desde una sola plataforma
- **Facturación electrónica (CFE):** Emisión de comprobantes fiscales electrónicos según normativa DGI
- **Control de inventario:** Gestión completa de stock y movimientos
- **Punto de venta profesional:** Sistema de caja para operaciones diarias
- **Gestión de proveedores:** Control de compras y entradas de mercadería
- **Cuenta corriente:** Seguimiento de saldos y cobros de clientes
- **Reportes:** Análisis y estadísticas de operaciones

### 1.2 Requisitos del Sistema

**Navegadores compatibles:**
- Google Chrome (recomendado)
- Mozilla Firefox
- Microsoft Edge
- Safari

**Conexión a internet:** Requerida para acceso al sistema

### 1.3 Seguridad

- **Contraseña:** Mínimo 8 caracteres, recomendado incluir mayúsculas, minúsculas y números
- **Bloqueo:** Después de 5 intentos fallidos de login
- **Sesión:** Cierra automáticamente después de 30 minutos de inactividad
- **Recuperación:** Recuperación de contraseña por email

---

## 2. Primeros Pasos

### 2.1 Registro

1. Acceda a la URL del sistema
2. Haga clic en "Registrarse"
3. Complete el formulario:
   - **Email:** Su dirección de correo electrónico
   - **Contraseña:** Su contraseña segura
   - **Confirmar contraseña:** Repita su contraseña
   - **Nombre:** Su nombre completo
   - **RUT:** Su número de RUT (si aplica)
4. Haga clic en "Crear cuenta"

### 2.2 Inicio de Sesión

1. En la página de login, ingrese:
   - **Email:** Su email registrado
   - **Contraseña:** Su contraseña
2. Haga clic en "Iniciar sesión"

### 2.3 Recuperación de Contraseña

Si olvidó su contraseña:

1. Haga clic en "¿Olvidó su contraseña?"
2. Ingrese su email registrado
3. Recibirá un email con instrucciones para restablecerla
4. Siga el enlace en el email y cree una nueva contraseña

### 2.4 Primer Acceso

Al acceder por primera vez:

1. Complete su perfil en "Perfil"
2. Verifique su información de contacto
3. Configure sus preferencias de idioma y zona horaria

---

## 3. Dashboard

### 3.1 Vista General

El Dashboard muestra un resumen de las operaciones del día:

- **Total Tenants:** Número de empresas activas
- **Total Companies:** Número de empresas en el sistema
- **Total Users:** Número de usuarios activos
- **Ventas del día:** Total de ventas del día actual
- **CFE emitidos:** Número de comprobantes fiscales emitidos
- **Stock bajo:** Productos con stock bajo el mínimo

### 3.2 Navegación

El menú principal permite acceder a:

- **Dashboard:** Vista general del sistema
- **Tenants:** Gestión de tenants (multiempresa)
- **Companies:** Gestión de empresas
- **Usuarios:** Gestión de usuarios y permisos
- **Clientes:** Gestión de clientes
- **Proveedores:** Gestión de proveedores
- **Productos:** Gestión de productos y servicios
- **Inventario:** Control de stock y movimientos
- **POS:** Punto de venta
- **Facturación:** Gestión de facturas y CFE
- **Pagos:** Gestión de pagos y cuenta corriente
- **Reportes:** Estadísticas y reportes
- **Configuración Fiscal:** Configuración de parámetros fiscales
- **Certificados:** Gestión de certificados digitales
- **Impuestos:** Configuración de tasas impositivas
- **Auditoría:** Registro de todas las operaciones

---

## 4. Gestión de Tenants

### 4.1 Crear Tenant

1. Vaya a "Tenants"
2. Haga clic en "Add Tenant"
3. Complete el formulario:
   - **Nombre:** Nombre del tenant (ej. "Empresa Principal")
   - **Estado:** Active (activo) o Suspended (suspendido)
   - **Configuración:** Configuración adicional en formato JSON
4. Haga clic en "Guardar"

### 4.2 Listar Tenants

La lista de tenants muestra:
- **Nombre:** Nombre del tenant
- **Estado:** Active o Suspended
- **Fecha de creación:** Fecha en que se creó el tenant
- **Acciones:** Editar, Eliminar

### 4.3 Editar Tenant

1. Haga clic en "Edit" en el tenant deseado
2. Modifique los campos necesarios
3. Haga clic en "Guardar"

### 4.4 Eliminar Tenant

⚠️ **Precaución:** Eliminar un tenant eliminará todos los datos asociados (empresas, usuarios, clientes, etc.)

1. Haga clic en "Delete" en el tenant deseado
2. Confirme la eliminación

---

## 5. Gestión de Empresas

### 5.1 Crear Empresa

1. Vaya a "Companies"
2. Haga clic en "Add Company"
3. Complete el formulario:
   - **Tenant:** Seleccione el tenant al que pertenece
   - **Razón Social:** Nombre legal de la empresa
   - **Nombre Comercial:** Nombre con el que se conoce la empresa
   - **RUT:** Número de RUT de la empresa
   - **Dirección Fiscal:** Dirección fiscal completa
   - **Teléfono:** Número de teléfono
   - **Email:** Email de contacto
   - **Sitio Web:** Sitio web (opcional)
   - **País:** Uruguay (por defecto)
   - **Departamento:** Departamento (ej. Montevideo)
   - **Localidad:** Localidad (ej. Montevideo)
   - **Moneda:** UYU (peso uruguayo) por defecto
   - **Régimen Tributario:** IVA, IVA Mínimo, etc.
4. Haga clic en "Guardar"

### 5.2 Listar Empresas

La lista muestra:
- **Razón Social:** Nombre legal de la empresa
- **RUT:** Número de RUT
- **Email:** Email de contacto
- **Estado:** Estado de la empresa
- **Acciones:** Editar, Eliminar

### 5.3 Editar Empresa

1. Haga clic en "Edit" en la empresa deseada
2. Modifique los campos necesarios
3. Haga clic en "Guardar"

---

## 6. Gestión de Usuarios

### 6.1 Crear Usuario

1. Vaya a "Usuarios"
2. Haga clic en "Add User"
3. Complete el formulario:
   - **Email:** Email del usuario
   - **Contraseña:** Contraseña temporal
   - **Nombre:** Nombre del usuario
   - **Apellido:** Apellido del usuario
   - **Empresa:** Seleccione la empresa
   - **Rol:** Seleccione el rol (Super Admin, Admin, Vendedor, Contador, etc.)
4. Haga clic en "Guardar"

### 6.2 Roles y Permisos

**Roles disponibles:**
- **SUPER_ADMIN:** Acceso total al sistema
- **TENANT_ADMIN:** Administrador de tenant
- **ADMIN:** Administrador de empresa
- **ACCOUNTANT:** Contador
- **SALES:** Vendedor
- **PURCHASES:** Compras
- **WAREHOUSE:** Depósito
- **CASHIER:** Cajero
- **VIEWER:** Solo lectura

### 6.3 Cambiar Contraseña

1. Vaya a "Perfil"
2. Haga clic en "Cambiar contraseña"
3. Ingrese su contraseña actual
4. Ingrese la nueva contraseña
5. Confirme la nueva contraseña
6. Haga clic en "Guardar"

---

## 7. Gestión de Clientes

### 7.1 Crear Cliente

1. Vaya a "Clientes"
2. Haga clic en "Add Customer"
3. Complete el formulario:
   - **Tipo de Documento:** CI, RUC, NIE, Otro, Pasaporte, DNI, NIFE
   - **Número de Documento:** Número de documento
   - **Razón Social:** Nombre legal (para empresas)
   - **Nombre Comercial:** Nombre comercial
   - **Dirección:** Dirección completa
   - **Email:** Email de contacto
   - **Teléfono:** Número de teléfono
   - **País:** Uruguay (por defecto)
   - **Departamento:** Departamento
   - **Localidad:** Localidad
   - **Límite de Crédito:** Límite de crédito (opcional)
   - **Estado:** Active o Inactive
4. Haga clic en "Guardar"

### 7.2 Listar Clientes

La lista muestra:
- **Nombre:** Nombre del cliente
- **Documento:** Tipo y número de documento
- **Email:** Email de contacto
- **Teléfono:** Número de teléfono
- **Estado:** Active o Inactive
- **Acciones:** Editar, Eliminar, Ver cuenta corriente

### 7.3 Cuenta Corriente del Cliente

1. Haga clic en "Cuenta Corriente" en el cliente deseado
2. Verá:
   - **Saldo actual:** Saldo de la cuenta corriente
   - **Vencido:** Monto vencido
   - **Límite de crédito:** Límite asignado
   - **Facturas abiertas:** Facturas pendientes de pago
   - **Historial de cobros:** Pagos realizados

---

## 8. Gestión de Proveedores

### 8.1 Crear Proveedor

1. Vaya a "Proveedores"
2. Haga clic en "Add Supplier"
3. Complete el formulario similar al de clientes
4. Haga clic en "Guardar"

### 8.2 Entradas de Proveedor

Para registrar entradas de mercadería:

1. Vaya a "Entradas de Proveedor"
2. Haga clic en "Add Purchase Receipt"
3. Complete el formulario:
   - **Proveedor:** Seleccione el proveedor
   - **Depósito:** Seleccione el depósito de destino
   - **Fecha:** Fecha de la entrada
   - **Productos:** Agregue los productos recibidos
   - **Cantidad:** Cantidad recibida
   - **Costo unitario:** Costo unitario
4. Haga clic en "Guardar"

Esto actualizará automáticamente el stock del depósito.

---

## 9. Gestión de Productos

### 9.1 Crear Producto

1. Vaya a "Productos"
2. Haga clic en "Add Product"
3. Complete el formulario:
   - **SKU:** Código único del producto
   - **Código:** Código alternativo
   - **Nombre:** Nombre del producto
   - **Descripción:** Descripción detallada
   - **Categoría:** Seleccione la categoría
   - **Unidad:** Unidad de medida (ej. unidad, kg, litro)
   - **Precio:** Precio de venta
   - **Costo:** Costo del producto
   - **Tasa de IVA:** Tasa impositiva (por defecto 22%)
   - **Estado:** Active o Inactive
4. Haga clic en "Guardar"

### 9.2 Categorías de Productos

1. Vaya a "Categorías"
2. Haga clic en "Add Category"
3. Complete el formulario:
   - **Nombre:** Nombre de la categoría
   - **Descripción:** Descripción de la categoría
   - **Categoría padre:** Si es subcategoría
4. Haga clic en "Guardar"

### 9.3 Listas de Precios

1. Vaya a "Listas de Precios"
2. Haga clic en "Add Price List"
3. Complete el formulario:
   - **Nombre:** Nombre de la lista de precios
   - **Moneda:** Moneda de la lista
   - **Vigencia:** Fecha de inicio y fin
   - **Productos:** Agregue productos con sus precios
4. Haga clic en "Guardar"

---

## 10. Gestión de Inventario

### 10.1 Depósitos

1. Vaya a "Depósitos"
2. Haga clic en "Add Warehouse"
3. Complete el formulario:
   - **Nombre:** Nombre del depósito
   - **Ubicación:** Ubicación física
   - **Estado:** Active o Inactive
4. Haga clic en "Guardar"

### 10.2 Movimientos de Stock

Los movimientos de stock se registran automáticamente cuando:

- **Entradas de proveedor:** Stock aumenta
- **Ventas pagadas/emitidas:** Stock disminuye
- **Notas de crédito (102/112):** Stock aumenta (devolución)
- **Ajustes manuales:** Ajustes manuales de stock

### 10.3 Consultar Stock

1. Vaya a "Movimientos de Stock"
2. Verá el historial de movimientos
3. Filtre por:
   - **Depósito:** Depósito específico
   - **Producto:** Producto específico
   - **Tipo de movimiento:** Entrada, Salida, Ajuste
   - **Fecha:** Rango de fechas

### 10.4 Stock Bajo

Los productos con stock bajo el mínimo aparecen en:
- Dashboard (alerta de stock bajo)
- Reportes de inventario

---

## 11. Punto de Venta (POS)

### 11.1 Interfaz del POS

El POS cuenta con:

- **Dos columnas:** Productos a la izquierda, ticket a la derecha
- **Buscador:** Buscar productos por SKU, nombre o código
- **Medios de pago:** Efectivo, transferencia, tarjeta
- **Cálculo de vuelto:** Automático
- **Atajos de teclado:**
  - **F1:** Nueva venta
  - **F2:** Buscar producto
  - **F4:** Poner en espera
  - **F5:** Pago efectivo
  - **F6:** Pago transferencia
  - **F7:** Pago tarjeta
  - **F9:** Cobrar
  - **F11:** Modo caja (fullscreen)
  - **Esc:** Vaciar ticket

### 11.2 Realizar una Venta

1. Acceda al POS
2. Busque el producto (por SKU, nombre o código)
3. Ingrese la cantidad
4. El producto se agrega al ticket
5. Repita para agregar más productos
6. Seleccione el medio de pago
7. Haga clic en "Cobrar" (F9)
8. Se generará la factura automáticamente
9. Se imprimirá el ticket (si está configurado)

### 11.3 Modo Caja

Para usar el POS en modo caja (pantalla completa):

1. Presione **F11** para entrar en modo caja
2. El menú se oculta para maximizar la pantalla
3. Presione **F11** nuevamente para salir del modo caja

### 11.4 Ticket en Espera

Para poner un ticket en espera:

1. Presione **F4** mientras tiene productos en el ticket
2. El ticket se guarda en espera
3. Puede continuar con otra venta
4. Para recuperar el ticket en espera, selecciónelo de la lista

### 11.5 Resumen del Día

1. En el POS, haga clic en "Resumen del Día"
2. Verá:
   - **Total ventas:** Total del día
   - **Ventas por medio de pago:** Desglose por efectivo, transferencia, tarjeta
   - **Productos más vendidos:** Ranking de productos
   - **Operaciones:** Número de transacciones

---

## 12. Facturación

### 12.1 Crear Factura

1. Vaya a "Facturación"
2. Haga clic en "Add Invoice"
3. Complete el formulario:
   - **Cliente:** Seleccione el cliente
   - **Tipo de CFE:** e-Factura (111) o e-Ticket (101)
   - **Serie:** Serie de numeración
   - **Fecha:** Fecha de emisión
   - **Productos:** Agregue productos
   - **Cantidad:** Cantidad
   - **Precio unitario:** Precio unitario
   - **Descuento:** Porcentaje de descuento (opcional)
4. Haga clic en "Guardar"

### 12.2 Tipos de CFE

**e-Factura (111, 112, 113):**
- Para operaciones con RUC (contribuyentes)
- Receptor obligatorio con RUC

**e-Ticket (101, 102, 103):**
- Para consumo final
- Receptor opcional (obligatorio si supera tope)

**Notas de Crédito (102, 112):**
- Para devoluciones o anulaciones
- Referencia a la factura original

**Notas de Débito (103, 113):**
- Para ajustes al alza
- Referencia a la factura original

### 12.3 Estados de Factura

- **Draft:** Borrador
- **Validating:** Validando
- **Generated:** Generada
- **Queued:** En cola para envío
- **Sent:** Enviada a DGI
- **Response Received:** Respuesta recibida
- **Accepted:** Aceptada por DGI
- **Rejected:** Rechazada por DGI
- **Finalized:** Finalizada
- **Cancelled:** Cancelada

### 12.4 Emitir CFE

Para emitir un comprobante fiscal electrónico:

1. Cree la factura como se indica arriba
2. El sistema genera automáticamente el CFE
3. El CFE se firma con el certificado digital
4. Se envía a DGI (si está configurado)
5. Se genera la representación gráfica (PDF)

### 12.5 Consultar Estado de CFE

1. Vaya a "Documentos Fiscales"
2. Haga clic en el CFE deseado
3. Verá:
   - **Estado:** Estado actual del CFE
   - **CAE:** Número de CAE (si fue aceptado)
   - **Respuesta DGI:** Respuesta de DGI
   - **XML:** XML del CFE
   - **PDF:** Representación gráfica

---

## 13. Pagos y Cuenta Corriente

### 13.1 Registrar Pago

1. Vaya a "Pagos"
2. Haga clic en "Add Payment"
3. Complete el formulario:
   - **Cliente:** Seleccione el cliente
   - **Factura:** Seleccione la factura a pagar
   - **Monto:** Monto del pago
   - **Medio de pago:** Efectivo, transferencia, tarjeta, cheque
   - **Fecha:** Fecha del pago
   - **Referencia:** Número de referencia (opcional)
4. Haga clic en "Guardar"

El pago se registrará y actualizará:
- La factura se marcará como "Pagada" si el pago cubre el total
- La cuenta corriente del cliente se actualizará

### 13.2 Cuenta Corriente

Para ver la cuenta corriente de un cliente:

1. Vaya a "Cuenta Corriente"
2. Seleccione el cliente
3. Verá:
   - **Saldo actual:** Saldo de la cuenta
   - **Vencido:** Monto vencido
   - **Límite de crédito:** Límite asignado
   - **Facturas abiertas:** Facturas pendientes
   - **Historial de cobros:** Pagos realizados

### 13.3 Saldo de Cuenta Corriente

El saldo se calcula como:

```
Saldo = Facturas que afectan cuenta corriente - Pagos completados
```

Las notas de crédito restan del saldo.

---

## 14. Reportes

### 14.1 Reportes Disponibles

- **Ventas del día:** Resumen de ventas del día actual
- **Ventas del mes:** Resumen de ventas del mes actual
- **Ventas por período:** Ventas en un rango de fechas
- **CFE emitidos:** Resumen de comprobantes fiscales emitidos
- **Stock:** Estado actual del inventario
- **Movimientos de stock:** Historial de movimientos
- **Cuentas por cobrar:** Saldo de cuentas por cobrar
- **Cuentas por pagar:** Saldo de cuentas por pagar
- **Caja:** Estado de caja
- **Rentabilidad:** Análisis de rentabilidad

### 14.2 Generar Reporte

1. Vaya a "Reportes"
2. Seleccione el tipo de reporte
3. Configure los filtros:
   - **Fecha:** Rango de fechas
   - **Cliente:** Cliente específico (opcional)
   - **Producto:** Producto específico (opcional)
4. Haga clic en "Generar"
5. El reporte se mostrará en pantalla
6. Puede exportar a:
   - **PDF:** Formato PDF
   - **CSV:** Formato CSV
   - **Excel:** Formato Excel (cuando disponible)

---

## 15. Configuración Fiscal

### 15.1 Configuración General

1. Vaya a "Configuración Fiscal"
2. Configure:
   - **Ambiente DGI:** Testing, Homologación, Producción
   - **URL Web Service DGI:** URL del servicio DGI
   - **Tiempo de espera:** Timeout para comunicaciones DGI
   - **Número de reintentos:** Número de reintentos automáticos

### 15.2 Series de Numeración

1. Vaya a "Series"
2. Haga clic en "Add Series"
3. Complete el formulario:
   - **Tipo de CFE:** Tipo de comprobante
   - **Prefijo:** Prefijo de la serie (ej. A, B, C)
   - **Número actual:** Número actual de la serie
4. Haga clic en "Guardar"

### 15.3 CAE (Constancia de Autorización de Emisión)

Para agregar un CAE:

1. Descargue el archivo CAE XML desde el portal de DGI
2. Vaya a "CAE"
3. Haga clic en "Add CAE"
4. Suba el archivo CAE XML
5. El sistema:
   - Validará el CAE
   - Extraerá el rango de numeración
   - Configurará la vigencia
   - Habilitará la emisión para ese tipo de CFE

---

## 16. Certificados Digitales

### 16.1 Agregar Certificado

⚠️ **Importante:** Los certificados digitales se obtienen de proveedores autorizados (ABITAB, Correo Uruguayo, ANTEL).

1. Vaya a "Certificados"
2. Haga clic en "Add Certificate"
3. Complete el formulario:
   - **Nombre:** Nombre del certificado
   - **Tipo:** Nominado, Innominado, Avanzado
   - **Archivo de certificado:** Suba el archivo .pem o .crt
   - **Archivo de clave privada:** Suba el archivo .key
   - **Contraseña:** Contraseña del certificado (se cifrará)
   - **Ambiente:** Testing, Homologación, Producción
4. Haga clic en "Guardar"

### 16.2 Tipos de Certificados

**Nominado:**
- Incluye nombre y documento del solicitante
- Trazabilidad hasta el solicitante
- Clave RSA 1024 bits

**Innominado:**
- No incluye información del solicitante
- Pensado para sistemas automatizados
- Clave RSA 1024 bits

**Avanzado:**
- Mayor seguridad
- Clave RSA 2048 bits

### 16.3 Validez

Los certificados tienen una validez de 1 o 2 años. El sistema alertará cuando el certificado esté próximo a vencer.

---

## 17. Configuración de Impuestos

### 17.1 Configurar Tasa Impositiva

1. Vaya a "Impuestos"
2. Haga clic en "Add Tax Configuration"
3. Complete el formulario:
   - **Nombre:** Nombre de la tasa (ej. IVA 22%)
   - **Tasa:** Porcentaje (ej. 22 para 22%)
   - **Descripción:** Descripción de la tasa
   - **Vigencia desde:** Fecha desde la cual aplica
   - **Vigencia hasta:** Fecha hasta la cual aplica (opcional)
4. Haga clic en "Guardar"

### 17.2 Tasas Preconfiguradas

El sistema incluye tasas preconfiguradas:
- **IVA 22%:** Tasa general de IVA
- **IVA 10%:** Tasa reducida de IVA
- **IVA 0%:** Tasa exenta
- **IVA Mínimo:** Tasa para contribuyentes de IVA Mínimo

---

## 18. Auditoría

### 18.1 Registro de Auditoría

El sistema registra todas las operaciones:

- **Login:** Inicios de sesión
- **Logout:** Cierres de sesión
- **Creación:** Creación de registros
- **Modificación:** Modificación de registros
- **Eliminación:** Eliminación de registros
- **Emisión:** Emisión de facturas
- **Anulación:** Anulación de documentos
- **Cambios de configuración:** Cambios en configuración
- **Cambios de permisos:** Cambios en permisos
- **Operaciones CFE:** Operaciones de facturación electrónica

### 18.2 Consultar Auditoría

1. Vaya a "Auditoría"
2. Filtre por:
   - **Usuario:** Usuario específico
   - **Entidad:** Tipo de entidad (cliente, producto, factura, etc.)
   - **Acción:** Tipo de acción
   - **Fecha:** Rango de fechas
3. Verá el historial de operaciones

### 18.3 Detalle de Auditoría

Cada registro de auditoría incluye:
- **Usuario:** Usuario que realizó la acción
- **IP:** Dirección IP desde la cual se realizó
- **Fecha y hora:** Timestamp de la acción
- **Entidad:** Tipo de entidad afectada
- **ID de entidad:** ID del registro afectado
- **Acción:** Tipo de acción
- **Valores anteriores:** Valores antes del cambio
- **Valores nuevos:** Valores después del cambio

---

## 19. Solución de Problemas

### 19.1 No puedo iniciar sesión

**Problema:** No puedo acceder al sistema

**Soluciones:**
1. Verifique que el email y contraseña sean correctos
2. Si olvidó su contraseña, use "¿Olvidó su contraseña?"
3. Verifique que su cuenta no esté bloqueada (5 intentos fallidos)
4. Contacte al administrador si el problema persiste

### 19.2 El sistema está lento

**Problema:** El sistema responde lentamente

**Soluciones:**
1. Verifique su conexión a internet
2. Cierre otras pestañas del navegador
3. Limpie el caché del navegador
4. Intente con otro navegador
5. Contacte al soporte si el problema persiste

### 19.3 No puedo emitir facturas

**Problema:** Las facturas no se emiten

**Soluciones:**
1. Verifique que tenga un CAE vigente para el tipo de CFE
2. Verifique que el certificado digital esté configurado
3. Verifique que la serie de numeración tenga números disponibles
4. Consulte el estado del CFE en "Documentos Fiscales"
5. Contacte al soporte si el problema persiste

### 19.4 Error al enviar CFE a DGI

**Problema:** El CFE fue rechazado por DGI

**Soluciones:**
1. Consulte el motivo de rechazo en "Documentos Fiscales"
2. Verifique que los datos del CFE sean correctos
3. Verifique que el certificado digital sea válido
4. Consulte la documentación de DGI para requisitos específicos
5. Contacte al soporte si el problema persiste

### 19.5 Stock no se actualiza

**Problema:** El stock no se actualiza después de una venta

**Soluciones:**
1. Verifique que la venta esté en estado "Pagada" o "Emitida"
2. Verifique que el producto tenga suficiente stock
3. Consulte los movimientos de stock
4. Contacte al soporte si el problema persiste

---

## 20. Preguntas Frecuentes

### 20.1 ¿Qué es un CFE?

Un CFE (Comprobante Fiscal Electrónico) es un documento fiscal electrónico que tiene la misma validez legal que los documentos en papel, emitido según la normativa de DGI.

### 20.2 ¿Qué es un CAE?

Un CAE (Constancia de Autorización de Emisión) es un archivo XML firmado por DGI que autoriza la emisión de CFE dentro de un rango de numeración específico.

### 20.3 ¿Cuánto tiempo dura un CAE?

Un CAE tiene una vigencia de 2 años desde su fecha de emisión.

### 20.4 ¿Qué hago si se agota el rango de CAE?

Debe solicitar un nuevo CAE al portal de DGI en "Servicios en línea / Constancias / eFactura - Constancia Comprobante Fiscal Electrónico - Solicitud".

### 20.5 ¿Puedo emitir facturas en papel?

Solo en casos de contingencia justificada. La normativa DGI establece procedimientos específicos para contingencia.

### 20.6 ¿Qué es contingencia?

Contingencia es la situación en la que no se puede emitir comprobantes electrónicos por indisponibilidad del sistema o de DGI. Existen procedimientos específicos para estos casos.

### 20.7 ¿Cómo obtengo un certificado digital?

Los certificados digitales se obtienen de proveedores autorizados: ABITAB, Administración Nacional de Correos, o ANTEL.

### 20.8 ¿Cuánto cuesta un certificado digital?

El costo varía según el tipo de empresa y la vigencia (1 o 2 años). Consulte con el proveedor autorizado.

### 20.9 ¿Puedo usar el mismo certificado para varias empresas?

No, cada empresa debe tener su propio certificado digital.

### 20.10 ¿Qué pasa si vence mi certificado digital?

El sistema alertará cuando el certificado esté próximo a vencer. Debe obtener un nuevo certificado antes de que venza el actual.

### 20.11 ¿Puedo anular una factura ya emitida?

Sí, puede emitir una nota de crédito que haga referencia a la factura original.

### 20.12 ¿Cómo recupero una factura anulada?

Una factura anulada mediante nota de crédito no se puede recuperar. Debe emitir una nueva factura.

### 20.13 ¿Puedo cambiar el tipo de CFE después de crear la factura?

No, el tipo de CFE no se puede cambiar después de crear la factura. Debe crear una nueva factura con el tipo correcto.

### 20.14 ¿Qué es el modo caja en el POS?

El modo caja es una configuración del POS que oculta el menú y maximiza la pantalla para uso en cajas registradoras.

### 20.15 ¿Cómo salgo del modo caja?

Presione **F11** nuevamente para salir del modo caja.

### 20.16 ¿Puedo usar el POS sin mouse?

Sí, el POS tiene atajos de teclado para todas las operaciones principales.

### 20.17 ¿Qué hago si cometo un error en una venta?

Si la venta aún no está cobrada, puede vaciar el ticket con **Esc**. Si ya está cobrada, debe emitir una nota de crédito.

### 20.18 ¿Cómo veo el resumen del día?

En el POS, haga clic en "Resumen del Día" para ver el resumen de operaciones del día.

### 20.19 ¿Puedo exportar reportes?

Sí, puede exportar reportes a PDF, CSV o Excel (cuando disponible).

### 20.20 ¿Dónde se almacenan los documentos fiscales?

Los documentos fiscales (XML, PDF) se almacenan de forma segura en el sistema y están disponibles para consulta y descarga.

---

## Soporte

Para soporte técnico, contáctese a:

- **Email:** soporte@nexorux.erp
- **Teléfono:** [número de teléfono]
- **Horario:** Lunes a viernes, 9:00 - 18:00

---

**Versión del manual:** 1.0  
**Última actualización:** 2026-08-13  
**Sistema:** NEXORUX ERP v0.1.0
