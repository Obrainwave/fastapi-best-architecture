import uuid

from sqlalchemy import text

from app.core.security import hash_password


async def seed_super_admin(session):
    # Check if a super admin already exists
    check_stmt = text("SELECT id FROM users WHERE email = :email")
    result = await session.execute(check_stmt, {"email": "admin@agropro.com"})
    
    if result.scalar_one_or_none() is None:
        user_id = uuid.uuid4()
        hashed_pw = hash_password("Secret123!")
        
        insert_user_stmt = text("""
            INSERT INTO users (id, name, email, username, password_hash, account, is_active, is_verified) 
            VALUES (CAST(:id AS UUID), :name, :email, :username, :password, :account, :is_active, :is_verified)
        """)
        
        await session.execute(insert_user_stmt, {
            "id": user_id,
            "name": "System Administrator",
            "email": "admin@email.com",
            "username": "superadmin",
            "password": hashed_pw,
            "account": "super_admin",
            "is_active": True,
            "is_verified": True
        })
        await session.commit()