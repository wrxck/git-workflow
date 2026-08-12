---
description: This is a guided release process
---

# /release -- Prepare a Release

This is a guided release process. It requires Matt's explicit approval at every step.

## Step 1: Confirm with the user

Ask Matt:
- What version number? (e.g. `v0.5.0`)
- Is `develop` ready to release? (list the commits since last tag)

Show: `git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~20)..develop --oneline`

**STOP and wait for confirmation before proceeding.**

## Step 2: Prepare release

Only after Matt confirms:

1. Ensure you are on `develop` and it's up to date: `git checkout develop && git pull origin develop`
2. Update version numbers in all `package.json` files if requested.
3. Run `pnpm build && pnpm test && pnpm lint` -- all must pass.
4. If Matt requested a changelog, prepare it.

**STOP and show Matt the summary. Wait for approval.**

## Step 3: Tag and publish (only with explicit approval)

1. Create and push the tag: `git tag -a vX.Y.Z -m "vX.Y.Z"` then `git push origin vX.Y.Z`
2. Wait for CI to confirm the npm publish succeeded (check GitHub Actions).
3. Create a GitHub release via `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."`.

**STOP and confirm success with Matt.**

## Step 4: PR develop into main

1. Create a PR from `develop` to `main` with the release changelog.
2. Tell Matt: "PR is ready for you to merge develop into main."

## Rules

- **NEVER** run this without Matt's explicit request.
- **NEVER** push tags or publish without confirmation at each step.
- **NEVER** include `Co-Authored-By` in any commit.
- **NEVER** push directly to main -- always PR.
- Matt reviews and merges the final PR to main himself.
