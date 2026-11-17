[English](README.md) | 简体中文

# 源码与来源

`async-question-touch.patch` 是针对 `upstream.json` 固定提交的 Codex Rust TUI 补丁，保留原文件名，累计包含异步问答、快捷键提示、Agent command center 和工作中断提示点击的实现及上游测试。测试文件随补丁保留在上游对应模块中，仓库的 `scripts/check.sh --rust-tests` 为统一入口。

补丁基于 OpenAI Codex（https://github.com/openai/codex），保留上游 Apache-2.0 许可，许可与声明副本为 `LICENSE.upstream`、`NOTICE.upstream`。补丁标识了 codex-touch 对上游文件的修改；原作者的声明保持不变。本项目自有代码、脚本与文档统一采用根目录 Apache-2.0；版权及修改说明见根目录 `NOTICE`。第三方组件保留各自许可证，历史 `v0.1.0` 的 MIT 许可记录不变。分发完整二进制时也需遵守上游及依赖许可。

补丁不包含发布标签的 Cargo.lock 元数据规范化；该修正继续由 `scripts/prepare-lock.py` 独立处理。`prepare-touch.py` 用临时 Git 索引计算预期源码，不修改真实索引，拒绝未知改动。
