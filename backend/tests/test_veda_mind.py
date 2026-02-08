#!/usr/bin/env python3
"""
Test script for VedaMind AI assistant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.veda_mind import VedaMind, get_veda_mind
from modules.jnana_hub.vedic_knowledge_base import get_relevant_context, search_knowledge

def test_knowledge_base():
    """Test the Vedic knowledge base"""
    print("🧪 Testing Vedic Knowledge Base...")
    
    try:
        # Test search functionality
        results = search_knowledge("planets")
        print(f"✅ Search for 'planets': Found {len(results)} results")
        
        # Test context retrieval
        context = get_relevant_context("What are nakshatras?")
        print(f"✅ Context for 'nakshatras': {len(context)} characters")
        if context:
            print(f"   Preview: {context[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Knowledge base error: {e}")
        return False

def test_veda_mind_initialization():
    """Test VedaMind initialization with different providers"""
    print("\n🧪 Testing VedaMind Initialization...")
    
    success_count = 0
    
    # Test with mock provider (no API key needed)
    try:
        # We'll test initialization without actual API calls
        print("   Testing local provider initialization...")
        veda_mind = VedaMind(provider="local")
        print("✅ Local provider initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Local provider initialization failed: {e}")
    
    # Test conversation memory
    try:
        print("   Testing conversation memory...")
        veda_mind = VedaMind(provider="local")
        memory = veda_mind._get_or_create_memory("test_session")
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Namaste! How can I help you with Vedic astrology?")
        
        history = memory.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        
        print("✅ Conversation memory working correctly")
        success_count += 1
    except Exception as e:
        print(f"❌ Conversation memory test failed: {e}")
    
    # Test context management
    try:
        print("   Testing user context management...")
        veda_mind = VedaMind(provider="local")
        memory = veda_mind._get_or_create_memory("test_session")
        
        context = {
            "birth_chart": {
                "location": "Mumbai, India",
                "datetime": "1990-05-15 10:30:00",
                "ascendant": "Leo"
            },
            "preferences": ["career", "relationships"]
        }
        
        memory.set_user_context(context)
        context_summary = memory.get_context_summary()
        
        assert "Mumbai, India" in context_summary
        assert "1990-05-15" in context_summary
        
        print("✅ User context management working correctly")
        success_count += 1
    except Exception as e:
        print(f"❌ User context test failed: {e}")
    
    return success_count

def test_suggestions_and_topics():
    """Test suggestion and topic generation"""
    print("\n🧪 Testing Suggestions and Topics...")
    
    try:
        veda_mind = VedaMind(provider="local")
        
        # Test suggestions for new session
        suggestions = veda_mind.get_suggestions("Hello", "new_session")
        print(f"✅ Generated {len(suggestions)} suggestions for new session")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        # Test related topics
        topics = veda_mind.get_related_topics("Tell me about my career prospects")
        print(f"✅ Generated {len(topics)} related topics")
        for i, topic in enumerate(topics, 1):
            print(f"   {i}. {topic}")
        
        return True
    except Exception as e:
        print(f"❌ Suggestions/topics test failed: {e}")
        return False

def test_chart_context_building():
    """Test chart context building"""
    print("\n🧪 Testing Chart Context Building...")
    
    try:
        veda_mind = VedaMind(provider="local")
        
        # Mock chart data object
        class MockChartData:
            def __init__(self):
                self.ascendant = MockValue("Leo")
                self.sun_sign = MockValue("Taurus")
                self.moon_sign = MockValue("Scorpio")
                self.birth_time = "10:30 AM"
                self.birth_location = "Mumbai, India"
        
        class MockValue:
            def __init__(self, value):
                self.value = value
        
        chart_data = MockChartData()
        context = veda_mind._build_chart_context(chart_data)
        
        assert context['ascendant'] == 'Leo'
        assert context['sun_sign'] == 'Taurus'
        assert context['moon_sign'] == 'Scorpio'
        assert context['birth_time'] == '10:30 AM'
        assert context['birth_location'] == 'Mumbai, India'
        
        print("✅ Chart context building working correctly")
        print(f"   Context keys: {list(context.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Chart context building test failed: {e}")
        return False

def test_mock_response_generation():
    """Test response generation with mock data (no API calls)"""
    print("\n🧪 Testing Mock Response Generation...")
    
    try:
        # Test the enhanced message building
        veda_mind = VedaMind(provider="local")
        memory = veda_mind._get_or_create_memory("test_session")
        
        # Set up context
        memory.set_user_context({
            "birth_chart": {
                "ascendant": "Leo",
                "sun_sign": "Taurus"
            }
        })
        
        # Test enhanced message building
        message = "What does my ascendant mean?"
        knowledge_context = get_relevant_context(message)
        enhanced_message = veda_mind._build_enhanced_message(message, memory, knowledge_context)
        
        print("✅ Enhanced message building working")
        print(f"   Original: {message}")
        print(f"   Enhanced length: {len(enhanced_message)} characters")
        
        # Test system prompt
        system_prompt = veda_mind.system_prompt
        assert "VedaMind" in system_prompt
        assert "Vedic Astrology" in system_prompt
        print("✅ System prompt properly configured")
        
        return True
    except Exception as e:
        print(f"❌ Mock response generation test failed: {e}")
        return False

def test_global_instance():
    """Test global VedaMind instance"""
    print("\n🧪 Testing Global Instance...")
    
    try:
        # Set environment to use local provider for testing
        import os
        original_provider = os.environ.get("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = "local"
        
        # Clear any existing global instance
        from modules.veda_mind import _veda_mind_instance
        import modules.veda_mind as vm
        vm._veda_mind_instance = None
        
        # Test getting global instance
        veda_mind1 = get_veda_mind()
        veda_mind2 = get_veda_mind()
        
        # Should be the same instance
        assert veda_mind1 is veda_mind2
        
        # Restore original environment
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        else:
            os.environ.pop("LLM_PROVIDER", None)
        
        print("✅ Global instance working correctly (singleton pattern)")
        return True
    except Exception as e:
        print(f"❌ Global instance test failed: {e}")
        return False

def main():
    """Run all VedaMind tests"""
    print("🧪 Testing VedaMind AI Assistant...")
    print("=" * 60)
    
    tests = [
        ("Knowledge Base", test_knowledge_base),
        ("VedaMind Initialization", test_veda_mind_initialization),
        ("Suggestions & Topics", test_suggestions_and_topics),
        ("Chart Context Building", test_chart_context_building),
        ("Mock Response Generation", test_mock_response_generation),
        ("Global Instance", test_global_instance)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            if result is True:
                passed_tests += 1
            elif isinstance(result, int):
                # For tests that return success count
                if result > 0:
                    passed_tests += 1
                print(f"   Subtests passed: {result}")
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 VedaMind AI Assistant is ready for use!")
        print("\n📝 Configuration Notes:")
        print("   • Set OPENAI_API_KEY environment variable for OpenAI")
        print("   • Set ANTHROPIC_API_KEY environment variable for Anthropic")
        print("   • Set LLM_PROVIDER environment variable (openai/anthropic/local)")
        print("   • For local LLM, ensure Ollama is running on localhost:11434")
    else:
        print("⚠️  Some tests failed. VedaMind may have issues.")
    
    print("\n🔧 Environment Variables for Production:")
    print("   export LLM_PROVIDER=openai")
    print("   export OPENAI_API_KEY=sk-your-key-here")
    print("   export OPENAI_MODEL=gpt-4  # optional, defaults to gpt-4")

if __name__ == "__main__":
    main()