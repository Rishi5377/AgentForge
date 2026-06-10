# Day 5: May 30, 2026 - The Dyad Pivot and Native Execution

## What We Did
We conducted a deep analysis of the `dyad-sh/dyad` repository and realized they completely bypass in-browser sandboxes. We pivoted AgentForge to use Native Execution: writing files directly to the local disk (`workspace/app/`) and spawning `npm run dev` via `child_process`. We ran a stress test using 7 Beginner Test Cases (To-Do List, Calculator, etc.).

## Challenges Faced
- **In-Browser Sandboxes Failed**: Both WebContainers and Sandpack proved too fragile for full-stack AI app generation.
- **Model Unavailability**: Groq API rejected `moonshotai/kimi-k2-instruct` with a 404 error.
- **Zombie Processes**: The native execution model occasionally left orphaned Node.js servers running, crashing subsequent tests due to port conflicts (EADDRINUSE).
- **Groq 413 Rate Limit**: Bumping the `max_tokens` to `8192` triggered immediate rate limit crashes.

## How We Overcame Them
- Rewrote `assembler.py` to write files to disk and use native Node.js subprocesses to serve the previews via `localhost:5173`.
- Switched the backend model to `qwen/qwen3-32b`.
- Patched the Assembler to properly track and kill previous `npm start` processes before launching new ones.
