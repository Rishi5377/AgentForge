# Day 11: June 05, 2026 - Open Design and System Prompts Leak

## What We Did
We integrated the `open-design` CSS token system to upgrade the UI. We executed 5 complex QA test cases (Form Validation, Product Catalog, Hotel Booking, Live Voting, Role Management) using the `browser` subagent. The user provided an incredible repository of leaked MNC system prompts (`asgeirtj/system_prompts_leaks`), which we used to completely rewrite AgentForge's brain. We completed Phase 3.1 (Project Templates).

## Challenges Faced
- **CSS Variable Compilation**: Tailwind v4's `@theme` compiler failed to resolve `var()` pointers, rendering the UI completely blank.
- **Iterative Destruction**: During the complex test cases, iterative modification prompts often crashed the React applications because the LLM overwrote working logic.
- **Chesterton's Fence**: Blindly updating prompts risked breaking carefully constructed edge-case handling.
- **React Hydration Errors**: A missing `</div>` tag during the Device Mode UI update broke the Next.js compilation.

## How We Overcame Them
- Deployed a hybrid design system approach, fixing the `globals.css` imports.
- Spun up a Prompt Leak Researcher subagent to extract the best instructions from Claude, v0, and Bolt, and injected them into our agents while respecting Chesterton's Fence.
- Successfully verified the new prompt architecture by generating a flawless Full-Stack SaaS Dashboard.
- Investigated 10 competitor repositories (Bolt.diy, OpenHands, Devika, etc.) and drafted brainstorming reports to plan the final evolution of AgentForge.
