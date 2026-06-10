# Day 10: June 04, 2026 - Gemini Migration and Optimization

## What We Did
A massive day of engineering. We implemented the Circuit Breaker, Project Persistence, and Iterative Memory. We abandoned Groq due to severe rate limits and migrated the entire pipeline to the Gemini Free Tier (Gemini 3.1 Pro and 3.1 Flash-Lite). We also switched the backend scaffolding to use `pnpm` globally.

## Challenges Faced
- **Groq TPM Limits**: `qwen3-32b` on Groq only allowed 6,000 Tokens Per Minute, completely crashing on large app generation.
- **Disk Space Exhaustion**: Generating a new `node_modules` folder for every test case was rapidly eating up disk space.
- **Tailwind CSS v4 Release**: Tailwind suddenly released v4, which broke Vite's PostCSS compiler with `Cannot apply unknown utility class` errors.
- **Duplicate Projects**: The batch test script created UI duplicates because it generated random UUIDs on every run without clearing the DB.

## How We Overcame Them
- Switched to Gemini 3.5 Flash / 3.1 Flash-Lite, unlocking 250,000 TPM and eliminating the rate limit crashes.
- Implemented `pnpm` scaffolding, allowing all projects to share a single global `node_modules` cache, massively speeding up rendering and saving disk space.
- Patched the project templates to use `@tailwindcss/postcss` and removed the deprecated `@tailwind` directives.
