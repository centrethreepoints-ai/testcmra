#!/usr/bin/env python3
"""
Advanced User Management Script for CRM Maroc
"""

import os
import sys
import django
import getpass

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from users.models import User
from companies.models import Company

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
        print(f"  {role_icon} Email: {user.email}")
        print(f"  👤 Name: {user.get_full_name()}")
        print(f"  🏷️  Role: {user.role}")
        print(f"  🏢 Company: {user.company.name if user.company else 'None'}")
        print(f"  {status}")
        print(f"  📅 Created: {user.date_joined.strftime('%Y-%m-%d %H:%M')}")
        print(f"  🔑 Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}")
        print("-" * 80)

def create_user():
    """Create a new user interactively."""
    print("\n👤 Create New User")
    print("=" * 40)
    
    # Get company
    companies = Company.objects.all()
    if not companies:
        print("❌ No companies found. Please create a company first.")
        return False
    
    if len(companies) == 1:
        company = companies.first()
        print(f"🏢 Using company: {company.name}")
    else:
        print("Available companies:")
        for i, comp in enumerate(companies, 1):
            print(f"  {i}. {comp.name}")
        
        try:
            choice = int(input("Select company (number): ")) - 1
            company = companies[choice]
        except (ValueError, IndexError):
            print("❌ Invalid choice.")
            return False
    
    # Get user details
    email = input("📧 Email: ").strip()
    if not email:
        print("❌ Email is required.")
        return False
    
    if User.objects.filter(email=email).exists():
        print("❌ User with this email already exists.")
        return False
    
    first_name = input("👤 First Name: ").strip()
    last_name = input("👤 Last Name: ").strip()
    
    # Get role
    roles = [
        ('admin', '👑 Administrator'),
        ('comptable', '📊 Accountant'),
        ('vente', '💰 Sales'),
        ('achat', '🛒 Purchasing'),
        ('lecture', '👁️ Read Only')
    ]
    
    print("\nAvailable roles:")
    for i, (role, desc) in enumerate(roles, 1):
        print(f"  {i}. {desc}")
    
    try:
        role_choice = int(input("Select role (number): ")) - 1
        role = roles[role_choice][0]
    except (ValueError, IndexError):
        print("❌ Invalid role choice.")
        return False
    
    # Get password
    password = getpass.getpass("🔑 Password: ")
    if not password:
        print("❌ Password is required.")
        return False
    
    password_confirm = getpass.getpass("🔑 Confirm Password: ")
    if password != password_confirm:
        print("❌ Passwords don't match.")
        return False
    
    # Create user
    try:
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            company=company
        )
        user.set_password(password)
        user.save()
        
        print(f"\n✅ User created successfully!")
        print(f"  📧 Email: {user.email}")
        print(f"  👤 Name: {user.get_full_name()}")
        print(f"  🏷️  Role: {user.role}")
        print(f"  🏢 Company: {user.company.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def update_user():
    """Update an existing user."""
    print("\n✏️  Update User")
    print("=" * 40)
    
    users = User.objects.all()
    if not users:
        print("❌ No users found.")
        return False
    
    print("Select user to update:")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user.email} ({user.get_full_name()})")
    
    try:
        choice = int(input("Select user (number): ")) - 1
        user = users[choice]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return False
    
    print(f"\nUpdating user: {user.email}")
    
    # Update fields
    first_name = input(f"👤 First Name ({user.first_name}): ").strip()
    if first_name:
        user.first_name = first_name
    
    last_name = input(f"👤 Last Name ({user.last_name}): ").strip()
    if last_name:
        user.last_name = last_name
    
    # Update role
    roles = [
        ('admin', '👑 Administrator'),
        ('comptable', '📊 Accountant'),
        ('vente', '💰 Sales'),
        ('achat', '🛒 Purchasing'),
        ('lecture', '👁️ Read Only')
    ]
    
    print(f"\nCurrent role: {user.role}")
    print("Available roles:")
    for i, (role, desc) in enumerate(roles, 1):
        print(f"  {i}. {desc}")
    
    role_choice = input("Select new role (number, or Enter to keep current): ").strip()
    if role_choice:
        try:
            role_idx = int(role_choice) - 1
            user.role = roles[role_idx][0]
        except (ValueError, IndexError):
            print("❌ Invalid role choice. Keeping current role.")
    
    # Update password
    change_password = input("🔑 Change password? (y/N): ").strip().lower()
    if change_password in ['y', 'yes']:
        password = getpass.getpass("New password: ")
        if password:
            password_confirm = getpass.getpass("Confirm new password: ")
            if password == password_confirm:
                user.set_password(password)
                print("✅ Password updated.")
            else:
                print("❌ Passwords don't match. Password not changed.")
    
    # Save changes
    try:
        user.save()
        print(f"\n✅ User updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return False

def delete_user():
    """Delete a user."""
    print("\n🗑️  Delete User")
    print("=" * 40)
    
    users = User.objects.all()
    if not users:
        print("❌ No users found.")
        return False
    
    print("Select user to delete:")
    for i, user in enumerate(users, 1):
        print(f"  {i}. {user.email} ({user.get_full_name()})")
    
    try:
        choice = int(input("Select user (number): ")) - 1
        user = users[choice]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return False
    
    confirm = input(f"\n⚠️  Are you sure you want to delete {user.email}? (yes/no): ").strip().lower()
    if confirm == 'yes':
        try:
            user.delete()
            print(f"✅ User {user.email} deleted successfully!")
            return True
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    else:
        print("❌ Deletion cancelled.")
        return False

def main():
    """Main function."""
    print("🏢 CRM Maroc - User Management")
    print("=" * 50)
    
    while True:
        print("\n📋 Available actions:")
        print("  1. 📋 List users")
        print("  2. 👤 Create user")
        print("  3. ✏️  Update user")
        print("  4. 🗑️  Delete user")
        print("  5. 🚪 Exit")
        
        choice = input("\nSelect action (1-5): ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            create_user()
        elif choice == '3':
            update_user()
        elif choice == '4':
            delete_user()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-5.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
