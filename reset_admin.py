#!/usr/bin/env python3
"""
Reset superadmin password script
Run: python reset_admin.py
"""
import sys
sys.path.insert(0, '/Users/bigzilly/Desktop/gown system')

from werkzeug.security import generate_password_hash
import sqlite3
import os

# Database path
db_path = '/Users/bigzilly/Desktop/gown system/instance/university_gowns.db'

# New password (change this!)
new_password = 'admin123'

# Generate hash using werkzeug
password_hash = generate_password_hash(new_password)

print(f"Generated hash: {password_hash}")

# Connect and update
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Try to find and update existing superadmin
cursor.execute("SELECT id, username, role FROM users WHERE role = 'SuperAdmin' LIMIT 1")
result = cursor.fetchone()

if result:
    user_id, username, role = result
    print(f"Found SuperAdmin: id={user_id}, username={username}")
    
    # Update password
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id)
    )
    conn.commit()
    print(f"Password updated successfully for user '{username}'")
    print(f"New password: {new_password}")
else:
    print("No SuperAdmin found. Creating new one...")
    
    # Create new superadmin
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, ?, ?)",
        ('superadmin', 'admin@gctu.edu.gh', password_hash, 'SuperAdmin', 1, 1)
    )
    conn.commit()
    print(f"Created new SuperAdmin user")
    print(f"Username: superadmin")
    print(f"Password: {new_password}")

conn.close()
print("\nDone!")
