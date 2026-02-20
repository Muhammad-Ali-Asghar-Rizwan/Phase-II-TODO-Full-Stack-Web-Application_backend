"""Migration script to add missing columns to tasks table."""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    """Add missing columns to tasks table."""
    from db import async_engine
    
    async with async_engine.connect() as conn:
        # Get all existing columns
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks'
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        columns_to_add = []
        
        if 'status' not in existing_columns:
            columns_to_add.append(("status", "VARCHAR(20) DEFAULT 'pending'"))
        
        if 'completed' not in existing_columns:
            columns_to_add.append(("completed", "BOOLEAN DEFAULT FALSE"))
        
        if 'due_date' not in existing_columns:
            columns_to_add.append(("due_date", "TIMESTAMP"))
        
        if 'priority' not in existing_columns:
            columns_to_add.append(("priority", "VARCHAR(20) DEFAULT 'medium'"))
        
        if 'updated_at' not in existing_columns:
            columns_to_add.append(("updated_at", "TIMESTAMP DEFAULT NOW()"))
        
        if not columns_to_add:
            print("[OK] All columns already exist!")
        else:
            for col_name, col_type in columns_to_add:
                print(f"Adding '{col_name}' column...")
                await conn.execute(text(f"""
                    ALTER TABLE tasks 
                    ADD COLUMN {col_name} {col_type}
                """))
                await conn.commit()
                print(f"[OK] '{col_name}' column added successfully!")
    
    print("\nMigration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())
