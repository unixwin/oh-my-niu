#!/usr/bin/env python3
"""Regenerate completions/jj.toml from the official jj bash completions.

Usage:
    jj util completion bash > /tmp/jj.bash
    python tools/convert_jj_completions.py /tmp/jj.bash > completions/jj.toml

The parser targets clap_complete's bash output (two-space indent, one
`opts="..."` per `case "${cmd}"` branch). It extracts:
  - top-level flags (tokens starting with `-` in the `jj` branch)
  - every level-1 subcommand (from the dispatch table) with its own flags
  - static value lists from `--flag)` / `compgen -W "..."` prev-cases
"""

import re
import sys


def convert(src: str) -> str:
    l1 = re.findall(r'jj,([A-Za-z0-9_-]+)\)\s*\n?\s*cmd="jj__subcmd__\1"', src)
    branches = {}
    for m in re.finditer(r'\n\s+(jj__subcmd__[A-Za-z0-9_]+|jj)\)\n\s+opts="([^"]*)"', src):
        branches[m.group(1)] = m.group(2).split()
    valmap = {}
    for m in re.finditer(r'(--[A-Za-z0-9_-]+)\)\n\s+COMPREPLY=\(\$\(compgen -W "([^"]*)"', src):
        valmap.setdefault(m.group(1), m.group(2).split())

    out = [
        '# jj completions for niubash / oh-my-niu.',
        '# Generated from the official `jj util completion bash` output.',
        '# Regenerate: jj util completion bash | tools/convert_jj_completions.py',
        'command = "jj"',
        'description = "Jujutsu VCS (Git-compatible)"',
        '',
    ]

    def flag_block(flag: str, sub: bool, values):
        key = 'long' if flag.startswith('--') else 'short'
        lines = [('[[subcommands.flags]]' if sub else '[[flags]]'), f'{key} = "{flag}"']
        if values:
            lines.append('values = [' + ', '.join(f'"{v}"' for v in values) + ']')
        lines.append('')
        return lines

    for flag in sorted({t for t in branches.get('jj', []) if t.startswith('-')}):
        out += flag_block(flag, False, valmap.get(flag))
    for name in l1:
        tokens = branches.get(f'jj__subcmd__{name}')
        if tokens is None:
            continue
        out += ['[[subcommands]]', f'name = "{name}"', '']
        for flag in sorted({t for t in tokens if t.startswith('-')}):
            out += flag_block(flag, True, valmap.get(flag))
    return '\n'.join(out)


if __name__ == '__main__':
    src = open(sys.argv[1], encoding='utf-8').read() if len(sys.argv) > 1 else sys.stdin.read()
    print(convert(src))
