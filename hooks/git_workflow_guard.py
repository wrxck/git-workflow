#!/usr/bin/env python3
"""git_workflow_guard: pretooluse bash hook that blocks policy-violating git ops."""

import json
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "develop"}


def block(reason: str) -> None:
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)


def fail_closed(reason: str) -> None:
    print(
        f"BLOCKED: git_workflow_guard could not parse command safely ({reason}). "
        "retype the command more simply, or run git directly outside of claude.",
        file=sys.stderr,
    )
    sys.exit(2)


def strip_heredocs(command: str) -> tuple[str, list[str]]:
    bodies: list[str] = []
    remaining: list[str] = []
    lines = command.split("\n")
    i = 0
    hd_re = re.compile(r"<<-?\s*(?P<q>['\"]?)(?P<word>[A-Za-z_][A-Za-z0-9_]*)(?P=q)")
    while i < len(lines):
        line = lines[i]
        matches = list(hd_re.finditer(line))
        if not matches:
            remaining.append(line)
            i += 1
            continue
        header = line
        for m in matches:
            header = header.replace(m.group(0), "")
        remaining.append(header)
        pending = [(m.group("word"), "<<-" in m.group(0)) for m in matches]
        i += 1
        for word, dash in pending:
            body: list[str] = []
            closed = False
            while i < len(lines):
                cand = lines[i]
                stripped = cand.lstrip("\t") if dash else cand
                if stripped.rstrip() == word or stripped == word:
                    i += 1
                    closed = True
                    break
                body.append(cand)
                i += 1
            if not closed:
                raise ValueError(f"unterminated heredoc {word!r}")
            bodies.append("\n".join(body))
    return "\n".join(remaining), bodies


def split_command_string(s: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    in_single = False
    in_double = False
    while i < len(s):
        c = s[i]
        if in_single:
            buf.append(c)
            if c == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            buf.append(c)
            if c == '"' and not (i > 0 and s[i - 1] == "\\"):
                in_double = False
            i += 1
            continue
        if c == "'":
            in_single = True
            buf.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            buf.append(c)
            i += 1
            continue
        two = s[i:i + 2]
        if two in ("&&", "||"):
            parts.append("".join(buf).strip())
            buf = []
            i += 2
            continue
        if c in (";", "|", "&", "\n"):
            parts.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def split_statements(tokens: list[str]) -> list[list[str]]:
    return [tokens] if tokens else []


def strip_env_prefix(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    return tokens[i:]


def unwrap_bash_c(tokens: list[str]) -> list[list[str]] | None:
    if len(tokens) < 2:
        return None
    base = tokens[0].rsplit("/", 1)[-1]
    if base not in {"bash", "sh", "zsh"}:
        return None
    for j in range(1, len(tokens)):
        if tokens[j] == "-c" and j + 1 < len(tokens):
            inner = tokens[j + 1]
            try:
                cleaned, _ = strip_heredocs(inner)
            except ValueError as exc:
                raise ValueError(f"bash -c body: {exc}")
            out: list[list[str]] = []
            for stmt_str in split_command_string(cleaned):
                try:
                    out.append(shlex.split(stmt_str, posix=True))
                except ValueError as exc:
                    raise ValueError(f"bash -c body: {exc}")
            return [s for s in out if s]
    return None


def is_git(tokens: list[str]) -> bool:
    return bool(tokens) and tokens[0].rsplit("/", 1)[-1] == "git"


def current_branch() -> str | None:
    try:
        r = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    return None


def get_git_args(tokens: list[str]) -> tuple[str | None, list[str]]:
    if not is_git(tokens):
        return None, []
    args = tokens[1:]
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] in {"-C", "-c"} and i + 1 < len(args):
            i += 2
            continue
        i += 1
    if i >= len(args):
        return None, []
    return args[i], args[i + 1:]


def check_push(args: list[str]) -> None:
    force = {"--force", "-f", "--force-with-lease"}
    for a in args:
        if a in force or a.startswith("--force-with-lease="):
            block("force push is not allowed (--force, -f, and "
                  "--force-with-lease are all blocked). ask matt before "
                  "rewriting history.")
        if a == "--no-verify":
            block("--no-verify is not allowed on git push. fix the hook.")

    pos: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("-"):
            if a in {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}:
                i += 2
                continue
            if a in {"--delete", "-d"}:
                rest = [x for x in args[i + 1:] if not x.startswith("-")]
                for ref in rest[1:] if rest else []:
                    if ref in PROTECTED:
                        block(f"refusing to delete remote branch '{ref}'. "
                              "matt forbids deleting main or develop.")
                i += 1
                continue
            i += 1
            continue
        pos.append(a)
        i += 1

    if not pos:
        b = current_branch()
        if b in PROTECTED:
            block(f"current branch '{b}' is protected; bare `git push` would "
                  "push it. check out a feature branch. (if symbolic-ref "
                  "failed this check, retype with an explicit refspec.)")
        return

    refs = pos[1:]
    if not refs:
        b = current_branch()
        if b in PROTECTED:
            block(f"current branch '{b}' is protected; `git push <remote>` "
                  "without a refspec would push it.")
        return

    for spec in refs:
        if spec.startswith("+"):
            block(f"force-push refspec '{spec}' (leading '+') rewrites "
                  "remote history and is blocked.")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        dst = dst.lstrip("+")
        short = dst.split("/")[-1] if dst.startswith("refs/heads/") else dst
        if short in PROTECTED:
            block(f"direct push to protected branch '{short}' is blocked. "
                  "open a pr from a feature branch into develop.")


def check_commit(args: list[str], bodies: list[str]) -> None:
    if "--amend" in args:
        block("git commit --amend is not allowed unless matt explicitly "
              "asks for it. create a new commit.")
    if "--no-verify" in args:
        block("--no-verify skips commit hooks and is not allowed. fix the "
              "hook failure at its source.")

    messages: list[str] = []
    uses_file = False
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"-m", "--message"} and i + 1 < len(args):
            messages.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--message="):
            messages.append(a.split("=", 1)[1])
            i += 1
            continue
        if a.startswith("-m") and len(a) > 2:
            messages.append(a[2:])
            i += 1
            continue
        if a in {"-F", "--file"}:
            uses_file = True
            i += 2
            continue
        if a.startswith("--file="):
            uses_file = True
            i += 1
            continue
        i += 1

    combined = "\n\n".join(messages + bodies)
    if re.search(r"co-authored-by\s*:", combined, re.IGNORECASE):
        block("commit message contains 'co-authored-by:'. matt is the "
              "sole author. remove the trailer and retry.")

    if uses_file and not messages and not bodies:
        block("commit uses -F/--file=<path>. git_workflow_guard cannot "
              "read the file to check for 'co-authored-by'. run "
              "`grep -i 'co-authored-by' <file>` yourself; if clean, "
              "inline the message with -m or a heredoc.")


def check_branch(args: list[str]) -> None:
    delete = False
    for a in args:
        if a in {"-D", "--delete", "-d"}:
            delete = True
        elif a.startswith("-") and not a.startswith("--") and len(a) > 1:
            if "D" in a[1:] or "d" in a[1:]:
                delete = True
    if not delete:
        return
    for a in args:
        if a.startswith("-"):
            continue
        if a in PROTECTED:
            block(f"refusing to delete local branch '{a}'. matt forbids "
                  "deleting main or develop.")


def check_tag(args: list[str]) -> None:
    if "--no-verify" in args:
        block("--no-verify is not allowed on git tag. fix the hook.")


def inspect(tokens: list[str], bodies: list[str]) -> None:
    tokens = strip_env_prefix(tokens)
    if not tokens:
        return
    try:
        inner = unwrap_bash_c(tokens)
    except ValueError as exc:
        fail_closed(str(exc))
        return
    if inner is not None:
        for sub in inner:
            inspect(sub, bodies)
        return
    if not is_git(tokens):
        return
    sub, sub_args = get_git_args(tokens)
    if sub == "push":
        check_push(sub_args)
    elif sub == "commit":
        check_commit(sub_args, bodies)
    elif sub == "branch":
        check_branch(sub_args)
    elif sub == "tag":
        check_tag(sub_args)


def process(command: str) -> None:
    try:
        cleaned, bodies = strip_heredocs(command)
    except ValueError as exc:
        fail_closed(str(exc))
        return

    if re.search(r"co-authored-by\s*:", command, re.IGNORECASE) and (
        "git commit" in command or "git tag" in command
    ):
        block("command contains 'co-authored-by:' near a git commit/tag. "
              "matt is the sole author. remove the trailer and retry.")

    for stmt_str in split_command_string(cleaned):
        try:
            stmt_tokens = shlex.split(stmt_str, posix=True)
        except ValueError as exc:
            fail_closed(f"shell tokenisation failed: {exc}")
            return
        if stmt_tokens:
            inspect(stmt_tokens, bodies)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)
    if "git" not in command:
        sys.exit(0)

    process(command)
    sys.exit(0)


if __name__ == "__main__":
    main()
