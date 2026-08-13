import hashlib
import uuid
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.rbac import get_current_user_with_permissions
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.permission import Permission
from app.models.company import Company
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    PasswordChangeRequest,
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    PasswordResetRequest,
    UserCreate,
    UserProfileUpdate,
    UserResponse,
    Token,
)
import structlog

router = APIRouter()

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
PASSWORD_RESET_EXPIRES_MINUTES = 60

_login_attempts: dict[str, dict] = {}
MAX_LOGIN_ATTEMPTS = settings.LOCKOUT_MAX_ATTEMPTS
LOCKOUT_MINUTES = settings.LOCKOUT_MINUTES
_redis_lockout_client = None


def _lockout_key(identifier: str) -> str:
    return f"login_attempts:{identifier}"


def _lockout_block_key(identifier: str) -> str:
    return f"login_block:{identifier}"


def _use_redis_lockout() -> bool:
    return settings.LOCKOUT_USE_REDIS and not settings.DEBUG


async def _get_redis_lockout_client():
    global _redis_lockout_client
    if _redis_lockout_client is None:
        import redis.asyncio as aioredis

        _redis_lockout_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_lockout_client


def _record_failed_attempt(identifier: str):
    key = _lockout_key(identifier)
    now = datetime.utcnow()
    entry = _login_attempts.get(key, {"count": 0, "first_attempt": now, "locked_until": None})
    entry["count"] += 1
    if entry["count"] >= MAX_LOGIN_ATTEMPTS:
        entry["locked_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
    _login_attempts[key] = entry


def _is_locked(identifier: str) -> bool:
    entry = _login_attempts.get(_lockout_key(identifier))
    if not entry:
        return False
    if entry["count"] < MAX_LOGIN_ATTEMPTS:
        return False
    locked_until = entry.get("locked_until")
    if not locked_until:
        return False
    if datetime.utcnow() > locked_until:
        del _login_attempts[_lockout_key(identifier)]
        return False
    return True


def _clear_attempts(identifier: str):
    _login_attempts.pop(_lockout_key(identifier), None)


async def _record_failed_attempt_async(identifier: str):
    if not _use_redis_lockout():
        _record_failed_attempt(identifier)
        return
    try:
        redis_client = await _get_redis_lockout_client()
        attempts_key = _lockout_key(identifier)
        block_key = _lockout_block_key(identifier)
        count = await redis_client.incr(attempts_key)
        if count == 1:
            await redis_client.expire(attempts_key, LOCKOUT_MINUTES * 60)
        if count >= MAX_LOGIN_ATTEMPTS:
            await redis_client.set(block_key, "1", ex=LOCKOUT_MINUTES * 60)
            await redis_client.delete(attempts_key)
    except Exception as exc:
        logger.warning("lockout_redis_fallback_record", error=str(exc))
        _record_failed_attempt(identifier)


async def _is_locked_async(identifier: str) -> bool:
    if not _use_redis_lockout():
        return _is_locked(identifier)
    try:
        redis_client = await _get_redis_lockout_client()
        return await redis_client.exists(_lockout_block_key(identifier)) == 1
    except Exception as exc:
        logger.warning("lockout_redis_fallback_check", error=str(exc))
        return _is_locked(identifier)


async def _clear_attempts_async(identifier: str):
    if not _use_redis_lockout():
        _clear_attempts(identifier)
        return
    try:
        redis_client = await _get_redis_lockout_client()
        await redis_client.delete(_lockout_key(identifier), _lockout_block_key(identifier))
    except Exception as exc:
        logger.warning("lockout_redis_fallback_clear", error=str(exc))
        _clear_attempts(identifier)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_or_create_bootstrap_tenant_company(
    db: AsyncSession,
    tenant_name: str,
    company_legal_name: str,
    company_email: str | None,
):
    tenant_result = await db.execute(select(Tenant).limit(1))
    tenant_obj = tenant_result.scalar_one_or_none()
    if tenant_obj:
        company_result = await db.execute(select(Company).where(Company.tenant_id == tenant_obj.id).limit(1))
        company_obj = company_result.scalar_one_or_none()
        if company_obj:
            return tenant_obj, company_obj

        company_obj = Company(
            tenant_id=tenant_obj.id,
            legal_name=company_legal_name,
            rut="00000000K",
            country="Uruguay",
            currency="UYU",
            email=company_email,
        )
        db.add(company_obj)
        await db.flush()
        return tenant_obj, company_obj

    tenant_obj = Tenant(
        name=tenant_name,
        status="active",
        settings={},
    )
    db.add(tenant_obj)
    await db.flush()

    company_obj = Company(
        tenant_id=tenant_obj.id,
        legal_name=company_legal_name,
        rut="00000000K",
        country="Uruguay",
        currency="UYU",
        email=company_email,
    )
    db.add(company_obj)
    await db.flush()
    return tenant_obj, company_obj


async def _get_or_create_admin_role(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> Role:
    role_result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.tenant_id == tenant_id, Role.key == "admin")
        .limit(1)
    )
    role_obj = role_result.scalar_one_or_none()
    if role_obj:
        return role_obj

    role_obj = Role(
        tenant_id=tenant_id,
        name="Administrator",
        key="admin",
        description="Full access administrator role",
        is_default=True,
    )
    db.add(role_obj)
    await db.flush()
    return role_obj


async def _get_or_create_wildcard_permission(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> Permission:
    permission_result = await db.execute(
        select(Permission).where(Permission.tenant_id == tenant_id, Permission.code == "*").limit(1)
    )
    permission_obj = permission_result.scalar_one_or_none()
    if permission_obj:
        return permission_obj

    permission_obj = Permission(
        tenant_id=tenant_id,
        name="All Permissions",
        code="*",
        description="Full access wildcard permission",
    )
    db.add(permission_obj)
    await db.flush()
    return permission_obj


async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> User | None:
    if await _is_locked_async(identifier):
        logger.warning("account_lockout", identifier=identifier)
        return None

    stmt = select(User).where(
        or_(User.email == identifier, User.username == identifier)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        await _record_failed_attempt_async(identifier)
        logger.warning("login_failed", identifier=identifier)
        return None

    await _clear_attempts_async(identifier)
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cannot be used for authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    existing_email = await get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    existing_username = await get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists",
        )

    try:
        tenant_uuid = (
            user.tenant_id
            if isinstance(user.tenant_id, uuid.UUID)
            else uuid.UUID(str(user.tenant_id))
            if user.tenant_id
            else None
        )
    except (TypeError, ValueError):
        tenant_uuid = None

    try:
        company_uuid = (
            user.company_id
            if isinstance(user.company_id, uuid.UUID)
            else uuid.UUID(str(user.company_id))
            if user.company_id
            else None
        )
    except (TypeError, ValueError):
        company_uuid = None

    if not tenant_uuid or not company_uuid:
        tenant_obj, company_obj = await _get_or_create_bootstrap_tenant_company(
            db,
            tenant_name=f"{user.full_name.split()[0] if user.full_name.split() else 'Default'} Tenant",
            company_legal_name=user.full_name or "Default Company",
            company_email=user.email,
        )
        tenant_uuid = tenant_obj.id
        company_uuid = company_obj.id

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant does not exist",
        )

    company_result = await db.execute(select(Company).where(Company.id == company_uuid))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company does not exist",
        )

    if company.tenant_id != tenant.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company does not belong to the provided tenant",
        )

    password_hash = get_password_hash(user.password)
    admin_role = await _get_or_create_admin_role(db, tenant_uuid)
    wildcard_permission = await _get_or_create_wildcard_permission(db, tenant_uuid)
    if wildcard_permission not in admin_role.permissions:
        admin_role.permissions.append(wildcard_permission)
        await db.flush()

    user_obj = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        tenant_id=tenant.id,
        company_id=company.id,
        password_hash=password_hash,
        is_active=user.is_active,
        settings=user.settings or {},
    )
    db.add(user_obj)
    await db.flush()
    await db.execute(
        text(
            "INSERT INTO user_role (user_id, role_id) VALUES (:user_id, :role_id) "
            "ON CONFLICT DO NOTHING"
        ),
        {"user_id": str(user_obj.id), "role_id": str(admin_role.id)},
    )
    await db.commit()
    await db.refresh(user_obj)
    return user_obj


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.email and payload.email != current_user.email:
        existing_email = await get_user_by_email(db, payload.email)
        if existing_email and existing_email.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )
        current_user.email = payload.email

    if payload.username and payload.username != current_user.username:
        existing_username = await get_user_by_username(db, payload.username)
        if existing_username and existing_username.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists",
            )
        current_user.username = payload.username

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.settings is not None:
        current_user.settings = payload.settings

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/password", response_model=MessageResponse)
async def change_current_user_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.password_reset_token_hash = None
    current_user.password_reset_token_expires_at = None
    await db.commit()
    return {"message": "Password updated successfully"}


@router.post("/password/forgot", response_model=PasswordRecoveryResponse)
async def request_password_reset(
    payload: PasswordRecoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a reset token to the registered email, then user sets a new password."""
    from app.services.email import send_password_reset_email

    try:
        email = payload.resolved_email()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # ilike → case-insensitive match on registered email
    stmt = select(User).where(User.email.ilike(email)).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay una cuenta registrada con ese correo",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta está desactivada",
        )

    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token_hash = _hash_reset_token(reset_token)
    user.password_reset_token_expires_at = datetime.utcnow() + timedelta(
        minutes=PASSWORD_RESET_EXPIRES_MINUTES
    )
    await db.commit()

    try:
        sent = await send_password_reset_email(
            to_email=user.email, reset_token=reset_token
        )
    except Exception as exc:
        logger.exception("password_reset_email_failed", user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No se pudo enviar el correo de recuperación. "
                "Verificá la configuración SMTP o intentá más tarde."
            ),
        ) from exc

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El envío de correo no está habilitado. "
                "Configurá SMTP_ENABLED=true y SMTP_HOST."
            ),
        )

    local_delivery = settings.DEBUG and (
        (settings.EMAIL_BACKEND or "").lower() == "outbox"
        or (settings.SMTP_HOST or "") in ("127.0.0.1", "localhost", "mailpit")
    )
    return {
        "message": (
            f"Enviamos un correo a {user.email} con el token para restablecer "
            "la contraseña."
            + (
                " Modo local: abrí el archivo más nuevo en backend/storage/mail_outbox/ "
                "(ahí está el token). Para Gmail real usá smtp.gmail.com — docs/EMAIL.md."
                if local_delivery
                else " Revisá la bandeja de entrada y spam."
            )
        )
    }


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash = _hash_reset_token(payload.token)
    stmt = select(User).where(User.password_reset_token_hash == token_hash).limit(1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    expires = getattr(user, "password_reset_token_expires_at", None) if user else None
    if not user or expires is None or expires <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o vencido",
        )

    user.password_hash = get_password_hash(payload.new_password)
    user.password_reset_token_hash = None
    user.password_reset_token_expires_at = None
    await db.commit()
    return {"message": "Contraseña actualizada. Ya podés ingresar con la nueva clave."}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, username, or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "type": "access"}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "type": "access"}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user_with_permissions),
) -> User:
    return current_user
