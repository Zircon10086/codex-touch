[English](README.md) | [简体中文](README.zh-CN.md)

# Source and provenance

`async-question-touch.patch` applies to the Codex Rust TUI revision pinned in `upstream.json`. The filename is retained for continuity; the cumulative patch includes asynchronous questions, shortcut hints, the agent command center, interruption, and upstream regression tests. Tests stay in their corresponding upstream modules. Run them through `scripts/check.sh --rust-tests`.

The patch derives from [OpenAI Codex](https://github.com/openai/codex) and retains its Apache-2.0 license. Copies of the upstream license and notices are `LICENSE.upstream` and `NOTICE.upstream`. The patch identifies modified files and preserves original author notices. Current project code, scripts, and documentation also use Apache-2.0; see root `NOTICE` for copyright and modifications. Third-party components retain their own licenses, and the historical `v0.1.0` MIT record remains unchanged. Full binary distributions must also retain applicable dependency notices.

The patch excludes the release tag's Cargo.lock metadata normalization, which is handled separately by `scripts/prepare-lock.py`. `prepare-touch.py` computes expected source using a temporary Git index, preserves the real index, and rejects unknown edits.
