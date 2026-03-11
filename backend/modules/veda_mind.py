"""
VedaMind - AI-powered Vedic Astrology Assistant
Integrates with LLM providers for context-aware Vedic guidance
"""

from typing import Dict, Any, Optional, List
import os
import json
from datetime import datetime
from modules.jnana_hub.vedic_knowledge_base import get_relevant_context


class ConversationMemory:
    """Manages conversation history and context"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
        self.user_context: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep only recent messages
        if len(self.messages) > self.max_history * 2:  # *2 for user+assistant pairs
            self.messages = self.messages[-(self.max_history * 2):]
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history for LLM context"""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]
    
    def set_user_context(self, context: Dict[str, Any]):
        """Store user-specific context (chart data, preferences, etc.)"""
        self.user_context.update(context)
    
    def get_context_summary(self) -> str:
        """Generate a summary of user context for LLM"""
        if not self.user_context:
            return ""
        
        summary_parts = []
        if "birth_chart" in self.user_context:
            chart = self.user_context["birth_chart"]
            summary_parts.append(f"User's birth chart: {chart.get('location', 'Unknown location')}, {chart.get('datetime', 'Unknown time')}")
        if "preferences" in self.user_context:
            prefs = self.user_context["preferences"]
            summary_parts.append(f"Preferences: {', '.join(prefs)}")
        
        return "\n".join(summary_parts) if summary_parts else ""


class VedaMind:
    """AI assistant for Vedic astrology queries with LLM integration"""
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize VedaMind with specified LLM provider
        
        Args:
            provider: LLM provider - "openai", "anthropic", or "local"
        """
        self.provider = provider.lower()
        self.conversation_memories: Dict[str, ConversationMemory] = {}
        self.system_prompt = self._build_system_prompt()
        
        # Initialize LLM client based on provider
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "local":
            self._init_local()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for VedaMind"""
        return """You are VedaMind, an expert AI assistant specializing in Vedic Astrology (Jyotish).

Your role is to provide accurate, insightful, and compassionate guidance based on Vedic astrological principles. You have deep knowledge of:
- Vedic birth charts (kundli) and planetary positions
- Nakshatras (lunar mansions) and their influences
- Dashas (planetary periods) and transits
- Doshas (afflictions) and their remedies
- Auspicious timings (muhurta)
- Compatibility analysis (guna milan)
- Gemstone and mantra recommendations

Guidelines:
1. Provide clear, actionable insights based on Vedic astrology principles
2. Be respectful and compassionate in all guidance
3. When specific chart data is unavailable, ask clarifying questions
4. Suggest remedies and positive actions when discussing challenges
5. Acknowledge the limitations of astrological predictions
6. Encourage users to use astrology as a tool for self-awareness, not fatalism

Always ground your responses in authentic Vedic astrology traditions while being accessible to modern seekers."""
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude client"""
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
    
    def _init_local(self):
        """Initialize local LLM (e.g., Ollama)"""
        self.api_base = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LOCAL_LLM_MODEL", "llama2")
        # Use requests for local API calls
    
    def _get_or_create_memory(self, session_id: str) -> ConversationMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = ConversationMemory()
        return self.conversation_memories[session_id]
    
    def generate_response(
        self, 
        message: str, 
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate AI response to user query with conversation context
        
        Args:
            message: User's message
            session_id: Session identifier for conversation memory
            context: Additional context (birth chart, user preferences, etc.)
        
        Returns:
            AI-generated response
        """
        memory = self._get_or_create_memory(session_id)
        
        # Update user context if provided
        if context:
            memory.set_user_context(context)
        
        # Add user message to history
        memory.add_message("user", message)
        
        # Get relevant Vedic knowledge
        knowledge_context = get_relevant_context(message)
        
        # Build enhanced prompt with context
        enhanced_message = self._build_enhanced_message(message, memory, knowledge_context)
        
        # Generate response based on provider
        try:
            if self.provider == "openai":
                response = self._generate_openai_response(memory, enhanced_message)
            elif self.provider == "anthropic":
                response = self._generate_anthropic_response(memory, enhanced_message)
            elif self.provider == "local":
                response = self._generate_local_response(memory, enhanced_message)
            else:
                response = f"Provider {self.provider} not supported"
            
            # Add assistant response to history
            memory.add_message("assistant", response)
            
            return response
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _build_enhanced_message(
        self, 
        message: str, 
        memory: ConversationMemory,
        knowledge_context: str
    ) -> str:
        """Build enhanced message with user context and knowledge base"""
        parts = []
        
        # Add user context summary
        context_summary = memory.get_context_summary()
        if context_summary:
            parts.append(f"User Context:\n{context_summary}\n")
        
        # Add relevant Vedic knowledge
        if knowledge_context:
            parts.append(f"Relevant Vedic Knowledge:\n{knowledge_context}\n")
        
        # Add the actual user message
        parts.append(f"User Query: {message}")
        
        return "\n".join(parts)
    
    def _generate_openai_response(self, memory: ConversationMemory, message: str) -> str:
        """Generate response using OpenAI"""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(memory.get_history()[:-1])  # Exclude last message (current)
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic_response(self, memory: ConversationMemory, message: str) -> str:
        """Generate response using Anthropic Claude"""
        # Anthropic doesn't use system messages in the messages array
        messages = memory.get_history()[:-1]  # Exclude last message (current)
        messages.append({"role": "user", "content": message})
        
        response = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        return response.content[0].text
    
    def _generate_local_response(self, memory: ConversationMemory, message: str) -> str:
        """Generate response using local LLM (Ollama)"""
        import requests
        
        # Build prompt for local LLM (concatenate system + history + message)
        full_prompt = f"{self.system_prompt}\n\n"
        for msg in memory.get_history()[:-1]:
            role_prefix = "Human: " if msg["role"] == "user" else "Assistant: "
            full_prompt += f"{role_prefix}{msg['content']}\n\n"
        full_prompt += f"Human: {message}\n\nAssistant:"
        
        response = requests.post(
            f"{self.api_base}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response generated")
        else:
            raise Exception(f"Local LLM error: {response.status_code}")
    
    def get_suggestions(self, message: str, session_id: str = "default") -> List[str]:
        """
        Generate contextual follow-up suggestions
        
        Args:
            message: Current user message
            session_id: Session identifier
        
        Returns:
            List of suggested follow-up questions
        """
        memory = self._get_or_create_memory(session_id)
        
        # Context-aware suggestions based on conversation
        if not memory.messages:
            # First interaction
            return [
                "Tell me about my birth chart",
                "What are the current planetary transits?",
                "How can I determine auspicious timings?",
                "Explain my nakshatra and its significance"
            ]
        
        # Generate suggestions based on last topic
        last_assistant_msg = next(
            (msg["content"] for msg in reversed(memory.messages) if msg["role"] == "assistant"),
            ""
        )
        
        # Simple keyword-based suggestions (could be enhanced with LLM)
        suggestions = []
        if "dasha" in last_assistant_msg.lower():
            suggestions.extend([
                "Tell me more about my current dasha period",
                "What remedies can help during difficult dashas?"
            ])
        if "compatibility" in last_assistant_msg.lower():
            suggestions.extend([
                "How is compatibility calculated in Vedic astrology?",
                "What are the most important factors for compatibility?"
            ])
        if "remedy" in last_assistant_msg.lower() or "gemstone" in last_assistant_msg.lower():
            suggestions.extend([
                "What other remedies are available?",
                "How do I energize gemstones?"
            ])
        
        # Default suggestions if none matched
        if not suggestions:
            suggestions = [
                "What should I focus on this month?",
                "Tell me about my career prospects",
                "How can I improve my relationships?"
            ]
        
        return suggestions[:4]  # Return top 4
    
    def get_related_topics(self, message: str) -> List[str]:
        """
        Get related Vedic astrology topics based on query
        
        Args:
            message: User's message
        
        Returns:
            List of related topics
        """
        message_lower = message.lower()
        
        # Topic mapping
        topic_map = {
            "nakshatra": ["Nakshatras", "Lunar Mansions", "Birth Star"],
            "dasha": ["Mahadasha", "Antardasha", "Planetary Periods"],
            "dosha": ["Mangal Dosha", "Kaal Sarp Dosha", "Pitra Dosha"],
            "compatibility": ["Guna Milan", "Ashtakoota", "Marriage Compatibility"],
            "career": ["Profession Astrology", "10th House", "Career Timing"],
            "health": ["6th House", "Health Astrology", "Ayurveda"],
            "remedy": ["Gemstones", "Mantras", "Pujas", "Charity"],
            "transit": ["Planetary Transits", "Gochar", "Current Influences"]
        }
        
        # Find matching topics
        related = []
        for keyword, topics in topic_map.items():
            if keyword in message_lower:
                related.extend(topics)
        
        # Default topics if none matched
        if not related:
            related = ["Birth Chart Analysis", "Planetary Positions", "Vedic Remedies"]
        
        return list(set(related))[:5]  # Return unique topics, max 5
    
    def clear_session(self, session_id: str):
        """Clear conversation memory for a session"""
        if session_id in self.conversation_memories:
            del self.conversation_memories[session_id]
    
    def answer_question(self, question: str, chart_data: Any) -> str:
        """
        Answer a specific question about a birth chart
        
        Args:
            question: User's question about their chart
            chart_data: Chart data object with astrological details
        
        Returns:
            AI-generated answer specific to the user's chart
        """
        # Build chart context for the LLM
        chart_context = self._build_chart_context(chart_data)
        
        # Use default session for chart-based queries
        memory = self._get_or_create_memory("chart-question")
        memory.set_user_context({"birth_chart": chart_context})
        
        # Generate response with chart context
        response = self.generate_response(
            message=question,
            session_id="chart-question",
            context={"birth_chart": chart_context}
        )
        
        return response
    
    def _build_chart_context(self, chart_data: Any) -> dict:
        """Build context dictionary from chart data"""
        context = {}
        
        # Extract chart attributes if they exist
        if hasattr(chart_data, 'ascendant'):
            context['ascendant'] = getattr(chart_data, 'ascendant').value if hasattr(chart_data.ascendant, 'value') else str(chart_data.ascendant)
        if hasattr(chart_data, 'sun_sign'):
            context['sun_sign'] = getattr(chart_data, 'sun_sign').value if hasattr(chart_data.sun_sign, 'value') else str(chart_data.sun_sign)
        if hasattr(chart_data, 'moon_sign'):
            context['moon_sign'] = getattr(chart_data, 'moon_sign').value if hasattr(chart_data.moon_sign, 'value') else str(chart_data.moon_sign)
        if hasattr(chart_data, 'birth_time'):
            context['birth_time'] = str(chart_data.birth_time)
        if hasattr(chart_data, 'birth_location'):
            context['birth_location'] = str(chart_data.birth_location)
        
        return context


# Global instance (can be initialized in main.py with env config)
_veda_mind_instance: Optional[VedaMind] = None


def get_veda_mind() -> VedaMind:
    """Get or create global VedaMind instance"""
    global _veda_mind_instance
    if _veda_mind_instance is None:
        provider = os.getenv("LLM_PROVIDER", "openai")
        _veda_mind_instance = VedaMind(provider=provider)
    return _veda_mind_instance
