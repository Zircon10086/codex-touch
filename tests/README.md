# 测试目录

按实际行为添加测试，并接入 `scripts/check.sh`。优先使用合成输入验证事件转换、边界处理和退出清理，避免依赖私人会话数据。

`probe_pty.py` 在独立伪终端内运行诊断脚本，检查点击命中、短时关闭与恢复鼠标上报、正常退出和信号退出后的终端状态。已接入 `bash scripts/check.sh`。这不是 Codex 集成测试；[键盘真机验收](../docs/termux-touch.md)需在普通 Termux 会话中另做。

`test_prepare_lock.py` 检查发布锁文件修正只影响本地包版本，拒绝未知输入或错误输出校验值，并覆盖只读检查与重复执行。

`baseline_smoke.py` 验证实际构建包的版本和辅助程序、app-server 初始化，以及回环假模型驱动的代码执行和回复；另在合成 PTY 中验证默认后台模式的 TUI，并停止测试后台服务。使用独立临时 HOME/CODEX_HOME，只向本机假服务发送合成数据。它需要先完成基线构建，通过统一入口显式运行：

```sh
bash scripts/check.sh --baseline-package /home/developer/codex-touch-build/packages/baseline-0.169.0
```

不传 `--baseline-package` 时不会执行已构建 Codex 的集成验收。
