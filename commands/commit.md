# /commit -- Create a Git Commit

Create a commit on the current feature branch. Follow these rules exactly:

## Pre-flight checks

1. Verify you are NOT on `main` or `develop`. If you are, STOP and tell the user to switch to a feature branch first.
2. Run `git status` to see what's changed.
3. Run `git diff --staged` to review staged changes. If nothing is staged, stage the relevant files (NEVER use `git add .` or `git add -A` -- add specific files by name).

## Commit rules

- **NEVER** include `Co-Authored-By` in the commit message. Matt is the sole author.
- **NEVER** use `--no-verify`.
- **NEVER** amend a previous commit unless the user explicitly says "amend".
- Use **conventional commit** format: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`
  - Scope is optional but recommended (e.g. `feat(compiler):`, `fix(runtime):`)
- Keep the first line under 72 characters.
- Add a blank line then a body if the change needs explanation.
- Use a HEREDOC to pass the message:

```bash
git commit -m "$(cat <<'EOF'
type(scope): short description

Optional longer explanation of what changed and why.
EOF
)"
```

## Post-commit

- Run `git log --oneline -1` to confirm the commit.
- Tell the user what was committed and suggest `/pr` when they're ready.

## Arguments

If the user passes a message like `/commit fix: typo in readme`, use that as the commit message directly (still verify branch and stage files first).
