# GitHub CLI (gh)

- **网址**：https://github.com/cli/cli
- **简介**：GitHub 官方命令行工具，README 一句话定位是"`gh` is GitHub on the command line"——把 pull request、issue 等 GitHub 概念搬到终端，与 `git` 和代码放在一起操作。
- **开发语言**：Go
- **核心能力**：
  - 终端内完成 PR、issue 及相关工作流：`gh pr create` / `gh pr checks` / `gh pr merge` / `gh issue` 等
  - `gh api` 直调任意 REST/GraphQL 端点，覆盖子命令未封装的能力
  - 自带 agent skill：`gh skill install cli/cli gh --scope user` 安装，`gh skill update gh` 更新
  - 支持 GitHub.com、GitHub Enterprise Cloud 与受支持的 GitHub Enterprise Server 版本；跨 macOS / Windows / Linux
  - GitHub 托管的 Actions runner 已预装，按周更新；Codespaces 里加 devcontainer feature `ghcr.io/devcontainers/features/github-cli:1` 即可
  - 产物可验证：v2.93.0 起 release 不可变，v2.50.0 起产出经 Public Good Sigstore 签名的 Build Provenance Attestation，可用 `gh at verify -R cli/cli <file>` 或 cosign 校验
- **安装方式**：Windows 用 WinGet；macOS 用 Homebrew；Linux 提供 Debian/Ubuntu/Raspberry Pi 包与 RPM 系（Amazon Linux、CentOS、Fedora、openSUSE、RHEL、SUSE）包；各平台均提供预编译二进制；也可按 `docs/install_source.md` 从源码构建。官方 README 只给出分平台安装文档的链接，未在页面上列出具体命令。
- **备注**：本仓库 `commit-cc-plugin` skill 的第五步（开 PR → 等六项必需检查 → squash merge）自 6.0.0 起以它为唯一依赖，替换掉原先的 GitHub MCP（见 `tools.ref.github-mcp-server`，已从 `optimus-mcp-servers` 移除）。⚠️ 本机实测该仓库 `allow_auto_merge: false`，因此 skill 里刻意不用 `gh pr merge --auto`，改为 `gh pr checks --required --watch` 等待后显式合并。更新方式与卸载方式官方 README 均未给出（只有 agent skill 的 `gh skill update gh`），随各平台包管理器处理。MIT 许可，GitHub 46.3k star，最新版本 v2.101.0（2026-09-15）。
