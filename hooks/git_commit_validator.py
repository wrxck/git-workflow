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


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')

    # only check git commit commands
    if 'git commit' not in command:
        sys.exit(0)

    # extract commit message from -m flag
    message_match = re.search(r'-m\s+[\'"](.+?)[\'"]', command, re.DOTALL)
    if not message_match:
        # check for heredoc style
        heredoc_match = re.search(r'-m\s+"\$\(cat <<[\'"]?EOF[\'"]?\s*\n(.+?)\nEOF', command, re.DOTALL)
        if heredoc_match:
            message = heredoc_match.group(1)
        else:
            sys.exit(0)
    else:
        message = message_match.group(1)

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
