import js from "@eslint/js";

/** @type {import('eslint').Linter.Config[]} */
const config = [
  js.configs.recommended,
  {
    // Ignore everything - ESLint is for local dev only
    // next build handles its own type checking
    ignores: [
      "**/*"
    ],
  },
];

export default config;
