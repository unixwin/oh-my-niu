# Changelog

All notable changes to the official oh-my-niu bundle are recorded here.
Release entries describe bundle artifacts, host compatibility, permission
changes, and user-visible asset changes.

## 2.0.0 (unreleased)

- Release artifact: `oh-my-niu-2.0.0.zip` (`api = "niubash:plugin-bundle@0.1.0"`,
  `min_niubash = "1.0.0"`).
- Renamed the bundle from `oh-my-winuxsh` to `oh-my-niu` to match the
  niubash 1.0.0 brand. Installed `~/.oh-my-winuxsh` directories keep
  working: niubash discovers the pre-rename layout as a fallback.
- Bundle/plugin API identifiers move from the `winuxsh:` prefix to
  `niubash:` (`niubash:plugin-bundle@0.1.0`, `niubash:plugin@0.1.0`,
  `niubash:plugin-index@0.1.0`). Manifests may declare either
  `min_niubash` or the legacy `min_winuxsh` field.
- Entry point renamed to `oh-my-niu.winux`; scripts now use the `NIU_*`
  environment prefix (`NIU_PLUGINS`, `NIU_THEME`, `NIU_THEME_PLUGIN`)
  and the `NIUBASH` bundle-root variable.
- New first-party plugins: `command-timer` (per-command duration and exit
  code), `auto-env` (automatic `.venv` activation per directory),
  `dirmarks` (directory bookmarks), `git-fetch-reminder` (upstream
  divergence notices), and `env-sync` (push/pull shell config and the WPM
  package manifest through any rclone remote).
- All first-party pack manifests move to version 2.0.0 to match the
  bundle release.

## 1.0.1 - 2026-08-02

### Changed

- Released first-party `.winux` source packs for Git, Docker, kubectl, npm,
  zoxide, direnv, dotenv, fzf, last-working-dir, and thefuck against the
  Winuxsh source lifecycle host.
- Added the framework entry point, directory-first official plugins,
  `prompt-core`, and theme plugins for minimal, classic, pure, compact,
  cyberpunk, forest, and ocean.
- Kept keybindings and command-not-found as bridge plugins while their low-level
  Reedline/provider call sites remain host-owned.
- Kept old `packs/` manifests as compatibility and package-review metadata over
  the directory plugin surface.
- Added `tools/smoke_framework.winux` for runtime verification with an
  installed Winuxsh binary.
- Updated bundle metadata with `api = "winuxsh:plugin-bundle@0.1.0"` and
  `min_winuxsh = "0.10.0"` so older Winuxsh hosts refuse this RC-first
  source-pack bundle.
- Added deterministic release packaging for `oh-my-winuxsh-1.0.1.zip` and the
  matching `.sha256` checksum file.

### Compatibility

- Requires Winuxsh 0.10.0 or newer for source plugin startup and lifecycle hook
  loading through `.winux` files.
- Keeps process and WASM plugin protocols unchanged; WASM provider/effect APIs
  remain future host work.

### Release Checklist

- Attach `oh-my-winuxsh-1.0.1.zip` and
  `oh-my-winuxsh-1.0.1.zip.sha256` to the GitHub release.
- Include this changelog entry and `docs/compatibility.md` in the release notes.
- Run `python tools/validate_bundle.py` and
  `python tools/package_bundle.py --check` before publishing.
- Run `winuxsh tools/smoke_framework.winux .` before publishing framework
  changes.

## 1.0.0 - 2026-07-31

### Added

- Established the repository as the official Winuxsh plugin bundle rather than
  a legacy `.winsh` script framework.
- Added bundle metadata with `api = "winuxsh:plugin-bundle@0.1.0"` and
  `min_winuxsh = "0.8.3"`.
- Added first-party source packs for Git, Docker, kubectl, npm, zoxide,
  direnv, dotenv, fzf, last-working-dir, and thefuck with bundle-local `.winux`
  startup and lifecycle hook code.
- Added first-party builtin/native packs for command-not-found, prompts, and
  keybindings where host-owned provider/editor/prompt behavior still applies.
- Added bundle-owned aliases, completions, prompt presets, keybinding metadata,
  official theme assets, authoring templates, and public authoring documentation.
- Added deterministic release packaging for `oh-my-winuxsh-1.0.0.zip` and the
  matching `.sha256` checksum file.

### Compatibility

- Requires Winuxsh 0.8.3 or newer for local bundle install, rollback, doctor,
  review, process plugin, and Phase 8 WASM command execution support.
- Uses pack manifest API `winuxsh:plugin@0.1.0`, process plugin protocol
  `winuxsh:process-plugin@0.1.0`, and WASM plugin protocol
  `winuxsh:wasm-plugin@0.1.0`.
- Keeps source, process, and WASM execution visible through manifest
  permissions because they can execute outside pure static asset loading.

### Release Checklist

- Attach `oh-my-winuxsh-1.0.0.zip` and
  `oh-my-winuxsh-1.0.0.zip.sha256` to the GitHub release.
- Include this changelog entry and `docs/compatibility.md` in the release notes.
- Run `python tools/validate_bundle.py` and
  `python tools/package_bundle.py --check` before publishing.
