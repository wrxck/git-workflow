#!/usr/bin/env python3
"""
Claude Code hook to validate git commit messages:
- conventional commits format (feat, fix, docs, style, refactor, test, chore)
- british english spelling
- lowercase after type prefix
- no trailing period
"""

import json
import re
import shlex
import sys

# british spelling replacements (subset focused on common commit message words)
BRITISH_SPELLINGS = {
    'behavior': 'behaviour',
    'behaviors': 'behaviours',
    'color': 'colour',
    'colors': 'colours',
    'favor': 'favour',
    'favorite': 'favourite',
    'initialize': 'initialise',
    'initialized': 'initialised',
    'initializing': 'initialising',
    'initialization': 'initialisation',
    'optimize': 'optimise',
    'optimized': 'optimised',
    'optimizing': 'optimising',
    'optimization': 'optimisation',
    'organize': 'organise',
    'organized': 'organised',
    'organizing': 'organising',
    'organization': 'organisation',
    'recognize': 'recognise',
    'recognized': 'recognised',
    'synchronize': 'synchronise',
    'synchronized': 'synchronised',
    'customize': 'customise',
    'customized': 'customised',
    'customize': 'customise',
    'analyze': 'analyse',
    'analyzed': 'analysed',
    'center': 'centre',
    'centered': 'centred',
    'canceled': 'cancelled',
    'canceling': 'cancelling',
    'labeled': 'labelled',
    'labeling': 'labelling',
    'modeled': 'modelled',
    'modeling': 'modelling',
    'traveled': 'travelled',
    'traveling': 'travelling',
    'gray': 'grey',
    'license': 'licence',
    'defense': 'defence',
    'offense': 'offence',
}

# conventional commit types
COMMIT_TYPES = {'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'perf', 'ci', 'build', 'revert'}


def check_commit_message(message: str) -> list[str]:
    """validate commit message format and spelling"""
    issues = []

    # get first line (subject)
    lines = message.strip().split('\n')
    subject = lines[0] if lines else ''

    if not subject:
        return ['empty commit message']

    # check conventional commit format
    conv_match = re.match(r'^(\w+)(\([^)]+\))?(!)?:\s*(.+)$', subject)

    if not conv_match:
        issues.append(
            "commit should follow conventional format: type(scope): description"
        )
    else:
        commit_type = conv_match.group(1)
        description = conv_match.group(4)

        # check type is valid
        if commit_type not in COMMIT_TYPES:
            issues.append(
                f"unknown commit type '{commit_type}' - use: {', '.join(sorted(COMMIT_TYPES))}"
            )

        # check description starts with lowercase
        if description and description[0].isupper():
            issues.append("description should start with lowercase letter")

        # check for trailing period
        if description and description.rstrip().endswith('.'):
            issues.append("commit message should not end with a period")

        # check length
        if len(subject) > 72:
            issues.append(f"subject line too long ({len(subject)} chars) - keep under 72")

    # check british spelling in entire message
    message_lower = message.lower()
    for american, british in BRITISH_SPELLINGS.items():
        if re.search(rf'\b{american}\b', message_lower):
            issues.append(f"use british spelling: '{american}' → '{british}'")

    return issues


def _strip_heredocs(command):
    bodies = []
    remaining = []
    lines = command.split('\n')
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
            header = header.replace(m.group(0), '')
        remaining.append(header)
        pending = [(m.group('word'), '<<-' in m.group(0)) for m in matches]
        i += 1
        for word, dash in pending:
            body = []
            closed = False
            while i < len(lines):
                cand = lines[i]
                stripped = cand.lstrip('\t') if dash else cand
                if stripped.rstrip() == word or stripped == word:
                    i += 1
                    closed = True
                    break
                body.append(cand)
                i += 1
            if not closed:
                return command, []
            bodies.append('\n'.join(body))
    return '\n'.join(remaining), bodies


def _extract_message(command):
    """return commit message body (possibly empty) and whether -F was used."""
    try:
        cleaned, bodies = _strip_heredocs(command)
        tokens = shlex.split(cleaned, posix=True)
    except ValueError:
        return '', False

    # find first `git` then the `commit` subcommand
    i = 0
    while i < len(tokens) and tokens[i] != 'git':
        i += 1
    if i >= len(tokens):
        return '', False
    j = i + 1
    while j < len(tokens) and tokens[j].startswith('-'):
        if tokens[j] in {'-C', '-c'} and j + 1 < len(tokens):
            j += 2
            continue
        j += 1
    if j >= len(tokens) or tokens[j] != 'commit':
        return '', False

    args = tokens[j + 1:]
    messages = []
    uses_file = False
    k = 0
    while k < len(args):
        a = args[k]
        if a in {'-m', '--message'} and k + 1 < len(args):
            messages.append(args[k + 1])
            k += 2
            continue
        if a.startswith('--message='):
            messages.append(a.split('=', 1)[1])
            k += 1
            continue
        if a.startswith('-m') and len(a) > 2:
            messages.append(a[2:])
            k += 1
            continue
        if a in {'-F', '--file'}:
            uses_file = True
            k += 2
            continue
        if a.startswith('--file='):
            uses_file = True
            k += 1
            continue
        k += 1

    combined = '\n\n'.join(messages + bodies)
    return combined, uses_file


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')

    if 'git commit' not in command:
        sys.exit(0)

    message, uses_file = _extract_message(command)
    if uses_file and not message:
        sys.exit(0)
    if not message:
        sys.exit(0)

    issues = check_commit_message(message)

    if issues:
        print("commit message issues:", file=sys.stderr)
        for issue in issues:
            print(f"  • {issue}", file=sys.stderr)
        print("\nformat: type(scope): lowercase description without period", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
