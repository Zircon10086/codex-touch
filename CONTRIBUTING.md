[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md)

# Contributing

Reproducible reports and focused changes are welcome. codex-touch adapts the Codex TUI through a patch against a pinned upstream revision. Prefer existing upstream events, shortcuts, and business logic. Avoid speculative frameworks and dependencies.

## Reporting a problem

Include the Codex baseline and codex-touch commit, Termux version and distribution channel, Linux userspace, approximate terminal dimensions, reproduction steps, expected behavior, and actual behavior. For touch problems, distinguish tapping, dragging, and scrolling, and mention whether the keyboard is visible. Use synthetic questions or a minimal example; do not upload session transcripts, credentials, or personal information.

## Making a change

1. Read [AGENTS.md](AGENTS.md), the [design](docs/design.md), and the [phone build guide](docs/build.md). Create a branch from `main`.
2. Edit the pinned upstream source while preserving existing behavior, license notices, and confirmation flows. Derive hit targets from actual rendering.
3. Update `src/async-question-touch.patch`, including any new upstream test files. Keep caches, binaries, and local configuration out of the repository.
4. Run `bash scripts/check.sh`. For patch changes, also verify the exact source and run the relevant Rust regressions. For input-routing changes, run the package PTY checks. See [tests](tests/README.md).
5. Update `Unreleased` in `CHANGELOG.md` and the relevant behavior documentation. Describe the problem, change, validation, and unverified scope in the PR.

Use LF line endings. Invoke scripts with `bash` or `python3`; Android shared storage may not preserve executable permissions. An ordinary development commit does not automatically bump the version, create a tag, or publish a Release.

GitHub Actions runs basic checks on pushes and PRs with read-only permissions. It does not compile all of Codex or establish Android behavior. Full builds can still run entirely on a phone.

## Documentation language

Use English for default documentation, code comments, script output, and release materials. Chinese translations use sibling `*.zh-CN.md` files. Put reciprocal language links at the top, and update both versions when behavior or version information changes. Preserve multilingual test inputs and character-width fixtures.

## License

New contributions are provided under the project's Apache-2.0 license. Retain provenance, licenses, and NOTICE files when incorporating third-party code. Historical license records remain intact; a project license change does not change third-party licenses.
