[English](development.md) | 简体中文

# 开发指南

## 本地检查

```sh
bash scripts/check.sh
```

当前基础检查覆盖补丁语法、必要文件、版本号格式、变更记录、Shell 语法、Git 空白错误，以及键盘探针在合成 PTY 中的命中和清理。探针测试不启动 Codex 或操作 Android 前台，不能证明手机输入法已弹出。真机对照步骤见[首次调查](termux-touch.zh-CN.md)。

脚本可以从其他目录调用，会自行定位项目根目录。需要 Bash、Python 3.11+（标准库）、Git 和常见 Unix 工具。正常使用直接调用当前 Linux 环境的 Git；开发设备已有 `termux-run` 时，脚本在没有本地 Git 的情况下也支持桥接调用。桥不是项目依赖，专用启动命令见[环境示例](build.zh-CN.md#开发设备的启动示例)。

Android 共享存储可能限制直接执行文件，因此统一使用 `bash scripts/check.sh`，无需改变挂载或权限配置。

## 日常开发

触摸补丁开发前先按[手机构建指南](build.zh-CN.md)准备固定版本的上游源码和可运行程序。源码、编译与下载缓存位于 Debian Linux 文件系统；本仓库保存版本锁定、构建入口及适配改动。

1. 基于 `main` 开始一个范围明确的改动，需要隔离开发时创建 `feat/<name>` 或 `fix/<name>` 分支。
2. 实现前检查已有代码与接口；实现语言确定后再添加相应的依赖清单和构建配置。
3. 将源码加入 `src/`，有必要的测试加入 `tests/`，统一接入检查入口。
4. 将用户可见的变化记录到 `CHANGELOG.md` 的 `Unreleased` 下，运行检查并审阅差异后提交。

Git 提交按可独立理解的改动组织，例如 `chore: initialize development scaffold`、`feat: ...`、`fix: ...`。宿主工具使用 `termux-run`；Debian 已安装原生 Git 时，可直接操作 guest 源码。

若 Git 提示仓库所有权不一致，仅对本仓库使用单次参数：

```sh
git -c safe.directory="$(pwd -P)" status
```

若未配置提交身份，使用自己的 `user.name`、`user.email`，以单次 `git -c` 参数传入；不需要修改全局配置。

## 版本管理

- `VERSION` 为版本号的唯一来源，格式为 `X.Y.Z`，标签为 `vX.Y.Z`。
- `0.2.0` 是首个功能版本，`0.1.0` 是历史框架基线。开发期间的未发布变化写入 `Unreleased`，不必每次提交都改版本号。
- 0.x 阶段新增功能或不兼容变化递增次版本，兼容性修复递增修订版本；到 1.0.0 后遵循稳定接口的语义化版本规则。
- 准备版本时，在同一提交中更新 `VERSION`、README 当前版本和带日期的变更记录，检查通过后创建附注标签。
- 已共享的版本标签不移动；需要修正时提交新版本。

用户确认更新版本时，默认在同一轮交付中同步发布 GitHub Release，除非用户明确要求暂缓。普通开发提交可以留在 `Unreleased`；一旦确认版本更新，不能只推源码就结束，也不再次索要独立发布许可。

按以下顺序完成：

1. 确定版本，将已验收变化移入带日期的版本记录，同步 VERSION、双语 README 和 `docs/releases/vX.Y.Z.md` 及中文版本。
2. 运行基础检查，核对补丁与已验证程序包。测试代码未变时可沿用已有 Rust/程序包结果；否则运行相应验证。
3. 使用已验证的 noreply 身份提交，在同一提交创建附注版本标签。只推送 `main` 和该标签，关闭自动跟随标签。
4. 从标签导出源码，不含 Git 元数据、本地配置或缓存；逐文件核对归档与提交、检查解包源码，生成 SHA256SUMS，保留许可证及声明。
5. 创建草稿 Release，使用英文说明与语言切换链接，上传源码及校验文件。确认发布提交的 CI 通过，并下载草稿附件核对字节。
6. 正式发布并设为 Latest，核对公开元数据、标签、附件与匿名下载，记录 Release 链接及 CI 结果。仅源码推送或草稿不算完成已确认的版本更新；若发布受阻，明确报告未完成步骤。

使用当前环境的 Git；开发设备的认证远端操作经 `termux-run` 调用 Termux Git/gh。保留已有发布标签和 Release。禁止通过 `--all`、`--mirror` 或 `--tags` 推送本地备份分支及无关历史标签。

适配版构建与完整验证入口见[第一阶段](phase1.zh-CN.md)。`--rust-tests` 和 `--touch-package PATH` 属于显式的耗时检查，不会在基础检查时自动编译。

## 更新上游补丁

上游 checkout 的 HEAD 必须保持 `upstream.json` 指定的提交，不要在该 checkout 提交适配代码而让 HEAD 偏离基线。仓库中的补丁才是适配代码的版本记录。编辑后，新文件先用 `git add -N <具体新文件路径>` 登记，再从上游目录导出：

```sh
# 从 codex-touch 仓库目录执行，输出保持原累计补丁文件名
git -C "$HOME/codex-touch-build/upstream" diff --binary HEAD -- codex-rs/tui > src/async-question-touch.patch
python3 -B scripts/prepare-touch.py "$HOME/codex-touch-build/upstream" --check
```

仅导出 TUI 目录，已知 Cargo.lock 元数据修正由 `prepare-lock.py` 独立维护。不要夹带其他源码改动。Rust 测试筛选位于 `scripts/test-touch.sh`；新增范围应接入统一入口，不能只在本地单独运行。

## 持续检查

`.github/workflows/check.yml` 在 `main` 推送和 Pull Request 时执行 `bash scripts/check.sh`。工作流仅授予 `contents: read`，checkout 固定到已核对的提交，且不保留凭据。基础检查不下载或编译上游 Codex；完整 Rust 和程序包验收继续由开发者显式运行。

默认文档使用英文，中文版本使用 `*.zh-CN.md`。每份文档顶部提供双向语言切换；`scripts/check-docs.py` 通过统一检查入口验证语言配对、相对链接和版本信息。
