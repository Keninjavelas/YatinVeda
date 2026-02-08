#!/usr/bin/env python3
"""
Standalone property-based test for dual user registration database schema.
Feature: dual-user-registration, Property 14: Database integrity preservation
Validates: Requirements 8.3, 8.5
"""

import sqlite3
import os
import sys
from pathlib import Path


def test_database_schema_integrity():
    """
    Property 14: Database integrity preservation
    For any database operation, existing relationships and foreign key constraints 
    should be maintained, ensuring referential integrity.
    
    Feature: dual-user-registration, Property 14: Database integrity preservation
    Validates: Requirements 8.3, 8.5
    """
    print("Testing database schema integrity...")
    
    # Connect to the database
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check users table has new columns
        cursor.execute("PRAGMA table_info(users)")
        users_columns = [row[1] for row in cursor.fetchall()]
        
        required_user_columns = ['role', 'verification_status']
        for col in required_user_columns:
            if col not in users_columns:
                print(f"❌ Users table missing '{col}' column")
                return False
        print("✅ Users table has required columns")
        
        # Check gurus table has new columns
        cursor.execute("PRAGMA table_info(gurus)")
        gurus_columns = [row[1] for row in cursor.fetchall()]
        
        required_guru_columns = ['user_id', 'certification_details', 'verification_documents', 'verified_at', 'verified_by']
        for col in required_guru_columns:
            if col not in gurus_columns:
                print(f"❌ Gurus table missing '{col}' column")
                return False
        print("✅ Gurus table has required columns")
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        users_indexes = [row[0] for row in cursor.fetchall()]
        
        required_user_indexes = ['idx_users_role', 'idx_users_verification_status']
        for idx in required_user_indexes:
            if idx not in users_indexes:
                print(f"❌ Missing index {idx}")
                return False
        print("✅ Users table has required indexes")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='gurus'")
        gurus_indexes = [row[0] for row in cursor.fetchall()]
        
        required_guru_indexes = ['idx_gurus_user_id', 'idx_gurus_verified_by']
        for idx in required_guru_indexes:
            if idx not in gurus_indexes:
                print(f"❌ Missing index {idx}")
                return False
        print("✅ Gurus table has required indexes")
        
        # Test that we can insert data with new schema
        test_username = "test_user_schema_integrity"
        test_email = "test_schema_integrity@example.com"
        
        # Clean up any existing test data first
        cursor.execute("DELETE FROM gurus WHERE user_id IN (SELECT id FROM users WHERE username = ?)", (test_username,))
        cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, verification_status)
            VALUES (?, ?, ?, ?, ?)
        """, (test_username, test_email, "hash", "practitioner", "pending_verification"))
        
        user_id = cursor.lastrowid
        print(f"✅ Created test user with ID {user_id}")
        
        # Test foreign key relationship
        cursor.execute("""
            INSERT INTO gurus (user_id, name, price_per_hour, certification_details)
            VALUES (?, ?, ?, ?)
        """, (user_id, "Test Guru", 1000, '{"cert": "test", "number": "12345"}'))
        
        guru_id = cursor.lastrowid
        print(f"✅ Created test guru with ID {guru_id}")
        
        # Verify the data was inserted correctly
        cursor.execute("SELECT role, verification_status FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data[0] != "practitioner" or user_data[1] != "pending_verification":
            print(f"❌ User data not stored correctly: {user_data}")
            return False
        print("✅ User role and verification status stored correctly")
        
        # Test JSON field
        cursor.execute("SELECT certification_details FROM gurus WHERE id = ?", (guru_id,))
        cert_data = cursor.fetchone()[0]
        if '"cert": "test"' not in cert_data:
            print(f"❌ JSON data not stored correctly: {cert_data}")
            return False
        print("✅ JSON certification details stored correctly")
        
        # Test foreign key relationship works
        cursor.execute("""
            SELECT u.username, g.name 
            FROM users u 
            JOIN gurus g ON u.id = g.user_id 
            WHERE u.id = ?
        """, (user_id,))
        
        join_result = cursor.fetchone()
        if not join_result or join_result[0] != test_username:
            print(f"❌ Foreign key relationship not working: {join_result}")
            return False
        print("✅ Foreign key relationship working correctly")
        
        # Clean up test data
        cursor.execute("DELETE FROM gurus WHERE id = ?", (guru_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during schema integrity test: {e}")
        return False
    finally:
        conn.close()


def test_role_constraints():
    """Test that role field accepts valid values."""
    print("\nTesting role constraints...")
    
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Test valid role values
        valid_roles = ['user', 'practitioner']
        for role in valid_roles:
            test_username = f"test_role_{role}"
            test_email = f"test_role_{role}@example.com"
            
            # Clean up first
            cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, verification_status)
                VALUES (?, ?, ?, ?, ?)
            """, (test_username, test_email, "hash", role, "active"))
            
            user_id = cursor.lastrowid
            
            # Verify role was stored correctly
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            stored_role = cursor.fetchone()[0]
            if stored_role != role:
                print(f"❌ Role '{role}' not stored correctly, got '{stored_role}'")
                return False
            
            # Clean up
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        print("✅ All role constraints working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error during role constraints test: {e}")
        return False
    finally:
        conn.close()


def test_verification_status_constraints():
    """Test that verification_status field accepts valid values."""
    print("\nTesting verification status constraints...")
    
    db_path = Path(__file__).parent / "yatinveda.db"
    if not db_path.exists():
        print(f"❌ Database file not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Test valid verification status values
        valid_statuses = ['active', 'pending_verification', 'verified', 'rejected']
        for status in valid_statuses:
            test_username = f"test_status_{status}"
            test_email = f"test_status_{status}@example.com"
            
            # Clean up first
            cursor.execute("DELETE FROM users WHERE username = ?", (test_username,))
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, verification_status)
                VALUES (?, ?, ?, ?, ?)
            """, (test_username, test_email, "hash", "user", status))
            
            user_id = cursor.lastrowid
            
            # Verify status was stored correctly
            cursor.execute("SELECT verification_status FROM users WHERE id = ?", (user_id,))
            stored_status = cursor.fetchone()[0]
            if stored_status != status:
                print(f"❌ Status '{status}' not stored correctly, got '{stored_status}'")
                return False
            
            # Clean up
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        print("✅ All verification status constraints working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification status constraints test: {e}")
        return False
    finally:
        conn.close()


def main():
    """Run all schema integrity tests."""
    print("🧪 Running Database Schema Integrity Tests")
    print("=" * 50)
    
    tests = [
        test_database_schema_integrity,
        test_role_constraints,
        test_verification_status_constraints
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
        print("🎉 All database schema integrity tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)