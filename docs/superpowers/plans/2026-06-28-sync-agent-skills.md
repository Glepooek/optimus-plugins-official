# sync-agent-skills 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `unipus-devops-plugin` 中新增 `sync-agent-skills` skill，将 `~/.agents/skills/` 的所有子目录以符号链接方式同步到 `~/.claude/skills/` 和 `~/.kiro/skills/`。

**Architecture:** 纯 SKILL.md 声明式 skill——不含外部脚本，Claude 读取指令后直接用 PowerShell/Bash 工具执行链接操作。分四步：扫描源目录、创建缺失链接、检测失效链接、CHECKPOINT 处理失效链接。

**Tech Stack:** Claude Code skill（Markdown 指令文档）、PowerShell（Windows）、Bash（macOS/Linux）

## Global Constraints

- skill frontmatter 必须包含 `name`、`description` 字段
- 触发词覆盖：`同步 skills`、`sync agent skills`、`链接 skills`、`更新 skill 链接`、`sync-agent-skills`
- Windows 使用 `New-Item -ItemType SymbolicLink`；macOS/Linux 使用 `ln -s`
- 版本从 `3.0.7` 升级到 `3.1.0`（新增 skill → Minor bump）
- 提交必须通过 `commit-cc-plugin` skill，不得手动 git

---

### Task 1: 创建 sync-agent-skills SKILL.md

**Files:**
- Create: `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`

**Interfaces:**
- Produces: 可被 Claude Code 加载的 skill，触发词命中后执行符号链接同步

- [ ] **Step 1: 创建目录并写入 SKILL.md**

创建 `plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md`，内容如下：

```markdown
---
name: sync-agent-skills
description: 将 ~/.agents/skills/ 中的所有 skill 目录以符号链接同步到 ~/.claude/skills/ 和 ~/.kiro/skills/，使用户只需维护一个 source of truth。触发词：同步 skills、sync agent skills、链接 skills、更新 skill 链接、sync-agent-skills。
---

# sync-agent-skills

将 `~/.agents/skills/` 中的所有 skill 同步为符号链接，分发到各 AI 工具的 skills 目录。

> **全局使用说明：** 如需在所有项目中使用本 skill，将本目录（`sync-agent-skills/`）复制到
> `~/.agents/skills/sync-agent-skills/`，再运行一次本 skill 自动链接即可全局生效。

---

## Step 0 — 平台检测与权限预检（Windows 专用）

检测当前平台。若为 Windows，执行：

```powershell
# 检测是否有符号链接创建权限（开发者模式或管理员）
$canSymlink = $false
try {
    $testLink = "$env:TEMP\__symlink_test_$(Get-Random)"
    $testTarget = "$env:TEMP\__symlink_target_$(Get-Random)"
    New-Item -ItemType Directory -Path $testTarget -Force | Out-Null
    New-Item -ItemType SymbolicLink -Path $testLink -Target $testTarget -ErrorAction Stop | Out-Null
    Remove-Item $testLink -Force
    Remove-Item $testTarget -Force
    $canSymlink = $true
} catch {
    Write-Host "❌ 无法创建符号链接。请开启 Windows 开发者模式（设置 → 隐私和安全 → 开发者选项），或以管理员身份运行终端。" -ForegroundColor Red
}
if (-not $canSymlink) { exit 1 }
```

macOS/Linux 无需此步骤，直接进入 Step 1。

---

## Step 1 — 扫描源目录

```powershell
# Windows
$source = "$env:USERPROFILE\.agents\skills"
$skills = Get-ChildItem -Path $source -Directory | Select-Object -ExpandProperty Name
Write-Host "🔍 发现 $($skills.Count) 个 skill: $($skills -join ', ')"
```

```bash
# macOS/Linux
source="$HOME/.agents/skills"
skills=($(ls -d "$source"/*/  2>/dev/null | xargs -I{} basename {}))
echo "🔍 发现 ${#skills[@]} 个 skill: ${skills[*]}"
```

---

## Step 2 — 检测目标目录 & 创建缺失链接

目标目录：`~/.claude/skills/` 和 `~/.kiro/skills/`（若 `~/.kiro/` 不存在则跳过 kiro）。

**Windows PowerShell：**

```powershell
$targets = @(
    "$env:USERPROFILE\.claude\skills",
    "$env:USERPROFILE\.kiro\skills"
)

$created = 0
$skipped = 0
$warned  = 0

foreach ($target in $targets) {
    # 检查父目录（.kiro 本体）是否存在
    $parent = Split-Path (Split-Path $target -Parent) -Parent
    if (-not (Test-Path (Split-Path $target -Parent))) {
        Write-Host "ℹ️  $(Split-Path $target -Parent) 不存在，已跳过 $(Split-Path $target -Leaf) 同步"
        continue
    }
    # 自动创建目标目录
    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }
    foreach ($skill in $skills) {
        $dest = Join-Path $target $skill
        $src  = Join-Path $source $skill
        if (-not (Test-Path $dest)) {
            New-Item -ItemType SymbolicLink -Path $dest -Target $src | Out-Null
            Write-Host "✅ 新建链接: $skill → $target\"
            $created++
        } elseif ((Get-Item $dest).LinkType -eq "SymbolicLink") {
            Write-Host "⚠️  已存在，跳过: $skill ($target)"
            $skipped++
        } else {
            Write-Host "⚠️  警告: $dest 已存在且非符号链接，请手动处理"
            $warned++
        }
    }
}
```

**macOS/Linux Bash：**

```bash
targets=("$HOME/.claude/skills" "$HOME/.kiro/skills")
created=0; skipped=0; warned=0

for target in "${targets[@]}"; do
    parent=$(dirname "$target")
    grandparent=$(dirname "$parent")
    if [ ! -d "$parent" ]; then
        echo "ℹ️  $parent 不存在，已跳过 $(basename $parent) 同步"
        continue
    fi
    mkdir -p "$target"
    for skill in "${skills[@]}"; do
        dest="$target/$skill"
        src="$source/$skill"
        if [ ! -e "$dest" ] && [ ! -L "$dest" ]; then
            ln -s "$src" "$dest"
            echo "✅ 新建链接: $skill → $target/"
            ((created++))
        elif [ -L "$dest" ]; then
            echo "⚠️  已存在，跳过: $skill ($target)"
            ((skipped++))
        else
            echo "⚠️  警告: $dest 已存在且非符号链接，请手动处理"
            ((warned++))
        fi
    done
done
```

---

## Step 3 — 检测失效链接

**Windows：**

```powershell
$dangling = @()
foreach ($target in $targets) {
    if (-not (Test-Path $target)) { continue }
    Get-ChildItem -Path $target | Where-Object { $_.LinkType -eq "SymbolicLink" } | ForEach-Object {
        if (-not (Test-Path $_.Target)) {
            $dangling += [PSCustomObject]@{ Path = $_.FullName; Target = $_.Target }
        }
    }
}
```

**macOS/Linux：**

```bash
dangling=()
for target in "${targets[@]}"; do
    [ -d "$target" ] || continue
    while IFS= read -r -d '' link; do
        [ -L "$link" ] && [ ! -e "$link" ] && dangling+=("$link")
    done < <(find "$target" -maxdepth 1 -type l -print0)
done
```

---

## Step 4 — 汇总输出 & CHECKPOINT 处理失效链接

先打印汇总：

```
──────────────────────────────────────────
汇总: 新建 N 条，跳过 N 条，警告 N 条，失效 N 条
```

若 `dangling` 非空，列出所有失效链接后进入 CHECKPOINT：

🔴 **CHECKPOINT — 失效链接处理（继续前必须完成）：**

> 以上 X 条失效链接指向已不存在的源目录，是否删除？
> 请回复 `y` 确认删除，或 `n` 跳过（稍后手动处理）。

- 若用户回复 `y`：逐条删除失效链接，打印 `🗑️ 已删除: <path>`
- 若用户回复 `n`：打印 `ℹ️  已跳过，失效链接仍保留，请稍后手动处理`
```

- [ ] **Step 2: 验证文件创建成功**

```bash
# Windows
Test-Path "plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md"
# 期望输出: True

# macOS/Linux
ls plugins/unipus-devops-plugin/skills/sync-agent-skills/SKILL.md
```

- [ ] **Step 3: 手动触发测试**

在加载了本插件的 Claude Code 会话中输入"同步 skills"，验证：
1. Step 0 权限检测通过（Windows）
2. Step 1 正确列出 `~/.agents/skills/` 下所有 skill 名
3. Step 2 对已存在的链接输出"已存在，跳过"，对新 skill（如 `youdaonote-skill`）输出"新建链接"
4. 汇总行数据正确
5. 无失效链接时不出现 CHECKPOINT

---

### Task 2: 版本升级与提交

**Files:**
- Modify: `.claude-plugin/marketplace.json`（version: `3.0.7` → `3.1.0`）

**Interfaces:**
- Consumes: Task 1 完成，`sync-agent-skills/SKILL.md` 已存在

- [ ] **Step 1: 更新版本号**

编辑 `.claude-plugin/marketplace.json`，将 `"version": "3.0.7"` 改为 `"version": "3.1.0"`。

- [ ] **Step 2: 提交推送**

触发 `commit-cc-plugin` skill（说"提交"），不得手动执行 git 命令。

commit message 参考：
```
feat(devops): 新增 sync-agent-skills skill，自动同步 ~/.agents/skills/ 符号链接
```
