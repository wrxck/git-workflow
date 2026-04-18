# git-workflow

Git workflow enforcement and commands for Claude Code sessions.

## What it enforces (via PreToolUse Bash hooks)

`git_workflow_guard.py` parses every Bash invocation with a shell tokeniser
(handles env-var prefixes, `bash -c`, `;`/`&&`/`||`/`|` splits, and heredocs)
and blocks the following with a non-zero exit and a `BLOCKED:` reason:

- Direct push to `main` or `develop`, including refspec forms like
  `origin HEAD:main`, `origin +main`, `origin feat/x:main`, and
  `origin main develop`. Bare `git push` is blocked when the local branch
  resolves to `main`/`develop` (best-effort via `git symbolic-ref`).
- Force push in every flavour: `--force`, `-f`, and `--force-with-lease`
  are all treated the same — Matt does not use lease-force.
- `--no-verify` on `commit`, `push`, or `tag`.
- `git commit --amend` (create a new commit instead).
- Deleting `main` or `develop` locally (`git branch -D main`) or remotely
  (`git push origin --delete main`).
- Commit messages containing `Co-Authored-By:` (case-insensitive). Handles
  `-m "..."`, `-m '...'`, `-m $'...'`, multiple `-m` flags, and full
  heredoc bodies (`<<EOF`, `<<'EOF'`, `<<-EOF`).

If the guard cannot safely parse a command it **fails closed** with
`BLOCKED: git_workflow_guard could not parse command safely` — retype
the command more simply.

## What it cannot enforce

Commits that read the message from a file (`git commit -F file.txt` or
`--file=...`) are not content-scanned; the hook cannot reliably read
arbitrary files from the sandbox. If you use `-F`, verify the file does
not contain `Co-Authored-By:` yourself (e.g. `grep -i co-authored-by
<file>`). The guard will warn and block when `-F` is used without any
inline message content.

## Commit message linting

`git_commit_validator.py` additionally lints inline commit messages for
conventional-commit format, British English spelling, lowercase subject
after the type, no trailing period, and subject length. It uses a proper
shell tokeniser so it handles heredocs and multiple `-m` flags.

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
