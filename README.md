# git-workflow

Git workflow enforcement and commands for Claude Code sessions.

## What it checks

- **Commit validation**: conventional commit format, British English spelling, lowercase descriptions, no trailing period, subject line length

## Commands

- `/commit` -- create a git commit following conventional commit rules
- `/pr` -- create a pull request from the current feature branch to develop
- `/release` -- guided release process with step-by-step approval
- `/review` -- comprehensive parallel code review (security, performance, correctness)

## Installation

```
claude plugin marketplace add wrxck/claude-plugins
claude plugin install git-workflow@wrxck-claude-plugins
```
