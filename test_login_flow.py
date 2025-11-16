#!/usr/bin/env python3
"""Test the full login flow to find the issue."""

import sys
sys.path.insert(0, '.')

from backend.config import Settings
from backend.database import Database
from backend.auth import AuthManager
from backend.repositories.user_repository import UserRepository
from backend.services.auth_service import AuthService

def main():
    print("=== Testing Login Flow ===\n")

    config = Settings()
    db = Database(config.database_url)
    auth_manager = AuthManager(db, config)
    user_repository = UserRepository(auth_manager)
    auth_service = AuthService(user_repository)

    email = 'maftoul.eli@gmail.com'
    password = 'qHjs7fzFXR1994'

    print(f"Email: {email}")
    print(f"Password: {password}")
    print()

    # Step 1: Test UserRepository.authenticate()
    print("Step 1: UserRepository.authenticate()")
    try:
        result = user_repository.authenticate(email, password)
        print(f"  Result type: {type(result)}")
        if result:
            print(f"  Success: {result.get('success')}")
            print(f"  User: {result.get('user', {}).get('email') if result.get('user') else 'None'}")
            print(f"  Token: {'Present' if result.get('token') else 'Missing'}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
        else:
            print("  Result: None")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

    # Step 2: Test AuthService.login()
    print("Step 2: AuthService.login()")
    try:
        user_data = auth_service.login(email, password)
        print(f"  Result type: {type(user_data)}")
        if user_data:
            print(f"  User ID: {user_data.get('id')}")
            print(f"  Email: {user_data.get('email')}")
            print(f"  Role: {user_data.get('role')}")
            print(f"  Token: {'Present' if user_data.get('token') else 'Missing'}")
        else:
            print("  Result: None (login failed)")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

    # Step 3: Test AuthManager.login_user() directly
    print("Step 3: AuthManager.login_user() - Direct call")
    try:
        result = auth_manager.login_user(email, password)
        print(f"  Result type: {type(result)}")
        print(f"  Success: {result.get('success')}")
        if result.get('success'):
            print(f"  User email: {result.get('user', {}).get('email')}")
            print(f"  User role: {result.get('user', {}).get('role')}")
            print(f"  Token: {'Present' if result.get('token') else 'Missing'}")
        else:
            print(f"  Error: {result.get('error')}")
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == '__main__':
    main()
