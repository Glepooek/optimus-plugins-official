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
if (-not $canSymlink) {
    Write-Host "⛔ 权限检测失败，操作终止。解决权限后重新运行本 skill。" -ForegroundColor Red
    return
}
```

macOS/Linux 无需此步骤，直接进入 Step 1。

---

## Step 1 — 扫描源目录

**Windows PowerShell：**

```powershell
# Windows
$source = "$env:USERPROFILE\.agents\skills"

# 源目录不存在 → 终止并提示
if (-not (Test-Path $source)) {
    Write-Host "❌ 源目录不存在: $source" -ForegroundColor Red
    Write-Host "   请先创建该目录，并在其中放置 skill 子目录，再运行本 skill。"
    return
}

$skills = Get-ChildItem -Path $source -Directory | Select-Object -ExpandProperty Name

# 源目录为空 → 提示并终止
if ($skills.Count -eq 0) {
    Write-Host "⚠️  $source 中没有发现任何 skill 子目录，无需同步。"
    return
}

Write-Host "🔍 发现 $($skills.Count) 个 skill: $($skills -join ', ')"
```

**macOS/Linux Bash：**

```bash
# macOS/Linux
source="$HOME/.agents/skills"

# 源目录不存在 → 终止并提示
if [ ! -d "$source" ]; then
    echo "❌ 源目录不存在: $source"
    echo "   请先创建该目录，并在其中放置 skill 子目录，再运行本 skill。"
    return 1
fi

skills=($(ls -d "$source"/*/  2>/dev/null | xargs -I{} basename {}))

# 源目录为空 → 提示并终止
if [ ${#skills[@]} -eq 0 ]; then
    echo "⚠️  $source 中没有发现任何 skill 子目录，无需同步。"
    return 0
fi

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
            Write-Host "✅ 新建链接: $skill → $target/"
            $created++
        } elseif ((Get-Item $dest).LinkType -eq "SymbolicLink") {
            Write-Host "⚠️  已存在，跳过: $skill ($target)"
            $skipped++
        } else {
            Write-Host "⚠️  警告: $dest 已存在且非符号链接，自动同步失败。" -ForegroundColor Yellow
            Write-Host "    修复：执行 Remove-Item '$dest' -Recurse -Force，再重新运行本 skill。"
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
            echo "⚠️  警告: $dest 已存在且非符号链接，自动同步失败。"
            echo "    修复：执行 rm -rf '$dest'，再重新运行本 skill。"
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

检测完成后输出结果：

**Windows：**
```powershell
if ($dangling.Count -eq 0) {
    Write-Host "✅ 未检测到失效链接"
} else {
    Write-Host "⚠️  检测到 $($dangling.Count) 条失效链接："
    $dangling | ForEach-Object { Write-Host "   $($_.Path) → $($_.Target)" }
}
```

**macOS/Linux：**
```bash
if [ ${#dangling[@]} -eq 0 ]; then
    echo "✅ 未检测到失效链接"
else
    echo "⚠️  检测到 ${#dangling[@]} 条失效链接："
    for link in "${dangling[@]}"; do echo "   $link"; done
fi
```

---

## Step 4 — 汇总输出 & CHECKPOINT 处理失效链接

先打印汇总：

**Windows：**
```powershell
Write-Host "──────────────────────────────────────────"
Write-Host "汇总: 新建 $created 条，跳过 $skipped 条，警告 $warned 条，失效 $($dangling.Count) 条"
```

**macOS/Linux：**
```bash
echo "──────────────────────────────────────────"
echo "汇总: 新建 $created 条，跳过 $skipped 条，警告 $warned 条，失效 ${#dangling[@]} 条"
```

若 `dangling` 非空，列出所有失效链接后进入 CHECKPOINT：

🔴 **CHECKPOINT — 失效链接处理（继续前必须完成）：**

> 以上 X 条失效链接指向已不存在的源目录，是否删除？
> 请回复 `y` 确认删除，或 `n` 跳过（稍后手动处理）。

- 若用户回复 `y`：逐条删除失效链接，打印 `🗑️ 已删除: <path>`

**Windows — 删除失效链接**

```powershell
foreach ($item in $dangling) {
    Remove-Item $item.Path -Force
    Write-Host "🗑️ 已删除: $($item.Path)"
}
```

**macOS/Linux — 删除失效链接**

```bash
for link in "${dangling[@]}"; do
    rm "$link"
    echo "🗑️ 已删除: $link"
done
```

- 若用户回复 `n`：打印 `ℹ️  已跳过，失效链接保留在原位置。如需清理：Windows 执行 Remove-Item <path> -Force；macOS/Linux 执行 rm <path>`

---

## ⛔ 反例与黑名单

以下操作会导致 skill 失败、数据丢失或产生难以排查的问题，**绝对不要做**：

| # | 禁止行为 | 后果 | 正确做法 |
|---|---------|------|---------|
| 1 | 在 `~/.agents/skills/` 中直接放置文件（非子目录） | skill 不识别，会被 `ls -d */` 跳过，但可能引起路径歧义 | 每个 skill 必须是独立子目录，如 `my-skill/SKILL.md` |
| 2 | 在目标目录（`~/.claude/skills/` 等）手动创建与 skill 同名的普通目录 | skill 检测为"非符号链接"，打印警告跳过，永远无法自动同步 | 先手动删除该目录，再运行 skill |
| 3 | 在 Windows 未开启开发者模式也未以管理员身份运行时强行执行 | Step 0 权限检测失败，skill 终止 | 开启设置 → 隐私和安全 → 开发者选项，或右键以管理员身份运行终端 |
| 4 | 手动修改已创建的符号链接指向 | 下次运行 skill 时该链接显示"已存在，跳过"，不会被修正 | 先删除错误的符号链接，再运行 skill 重新创建 |
| 5 | 在 `~/.agents/skills/` 被删除后不处理仍运行 skill | Step 1 源目录不存在检测会终止，但目标目录中的失效链接不会自动清除 | 先运行 skill 触发 CHECKPOINT，选 `y` 清除失效链接 |
| 6 | 对 `~/.claude/skills/` 中非本 skill 管理的符号链接执行失效检测 | Step 3 会检测所有符号链接，包括你手动创建或其他工具创建的链接，可能误列为"失效" | 在 CHECKPOINT 仔细核对列表再选 `y`，不确定则选 `n` |
