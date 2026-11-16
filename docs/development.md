# 开发指南

## 本地检查

```sh
bash scripts/check.sh
```

当前检查覆盖必要文件、版本号格式、变更记录、Shell 语法、Git 空白错误，以及键盘探针在合成 PTY 中的命中和清理。探针测试不启动 Codex 或操作 Android 前台，不能证明手机输入法已弹出。真机对照步骤见[首次调查](termux-touch.md)。

脚本可以从其他目录调用，会自行定位项目根目录。需要 Bash、Python 3（标准库）、Git 和常见 Unix 工具；Debian guest 缺少 Git 时自动经 `termux-run` 使用宿主 Git。也可以显式在宿主运行：

```sh
termux-run --cwd /storage/emulated/0/Agent/codex-touch bash scripts/check.sh
```

Android 共享存储可能限制直接执行文件，因此统一使用 `bash scripts/check.sh`，无需改变挂载或权限配置。

## 日常开发

1. 基于 `main` 开始一个范围明确的改动，需要隔离开发时创建 `feat/<name>` 或 `fix/<name>` 分支。
2. 实现前检查已有代码与接口；实现语言确定后再添加相应的依赖清单和构建配置。
3. 将源码加入 `src/`，有必要的测试加入 `tests/`，统一接入检查入口。
4. 将用户可见的变化记录到 `CHANGELOG.md` 的 `Unreleased` 下，运行检查并审阅差异后提交。

Git 提交按可独立理解的改动组织，例如 `chore: initialize development scaffold`、`feat: ...`、`fix: ...`。在 guest 中手动使用 Git 时加上 `termux-run` 前缀。

若 Git 提示仓库所有权不一致，仅对本仓库使用单次参数：

```sh
termux-run git -c safe.directory=/storage/emulated/0/Agent/codex-touch status
```

若未配置提交身份，使用自己的 `user.name`、`user.email`，以单次 `git -c` 参数传入；不需要修改全局配置。

## 版本管理

- `VERSION` 为版本号的唯一来源，格式为 `X.Y.Z`，标签为 `vX.Y.Z`。
- 当前 `0.1.0` 表示框架基线。开发期间的未发布变化写入 `Unreleased`，不必每次提交都改版本号。
- 0.x 阶段新增功能或不兼容变化递增次版本，兼容性修复递增修订版本；到 1.0.0 后遵循稳定接口的语义化版本规则。
- 准备版本时，在同一提交中更新 `VERSION`、README 当前版本和带日期的变更记录，检查通过后创建附注标签。
- 已共享的版本标签不移动；需要修正时提交新版本。

例如准备好 0.2.0 对应提交后，在 Termux 中执行：

```sh
bash scripts/check.sh
git tag -a v0.2.0 -m "codex-touch 0.2.0"
```

guest 中标签命令同样通过 `termux-run git` 执行。提交与附注标签都需要 Git 身份。远端仓库、推送和发布在确定托管位置后单独配置。
