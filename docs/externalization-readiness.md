# Externalization Readiness
This document classifies official bundle behavior during the framework-first
migration. The active runtime target is `plugins/<name>/`; old `packs/`
manifests remain a compatibility and review surface until Niubash loads
directory plugins directly.

## Current Bundle Facts
- Static bundle assets still cover aliases, completion tables, prompt presets,
  keybinding metadata, and theme style TOML.
- Directory plugins are now the product surface. `plugin.toml` describes
  package/review metadata; `<name>.plugin.winux` owns runtime behavior.
- Source plugins are reviewed bundle-local `.winux` startup and lifecycle
  scripts. They are the Oh My-style path for first-party shell helpers that
  intentionally define aliases, functions, exports, cwd changes, or hook glue
  in the current interactive shell.
- Bridge plugins identify features whose low-level call site is still
  Niubash/Reedline-owned. They are temporary ownership markers, not a final
  runtime kind for third-party behavior.
- WASM packs are command-only today. They can read args, cwd, and explicitly
  allowed env values, but they cannot act as completion, prompt, hook, or
  command-not-found or other providers yet.
- Process packs can wrap native commands, lifecycle hooks, and Niubash
  command-not-found provider binding, but they do not mutate the current shell;
  source plugins are the current shell-effect path.
- Shell-mutating WASM/provider packs still need explicit host APIs before they
  can mutate env/cwd/history outside trusted source code.
- Niubash plugin CLI review surfaces expose derived `execution_model`,
  `externalization_class`, and readiness profile values for these rows. They
  are not bundle manifest fields.
- `exports.providers` is a guarded provider marker. In current Niubash, process
  packs may use it for command-not-found with `command:diagnose`; it is not a
  new runtime kind and does not make command-style WASM act as a provider.

## Pack Matrix
| Feature | Current surface | Classification | Target runtime / execution model | Missing host API or decision | Shell-mutating | Fallback needed |
| --- | --- | --- | --- | --- | --- | --- |
| `prompt-core` | `plugins/prompt-core` | Prompt API source plugin | Prompt segment registry, render entry points, `NIU_PROMPT_GIT` host snapshot backed by a persistent gitstatus helper | Richer host prompt call-in | No direct mutation | Yes |
| `git` | `plugins/git` | Source workflow helper plus declarative assets | `.winux` aliases/functions plus alias/completion assets | Remove core fallback alias injection when plugin disabled | Yes, by trusted source | Minimal |
| `common-aliases` | `plugins/common-aliases` | Source alias helper plus declarative asset | Small Oh My-style aliases owned by the plugin directory | None for current first-party helper scope | Yes, by trusted source | Minimal |
| `docker` | `plugins/docker` | Source helper plus declarative assets | `.winux` helpers plus alias/completion assets | None for current first-party helper scope | Yes, by trusted source | Minimal |
| `kubectl` | `plugins/kubectl` | Source helper plus declarative assets | `.winux` helpers plus alias/completion assets | None for current first-party helper scope | Yes, by trusted source | Minimal |
| `npm` | `plugins/npm` | Source helper plus declarative assets | `.winux` helpers plus assets; dynamic completion can move later | Completion/provider ABI | Yes, by trusted source | Yes |
| `path-tools` | `plugins/path-tools` | Source shell-effect helper | PATH list/prepend/append/remove/dedupe functions | Structured env-effect API only if sandboxed provider is needed | Yes, by trusted source | Minimal |
| `extract` | `plugins/extract` | Source external-tool helper | Archive extraction function with explicit tool checks | Optional command/provider ABI for sandboxed archive helpers | Yes, by trusted source | Minimal |
| `zoxide` | `plugins/zoxide` | Source shell-effect helper | `.winux` `z`/`zi` helpers plus startup/precmd/chpwd tracking | Future sandboxed cwd effect API only if needed | Yes, by trusted source | Minimal |
| `direnv` | `plugins/direnv` | Source shell-effect helper | `.winux` lifecycle adapter around `direnv export bash` | Future structured env-effect API only if sandboxed/runtime provider is needed | Yes, by trusted source | Minimal |
| `dotenv` | `plugins/dotenv` | Source shell-effect helper | `.winux` scoped `.env` loader on startup/precmd/chpwd | Future parser hardening and sandboxed file/env effect API | Yes, by trusted source | Minimal |
| `fzf` | `plugins/fzf` | Source shell-effect helper | `.winux` directory selector functions that `cd` in-session | Interactive provider policy only if moving away from source | Yes, by trusted source | Minimal |
| `last-working-dir` | `plugins/last-working-dir` | Source shell-effect helper | `.winux` startup restore plus chpwd cache write | Future structured cache/cwd effect API only if sandboxed runtime is needed | Yes, by trusted source | Minimal |
| `thefuck` | `plugins/thefuck` | Source external-tool helper | `.winux` function that evaluates reviewed `thefuck` output in-session | Better history context/provider API for richer suggestions | Yes, by trusted source | Minimal |
| `theme-*` | `plugins/theme-*` | Source theme plugins plus style assets | Theme plugin selects layout, symbol, colors, prompt template, and true-colour style data | Richer prompt style/render API | No | Minimal |
| `keybindings` | `plugins/keybindings` | Bridge over Reedline assets | Directory plugin identity; Reedline still applies native actions | Completion of keybinding plugin API or asset-only schema | No | Minimal |
| `command-not-found` | `plugins/command-not-found` | Bridge over host provider | Directory plugin identity; provider can later move to process/WASM provider ABI | Provider entrypoint and migration decision | No | Yes |
| Old `prompts` pack | `packs/prompts` | Transitional compatibility asset | Fold prompt presets into `prompt-core`/theme plugins | Host prompt API and compatibility migration | No | Yes |
| Old `themes` pack | `packs/themes` | Transitional compatibility asset | Superseded by `theme-*` plugins, including migrated `default`/`dark`/`light`/`colorful` and p10-style themes | Keep catalog compatibility until host loads plugin themes directly | No | Minimal |

## Next Bundle Work
1. Wire Niubash managed config to the same directory loader as shell arrays.
2. Stop host fallback injection when an equivalent directory plugin is disabled.
3. Keep reducing legacy `packs/prompts` and `packs/themes` to package-review
   metadata now that `prompt-core` and `theme-*` plugins own prompt behavior.
4. Broaden persistent gitstatus helper coverage around chpwd/git-command
   invalidation, dirty compact coloring, and stale snapshot handling.
5. Use [command-not-found](command-not-found-provider-abi.md) to design the
   first real provider migration after provider input/output, permission review,
   timeout behavior, and bridge-disable rules are stable.
