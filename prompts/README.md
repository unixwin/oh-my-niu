# Prompt Assets

This directory owns first-party prompt segment metadata and preset layouts that
Niubash can load from the active `oh-my-niu` bundle.

- `segments.toml` maps exported segment names, such as `cwd` and `git`, to
  native Niubash segment IDs.
- `[presets.<name>]` tables define segment order, right-prompt elements,
  separators, and optional git prompt formatting.
- Niubash keeps compiled fallback presets so offline releases still render
  prompts when no bundle is installed.
