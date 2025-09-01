#!/usr/bin/env python3
"""
Script to create an admin user for CRM Maroc
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from users.models import User
from companies.models import Company

def create_admin_user():
    """Create admin user if it doesn't exist."""
    
    # Check if user with email 'admin@admin.local' already exists
    if User.objects.filter(email='admin@admin.local').exists():
        print("User 'admin@admin.local' already exists. Updating password...")
        user = User.objects.get(email='admin@admin.local')
        user.set_password('REDACTED')
        user.save()
        print(f"✓ Password updated for user: {user.email}")
    else:
        print("Creating new admin user...")
        
        # Get the first company (or create one if none exists)
        try:
            company = Company.objects.first()
            if not company:
                print("No company found. Creating default company...")
                company = Company.objects.create(
                    name="Default Company",
                    country="Maroc",
                    default_currency="MAD",
                    current_fiscal_year="2024-2025"
                )
                print(f"✓ Created company: {company.name}")
        except Exception as e:
            print(f"Error getting/creating company: {e}")
            return False
        
        # Create the admin user
        try:
            user = User.objects.create_user(
                email='admin@admin.local',
                first_name='Admin',
                last_name='User',
                role='admin',
                company=company,
                is_staff=True,
                is_superuser=True
            )
            
            # Set the specific password
            user.set_password('REDACTED')
            user.save()
            
            print(f"✓ Created admin user: {user.email}")
            print(f"  - Name: {user.get_full_name()}")
            print(f"  - Role: {user.role}")
            print(f"  - Company: {user.company.name if user.company else 'None'}")
            print(f"  - Password: REDACTED")
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    return True

def list_users():
    """List all existing users."""
    print("\nExisting users:")
    print("-" * 50)
    
    users = User.objects.all().order_by('date_joined')
    for user in users:
        print(f"ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.get_full_name()}")
        print(f"  Role: {user.role}")
        print(f"  Company: {user.company.name if user.company else 'None'}")
        print(f"  Active: {user.is_active}")
        print(f"  Created: {user.date_joined}")
        print("-" * 50)

def main():
    """Main function."""
    print("CRM Maroc - Admin User Creation")
    print("=" * 40)
    
    # Create admin user
    if create_admin_user():
        print("\n✓ Admin user setup completed successfully!")
        
        # List all users
        list_users()
        
        print("\n🎉 You can now login with:")
        print("  Email: admin@admin.local")
        print("  Password: REDACTED")
        print("\nAccess your application at: http://10.10.10.15:8000/login/")
        
    else:
        print("\n❌ Failed to create admin user!")
        sys.exit(1)

if __name__ == "__main__":
    main()
