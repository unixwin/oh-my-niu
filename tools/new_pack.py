#!/usr/bin/env python3
"""Scaffold (or remove) an oh-my-niu pack with every registration wired.

A pack lives in FOUR places plus one optional asset, and forgetting any of
them fails Bundle CI after the fact (that is exactly how the jj pack first
landed broken):

    packs/<name>/plugin.toml          pack manifest (bundle-owned fields)
    packs/<name>/init.niu             pack entry sourced by the loader
    plugins/<name>/plugin.toml        framework plugin manifest
    plugins/<name>/<name>.plugin.niu  framework plugin body
    completions/<name>.toml           optional (--with-completions)

Registrations, all appended in one consistent position:

    index.toml                        [[packs]] entry (end of the list)
    bundle.toml                       "available" list (end)
    tools/validate_bundle.py          EXPECTED_FRAMEWORK_PLUGINS tuple

Usage:
    python tools/new_pack.py add <name> [--summary S] [--category C]
                                  [--required-binary B] [--with-completions]
    python tools/new_pack.py remove <name>

Both commands run the bundle validator at the end and fail loudly if any
anchor drifted, so the tool itself goes stale visibly instead of silently.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

PACK_MANIFEST = """\
name = "{name}"
bundle = "oh-my-niu"
version = "1.0.0"
kind = "source"
api = "niubash:plugin@0.1.0"
category = "{category}"
summary = "{summary}"
default = false
permissions = ["shell:source", "cwd:read"{process_perm}]
required_binaries = [{required}]

[exports]
aliases = false
completions = [{completions}]
prompt_segments = []
hooks = []
commands = []
keybindings = []
themes = []

[source]
entry = "packs/{name}/init.niu"
"""

PACK_INIT = """\
# oh-my-niu {name} plugin
# Scaffolded by tools/new_pack.py; replace the placeholder with real
# behavior. Aliases and completions live in bundle assets.

{name}_hello() {{
  echo "{name} pack is wired"
}}
"""

PLUGIN_MANIFEST = """\
name = "{name}"
version = "1.0.0"
kind = "source"
entry = "{name}.plugin.niu"
summary = "{summary}"
permissions = ["shell:source", "cwd:read"{process_perm}]
required_binaries = [{required}]

[exports]
aliases = false
functions = ["{name}_hello"]
completions = [{completions}]
"""

PLUGIN_BODY = """\
# Oh My Niu {name} plugin.

# Scaffolded by tools/new_pack.py; the framework loader sources this file
# when the pack is enabled. Keep it aligned with packs/{name}/init.niu.
{name}_hello() {{
  echo "{name} pack is wired"
}}
"""

COMPLETIONS_STUB = """\
# {name} completions for niubash / oh-my-niu.
command = "{name}"
description = "{summary}"

[[flags]]
short = "-h"
long = "--help"
description = "show help"
"""


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def assert_anchor(text: str, needle: str, where: str) -> None:
    if needle not in text:
        die(f"anchor drifted in {where}: {needle!r} not found — "
            f"update tools/new_pack.py to match the file")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)}")


def add(name: str, args) -> None:
    if not NAME_RE.match(name):
        die(f"invalid pack name {name!r}: lowercase letters, digits, dashes")
    if (ROOT / "packs" / name).exists() or (ROOT / "plugins" / name).exists():
        die(f"pack {name!r} already exists")

    required = f'"{args.required_binary}"' if args.required_binary else ""
    completions = f'"{name}"' if args.with_completions else ""
    process_perm = f', "process:run:{args.required_binary}"' if args.required_binary else ""
    fields = {
        "name": name,
        "summary": args.summary,
        "category": args.category,
        "required": required,
        "completions": completions,
        "process_perm": process_perm,
    }

    print(f"scaffolding pack {name!r}:")
    write(ROOT / "packs" / name / "plugin.toml", PACK_MANIFEST.format(**fields))
    write(ROOT / "packs" / name / "init.niu", PACK_INIT.format(**fields))
    write(ROOT / "plugins" / name / "plugin.toml", PLUGIN_MANIFEST.format(**fields))
    write(ROOT / "plugins" / name / f"{name}.plugin.niu", PLUGIN_BODY.format(**fields))
    if args.with_completions:
        write(ROOT / "completions" / f"{name}.toml", COMPLETIONS_STUB.format(**fields))

    # index.toml: packs run to end of file — append.
    index = ROOT / "index.toml"
    text = index.read_text(encoding="utf-8")
    assert_anchor(text, '[[packs]]\nname = "git"', str(index))
    if not text.endswith("\n"):
        text += "\n"
    entry = ("\n[[packs]]\n"
             f'name = "{name}"\n'
             'version = "1.0.0"\n'
             'api = "niubash:plugin@0.1.0"\n'
             'kind = "source"\n'
             f'category = "{args.category}"\n'
             f'summary = "{args.summary}"\n'
             "default = false\n"
             'permissions = ["shell:source", "cwd:read"' + process_perm + "]\n"
             f"required_binaries = [{required}]\n")
    index.write_text(text + entry, encoding="utf-8", newline="\n")
    print(f"  registered {index.relative_to(ROOT)}")

    # bundle.toml: append at the end of the available list.
    bundle = ROOT / "bundle.toml"
    text = bundle.read_text(encoding="utf-8")
    match = re.search(r"available = \[\n(.*?)(^\]\s*$)", text, re.S | re.M)
    if not match:
        die("anchor drifted in bundle.toml: available list not found")
    insert_at = match.start(2)
    text = text[:insert_at] + f'  "{name}",\n' + text[insert_at:]
    bundle.write_text(text, encoding="utf-8", newline="\n")
    print(f"  registered {bundle.relative_to(ROOT)}")

    # validate_bundle.py: EXPECTED_FRAMEWORK_PLUGINS tuple.
    validator = ROOT / "tools" / "validate_bundle.py"
    text = validator.read_text(encoding="utf-8")
    assert_anchor(text, "EXPECTED_FRAMEWORK_PLUGINS = (", str(validator))
    text, count = re.subn(
        r"(EXPECTED_FRAMEWORK_PLUGINS = \(\n.*?)(^\))",
        lambda m: m.group(1) + f'    "{name}",\n' + m.group(2),
        text, count=1, flags=re.S | re.M)
    if count != 1:
        die("anchor drifted in validate_bundle.py: tuple close not found")
    validator.write_text(text, encoding="utf-8", newline="\n")
    print(f"  registered {validator.relative_to(ROOT)}")


def remove(name: str) -> None:
    removed = False
    for sub in ("packs", "plugins"):
        d = ROOT / sub / name
        if d.exists():
            for f in d.iterdir():
                f.unlink()
            d.rmdir()
            print(f"  removed {d.relative_to(ROOT)}/")
            removed = True
    comp = ROOT / "completions" / f"{name}.toml"
    if comp.exists():
        comp.unlink()
        print(f"  removed {comp.relative_to(ROOT)}")
        removed = True
    if not removed:
        die(f"pack {name!r} not found")

    for path, pattern in (
        (ROOT / "bundle.toml", re.compile(rf'^  "{re.escape(name)}",\n', re.M)),
        (ROOT / "tools" / "validate_bundle.py",
         re.compile(rf'^    "{re.escape(name)}",\n', re.M)),
    ):
        text = path.read_text(encoding="utf-8")
        text, n = pattern.subn("", text)
        if n != 1:
            die(f"expected exactly one registration line in {path.name}, found {n}")
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"  unregistered {path.relative_to(ROOT)}")

    # index.toml: split into [[packs]] blocks and drop the matching one.
    # Block lines may contain '[' (permissions = [...]), so anchor on the
    # next table header rather than scanning for bracket-free lines.
    index = ROOT / "index.toml"
    text = index.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^\[\[packs\]\]\n", text)
    header, blocks = parts[0], parts[1:]
    kept = []
    dropped = 0
    for block in blocks:
        if block.startswith(f'name = "{name}"\n'):
            dropped += 1
        else:
            kept.append(block)
    if dropped != 1:
        die(f"expected exactly one [[packs]] block for {name!r} in index.toml, "
            f"found {dropped}")
    text = header + "".join(f"[[packs]]\n{b}" for b in kept)
    text = text.rstrip("\n") + "\n"
    index.write_text(text, encoding="utf-8", newline="\n")
    print(f"  unregistered {index.relative_to(ROOT)}")


def validate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_bundle.py")],
        capture_output=True, text=True)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        die("bundle validation failed after the change — fix before committing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    addp = sub.add_parser("add", help="scaffold a new pack with all wiring")
    addp.add_argument("name")
    addp.add_argument("--summary", default="TODO: one-line summary")
    addp.add_argument("--category", default="devtools")
    addp.add_argument("--required-binary", default=None,
                      help="binary that must be on PATH (gates the pack)")
    addp.add_argument("--with-completions", action="store_true",
                      help="also scaffold completions/<name>.toml")
    remp = sub.add_parser("remove", help="remove a scaffolded/any pack cleanly")
    remp.add_argument("name")
    args = parser.parse_args()

    if args.command == "add":
        add(args.name, args)
    else:
        remove(args.name)
    validate()


if __name__ == "__main__":
    main()
