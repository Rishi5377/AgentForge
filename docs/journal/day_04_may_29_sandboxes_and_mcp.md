# Day 4: May 29, 2026 - The Sandbox Dilemma and Chrome MCP

## What We Did
We explored alternatives to WebContainers due to persistent mounting and iframe communication issues. We successfully integrated the `chrome-devtools-mcp` to allow the AI to directly interact with and visually verify the AgentForge UI. We also attempted to switch from WebContainers to Sandpack.

## Challenges Faced
- **WebContainer Flaws**: `npm install` inside the browser was slow and fragile.
- **Sandpack Constraints**: Sandpack's `node` template threw Unicode escape sequence errors when parsing the LLM-generated code.
- **Prompt Architecture Mismatch**: Our AI prompts were highly optimized for WebContainers, causing conflicts when Sandpack expected a different file structure.

## How We Overcame Them
- Used Chrome DevTools MCP to get visual confirmation that the backend pipeline was successfully transmitting data to the frontend via WebSockets.
- Stripped strict `Cross-Origin-Embedder-Policy` headers to allow Sandpack to load.
- Avoided rewriting the AI prompts by configuring Sandpack to use a raw Node.js environment, attempting to perfectly mimic the WebContainer execution context.
