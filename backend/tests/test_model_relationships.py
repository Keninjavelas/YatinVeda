#!/usr/bin/env python3
"""
Property test for model relationships in dual user registration.
Feature: dual-user-registration, Property 6: Practitioner record creation with proper relationships
Validates: Requirements 3.5, 8.2
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime


def test_practitioner_record_creation():
    """
    Property 6: Practitioner record creation with proper relationships
    For any successful practitioner registration, both a User record and a linked Guru record 
    should be created with proper foreign key relationships.
    
    Feature: dual-user-registration, Property 6: Practitioner record creation with proper relationships
    Validates: Requirements 3.5, 8.2
    """
    print("Testing practitioner record creation with relationships...")
    
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Test data for practitioner registration
        test_cases = [
            {
                "username": "test_practitioner_1",
                "email": "practitioner1@example.com",
                "role": "practitioner",
                "verification_status": "pending_verification",
                "guru_name": "Dr. Astro Guru",
                "specializations": ["vedic_astrology", "numerology"],
                "experience_years": 10,
                "certification": {"cert_number": "AST001", "issuer": "Vedic Institute"}
            },
            {
                "username": "test_practitioner_2", 
                "email": "practitioner2@example.com",
                "role": "practitioner",
                "verification_status": "pending_verification",
                "guru_name": "Pandit Jyotish",
                "specializations": ["tarot", "palmistry"],
                "experience_years": 5,
                "certification": {"cert_number": "TAR002", "issuer": "Tarot Academy"}
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n  Testing case {i+1}: {test_case['username']}")
            
            # Clean up any existing test data
            cursor.execute("DELETE FROM gurus WHERE user_id IN (SELECT id FROM users WHERE username = ?)", 
                          (test_case['username'],))
            cursor.execute("DELETE FROM users WHERE username = ?", (test_case['username'],))
            
            # Step 1: Create User record (practitioner)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, verification_status)
                VALUES (?, ?, ?, ?, ?)
            """, (test_case['username'], test_case['email'], "hashed_password", 
                  test_case['role'], test_case['verification_status']))
            
            user_id = cursor.lastrowid
            print(f"    ✅ Created user record with ID {user_id}")
            
            # Step 2: Create linked Guru record
            cursor.execute("""
                INSERT INTO gurus (user_id, name, price_per_hour, specializations, experience_years, certification_details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, test_case['guru_name'], 2000, 
                  json.dumps(test_case['specializations']), 
                  test_case['experience_years'],
                  json.dumps(test_case['certification'])))
            
            guru_id = cursor.lastrowid
            print(f"    ✅ Created guru record with ID {guru_id}")
            
            # Step 3: Verify foreign key relationship
            cursor.execute("""
                SELECT u.id, u.username, u.role, u.verification_status,
                       g.id, g.name, g.user_id, g.specializations, g.certification_details
                FROM users u
                JOIN gurus g ON u.id = g.user_id
                WHERE u.id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                print(f"    ❌ Failed to join user and guru records")
                return False
            
            # Verify all data is correct
            user_data = result[:4]
            guru_data = result[4:]
            
            if user_data[1] != test_case['username']:
                print(f"    ❌ Username mismatch: expected {test_case['username']}, got {user_data[1]}")
                return False
            
            if user_data[2] != test_case['role']:
                print(f"    ❌ Role mismatch: expected {test_case['role']}, got {user_data[2]}")
                return False
            
            if guru_data[2] != user_id:  # g.user_id should match u.id
                print(f"    ❌ Foreign key mismatch: expected {user_id}, got {guru_data[2]}")
                return False
            
            # Verify JSON fields
            stored_specializations = json.loads(guru_data[3])
            if stored_specializations != test_case['specializations']:
                print(f"    ❌ Specializations mismatch: expected {test_case['specializations']}, got {stored_specializations}")
                return False
            
            stored_certification = json.loads(guru_data[4])
            if stored_certification != test_case['certification']:
                print(f"    ❌ Certification mismatch: expected {test_case['certification']}, got {stored_certification}")
                return False
            
            print(f"    ✅ All relationship data verified correctly")
            
            # Step 4: Test that we can query in both directions
            # User -> Guru
            cursor.execute("SELECT COUNT(*) FROM gurus WHERE user_id = ?", (user_id,))
            guru_count = cursor.fetchone()[0]
            if guru_count != 1:
                print(f"    ❌ Expected 1 guru for user {user_id}, got {guru_count}")
                return False
            
            # Guru -> User
            cursor.execute("SELECT COUNT(*) FROM users WHERE id = (SELECT user_id FROM gurus WHERE id = ?)", (guru_id,))
            user_count = cursor.fetchone()[0]
            if user_count != 1:
                print(f"    ❌ Expected 1 user for guru {guru_id}, got {user_count}")
                return False
            
            print(f"    ✅ Bidirectional relationship queries work correctly")
            
            # Clean up test data
            cursor.execute("DELETE FROM gurus WHERE id = ?", (guru_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
        conn.commit()
        print("\n✅ All practitioner record creation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error during practitioner record creation test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_verification_relationship():
    """
    Test the verification relationship (verified_by foreign key).
    For any guru verification, the verified_by field should correctly reference an admin user.
    
    Feature: dual-user-registration, Property 6: Practitioner record creation with proper relationships
    Validates: Requirements 3.5, 8.2
    """
    print("\nTesting verification relationship...")
    
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Clean up any existing test data
        test_usernames = ["test_practitioner_verify", "test_admin_verify"]
        for username in test_usernames:
            cursor.execute("DELETE FROM gurus WHERE user_id IN (SELECT id FROM users WHERE username = ?)", (username,))
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, verification_status, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("test_admin_verify", "admin@example.com", "hash", "user", "active", True))
        
        admin_id = cursor.lastrowid
        print(f"  ✅ Created admin user with ID {admin_id}")
        
        # Create practitioner user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, verification_status)
            VALUES (?, ?, ?, ?, ?)
        """, ("test_practitioner_verify", "practitioner@example.com", "hash", "practitioner", "pending_verification"))
        
        practitioner_id = cursor.lastrowid
        print(f"  ✅ Created practitioner user with ID {practitioner_id}")
        
        # Create guru record
        cursor.execute("""
            INSERT INTO gurus (user_id, name, price_per_hour)
            VALUES (?, ?, ?)
        """, (practitioner_id, "Test Verification Guru", 1500))
        
        guru_id = cursor.lastrowid
        print(f"  ✅ Created guru record with ID {guru_id}")
        
        # Simulate verification process
        verification_time = datetime.now().isoformat()
        cursor.execute("""
            UPDATE gurus 
            SET verified_by = ?, verified_at = ?
            WHERE id = ?
        """, (admin_id, verification_time, guru_id))
        
        # Update user verification status
        cursor.execute("""
            UPDATE users 
            SET verification_status = ?
            WHERE id = ?
        """, ("verified", practitioner_id))
        
        print(f"  ✅ Simulated verification by admin {admin_id}")
        
        # Test the verification relationship
        cursor.execute("""
            SELECT g.id, g.name, g.verified_by, g.verified_at,
                   u_practitioner.username as practitioner_username,
                   u_admin.username as admin_username, u_admin.is_admin
            FROM gurus g
            JOIN users u_practitioner ON g.user_id = u_practitioner.id
            LEFT JOIN users u_admin ON g.verified_by = u_admin.id
            WHERE g.id = ?
        """, (guru_id,))
        
        result = cursor.fetchone()
        if not result:
            print(f"  ❌ Failed to retrieve verification relationship data")
            return False
        
        guru_id_result, guru_name, verified_by, verified_at, practitioner_username, admin_username, is_admin = result
        
        # Verify the relationships
        if verified_by != admin_id:
            print(f"  ❌ Verified_by mismatch: expected {admin_id}, got {verified_by}")
            return False
        
        if admin_username != "test_admin_verify":
            print(f"  ❌ Admin username mismatch: expected test_admin_verify, got {admin_username}")
            return False
        
        if not is_admin:
            print(f"  ❌ Verifier is not an admin user")
            return False
        
        if practitioner_username != "test_practitioner_verify":
            print(f"  ❌ Practitioner username mismatch: expected test_practitioner_verify, got {practitioner_username}")
            return False
        
        print(f"  ✅ Verification relationship data verified correctly")
        
        # Clean up test data
        cursor.execute("DELETE FROM gurus WHERE id = ?", (guru_id,))
        cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (practitioner_id, admin_id))
        conn.commit()
        
        print("✅ Verification relationship test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification relationship test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def test_unique_constraints():
    """
    Test unique constraints on user_id in gurus table.
    For any user, there should be at most one guru profile.
    
    Feature: dual-user-registration, Property 6: Practitioner record creation with proper relationships
    Validates: Requirements 3.5, 8.2
    """
    print("\nTesting unique constraints...")
    
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Clean up any existing test data
        cursor.execute("DELETE FROM gurus WHERE user_id IN (SELECT id FROM users WHERE username = ?)", ("test_unique_constraint",))
        cursor.execute("DELETE FROM users WHERE username = ?", ("test_unique_constraint",))
        
        # Create test user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, verification_status)
            VALUES (?, ?, ?, ?, ?)
        """, ("test_unique_constraint", "unique@example.com", "hash", "practitioner", "pending_verification"))
        
        user_id = cursor.lastrowid
        print(f"  ✅ Created test user with ID {user_id}")
        
        # Create first guru record
        cursor.execute("""
            INSERT INTO gurus (user_id, name, price_per_hour)
            VALUES (?, ?, ?)
        """, (user_id, "First Guru Profile", 1000))
        
        guru_id_1 = cursor.lastrowid
        print(f"  ✅ Created first guru record with ID {guru_id_1}")
        
        # Try to create second guru record with same user_id (should fail due to unique constraint)
        try:
            cursor.execute("""
                INSERT INTO gurus (user_id, name, price_per_hour)
                VALUES (?, ?, ?)
            """, (user_id, "Second Guru Profile", 2000))
            
            # If we get here, the unique constraint didn't work
            print(f"  ❌ Unique constraint failed - was able to create duplicate guru profile")
            return False
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                print(f"  ✅ Unique constraint working correctly - prevented duplicate guru profile")
            else:
                print(f"  ❌ Unexpected integrity error: {e}")
                return False
        
        # Verify only one guru record exists for the user
        cursor.execute("SELECT COUNT(*) FROM gurus WHERE user_id = ?", (user_id,))
        guru_count = cursor.fetchone()[0]
        if guru_count != 1:
            print(f"  ❌ Expected 1 guru record, found {guru_count}")
            return False
        
        print(f"  ✅ Confirmed only one guru record exists for user {user_id}")
        
        # Clean up test data
        cursor.execute("DELETE FROM gurus WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        print("✅ Unique constraints test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error during unique constraints test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Run all model relationship tests."""
    print("🧪 Running Model Relationship Tests")
    print("=" * 50)
    
    tests = [
        test_practitioner_record_creation,
        test_verification_relationship,
        test_unique_constraints
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All model relationship tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)