# AI Assistant Integration Guide

## Overview

YatinVeda includes an AI-powered Vedic astrology assistant called **VedaMind** that provides intelligent, context-aware guidance on Vedic astrology concepts, birth chart analysis, and personalized recommendations.

## Architecture

### Components

1. **VedaMind Module** (`backend/modules/veda_mind.py`)
   - Core AI assistant engine
   - Conversation memory management
   - LLM provider abstraction (OpenAI, Anthropic, Ollama)
   - Context-aware response generation

2. **Vedic Knowledge Base** (`backend/modules/jnana_hub/vedic_knowledge_base.py`)
   - Repository of Vedic astrology concepts
   - Smart context retrieval for user queries
   - Knowledge graph for related topics

3. **Chat API Endpoints** (`backend/api/v1/chat.py`)
   - `/api/v1/chat/message` - Send message to AI assistant
   - `/api/v1/chat/chart-question` - Ask specific chart-related questions
   - `/api/v1/chat/suggestions` - Get suggested follow-up questions
   - `/api/v1/chat/topics` - Get available chat topics

4. **Conversation Memory**
   - Session-based conversation tracking
   - User context persistence (birth chart, preferences)
   - Message history for coherent multi-turn conversations

## Setup Instructions

### 1. Choose Your LLM Provider

#### Option A: OpenAI (GPT-4) - Recommended

```bash
# Set environment variables in .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo for cost savings
```

**Get API Key:**
1. Go to https://platform.openai.com/account/api-keys
2. Create new API key
3. Add it to your `.env` file

**Cost Estimate:**
- GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
- Typical chat: $0.10-0.50 per conversation

#### Option B: Anthropic Claude

```bash
# Set environment variables in .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Get API Key:**
1. Go to https://console.anthropic.com/
2. Create API key in account settings
3. Add it to your `.env` file

**Advantages:**
- Strong reasoning capabilities
- Better at long-context understanding
- More affordable than GPT-4

#### Option C: Local LLM (Ollama) - Free

```bash
# Set environment variables in .env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2  # or other models
```

**Setup Ollama:**
1. Download from https://ollama.ai
2. Run: `ollama serve`
3. Pull model: `ollama pull llama2`
4. Available models: llama2, neural-chat, mistral, etc.

**Advantages:**
- Completely free
- No API keys needed
- Full privacy (runs locally)
- Good for development/testing

### 2. Install Dependencies

```bash
# Install LLM packages (already in requirements.txt)
pip install -r backend/requirements.txt

# Or individually:
pip install openai==1.31.0        # For OpenAI
pip install anthropic==0.25.1     # For Anthropic
pip install requests==2.31.0      # For local LLM
```

### 3. Configure Environment

Create/update `.env` in the backend directory:

```env
# LLM Provider Configuration
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# OR Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# ANTHROPIC_MODEL=claude-3-sonnet-20240229

# OR Local
# LOCAL_LLM_BASE_URL=http://localhost:11434
# LOCAL_LLM_MODEL=llama2
```

### 4. Start the Backend

```bash
cd backend
python main.py

# Or with uvicorn directly:
uvicorn main:app --reload
```

## API Usage

### Send a Message to AI Assistant

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does my moon sign tell me about my emotions?",
    "context": {
      "birth_chart": {
        "sun_sign": "Leo",
        "moon_sign": "Pisces",
        "ascendant": "Taurus"
      }
    }
  }'
```

**Response:**
```json
{
  "response": "Your Pisces Moon indicates a deeply emotional and intuitive nature...",
  "suggestions": [
    "Tell me about my chart's houses",
    "What planetary transits affect me now?",
    "How can I work with my Pisces Moon?"
  ],
  "related_topics": ["Moon Sign", "Emotions", "Intuition", "Neptune's Influence"]
}
```

### Ask Chart-Specific Questions

```bash
curl -X POST "http://localhost:8000/api/v1/chat/chart-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "When is my next good time for career changes?",
    "chart_data": {
      "ascendant": "Taurus",
      "sun_sign": "Leo",
      "moon_sign": "Pisces",
      "birth_time": "14:30",
      "birth_location": "New York"
    }
  }'
```

### Get Suggestions

```bash
curl -X GET "http://localhost:8000/api/v1/chat/suggestions"
```

### Get Topics

```bash
curl -X GET "http://localhost:8000/api/v1/chat/topics"
```

## Knowledge Base Structure

The Vedic Knowledge Base includes:

- **Nakshatras (27 Lunar Mansions)**: Birth star characteristics and influences
- **Planets (9 Grahas)**: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
- **Houses (12 Bhavas)**: Life areas and astrological houses
- **Doshas**: Vata, Pitta, Kapha - constitutional types
- **Yogas**: Raj Yoga, Dhana Yoga, Gajakesari Yoga - planetary combinations
- **Dashas**: Vimshottari and other planetary period systems

The AI assistant automatically retrieves relevant knowledge and includes it in its responses.

## Conversation Memory

Each user gets a persistent conversation session identified by their user ID:

```python
session_id = f"user_{user_id}"
```

**Features:**
- Maintains up to 10 user-assistant message pairs
- Stores user context (birth chart, preferences)
- Automatic memory cleanup after 10 exchanges
- Can be cleared via `clear_session(session_id)`

## Customization

### Add Custom Vedic Knowledge

Edit `backend/modules/jnana_hub/vedic_knowledge_base.py`:

```python
knowledge_base = {
    "your_topic": {
        "description": "Topic description",
        "related_concepts": ["concept1", "concept2"],
        "significance": "Why this matters in Vedic astrology"
    }
}
```

### Modify System Prompt

Edit the `_build_system_prompt()` method in `backend/modules/veda_mind.py` to customize the AI's personality and guidelines.

### Add Domain-Specific Logic

Extend VedaMind class methods:

```python
def analyze_birth_chart(self, chart_data) -> dict:
    """Custom analysis logic"""
    # Your implementation
    pass
```

## Cost Estimation

### OpenAI (GPT-4)

| Provider | Input Cost | Output Cost | Typical Response | Total/Chat |
|----------|-----------|------------|-----------------|-----------|
| GPT-4 | $0.03/1K | $0.06/1K | 2K tokens input, 500 output | $0.06-$0.15 |
| GPT-3.5 | $0.0005/1K | $0.0015/1K | Same as above | $0.003-$0.01 |

### Anthropic (Claude)

| Model | Input Cost | Output Cost | Typical Response | Total/Chat |
|-------|-----------|------------|-----------------|-----------|
| Claude 3 Sonnet | $0.003/1K | $0.015/1K | 2K input, 500 output | $0.01-$0.03 |
| Claude 3 Opus | $0.015/1K | $0.075/1K | Same as above | $0.06-$0.15 |

### Local (Ollama)

- **Cost**: $0 (runs on your hardware)
- **Best For**: Development, privacy, cost-sensitive deployments
- **Requirements**: 8GB+ RAM, 20GB+ disk space

## Monitoring & Debugging

### Enable Logging

Set in `.env`:
```env
LOG_LEVEL=DEBUG
```

### Monitor Token Usage

Add to VedaMind for cost tracking:

```python
def _log_usage(self, message: str, response: str, provider: str):
    """Log token usage for cost tracking"""
    import tiktoken
    
    if provider == "openai":
        encoding = tiktoken.encoding_for_model("gpt-4")
        input_tokens = len(encoding.encode(message))
        output_tokens = len(encoding.encode(response))
        logger.info(f"OpenAI Usage: {input_tokens} input, {output_tokens} output")
```

## Production Best Practices

1. **API Key Security**
   - Never commit `.env` to git
   - Use environment variables or secure vaults (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys regularly

2. **Rate Limiting**
   - Implement rate limiting per user
   - Set maximum tokens per conversation
   - Monitor LLM API usage

3. **Error Handling**
   - Gracefully degrade if LLM is unavailable
   - Provide fallback responses from knowledge base
   - Log all errors for monitoring

4. **Performance**
   - Cache common questions and answers
   - Use Redis for conversation memory in production
   - Implement streaming responses for long answers

5. **Cost Management**
   - Use cheaper models (GPT-3.5, Claude 3 Sonnet) for general queries
   - Reserve GPT-4 for complex analysis
   - Consider local LLM for high-volume scenarios

## Troubleshooting

### "OPENAI_API_KEY not set"
- Check `.env` file exists and has correct variable name
- Make sure you're running from backend directory
- Verify key is valid on OpenAI dashboard

### "Connection refused" for local LLM
- Ensure Ollama is running: `ollama serve`
- Check `LOCAL_LLM_BASE_URL` is correct
- Verify model is pulled: `ollama pull llama2`

### Slow responses
- Local LLM (Ollama) is slower than cloud APIs
- Large models are slower; try smaller variants
- Consider async/streaming for better UX

### High costs
- Switch to cheaper model (GPT-3.5 Turbo, Claude 3 Sonnet)
- Implement response caching
- Use local LLM for development/testing

## Next Steps

1. Choose and configure your LLM provider
2. Update `.env` with API keys
3. Run `pip install -r requirements.txt`
4. Start backend: `python main.py`
5. Test chat endpoint in Swagger UI: http://localhost:8000/docs
6. Monitor costs and performance in production

## Resources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Claude Docs](https://docs.anthropic.com)
- [Ollama Documentation](https://ollama.ai)
- [VedaMind Source Code](backend/modules/veda_mind.py)
- [Chat API Implementation](backend/api/v1/chat.py)
