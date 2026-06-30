---
name: sync-agent-skills
version: 1.2.0
description: 将 skill 源目录以符号链接同步到各 AI 工具的 skills 目录，维护单一 source of truth。默认 source：~/.agents/skills/，默认 targets：~/.claude/skills/ 和 ~/.kiro/skills/。支持自定义：source=<路径> target=<路径1,路径2,...>。触发词：同步 skills、sync agent skills、链接 skills、更新 skill 链接、sync-agent-skills、link skills、update skill symlinks。不适用：仅需查看已有链接状态而不修改时，无需触发本 skill。
---

# sync-agent-skills

将 skill 源目录中的所有 skill 子目录以符号链接形式分发到各 AI 工具的 skills 目录，使用户只需维护一个 source of truth。

---

## Step 0 — 参数解析与路径验证

读取用户指令，提取 `source=` 和 `target=` 参数；若使用自定义路径，同步执行边界检查。

### 0.1 参数解析

**Windows PowerShell：**

```powershell
# 默认值
$source    = "$env:USERPROFILE\.agents\skills"
$targets   = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills")
$useCustom = $false

# 从用户消息中提取 source= 和 target= 参数
# 示例："同步 skills source=D:\my-skills target=C:\cursor\skills,C:\windsurf\skills"
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
    Write-Host "    source=<绝对路径>         指定 skill 源目录（默认：~\.agents\skills）"
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
# 示例："同步 skills source=~/my-skills target=~/.cursor/skills,~/.windsurf/skills"
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
    echo "    source=<绝对路径>         指定 skill 源目录（默认：~/.agents/skills）"
    echo "    target=<路径1,路径2,...>  指定一个或多个目标目录（逗号分隔）"
fi
```

### 0.2 自定义路径边界检查（仅 `$useCustom = true` 时执行）

**检查 A — target 父目录不存在：** 收集所有父目录缺失的 target，进入 CHECKPOINT：

🔴 **CHECKPOINT — 目标父目录缺失（继续前必须完成）：**

> 以下目标目录的父目录不存在，无法自动创建符号链接：
> - `<target>`（父目录：`<parent>`）
>
> 是否自动创建缺失的父目录？回复 `y` 全部创建，`n` 跳过这些目标。

- 若回复 `y`（Windows）：`New-Item -ItemType Directory -Path $parentDir -Force | Out-Null`；打印 `✅ 已创建: <parent>`
- 若回复 `y`（Bash）：`mkdir -p "$(dirname "$target")"`；打印 `✅ 已创建: <parent>`
- 若回复 `n`：将这些 target 从 `$targets` 数组移除，打印 `ℹ️  已跳过: <target>`
- 若所有 target 均被跳过：打印 `⛔ 无可用目标目录，操作终止。` 并退出

**检查 B — target 路径是文件（非目录）：** 直接过滤，无需 CHECKPOINT：

```powershell
# Windows
$targets = $targets | Where-Object {
    if (Test-Path $_ -PathType Leaf) {
        Write-Host "❌ $_ 已存在且是文件，已跳过。" -ForegroundColor Red
        $false
    } else { $true }
}
```

```bash
# Bash
filtered=()
for t in "${targets[@]}"; do
    if [ -f "$t" ]; then echo "❌ $t 已存在且是文件，已跳过。"
    else filtered+=("$t"); fi
done
targets=("${filtered[@]}")
```

---

## Step 1 — 权限预检（Windows 专用）

检测当前平台。若为 Windows，执行：

```powershell
$canSymlink = $false
try {
    $testLink   = "$env:TEMP\__symlink_test_$(Get-Random)"
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
    Write-Host "⛔ 权限检测失败，操作终止。" -ForegroundColor Red
    return
}
```

macOS/Linux 无需此步骤，直接进入 Step 2。

---

## Step 2 — 扫描源目录

**Windows PowerShell：**

```powershell
# $source 由 Step 0 赋值；此处兜底仅在 Step 0 未执行时生效
if (-not $source) { $source = "$env:USERPROFILE\.agents\skills" }

if (-not (Test-Path $source)) {
    Write-Host "❌ 源目录不存在: $source" -ForegroundColor Red
    Write-Host "   请先创建该目录并放置 skill 子目录，再运行本 skill。"
    return
}

$skills = Get-ChildItem -Path $source -Directory | Select-Object -ExpandProperty Name

if ($skills.Count -eq 0) {
    Write-Host "⚠️  $source 中没有发现任何 skill 子目录，无需同步。"
    return
}

Write-Host "🔍 发现 $($skills.Count) 个 skill: $($skills -join ', ')"
```

**macOS/Linux Bash：**

```bash
# $source_dir 由 Step 0 赋值；此处兜底仅在 Step 0 未执行时生效
source_dir="${source_dir:-$HOME/.agents/skills}"

if [ ! -d "$source_dir" ]; then
    echo "❌ 源目录不存在: $source_dir"
    echo "   请先创建该目录并放置 skill 子目录，再运行本 skill。"
    return 1
fi

skills=()
while IFS= read -r -d '' d; do
    skills+=("$(basename "$d")")
done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d -print0)

if [ ${#skills[@]} -eq 0 ]; then
    echo "⚠️  $source_dir 中没有发现任何 skill 子目录，无需同步。"
    return 0
fi

echo "🔍 发现 ${#skills[@]} 个 skill: ${skills[*]}"
```

---

## Step 3 — 创建符号链接

`$targets` 由 Step 0 赋值（默认：`~/.claude/skills/` 和 `~/.kiro/skills/`）。对每个目标目录逐一处理：父目录不存在则静默跳过（默认 targets）；自动创建目标目录本身；链接不存在则新建，已存在但目标路径不符则自动更新，目标路径一致则跳过，非符号链接则警告。

**Windows PowerShell：**

```powershell
# $targets 由 Step 0 赋值；此处兜底仅在 Step 0 未执行时生效
if (-not $targets) {
    $targets = @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.kiro\skills")
}

$created = 0; $skipped = 0; $warned = 0

foreach ($target in $targets) {
    $parentDir = Split-Path $target -Parent
    if (-not (Test-Path $parentDir)) {
        Write-Host "ℹ️  $parentDir 不存在，已跳过"
        continue
    }
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
            $cur = (Get-Item $dest).Target
            if ($cur -ne $src) {
                Remove-Item $dest -Force
                New-Item -ItemType SymbolicLink -Path $dest -Target $src | Out-Null
                Write-Host "🔄 更新链接: $skill ($cur → $src)"
                $created++
            } else {
                Write-Host "✔  已是最新，跳过: $skill"
                $skipped++
            }
        } else {
            Write-Host "⚠️  $dest 已存在且非符号链接，跳过。修复：Remove-Item '$dest' -Recurse -Force" -ForegroundColor Yellow
            $warned++
        }
    }
}
```

**macOS/Linux Bash：**

```bash
# targets 由 Step 0 赋值；此处兜底仅在 Step 0 未执行时生效
if [ ${#targets[@]} -eq 0 ]; then
    targets=("$HOME/.claude/skills" "$HOME/.kiro/skills")
fi
created=0; skipped=0; warned=0

for target in "${targets[@]}"; do
    parent=$(dirname "$target")
    if [ ! -d "$parent" ]; then
        echo "ℹ️  $parent 不存在，已跳过"
        continue
    fi
    mkdir -p "$target"
    for skill in "${skills[@]}"; do
        dest="$target/$skill"
        src="$source_dir/$skill"
        if [ ! -e "$dest" ] && [ ! -L "$dest" ]; then
            ln -s "$src" "$dest"
            echo "✅ 新建链接: $skill → $target/"
            ((created++))
        elif [ -L "$dest" ]; then
            cur=$(readlink "$dest")
            if [ "$cur" != "$src" ]; then
                rm "$dest" && ln -s "$src" "$dest"
                echo "🔄 更新链接: $skill ($cur → $src)"
                ((created++))
            else
                echo "✔  已是最新，跳过: $skill"
                ((skipped++))
            fi
        else
            echo "⚠️  $dest 已存在且非符号链接，跳过。修复：rm -rf '$dest'"
            ((warned++))
        fi
    done
done
```

---

## Step 4 — 检测失效链接

扫描所有目标目录中的符号链接，收集指向已不存在路径的链接：

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
if ($dangling.Count -eq 0) { Write-Host "✅ 未检测到失效链接" }
else {
    Write-Host "⚠️  检测到 $($dangling.Count) 条失效链接："
    $dangling | ForEach-Object { Write-Host "   $($_.Path) → $($_.Target)" }
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
if [ ${#dangling[@]} -eq 0 ]; then echo "✅ 未检测到失效链接"
else
    echo "⚠️  检测到 ${#dangling[@]} 条失效链接："
    for link in "${dangling[@]}"; do echo "   $link"; done
fi
```

---

## Step 5 — 汇总 & CHECKPOINT 处理失效链接

打印汇总：

```
──────────────────────────────────────────
汇总: 新建 X 条，跳过 X 条，警告 X 条，失效 X 条
```

若 `dangling` 非空：

🔴 **CHECKPOINT — 失效链接处理（继续前必须完成）：**

> 以上 X 条失效链接指向已不存在的目录，是否删除？
> 回复 `y` 确认删除，`n` 跳过留待手动处理。

- 若回复 `y`（Windows）：`foreach ($item in $dangling) { Remove-Item $item.Path -Force; Write-Host "🗑️ 已删除: $($item.Path)" }`
- 若回复 `y`（Bash）：`for link in "${dangling[@]}"; do rm "$link"; echo "🗑️ 已删除: $link"; done`
- 若回复 `n`：`ℹ️  已跳过，失效链接保留原位。清理方式：Windows → Remove-Item <path> -Force；macOS/Linux → rm <path>`

---

## ⛔ 反例与黑名单

| # | 禁止行为 | 后果 | 正确做法 |
|---|---------|------|---------|
| 1 | 在源目录中直接放置文件（非子目录） | 被 `find -type d` 跳过，skill 不会被同步 | 每个 skill 必须是独立子目录，如 `my-skill/SKILL.md` |
| 2 | 在目标目录手动创建与 skill 同名的普通目录 | 被检测为"非符号链接"，打印警告并永远跳过 | 先删除该目录（`rm -rf` / `Remove-Item -Recurse`），再运行 skill |
| 3 | Windows 下未开启开发者模式也非管理员 | Step 1 权限检测失败，skill 终止 | 开启设置 → 隐私和安全 → 开发者选项，或以管理员身份运行终端 |
| 4 | 直接编辑目标目录（`~/.claude/skills/xxx`）中的文件 | 实际修改的是 source 中的原始文件（符号链接穿透），符合预期；但若误删链接则 source 文件不受影响 | 明确知道这一点即可；若要独立副本请改用 `cp -r` 复制而非 symlink |
| 5 | source 目录被删除后不清理即再次运行 | Step 2 正常终止，但目标目录中的失效链接不会自动清除 | 运行 skill 触发 Step 5 CHECKPOINT，回复 `y` 清除失效链接 |
| 6 | CHECKPOINT 确认删除时未仔细核对失效链接列表 | Step 4 扫描所有符号链接，含手动创建或其他工具管理的链接，可能误删 | 回复 `y` 前逐条核对路径；不确定的选 `n` 留待手动处理 |

---

## 全局使用说明

如需在所有项目会话中使用本 skill（而非仅在加载了 `unipus-devops-plugin` 的会话中）：

1. 将本目录复制到 `~/.agents/skills/sync-agent-skills/`
2. 在任意已加载本 skill 的会话中输入「同步 skills」
3. skill 会将 `sync-agent-skills` 自身链接到目标目录，之后全局生效
