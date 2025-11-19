#!/usr/bin/env python3
"""
Create Admin User Script
Creates the first superuser account for Alpha AI Autotrader
"""
import sys
import os
from getpass import getpass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.models.database import User, SessionLocal, init_db
from loguru import logger

def create_admin_user():
    """Interactive script to create admin user"""
    print("=" * 60)
    print("  Alpha AI Autotrader - Create Admin User")
    print("=" * 60)
    print()

    # Initialize database
    init_db()
    print("✅ Database initialized")
    print()

    # Get user input
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()

    while not email:
        print("❌ Email is required")
        email = input("Enter admin email: ").strip()

    full_name = input("Enter full name (optional): ").strip() or None

    # Get password
    while True:
        password = getpass("Enter password (min 8 chars): ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long")
            continue

        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords don't match")
            continue

        break

    print()
    print("Creating admin user...")

    # Create user in database
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print(f"❌ User already exists: {existing_user.username}")
            return

        # Create new admin user
        admin_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=User.hash_password(password),
            is_active=True,
            is_superuser=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print()
        print("=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Full Name: {admin_user.full_name or 'N/A'}")
        print(f"Is Superuser: {admin_user.is_superuser}")
        print()
        print("You can now login at: http://localhost:8000/api/auth/login")
        print("API Documentation: http://localhost:8000/api/docs")
        print()

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
