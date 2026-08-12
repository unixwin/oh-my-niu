#!/usr/bin/env python3
"""Validate the oh-my-winuxsh bundle manifest layout."""

from __future__ import annotations

import hashlib
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWN_KINDS = {"builtin", "source", "wasm", "process"}
FRAMEWORK_PLUGIN_KINDS = {"source", "bridge"}
KNOWN_CATEGORIES = {"devtools", "environment", "workflow", "hints", "ux"}
BUNDLE_API_VERSION = "winuxsh:plugin-bundle@0.1.0"
INDEX_SCHEMA = "winuxsh:plugin-index@0.1.0"
EXPORT_KEYS = {
    "aliases",
    "completions",
    "prompt_segments",
    "hooks",
    "commands",
    "keybindings",
    "themes",
    "providers",
}
REQUIRED_EXPORT_KEYS = EXPORT_KEYS - {"keybindings", "providers"}
KNOWN_PROVIDER_EXPORTS = {"command-not-found"}
SOURCE_PLUGIN_HOOKS = {"startup", "precmd", "preexec", "chpwd"}
PROCESS_PLUGIN_PROTOCOL = "winuxsh:process-plugin@0.1.0"
PROCESS_PLUGIN_MAX_TIMEOUT_MILLIS = 30_000
WASM_PLUGIN_PROTOCOL = "winuxsh:wasm-plugin@0.1.0"
WASM_PLUGIN_MAX_TIMEOUT_MILLIS = 30_000
WASM_PLUGIN_MAX_MEMORY_PAGES = 4096
AUTHORING_TEMPLATE_KINDS = {
    "builtin": "builtin",
    "source": "source",
    "process": "process",
    "wasm": "wasm",
}
THEME_STYLE_KEYS = {
    "prompt_user",
    "prompt_host",
    "prompt_dir",
    "prompt_symbol",
    "error",
    "warning",
    "success",
    "git_clean",
    "git_dirty",
    "git_status_detail",
}
THEME_COLOR_NAMES = {
    "black",
    "darkgray",
    "darkgrey",
    "red",
    "lightred",
    "green",
    "lightgreen",
    "yellow",
    "lightyellow",
    "blue",
    "lightblue",
    "purple",
    "lightpurple",
    "magenta",
    "lightmagenta",
    "cyan",
    "lightcyan",
    "white",
    "lightgray",
    "lightgrey",
}
RELEASE_DOCUMENTS = {
    "CHANGELOG.md": (
        "# Changelog",
        "oh-my-winuxsh-{version}.zip",
        'api = "winuxsh:plugin-bundle@0.1.0"',
        'min_winuxsh = "{min_winuxsh}"',
    ),
    "docs/compatibility.md": (
        "# Compatibility",
        "winuxsh:plugin-bundle@0.1.0",
        "winuxsh:plugin@0.1.0",
        PROCESS_PLUGIN_PROTOCOL,
        WASM_PLUGIN_PROTOCOL,
        'min_winuxsh = "{min_winuxsh}"',
        "Patch releases",
        "Minor releases",
        "Major releases",
    ),
}
FRAMEWORK_FILES = (
    "oh-my-winuxsh.winux",
    "lib/hooks.winux",
    "lib/aliases.winux",
    "lib/prompt.winux",
    "lib/git.winux",
    "plugins/README.md",
    "tools/smoke_framework.winux",
)
EXPECTED_FRAMEWORK_PLUGINS = (
    "prompt-core",
    "git",
    "common-aliases",
    "docker",
    "kubectl",
    "npm",
    "path-tools",
    "extract",
    "zoxide",
    "direnv",
    "dotenv",
    "fzf",
    "last-working-dir",
    "thefuck",
    "keybindings",
    "command-not-found",
    "theme-default",
    "theme-dark",
    "theme-light",
    "theme-colorful",
    "theme-minimal",
    "theme-classic",
    "theme-pure",
    "theme-compact",
    "theme-cyberpunk",
    "theme-forest",
    "theme-ocean",
    "theme-agnoster",
    "theme-avit",
    "theme-bira",
    "theme-clean",
    "theme-fishy",
    "theme-lambda",
    "theme-p10-lean",
    "theme-p10-classic",
    "theme-p10-rainbow",
    "theme-p10-pure",
    "theme-robbyrussell",
    "theme-dracula",
    "theme-catppuccin-mocha",
    "theme-gruvbox",
    "theme-spaceship",
    "theme-tokyonight",
    "starship",
)


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def safe_load_toml(path: Path, context: str, errors: list[str]) -> dict | None:
    try:
        return load_toml(path)
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"{context}: invalid TOML in {path}: {exc}")
    except OSError as exc:
        errors.append(f"{context}: failed to read {path}: {exc}")
    return None


def validate_completion_flags(owner: str, flags: object, errors: list[str]) -> None:
    expect(isinstance(flags, list), f"{owner}: flags must be list", errors)
    if not isinstance(flags, list):
        return
    for index, flag in enumerate(flags):
        flag_owner = f"{owner}: flags[{index}]"
        expect(isinstance(flag, dict), f"{flag_owner} must be table", errors)
        if not isinstance(flag, dict):
            continue
        short = flag.get("short")
        long = flag.get("long")
        if short is not None:
            expect(isinstance(short, str) and bool(short.strip()), f"{flag_owner}.short must be non-empty string", errors)
        if long is not None:
            expect(isinstance(long, str) and bool(long.strip()), f"{flag_owner}.long must be non-empty string", errors)
        expect(short is not None or long is not None, f"{flag_owner} must define short or long", errors)
        if "description" in flag:
            expect(isinstance(flag.get("description"), str), f"{flag_owner}.description must be string", errors)
        if "takes_value" in flag:
            expect(isinstance(flag.get("takes_value"), bool), f"{flag_owner}.takes_value must be bool", errors)
        if "values" in flag:
            values = flag.get("values")
            expect(isinstance(values, list), f"{flag_owner}.values must be list", errors)
            if isinstance(values, list):
                for value in values:
                    expect(isinstance(value, str) and bool(value.strip()), f"{flag_owner}.values entries must be non-empty strings", errors)
        if "values_from" in flag:
            expect(flag.get("values_from") == "path", f"{flag_owner}.values_from must be \"path\"", errors)


def validate_completion_asset(
    pack_name: str,
    completion_name: str,
    completions_dir: Path,
    errors: list[str],
) -> None:
    completion_path = completions_dir / f"{completion_name}.toml"
    expect(completion_path.exists(), f"{pack_name}: missing completion asset {completion_path}", errors)
    if not completion_path.exists():
        return
    completion_asset = safe_load_toml(completion_path, f"{pack_name}: completion {completion_name}", errors)
    if completion_asset is None:
        return
    expect(
        completion_asset.get("command") == completion_name,
        f"{pack_name}: completion asset {completion_path} must declare command = {completion_name!r}",
        errors,
    )
    if "description" in completion_asset:
        expect(isinstance(completion_asset.get("description"), str), f"{pack_name}: completion {completion_name}.description must be string", errors)
    if "flags" in completion_asset:
        validate_completion_flags(f"{pack_name}: completion {completion_name}", completion_asset.get("flags"), errors)
    if "subcommands" in completion_asset:
        subcommands = completion_asset.get("subcommands")
        expect(isinstance(subcommands, list), f"{pack_name}: completion {completion_name}.subcommands must be list", errors)
        if isinstance(subcommands, list):
            for index, subcommand in enumerate(subcommands):
                sub_owner = f"{pack_name}: completion {completion_name}: subcommands[{index}]"
                expect(isinstance(subcommand, dict), f"{sub_owner} must be table", errors)
                if not isinstance(subcommand, dict):
                    continue
                name = subcommand.get("name")
                expect(isinstance(name, str) and bool(name.strip()), f"{sub_owner}.name must be non-empty string", errors)
                if "description" in subcommand:
                    expect(isinstance(subcommand.get("description"), str), f"{sub_owner}.description must be string", errors)
                if "flags" in subcommand:
                    validate_completion_flags(sub_owner, subcommand.get("flags"), errors)

def validate_prompt_assets(pack_name: str, exported_segments: list, prompts_dir: Path, errors: list[str]) -> None:
    segments_path = prompts_dir / "segments.toml"
    expect(segments_path.exists(), f"{pack_name}: missing prompt asset {segments_path}", errors)
    if not segments_path.exists():
        return
    asset = safe_load_toml(segments_path, f"{pack_name}: prompt segments", errors)
    if asset is None:
        return
    segments = asset.get("segments")
    expect(isinstance(segments, dict), f"{pack_name}: prompt asset must contain [segments] tables", errors)
    if isinstance(segments, dict):
        for segment_name in exported_segments:
            expect(isinstance(segment_name, str) and bool(segment_name.strip()), f"{pack_name}: exports.prompt_segments entries must be non-empty strings", errors)
            if isinstance(segment_name, str) and segment_name.strip():
                expect(segment_name in segments, f"{pack_name}: missing prompt segment asset {segment_name!r}", errors)
        for segment_name, segment in segments.items():
            owner = f"{pack_name}: prompt segment {segment_name}"
            expect(isinstance(segment, dict), f"{owner} must be table", errors)
            if not isinstance(segment, dict):
                continue
            expect(isinstance(segment.get("id"), str) and bool(segment.get("id", "").strip()), f"{owner}.id must be non-empty string", errors)
            if "description" in segment:
                expect(isinstance(segment.get("description"), str), f"{owner}.description must be string", errors)
    presets = asset.get("presets")
    expect(isinstance(presets, dict) and bool(presets), f"{pack_name}: prompt asset must contain non-empty [presets] tables", errors)
    if isinstance(presets, dict):
        for preset_name, preset in presets.items():
            owner = f"{pack_name}: prompt preset {preset_name}"
            expect(isinstance(preset, dict), f"{owner} must be table", errors)
            if not isinstance(preset, dict):
                continue
            for key in ("left", "right"):
                values = preset.get(key)
                expect(isinstance(values, list), f"{owner}.{key} must be list", errors)
                if isinstance(values, list):
                    for value in values:
                        expect(isinstance(value, str) and bool(value.strip()), f"{owner}.{key} entries must be non-empty strings", errors)
                        if isinstance(value, str) and isinstance(segments, dict):
                            expect(value in segments, f"{owner}.{key} references unknown segment {value!r}", errors)
            if "separator" in preset:
                expect(isinstance(preset.get("separator"), str), f"{owner}.separator must be string", errors)
            if "git_prompt_format" in preset:
                expect(isinstance(preset.get("git_prompt_format"), str), f"{owner}.git_prompt_format must be string", errors)


def validate_keybinding_asset(pack_name: str, keybinding_name: str, keybindings_dir: Path, errors: list[str]) -> None:
    keybinding_path = keybindings_dir / f"{keybinding_name}.toml"
    expect(keybinding_path.exists(), f"{pack_name}: missing keybinding asset {keybinding_path}", errors)
    if not keybinding_path.exists():
        return
    asset = safe_load_toml(keybinding_path, f"{pack_name}: keybinding {keybinding_name}", errors)
    if asset is None:
        return
    expect(asset.get("name") == keybinding_name, f"{pack_name}: keybinding asset {keybinding_path} must declare name = {keybinding_name!r}", errors)
    if "summary" in asset:
        expect(isinstance(asset.get("summary"), str), f"{pack_name}: keybinding {keybinding_name}.summary must be string", errors)
    if "keymap" in asset:
        expect(isinstance(asset.get("keymap"), str), f"{pack_name}: keybinding {keybinding_name}.keymap must be string", errors)
    bindings = asset.get("bindings")
    expect(isinstance(bindings, list) and bool(bindings), f"{pack_name}: keybinding {keybinding_name}.bindings must be non-empty list", errors)
    if isinstance(bindings, list):
        for index, binding in enumerate(bindings):
            owner = f"{pack_name}: keybinding {keybinding_name}.bindings[{index}]"
            expect(isinstance(binding, dict), f"{owner} must be table", errors)
            if not isinstance(binding, dict):
                continue
            expect(isinstance(binding.get("key"), str) and bool(binding.get("key", "").strip()), f"{owner}.key must be non-empty string", errors)
            expect(isinstance(binding.get("action"), str) and bool(binding.get("action", "").strip()), f"{owner}.action must be non-empty string", errors)
            if "description" in binding:
                expect(isinstance(binding.get("description"), str), f"{owner}.description must be string", errors)


def normalize_theme_color(value: str) -> str:
    return "".join(ch for ch in value if ch not in "_-" and not ch.isspace()).lower()


def is_theme_color(value: str) -> bool:
    normalized = normalize_theme_color(value)
    if normalized in THEME_COLOR_NAMES:
        return True
    if normalized.isdigit():
        try:
            return 0 <= int(normalized) <= 255
        except ValueError:
            return False
    hex_value = normalized[1:] if normalized.startswith("#") else normalized
    return len(hex_value) == 6 and all(ch in "0123456789abcdef" for ch in hex_value)


def validate_theme_asset(pack_name: str, theme_name: str, themes_dir: Path, errors: list[str]) -> None:
    theme_path = themes_dir / f"{theme_name}.toml"
    expect(theme_path.exists(), f"{pack_name}: missing theme asset {theme_path}", errors)
    if not theme_path.exists():
        return
    asset = safe_load_toml(theme_path, f"{pack_name}: theme {theme_name}", errors)
    if asset is None:
        return
    expect(bool(asset), f"{pack_name}: theme asset {theme_path} must define at least one style table", errors)
    for style_name, style in asset.items():
        owner = f"{pack_name}: theme {theme_name}.{style_name}"
        expect(style_name in THEME_STYLE_KEYS, f"{owner} is not a supported theme style", errors)
        expect(isinstance(style, dict), f"{owner} must be table", errors)
        if not isinstance(style, dict):
            continue
        for key in style.keys():
            expect(key in {"fg", "bg", "bold", "italic", "underline", "dimmed"}, f"{owner}.{key} is not supported", errors)
        for color_key in ("fg", "bg"):
            if color_key in style:
                color = style.get(color_key)
                expect(isinstance(color, str) and bool(color.strip()), f"{owner}.{color_key} must be non-empty string", errors)
                if isinstance(color, str) and color.strip():
                    expect(is_theme_color(color), f"{owner}.{color_key} uses unknown color {color!r}", errors)
        for bool_key in ("bold", "italic", "underline", "dimmed"):
            if bool_key in style:
                expect(isinstance(style.get(bool_key), bool), f"{owner}.{bool_key} must be bool", errors)


def validate_semver(owner: str, value: object, errors: list[str]) -> None:
    expect(isinstance(value, str) and bool(value.strip()), f"{owner} must be non-empty string", errors)
    if not isinstance(value, str):
        return
    core = value.split("-", 1)[0].split("+", 1)[0]
    parts = core.split(".")
    expect(len(parts) == 3 and all(part.isdigit() for part in parts), f"{owner} must be semver major.minor.patch", errors)


def valid_manifest_token(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\n" not in value and "\r" not in value


def validate_provider_exports(pack_name: str, manifest: dict, exports: dict, errors: list[str]) -> None:
    if "providers" not in exports:
        return
    providers = exports.get("providers")
    expect(isinstance(providers, list), f"{pack_name}: exports.providers must be list", errors)
    if not isinstance(providers, list):
        return

    seen: set[str] = set()
    for index, provider in enumerate(providers):
        expect(valid_manifest_token(provider), f"{pack_name}: exports.providers[{index}] must be a non-empty single-line string", errors)
        if not valid_manifest_token(provider):
            continue
        if provider in seen:
            expect(False, f"{pack_name}: exports.providers repeats {provider!r}", errors)
        seen.add(provider)
        expect(provider in KNOWN_PROVIDER_EXPORTS, f"{pack_name}: exports.providers contains unknown provider {provider!r}", errors)

    if not providers:
        return
    kind = manifest.get("kind")
    expect(
        kind != "wasm",
        f"{pack_name}: wasm packs must not export providers until a WASM provider ABI is implemented",
        errors,
    )
    if "command-not-found" in providers:
        if kind == "builtin":
            expect(pack_name == "command-not-found", f"{pack_name}: provider 'command-not-found' is reserved for the command-not-found pack", errors)
        else:
            expect(kind == "process", f"{pack_name}: provider 'command-not-found' requires kind = 'builtin' or kind = 'process'", errors)
        permissions = manifest.get("permissions")
        if isinstance(permissions, list):
            expect("command:diagnose" in permissions, f"{pack_name}: provider 'command-not-found' requires command:diagnose", errors)


def validate_wasm_artifact(pack_name: str, module: str, expected_sha256: str, errors: list[str]) -> None:
    module_path = ROOT / module
    expect(module_path.exists(), f"{pack_name}: missing wasm module {module_path}", errors)
    if not module_path.exists():
        return
    data = module_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    expect(digest.lower() == expected_sha256.lower(), f"{pack_name}: wasm module checksum mismatch for {module}: expected {expected_sha256}, found {digest}", errors)
    expect(data.startswith(b"\0asm\x01\0\0\0"), f"{pack_name}: wasm module {module} must be a valid WASM binary", errors)


def validate_process_manifest(pack_name: str, manifest: dict, exports: dict, errors: list[str]) -> None:
    kind = manifest.get("kind")
    process = manifest.get("process")
    if kind != "process":
        expect(process is None, f"{pack_name}: [process] is only valid for kind = \"process\"", errors)
        return

    expect(manifest.get("default") is False, f"{pack_name}: process packs must be explicit opt-in with default = false", errors)
    expect(isinstance(process, dict), f"{pack_name}: process pack must include [process]", errors)
    if not isinstance(process, dict):
        return

    expect(process.get("protocol") == PROCESS_PLUGIN_PROTOCOL, f"{pack_name}: process.protocol must be {PROCESS_PLUGIN_PROTOCOL!r}", errors)
    command = process.get("command")
    expect(valid_manifest_token(command), f"{pack_name}: process.command must be a non-empty single-line string", errors)
    args = process.get("args", [])
    expect(isinstance(args, list), f"{pack_name}: process.args must be list", errors)
    if isinstance(args, list):
        for index, arg in enumerate(args):
            expect(valid_manifest_token(arg), f"{pack_name}: process.args[{index}] must be a non-empty single-line string", errors)
    timeout = process.get("timeout_millis")
    expect(
        isinstance(timeout, int) and not isinstance(timeout, bool) and 0 < timeout <= PROCESS_PLUGIN_MAX_TIMEOUT_MILLIS,
        f"{pack_name}: process.timeout_millis must be between 1 and {PROCESS_PLUGIN_MAX_TIMEOUT_MILLIS}",
        errors,
    )
    expect(bool(exports.get("commands")) or bool(exports.get("hooks")), f"{pack_name}: process packs must export at least one command or hook", errors)

    permissions = manifest.get("permissions")
    if valid_manifest_token(command) and isinstance(permissions, list):
        expect(f"process:run:{command}" in permissions, f"{pack_name}: permissions must include process:run:{command}", errors)
    required_binaries = manifest.get("required_binaries")
    expect(isinstance(required_binaries, list), f"{pack_name}: process packs must declare required_binaries", errors)
    if valid_manifest_token(command) and isinstance(required_binaries, list):
        expect(command in required_binaries, f"{pack_name}: required_binaries must include {command!r}", errors)


def validate_source_manifest(pack_name: str, manifest: dict, errors: list[str]) -> None:
    kind = manifest.get("kind")
    source = manifest.get("source")
    if kind != "source":
        expect(source is None, f"{pack_name}: [source] is only valid for kind = \"source\"", errors)
        return

    expect(isinstance(source, dict), f"{pack_name}: source pack must include [source]", errors)
    if not isinstance(source, dict):
        return
    entry = source.get("entry")
    expect(valid_manifest_token(entry), f"{pack_name}: source.entry must be a non-empty single-line string", errors)
    if valid_manifest_token(entry):
        entry_path = Path(str(entry))
        expect(str(entry).endswith(".winux"), f"{pack_name}: source.entry must point to a .winux script", errors)
        expect(not entry_path.is_absolute() and ".." not in entry_path.parts, f"{pack_name}: source.entry must be relative inside the bundle", errors)
        expect((ROOT / entry_path).is_file(), f"{pack_name}: missing source entry {ROOT / entry_path}", errors)
    permissions = manifest.get("permissions")
    if isinstance(permissions, list):
        expect("shell:source" in permissions, f"{pack_name}: source packs must declare shell:source", errors)
    exports = manifest.get("exports")
    if isinstance(exports, dict):
        hooks = exports.get("hooks", [])
        if isinstance(hooks, list):
            for index, hook in enumerate(hooks):
                expect(valid_manifest_token(hook), f"{pack_name}: exports.hooks[{index}] must be a non-empty single-line string", errors)
                if valid_manifest_token(hook):
                    expect(hook in SOURCE_PLUGIN_HOOKS, f"{pack_name}: source hook {hook!r} is not supported", errors)


def validate_wasm_manifest(pack_name: str, manifest: dict, exports: dict, errors: list[str]) -> None:
    kind = manifest.get("kind")
    wasm = manifest.get("wasm")
    if kind != "wasm":
        expect(wasm is None, f"{pack_name}: [wasm] is only valid for kind = \"wasm\"", errors)
        return

    expect(manifest.get("default") is False, f"{pack_name}: wasm packs must be explicit opt-in with default = false", errors)
    expect(isinstance(wasm, dict), f"{pack_name}: wasm pack must include [wasm]", errors)
    if not isinstance(wasm, dict):
        return

    expect(wasm.get("protocol") == WASM_PLUGIN_PROTOCOL, f"{pack_name}: wasm.protocol must be {WASM_PLUGIN_PROTOCOL!r}", errors)
    module = wasm.get("module")
    expect(valid_manifest_token(module), f"{pack_name}: wasm.module must be a non-empty single-line string", errors)
    sha256 = wasm.get("sha256")
    expect(valid_manifest_token(sha256), f"{pack_name}: wasm.sha256 must be a non-empty single-line string", errors)
    if valid_manifest_token(module):
        module_path = Path(str(module))
        expect(str(module).endswith(".wasm"), f"{pack_name}: wasm.module must point to a .wasm artifact", errors)
        expect(not module_path.is_absolute() and ".." not in module_path.parts, f"{pack_name}: wasm.module must be relative inside the bundle", errors)
        if valid_manifest_token(sha256):
            validate_wasm_artifact(pack_name, str(module), str(sha256), errors)
    wit_world = wasm.get("wit_world")
    if wit_world is not None:
        expect(valid_manifest_token(wit_world), f"{pack_name}: wasm.wit_world must be a non-empty single-line string", errors)
    timeout = wasm.get("timeout_millis")
    expect(
        isinstance(timeout, int) and not isinstance(timeout, bool) and 0 < timeout <= WASM_PLUGIN_MAX_TIMEOUT_MILLIS,
        f"{pack_name}: wasm.timeout_millis must be between 1 and {WASM_PLUGIN_MAX_TIMEOUT_MILLIS}",
        errors,
    )
    memory_pages = wasm.get("max_memory_pages")
    expect(
        isinstance(memory_pages, int) and not isinstance(memory_pages, bool) and 0 < memory_pages <= WASM_PLUGIN_MAX_MEMORY_PAGES,
        f"{pack_name}: wasm.max_memory_pages must be between 1 and {WASM_PLUGIN_MAX_MEMORY_PAGES}",
        errors,
    )
    required_binaries = manifest.get("required_binaries")
    expect(required_binaries == [], f"{pack_name}: wasm packs must not declare native required_binaries", errors)
    permissions = manifest.get("permissions")
    if isinstance(permissions, list):
        expect(not any(isinstance(permission, str) and permission.startswith("process:run:") for permission in permissions), f"{pack_name}: wasm packs must not request native process permissions", errors)
    expect(not exports.get("aliases") and not exports.get("hooks") and not exports.get("keybindings") and not exports.get("themes"), f"{pack_name}: wasm packs may only export commands, completions, or prompt_segments in phase 8", errors)
    expect(bool(exports.get("commands")) or bool(exports.get("completions")) or bool(exports.get("prompt_segments")), f"{pack_name}: wasm packs must export at least one command, completion, or prompt_segment", errors)


def validate_framework_export_list(plugin_name: str, exports: dict, key: str, errors: list[str]) -> list[str]:
    values = exports.get(key, [])
    expect(isinstance(values, list), f"framework plugin {plugin_name}: exports.{key} must be list", errors)
    if not isinstance(values, list):
        return []
    for index, value in enumerate(values):
        expect(valid_manifest_token(value), f"framework plugin {plugin_name}: exports.{key}[{index}] must be a non-empty single-line string", errors)
    return [str(value) for value in values if valid_manifest_token(value)]


def validate_framework_plugin_manifest(
    plugin_name: str,
    plugin_dir: Path,
    asset_dirs: dict[str, Path],
    errors: list[str],
) -> None:
    manifest_path = plugin_dir / "plugin.toml"
    expect(manifest_path.exists(), f"framework plugin {plugin_name}: missing plugin.toml", errors)
    if not manifest_path.exists():
        return

    manifest = safe_load_toml(manifest_path, f"framework plugin {plugin_name}", errors)
    if manifest is None:
        return

    expect(manifest.get("name") == plugin_name, f"framework plugin {plugin_name}: name mismatch", errors)
    validate_semver(f"framework plugin {plugin_name}: version", manifest.get("version"), errors)
    kind = manifest.get("kind")
    expect(kind in FRAMEWORK_PLUGIN_KINDS, f"framework plugin {plugin_name}: kind must be one of {sorted(FRAMEWORK_PLUGIN_KINDS)}", errors)

    entry = manifest.get("entry")
    expect(valid_manifest_token(entry), f"framework plugin {plugin_name}: entry must be a non-empty single-line string", errors)
    if valid_manifest_token(entry):
        entry_path = Path(str(entry))
        expect(str(entry).endswith(".winux"), f"framework plugin {plugin_name}: entry must point to a .winux script", errors)
        expect(not entry_path.is_absolute() and ".." not in entry_path.parts, f"framework plugin {plugin_name}: entry must be relative inside the plugin directory", errors)
        expect(str(entry) == f"{plugin_name}.plugin.winux", f"framework plugin {plugin_name}: entry must follow <name>.plugin.winux", errors)
        expect((plugin_dir / entry_path).is_file(), f"framework plugin {plugin_name}: missing entry {plugin_dir / entry_path}", errors)

    summary = manifest.get("summary")
    expect(isinstance(summary, str) and bool(summary.strip()), f"framework plugin {plugin_name}: summary must be non-empty string", errors)
    permissions = manifest.get("permissions")
    expect(isinstance(permissions, list), f"framework plugin {plugin_name}: permissions must be list", errors)
    if kind == "source" and isinstance(permissions, list):
        expect("shell:source" in permissions, f"framework plugin {plugin_name}: source plugins must declare shell:source", errors)
    required_binaries = manifest.get("required_binaries")
    expect(isinstance(required_binaries, list), f"framework plugin {plugin_name}: required_binaries must be list", errors)

    exports = manifest.get("exports")
    expect(isinstance(exports, dict), f"framework plugin {plugin_name}: missing [exports]", errors)
    if not isinstance(exports, dict):
        return

    allowed_export_keys = EXPORT_KEYS | {"functions", "host_bridge"}
    for key in exports:
        expect(key in allowed_export_keys, f"framework plugin {plugin_name}: exports.{key} is not supported", errors)

    if "aliases" in exports:
        expect(isinstance(exports.get("aliases"), bool), f"framework plugin {plugin_name}: exports.aliases must be bool", errors)
    if "host_bridge" in exports:
        expect(valid_manifest_token(exports.get("host_bridge")), f"framework plugin {plugin_name}: exports.host_bridge must be a non-empty single-line string", errors)
    if kind == "bridge":
        expect(valid_manifest_token(exports.get("host_bridge")), f"framework plugin {plugin_name}: bridge plugins must declare exports.host_bridge", errors)

    hooks = validate_framework_export_list(plugin_name, exports, "hooks", errors)
    for hook in hooks:
        expect(hook in SOURCE_PLUGIN_HOOKS, f"framework plugin {plugin_name}: source hook {hook!r} is not supported", errors)

    for key in ("commands", "completions", "functions", "keybindings", "prompt_segments", "providers", "themes"):
        validate_framework_export_list(plugin_name, exports, key, errors)

    if exports.get("aliases"):
        alias_path = asset_dirs["aliases"] / f"{plugin_name}.toml"
        expect(alias_path.exists(), f"framework plugin {plugin_name}: missing aliases asset {alias_path}", errors)
    for completion_name in validate_framework_export_list(plugin_name, exports, "completions", errors):
        validate_completion_asset(plugin_name, completion_name, asset_dirs["completions"], errors)
    prompt_segments = validate_framework_export_list(plugin_name, exports, "prompt_segments", errors)
    if prompt_segments:
        validate_prompt_assets(plugin_name, prompt_segments, asset_dirs["prompts"], errors)
    for keybinding_name in validate_framework_export_list(plugin_name, exports, "keybindings", errors):
        validate_keybinding_asset(plugin_name, keybinding_name, asset_dirs["keybindings"], errors)
    for theme_name in validate_framework_export_list(plugin_name, exports, "themes", errors):
        validate_theme_asset(plugin_name, theme_name, asset_dirs["themes"], errors)
    for provider in validate_framework_export_list(plugin_name, exports, "providers", errors):
        expect(provider in KNOWN_PROVIDER_EXPORTS, f"framework plugin {plugin_name}: unknown provider {provider!r}", errors)


def validate_ci_surface(errors: list[str]) -> None:
    workflow = ROOT / ".github" / "workflows" / "bundle.yml"
    expect(workflow.exists(), f"missing bundle CI workflow: {workflow}", errors)
    if not workflow.exists():
        return
    text = workflow.read_text(encoding="utf-8")
    required_fragments = (
        "python -m py_compile tools/validate_bundle.py tools/package_bundle.py",
        "python tools/validate_bundle.py",
        "python tools/package_bundle.py --check",
        "actions/setup-python@v5",
    )
    for fragment in required_fragments:
        expect(fragment in text, f"bundle CI workflow missing {fragment!r}", errors)


def validate_framework_surface(asset_dirs: dict[str, Path], errors: list[str]) -> None:
    for relative in FRAMEWORK_FILES:
        path = ROOT / relative
        expect(path.exists(), f"missing framework file: {path}", errors)
        if path.exists():
            expect(path.stat().st_size > 0, f"framework file must not be empty: {path}", errors)

    plugins_dir = ROOT / "plugins"
    expect(plugins_dir.is_dir(), f"missing framework plugins directory: {plugins_dir}", errors)
    if not plugins_dir.is_dir():
        return

    plugin_dirs = sorted(path.name for path in plugins_dir.iterdir() if path.is_dir())
    expect(
        plugin_dirs == sorted(EXPECTED_FRAMEWORK_PLUGINS),
        f"framework plugin inventory drift: expected={sorted(EXPECTED_FRAMEWORK_PLUGINS)} dirs={plugin_dirs}",
        errors,
    )
    for plugin_name in plugin_dirs:
        validate_framework_plugin_manifest(plugin_name, plugins_dir / plugin_name, asset_dirs, errors)


def validate_authoring_surface(errors: list[str]) -> None:
    authoring_doc = ROOT / "docs" / "authoring.md"
    expect(authoring_doc.exists(), f"missing authoring guide: {authoring_doc}", errors)

    templates_dir = ROOT / "templates"
    expect(templates_dir.is_dir(), f"missing authoring templates directory: {templates_dir}", errors)
    if not templates_dir.is_dir():
        return

    readme = templates_dir / "README.md"
    expect(readme.exists(), f"missing template README: {readme}", errors)

    for template_name, expected_kind in AUTHORING_TEMPLATE_KINDS.items():
        template_path = templates_dir / template_name / "plugin.toml"
        expect(template_path.exists(), f"missing {template_name} authoring template: {template_path}", errors)
        if not template_path.exists():
            continue
        manifest = safe_load_toml(template_path, f"template {template_name}", errors)
        if manifest is None:
            continue
        expect(manifest.get("kind") == expected_kind, f"template {template_name}: kind must be {expected_kind!r}", errors)
        expect(manifest.get("default") is False, f"template {template_name}: default must be false", errors)
        expect(isinstance(manifest.get("permissions"), list), f"template {template_name}: permissions must be list", errors)
        expect(isinstance(manifest.get("exports"), dict), f"template {template_name}: missing [exports]", errors)
        if expected_kind == "process":
            expect(isinstance(manifest.get("process"), dict), "template process: missing [process]", errors)
        if expected_kind == "source":
            expect(isinstance(manifest.get("source"), dict), "template source: missing [source]", errors)
        if expected_kind == "wasm":
            expect(isinstance(manifest.get("wasm"), dict), "template wasm: missing [wasm]", errors)


def validate_package_index(bundle: dict, available: list, manifests: dict, errors: list[str]) -> None:
    index_path = ROOT / "index.toml"
    expect(index_path.exists(), f"missing package index: {index_path}", errors)
    if not index_path.exists():
        return
    index = safe_load_toml(index_path, "package index", errors)
    if index is None:
        return
    expect(index.get("schema") == INDEX_SCHEMA, f"index.toml schema must be {INDEX_SCHEMA!r}", errors)
    expect(index.get("bundle") == bundle.get("name"), "index.toml bundle must match bundle.toml name", errors)
    expect(index.get("version") == bundle.get("version"), "index.toml version must match bundle.toml version", errors)
    expect(index.get("bundle_api") == bundle.get("api"), "index.toml bundle_api must match bundle.toml api", errors)
    expect(index.get("min_winuxsh") == bundle.get("min_winuxsh"), "index.toml min_winuxsh must match bundle.toml min_winuxsh", errors)
    release = index.get("release")
    expect(isinstance(release, dict), "index.toml must contain [release]", errors)
    if isinstance(release, dict):
        version = bundle.get("version")
        expected_artifact = f"oh-my-winuxsh-{version}.zip" if isinstance(version, str) else None
        expected_checksum = f"{expected_artifact}.sha256" if expected_artifact else None
        expect(release.get("artifact") == expected_artifact, "index.toml release.artifact must match bundle version", errors)
        expect(release.get("checksum") == expected_checksum, "index.toml release.checksum must match bundle version", errors)
        expect(release.get("checksum_algorithm") == "sha256", "index.toml release.checksum_algorithm must be sha256", errors)
        expect(release.get("checksum_required") is True, "index.toml release.checksum_required must be true", errors)
        expect(release.get("signature") == "unsupported", "index.toml release.signature must be unsupported until signing is implemented", errors)
    index_packs = index.get("packs")
    expect(isinstance(index_packs, list) and bool(index_packs), "index.toml packs must be a non-empty list", errors)
    if not isinstance(index_packs, list):
        return
    index_names = [entry.get("name") for entry in index_packs if isinstance(entry, dict)]
    expect(index_names == available, f"index.toml pack order drift: index={index_names} bundle={available}", errors)
    for entry in index_packs:
        expect(isinstance(entry, dict), "index.toml pack entries must be tables", errors)
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        expect(isinstance(name, str) and bool(name.strip()), "index.toml pack name must be non-empty string", errors)
        manifest = manifests.get(name) if isinstance(name, str) else None
        if manifest is None:
            continue
        for key in ("version", "api", "kind", "category", "summary", "default", "permissions", "required_binaries"):
            expect(entry.get(key) == manifest.get(key), f"index.toml {name}.{key} must match manifest", errors)


def validate_release_documents(bundle: dict, errors: list[str]) -> None:
    version = bundle.get("version")
    min_winuxsh = bundle.get("min_winuxsh")
    for relative, required_fragments in RELEASE_DOCUMENTS.items():
        path = ROOT / relative
        expect(path.exists(), f"missing release document: {path}", errors)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if isinstance(version, str):
            expect(version in text, f"{relative}: must mention bundle version {version!r}", errors)
        for fragment in required_fragments:
            expected = fragment
            if isinstance(version, str):
                expected = expected.replace("{version}", version)
            if isinstance(min_winuxsh, str):
                expected = expected.replace("{min_winuxsh}", min_winuxsh)
            expect(expected in text, f"{relative}: missing release note fragment {expected!r}", errors)


def validate() -> list[str]:
    errors: list[str] = []
    bundle_path = ROOT / "bundle.toml"
    expect(bundle_path.exists(), "missing bundle.toml", errors)
    if not bundle_path.exists():
        return errors

    bundle = load_toml(bundle_path)
    expect(bundle.get("api") == BUNDLE_API_VERSION, f"bundle.toml api must be {BUNDLE_API_VERSION!r}", errors)
    validate_semver("bundle.toml version", bundle.get("version"), errors)
    validate_semver("bundle.toml min_winuxsh", bundle.get("min_winuxsh"), errors)
    validate_release_documents(bundle, errors)
    packs_config = bundle.get("packs", {})
    layout = bundle.get("layout", {})

    available = as_list(packs_config.get("available"))
    default = as_list(packs_config.get("default"))
    expect(bool(available), "bundle.toml [packs].available must not be empty", errors)
    expect(
        set(default).issubset(set(available)),
        "bundle.toml [packs].default must be a subset of available packs",
        errors,
    )

    packs_dir = ROOT / str(layout.get("packs_dir", "packs"))
    expect(packs_dir.is_dir(), f"missing packs directory: {packs_dir}", errors)
    if not packs_dir.is_dir():
        return errors

    pack_dirs = sorted(path.name for path in packs_dir.iterdir() if path.is_dir())
    expect(
        sorted(available) == pack_dirs,
        f"pack inventory drift: bundle={sorted(available)} dirs={pack_dirs}",
        errors,
    )

    asset_dirs = {
        "aliases": ROOT / str(layout.get("aliases_dir", "aliases")),
        "completions": ROOT / str(layout.get("completions_dir", "completions")),
        "prompts": ROOT / str(layout.get("prompts_dir", "prompts")),
        "keybindings": ROOT / str(layout.get("keybindings_dir", "keybindings")),
        "themes": ROOT / str(layout.get("themes_dir", "themes")),
    }
    for key, path in asset_dirs.items():
        expect(path.is_dir(), f"missing {key} asset directory: {path}", errors)

    validate_authoring_surface(errors)
    validate_ci_surface(errors)
    validate_framework_surface(asset_dirs, errors)

    manifests = {}
    for pack_name in available:
        manifest_path = packs_dir / pack_name / "plugin.toml"
        expect(manifest_path.exists(), f"missing manifest for pack: {pack_name}", errors)
        if not manifest_path.exists():
            continue

        manifest = load_toml(manifest_path)
        manifests[pack_name] = manifest
        expect(manifest.get("name") == pack_name, f"{pack_name}: manifest name mismatch", errors)
        expect(manifest.get("kind") in KNOWN_KINDS, f"{pack_name}: unknown kind", errors)
        expect(
            manifest.get("category") in KNOWN_CATEGORIES,
            f"{pack_name}: unknown category",
            errors,
        )
        expect(
            isinstance(manifest.get("default"), bool),
            f"{pack_name}: default must be bool",
            errors,
        )
        expect(isinstance(manifest.get("permissions"), list), f"{pack_name}: permissions must be list", errors)
        required_binaries = manifest.get("required_binaries")
        if required_binaries is not None:
            expect(isinstance(required_binaries, list), f"{pack_name}: required_binaries must be list", errors)

        exports = manifest.get("exports")
        expect(isinstance(exports, dict), f"{pack_name}: missing [exports]", errors)
        if not isinstance(exports, dict):
            continue

        expect(
            REQUIRED_EXPORT_KEYS.issubset(exports.keys()),
            f"{pack_name}: [exports] missing keys {sorted(REQUIRED_EXPORT_KEYS - set(exports.keys()))}",
            errors,
        )
        expect(isinstance(exports.get("aliases"), bool), f"{pack_name}: exports.aliases must be bool", errors)
        for key in REQUIRED_EXPORT_KEYS - {"aliases"}:
            expect(isinstance(exports.get(key), list), f"{pack_name}: exports.{key} must be list", errors)
        if "keybindings" in exports:
            expect(isinstance(exports.get("keybindings"), list), f"{pack_name}: exports.keybindings must be list", errors)
        if "providers" in exports:
            expect(isinstance(exports.get("providers"), list), f"{pack_name}: exports.providers must be list", errors)
        if pack_name == "keybindings":
            expect(bool(exports.get("keybindings")), "keybindings: exports.keybindings must not be empty", errors)
        validate_provider_exports(pack_name, manifest, exports, errors)
        validate_source_manifest(pack_name, manifest, errors)
        validate_process_manifest(pack_name, manifest, exports, errors)
        validate_wasm_manifest(pack_name, manifest, exports, errors)

        if exports.get("aliases"):
            expect(asset_dirs["aliases"].is_dir(), f"{pack_name}: aliases export without aliases dir", errors)
            alias_path = asset_dirs["aliases"] / f"{pack_name}.toml"
            expect(alias_path.exists(), f"{pack_name}: missing aliases asset {alias_path}", errors)
            if alias_path.exists():
                alias_asset = load_toml(alias_path)
                aliases = alias_asset.get("aliases")
                expect(isinstance(aliases, dict), f"{pack_name}: aliases asset must contain [aliases]", errors)
                if isinstance(aliases, dict):
                    expect(bool(aliases), f"{pack_name}: aliases asset must not be empty", errors)
                    for alias_name, alias_value in aliases.items():
                        expect(isinstance(alias_name, str) and bool(alias_name.strip()), f"{pack_name}: alias name must be non-empty", errors)
                        expect(isinstance(alias_value, str) and bool(alias_value.strip()), f"{pack_name}: alias {alias_name!r} must have a non-empty value", errors)
        if exports.get("completions"):
            expect(asset_dirs["completions"].is_dir(), f"{pack_name}: completions export without completions dir", errors)
            for completion_name in exports.get("completions", []):
                expect(isinstance(completion_name, str) and bool(completion_name.strip()), f"{pack_name}: exports.completions entries must be non-empty strings", errors)
                if isinstance(completion_name, str) and completion_name.strip():
                    validate_completion_asset(pack_name, completion_name, asset_dirs["completions"], errors)
        if exports.get("prompt_segments"):
            expect(asset_dirs["prompts"].is_dir(), f"{pack_name}: prompt export without prompts dir", errors)
            validate_prompt_assets(pack_name, exports.get("prompt_segments", []), asset_dirs["prompts"], errors)
        if exports.get("keybindings"):
            expect(asset_dirs["keybindings"].is_dir(), f"{pack_name}: keybindings export without keybindings dir", errors)
            for keybinding_name in exports.get("keybindings", []):
                expect(isinstance(keybinding_name, str) and bool(keybinding_name.strip()), f"{pack_name}: exports.keybindings entries must be non-empty strings", errors)
                if isinstance(keybinding_name, str) and keybinding_name.strip():
                    validate_keybinding_asset(pack_name, keybinding_name, asset_dirs["keybindings"], errors)
        if exports.get("themes"):
            expect(asset_dirs["themes"].is_dir(), f"{pack_name}: themes export without themes dir", errors)
            for theme_name in exports.get("themes", []):
                expect(isinstance(theme_name, str) and bool(theme_name.strip()), f"{pack_name}: exports.themes entries must be non-empty strings", errors)
                if isinstance(theme_name, str) and theme_name.strip():
                    validate_theme_asset(pack_name, theme_name, asset_dirs["themes"], errors)

    validate_package_index(bundle, available, manifests, errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    pack_count = len(load_toml(ROOT / "bundle.toml")["packs"]["available"])
    print(f"bundle validation ok: {pack_count} packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
