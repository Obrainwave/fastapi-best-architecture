"""Purpose: Seed development and demonstration data."""

import asyncio
import os
import sys

from sqlalchemy import text

# Ensure the app module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.session import SessionLocal
from migrations.seeders.plans import seed_plans

from migrations.seeders.currencies import seed_currencies
from migrations.seeders.super_admin import seed_super_admin


async def get_org_id_by_email(session, email: str) -> str | None:
    result = await session.execute(
        text("SELECT organization_id FROM users WHERE email = :email LIMIT 1"),
        {"email": email}
    )
    row = result.first()
    return str(row[0]) if row else None

async def main():
    print("Starting database seed...")
    async with SessionLocal() as session:
        
        print("Seeding plans and plan features...")
        await seed_plans(session)
        
        print("Seeding currencies...")
        await seed_currencies(session)
        
        print("Seeding super admin...")
        await seed_super_admin(session)
            
    print("Database seeding completed successfully.")

async def admin_seeded(session) -> bool:
    result = await session.execute(
        text("""
            SELECT 
                * 
            FROM users
            WHERE account = 'super_admin'
        """)
    )

    return result.first()

if __name__ == "__main__":
    asyncio.run(main())
