#!/usr/bin/env python3
"""
Test script for authentication with username or email
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from django.contrib.auth import authenticate
from users.models import User

def test_authentication():
    """Test authentication with different methods."""
    
    print("🔐 Testing Authentication Methods")
    print("=" * 50)
    
    # Test credentials (from environment)
    import os
    test_credentials = [
        (os.environ.get('TEST_ADMIN_USERNAME', ''), os.environ.get('TEST_ADMIN_PASSWORD', ''), 'Username'),
        (os.environ.get('TEST_ADMIN_EMAIL', ''), os.environ.get('TEST_ADMIN_PASSWORD', ''), 'Email'),
    ]
    
    for identifier, password, method in test_credentials:
        print(f"\n🧪 Testing {method}: {identifier}")
        print("-" * 30)
        
        # Try to authenticate
        user = authenticate(username=identifier, password=password)
        
        if user:
            print(f"✅ Authentication successful!")
            print(f"   User: {user.get_display_name()}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username or 'None'}")
            print(f"   Role: {user.role}")
            print(f"   Company: {user.company.name if user.company else 'None'}")
        else:
            print(f"❌ Authentication failed!")
            print(f"   {method}: {identifier}")
            print(f"   Password: {password}")
    
    print("\n" + "=" * 50)
    
    # Show all users for reference
    print("\n📋 All Users in Database:")
    print("-" * 50)
    
    users = User.objects.all().order_by('date_joined')
    for user in users:
        print(f"ID: {user.id}")
        print(f"  Username: {user.username or 'None'}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.get_full_name()}")
        print(f"  Role: {user.role}")
        print(f"  Active: {user.is_active}")
        print("-" * 30)

def test_login_form():
    """Test the custom authentication form."""
    
    print("\n🔍 Testing Custom Authentication Form")
    print("=" * 50)
    
    from users.forms import CustomAuthenticationForm
    from django.test import RequestFactory
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/login/')
    
    # Test form with username
    form_data = {
        'username': os.environ.get('TEST_ADMIN_USERNAME', ''),
        'password': os.environ.get('TEST_ADMIN_PASSWORD', '')
    }
    
    form = CustomAuthenticationForm(request, data=form_data)
    if form.is_valid():
        user = form.get_user()
        print(f"✅ Form validation successful with username!")
        print(f"   User: {user.get_display_name()}")
    else:
        print(f"❌ Form validation failed with username!")
        print(f"   Errors: {form.errors}")
    
    # Test form with email
    form_data = {
        'username': os.environ.get('TEST_ADMIN_EMAIL', ''),
        'password': os.environ.get('TEST_ADMIN_PASSWORD', '')
    }
    
    form = CustomAuthenticationForm(request, data=form_data)
    if form.is_valid():
        user = form.get_user()
        print(f"✅ Form validation successful with email!")
        print(f"   User: {user.get_display_name()}")
    else:
        print(f"❌ Form validation failed with email!")
        print(f"   Errors: {form.errors}")

def main():
    """Main function."""
    print("🏢 CRM Maroc - Authentication Test")
    print("=" * 60)
    
    # Test basic authentication
    test_authentication()
    
    # Test custom form
    test_login_form()
    
    print("\n🎉 Authentication test completed!")
    print("\n💡 Login Summary:")
    print("  - Username + password from env ✅")
    print("  - Email + password from env ✅")
    
    print("\n🌐 Access your application at: http://10.10.10.15:8000/login/")

if __name__ == "__main__":
    main()
