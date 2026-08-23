# 02 · 提交信息规范与敏感信息防护

> 更新历史：2026-08-23 创建，迁移自 `csharp/16-collaboration.md` §2 并新增提交前检查、Hooks 规范与敏感信息防护。

## 1. 提交信息

- **必须**：遵循 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

  ```
  type(scope): description
  ```

  常用 `type`：`feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `build` / `ci` / `chore`
- **必须**：提交信息描述变更意图（What & Why），不逐行罗列
- **禁止**：无意义提交（`update`、`fix`、堆叠的 `wip`）
- **应该**：一个提交一个逻辑变更（原子提交，便于回滚与审阅）

## 2. 提交前检查与 Hooks

- **必须**：仓库配置的 pre-commit / commit-msg hook（格式化、lint、提交信息校验）不得绕过，禁止使用 `--no-verify` 跳过
- **必须**：hook 执行失败时定位并修复根因，不得注释掉 hook 配置或强行提交
- **应该**：pre-commit hook 只做快速检查（格式化、lint），耗时的测试/构建交给 CI，避免拖慢本地提交

## 3. 敏感信息与大文件防护

- **必须**：密钥、密码、Token、连接串禁止出现在提交内容中，走密钥管理（环境变量、Secret Manager），配置示例文件用占位符
- **必须**：一旦敏感信息进入 Git 历史（即使后续删除），视为已泄露，须立即在源头轮换该密钥/密码，删除历史记录不能替代轮换
- **应该**：仓库配置 `.gitignore` 基线覆盖常见敏感文件模式（`.env`、`*.pem`、`credentials.json` 等）与本地产物目录
- **应该**：CI 集成 secret scanning，在 PR 阶段拦截误提交的密钥模式
- **禁止**：直接提交大体积二进制文件（构建产物、依赖包、视频等）到常规版本控制，超过仓库约定阈值的资产应走 Git LFS 或外部存储
