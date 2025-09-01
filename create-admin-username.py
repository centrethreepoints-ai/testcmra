#!/usr/bin/env python3
"""
Script to create an admin user with username 'admin' for CRM Maroc
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_env')
django.setup()

from users.models import User  # noqa: E402
from companies.models import Company  # noqa: E402


def create_admin_username():
    """Create admin user with username 'admin' if it doesn't exist."""

    admin_password = os.environ.get('TEST_ADMIN_PASSWORD', '')
    admin_email = os.environ.get('TEST_ADMIN_EMAIL', 'admin@admin.local')
    admin_username = os.environ.get('TEST_ADMIN_USERNAME', 'admin')

    # Check if user with username 'admin' already exists
    if User.objects.filter(username=admin_username).exists():
        print(f"User with username '{admin_username}' already exists. Updating password...")
        user = User.objects.get(username=admin_username)
        if admin_password:
            user.set_password(admin_password)
            user.save()
            print(f"✓ Password updated for user: {user.username} ({user.email})")
    else:
        # Check if user with email exists and update username
        if User.objects.filter(email=admin_email).exists():
            print(f"User with email '{admin_email}' exists. Adding username '{admin_username}'...")
            user = User.objects.get(email=admin_email)
            user.username = admin_username
            if admin_password:
                user.set_password(admin_password)
            user.save()
        else:
            print(f"Creating new admin user with username '{admin_username}'...")
            company = Company.objects.first()
            if company is None:
                company = Company.objects.create(name='Demo Company')

            user = User.objects.create_user(
                email=admin_email,
                username=admin_username,
                first_name='Admin',
                last_name='User',
                role='admin',
                is_staff=True,
                is_superuser=True,
                company=company,
            )
            if admin_password:
                user.set_password(admin_password)
                user.save()

        print("✓ Admin user ensured.")
        print(f"  - Username: {admin_username}")
        print(f"  - Email: {admin_email}")
        print("  - Password: [from env TEST_ADMIN_PASSWORD]")
        
        return user


if __name__ == '__main__':
    try:
        create_admin_username()
        print("\n🎉 Admin setup completed!")
        print("\nYou can now login with the credentials from your environment variables.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
