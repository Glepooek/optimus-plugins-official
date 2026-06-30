---
name: sync-agent-skills
version: 1.2.0
description: 将 ~/.agents/skills/ 中的所有 skill 目录以符号链接同步到 ~/.claude/skills/ 和 ~/.kiro/skills/，使用户只需维护一个 source of truth。触发词：同步 skills、sync agent skills、链接 skills、更新 skill 链接、sync-agent-skills。
---

# sync-agent-skills

将 `~/.agents/skills/` 中的所有 skill 同步为符号链接，分发到各 AI 工具的 skills 目录。

---

## Step 0 — 参数解析

读取用户指令，提取 `source=` 和 `target=` 参数。未提供则使用默认值。

**Windows PowerShell：**

```powershell
# 默认值
$source    = "$env:USERPROFILE\.agents\skills"
$targets   = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills")
$useCustom = $false

# 从用户消息中提取 source= 和 target= 参数
# 用户消息示例："同步 skills source=D:\my-skills target=C:\cursor\skills,C:\windsurf\skills"
$userMsg = "<此处为用户完整消息>"   # AI 将此变量替换为实际用户消息

if ($userMsg -match '(?:^|\s)source=([^\s]+)') {
    $source    = $Matches[1]
    $useCustom = $true
}
if ($userMsg -match '(?:^|\s)target=([^\s]+)') {
    $targets   = $Matches[1] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
    $useCustom = $true
}

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

# 从用户消息中提取 source= 和 target= 参数
# 用户消息示例："同步 skills source=~/my-skills target=~/.cursor/skills,~/.windsurf/skills"
user_msg="<此处为用户完整消息>"   # AI 将此变量替换为实际用户消息

if [[ "$user_msg" =~ (^|[[:space:]])source=([^[:space:]]+) ]]; then
    source_dir="${BASH_REMATCH[2]}"
    use_custom=true
fi
if [[ "$user_msg" =~ (^|[[:space:]])target=([^[:space:]]+) ]]; then
    IFS=',' read -ra targets <<< "${BASH_REMATCH[2]}"
    use_custom=true
fi

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

## Step 1 — 平台检测与权限预检（Windows 专用）

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

macOS/Linux 无需此步骤，直接进入 Step 2。

---

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

## Step 2 — 扫描源目录

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
# macOS/Linux（$source_dir 由 Step 0 赋值，此处仅在 Step 0 未执行时兜底）
source_dir="${source_dir:-$HOME/.agents/skills}"

# 源目录不存在 → 终止并提示
if [ ! -d "$source_dir" ]; then
    echo "❌ 源目录不存在: $source_dir"
    echo "   请先创建该目录，并在其中放置 skill 子目录，再运行本 skill。"
    return 1
fi

skills=()
while IFS= read -r -d '' d; do
    skills+=("$(basename "$d")")
done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d -print0)

# 源目录为空 → 提示并终止
if [ ${#skills[@]} -eq 0 ]; then
    echo "⚠️  $source_dir 中没有发现任何 skill 子目录，无需同步。"
    return 0
fi

echo "🔍 发现 ${#skills[@]} 个 skill: ${skills[*]}"
```

---

## Step 3 — 检测目标目录 & 创建缺失链接

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
    $parentDir = Split-Path $target -Parent
    if (-not (Test-Path $parentDir)) {
        Write-Host "ℹ️  $parentDir 不存在，已跳过 $(Split-Path $target -Leaf) 同步"
        continue
    }
    # 自动创建目标目录
    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }
    foreach ($skill in $skills) {
        $dest = Join-Path $target $skill
        $src  = Join-Path $source $skill
        $item = Get-Item $dest -ErrorAction SilentlyContinue
        if ($null -eq $item) {
            New-Item -ItemType SymbolicLink -Path $dest -Target $src | Out-Null
            Write-Host "✅ 新建链接: $skill → $target/"
            $created++
        } elseif ($item.LinkType -eq "SymbolicLink") {
            $currentTarget = (Get-Item $dest).Target
            if ($currentTarget -ne $src) {
                Remove-Item $dest -Force
                New-Item -ItemType SymbolicLink -Path $dest -Target $src | Out-Null
                Write-Host "🔄 更新链接: $skill ($currentTarget → $src)"
                $created++
            } else {
                Write-Host "✔  已是最新，跳过: $skill ($target)"
                $skipped++
            }
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
            current_target=$(readlink "$dest")
            if [ "$current_target" != "$src" ]; then
                rm "$dest"
                ln -s "$src" "$dest"
                echo "🔄 更新链接: $skill ($current_target → $src)"
                ((created++))
            else
                echo "✔  已是最新，跳过: $skill ($target)"
                ((skipped++))
            fi
        else
            echo "⚠️  警告: $dest 已存在且非符号链接，自动同步失败。"
            echo "    修复：执行 rm -rf '$dest'，再重新运行本 skill。"
            ((warned++))
        fi
    done
done
```

---

## Step 4 — 检测失效链接

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

## Step 5 — 汇总输出 & CHECKPOINT 处理失效链接

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

| # | 禁止行为 | 后果 | 正确做法 |
|---|---------|------|---------|
| 1 | 在 `~/.agents/skills/` 中直接放置文件（非子目录） | skill 不识别，会被 `ls -d */` 跳过，但可能引起路径歧义 | 每个 skill 必须是独立子目录，如 `my-skill/SKILL.md` |
| 2 | 在目标目录（`~/.claude/skills/` 等）手动创建与 skill 同名的普通目录 | skill 检测为"非符号链接"，打印警告跳过，永远无法自动同步 | 先手动删除该目录，再运行 skill |
| 3 | 在 Windows 未开启开发者模式也未以管理员身份运行时强行执行 | Step 0 权限检测失败，skill 终止 | 开启设置 → 隐私和安全 → 开发者选项，或右键以管理员身份运行终端 |
| 4 | 手动修改已创建的符号链接指向 | 下次运行 skill 时会自动检测目标路径不符，自动删除旧链接并重建正确链接 | 直接重新运行本 skill 即可 |
| 5 | 在 `~/.agents/skills/` 被删除后不处理仍运行 skill | Step 2 源目录不存在检测会终止，但目标目录中的失效链接不会自动清除 | 先运行 skill 触发 CHECKPOINT，选 `y` 清除失效链接 |
| 6 | 对 `~/.claude/skills/` 中非本 skill 管理的符号链接执行失效检测 | Step 3 会检测所有符号链接，包括你手动创建或其他工具创建的链接，可能误列为"失效" | 在 CHECKPOINT 仔细核对列表再选 `y`，不确定则选 `n` |

---

## 全局使用说明

如需在所有项目会话中使用本 skill（而非仅在加载了 `unipus-devops-plugin` 的会话中）：

1. 将本目录复制到 `~/.agents/skills/sync-agent-skills/`
2. 在任意已加载本 skill 的会话中输入「同步 skills」
3. skill 会将 `sync-agent-skills` 自身也链接到目标目录，之后全局生效
