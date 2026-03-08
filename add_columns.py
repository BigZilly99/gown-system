#!/usr/bin/env python3
"""
Add missing columns to existing tables
Run: python add_columns.py
"""
import sys
sys.path.insert(0, '/Users/bigzilly/Desktop/gown system')

import sqlite3

db_path = '/Users/bigzilly/Desktop/gown system/instance/university_gowns.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current columns in transactions
cursor.execute("PRAGMA table_info(transactions)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current transactions columns: {columns}")

# Add gown_type if missing
if 'gown_type' not in columns:
    cursor.execute("ALTER TABLE transactions ADD COLUMN gown_type VARCHAR(50) DEFAULT 'GCTU Gowns'")
    print("Added gown_type column to transactions")

# Check if inventory table exists and has correct schema
cursor.execute("PRAGMA table_info(inventory)")
inv_columns = [col[1] for col in cursor.fetchall()]
print(f"Current inventory columns: {inv_columns}")

# Add initial inventory data if empty
cursor.execute("SELECT COUNT(*) FROM inventory")
count = cursor.fetchone()[0]
if count == 0:
    cursor.execute("INSERT INTO inventory (gown_type, total_count) VALUES ('GCTU Gowns', 0)")
    cursor.execute("INSERT INTO inventory (gown_type, total_count) VALUES ('Gowns Rented from Out of Campus', 0)")
    print("Added initial inventory data")

conn.commit()
conn.close()

print("\nDone! All columns added.")
