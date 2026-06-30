# sync-agent-skills 自定义 source/target 参数扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 sync-agent-skills skill 新增 `source=` 和 `target=` 参数支持，不指定时保持默认行为不变。

**Architecture:** 在现有 Step 0（权限检测）之前插入新的参数解析步骤，将解析结果赋值给 `$source`/`$targets` 变量，后续所有步骤通过变量消费，无需感知是否使用了自定义参数。步骤编号整体 +1。

**Tech Stack:** SKILL.md（AI agent 指令文档）、PowerShell（Windows）、Bash（macOS/Linux）

## Global Constraints

- 目标文件：`plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`
- 默认 source：`~/.agents/skills/`；默认 targets：`~/.claude/skills/`、`~/.kiro/skills/`
- `target` 多值以逗号分隔，解析为数组后 Trim 每项首尾空格
- 边界处理仅在使用自定义参数时触发（默认路径保持原有静默跳过逻辑）
- 版本升级至 `v1.2.0`（新增功能 → Minor）
- 必须同步更新 `CHANGELOG.md`

---

## File Structure

| 操作 | 文件 | 说明 |
|------|------|------|
| Modify | `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md` | 新增 Step 0、步骤重编号、边界处理 |
| Modify | `plugins/unipus-devops-plugin/skills/sync-agent-skills/CHANGELOG.md` | 新增 v1.2.0 条目 |

---

### Task 1: 新增 Step 0 — 参数解析（Windows + Bash）

**Files:**
- Modify: `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`

**Interfaces:**
- Produces: `$source`（字符串）、`$targets`（数组）、`$useCustom`（布尔）供后续所有步骤消费

- [ ] **Step 1: 阅读当前 SKILL.md 全文，确认插入位置**

  目标：在第一个 `## Step 0` 标题之前插入新内容。当前第一个标题为：
  ```
  ## Step 0 — 平台检测与权限预检（Windows 专用）
  ```
  插入点：该标题之前，`# sync-agent-skills` 正文标题之后。

- [ ] **Step 2: 在 SKILL.md 中插入 Step 0 参数解析章节**

  在 `---` 分隔线和 `## Step 0 — 平台检测与权限预检` 之间插入以下完整内容：

  ````markdown
  ## Step 0 — 参数解析

  读取用户指令，提取 `source=` 和 `target=` 参数。未提供则使用默认值。

  **Windows PowerShell：**

  ```powershell
  # 默认值
  $source    = "$env:USERPROFILE\.agents\skills"
  $targets   = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills")
  $useCustom = $false

  # 从用户指令中提取参数（AI 读取用户消息，有则覆盖）
  # source=<绝对路径>           → 覆盖 $source
  # target=<路径1,路径2,...>    → 按逗号分割并 .Trim()，覆盖 $targets

  # 示例：若用户说 "source=D:\my-skills target=C:\tools\cursor\skills,C:\tools\windsurf\skills"
  # 则：
  #   $source  = "D:\my-skills"
  #   $targets = @("C:\tools\cursor\skills", "C:\tools\windsurf\skills")
  #   $useCustom = $true

  Write-Host "📂 source : $source"
  Write-Host "🎯 targets: $($targets -join ' | ')"

  if ($useCustom) {
      Write-Host ""
      Write-Host "ℹ️  参数用法："
      Write-Host "    source=<绝对路径>         指定 skill 源目录"
      Write-Host "    target=<路径1,路径2,...>  指定一个或多个目标目录（逗号分隔）"
  }
  ```

  **macOS/Linux Bash：**

  ```bash
  # 默认值
  source_dir="$HOME/.agents/skills"
  targets=("$HOME/.claude/skills" "$HOME/.kiro/skills")
  use_custom=false

  # 从用户指令中提取参数（AI 读取用户消息，有则覆盖）
  # source=<绝对路径>           → 覆盖 source_dir
  # target=<路径1,路径2,...>    → IFS=',' read -ra targets，覆盖 targets 数组

  # 示例：若用户说 "source=~/my-skills target=~/.cursor/skills,~/.windsurf/skills"
  # 则：
  #   source_dir="$HOME/my-skills"
  #   targets=("$HOME/.cursor/skills" "$HOME/.windsurf/skills")
  #   use_custom=true

  echo "📂 source : $source_dir"
  echo "🎯 targets: $(IFS=' | '; echo "${targets[*]}")"

  if [ "$use_custom" = true ]; then
      echo ""
      echo "ℹ️  参数用法："
      echo "    source=<绝对路径>         指定 skill 源目录"
      echo "    target=<路径1,路径2,...>  指定一个或多个目标目录（逗号分隔）"
  fi
  ```

  ---

  ````

- [ ] **Step 3: 验证插入结果**

  读取 SKILL.md，确认：
  - `## Step 0 — 参数解析` 位于第一个 `---` 分隔线之后
  - 原 `## Step 0 — 平台检测与权限预检` 紧随其后（尚未重编号，Task 2 再处理）
  - Windows 和 Bash 两个代码块均完整

---

### Task 2: 步骤重编号（Step 0→1，其余依次 +1）

**Files:**
- Modify: `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`

**Interfaces:**
- Consumes: Task 1 插入后的 SKILL.md
- Produces: 步骤编号一致的 SKILL.md（Step 0 参数解析 → Step 1 权限检测 → Step 2 扫描 → Step 3 创建链接 → Step 4 检测失效 → Step 5 汇总）

- [ ] **Step 1: 重命名各 Step 标题**

  执行以下精确替换（每条独立，顺序执行）：

  | 原标题 | 新标题 |
  |--------|--------|
  | `## Step 0 — 平台检测与权限预检（Windows 专用）` | `## Step 1 — 平台检测与权限预检（Windows 专用）` |
  | `## Step 1 — 扫描源目录` | `## Step 2 — 扫描源目录` |
  | `## Step 2 — 检测目标目录 & 创建缺失链接` | `## Step 3 — 检测目标目录 & 创建缺失链接` |
  | `## Step 3 — 检测失效链接` | `## Step 4 — 检测失效链接` |
  | `## Step 4 — 汇总输出 & CHECKPOINT 处理失效链接` | `## Step 5 — 汇总输出 & CHECKPOINT 处理失效链接` |

  同时更新 Step 1 正文中的跳转说明：
  - `macOS/Linux 无需此步骤，直接进入 Step 1。` → `macOS/Linux 无需此步骤，直接进入 Step 2。`

- [ ] **Step 2: 验证编号连续性**

  读取 SKILL.md，确认出现顺序为：
  ```
  ## Step 0 — 参数解析
  ## Step 1 — 平台检测与权限预检（Windows 专用）
  ## Step 2 — 扫描源目录
  ## Step 3 — 检测目标目录 & 创建缺失链接
  ## Step 4 — 检测失效链接
  ## Step 5 — 汇总输出 & CHECKPOINT 处理失效链接
  ```
  共 6 个 Step 标题，无跳号。

---

### Task 3: 添加自定义路径边界处理

**Files:**
- Modify: `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`

**Interfaces:**
- Consumes: `$useCustom`/`$use_custom`（Task 1 产出）
- Produces: 在 Step 2（扫描源目录）之前插入边界检查块

- [ ] **Step 1: 在 Step 2 标题之前插入边界处理章节**

  在 `## Step 2 — 扫描源目录` 标题之前，`---` 分隔线之后插入：

  ````markdown
  ## 自定义路径边界处理（仅在使用自定义参数时执行）

  若 `$useCustom`（Windows）或 `$use_custom`（Bash）为 true，在扫描源目录前执行以下检查：

  **检查 1 — source 路径不存在：** 行为与默认模式一致，打印错误并终止。无需额外处理，Step 2 的扫描逻辑已覆盖。

  **检查 2 — target 父目录不存在：** AI 打印提示并进入 CHECKPOINT，用户回复 y/n 后继续。写法与现有 Step 5 CHECKPOINT 保持一致：

  ```
  🔴 CHECKPOINT — 目标目录父目录缺失（继续前必须完成）：

  以下目标目录的父目录不存在：
    - <target> (父目录: <parent>)
    ...

  是否自动创建缺失的父目录？
  请回复 `y` 全部创建，或 `n` 跳过这些目标。
  ```

  - 若用户回复 `y`（Windows）：
  ```powershell
  foreach ($target in $missingParentTargets) {
      $parentDir = Split-Path $target -Parent
      New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
      Write-Host "✅ 已创建: $parentDir"
  }
  ```

  - 若用户回复 `y`（Bash）：
  ```bash
  for target in "${missing_parent_targets[@]}"; do
      mkdir -p "$(dirname "$target")"
      echo "✅ 已创建: $(dirname "$target")"
  done
  ```

  - 若用户回复 `n`：将这些 target 从 `$targets` 数组中移除，打印 `ℹ️  已跳过: <target>`
  ```

  **检查 3 — target 路径是文件（非目录）（Windows）：**

  ```powershell
  $targets = $targets | Where-Object {
      $t = $_
      if (Test-Path $t -PathType Leaf) {
          Write-Host "❌ $t 已存在且是文件，跳过。" -ForegroundColor Red
          $false
      } else {
          $true
      }
  }
  ```

  **检查 3 — target 路径是文件（非目录）（Bash）：**

  ```bash
  final_targets=()
  for target in "${targets[@]}"; do
      if [ -f "$target" ]; then
          echo "❌ $target 已存在且是文件，跳过。"
      else
          final_targets+=("$target")
      fi
  done
  targets=("${final_targets[@]}")
  ```

  ---

  ````

- [ ] **Step 2: 验证插入位置**

  读取 SKILL.md，确认"自定义路径边界处理"章节位于：
  - `## Step 1 — 平台检测与权限预检` 之后
  - `## Step 2 — 扫描源目录` 之前

- [ ] **Step 3: 更新黑名单条目 5（源目录删除场景）**

  原条目 5 描述为：
  ```
  | 5 | 在 `~/.agents/skills/` 被删除后不处理仍运行 skill | Step 1 源目录不存在检测会终止...
  ```
  更新为：
  ```
  | 5 | 在 `~/.agents/skills/` 被删除后不处理仍运行 skill | Step 2 源目录不存在检测会终止，但目标目录中的失效链接不会自动清除 | 先运行 skill 触发 CHECKPOINT，选 `y` 清除失效链接 |
  ```
  （仅将"Step 1"改为"Step 2"，其余不变）

---

### Task 4: 更新版本号和 CHANGELOG

**Files:**
- Modify: `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`（frontmatter version）
- Modify: `plugins/unipus-devops-plugin/skills/sync-agent-skills/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1-3 完成后的 SKILL.md

- [ ] **Step 1: 更新 frontmatter version**

  将 SKILL.md 第 3 行：
  ```yaml
  version: 1.1.0
  ```
  改为：
  ```yaml
  version: 1.2.0
  ```

- [ ] **Step 2: 在 CHANGELOG.md 顶部插入 v1.2.0 条目**

  在现有 `## [1.1.0]` 条目之前插入：

  ```markdown
  ## [1.2.0] - 2026-06-30

  ### Added
  - Step 0 参数解析：支持 `source=<路径>` 和 `target=<路径1,路径2,...>` 参数语法
  - 支持 target 多目标（逗号分隔，解析为数组）
  - 自定义路径边界处理：target 父目录不存在时询问是否创建，target 是文件时报错跳过
  - 使用自定义参数时自动打印参数语法说明

  ### Changed
  - 步骤编号整体 +1（原 Step 0-4 → 新 Step 1-5），新 Step 0 为参数解析

  ```

- [ ] **Step 3: 验证 CHANGELOG 格式**

  读取 CHANGELOG.md，确认：
  - 版本号顺序：`[1.2.0]` → `[1.1.0]` → `[1.0.0]`（降序）
  - 每个版本均有日期
  - 无 TBD 或空白条目

- [ ] **Step 4: 提交**

  使用 `commit-cc-plugin` skill 提交，说"提交"即可触发。
  提交信息参考：`feat(sync-agent-skills): 支持自定义 source/target 参数（v1.2.0）`
