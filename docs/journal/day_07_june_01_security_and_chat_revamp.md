# Day 7: June 01, 2026 - Security Audits and Chat Revamp

## What We Did
We executed the architectural and security fixes highlighted by the user's previous code review. We completely revamped the Chat UI to behave conversationally, preserving the true chat history rather than overwriting it with system logs.

## Challenges Faced
- **Critical Security Flaws**: The application was vulnerable to CORS `*` exposure, prompt injection, and arbitrary code execution via `shell=True` in the Assembler.
- **Conversational Disruptions**: The Supervisor agent kept generating annoying clarifying questions instead of executing the pipeline.
- **State Wipes**: Refreshing the page caused immediate crashes due to bad `localStorage` caching logic.

## How We Overcame Them
- Removed `shell=True` and separated `npm install` and `npm start` into secure subprocess calls.
- Implemented state tracking (`last_active_agent`) and fixed the `GraphState` TypedDict.
- Updated `supervisor.txt` to strictly forbid asking clarifying questions, forcing it to assume reasonable defaults.
- Fixed the `useWebSocket.ts` cache to prevent the blank page error on refresh.
