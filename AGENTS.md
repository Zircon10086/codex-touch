# codex-touch 开发约定

- 本项目为 Termux 中的 Codex 提供触摸操作支持，采用 Apache-2.0 许可证，保留上游及第三方声明。
- 修改前阅读 `README.md`、`docs/design.md` 和相关源码；按需更新设计说明。
- 先验证 Termux 输入到 Codex 的实际链路，再确定实现语言和组件边界。优先复用已有接口与上游逻辑。
- 维持最小必要依赖；不要为尚未实现的功能预建插件、服务或抽象层。
- 源码放入 `src/`，有行为覆盖价值的测试放入 `tests/`。新检查和测试应接入 `scripts/check.sh`，避免漏跑。
- 每次改动运行 `bash scripts/check.sh`，报告检查范围；基础检查通过不代表触摸功能或手机交互已验证。
- 修改面向用户的行为时更新 `CHANGELOG.md`。版本与发布遵循 `docs/development.md`。
- 使用 UTF-8、LF；共享存储中的脚本通过 `bash` 调用，不能依赖文件系统可执行位。
- Debian guest 需要宿主工具时使用 `termux-run`，不混用 Android 与 Debian PATH。
- 不自动修改全局 Git 配置；需要时用单次 `-c` 指定身份和当前仓库的 `safe.directory`。
- 诊断材料使用合成数据，不提交终端会话内容、凭据或个人数据。保持上级工作区要求的手机操作与隐私边界。
