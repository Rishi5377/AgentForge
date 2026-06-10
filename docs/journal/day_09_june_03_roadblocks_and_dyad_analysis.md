# Day 9: June 03, 2026 - Identifying the Ultimate Roadblocks

## What We Did
We conducted a deep audit to figure out why AgentForge couldn't reliably build heavy, full-stack applications. We identified the core bottlenecks holding the project back from becoming a true Dyad/Bolt alternative.

## Challenges Faced
- **Token Limits**: The 5,000 token limit was drastically too small for a full React app.
- **Infinite Loops**: Agents would get stuck in endless retry cycles if a bug occurred.
- **No Persistence**: Every new prompt completely wiped the previous `workspace/app/` directory, making iterative development impossible.
- **WebContainer Artifacts**: Relics of the old WebContainer logic were still causing bugs in the native execution path.

## How We Overcame Them
- The user correctly proposed breaking down the code generation into multiple, smaller LLM calls (file-by-file scaffolding) rather than one massive monolithic generation. This formed the blueprint for the next day's architecture.
