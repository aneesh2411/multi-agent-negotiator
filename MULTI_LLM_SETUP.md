# Multi-LLM Setup Guide

## Overview

The Multi-Agent Negotiation Framework now supports multiple LLM providers (OpenAI, Anthropic, Google) with intelligent assignment of different LLMs to different agents based on their roles and expertise.

## Key Features

### 🤖 **Multi-LLM Support**
- **OpenAI GPT-4**: Best for analytical, technical, and structured reasoning
- **Anthropic Claude**: Excellent for ethical reasoning, philosophy, and safety considerations
- **Google Gemini**: Great for creative tasks, diverse perspectives, and general discussions

### 🧠 **Intelligent LLM Assignment**
- **Orchestrator Choice**: AI automatically selects the best LLM for each agent based on role
- **Diversity Preference**: Ensures varied LLM distribution across agents for richer debates
- **Role-Based Matching**: Technical roles get OpenAI, ethical roles get Anthropic, creative roles get Google

### 🔧 **Configuration Options**
- **Selection Strategy**: Choose how LLMs are assigned to agents
- **Provider Preferences**: Configure which providers to use
- **Fallback Handling**: Graceful degradation when providers are unavailable

## Environment Configuration

Create a `.env` file in the `backend/` directory with the following configuration:

```bash
# =============================================================================
# MULTI-LLM PROVIDER SETTINGS
# =============================================================================

# OpenAI Configuration
OPENAI_API_KEY="your-openai-api-key-here"
OPENAI_ORGANIZATION=""
OPENAI_DEFAULT_MODEL="gpt-4"
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2048
OPENAI_TIMEOUT=60

# Anthropic Configuration
ANTHROPIC_API_KEY="your-anthropic-api-key-here"
ANTHROPIC_DEFAULT_MODEL="claude-3-sonnet-20240229"
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=2048
ANTHROPIC_TIMEOUT=60

# Google/Gemini Configuration
GOOGLE_API_KEY="your-google-api-key-here"
GOOGLE_PROJECT_ID="your-google-project-id"
GOOGLE_LOCATION="us-central1"
GOOGLE_DEFAULT_MODEL="gemini-2.0-flash"
GOOGLE_TEMPERATURE=0.7
GOOGLE_MAX_TOKENS=2048
GOOGLE_TIMEOUT=60
GOOGLE_GENAI_USE_VERTEXAI=false

# LLM Provider Selection
AVAILABLE_LLM_PROVIDERS=["openai", "anthropic", "google"]
DEFAULT_LLM_PROVIDER="google"
ENABLE_MULTI_LLM=true

# LLM Selection Strategy
# Options: orchestrator_choice, random, round_robin
LLM_SELECTION_STRATEGY="orchestrator_choice"
LLM_DIVERSITY_PREFERENCE=0.8

# =============================================================================
# OTHER SETTINGS (Redis, ChromaDB, etc.)
# =============================================================================

# Redis Configuration
REDIS_URL="redis://localhost:6379"
REDIS_PASSWORD=""
REDIS_DB=0

# ChromaDB Configuration
CHROMA_HOST="localhost"
CHROMA_PORT=8001
CHROMA_SSL=false

# Application Settings
DEBUG=false
ENVIRONMENT="development"
API_HOST="0.0.0.0"
API_PORT=8000
```

## API Key Setup

### 1. OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set `OPENAI_API_KEY` in your `.env` file

### 2. Anthropic API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Set `ANTHROPIC_API_KEY` in your `.env` file

### 3. Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set `GOOGLE_API_KEY` in your `.env` file

## LLM Selection Strategies

### 1. Orchestrator Choice (Recommended)
```bash
LLM_SELECTION_STRATEGY="orchestrator_choice"
```
- AI analyzes agent roles and assigns the most suitable LLM
- Technical roles → OpenAI GPT-4
- Ethical/Legal roles → Anthropic Claude
- Creative/General roles → Google Gemini

### 2. Random Selection
```bash
LLM_SELECTION_STRATEGY="random"
```
- Randomly assigns LLMs to agents
- Good for testing and experimentation

### 3. Round Robin
```bash
LLM_SELECTION_STRATEGY="round_robin"
```
- Cycles through available providers
- Ensures equal distribution

## Role-Based LLM Matching

The system automatically matches LLMs to agent roles based on strengths:

### OpenAI GPT-4 - Best for:
- **Roles**: Data Analyst, Technical Lead, Engineer, Researcher
- **Strengths**: Analytical reasoning, technical discussions, structured thinking
- **Use Cases**: Complex problem-solving, data analysis, technical implementation

### Anthropic Claude - Best for:
- **Roles**: Ethics Officer, Legal Counsel, Compliance Manager, Philosopher
- **Strengths**: Ethical reasoning, safety considerations, nuanced thinking
- **Use Cases**: Ethical dilemmas, legal analysis, safety assessments

### Google Gemini - Best for:
- **Roles**: Creative Director, Marketing Manager, User Advocate, General Manager
- **Strengths**: Creative solutions, diverse perspectives, general discussions
- **Use Cases**: Creative brainstorming, user experience, general management

## Testing the Multi-LLM System

### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### 2. Create a Test Session
```bash
curl -X POST "http://localhost:8000/api/v1/sessions/start" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "Should our company implement a 4-day work week?",
    "agent_count": 5
  }'
```

### 3. Check Agent LLM Assignments
The response will show which LLM provider was assigned to each agent:
```json
{
  "agents": [
    {
      "name": "Sarah Chen",
      "role": "HR Director",
      "llm_provider": "anthropic",
      "llm_config": {...}
    },
    {
      "name": "Mike Rodriguez",
      "role": "Data Analyst",
      "llm_provider": "openai",
      "llm_config": {...}
    }
  ]
}
```

## Monitoring and Debugging

### 1. Check Available Providers
```bash
curl "http://localhost:8000/health"
```

### 2. View LLM Usage in Logs
The system logs which LLM provider is used for each agent response:
```
Agent Sarah Chen (anthropic) responded in round 1
Agent Mike Rodriguez (openai) responded in round 1
```

### 3. Debug LLM Selection
Set `DEBUG=true` in your `.env` file to see detailed LLM selection reasoning.

## Configuration Examples

### Minimal Setup (Single Provider)
```bash
# Use only Google Gemini
GOOGLE_API_KEY="your-google-api-key"
ENABLE_MULTI_LLM=false
DEFAULT_LLM_PROVIDER="google"
```

### Full Multi-LLM Setup
```bash
# All providers configured
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
GOOGLE_API_KEY="your-google-key"
ENABLE_MULTI_LLM=true
LLM_SELECTION_STRATEGY="orchestrator_choice"
LLM_DIVERSITY_PREFERENCE=0.8
```

### Testing Configuration
```bash
# Random assignment for testing
LLM_SELECTION_STRATEGY="random"
ENABLE_MULTI_LLM=true
DEBUG=true
```

## Troubleshooting

### Common Issues

1. **"No LLM providers available"**
   - Check that at least one API key is set correctly
   - Verify API keys are valid and have sufficient credits

2. **"Provider not available"**
   - Check API key configuration
   - Verify network connectivity
   - Check provider status pages

3. **Agent responses are inconsistent**
   - Adjust temperature settings for each provider
   - Check agent role assignments
   - Review LLM selection strategy

### Performance Tips

1. **For Better Debates**: Use `orchestrator_choice` strategy
2. **For Faster Responses**: Use fewer providers or increase timeouts
3. **For Cost Control**: Set appropriate token limits per provider

## Advanced Configuration

### Custom LLM Models
```bash
# Use specific models for each provider
OPENAI_DEFAULT_MODEL="gpt-4-turbo"
ANTHROPIC_DEFAULT_MODEL="claude-3-opus-20240229"
GOOGLE_DEFAULT_MODEL="gemini-2.0-flash"
```

### Provider-Specific Settings
```bash
# Different temperatures for different providers
OPENAI_TEMPERATURE=0.5  # More focused for technical tasks
ANTHROPIC_TEMPERATURE=0.7  # Balanced for ethical reasoning
GOOGLE_TEMPERATURE=0.9  # More creative for general discussions
```

## Support

For issues or questions about the multi-LLM system:
1. Check the logs for detailed error messages
2. Verify API key configuration
3. Test with a single provider first
4. Review the agent role assignments in the response

The multi-LLM system provides rich, diverse debates by leveraging the strengths of different AI models for different types of reasoning and discussion. 