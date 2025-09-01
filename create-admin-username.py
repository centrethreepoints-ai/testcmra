#!/usr/bin/env python3
"""
Script to create an admin user with username 'admin' for CRM Maroc
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from users.models import User
from companies.models import Company

def create_admin_username():
    """Create admin user with username 'admin' if it doesn't exist."""
    
    # Check if user with username 'admin' already exists
    if User.objects.filter(username='admin').exists():
        print("User with username 'admin' already exists. Updating password...")
        user = User.objects.get(username='admin')
        user.set_password('REDACTED')
        user.save()
        print(f"✓ Password updated for user: {user.username} ({user.email})")
        return user
    
    # Check if user with email 'admin@admin.local' exists and update username
    if User.objects.filter(email='admin@admin.local').exists():
        print("User with email 'admin@admin.local' exists. Adding username 'admin'...")
        user = User.objects.get(email='admin@admin.local')
        user.username = 'admin'
        user.set_password('REDACTED')
        user.save()
        print(f"✓ Username 'admin' added to user: {user.email}")
        return user
    
    # Create new user if none exists
    print("Creating new admin user with username 'admin'...")
    
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
        return None
    
    # Create the admin user
    try:
        user = User.objects.create_user(
            email='admin@admin.local',
            username='admin',
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
        
        print(f"✓ Created admin user: {user.username} ({user.email})")
        print(f"  - Username: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - Name: {user.get_full_name()}")
        print(f"  - Role: {user.role}")
        print(f"  - Company: {user.company.name if user.company else 'None'}")
        print(f"  - Password: REDACTED")
        
        return user
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def list_users():
    """List all existing users."""
    print("\n📋 Existing Users:")
    print("=" * 80)
    
    users = User.objects.all().order_by('date_joined')
    if not users:
        print("No users found.")
        return
    
    for user in users:
        status = "🟢 Active" if user.is_active else "🔴 Inactive"
        role_icon = {
            'admin': '👑',
            'comptable': '📊',
            'vente': '💰',
            'achat': '🛒',
            'lecture': '👁️'
        }.get(user.role, '❓')
        
        print(f"ID: {user.id}")
        print(f"  {role_icon} Username: {user.username or 'None'}")
        print(f"  📧 Email: {user.email}")
        print(f"  👤 Name: {user.get_full_name()}")
        print(f"  🏷️  Role: {user.role}")
        print(f"  🏢 Company: {user.company.name if user.company else 'None'}")
        print(f"  {status}")
        print(f"  📅 Created: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
        print(f"  🔑 Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
        print("-" * 80)

def main():
    """Main function."""
    print("🏢 CRM Maroc - Admin Username Creation")
    print("=" * 50)
    
    # Create admin user with username
    user = create_admin_username()
    
    if user:
        print("\n✓ Admin user setup completed successfully!")
        
        # List all users
        list_users()
        
        print("\n🎉 You can now login with:")
        print("  Username: admin")
        print("  OR Email: admin@admin.local")
        print("  Password: REDACTED")
        print("\nAccess your application at: http://10.10.10.15:8000/login/")
        
        print("\n💡 Login Options:")
        print("  - Use username 'admin' + password 'REDACTED'")
        print("  - Use email 'admin@admin.local' + password 'REDACTED'")
        
    else:
        print("\n❌ Failed to create admin user!")
        sys.exit(1)

if __name__ == "__main__":
    main()
