#!/usr/bin/env python3
"""
Property test for verification workflow in dual user registration.
Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
Validates: Requirements 4.4
"""

import sys
from pathlib import Path
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the backend directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

try:
    from models.database import Base, User, Guru
    from services.verification_service import VerificationService
    from services.user_service import UserService
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


def create_test_practitioner(db, user_service):
    """Create a test practitioner for verification testing."""
    registration_data = PractitionerRegistrationData(
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
        }
    )
    
    user, guru = user_service.create_practitioner(registration_data)
    return user, guru


def create_admin_user(db):
    """Create an admin user for verification testing."""
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash="hashed_password",
        role="user",
        verification_status="active",
        is_admin=True,
        created_at=datetime.utcnow()
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def test_pending_verification_listing():
    """
    Property 9: Pending verification listing
    For any practitioners with pending verification status, they should appear in the pending list.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("Testing pending verification listing...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create test practitioner
        user, guru = create_test_practitioner(db, user_service)
        
        # Store IDs before closing session
        user_id = user.id
        guru_id = guru.id
        
        # Check that practitioner appears in pending list
        # Force a commit to ensure data is persisted
        db.commit()
        
        # Create a fresh session to avoid any caching issues
        db.close()
        db = SessionLocal()
        verification_service = VerificationService(db)
        
        pending_list = verification_service.get_pending_verifications()
        
        if len(pending_list) == 1:
            print("  ✅ Pending practitioner appears in verification list")
        else:
            print(f"  ❌ Expected 1 pending practitioner, found {len(pending_list)}")
            # Debug: Check what's actually in the database
            all_users = db.query(User).all()
            all_gurus = db.query(Guru).all()
            print(f"  Debug: Total users: {len(all_users)}, Total gurus: {len(all_gurus)}")
            for u in all_users:
                print(f"    User {u.id}: role={u.role}, status={u.verification_status}")
            for g in all_gurus:
                print(f"    Guru {g.id}: user_id={g.user_id}, verified={g.is_verified}")
            return False
        
        # Verify the data in the pending list
        pending_item = pending_list[0]
        if (pending_item["guru_id"] == guru_id and 
            pending_item["user_id"] == user_id and
            pending_item["verification_status"] == "pending_verification"):
            print("  ✅ Pending practitioner data is correct")
        else:
            print("  ❌ Pending practitioner data is incorrect")
            return False
        
        db.close()
        print("✅ Pending verification listing passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_practitioner_approval_workflow():
    """
    Property 9: Practitioner approval workflow
    For any practitioner approval, the status should transition correctly and functionality should change.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("\nTesting practitioner approval workflow...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create test practitioner and admin
        user, guru = create_test_practitioner(db, user_service)
        admin = create_admin_user(db)
        
        # Verify initial status
        if user.verification_status == "pending_verification" and not guru.is_verified:
            print("  ✅ Initial verification status is correct")
        else:
            print(f"  ❌ Initial status incorrect: user={user.verification_status}, guru={guru.is_verified}")
            return False
        
        # Approve the practitioner
        result = verification_service.approve_practitioner(guru.id, admin.id, "Test approval")
        
        if result["success"]:
            print("  ✅ Practitioner approval succeeded")
        else:
            print(f"  ❌ Practitioner approval failed: {result}")
            return False
        
        # Refresh objects to get updated status
        db.refresh(user)
        db.refresh(guru)
        
        # Verify status after approval
        if (user.verification_status == "verified" and 
            guru.is_verified and 
            guru.verified_at is not None and
            guru.verified_by == admin.id):
            print("  ✅ Post-approval status is correct")
        else:
            print(f"  ❌ Post-approval status incorrect: user={user.verification_status}, guru_verified={guru.is_verified}")
            return False
        
        # Verify practitioner no longer appears in pending list
        pending_list = verification_service.get_pending_verifications()
        if len(pending_list) == 0:
            print("  ✅ Approved practitioner removed from pending list")
        else:
            print(f"  ❌ Approved practitioner still in pending list: {len(pending_list)}")
            return False
        
        db.close()
        print("✅ Practitioner approval workflow passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_practitioner_rejection_workflow():
    """
    Property 9: Practitioner rejection workflow
    For any practitioner rejection, the status should transition correctly.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("\nTesting practitioner rejection workflow...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create test practitioner and admin
        user, guru = create_test_practitioner(db, user_service)
        admin = create_admin_user(db)
        
        # Reject the practitioner
        result = verification_service.reject_practitioner(
            guru.id, admin.id, "Insufficient documentation", "Need more certification details"
        )
        
        if result["success"]:
            print("  ✅ Practitioner rejection succeeded")
        else:
            print(f"  ❌ Practitioner rejection failed: {result}")
            return False
        
        # Refresh objects to get updated status
        db.refresh(user)
        db.refresh(guru)
        
        # Verify status after rejection
        if (user.verification_status == "rejected" and 
            not guru.is_verified and
            guru.verification_documents is not None and
            "rejection_info" in guru.verification_documents):
            print("  ✅ Post-rejection status is correct")
        else:
            print(f"  ❌ Post-rejection status incorrect: user={user.verification_status}, guru_verified={guru.is_verified}")
            return False
        
        # Verify rejection information is stored
        rejection_info = guru.verification_documents["rejection_info"]
        if (rejection_info["rejected_by"] == admin.id and
            rejection_info["rejection_reason"] == "Insufficient documentation"):
            print("  ✅ Rejection information stored correctly")
        else:
            print(f"  ❌ Rejection information incorrect: {rejection_info}")
            return False
        
        # Verify practitioner no longer appears in pending list
        pending_list = verification_service.get_pending_verifications()
        if len(pending_list) == 0:
            print("  ✅ Rejected practitioner removed from pending list")
        else:
            print(f"  ❌ Rejected practitioner still in pending list: {len(pending_list)}")
            return False
        
        db.close()
        print("✅ Practitioner rejection workflow passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_verification_status_reset():
    """
    Property 9: Verification status reset
    For any verification status reset, the practitioner should return to pending status.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("\nTesting verification status reset...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create test practitioner and admin
        user, guru = create_test_practitioner(db, user_service)
        admin = create_admin_user(db)
        
        # First approve the practitioner
        verification_service.approve_practitioner(guru.id, admin.id, "Initial approval")
        db.refresh(user)
        db.refresh(guru)
        
        # Verify approved status
        if user.verification_status == "verified" and guru.is_verified:
            print("  ✅ Practitioner initially approved")
        else:
            print("  ❌ Initial approval failed")
            return False
        
        # Reset verification status
        result = verification_service.reset_verification_status(
            guru.id, admin.id, "Profile changes require re-verification"
        )
        
        if result["success"]:
            print("  ✅ Verification status reset succeeded")
        else:
            print(f"  ❌ Verification status reset failed: {result}")
            return False
        
        # Refresh objects to get updated status
        db.refresh(user)
        db.refresh(guru)
        
        # Verify status after reset
        if (user.verification_status == "pending_verification" and 
            not guru.is_verified and
            guru.verified_at is None and
            guru.verified_by is None):
            print("  ✅ Post-reset status is correct")
        else:
            print(f"  ❌ Post-reset status incorrect: user={user.verification_status}, guru_verified={guru.is_verified}")
            return False
        
        # Verify reset information is stored
        if (guru.verification_documents and 
            "reset_history" in guru.verification_documents and
            len(guru.verification_documents["reset_history"]) == 1):
            reset_info = guru.verification_documents["reset_history"][0]
            if (reset_info["reset_by"] == admin.id and
                reset_info["reset_reason"] == "Profile changes require re-verification"):
                print("  ✅ Reset information stored correctly")
            else:
                print(f"  ❌ Reset information incorrect: {reset_info}")
                return False
        else:
            print("  ❌ Reset history not stored")
            return False
        
        # Verify practitioner appears in pending list again
        db.commit()  # Ensure changes are committed
        pending_list = verification_service.get_pending_verifications()
        if len(pending_list) == 1 and pending_list[0]["guru_id"] == guru.id:
            print("  ✅ Reset practitioner appears in pending list")
        else:
            print(f"  ❌ Reset practitioner not in pending list: {len(pending_list)}")
            return False
        
        db.close()
        print("✅ Verification status reset passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_verification_requirements_checking():
    """
    Property 9: Verification requirements checking
    For any practitioner, verification requirements should be correctly identified.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("\nTesting verification requirements checking...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create test practitioner
        user, guru = create_test_practitioner(db, user_service)
        
        # Get verification details
        details = verification_service.get_verification_details(guru.id)
        
        if details is None:
            print("  ❌ Could not get verification details")
            return False
        
        # Check that practitioner is ready for verification
        if details["is_ready_for_verification"]:
            print("  ✅ Complete practitioner is ready for verification")
        else:
            print("  ❌ Complete practitioner not ready for verification")
            return False
        
        # Check verification requirements
        requirements = details["verification_requirements"]
        if len(requirements) >= 5:  # Should have at least 5 requirements
            print(f"  ✅ Found {len(requirements)} verification requirements")
        else:
            print(f"  ❌ Expected at least 5 requirements, found {len(requirements)}")
            return False
        
        # All requirements should be satisfied for our complete practitioner
        unsatisfied = [req for req in requirements if not req["satisfied"]]
        if len(unsatisfied) == 0:
            print("  ✅ All requirements satisfied for complete practitioner")
        else:
            print(f"  ❌ {len(unsatisfied)} requirements not satisfied: {[req['requirement'] for req in unsatisfied]}")
            return False
        
        # Test with incomplete practitioner
        # Create practitioner with missing bio
        incomplete_guru = Guru(
            user_id=user.id + 1,  # Different user ID
            professional_title="Test Guru",
            bio="Short",  # Too short
            specializations=["vedic_astrology"],
            experience_years=5,
            certification_details={
                "certification_type": "diploma",
                "issuing_authority": "Test Institute"
            },
            is_verified=False,
            created_at=datetime.utcnow()
        )
        
        db.add(incomplete_guru)
        db.commit()
        db.refresh(incomplete_guru)
        
        # Check requirements for incomplete practitioner
        incomplete_requirements = verification_service._get_verification_requirements(incomplete_guru)
        bio_requirement = next((req for req in incomplete_requirements if req["requirement"] == "Biography"), None)
        
        if bio_requirement and not bio_requirement["satisfied"]:
            print("  ✅ Incomplete bio correctly identified as unsatisfied")
        else:
            print("  ❌ Incomplete bio not correctly identified")
            return False
        
        db.close()
        print("✅ Verification requirements checking passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def test_verification_statistics():
    """
    Property 9: Verification statistics
    For any set of practitioners, statistics should be correctly calculated.
    
    Feature: dual-user-registration, Property 9: Verification status transitions and functionality changes
    Validates: Requirements 4.4
    """
    print("\nTesting verification statistics...")
    
    engine, SessionLocal, db_path = create_test_database()
    
    try:
        db = SessionLocal()
        user_service = UserService(db)
        verification_service = VerificationService(db)
        
        # Create multiple practitioners with different statuses
        admin = create_admin_user(db)
        
        # Create 3 practitioners
        practitioners = []
        for i in range(3):
            registration_data = PractitionerRegistrationData(
                username=f"guru{i}",
                email=f"guru{i}@example.com",
                password="StrongPass123!",
                role="practitioner",
                professional_title="Vedic Astrologer",
                bio="Experienced astrologer with comprehensive knowledge of Vedic traditions and modern applications.",
                specializations=["vedic_astrology"],
                experience_years=10,
                certification_details={
                    "certification_type": "diploma",
                    "issuing_authority": "Indian Institute of Astrology"
                }
            )
            user, guru = user_service.create_practitioner(registration_data)
            practitioners.append((user, guru))
        
        # Approve first practitioner
        verification_service.approve_practitioner(practitioners[0][1].id, admin.id, "Approved")
        
        # Reject second practitioner
        verification_service.reject_practitioner(practitioners[1][1].id, admin.id, "Rejected", "Test rejection")
        
        # Leave third practitioner pending
        
        # Get statistics
        stats = verification_service.get_verification_statistics()
        
        # Verify statistics
        expected_stats = {
            "total_practitioners": 3,
            "pending_verification": 1,
            "verified": 1,
            "rejected": 1
        }
        
        for key, expected_value in expected_stats.items():
            if stats[key] == expected_value:
                print(f"  ✅ {key}: {stats[key]} (correct)")
            else:
                print(f"  ❌ {key}: expected {expected_value}, got {stats[key]}")
                return False
        
        # Check verification rate
        expected_rate = 1/3 * 100  # 1 verified out of 3 total
        if abs(stats["verification_rate"] - expected_rate) < 0.01:
            print(f"  ✅ Verification rate: {stats['verification_rate']:.1f}% (correct)")
        else:
            print(f"  ❌ Verification rate: expected {expected_rate:.1f}%, got {stats['verification_rate']:.1f}%")
            return False
        
        db.close()
        print("✅ Verification statistics passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        cleanup_test_database(db_path)


def main():
    """Run all verification workflow tests."""
    print("🧪 Running Verification Workflow Tests")
    print("=" * 60)
    
    tests = [
        test_pending_verification_listing,
        test_practitioner_approval_workflow,
        test_practitioner_rejection_workflow,
        test_verification_status_reset,
        test_verification_requirements_checking,
        test_verification_statistics
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
        print("🎉 All verification workflow tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)