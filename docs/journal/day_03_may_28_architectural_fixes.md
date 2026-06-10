# Day 3: May 28, 2026 - Architectural Fixes and Prompt Engineering

## What We Did
We successfully ran the first end-to-end test ('Build a stopwatch') using the browser subagent. The user provided highly optimized custom prompts with EASY/MEDIUM/HARD complexity classification, which we integrated into the system. The user also pointed out 14 critical architectural issues in a brilliant code review.

## Challenges Faced
- **LangChain Escaping**: LangChain crashed because it attempted to parse raw `{` and `}` in the frontend/backend code templates as variables.
- **Port Conflicts**: Hardcoded ports (`8000`) caused silent failures when the backend was shifted to `8001`.
- **JSON Parsing Errors**: The Assembler generated JSON containing markdown backticks and nested WebContainer directory structures, which completely broke the frontend preview parser.

## How We Overcame Them
- Replaced `SystemMessagePromptTemplate.from_template()` with raw `SystemMessage` to permanently bypass the `{}` escaping issue.
- Moved all ports to `.env` variables and updated the frontend to dynamically fetch `NEXT_PUBLIC_API_URL`.
- Implemented a robust custom regex parser in `PreviewPanel.tsx` and updated the Assembler agent to sanitize JSON outputs, strip backticks, and properly nest the WebContainer file structures.
