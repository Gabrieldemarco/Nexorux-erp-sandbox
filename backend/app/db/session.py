import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text, select
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import Request
from app.core.config import settings
from app.core.security import decode_token
import structlog

logger = structlog.get_logger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)

Base = declarative_base()


async def set_tenant_guc(session: AsyncSession, tenant_id: uuid.UUID | str) -> None:
    """Set session-level tenant GUC for FORCE RLS (survives COMMIT)."""
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
        {"tenant_id": str(tenant_id)},
    )


async def reload_after_commit(session: AsyncSession, instance, tenant_id: uuid.UUID | str):
    """Re-apply RLS GUC after COMMIT and reload the instance.

    Under FORCE RLS, session.refresh() often fails after COMMIT even when the
    row was inserted. Prefer a SELECT with GUC set; fall back to the in-memory
    instance (expire_on_commit=False).
    """
    from sqlalchemy import inspect as sa_inspect

    if settings.RLS_TENANT_CONTEXT_ENABLED:
        await set_tenant_guc(session, tenant_id)

    mapper = sa_inspect(type(instance))
    identity = sa_inspect(instance).identity
    if not identity:
        return instance

    pk_cols = mapper.primary_key
    clause = pk_cols[0] == identity[0]
    for col, val in zip(pk_cols[1:], identity[1:]):
        clause = clause & (col == val)

    result = await session.execute(select(type(instance)).where(clause))
    loaded = result.scalar_one_or_none()
    return loaded if loaded is not None else instance



async def clear_tenant_guc(session: AsyncSession) -> None:
    """Clear tenant GUC so pooled connections do not leak context."""
    try:
        await session.execute(text("RESET app.current_tenant_id"))
    except Exception:
        try:
            await session.execute(text("SELECT set_config('app.current_tenant_id', '', false)"))
        except Exception:
            pass


async def resolve_tenant_id_from_request(session: AsyncSession, request: Request) -> uuid.UUID | None:
    """Resolve tenant for RLS from JWT (tenant_id claim or user lookup)."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    payload = decode_token(auth_header[7:])
    if not payload:
        return None
    # Access tokens always have type=access; older tokens may omit type.
    # Never use refresh tokens to set tenant context.
    if payload.get("type") == "refresh":
        return None

    raw_tenant = payload.get("tenant_id")
    if raw_tenant:
        try:
            return uuid.UUID(str(raw_tenant))
        except ValueError:
            pass

    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        user_uuid = uuid.UUID(str(user_id))
    except ValueError:
        return None

    from app.models.user import User

    result = await session.execute(select(User.tenant_id).where(User.id == user_uuid))
    return result.scalar_one_or_none()


async def get_db(request: Request) -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        tenant_guc_set = False
        try:
            if settings.RLS_TENANT_CONTEXT_ENABLED:
                tenant_id = await resolve_tenant_id_from_request(session, request)
                if tenant_id:
                    # Session-level GUC so DELETE/UPDATE still see tenant after any mid-request commit.
                    await set_tenant_guc(session, tenant_id)
                    tenant_guc_set = True
                else:
                    auth_header = request.headers.get("Authorization", "")
                    if auth_header.startswith("Bearer "):
                        logger.warning(
                            "rls_tenant_guc_not_set",
                            path=str(request.url.path),
                            reason="could_not_resolve_tenant_from_token",
                        )
            yield session
        finally:
            if tenant_guc_set:
                await clear_tenant_guc(session)
            await session.close()
