---
description: Create a PR from the current feature branch to `develop` for Matt to review
---

# /pr -- Create a Pull Request

Create a PR from the current feature branch to `develop` for Matt to review.

## Pre-flight checks

1. Verify you are on a feature branch (NOT `main` or `develop`). If not, STOP.
2. Run `git status` -- ensure working tree is clean. If there are uncommitted changes, ask the user if they want to commit first (suggest `/commit`).
3. Run `git log develop..HEAD --oneline` to see what commits will be in the PR.
4. Check if the branch is pushed: `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null`. If not tracking a remote, push with `git push -u origin HEAD`.

## Create the PR

- **Base branch**: `develop` (ALWAYS -- never PR directly to `main`)
- **Title**: Short, under 70 characters, describes the feature/fix
- **Body format**:

```
gh pr create --base develop --title "the title" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points describing what changed>

## Changes
<list of key files/areas modified>

## Test plan
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual verification steps if applicable
EOF
)"
```

- **NEVER** include `Co-Authored-By` anywhere in the PR.
- **NEVER** create a PR to `main`. All PRs go to `develop`.

## Post-PR

- Show the PR URL to the user.
- Tell them: "PR is ready for your review. I'll wait for your feedback."

## Arguments

`/pr` -- auto-detect everything
`/pr "title here"` -- use the provided title
