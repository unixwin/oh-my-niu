# Oh My Niu

Official Oh My-style plugin framework and bundled plugin distribution for
Niubash.

This repository is not a zsh runtime and does not provide zsh plugin
compatibility. It should, however, follow the useful shape of Oh My Zsh, fish
plugin managers, and PowerShell prompt frameworks: plugins are directories,
themes are plugins, and the shell core provides loader primitives instead of
owning high-level plugin behavior.

## Status

The active direction is framework-first. See [docs/design.md](docs/design.md).
The earlier manifest-first bundle design is retired in
[docs/design-manifest-first-retired.md](docs/design-manifest-first-retired.md).

- Niubash owns shell primitives, plugin loading, lifecycle dispatch, permission
  review, update/rollback, and fast native helpers.
- `oh-my-niu` owns framework libraries, plugin directories, themes, default
  composition, and the official bundled distribution.
- Bundled plugins may ship with Niubash, but bundled does not mean built in.
- `plugin.toml` is metadata for packaging, review, and updates. It should not be
  the only way to express local trusted shell behavior.

## Framework Model

The target interactive setup is directory-first and familiar:

```sh
NIU_PLUGINS=(prompt-core git docker zoxide)
NIU_THEME=minimal
source "$NIUBASH/oh-my-niu.winux"
```

Starship can also own the prompt through its normal Bash init path. In that
mode, load the `starship` plugin instead of `prompt-core`/`theme-*` prompt
plugins so Starship controls `PROMPT_COMMAND`, `PS1`, `PS2`, and `PS0`:

```sh
NIU_PLUGINS=(git starship docker zoxide)
NIU_THEME=
source "$NIUBASH/oh-my-niu.winux"
```

Managed TOML should map onto the same plugin system:

```toml
[plugins]
enabled = true
bundles = ["oh-my-niu"]
load = ["prompt-core", "git", "docker", "zoxide"]

[theme]
current_theme = "minimal"

[plugins.git]
enabled = true
permissions = ["shell:source", "cwd:read", "process:run:git"]
```

The bundle is still expected to ship with Niubash releases so users have an
offline baseline, then update independently:

```sh
niubash plugin update oh-my-niu --from dist\oh-my-niu-1.0.1.zip --checksum-file dist\oh-my-niu-1.0.1.zip.sha256
niubash plugin rollback oh-my-niu
```

User shell code and normal plugin/theme selection belong in `~/.niubashrc`.
`~/.winshrc` is only a legacy fallback when `~/.niubashrc` is absent:

```sh
alias ll='ls -la'
export EDITOR=vim
```

## Repository Layout

```text
oh-my-niu/
  oh-my-niu.winux
  bundle.toml
  index.toml
  lib/
    aliases.winux
    git.winux
    prompt.winux
    hooks.winux
  plugins/
    prompt-core/
      prompt-core.plugin.winux
      plugin.toml
    git/
      git.plugin.winux
      plugin.toml
      functions/
      completions/
    theme-minimal/
      theme-minimal.plugin.winux
      plugin.toml
    theme-default/
    theme-dark/
    theme-light/
    theme-colorful/
    theme-classic/
    theme-pure/
    theme-compact/
    theme-cyberpunk/
    theme-forest/
    theme-ocean/
    theme-agnoster/
    theme-avit/
    theme-bira/
    theme-clean/
    theme-fishy/
    theme-lambda/
    theme-p10-lean/
    theme-p10-classic/
    theme-p10-rainbow/
    theme-p10-pure/
    theme-robbyrussell/
    theme-dracula/
    theme-catppuccin-mocha/
    theme-gruvbox/
    theme-spaceship/
    theme-tokyonight/
    common-aliases/
    path-tools/
    extract/
    docker/
    kubectl/
    npm/
    zoxide/
    direnv/
    dotenv/
    fzf/
    last-working-dir/
    thefuck/
    keybindings/
    command-not-found/
  packs/
    ...
    # Transitional manifest-first compatibility surface.
  aliases/
    common-aliases.toml
    git.toml
    docker.toml
    kubectl.toml
    npm.toml
    README.md
  completions/
    git.toml
    docker.toml
    kubectl.toml
    npm.toml
    README.md
  prompts/
    segments.toml
    README.md
  keybindings/
    common.toml
    emacs.toml
    vi.toml
    README.md
  themes/
    default.toml
    dark.toml
    light.toml
    colorful.toml
    cyberpunk.toml
    classic.toml
    compact.toml
    forest.toml
    minimal.toml
    ocean.toml
    p10-lean.toml
    p10-classic.toml
    p10-rainbow.toml
    p10-pure.toml
    pure.toml
    robbyrussell.toml
    README.md
  docs/
    authoring.md
    design.md
    framework-smoke-notes.md
    design-manifest-first-retired.md
    migration.md
    roadmap.md
  templates/
    builtin/plugin.toml
    source/plugin.toml
    source/init.winux
    process/plugin.toml
    wasm/plugin.toml
```

## First-Party Plugins

These are the active Oh My-style plugin directories. Themes are regular
plugins, and `prompt-core` owns the common prompt API.

| Plugin | Purpose | Default |
| --- | --- | --- |
| `prompt-core` | Prompt API, segment registry, and Git status prompt service | On |
| `theme-default` | Official default theme plugin | Off |
| `theme-dark` | Official dark theme plugin | Off |
| `theme-light` | Official light theme plugin | Off |
| `theme-colorful` | Official colorful theme plugin | Off |
| `theme-minimal` | Minimal official prompt theme plugin | On |
| `theme-classic` | Classic two-line official prompt theme plugin | Off |
| `theme-pure` | Pure-inspired two-line official prompt theme plugin | Off |
| `theme-compact` | Compact single-line official prompt theme plugin | Off |
| `theme-cyberpunk` | Cyberpunk official prompt theme plugin | Off |
| `theme-forest` | Forest official prompt theme plugin | Off |
| `theme-ocean` | Ocean official prompt theme plugin | Off |
| `theme-agnoster` | Agnoster-style Nerd Font prompt theme plugin | Off |
| `theme-avit` | Avit-style Oh My Zsh prompt theme plugin | Off |
| `theme-bira` | Bira-style two-line Oh My Zsh prompt theme plugin | Off |
| `theme-clean` | Clean Oh My Zsh prompt theme plugin | Off |
| `theme-fishy` | Fish-like prompt theme plugin inspired by Oh My Zsh and fish-shell | Off |
| `theme-lambda` | Lambda-style minimal Oh My Zsh prompt theme plugin | Off |
| `theme-p10-lean` | Powerlevel-style lean prompt theme plugin | Off |
| `theme-p10-classic` | Powerlevel-style classic prompt theme plugin | Off |
| `theme-p10-rainbow` | Powerlevel-style rainbow prompt theme plugin | Off |
| `theme-p10-pure` | Powerlevel-style pure prompt theme plugin | Off |
| `theme-robbyrussell` | Robby Russell-style prompt theme plugin | Off |
| `theme-dracula` | Dracula Nerd Font prompt theme plugin inspired by Oh My Posh | Off |
| `theme-catppuccin-mocha` | Catppuccin Mocha Nerd Font prompt theme plugin inspired by Oh My Posh | Off |
| `theme-gruvbox` | Gruvbox Nerd Font prompt theme plugin inspired by Oh My Posh | Off |
| `theme-spaceship` | Spaceship-style Nerd Font prompt theme plugin inspired by Oh My Posh | Off |
| `theme-tokyonight` | Tokyo Night Nerd Font prompt theme plugin inspired by Oh My Posh | Off |
| `starship` | Full Starship prompt integration through the Bash prompt contract | Off |
| `git` | Git aliases, completions, and workflow helpers | On |
| `winuxcmd-core` | Static completions for WinuxCmd core command links | On |
| `common-aliases` | Small Oh My-style navigation/listing aliases | Off |
| `docker` | Docker `.winux` helpers, aliases, completion metadata | Off |
| `kubectl` | Kubernetes `.winux` helpers, aliases, completion metadata | Off |
| `npm` | npm `.winux` helpers, aliases, runtime completion shape | Off |
| `path-tools` | PATH inspection and edit helpers inspired by fish ergonomics | Off |
| `extract` | Archive extraction helper for common compressed formats | Off |
| `zoxide` | `.winux` `z`/`zi` helpers plus directory tracking hooks | Off |
| `direnv` | `.winux` lifecycle adapter for `direnv export bash` | Off |
| `dotenv` | `.winux` `.env` loader for current project directory | Off |
| `fzf` | `.winux` directory selector command shims | Off |
| `last-working-dir` | `.winux` last-directory cache and restore hooks | Off |
| `thefuck` | `.winux` correction shim for the previous command | Off |
| `keybindings` | Bridge plugin for official Reedline keybinding assets | On |
| `command-not-found` | Bridge plugin for the missing-command provider identity | Off |

## Transitional Packs

`packs/`, `aliases/`, `completions/`, `prompts/`, `keybindings/`, and
`themes/` remain in the repository because current Niubash releases and release
tools still understand the manifest-first bundle layout. New behavior should
land in `plugins/<name>/` first, then expose metadata through TOML for review,
managed install, update, and rollback.

The old `prompts` and `themes` packs are compatibility assets. They are no
longer the product model for prompt and theme behavior; `prompt-core` and
`theme-*` plugins are.

## Authoring

Public authoring is moving to plugin directories. During the transition,
[docs/authoring.md](docs/authoring.md) still describes the manifest-backed
bundle surface and templates, but new user-facing behavior should start as
plugin-owned code/assets rather than Niubash `builtin` packs.

```sh
python tools/validate_bundle.py
python tools/package_bundle.py --check
niubash plugin review <pack>
niubash plugin search devtools
niubash plugin themes
niubash plugin install git
niubash plugin doctor
```

`plugin.toml` remains useful for package metadata, permissions, exports, and
required binaries before Niubash runs distributed plugin code. It should be a
review/install surface over plugin directories, not the product identity.

## Legacy

The old repository content was a `.winsh` script framework from a previous
WinSH era. It is preserved through the `legacy-pre-niubash-plugin-system`
branch/tag; the active branch describes the official Niubash plugin bundle.

See [docs/migration.md](docs/migration.md).

## Roadmap

The active product direction lives in [docs/design.md](docs/design.md). The old
phase roadmap remains in [docs/roadmap.md](docs/roadmap.md) as manifest-first
history until the framework-first migration plan replaces it.
Release compatibility is tracked in [docs/compatibility.md](docs/compatibility.md),
and bundle changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## Validation And Packaging

```sh
python tools/validate_bundle.py
python tools/package_bundle.py --check
# Windows launcher:
py tools\validate_bundle.py
py tools\package_bundle.py --check
# Runtime smoke with the selected Niubash binary:
niubash tools/smoke_framework.winux .
```

The validator checks release documents, package index drift, release checksum
policy, bundle API and minimum Niubash metadata, old manifest inventory drift,
directory plugin inventory drift, plugin entry scripts, plugin metadata,
exported asset presence, parseable alias packs, parseable completion
definitions, prompt preset segment references, declarative keybinding metadata,
and theme TOML assets. Source manifests must declare `shell:source`, supported
lifecycle hooks, and a bundle-local `.winux` entry. Process manifests must be
explicit opt-in and declare protocol, command, timeout, permissions, and
required binaries. The package script builds
`dist/oh-my-niu-{version}.zip` plus a `.sha256` checksum when run without
`--check`.
WASM manifests must also declare a bundle-local `.wasm` module path and SHA-256;
the validator checks that the artifact exists, matches the digest, and has a
valid WASM binary header. The current Niubash host can execute explicit command
modules that export `niubash_plugin_main() -> i32`, may write stdout/stderr,
may read simple command arguments, read cwd when `cwd:read` is declared, and
read explicitly permitted env values through `env:read:<NAME>` using the Phase
14-17 `niubash:plugin/host` imports; broader WASI and
shell-mutating host APIs remain future work.

Local release smoke test:

```sh
py tools\package_bundle.py
niubash plugin update oh-my-niu --from dist\oh-my-niu-1.0.1.zip --checksum-file dist\oh-my-niu-1.0.1.zip.sha256
niubash plugin bundle status
niubash plugin search workflow
niubash plugin doctor
niubash plugin search workflow
```

## License

MIT unless the Unixwin project chooses a different repository license before the
first bundle release.
## Source Scope

`oh-my-niu.winux` is meant to be sourced from an interactive Niubash rc file.
Sourcing the framework updates the current shell process by registering aliases,
functions, prompt helpers, hooks, and environment variables exported by enabled
plugins.

Sourcing does not persist configuration by itself. Changes to `NIU_PLUGINS`,
`NIU_THEME`, `NIU_CUSTOM`, PATH setup, or other startup policy need to
live in the user's rc file, such as `~/.niubashrc`, or in files sourced from that
rc file. A plugin should only rewrite rc files through an explicit user command,
not as a side effect of normal framework sourcing.

