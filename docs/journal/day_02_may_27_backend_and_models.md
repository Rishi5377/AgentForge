# Day 2: May 27, 2026 - Backend Foundation and Model Selection

## What We Did
We set up the Next.js frontend and FastAPI backend. We established a LangGraph pipeline with specialized agents (Supervisor, Frontend, Backend, Database, Assembler). We also spun up research subagents to evaluate the best open-source models available on Groq (Llama 3.3, Qwen 2.5 Coder, Kimi K2, etc.).

## Challenges Faced
- **Python Version Conflict**: The system had Python 3.14, which lacked pre-compiled wheels for heavy ML libraries, causing installation failures.
- **Pydantic/CrewAI Conflicts**: Pydantic threw validation errors because CrewAI expected native LLM objects, and LiteLLM fallback errors crashed the pipeline.
- **Rate Limiting**: Using a single Groq API key caused immediate `429 Rate Limit` errors when multiple agents ran concurrently.
- **WebContainer Issues**: The browser subagent couldn't easily test the application because of local Chrome debugging constraints.

## How We Overcame Them
- Switched to a Python 3.11 virtual environment using the ultra-fast `uv` package manager.
- Stripped CrewAI out entirely and migrated to a pure LangGraph + LangChain LCEL architecture, making the pipeline significantly cleaner and faster.
- Refactored `groq_client.py` to support 5 distinct API keys (one for each agent) to bypass the rate limits.
- Launched Google Chrome with remote debugging enabled on port `9222` to allow the browser subagent to perform automated UI testing.
