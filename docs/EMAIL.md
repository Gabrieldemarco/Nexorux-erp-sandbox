# Envío de correo — Nexorux ERP

## Por qué no llega a Gmail

Si en `.env` tenés:

```env
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
```

**eso NO manda a Gmail.** Solo entrega a Mailpit local (`http://localhost:8025`) o, si falla, a `backend/storage/mail_outbox/`.

Para que el token llegue a `tuusuario@gmail.com` necesitás SMTP real (Gmail u otro).

## Requisitos

1. El correo tiene que estar **registrado** en Nexorux (el de la cuenta del usuario).
2. SMTP de Gmail con **contraseña de aplicación** (no la clave normal de Gmail).

## Configurar Gmail

1. Activá [verificación en 2 pasos](https://myaccount.google.com/security) en la cuenta que va a **enviar** el mail.
2. Creá una [contraseña de aplicación](https://myaccount.google.com/apppasswords) (16 caracteres).
3. En `backend/.env`:

```env
EMAIL_BACKEND=smtp
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USER=tuusuario@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM=tuusuario@gmail.com
PASSWORD_RESET_URL_BASE=http://localhost:3000/recover-password
```

4. Reiniciá uvicorn.
5. En Recover password usá el **mismo email registrado** en la app (ej. si el usuario es `gprepelec@gmail.com`, ese exacto).

## Probar SMTP

```powershell
cd backend
.\.venv311\Scripts\python.exe scripts\test_smtp.py tuusuario@gmail.com
```

## Alternativas locales (sin Gmail)

| Opción | Cómo |
|--------|------|
| Mailpit | `docker compose up -d mailpit` → mails en http://localhost:8025 |
| Outbox | `EMAIL_BACKEND=outbox` → archivos en `storage/mail_outbox/` |
