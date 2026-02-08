#!/usr/bin/env python3
"""
Property test for uniqueness constraints in dual user registration.
Feature: dual-user-registration, Property 7: Email and username uniqueness across all user types
Validates: Requirements 5.1, 5.2
"""

import sys
from pathlib import Path
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

try:
    from models.database import Base, User, Guru
    from services.user_service import UserService
    from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData
    from database import get_db
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)


def create_test_database():
    """Create a temporary test database."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create engine and session
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal, db_path


def cleanup_test_database(db_path):
    """Clean up temporary database file."""
    try:
        os.unlink(db_path)
    except OSError:
        pass


def test_email_uniqueness_across_user_types():
    """
    Property 7: Email uniqueness across all user types
    For any email address, it should be unique across both regular users and practitioners.
    No two users (regardless of role) should have the same email address.
    
    Feature: dual-user-registration, Property 7: Email and username uniqueness across all user types
    Validates: Requirements 5.1
    """
    print("Testing email uniqueness across user types...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test data
        email = "test@example.com"
        
        user_data = UserRegistrationData(
            username="testuser",
            email=email,
            password="StrongPass123!",
            role="user"
        )
        
        practitioner_data = PractitionerRegistrationData(
            username="testguru",
            email=email,  # Same email as user
            password="StrongPass123!",
            role="practitioner",
            professional_title="Vedic Astrologer",
            bio="Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
            specializations=["vedic_astrology"],
            experience_years=5,
            certification_details={
                "certification_type": "diploma",
                "issuing_authority": "Indian Institute of Astrology"
            }
        )
        
        # Create first user (regular user)
        user1 = user_service.create_user(user_data)
        print(f"  ✅ Created regular user with email {email}")
        
        # Try to create practitioner with same email (should fail)
        try:
            user_service.create_practitioner(practitioner_data)
            print(f"  ❌ Practitioner with duplicate email {email} was created")
            return False
        except ValueError as e:
            if "already registered" in str(e).lower():
                print(f"  ✅ Practitioner with duplicate email {email} correctly rejected")
            else:
                print(f"  ❌ Unexpected error for duplicate email: {e}")
                return False
        
        # Test reverse scenario - create practitioner first, then user
        db.query(User).delete()
        db.query(Guru).delete()
        db.commit()
        
        # Create practitioner first
        user2, guru2 = user_service.create_practitioner(practitioner_data)
        print(f"  ✅ Created practitioner with email {email}")
        
        # Try to create regular user with same email (should fail)
        try:
            user_service.create_user(user_data)
            print(f"  ❌ Regular user with duplicate email {email} was created")
            return False
        except ValueError as e:
            if "already registered" in str(e).lower():
                print(f"  ✅ Regular user with duplicate email {email} correctly rejected")
            else:
                print(f"  ❌ Unexpected error for duplicate email: {e}")
                return False
        
        db.close()
        print("✅ Email uniqueness across user types passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_username_uniqueness_across_user_types():
    """
    Property 7: Username uniqueness across all user types
    For any username, it should be unique across both regular users and practitioners.
    No two users (regardless of role) should have the same username.
    
    Feature: dual-user-registration, Property 7: Email and username uniqueness across all user types
    Validates: Requirements 5.2
    """
    print("\nTesting username uniqueness across user types...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test data
        username = "testuser123"
        
        user_data = UserRegistrationData(
            username=username,
            email="user@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        practitioner_data = PractitionerRegistrationData(
            username=username,  # Same username as user
            email="guru@example.com",
            password="StrongPass123!",
            role="practitioner",
            professional_title="Vedic Astrologer",
            bio="Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
            specializations=["vedic_astrology"],
            experience_years=5,
            certification_details={
                "certification_type": "diploma",
                "issuing_authority": "Indian Institute of Astrology"
            }
        )
        
        # Create first user (regular user)
        user1 = user_service.create_user(user_data)
        print(f"  ✅ Created regular user with username {username}")
        
        # Try to create practitioner with same username (should fail)
        try:
            user_service.create_practitioner(practitioner_data)
            print(f"  ❌ Practitioner with duplicate username {username} was created")
            return False
        except ValueError as e:
            if "already taken" in str(e).lower():
                print(f"  ✅ Practitioner with duplicate username {username} correctly rejected")
            else:
                print(f"  ❌ Unexpected error for duplicate username: {e}")
                return False
        
        # Test reverse scenario - create practitioner first, then user
        db.query(User).delete()
        db.query(Guru).delete()
        db.commit()
        
        # Create practitioner first
        user2, guru2 = user_service.create_practitioner(practitioner_data)
        print(f"  ✅ Created practitioner with username {username}")
        
        # Try to create regular user with same username (should fail)
        try:
            user_service.create_user(user_data)
            print(f"  ❌ Regular user with duplicate username {username} was created")
            return False
        except ValueError as e:
            if "already taken" in str(e).lower():
                print(f"  ✅ Regular user with duplicate username {username} correctly rejected")
            else:
                print(f"  ❌ Unexpected error for duplicate username: {e}")
                return False
        
        db.close()
        print("✅ Username uniqueness across user types passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_case_insensitive_uniqueness():
    """
    Test that uniqueness checks are case-insensitive.
    For any email or username, variations in case should be treated as the same value.
    
    Feature: dual-user-registration, Property 7: Email and username uniqueness across all user types
    Validates: Requirements 5.1, 5.2
    """
    print("\nTesting case-insensitive uniqueness...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Create user with lowercase email and username
        user_data = UserRegistrationData(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        user1 = user_service.create_user(user_data)
        print("  ✅ Created user with lowercase email and username")
        
        # Try to create another user with uppercase variations
        user_data_upper = UserRegistrationData(
            username="TESTUSER",  # Same username, different case
            email="TEST@EXAMPLE.COM",  # Same email, different case
            password="StrongPass123!",
            role="user"
        )
        
        # Test uppercase email
        try:
            user_service.create_user(user_data_upper)
            print("  ❌ User with uppercase email variation was created")
            return False
        except ValueError as e:
            if "already registered" in str(e).lower():
                print("  ✅ Uppercase email variation correctly rejected")
            else:
                print(f"  ❌ Unexpected error for uppercase email: {e}")
                return False
        
        # Test uppercase username with different email
        user_data_upper.email = "different@example.com"
        try:
            user_service.create_user(user_data_upper)
            print("  ❌ User with uppercase username variation was created")
            return False
        except ValueError as e:
            if "already taken" in str(e).lower():
                print("  ✅ Uppercase username variation correctly rejected")
            else:
                print(f"  ❌ Unexpected error for uppercase username: {e}")
                return False
        
        # Test mixed case variations
        user_data_mixed = UserRegistrationData(
            username="TestUser",
            email="Test@Example.Com",
            password="StrongPass123!",
            role="user"
        )
        
        try:
            user_service.create_user(user_data_mixed)
            print("  ❌ User with mixed case variations was created")
            return False
        except ValueError as e:
            if "already" in str(e).lower():
                print("  ✅ Mixed case variations correctly rejected")
            else:
                print(f"  ❌ Unexpected error for mixed case: {e}")
                return False
        
        db.close()
        print("✅ Case-insensitive uniqueness passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_uniqueness_validation_methods():
    """
    Test the uniqueness validation methods directly.
    For any email or username, the validation methods should correctly identify duplicates.
    
    Feature: dual-user-registration, Property 7: Email and username uniqueness across all user types
    Validates: Requirements 5.1, 5.2
    """
    print("\nTesting uniqueness validation methods...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Create a test user
        user_data = UserRegistrationData(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        user = user_service.create_user(user_data)
        print("  ✅ Created test user")
        
        # Test email uniqueness validation
        if not user_service.validate_email_uniqueness("test@example.com"):
            print("  ✅ Email uniqueness validation correctly identified duplicate")
        else:
            print("  ❌ Email uniqueness validation failed to identify duplicate")
            return False
        
        if user_service.validate_email_uniqueness("different@example.com"):
            print("  ✅ Email uniqueness validation correctly identified unique email")
        else:
            print("  ❌ Email uniqueness validation incorrectly rejected unique email")
            return False
        
        # Test username uniqueness validation
        if not user_service.validate_username_uniqueness("testuser"):
            print("  ✅ Username uniqueness validation correctly identified duplicate")
        else:
            print("  ❌ Username uniqueness validation failed to identify duplicate")
            return False
        
        if user_service.validate_username_uniqueness("differentuser"):
            print("  ✅ Username uniqueness validation correctly identified unique username")
        else:
            print("  ❌ Username uniqueness validation incorrectly rejected unique username")
            return False
        
        # Test exclusion functionality (for updates)
        if user_service.validate_email_uniqueness("test@example.com", exclude_user_id=user.id):
            print("  ✅ Email uniqueness validation correctly excluded current user")
        else:
            print("  ❌ Email uniqueness validation failed to exclude current user")
            return False
        
        if user_service.validate_username_uniqueness("testuser", exclude_user_id=user.id):
            print("  ✅ Username uniqueness validation correctly excluded current user")
        else:
            print("  ❌ Username uniqueness validation failed to exclude current user")
            return False
        
        db.close()
        print("✅ Uniqueness validation methods passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def main():
    """Run all uniqueness constraint tests."""
    print("🧪 Running Uniqueness Constraint Tests")
    print("=" * 60)
    
    tests = [
        test_email_uniqueness_across_user_types,
        test_username_uniqueness_across_user_types,
        test_case_insensitive_uniqueness,
        test_uniqueness_validation_methods
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All uniqueness constraint tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)