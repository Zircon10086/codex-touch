[English](AGENTS.md) | [简体中文](AGENTS.zh-CN.md)

# codex-touch development conventions

- This project adds touch controls to Codex in Termux under Apache-2.0. Preserve upstream and third-party notices.
- Before editing, read `README.md`, `docs/design.md`, and the relevant source. Update the design when needed.
- Verify the actual Termux-to-Codex input path before choosing an implementation language or component boundary. Prefer existing interfaces and upstream logic.
- Keep dependencies minimal. Do not prebuild plugins, services, or abstractions for features that do not exist yet.
- Keep source changes in `src/` and meaningful behavior tests in `tests/`. Register new checks with `scripts/check.sh` so they are not silently skipped.
- Run `bash scripts/check.sh` after changes and report its scope. Passing basic checks does not establish touch functionality or on-device interaction.
- Record user-visible changes in `CHANGELOG.md`. Follow `docs/development.md` for versions and releases.
- When the user confirms a version update, publish the matching GitHub Release as part of the same delivery unless the user explicitly defers it. Update version/docs, validate, push the intended commit and annotated tag, upload source/checksums, publish, and verify public downloads and CI. Do not stop after pushing source or request separate release permission again.
- Use UTF-8 and LF. Invoke shared-storage shell scripts through `bash`; do not depend on executable permission bits on Android shared storage.
- On the development device, use `termux-run` when Debian needs host Termux tools. Do not mix Android and Debian PATHs.
- Do not change global Git configuration automatically. Pass identity and the repository-specific `safe.directory` as one-command `git -c` options when needed.
- Use synthetic diagnostic data. Do not commit terminal sessions, credentials, or personal information. Respect the parent workspace's phone-operation and privacy requirements.
- Use English for default documentation, code comments, script output, commit messages, and Release notes. Keep Chinese documents in sibling `*.zh-CN.md` files with language links at the top of both versions. Update both languages when behavior or versions change. Preserve multilingual input fixtures needed by tests.
