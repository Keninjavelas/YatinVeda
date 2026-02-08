#!/usr/bin/env python3
"""
Property test for registration data validation in dual user registration.
Feature: dual-user-registration, Property 3: Required field validation for both user types
Validates: Requirements 2.1, 3.1, 3.2, 3.3
"""

import sys
from pathlib import Path
import json
from pydantic import ValidationError

# Add the backend directory to the path so we can import our schemas
sys.path.append(str(Path(__file__).parent))

try:
    from schemas.dual_registration import (
        UserRegistrationData, PractitionerRegistrationData, 
        BaseRegistrationData, FormConfig
    )
except ImportError as e:
    print(f"❌ Failed to import schemas: {e}")
    sys.exit(1)


def test_user_registration_required_fields():
    """
    Property 3: Required field validation for user registration
    For any user registration attempt, all required fields (username, email, password) 
    should be validated, and registration should fail if any required field is missing or invalid.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 2.1
    """
    print("Testing user registration required field validation...")
    
    # Valid base data
    valid_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "StrongPass123!",
        "role": "user"
    }
    
    # Test that valid data passes
    try:
        user_reg = UserRegistrationData(**valid_data)
        print("  ✅ Valid user registration data accepted")
    except ValidationError as e:
        print(f"  ❌ Valid data rejected: {e}")
        return False
    
    # Test required fields
    required_fields = ["username", "email", "password"]
    
    for field in required_fields:
        # Test missing field
        test_data = valid_data.copy()
        del test_data[field]
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ❌ Missing {field} was not caught")
            return False
        except ValidationError as e:
            if field in str(e):
                print(f"  ✅ Missing {field} correctly rejected")
            else:
                print(f"  ❌ Missing {field} error message unclear: {e}")
                return False
        
        # Test empty field
        test_data = valid_data.copy()
        test_data[field] = ""
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ❌ Empty {field} was not caught")
            return False
        except ValidationError as e:
            print(f"  ✅ Empty {field} correctly rejected")
    
    print("✅ User registration required field validation passed")
    return True


def test_practitioner_registration_required_fields():
    """
    Property 3: Required field validation for practitioner registration
    For any practitioner registration attempt, all required fields should be validated,
    and registration should fail if any required field is missing or invalid.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 3.1, 3.2, 3.3
    """
    print("\nTesting practitioner registration required field validation...")
    
    # Valid base data
    valid_data = {
        "username": "testguru123",
        "email": "guru@example.com", 
        "password": "StrongPass123!",
        "role": "practitioner",
        "professional_title": "Vedic Astrologer",
        "bio": "Experienced astrologer with over 10 years of practice in Vedic astrology and spiritual guidance.",
        "specializations": ["vedic_astrology", "numerology"],
        "experience_years": 10,
        "certification_details": {
            "certification_type": "diploma",
            "issuing_authority": "Indian Institute of Astrology"
        }
    }
    
    # Test that valid data passes
    try:
        practitioner_reg = PractitionerRegistrationData(**valid_data)
        print("  ✅ Valid practitioner registration data accepted")
    except ValidationError as e:
        print(f"  ❌ Valid data rejected: {e}")
        return False
    
    # Test required fields (base + practitioner-specific)
    required_fields = [
        "username", "email", "password", "professional_title", 
        "bio", "specializations", "experience_years", "certification_details"
    ]
    
    for field in required_fields:
        # Test missing field
        test_data = valid_data.copy()
        del test_data[field]
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ❌ Missing {field} was not caught")
            return False
        except ValidationError as e:
            if field in str(e):
                print(f"  ✅ Missing {field} correctly rejected")
            else:
                print(f"  ❌ Missing {field} error message unclear: {e}")
                return False
        
        # Test empty/invalid field values
        test_data = valid_data.copy()
        
        if field in ["username", "email", "password", "professional_title", "bio"]:
            test_data[field] = ""
        elif field == "specializations":
            test_data[field] = []
        elif field == "experience_years":
            test_data[field] = -1  # Invalid negative value
        elif field == "certification_details":
            test_data[field] = {}  # Empty dict missing required fields
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ❌ Invalid {field} was not caught")
            return False
        except ValidationError as e:
            print(f"  ✅ Invalid {field} correctly rejected")
    
    print("✅ Practitioner registration required field validation passed")
    return True


def test_username_validation():
    """
    Test username validation rules.
    For any username, it should follow the format rules and not be reserved.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 2.1, 3.1
    """
    print("\nTesting username validation...")
    
    base_data = {
        "email": "test@example.com",
        "password": "StrongPass123!",
        "role": "user"
    }
    
    # Valid usernames
    valid_usernames = ["user123", "test_user", "guru-astro", "vedic123", "a1b2c3"]
    
    for username in valid_usernames:
        test_data = base_data.copy()
        test_data["username"] = username
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ✅ Valid username '{username}' accepted")
        except ValidationError as e:
            print(f"  ❌ Valid username '{username}' rejected: {e}")
            return False
    
    # Invalid usernames
    invalid_usernames = [
        ("ab", "too short"),
        ("user@name", "contains @"),
        ("user name", "contains space"),
        ("user.name", "contains period"),
        ("admin", "reserved word"),
        ("root", "reserved word"),
        ("a" * 51, "too long")
    ]
    
    for username, reason in invalid_usernames:
        test_data = base_data.copy()
        test_data["username"] = username
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ❌ Invalid username '{username}' ({reason}) was accepted")
            return False
        except ValidationError as e:
            print(f"  ✅ Invalid username '{username}' ({reason}) correctly rejected")
    
    print("✅ Username validation passed")
    return True


def test_password_validation():
    """
    Test password validation rules.
    For any password, it should meet strength requirements.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 2.1, 3.1
    """
    print("\nTesting password validation...")
    
    base_data = {
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }
    
    # Valid passwords
    valid_passwords = ["StrongPass123!", "MySecure1Pass", "Test123Password", "Guru@2024"]
    
    for password in valid_passwords:
        test_data = base_data.copy()
        test_data["password"] = password
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ✅ Valid password accepted")
        except ValidationError as e:
            print(f"  ❌ Valid password rejected: {e}")
            return False
    
    # Invalid passwords
    invalid_passwords = [
        ("short", "too short"),
        ("nouppercase123", "no uppercase"),
        ("NOLOWERCASE123", "no lowercase"),
        ("NoNumbers!", "no digits"),
        ("a" * 73, "too long for bcrypt")
    ]
    
    for password, reason in invalid_passwords:
        test_data = base_data.copy()
        test_data["password"] = password
        
        try:
            UserRegistrationData(**test_data)
            print(f"  ❌ Invalid password ({reason}) was accepted")
            return False
        except ValidationError as e:
            print(f"  ✅ Invalid password ({reason}) correctly rejected")
    
    print("✅ Password validation passed")
    return True


def test_specializations_validation():
    """
    Test specializations validation for practitioners.
    For any specializations list, it should contain only valid specializations.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 3.2
    """
    print("\nTesting specializations validation...")
    
    base_data = {
        "username": "testguru",
        "email": "guru@example.com",
        "password": "StrongPass123!",
        "role": "practitioner",
        "professional_title": "Astrologer",
        "bio": "Experienced astrologer with deep knowledge of Vedic traditions and modern applications.",
        "experience_years": 5,
        "certification_details": {
            "certification_type": "diploma",
            "issuing_authority": "Astrology Institute"
        }
    }
    
    # Valid specializations
    valid_specializations = [
        ["vedic_astrology"],
        ["tarot", "numerology"],
        ["palmistry", "vastu", "gemology"],
        ["career_guidance", "relationship_counseling"]
    ]
    
    for specs in valid_specializations:
        test_data = base_data.copy()
        test_data["specializations"] = specs
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ✅ Valid specializations {specs} accepted")
        except ValidationError as e:
            print(f"  ❌ Valid specializations {specs} rejected: {e}")
            return False
    
    # Invalid specializations
    invalid_specializations = [
        ([], "empty list"),
        (["invalid_spec"], "invalid specialization"),
        (["vedic_astrology", "fake_astrology"], "contains invalid"),
        (["vedic_astrology"] * 11, "too many items")
    ]
    
    for specs, reason in invalid_specializations:
        test_data = base_data.copy()
        test_data["specializations"] = specs
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ❌ Invalid specializations ({reason}) was accepted")
            return False
        except ValidationError as e:
            print(f"  ✅ Invalid specializations ({reason}) correctly rejected")
    
    print("✅ Specializations validation passed")
    return True


def test_certification_details_validation():
    """
    Test certification details validation for practitioners.
    For any certification details, it should contain required fields with valid values.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 3.3
    """
    print("\nTesting certification details validation...")
    
    base_data = {
        "username": "testguru",
        "email": "guru@example.com",
        "password": "StrongPass123!",
        "role": "practitioner",
        "professional_title": "Astrologer",
        "bio": "Experienced astrologer with comprehensive training in traditional methods.",
        "specializations": ["vedic_astrology"],
        "experience_years": 5
    }
    
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
        }
    ]
    
    for cert in valid_certifications:
        test_data = base_data.copy()
        test_data["certification_details"] = cert
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ✅ Valid certification details accepted")
        except ValidationError as e:
            print(f"  ❌ Valid certification details rejected: {e}")
            return False
    
    # Invalid certification details
    invalid_certifications = [
        ({}, "empty dict"),
        ({"certification_type": "diploma"}, "missing issuing_authority"),
        ({"issuing_authority": "Some Institute"}, "missing certification_type"),
        ({"certification_type": "invalid_type", "issuing_authority": "Institute"}, "invalid certification_type"),
        ({"certification_type": "diploma", "issuing_authority": ""}, "empty issuing_authority")
    ]
    
    for cert, reason in invalid_certifications:
        test_data = base_data.copy()
        test_data["certification_details"] = cert
        
        try:
            PractitionerRegistrationData(**test_data)
            print(f"  ❌ Invalid certification details ({reason}) was accepted")
            return False
        except ValidationError as e:
            print(f"  ✅ Invalid certification details ({reason}) correctly rejected")
    
    print("✅ Certification details validation passed")
    return True


def test_form_configuration():
    """
    Test form configuration generation for both user types.
    For any user role, the appropriate form configuration should be generated.
    
    Feature: dual-user-registration, Property 3: Required field validation for both user types
    Validates: Requirements 2.1, 3.1, 3.2, 3.3
    """
    print("\nTesting form configuration...")
    
    # Test user form configuration
    try:
        user_config = FormConfig.get_user_form_config()
        assert user_config.role == "user"
        assert len(user_config.fields) >= 4  # username, email, password, full_name
        
        field_names = [field.name for field in user_config.fields]
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            assert field in field_names, f"Missing required field {field} in user form config"
        
        print("  ✅ User form configuration generated correctly")
    except Exception as e:
        print(f"  ❌ User form configuration failed: {e}")
        return False
    
    # Test practitioner form configuration
    try:
        practitioner_config = FormConfig.get_practitioner_form_config()
        assert practitioner_config.role == "practitioner"
        assert len(practitioner_config.fields) >= 8  # All required fields
        
        field_names = [field.name for field in practitioner_config.fields]
        required_fields = [
            "username", "email", "password", "professional_title", 
            "bio", "specializations", "experience_years", "certification_details"
        ]
        for field in required_fields:
            assert field in field_names, f"Missing required field {field} in practitioner form config"
        
        # Check that specializations field has options
        spec_field = next((f for f in practitioner_config.fields if f.name == "specializations"), None)
        assert spec_field is not None, "Specializations field not found"
        assert spec_field.options is not None, "Specializations field missing options"
        assert len(spec_field.options) > 10, "Specializations options too few"
        
        print("  ✅ Practitioner form configuration generated correctly")
    except Exception as e:
        print(f"  ❌ Practitioner form configuration failed: {e}")
        return False
    
    print("✅ Form configuration test passed")
    return True


def main():
    """Run all registration validation tests."""
    print("🧪 Running Registration Data Validation Tests")
    print("=" * 60)
    
    tests = [
        test_user_registration_required_fields,
        test_practitioner_registration_required_fields,
        test_username_validation,
        test_password_validation,
        test_specializations_validation,
        test_certification_details_validation,
        test_form_configuration
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
        print("🎉 All registration data validation tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)