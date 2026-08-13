import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text, select
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import Request
from app.core.config import settings
from app.core.security import decode_token

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


async def get_db(request: Request) -> AsyncSession:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        tenant_guc_set = False
        try:
            if settings.RLS_TENANT_CONTEXT_ENABLED:
                tenant_id = None
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    payload = decode_token(auth_header[7:])
                    if payload and payload.get("type") == "access":
                        user_id = payload.get("sub")
                        if user_id:
                            from app.models.user import User
                            try:
                                user_uuid = uuid.UUID(str(user_id))
                            except ValueError:
                                user_uuid = None
                            if user_uuid:
                                result = await session.execute(select(User.tenant_id).where(User.id == user_uuid))
                                tenant_id = result.scalar_one_or_none()
                if tenant_id:
                    # Session-level GUC so DELETE/UPDATE still see tenant after any mid-request commit.
                    # Cleared in finally so pooled connections do not leak tenant context.
                    await session.execute(
                        text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
                        {"tenant_id": str(tenant_id)},
                    )
                    tenant_guc_set = True
            yield session
        finally:
            if tenant_guc_set:
                try:
                    # Prefer RESET so current_setting(..., missing_ok) returns NULL, not ''.
                    await session.execute(text("RESET app.current_tenant_id"))
                except Exception:
                    try:
                        await session.execute(
                            text("SELECT set_config('app.current_tenant_id', '', false)")
                        )
                    except Exception:
                        pass
            await session.close()
