#!/usr/bin/env python3
"""
Property test for practitioner validation in dual user registration.
Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
Validates: Requirements 5.3, 5.4, 5.5
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
    from services.practitioner_service import PractitionerService
    from schemas.dual_registration import PractitionerRegistrationData
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


def test_specializations_validation():
    """
    Property 5: Specializations validation
    For any list of specializations, only valid specializations should be accepted.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.3
    """
    print("Testing specializations validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid specializations
        valid_specializations = [
            ["vedic_astrology"],
            ["tarot", "numerology"],
            ["palmistry", "vastu", "gemology"],
            ["career_guidance", "relationship_counseling"],
            ["spiritual_guidance", "meditation", "yoga"]
        ]
        
        for specs in valid_specializations:
            if practitioner_service.validate_specializations(specs):
                print(f"  ✅ Valid specializations {specs} accepted")
            else:
                print(f"  ❌ Valid specializations {specs} rejected")
                return False
        
        # Invalid specializations
        invalid_specializations = [
            ["invalid_specialization"],
            ["vedic_astrology", "fake_astrology"],
            [""],
            ["vedic_astrology", ""],
            []
        ]
        
        for specs in invalid_specializations:
            if not practitioner_service.validate_specializations(specs):
                print(f"  ✅ Invalid specializations {specs} correctly rejected")
            else:
                print(f"  ❌ Invalid specializations {specs} incorrectly accepted")
                return False
        
        db.close()
        print("✅ Specializations validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_experience_years_validation():
    """
    Property 5: Experience years validation
    For any experience years value, it should be within valid range (0-50).
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.4
    """
    print("\nTesting experience years validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid experience years
        valid_years = [0, 1, 5, 10, 25, 50]
        
        for years in valid_years:
            if practitioner_service.validate_experience_years(years):
                print(f"  ✅ Valid experience years {years} accepted")
            else:
                print(f"  ❌ Valid experience years {years} rejected")
                return False
        
        # Invalid experience years
        invalid_years = [-1, -5, 51, 100, 999]
        
        for years in invalid_years:
            if not practitioner_service.validate_experience_years(years):
                print(f"  ✅ Invalid experience years {years} correctly rejected")
            else:
                print(f"  ❌ Invalid experience years {years} incorrectly accepted")
                return False
        
        db.close()
        print("✅ Experience years validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_certification_details_validation():
    """
    Property 5: Certification details validation
    For any certification details, required fields should be present and valid.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.5
    """
    print("\nTesting certification details validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid certification details
        valid_certifications = [
            {
                "certification_type": "diploma",
                "issuing_authority": "Indian Institute of Astrology"
            },
            {
                "certification_type": "degree",
                "issuing_authority": "University of Vedic Sciences",
                "year_obtained": "2020"
            },
            {
                "certification_type": "professional_certification",
                "issuing_authority": "International Astrology Association",
                "certificate_number": "IAA-2023-001"
            },
            {
                "certification_type": "self_taught",
                "issuing_authority": "Self-directed study and practice"
            }
        ]
        
        for cert in valid_certifications:
            if practitioner_service.validate_certification_details(cert):
                print(f"  ✅ Valid certification details accepted")
            else:
                print(f"  ❌ Valid certification details rejected: {cert}")
                return False
        
        # Invalid certification details
        invalid_certifications = [
            {},  # Empty dict
            {"certification_type": "diploma"},  # Missing issuing_authority
            {"issuing_authority": "Some Institute"},  # Missing certification_type
            {"certification_type": "invalid_type", "issuing_authority": "Institute"},  # Invalid type
            {"certification_type": "diploma", "issuing_authority": ""},  # Empty authority
            {"certification_type": "", "issuing_authority": "Institute"},  # Empty type
            "not_a_dict",  # Not a dictionary
            None  # None value
        ]
        
        for cert in invalid_certifications:
            if not practitioner_service.validate_certification_details(cert):
                print(f"  ✅ Invalid certification details correctly rejected")
            else:
                print(f"  ❌ Invalid certification details incorrectly accepted: {cert}")
                return False
        
        db.close()
        print("✅ Certification details validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_languages_validation():
    """
    Property 5: Languages validation
    For any languages list, only valid language codes should be accepted.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.3
    """
    print("\nTesting languages validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid languages (including None)
        valid_languages = [
            None,
            ["english"],
            ["hindi", "sanskrit"],
            ["english", "hindi", "tamil", "telugu"],
            ["ENGLISH", "HINDI"],  # Case insensitive
            ["English", "Hindi", "Sanskrit"]  # Mixed case
        ]
        
        for langs in valid_languages:
            if practitioner_service.validate_languages(langs):
                print(f"  ✅ Valid languages {langs} accepted")
            else:
                print(f"  ❌ Valid languages {langs} rejected")
                return False
        
        # Invalid languages
        invalid_languages = [
            ["invalid_language"],
            ["english", "fake_language"],
            [""],
            ["english", ""],
            ["klingon", "dothraki"]
        ]
        
        for langs in invalid_languages:
            if not practitioner_service.validate_languages(langs):
                print(f"  ✅ Invalid languages {langs} correctly rejected")
            else:
                print(f"  ❌ Invalid languages {langs} incorrectly accepted")
                return False
        
        db.close()
        print("✅ Languages validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_price_validation():
    """
    Property 5: Price per hour validation
    For any price value, it should be within valid range or None.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.4
    """
    print("\nTesting price per hour validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid prices (including None)
        valid_prices = [None, 100, 1000, 15000, 50000]
        
        for price in valid_prices:
            if practitioner_service.validate_price_per_hour(price):
                print(f"  ✅ Valid price {price} accepted")
            else:
                print(f"  ❌ Valid price {price} rejected")
                return False
        
        # Invalid prices
        invalid_prices = [-1, 0, 99, 50001, 100000]
        
        for price in invalid_prices:
            if not practitioner_service.validate_price_per_hour(price):
                print(f"  ✅ Invalid price {price} correctly rejected")
            else:
                print(f"  ❌ Invalid price {price} incorrectly accepted")
                return False
        
        db.close()
        print("✅ Price per hour validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_contact_phone_validation():
    """
    Property 5: Contact phone validation
    For any phone number, it should follow valid format or be None.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.4
    """
    print("\nTesting contact phone validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid phone numbers (including None)
        valid_phones = [
            None,
            "9876543210",
            "+91-9876543210",
            "+1-234-567-8901",
            "(555) 123-4567",
            "555 123 4567",
            "91 98765 43210"
        ]
        
        for phone in valid_phones:
            if practitioner_service.validate_contact_phone(phone):
                print(f"  ✅ Valid phone {phone} accepted")
            else:
                print(f"  ❌ Valid phone {phone} rejected")
                return False
        
        # Invalid phone numbers
        invalid_phones = [
            "123",  # Too short
            "abc123def456",  # Contains letters
            "12345678901234567890",  # Too long
            "",  # Empty string
            "   ",  # Only spaces
        ]
        
        for phone in invalid_phones:
            if not practitioner_service.validate_contact_phone(phone):
                print(f"  ✅ Invalid phone {phone} correctly rejected")
            else:
                print(f"  ❌ Invalid phone {phone} incorrectly accepted")
                return False
        
        db.close()
        print("✅ Contact phone validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_bio_validation():
    """
    Property 5: Biography validation
    For any biography text, it should meet length requirements.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.3
    """
    print("\nTesting biography validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid biographies
        valid_bios = [
            "A" * 50,  # Minimum length
            "Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
            "A" * 1000,  # Medium length
            "A" * 2000   # Maximum length
        ]
        
        for bio in valid_bios:
            if practitioner_service.validate_bio(bio):
                print(f"  ✅ Valid bio (length {len(bio)}) accepted")
            else:
                print(f"  ❌ Valid bio (length {len(bio)}) rejected")
                return False
        
        # Invalid biographies
        invalid_bios = [
            "",  # Empty
            "A" * 49,  # Too short
            "A" * 2001,  # Too long
            None,  # None value
            123  # Not a string
        ]
        
        for bio in invalid_bios:
            if not practitioner_service.validate_bio(bio):
                print(f"  ✅ Invalid bio correctly rejected")
            else:
                print(f"  ❌ Invalid bio incorrectly accepted: {type(bio)}")
                return False
        
        db.close()
        print("✅ Biography validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_professional_title_validation():
    """
    Property 5: Professional title validation
    For any professional title, it should meet format and length requirements.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.3
    """
    print("\nTesting professional title validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid professional titles
        valid_titles = [
            "Astrologer",
            "Vedic Astrologer",
            "Tarot Reader",
            "Spiritual Guide",
            "Dr. Astrologer",
            "Master of Vedic Sciences",
            "A" * 100  # Maximum length
        ]
        
        for title in valid_titles:
            if practitioner_service.validate_professional_title(title):
                print(f"  ✅ Valid title '{title}' accepted")
            else:
                print(f"  ❌ Valid title '{title}' rejected")
                return False
        
        # Invalid professional titles
        invalid_titles = [
            "",  # Empty
            "A",  # Too short
            "A" * 101,  # Too long
            "Astrologer123",  # Contains numbers
            "Astrologer@Home",  # Contains special characters
            None,  # None value
            123  # Not a string
        ]
        
        for title in invalid_titles:
            if not practitioner_service.validate_professional_title(title):
                print(f"  ✅ Invalid title correctly rejected")
            else:
                print(f"  ❌ Invalid title incorrectly accepted: {title}")
                return False
        
        db.close()
        print("✅ Professional title validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_comprehensive_validation():
    """
    Property 5: Comprehensive practitioner data validation
    For any complete practitioner registration data, all validation rules should be applied.
    
    Feature: dual-user-registration, Property 5: Input validation rules for all practitioner fields
    Validates: Requirements 5.3, 5.4, 5.5
    """
    print("\nTesting comprehensive practitioner validation...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        practitioner_service = PractitionerService(db)
        
        # Valid practitioner data
        valid_data = PractitionerRegistrationData(
            username="testguru",
            email="guru@example.com",
            password="StrongPass123!",
            role="practitioner",
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
        
        errors = practitioner_service.validate_practitioner_data(valid_data)
        if len(errors) == 0:
            print("  ✅ Valid practitioner data passed comprehensive validation")
        else:
            print(f"  ❌ Valid practitioner data failed validation: {errors}")
            return False
        
        # Test individual validation methods with invalid data
        # (We can't create invalid PractitionerRegistrationData due to Pydantic validation)
        
        # Test invalid specializations
        if not practitioner_service.validate_specializations([]):
            print("  ✅ Empty specializations correctly rejected")
        else:
            print("  ❌ Empty specializations incorrectly accepted")
            return False
        
        # Test invalid experience years
        if not practitioner_service.validate_experience_years(100):
            print("  ✅ Invalid experience years correctly rejected")
        else:
            print("  ❌ Invalid experience years incorrectly accepted")
            return False
        
        # Test invalid certification details
        if not practitioner_service.validate_certification_details({}):
            print("  ✅ Invalid certification details correctly rejected")
        else:
            print("  ❌ Invalid certification details incorrectly accepted")
            return False
        
        # Test invalid bio
        if not practitioner_service.validate_bio("Short"):
            print("  ✅ Invalid bio correctly rejected")
        else:
            print("  ❌ Invalid bio incorrectly accepted")
            return False
        
        # Test invalid professional title
        if not practitioner_service.validate_professional_title("A"):
            print("  ✅ Invalid professional title correctly rejected")
        else:
            print("  ❌ Invalid professional title incorrectly accepted")
            return False
        
        db.close()
        print("✅ Comprehensive practitioner validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def main():
    """Run all practitioner validation tests."""
    print("🧪 Running Practitioner Validation Tests")
    print("=" * 60)
    
    tests = [
        test_specializations_validation,
        test_experience_years_validation,
        test_certification_details_validation,
        test_languages_validation,
        test_price_validation,
        test_contact_phone_validation,
        test_bio_validation,
        test_professional_title_validation,
        test_comprehensive_validation
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
        print("🎉 All practitioner validation tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)