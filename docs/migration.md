# Legacy Migration

This repository previously contained a `.winsh` script framework for an older
WinSH-era shell. That content does not match the current Niubash architecture.

## Preservation

Do not erase history. Preserve the old state with:

```sh
git tag legacy-pre-niubash-plugin-system
git branch legacy-pre-niubash-plugin-system
```

Then rebuild `main` as the official Niubash plugin bundle.

## What Changed

Old model:

- clone into `~/.oh-my-niu`;
- source `winshrc`;
- source theme and plugin scripts;
- configure plugin arrays in rc.

New model:

- ship the bundle with Niubash releases;
- describe packs with `bundle.toml` and `packs/*/plugin.toml`;
- let users enable packs and themes from `~/.niubashrc`;
- keep `~/.winshrc.toml` for legacy/managed plugin CLI state, permissions,
  bundle versions, migration blocks, and tests;
- keep `~/.winshrc` only as a compatibility fallback;
- support bundle update and rollback through Niubash plugin commands.

## Zsh and Oh My Zsh

This repository is not an Oh My Zsh fork.

Niubash may provide a zsh migration command that detects familiar configuration
intent such as:

```zsh
plugins=(git zoxide)
```

The output should suggest Niubash plugins:

```text
oh-my-niu/git
oh-my-niu/zoxide
```

It should not call those zsh plugins, and it should not execute zsh plugin
source.
