# Completion Assets

This directory owns first-party static completion definitions that Winuxsh loads
from the active `oh-my-winuxsh` bundle when the matching pack is enabled.

Current bundle-owned definitions:
- `git.toml`
- `docker.toml`
- `kubectl.toml`
- `npm.toml`
- WinuxCmd core command definitions generated from `winuxcmd.exe <command> --help` and exported by `packs/winuxcmd-core/plugin.toml`.

Each file uses the native Winuxsh TOML completion schema:
- top-level `command = "<name>"`;
- optional `[[flags]]` entries with `short`, `long`, `takes_value`, `values`, or
  `values_from = "path"`;
- optional `[[subcommands]]` entries with their own `[[subcommands.flags]]`.

`tools/validate_bundle.py` checks that every manifest entry in
`exports.completions` has a matching parseable `completions/<name>.toml` asset
whose `command` matches the exported completion name.
