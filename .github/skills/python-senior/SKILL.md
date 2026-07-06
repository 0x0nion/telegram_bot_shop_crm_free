---
name: python-senior
description: 'Use for senior-level Python development tasks such as implementing features, debugging issues, refactoring code, and improving reliability, readability, and test coverage.'
argument-hint: 'Describe the Python task, bug, or refactor you want to complete.'
user-invocable: true
---

# Senior Python Development

## When to Use
- Implementing a new Python feature or API flow
- Debugging a bug or unexpected behavior
- Refactoring for clarity, maintainability, or performance
- Improving tests, typing, error handling, or documentation
- Reviewing a change for production readiness

## Core Principles
- Clarify the goal before editing code
- Prefer the smallest change that satisfies the requirement
- Keep behavior backward-compatible unless a breaking change is explicitly requested
- Follow existing project conventions and patterns
- Improve reliability with tests, validation, and clear error handling
- Verify changes with real execution evidence

## Procedure
1. Understand the request
   - Restate the goal in your own words
   - Identify constraints, expected behavior, and acceptance criteria
   - Ask for clarification if requirements are ambiguous

2. Inspect the relevant codebase
   - Locate the modules, entry points, and data flow involved
   - Read adjacent implementations to match local conventions
   - Note dependencies, side effects, and any existing tests

3. Plan the change
   - Choose the minimal approach that solves the problem
   - Identify edge cases, regressions, and risks
   - Decide whether the change needs tests, docs, or config updates

4. Implement carefully
   - Make focused edits with clear naming and readable structure
   - Preserve existing behavior unless the request requires a change
   - Add or adjust typing, validation, logging, and exception handling where appropriate

5. Validate the result
   - Run the relevant tests or commands
   - Reproduce the issue before fixing it when debugging
   - Check for linting, formatting, or import issues if applicable
   - Confirm the change actually solves the request

6. Summarize and hand off
   - Explain what changed and why
   - Mention verification evidence, including commands or test results
   - Highlight any follow-up risks or next steps

## Decision Points
- If the request is a bug: reproduce it first, identify the root cause, and fix that directly
- If the request is a feature: verify requirements, implement with minimal surface area, and add coverage
- If the request is a refactor: preserve behavior and document the intent clearly
- If the change touches shared logic: review downstream impact and add regression tests

## Completion Checklist
- The requirement is implemented or the bug is fixed
- The solution follows project conventions
- Relevant tests or verification steps were executed
- The change is understandable and maintainable
- The final response includes what changed, why, and how it was verified
