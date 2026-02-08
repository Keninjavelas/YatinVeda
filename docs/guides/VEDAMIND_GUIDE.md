# VedaMind AI Integration Guide

## Overview

VedaMind is an AI-powered Vedic Astrology assistant that provides context-aware guidance using Large Language Models (LLMs). It supports multiple providers and maintains conversation memory for personalized interactions.

## Features

### ✅ Multi-Provider LLM Support
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude 3 Sonnet, Opus)
- **Local LLMs** (Ollama, llama2, etc.)

### ✅ Conversation Memory
- Session-based conversation history
- User context storage (birth charts, preferences)
- Automatic context summarization
- Configurable history limit (default: 10 messages)

### ✅ Vedic Knowledge Integration
- Integration with Jnana Hub knowledge base
- Context-enhanced responses with authentic Vedic principles
- Topic-based knowledge retrieval

### ✅ Smart Features
- Context-aware follow-up suggestions
- Related topics discovery
- User-specific session management
- Error handling and graceful degradation

## Installation

### Required Packages

```bash
# For OpenAI support
pip install openai

# For Anthropic Claude support
pip install anthropic

# For local LLM support (optional)
# Ollama should be installed and running
```

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# LLM Provider Configuration
LLM_PROVIDER=openai  # Options: openai, anthropic, local

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4  # Options: gpt-4, gpt-3.5-turbo

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229  # Options: claude-3-opus, claude-3-sonnet

# Local LLM Configuration (Ollama)
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2  # Options: llama2, mistral, codellama, etc.
```

## Usage

### Basic Usage

```python
from modules.veda_mind import get_veda_mind

# Get VedaMind instance (singleton)
veda_mind = get_veda_mind()

# Generate response
response = veda_mind.generate_response(
    message="What is my nakshatra?",
    session_id="user_123",
    context={
        "birth_chart": {
            "location": "Mumbai",
            "datetime": "1990-01-15 10:30"
        }
    }
)

print(response)
```

### With Session Management

```python
# Each user gets their own conversation memory
session_id = f"user_{user_id}"

# First message
response1 = veda_mind.generate_response(
    message="Tell me about my Sun sign",
    session_id=session_id
)

# Follow-up message (context preserved)
response2 = veda_mind.generate_response(
    message="What does it mean for my career?",
    session_id=session_id  # Previous context maintained
)

# Get contextual suggestions
suggestions = veda_mind.get_suggestions(
    message="career",
    session_id=session_id
)

# Get related topics
topics = veda_mind.get_related_topics("career")
```

### Clear Session

```python
# Clear conversation memory when user logs out or starts new conversation
veda_mind.clear_session(session_id="user_123")
```

## API Integration

The chat API endpoint automatically uses VedaMind:

```
POST /api/v1/chat/message
Authorization: Bearer <access_token>

{
  "message": "What are the effects of Saturn transit?",
  "context": {
    "birth_chart": { ... }
  }
}

Response:
{
  "response": "Saturn transits bring...",
  "suggestions": [
    "How long will this transit last?",
    "What remedies can help?",
    "Tell me about other transits"
  ],
  "related_topics": [
    "Planetary Transits",
    "Saturn Remedies",
    "Gochar Effects"
  ]
}
```

## Architecture

### ConversationMemory Class
- Manages per-session message history
- Stores user-specific context
- Limits history to prevent token overflow
- Provides formatted context for LLM

### VedaMind Class
- Provider-agnostic LLM interface
- System prompt engineering for Vedic expertise
- Knowledge base integration
- Response generation with context enhancement

### Global Instance Management
- `get_veda_mind()` returns singleton instance
- Lazy initialization based on environment
- Shared across all requests for efficiency

## System Prompt

VedaMind uses a carefully crafted system prompt that:
- Establishes expertise in Vedic Astrology
- Provides guidelines for compassionate guidance
- Sets boundaries and limitations
- Encourages positive, actionable insights

## Best Practices

### 1. Session Management
- Use user ID as session identifier
- Clear sessions on logout or conversation reset
- Limit history to last 10 message pairs

### 2. Context Enhancement
- Provide birth chart data when available
- Include user preferences (language, detail level)
- Add relevant timestamps for transit questions

### 3. Error Handling
- Graceful degradation if LLM unavailable
- Fallback to knowledge base responses
- User-friendly error messages

### 4. Cost Optimization
- Use GPT-3.5-turbo for simple queries
- Reserve GPT-4 for complex chart analysis
- Consider local LLMs for development

### 5. Response Quality
- Temperature: 0.7 (balanced creativity/consistency)
- Max tokens: 800 (comprehensive but not verbose)
- Include knowledge base context for accuracy

## Testing

### Unit Tests

```python
import pytest
from modules.veda_mind import VedaMind, ConversationMemory

def test_conversation_memory():
    memory = ConversationMemory(max_history=5)
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")
    
    assert len(memory.messages) == 2
    assert memory.get_history()[0]["role"] == "user"

def test_context_summary():
    memory = ConversationMemory()
    memory.set_user_context({
        "birth_chart": {
            "location": "Delhi",
            "datetime": "1995-06-20 14:00"
        }
    })
    
    summary = memory.get_context_summary()
    assert "Delhi" in summary
```

### Integration Tests

```python
def test_veda_mind_response():
    veda_mind = VedaMind(provider="openai")
    response = veda_mind.generate_response(
        message="What is a nakshatra?",
        session_id="test_session"
    )
    
    assert len(response) > 0
    assert "nakshatra" in response.lower()
```

## Monitoring

### Key Metrics
- Response time per provider
- Token usage (cost tracking)
- Error rates
- User satisfaction feedback

### Logging

```python
import logging

logging.info(f"VedaMind response generated: {len(response)} chars")
logging.error(f"LLM error: {str(e)}")
```

## Troubleshooting

### Common Issues

1. **ImportError: openai not found**
   ```bash
   pip install openai
   ```

2. **API Key Error**
   - Verify environment variables are set
   - Check API key validity
   - Ensure proper permissions

3. **Local LLM Connection Error**
   - Ensure Ollama is running: `ollama serve`
   - Verify base URL: `curl http://localhost:11434/api/tags`
   - Check model is downloaded: `ollama pull llama2`

4. **Out of Memory**
   - Reduce max_history parameter
   - Decrease max_tokens in response
   - Clear old sessions periodically

## Future Enhancements

- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Image-based chart analysis
- [ ] Fine-tuned Vedic astrology models
- [ ] Retrieval-Augmented Generation (RAG)
- [ ] User feedback integration
- [ ] A/B testing for prompt optimization
