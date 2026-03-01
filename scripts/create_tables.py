#!/usr/bin/env python3
"""
Create database tables in Railway MySQL .
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create all database tables"""
    print("🔧 Creating database tables...")
    
    try:
        from backend.api.app_production import create_app
        from backend.models.database import db
        
        # Create app with production config
        app = create_app('production')
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # List tables to verify
            from sqlalchemy import text
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            print(f"📊 Created tables: {tables}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def test_table_structure():
    """Test that tables have correct structure"""
    print("\n🔍 Testing table structure...")
    
    try:
        from backend.api.app_production import create_app
        from backend.models.database import db
        from sqlalchemy import text
        
        app = create_app('production')
        
        with app.app_context():
            # Check products table structure
            result = db.session.execute(text("DESCRIBE products"))
            columns = [f"{row[0]} ({row[1]})" for row in result]
            
            print(f"✅ Products table columns: {columns}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        return False

def main():
    """Create tables and test structure"""
    print("🚀 DSP Eco Tracker - Database Setup\n")
    
    # Step 1: Create tables
    tables_created = create_tables()
    if not tables_created:
        return False
    
    # Step 2: Test structure
    structure_ok = test_table_structure()
    if not structure_ok:
        return False
    
    print(f"\n🎉 Database setup complete!")
    print("📋 Next step: Run migration to import your 50,000 products")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
