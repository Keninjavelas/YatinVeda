"""
Performance and load tests for dual user registration system.
Tests registration endpoint performance, database query performance, and JWT token operations.
Feature: dual-user-registration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from main import app
from database import get_db
from models.database import User, Guru
from modules.auth import create_access_token, verify_token


class TestDualRegistrationPerformance:
    """Performance tests for dual user registration system."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)
        self.db = next(get_db())
        self.created_users = []  # Track created users for cleanup
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up all created users
        for user_id in self.created_users:
            try:
                guru = self.db.query(Guru).filter(Guru.user_id == user_id).first()
                user = self.db.query(User).filter(User.id == user_id).first()
                if guru:
                    self.db.delete(guru)
                if user:
                    self.db.delete(user)
                self.db.commit()
            except:
                self.db.rollback()
        self.db.close()
    
    def test_registration_endpoint_performance_under_load(self):
        """
        Test registration endpoint performance under concurrent load.
        Validates that the system can handle multiple simultaneous registrations.
        """
        num_concurrent_requests = 10
        registration_times = []
        
        def register_user(index):
            """Register a single user and measure time."""
            start_time = time.time()
            
            registration_data = {
                "username": f"perf_user_{index}_{int(time.time() * 1000)}",
                "email": f"perf_user_{index}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": f"Performance Test User",
                "role": "user"
            }
            
            try:
                response = self.client.post("/api/v1/auth/register", json=registration_data)
                end_time = time.time()
                
                if response.status_code == 200:
                    user_id = response.json().get("user_id")
                    if user_id:
                        self.created_users.append(user_id)
                    return end_time - start_time, True
                else:
                    return end_time - start_time, False
                    
            except Exception as e:
                end_time = time.time()
                return end_time - start_time, False
        
        # Execute concurrent registrations
        with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
            futures = [executor.submit(register_user, i) for i in range(num_concurrent_requests)]
            
            for future in as_completed(futures):
                duration, success = future.result()
                if success:
                    registration_times.append(duration)
        
        # Analyze performance
        assert len(registration_times) >= num_concurrent_requests * 0.8, "At least 80% of registrations should succeed"
        
        avg_time = statistics.mean(registration_times)
        max_time = max(registration_times)
        min_time = min(registration_times)
        
        # Performance assertions (adjust thresholds based on requirements)
        assert avg_time < 2.0, f"Average registration time should be under 2 seconds, got {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum registration time should be under 5 seconds, got {max_time:.2f}s"
        
        print(f"Registration Performance: avg={avg_time:.2f}s, min={min_time:.2f}s, max={max_time:.2f}s")
    
    def test_practitioner_registration_performance(self):
        """
        Test practitioner registration performance with complex data.
        Validates that practitioner registration (which involves more data) performs adequately.
        """
        num_registrations = 5
        registration_times = []
        
        for i in range(num_registrations):
            start_time = time.time()
            
            practitioner_data = {
                "username": f"perf_practitioner_{i}_{int(time.time() * 1000)}",
                "email": f"perf_practitioner_{i}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": "Performance Test Practitioner",
                "role": "practitioner",
                "professional_title": "Performance Test Astrologer",
                "bio": "This is a performance test practitioner with a comprehensive bio that includes detailed information about their experience, expertise, and approach to astrology. This bio is designed to be long enough to test performance with realistic data sizes.",
                "specializations": ["vedic_astrology", "western_astrology", "numerology", "tarot", "palmistry"],
                "experience_years": 10,
                "certification_details": {
                    "certification_type": "diploma",
                    "issuing_authority": "Performance Test Astrology Institute"
                },
                "languages": ["english", "hindi", "sanskrit", "tamil", "telugu"],
                "price_per_hour": 2000
            }
            
            try:
                response = self.client.post("/api/v1/auth/register", json=practitioner_data)
                end_time = time.time()
                
                if response.status_code == 200:
                    user_id = response.json().get("user_id")
                    if user_id:
                        self.created_users.append(user_id)
                    registration_times.append(end_time - start_time)
                
            except Exception as e:
                end_time = time.time()
                registration_times.append(end_time - start_time)
        
        # Analyze performance
        assert len(registration_times) == num_registrations
        
        avg_time = statistics.mean(registration_times)
        max_time = max(registration_times)
        
        # Practitioner registration should still be reasonably fast
        assert avg_time < 3.0, f"Average practitioner registration time should be under 3 seconds, got {avg_time:.2f}s"
        assert max_time < 6.0, f"Maximum practitioner registration time should be under 6 seconds, got {max_time:.2f}s"
        
        print(f"Practitioner Registration Performance: avg={avg_time:.2f}s, max={max_time:.2f}s")
    
    def test_database_query_performance_with_indexes(self):
        """
        Test database query performance with new indexes.
        Validates that database queries are optimized and perform well.
        """
        # Create test data
        test_users = []
        for i in range(20):
            user_data = {
                "username": f"db_perf_user_{i}_{int(time.time() * 1000)}",
                "email": f"db_perf_user_{i}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": "DB Performance Test User",
                "role": "user" if i % 2 == 0 else "practitioner"
            }
            
            if user_data["role"] == "practitioner":
                user_data.update({
                    "professional_title": "Test Astrologer",
                    "bio": "Test bio for practitioner with sufficient length to meet requirements for testing database performance and validation rules.",
                    "specializations": ["vedic_astrology"],
                    "experience_years": 5,
                    "certification_details": {
                        "certification_type": "certificate",
                        "issuing_authority": "Test Institute"
                    },
                    "languages": ["english"],
                    "price_per_hour": 1500
                })
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            if response.status_code == 200:
                user_id = response.json().get("user_id")
                if user_id:
                    test_users.append(user_id)
                    self.created_users.append(user_id)
        
        # Test query performance
        query_times = []
        
        # Test user lookup by email (should use index)
        for i in range(10):
            start_time = time.time()
            user = self.db.query(User).filter(User.email.like(f"%db_perf_user_{i}%")).first()
            end_time = time.time()
            query_times.append(end_time - start_time)
        
        # Test user lookup by username (should use index)
        for i in range(10):
            start_time = time.time()
            user = self.db.query(User).filter(User.username.like(f"%db_perf_user_{i}%")).first()
            end_time = time.time()
            query_times.append(end_time - start_time)
        
        # Test role-based queries
        start_time = time.time()
        practitioners = self.db.query(User).filter(User.role == "practitioner").all()
        end_time = time.time()
        query_times.append(end_time - start_time)
        
        start_time = time.time()
        pending_practitioners = self.db.query(User).filter(
            User.role == "practitioner",
            User.verification_status == "pending_verification"
        ).all()
        end_time = time.time()
        query_times.append(end_time - start_time)
        
        # Analyze query performance
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        # Database queries should be fast
        assert avg_query_time < 0.1, f"Average query time should be under 100ms, got {avg_query_time * 1000:.2f}ms"
        assert max_query_time < 0.5, f"Maximum query time should be under 500ms, got {max_query_time * 1000:.2f}ms"
        
        print(f"Database Query Performance: avg={avg_query_time * 1000:.2f}ms, max={max_query_time * 1000:.2f}ms")
    
    def test_jwt_token_generation_and_validation_performance(self):
        """
        Test JWT token generation and validation performance.
        Validates that token operations are fast enough for production use.
        """
        num_tokens = 100
        generation_times = []
        validation_times = []
        tokens = []
        
        # Test token generation performance
        for i in range(num_tokens):
            start_time = time.time()
            
            token_data = {
                "sub": f"test_user_{i}",
                "user_id": i,
                "is_admin": False,
                "role": "user" if i % 2 == 0 else "practitioner",
                "verification_status": "active" if i % 2 == 0 else "pending_verification"
            }
            
            token = create_access_token(data=token_data)
            end_time = time.time()
            
            generation_times.append(end_time - start_time)
            tokens.append(token)
        
        # Test token validation performance
        for token in tokens:
            start_time = time.time()
            payload = verify_token(token)
            end_time = time.time()
            
            validation_times.append(end_time - start_time)
            assert payload is not None, "Token validation should succeed"
        
        # Analyze performance
        avg_generation_time = statistics.mean(generation_times)
        avg_validation_time = statistics.mean(validation_times)
        max_generation_time = max(generation_times)
        max_validation_time = max(validation_times)
        
        # JWT operations should be very fast
        assert avg_generation_time < 0.01, f"Average token generation should be under 10ms, got {avg_generation_time * 1000:.2f}ms"
        assert avg_validation_time < 0.01, f"Average token validation should be under 10ms, got {avg_validation_time * 1000:.2f}ms"
        assert max_generation_time < 0.05, f"Maximum token generation should be under 50ms, got {max_generation_time * 1000:.2f}ms"
        assert max_validation_time < 0.05, f"Maximum token validation should be under 50ms, got {max_validation_time * 1000:.2f}ms"
        
        print(f"JWT Performance: gen_avg={avg_generation_time * 1000:.2f}ms, val_avg={avg_validation_time * 1000:.2f}ms")
    
    def test_concurrent_login_performance(self):
        """
        Test login performance under concurrent load.
        Validates that the authentication system can handle multiple simultaneous logins.
        """
        # First, create test users
        test_credentials = []
        for i in range(10):
            user_data = {
                "username": f"login_perf_user_{i}_{int(time.time() * 1000)}",
                "email": f"login_perf_user_{i}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": "Login Performance Test User",
                "role": "user"
            }
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            if response.status_code == 200:
                user_id = response.json().get("user_id")
                if user_id:
                    self.created_users.append(user_id)
                test_credentials.append({
                    "username": user_data["username"],
                    "password": user_data["password"]
                })
        
        def login_user(credentials):
            """Login a single user and measure time."""
            start_time = time.time()
            
            try:
                response = self.client.post("/api/v1/auth/login", json=credentials)
                end_time = time.time()
                
                if response.status_code == 200:
                    return end_time - start_time, True
                else:
                    return end_time - start_time, False
                    
            except Exception as e:
                end_time = time.time()
                return end_time - start_time, False
        
        # Execute concurrent logins
        login_times = []
        with ThreadPoolExecutor(max_workers=len(test_credentials)) as executor:
            futures = [executor.submit(login_user, creds) for creds in test_credentials]
            
            for future in as_completed(futures):
                duration, success = future.result()
                if success:
                    login_times.append(duration)
        
        # Analyze performance
        assert len(login_times) >= len(test_credentials) * 0.8, "At least 80% of logins should succeed"
        
        avg_time = statistics.mean(login_times)
        max_time = max(login_times)
        
        # Login should be fast
        assert avg_time < 1.0, f"Average login time should be under 1 second, got {avg_time:.2f}s"
        assert max_time < 3.0, f"Maximum login time should be under 3 seconds, got {max_time:.2f}s"
        
        print(f"Login Performance: avg={avg_time:.2f}s, max={max_time:.2f}s")
    
    def test_admin_endpoints_performance(self):
        """
        Test admin endpoint performance with realistic data volumes.
        Validates that admin operations perform well even with many practitioners.
        """
        # Create admin user
        admin_user = User(
            username="perf_admin",
            email="perf_admin@test.com",
            password_hash="test_hash",
            full_name="Performance Admin",
            role="user",
            verification_status="active",
            is_admin=True,
            created_at=datetime.utcnow()
        )
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        
        admin_token = create_access_token(
            data={
                "sub": admin_user.username,
                "user_id": admin_user.id,
                "is_admin": True,
                "role": admin_user.role,
                "verification_status": admin_user.verification_status
            }
        )
        
        # Create multiple practitioners for testing
        for i in range(15):
            practitioner_data = {
                "username": f"admin_perf_practitioner_{i}_{int(time.time() * 1000)}",
                "email": f"admin_perf_practitioner_{i}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": "Admin Performance Test Practitioner",
                "role": "practitioner",
                "professional_title": "Test Astrologer",
                "bio": "Performance test practitioner with detailed bio for testing admin endpoint performance with realistic data volumes and proper validation.",
                "specializations": ["vedic_astrology", "numerology"],
                "experience_years": 5,
                "certification_details": {
                    "certification_type": "diploma",
                    "issuing_authority": "Test Institute"
                },
                "languages": ["english"],
                "price_per_hour": 1500
            }
            
            response = self.client.post("/api/v1/auth/register", json=practitioner_data)
            if response.status_code == 200:
                user_id = response.json().get("user_id")
                if user_id:
                    self.created_users.append(user_id)
        
        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Test pending verifications endpoint performance
            start_time = time.time()
            pending_response = self.client.get("/api/v1/admin/pending-verifications", headers=headers)
            pending_time = time.time() - start_time
            
            assert pending_response.status_code == 200
            assert pending_time < 2.0, f"Pending verifications endpoint should respond in under 2 seconds, got {pending_time:.2f}s"
            
            # Test verification stats endpoint performance
            start_time = time.time()
            stats_response = self.client.get("/api/v1/admin/verification-stats", headers=headers)
            stats_time = time.time() - start_time
            
            assert stats_response.status_code == 200
            assert stats_time < 1.0, f"Verification stats endpoint should respond in under 1 second, got {stats_time:.2f}s"
            
            print(f"Admin Endpoint Performance: pending={pending_time:.2f}s, stats={stats_time:.2f}s")
            
        finally:
            # Clean up admin user
            self.db.delete(admin_user)
            self.db.commit()
    
    def test_memory_usage_during_bulk_operations(self):
        """
        Test memory usage during bulk registration operations.
        Validates that the system doesn't have memory leaks during high-volume operations.
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform bulk registrations
        num_registrations = 50
        for i in range(num_registrations):
            user_data = {
                "username": f"memory_test_user_{i}_{int(time.time() * 1000)}",
                "email": f"memory_test_user_{i}_{int(time.time() * 1000)}@example.com",
                "password": "TestPassword123",
                "full_name": "Memory Test User",
                "role": "user"
            }
            
            response = self.client.post("/api/v1/auth/register", json=user_data)
            if response.status_code == 200:
                user_id = response.json().get("user_id")
                if user_id:
                    self.created_users.append(user_id)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold based on requirements)
        assert memory_increase < 100, f"Memory increase should be under 100MB, got {memory_increase:.2f}MB"
        
        print(f"Memory Usage: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])