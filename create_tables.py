#!/usr/bin/env python3
"""
Create all missing database tables
Run: python create_tables.py
"""
import sys
sys.path.insert(0, '/Users/bigzilly/Desktop/gown system')

from app import create_app, db
from app.models import User, Department, Student, Inventory, Transaction, AuditLog, GownType, Gown

app = create_app('development')

with app.app_context():
    # Create all tables
    db.create_all()
    print("All tables created successfully!")
    
    # Check which tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\nExisting tables: {tables}")
