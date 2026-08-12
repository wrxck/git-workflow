---
description: Comprehensive code review that checks security, performance, and correctness in parallel, then produces a unified report ranked by severity
---

# /review

Comprehensive code review that checks security, performance, and correctness in parallel, then produces a unified report ranked by severity.

## Usage

- `/review` -- review all uncommitted changes (git diff)
- `/review <path>` -- review a specific file or directory

## Steps

1. **Identify scope** -- determine which files to review:
   - if a path argument is given, review that file or directory
   - otherwise, use `git diff` and `git diff --cached` to find all changed files
   - list the files that will be reviewed

2. **Spawn 3 parallel review agents** -- use the Task tool to launch these concurrently:

   ### Security agent
   Review all changed files for:
   - docker configuration issues (exposed ports, privileged mode, missing health checks)
   - environment variable handling (secrets in code, missing .env.example entries)
   - injection vulnerabilities (SQL, command, XSS, SSRF, path traversal)
   - authentication/authorisation gaps
   - dependency vulnerabilities (known CVEs in added packages)
   - exposed credentials or API keys

   Output format: one line per finding -- `file:line | issue | severity (critical/high/medium/low) | suggested fix`

   ### Performance agent
   Review all changed files for:
   - connection pooling changes (verify pool sizes, timeouts)
   - N+1 query patterns or missing indexes
   - middleware ordering issues
   - timeout and retry configuration (verify defaults are sensible)
   - memory leaks (unclosed resources, growing caches)
   - SSR/rendering performance (unnecessary re-renders, large bundles)
   - blocking operations in async contexts

   Output format: one line per finding -- `file:line | issue | severity (critical/high/medium/low) | suggested fix`

   ### Correctness agent
   Review all changed files for:
   - logic errors and off-by-one mistakes
   - unhandled edge cases (null, empty, boundary values)
   - error handling gaps (uncaught exceptions, missing error responses)
   - type safety issues (implicit any, unsafe casts)
   - race conditions or concurrency issues
   - broken API contracts (changed return types, missing fields)
   - test coverage gaps for new code paths

   Output format: one line per finding -- `file:line | issue | severity (critical/high/medium/low) | suggested fix`

3. **Synthesise results** -- combine all findings:
   - deduplicate overlapping findings across agents
   - flag conflicts (e.g. a security fix that hurts performance)
   - sort by severity: critical -> high -> medium -> low

4. **Produce unified report** -- format as a table:
   ```
   | # | File:Line | Category | Severity | Issue | Fix |
   ```

   followed by:
   - total counts per severity
   - total counts per category (security/performance/correctness)
   - any cross-cutting concerns or conflicts

5. **Auto-fix critical issues** -- for any critical-severity findings:
   - apply the suggested fix
   - run the test suite to verify the fix doesn't break anything
   - report what was fixed and test results

6. **Summary** -- end with a one-paragraph assessment of overall code quality and the most important action items.
