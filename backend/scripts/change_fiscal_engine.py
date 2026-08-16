"""
Script administrativo para cambiar el motor fiscal de un tenant.

Uso:
    python scripts/change_fiscal_engine.py --tenant-id <uuid> --engine <engine_id> [--environment <env>]

Ejemplos:
    python scripts/change_fiscal_engine.py --tenant-id 123e4567-e89b-12d3-a456-426614174000 --engine mock_fiscal
    python scripts/change_fiscal_engine.py --tenant-id 123e4567-e89b-12d3-a456-426614174000 --engine dgi_uruguay --environment produccion
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.tenant import Tenant
from app.services.fiscal.engines.registry import get_fiscal_engine_registry


async def change_fiscal_engine(tenant_id: str, engine_id: str, environment: str = None):
    """
    Cambia el motor fiscal de un tenant.
    
    Args:
        tenant_id: ID del tenant a modificar
        engine_id: ID del nuevo motor fiscal
        environment: Entorno opcional (testing, produccion, etc.)
    """
    print(f"🔄 Cambiando motor fiscal para tenant {tenant_id}...")
    print(f"   Nuevo motor: {engine_id}")
    if environment:
        print(f"   Entorno: {environment}")
    
    # Verificar que el motor existe
    registry = get_fiscal_engine_registry()
    if not registry.has_engine(engine_id):
        print(f"❌ Error: El motor '{engine_id}' no está registrado.")
        print(f"   Motores disponibles: {list(registry.list_engines().keys())}")
        return False
    
    # Mostrar información del motor
    engine_info = registry.get_engine_info(engine_id)
    print(f"   ℹ️  Motor: {engine_info['engine_name']}")
    print(f"   ℹ️  País: {engine_info['country']}")
    print(f"   ℹ️  Autoridad: {engine_info['fiscal_authority']}")
    
    # Conectar a la base de datos
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Buscar el tenant
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            result = await db.execute(stmt)
            tenant = result.scalar_one_or_none()
            
            if not tenant:
                print(f"❌ Error: Tenant '{tenant_id}' no encontrado.")
                return False
            
            print(f"   📋 Tenant actual: {tenant.name}")
            print(f"   📋 Motor actual: {tenant.fiscal_engine_id}")
            
            # Actualizar configuración fiscal
            tenant.fiscal_engine_id = engine_id
            
            if environment:
                if not tenant.fiscal_config:
                    tenant.fiscal_config = {}
                tenant.fiscal_config["environment"] = environment
            
            await db.commit()
            
            print(f"✅ Motor fiscal actualizado exitosamente.")
            print(f"   Nuevo motor: {tenant.fiscal_engine_id}")
            print(f"   Nueva configuración: {tenant.fiscal_config}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al actualizar: {e}")
        return False
    finally:
        await engine.dispose()


async def list_available_engines():
    """Lista todos los motores fiscales disponibles."""
    registry = get_fiscal_engine_registry()
    engines = registry.list_engines()
    
    print("🔧 Motores fiscales disponibles:")
    print()
    
    for engine_id, info in engines.items():
        print(f"📌 {engine_id}")
        print(f"   Nombre: {info['engine_name']}")
        print(f"   País: {info['country']}")
        print(f"   Autoridad: {info['fiscal_authority']}")
        print(f"   Versión: {info['version']}")
        print(f"   Soporta factura electrónica: {info['supports_electronic_invoice']}")
        print(f"   Soporta notas de crédito: {info['supports_credit_note']}")
        print(f"   Soporta notas de débito: {info['supports_debit_note']}")
        print(f"   Soporta contingencia: {info['supports_contingency']}")
        print(f"   Soporta cancelación: {info['supports_cancellation']}")
        print(f"   Soporta consulta de estado: {info['supports_query_status']}")
        print(f"   Documentos soportados: {', '.join(info['supported_document_types'])}")
        print()


async def list_tenants():
    """Lista todos los tenants con su configuración fiscal."""
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            stmt = select(Tenant)
            result = await db.execute(stmt)
            tenants = result.scalars().all()
            
            print("🏢 Tenants y configuración fiscal:")
            print()
            
            for tenant in tenants:
                print(f"📋 {tenant.name} (ID: {tenant.id})")
                print(f"   Motor fiscal: {tenant.fiscal_engine_id}")
                print(f"   Configuración: {tenant.fiscal_config}")
                print()
                
    except Exception as e:
        print(f"❌ Error al listar tenants: {e}")
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description="Script administrativo para gestión de motores fiscales"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando change
    change_parser = subparsers.add_parser("change", help="Cambiar motor fiscal de un tenant")
    change_parser.add_argument("--tenant-id", required=True, help="ID del tenant")
    change_parser.add_argument("--engine", required=True, help="ID del motor fiscal")
    change_parser.add_argument("--environment", help="Entorno (testing, produccion, etc.)")
    
    # Comando list-engines
    subparsers.add_parser("list-engines", help="Listar motores fiscales disponibles")
    
    # Comando list-tenants
    subparsers.add_parser("list-tenants", help="Listar tenants y su configuración fiscal")
    
    args = parser.parse_args()
    
    if args.command == "change":
        asyncio.run(change_fiscal_engine(args.tenant_id, args.engine, args.environment))
    elif args.command == "list-engines":
        asyncio.run(list_available_engines())
    elif args.command == "list-tenants":
        asyncio.run(list_tenants())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()