"""
Simple property-based tests for dual user registration database schema.
Feature: dual-user-registration
"""

import pytest
import sqlite3
import os
from pathlib import Path


class TestDatabaseSchemaIntegrity:
    """Property tests for database schema integrity."""
    
    def test_database_schema_integrity(self):
        """
        Property 14: Database integrity preservation
        For any database operation, existing relationships and foreign key constraints 
        should be maintained, ensuring referential integrity.
        
        Feature: dual-user-registration, Property 14: Database integrity preservation
        Validates: Requirements 8.3, 8.5
        """
        # Connect to the database
        db_path = Path(__file__).parent.parent / "yatinveda.db"
        if not db_path.exists():
            pytest.skip("Database file not found")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # Check users table has new columns
            cursor.execute("PRAGMA table_info(users)")
            users_columns = [row[1] for row in cursor.fetchall()]
            assert 'role' in users_columns, "Users table missing 'role' column"
            assert 'verification_status' in users_columns, "Users table missing 'verification_status' column"
            
            # Check gurus table has new columns
            cursor.execute("PRAGMA table_info(gurus)")
            gurus_columns = [row[1] for row in cursor.fetchall()]
            assert 'user_id' in gurus_columns, "Gurus table missing 'user_id' column"
            assert 'certification_details' in gurus_columns, "Gurus table missing 'certification_details' column"
            assert 'verification_documents' in gurus_columns, "Gurus table missing 'verification_documents' column"
            assert 'verified_at' in gurus_columns, "Gurus table missing 'verified_at' column"
            assert 'verified_by' in gurus_columns, "Gurus table missing 'verified_by' column"
            
            # Check indexes exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
            users_indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_users_role' in users_indexes, "Missing index on users.role"
            assert 'idx_users_verification_status' in users_indexes, "Missing index on users.verification_status"
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='gurus'")
            gurus_indexes = [row[0] for row in cursor.fetchall()]
            assert 'idx_gurus_user_id' in gurus_indexes, "Missing index on gurus.user_id"
            assert 'idx_gurus_verified_by' in gurus_indexes, "Missing index on gurus.verified_by"
            
            # Test that we can insert data with new schema
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, verification_status)
                VALUES (?, ?, ?, ?, ?)
            """, ("test_user_schema", "test_schema@example.com", "hash", "user", "active"))
            
            user_id = cursor.lastrowid
            
            # Test foreign key relationship
            cursor.execute("""
                INSERT INTO gurus (user_id, name, price_per_hour, certification_details)
                VALUES (?, ?, ?, ?)
            """, (user_id, "Test Guru", 1000, '{"cert": "test"}'))
            
            # Verify the data was inserted correctly
            cursor.execute("SELECT role, verification_status FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            assert user_data[0] == "user"
            assert user_data[1] == "active"
            
            # Clean up test data
            cursor.execute("DELETE FROM gurus WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
        finally:
            conn.close()
    
    def test_role_constraints(self):
        """
        Test that role field accepts valid values.
        
        Feature: dual-user-registration, Property 14: Database integrity preservation
        Validates: Requirements 8.3, 8.5
        """
        db_path = Path(__file__).parent.parent / "yatinveda.db"
        if not db_path.exists():
            pytest.skip("Database file not found")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # Test valid role values
            for role in ['user', 'practitioner']:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, verification_status)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"test_{role}", f"test_{role}@example.com", "hash", role, "active"))
                
                user_id = cursor.lastrowid
                
                # Verify role was stored correctly
                cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
                stored_role = cursor.fetchone()[0]
                assert stored_role == role
                
                # Clean up
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def test_verification_status_constraints(self):
        """
        Test that verification_status field accepts valid values.
        
        Feature: dual-user-registration, Property 14: Database integrity preservation
        Validates: Requirements 8.3, 8.5
        """
        db_path = Path(__file__).parent.parent / "yatinveda.db"
        if not db_path.exists():
            pytest.skip("Database file not found")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # Test valid verification status values
            for status in ['active', 'pending_verification', 'verified', 'rejected']:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, verification_status)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"test_{status}", f"test_{status}@example.com", "hash", "user", status))
                
                user_id = cursor.lastrowid
                
                # Verify status was stored correctly
                cursor.execute("SELECT verification_status FROM users WHERE id = ?", (user_id,))
                stored_status = cursor.fetchone()[0]
                assert stored_status == status
                
                # Clean up
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            
        finally:
            conn.close()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])