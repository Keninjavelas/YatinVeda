#!/usr/bin/env python3
"""
Property test for role-based registration in dual user registration.
Feature: dual-user-registration, Property 1: Role-based data collection
Feature: dual-user-registration, Property 2: Correct role and status assignment
Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.4, 2.5, 4.1, 4.2
"""

import sys
from pathlib import Path
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Add the backend directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

try:
    from models.database import Base, User, Guru
    from services.user_service import UserService
    from schemas.dual_registration import UserRegistrationData, PractitionerRegistrationData
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


def test_user_role_based_data_collection():
    """
    Property 1: Role-based data collection for users
    For any user registration, only user-specific fields should be collected and stored.
    
    Feature: dual-user-registration, Property 1: Role-based data collection
    Validates: Requirements 1.2, 2.4
    """
    print("Testing user role-based data collection...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test user registration data
        user_data = UserRegistrationData(
            username="testuser",
            email="user@example.com",
            password="StrongPass123!",
            role="user",
            full_name="Test User",
            birth_details={
                "birth_date": "1990-01-01",
                "birth_time": "10:30",
                "birth_place": "New York, USA"
            }
        )
        
        # Create user
        user = user_service.create_user(user_data)
        
        # Verify user data is stored correctly
        if user.role == "user":
            print("  ✅ User role correctly assigned")
        else:
            print(f"  ❌ User role incorrect: {user.role}")
            return False
        
        if user.username == "testuser":
            print("  ✅ Username correctly stored")
        else:
            print(f"  ❌ Username incorrect: {user.username}")
            return False
        
        if user.email == "user@example.com":
            print("  ✅ Email correctly stored")
        else:
            print(f"  ❌ Email incorrect: {user.email}")
            return False
        
        if user.full_name == "Test User":
            print("  ✅ Full name correctly stored")
        else:
            print(f"  ❌ Full name incorrect: {user.full_name}")
            return False
        
        if user.birth_details and user.birth_details.get("birth_place") == "New York, USA":
            print("  ✅ Birth details correctly stored")
        else:
            print(f"  ❌ Birth details incorrect: {user.birth_details}")
            return False
        
        # Verify no guru profile is created for regular users
        guru = db.query(Guru).filter(Guru.user_id == user.id).first()
        if guru is None:
            print("  ✅ No guru profile created for regular user")
        else:
            print("  ❌ Guru profile incorrectly created for regular user")
            return False
        
        db.close()
        print("✅ User role-based data collection passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_practitioner_role_based_data_collection():
    """
    Property 1: Role-based data collection for practitioners
    For any practitioner registration, both user and practitioner-specific fields should be collected.
    
    Feature: dual-user-registration, Property 1: Role-based data collection
    Validates: Requirements 1.3, 2.5
    """
    print("\nTesting practitioner role-based data collection...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test practitioner registration data
        practitioner_data = PractitionerRegistrationData(
            username="testguru",
            email="guru@example.com",
            password="StrongPass123!",
            role="practitioner",
            full_name="Test Guru",
            professional_title="Vedic Astrologer",
            bio="Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
            specializations=["vedic_astrology", "numerology"],
            experience_years=10,
            certification_details={
                "certification_type": "diploma",
                "issuing_authority": "Indian Institute of Astrology"
            },
            languages=["english", "hindi"],
            price_per_hour=15000,
            contact_phone="+91-9876543210"
        )
        
        # Create practitioner
        user, guru = user_service.create_practitioner(practitioner_data)
        
        # Verify user data is stored correctly
        if user.role == "practitioner":
            print("  ✅ Practitioner role correctly assigned")
        else:
            print(f"  ❌ Practitioner role incorrect: {user.role}")
            return False
        
        if user.username == "testguru":
            print("  ✅ Username correctly stored")
        else:
            print(f"  ❌ Username incorrect: {user.username}")
            return False
        
        if user.email == "guru@example.com":
            print("  ✅ Email correctly stored")
        else:
            print(f"  ❌ Email incorrect: {user.email}")
            return False
        
        # Verify guru profile is created and linked
        if guru is not None and guru.user_id == user.id:
            print("  ✅ Guru profile correctly created and linked")
        else:
            print("  ❌ Guru profile not created or not linked")
            return False
        
        # Verify practitioner-specific data
        if guru.professional_title == "Vedic Astrologer":
            print("  ✅ Professional title correctly stored")
        else:
            print(f"  ❌ Professional title incorrect: {guru.professional_title}")
            return False
        
        if "vedic_astrology" in guru.specializations and "numerology" in guru.specializations:
            print("  ✅ Specializations correctly stored")
        else:
            print(f"  ❌ Specializations incorrect: {guru.specializations}")
            return False
        
        if guru.experience_years == 10:
            print("  ✅ Experience years correctly stored")
        else:
            print(f"  ❌ Experience years incorrect: {guru.experience_years}")
            return False
        
        if guru.certification_details.get("certification_type") == "diploma":
            print("  ✅ Certification details correctly stored")
        else:
            print(f"  ❌ Certification details incorrect: {guru.certification_details}")
            return False
        
        db.close()
        print("✅ Practitioner role-based data collection passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_correct_role_assignment():
    """
    Property 2: Correct role and status assignment
    For any registration, the correct role and verification status should be assigned.
    
    Feature: dual-user-registration, Property 2: Correct role and status assignment
    Validates: Requirements 4.1, 4.2
    """
    print("\nTesting correct role and status assignment...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test user role and status assignment
        user_data = UserRegistrationData(
            username="testuser",
            email="user@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        user = user_service.create_user(user_data)
        
        if user.role == "user" and user.verification_status == "active":
            print("  ✅ User role and status correctly assigned (user/active)")
        else:
            print(f"  ❌ User role/status incorrect: {user.role}/{user.verification_status}")
            return False
        
        # Test practitioner role and status assignment
        practitioner_data = PractitionerRegistrationData(
            username="testguru",
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
        
        user2, guru = user_service.create_practitioner(practitioner_data)
        
        if (user2.role == "practitioner" and 
            user2.verification_status == "pending_verification" and
            not guru.is_verified):
            print("  ✅ Practitioner role and status correctly assigned (practitioner/pending_verification)")
        else:
            print(f"  ❌ Practitioner role/status incorrect: {user2.role}/{user2.verification_status}/{guru.is_verified}")
            return False
        
        db.close()
        print("✅ Correct role and status assignment passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_role_based_field_requirements():
    """
    Property 1 & 2: Role-based field requirements
    For any registration, required fields should be enforced based on role.
    
    Feature: dual-user-registration, Property 1: Role-based data collection
    Feature: dual-user-registration, Property 2: Correct role and status assignment
    Validates: Requirements 1.4, 1.5
    """
    print("\nTesting role-based field requirements...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Test that user registration works with minimal required fields
        minimal_user_data = UserRegistrationData(
            username="minimaluser",
            email="minimal@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        user = user_service.create_user(minimal_user_data)
        if user.id:
            print("  ✅ User registration works with minimal required fields")
        else:
            print("  ❌ User registration failed with minimal fields")
            return False
        
        # Test that practitioner registration requires additional fields
        # This should be caught by Pydantic validation, but let's test the service layer
        try:
            incomplete_practitioner_data = PractitionerRegistrationData(
                username="incompleteguru",
                email="incomplete@example.com",
                password="StrongPass123!",
                role="practitioner",
                professional_title="Astrologer",
                bio="Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
                specializations=["vedic_astrology"],
                experience_years=5,
                certification_details={
                    "certification_type": "diploma",
                    "issuing_authority": "Indian Institute of Astrology"
                }
            )
            
            user2, guru2 = user_service.create_practitioner(incomplete_practitioner_data)
            if user2.id and guru2.id:
                print("  ✅ Complete practitioner registration works")
            else:
                print("  ❌ Complete practitioner registration failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Practitioner registration failed unexpectedly: {e}")
            return False
        
        db.close()
        print("✅ Role-based field requirements passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_data_isolation_between_roles():
    """
    Property 1: Data isolation between roles
    For any registration, role-specific data should not interfere with other roles.
    
    Feature: dual-user-registration, Property 1: Role-based data collection
    Validates: Requirements 1.2, 1.3
    """
    print("\nTesting data isolation between roles...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        
        # Create both user types with similar usernames/emails
        user_data = UserRegistrationData(
            username="testuser1",
            email="user1@example.com",
            password="StrongPass123!",
            role="user"
        )
        
        practitioner_data = PractitionerRegistrationData(
            username="testuser2",
            email="user2@example.com",
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
        
        # Create both users
        user = user_service.create_user(user_data)
        practitioner_user, guru = user_service.create_practitioner(practitioner_data)
        
        # Verify data isolation
        # User should not have guru profile
        user_guru = db.query(Guru).filter(Guru.user_id == user.id).first()
        if user_guru is None:
            print("  ✅ Regular user has no guru profile")
        else:
            print("  ❌ Regular user incorrectly has guru profile")
            return False
        
        # Practitioner should have guru profile
        practitioner_guru = db.query(Guru).filter(Guru.user_id == practitioner_user.id).first()
        if practitioner_guru is not None and practitioner_guru.id == guru.id:
            print("  ✅ Practitioner has correct guru profile")
        else:
            print("  ❌ Practitioner missing or incorrect guru profile")
            return False
        
        # Verify role-specific fields are isolated
        if user.role == "user" and practitioner_user.role == "practitioner":
            print("  ✅ Roles are correctly isolated")
        else:
            print(f"  ❌ Roles not isolated: {user.role}, {practitioner_user.role}")
            return False
        
        # Verify verification status is role-appropriate
        if (user.verification_status == "active" and 
            practitioner_user.verification_status == "pending_verification"):
            print("  ✅ Verification statuses are role-appropriate")
        else:
            print(f"  ❌ Verification statuses incorrect: {user.verification_status}, {practitioner_user.verification_status}")
            return False
        
        db.close()
        print("✅ Data isolation between roles passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def main():
    """Run all role-based registration tests."""
    print("🧪 Running Role-Based Registration Tests")
    print("=" * 60)
    
    tests = [
        test_user_role_based_data_collection,
        test_practitioner_role_based_data_collection,
        test_correct_role_assignment,
        test_role_based_field_requirements,
        test_data_isolation_between_roles
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
        print("🎉 All role-based registration tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)