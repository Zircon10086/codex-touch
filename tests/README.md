# 测试目录

按实际行为添加测试，并接入 `scripts/check.sh`。优先使用合成输入验证事件转换、边界处理和退出清理，避免依赖私人会话数据。

`probe_pty.py` 在独立伪终端内运行诊断脚本，检查点击命中、短时关闭与恢复鼠标上报、正常退出和信号退出后的终端状态。已接入 `bash scripts/check.sh`。这不是 Codex 集成测试；[键盘真机验收](../docs/termux-touch.md)需在普通 Termux 会话中另做。
