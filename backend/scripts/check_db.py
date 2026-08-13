import asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from app.models.company import Company
from app.models.user import User

async def main():
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async with AsyncSession(engine) as session:
        tenant_result = await session.execute(select(Tenant))
        company_result = await session.execute(select(Company))
        user_result = await session.execute(select(User))
        tenants = tenant_result.scalars().all()
        companies = company_result.scalars().all()
        users = user_result.scalars().all()
        print('tenants', len(tenants))
        print('companies', len(companies))
        print('users', len(users))
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
