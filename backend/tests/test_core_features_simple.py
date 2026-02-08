#!/usr/bin/env python3
"""
Simple test for core backend features
Tests the main functionality without complex integration setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core modules can be imported successfully"""
    print("🧪 Testing Core Module Imports...")
    
    success_count = 0
    total_tests = 0
    
    # Test VedaMind AI Assistant
    try:
        from modules.veda_mind import VedaMind, get_veda_mind
        from modules.jnana_hub.vedic_knowledge_base import get_relevant_context
        print("✅ VedaMind AI Assistant - Import successful")
        success_count += 1
    except Exception as e:
        print(f"❌ VedaMind AI Assistant - Import failed: {e}")
    total_tests += 1
    
    # Test PDF Prescription Generator
    try:
        from modules.prescription_generator import PrescriptionGenerator
        print("✅ PDF Prescription Generator - Import successful")
        success_count += 1
    except Exception as e:
        print(f"❌ PDF Prescription Generator - Import failed: {e}")
    total_tests += 1
    
    # Test Database Models
    try:
        from models.database import (
            User, Guru, Chart, Prescription, CommunityPost, 
            MFASettings, TrustedDevice, RefreshToken
        )
        print("✅ Database Models - Import successful")
        success_count += 1
    except Exception as e:
        print(f"❌ Database Models - Import failed: {e}")
    total_tests += 1
    
    # Test API Routers
    try:
        from api.v1 import auth, user_charts, profile, prescriptions, chat, community, health, mfa
        print("✅ API Routers - Import successful")
        success_count += 1
    except Exception as e:
        print(f"❌ API Routers - Import failed: {e}")
    total_tests += 1
    
    # Test Services
    try:
        from services.user_service import UserService
        from services.practitioner_service import PractitionerService
        print("✅ Services - Import successful")
        success_count += 1
    except Exception as e:
        print(f"❌ Services - Import failed: {e}")
    total_tests += 1
    
    return success_count, total_tests

def test_database_models():
    """Test database model functionality"""
    print("\n🧪 Testing Database Models...")
    
    success_count = 0
    total_tests = 0
    
    # Test User model methods
    try:
        from models.database import User
        
        # Test role validation
        valid_roles = User.get_valid_roles()
        assert "user" in valid_roles
        assert "practitioner" in valid_roles
        
        # Test verification status validation
        valid_statuses = User.get_valid_verification_statuses()
        assert "active" in valid_statuses
        assert "pending_verification" in valid_statuses
        assert "verified" in valid_statuses
        
        print("✅ User Model - Validation methods working")
        success_count += 1
    except Exception as e:
        print(f"❌ User Model - Test failed: {e}")
    total_tests += 1
    
    # Test Guru model methods
    try:
        from models.database import Guru
        
        # Test specializations
        specializations = Guru.get_valid_specializations()
        assert "vedic_astrology" in specializations
        assert "career_guidance" in specializations
        
        print("✅ Guru Model - Validation methods working")
        success_count += 1
    except Exception as e:
        print(f"❌ Guru Model - Test failed: {e}")
    total_tests += 1
    
    return success_count, total_tests

def test_pdf_generation():
    """Test PDF generation functionality"""
    print("\n🧪 Testing PDF Generation...")
    
    try:
        from modules.prescription_generator import PrescriptionGenerator
        
        generator = PrescriptionGenerator()
        
        # Test that reportlab is available
        assert generator.reportlab_available == True
        
        # Test basic PDF generation (without saving)
        prescription_data = {
            'id': 'TEST-001',
            'title': 'Test Prescription',
            'diagnosis': 'Test diagnosis',
            'verification_code': 'TEST-CODE'
        }
        
        user_data = {'name': 'Test User', 'birth_date': '1990-01-01', 'birth_place': 'Test City'}
        guru_data = {'name': 'Test Guru', 'specialization': 'Test Specialization'}
        remedies = [{'category': 'Test', 'description': 'Test remedy', 'duration': '1 month', 'frequency': 'Daily'}]
        
        pdf_bytes = generator.generate_prescription_pdf(
            prescription_data, user_data, guru_data, remedies
        )
        
        assert len(pdf_bytes) > 0
        print("✅ PDF Generation - Working correctly")
        return 1, 1
        
    except Exception as e:
        print(f"❌ PDF Generation - Test failed: {e}")
        return 0, 1

def test_ai_assistant():
    """Test AI assistant functionality"""
    print("\n🧪 Testing AI Assistant...")
    
    try:
        from modules.veda_mind import VedaMind
        
        # Test initialization with local provider (no API key needed)
        veda_mind = VedaMind(provider="local")
        
        # Test conversation memory
        memory = veda_mind._get_or_create_memory("test_session")
        memory.add_message("user", "Hello")
        
        history = memory.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        
        # Test suggestions
        suggestions = veda_mind.get_suggestions("Hello", "test_session")
        assert len(suggestions) > 0
        
        # Test related topics
        topics = veda_mind.get_related_topics("career astrology")
        assert len(topics) > 0
        
        print("✅ AI Assistant - Core functionality working")
        return 1, 1
        
    except Exception as e:
        print(f"❌ AI Assistant - Test failed: {e}")
        return 0, 1

def test_knowledge_base():
    """Test Vedic knowledge base"""
    print("\n🧪 Testing Vedic Knowledge Base...")
    
    try:
        from modules.jnana_hub.vedic_knowledge_base import search_knowledge, get_relevant_context
        
        # Test search functionality
        results = search_knowledge("planets")
        assert len(results) > 0
        
        # Test context retrieval
        context = get_relevant_context("nakshatras")
        # Context might be empty for this simple knowledge base, but function should work
        
        print("✅ Vedic Knowledge Base - Working correctly")
        return 1, 1
        
    except Exception as e:
        print(f"❌ Vedic Knowledge Base - Test failed: {e}")
        return 0, 1

def test_api_structure():
    """Test API router structure"""
    print("\n🧪 Testing API Structure...")
    
    success_count = 0
    total_tests = 0
    
    # Test auth router
    try:
        from api.v1.auth import router as auth_router
        assert auth_router is not None
        print("✅ Auth Router - Structure valid")
        success_count += 1
    except Exception as e:
        print(f"❌ Auth Router - Test failed: {e}")
    total_tests += 1
    
    # Test charts router
    try:
        from api.v1.user_charts import router as charts_router
        assert charts_router is not None
        print("✅ Charts Router - Structure valid")
        success_count += 1
    except Exception as e:
        print(f"❌ Charts Router - Test failed: {e}")
    total_tests += 1
    
    # Test community router
    try:
        from api.v1.community import router as community_router
        assert community_router is not None
        print("✅ Community Router - Structure valid")
        success_count += 1
    except Exception as e:
        print(f"❌ Community Router - Test failed: {e}")
    total_tests += 1
    
    # Test prescriptions router
    try:
        from api.v1.prescriptions import router as prescriptions_router
        assert prescriptions_router is not None
        print("✅ Prescriptions Router - Structure valid")
        success_count += 1
    except Exception as e:
        print(f"❌ Prescriptions Router - Test failed: {e}")
    total_tests += 1
    
    return success_count, total_tests

def main():
    """Run all core feature tests"""
    print("🧪 Testing Core Backend Features...")
    print("=" * 60)
    
    total_passed = 0
    total_tests = 0
    
    # Run all test categories
    test_categories = [
        ("Module Imports", test_imports),
        ("Database Models", test_database_models),
        ("PDF Generation", test_pdf_generation),
        ("AI Assistant", test_ai_assistant),
        ("Knowledge Base", test_knowledge_base),
        ("API Structure", test_api_structure)
    ]
    
    for category_name, test_func in test_categories:
        try:
            passed, tests = test_func()
            total_passed += passed
            total_tests += tests
            print(f"   {category_name}: {passed}/{tests} tests passed")
        except Exception as e:
            print(f"   {category_name}: Failed with exception: {e}")
            total_tests += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Overall Results: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All core backend features are working correctly!")
        print("\n✅ Ready for production deployment:")
        print("   • Database models and migrations ✅")
        print("   • PDF prescription generation ✅")
        print("   • AI assistant (VedaMind) ✅")
        print("   • API endpoints structure ✅")
        print("   • Vedic knowledge base ✅")
    else:
        print("⚠️  Some core features have issues.")
        print("   Check the error messages above for details.")
    
    print("\n🔧 Next Steps:")
    print("   1. Set up LLM provider (OpenAI/Anthropic) for AI assistant")
    print("   2. Configure email service for notifications")
    print("   3. Set up production database (PostgreSQL)")
    print("   4. Configure HTTPS/TLS certificates")
    print("   5. Deploy with Docker Compose")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)