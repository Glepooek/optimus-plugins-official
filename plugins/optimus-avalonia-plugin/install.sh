#!/usr/bin/env bash
# Avalonia Skills Installer — optimus-avalonia-plugin 版
#
# 把本插件 skills/ 下的每个 skill 符号链接到各 agent harness 的用户级 skill 目录，
# 使 skill 在没有插件机制的 harness（如 Kiro）里也能被发现。
#
# 与上游 linuxdevel/Avalonia-skills 的 install.sh 有三处实质差异，改动理由如下：
#
#   1. 不下载任何东西。上游把仓库拉到 ~/.local/share/avalonia-skills 再链接过去，
#      因为它是「一个脚本分发一个仓库」。本脚本就住在插件里，源即 ${PLUGIN_ROOT}/skills
#      —— 插件已是单一真源，再引入一个中性存放点会造出第二真源（AGENTS.md 的
#      「单一真源」原则）。因此本脚本必须从插件 checkout 内运行，不支持 curl | bash。
#
#   2. harness 目录改为 claude / codex / kiro 三家（上游是 opencode / claude / agents）。
#      ⚠️ Codex 的用户级目录实测是 ~/.codex/skills，**不是** ~/.agents/skills ——
#      后者只在「工作目录相对」位置被 Codex 发现（仓库根作工作目录时因此有效，
#      这也是仓库内 .agents/skills 镜像能工作的原因）。取证：codex-cli 0.154.0，
#      隔离 CODEX_HOME 后跑 `codex debug prompt-input`，六处候选路径各埋一个带唯一
#      名字的 SKILL.md，只有 $CODEX_HOME/skills 与 <cwd>/.agents/skills 被报告。
#
#   3. 链接前后各加一道符号链接能力探测/复核。原因见下方 symlink_works()：
#      Windows 上 ln -s 对目录会**静默退化成复制**（退出码 0、无告警），
#      那样装出来的就不是链接而是旧副本，且此后插件更新不会生效。
#
# Usage:
#   ./install.sh                    # 安装到 ~/.claude/skills、~/.codex/skills、~/.kiro/skills
#   ./install.sh --target DIR       # 额外安装到 DIR（可重复）
#   ./install.sh --help

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SKILLS_SOURCE="${PLUGIN_ROOT}/skills"

# 已知 agent 的用户级 skill 目录。三家都会被创建（不存在时），
# 因为本脚本的用途正是让 skill 在「还没装插件机制」的 harness 里也能被发现。
AGENT_DIRS=(
    "${HOME}/.claude/skills"    # Claude Code
    "${HOME}/.codex/skills"     # Codex CLI
    "${HOME}/.kiro/skills"      # Kiro
)

# ── Helpers ───────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { printf "${BLUE}  •${RESET} %s\n" "$*"; }
success() { printf "${GREEN}  ✓${RESET} %s\n" "$*"; }
warn()    { printf "${YELLOW}  !${RESET} %s\n" "$*"; }
error()   { printf "${RED}  ✗${RESET} %s\n" "$*" >&2; }
header()  { printf "\n${BOLD}%s${RESET}\n" "$*"; }

# 让 ln -s 走 Windows 原生符号链接。默认 MSYS 在权限不足时**不报错**，
# 而是退化成把目标复制一份；nativestrict 则让它在建不了链接时直接失败，
# 把静默失效转成可检出的报错。非 MSYS 平台该变量无副作用。
export MSYS=winsymlinks:nativestrict

# 探测本机能否创建真符号链接。**不在安装中途才发现** —— 那会留下
# 「前几个是链接、后几个是复制」的半成品状态，且退出码仍是 0。
# 返回 0 = 可以，1 = 不可以。
symlink_works() {
    local probe_dir probe_link
    probe_dir="$(mktemp -d)"
    mkdir -p "${probe_dir}/src"
    ln -s "${probe_dir}/src" "${probe_dir}/link" 2>/dev/null || true
    local ok=1
    if [[ -L "${probe_dir}/link" ]]; then ok=0; fi
    rm -rf "${probe_dir}"
    return $ok
}

# 两个路径是否指向同一实体（比对规范化后的绝对路径）。
# 直接比较 readlink 的字符串不够稳：同一目录在 MSYS 形态与 Windows 形态下
# 字符串不同，却指向同一处。
same_target() {
    local a b
    a="$(cd "$1" 2>/dev/null && pwd -P)" || return 1
    b="$(cd "$2" 2>/dev/null && pwd -P)" || return 1
    [[ "$a" == "$b" ]]
}

# ── Argument parsing ─────────────────────────────────────────────────────────

EXTRA_TARGETS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            target="${2:-}"
            if [[ -z "$target" ]]; then
                error "--target requires a directory path"
                exit 1
            fi
            # 拒绝文档里复制粘贴的占位符——上游踩过这个坑，代价是往
            # 「/path/to/...」这种目录里装一堆链接，且当时无人察觉。
            case "$target" in
                /path/to/*|/path/*|"<"*">"*|/your/*|./path/*)
                    error "'--target $target' 看起来是文档里的占位符，不是真实路径。"
                    error "请传一个真实目录，例如：--target \"\$HOME/my-agent/skills\""
                    exit 1
                    ;;
            esac
            EXTRA_TARGETS+=("$target")
            shift 2
            ;;
        --help|-h)
            printf "Usage: install.sh [--target DIR]...\n"
            printf "  把 skills/ 下的每个 skill 链接到各 agent 的用户级 skill 目录。\n"
            printf "  源（单一真源）：%s\n" "${SKILLS_SOURCE}"
            printf "  默认目标：%s\n" "${AGENT_DIRS[*]}"
            printf "  --target 可重复，用于额外目标目录。\n"
            exit 0
            ;;
        *)
            error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# ── 前置校验：源与能力 ────────────────────────────────────────────────────────

header "Avalonia Skills Installer"

# 源必须是插件 checkout（脚本被单独拷出来跑时，源就没了——要显式报错，
# 不要静默装出空结果）。
if [[ ! -d "${SKILLS_SOURCE}" ]]; then
    error "找不到 skills 源目录：${SKILLS_SOURCE}"
    error "本脚本必须从插件 checkout 内运行（它把插件目录当单一真源，不下载任何东西）。"
    exit 1
fi

# 只挑「含 SKILL.md 的目录」作为 skill。这条判据同时排除了非 skill 目录与
# 嵌套子 skill（如 avalonia-controls/data-display）——嵌套项随其父目录
# 一起被链接过去，不单独处理。**这是刻意的**：扁平化会重命名用户可见 skill，
# 属独立议题，不在本脚本范围内。
SKILL_DIRS=()
for d in "${SKILLS_SOURCE}"/*/; do
    [[ -f "${d}SKILL.md" ]] && SKILL_DIRS+=("${d%/}")
done

if [[ ${#SKILL_DIRS[@]} -eq 0 ]]; then
    error "在 ${SKILLS_SOURCE} 下没找到任何含 SKILL.md 的目录。"
    exit 1
fi

if ! symlink_works; then
    error "本机无法创建符号链接——ln -s 会静默退化成复制，装出来的将是旧副本，"
    error "且此后插件更新不会反映到各 harness。已中止，未做任何改动。"
    error ""
    error "常见解法（按平台）："
    error "  Windows：开启「开发者模式」（设置 → 隐私和安全性 → 开发者选项），"
    error "           或以管理员身份运行；本脚本已设 MSYS=winsymlinks:nativestrict 强制暴露失败。"
    error "  Linux/macOS：检查目标所在文件系统是否支持符号链接（FAT/exFAT 不支持）。"
    exit 1
fi
info "符号链接能力：可用"

# ── 解析目标目录 ──────────────────────────────────────────────────────────────

header "Installing skills"

TARGET_DIRS=("${AGENT_DIRS[@]}")
for t in "${EXTRA_TARGETS[@]:-}"; do
    [[ -n "$t" ]] && TARGET_DIRS+=("$t")
done

installed=0
skipped=0
backed_up=0
failures=()

for agent_dir in "${TARGET_DIRS[@]}"; do
    # 三家目标目录都按需创建。上游只装进「已存在」的目录，本脚本不这么做：
    # 用户显式点名了 claude/codex/kiro，缺目录时静默跳过会让人以为装好了。
    if [[ ! -d "$agent_dir" ]]; then
        mkdir -p "$agent_dir"
        info "创建目标目录：$agent_dir"
    fi

    for src in "${SKILL_DIRS[@]}"; do
        name="$(basename "$src")"
        link="${agent_dir}/${name}"

        if [[ -L "$link" ]]; then
            if same_target "$link" "$src"; then
                skipped=$((skipped + 1))
                continue
            fi
            info "重指向已存在的链接：$link"
            ln -sfn "$src" "$link"
        elif [[ -d "$link" ]]; then
            # 实体目录占位——先备份再链接，绝不静默覆盖用户的东西。
            backup="${link}.backup.$(date +%Y%m%d%H%M%S)"
            warn "已存在实体目录，备份到：$backup"
            mv "$link" "$backup"
            ln -sfn "$src" "$link"
            backed_up=$((backed_up + 1))
        else
            ln -sfn "$src" "$link"
        fi

        # 复核：这一次创建真的产出了符号链接、且能解析到 SKILL.md。
        # 不做这一步的话，退化成的复制会一路绿灯到「安装完成」。
        if [[ ! -L "$link" ]]; then
            failures+=("$link 不是符号链接（退化成了复制）")
        elif [[ ! -f "$link/SKILL.md" ]]; then
            failures+=("$link 是悬空链接，解析不到 SKILL.md")
        else
            installed=$((installed + 1))
        fi
    done
    success "已处理：$agent_dir"
done

# ── Summary ───────────────────────────────────────────────────────────────────

header "Done"

printf "\n"
printf "  ${BOLD}Skills:${RESET}         %d 个（每个 skill 在每个目标目录各一条链接）\n" "${#SKILL_DIRS[@]}"
printf "  ${BOLD}目标目录:${RESET}       %d 个\n" "${#TARGET_DIRS[@]}"
printf "  ${BOLD}新建链接:${RESET}       %d\n" "$installed"
if [[ $skipped -gt 0 ]]; then
    printf "  ${BOLD}已是当前指向:${RESET}   %d\n" "$skipped"
fi
if [[ $backed_up -gt 0 ]]; then
    printf "  ${BOLD}备份的实体目录:${RESET} %d（后缀 .backup.<时间戳>）\n" "$backed_up"
fi
printf "  ${BOLD}单一真源:${RESET}       %s\n" "${SKILLS_SOURCE}"
printf "\n"

if [[ ${#failures[@]} -gt 0 ]]; then
    error "有 ${#failures[@]} 处未通过复核："
    for f in "${failures[@]}"; do
        error "  - $f"
    done
    exit 1
fi

printf "  改动插件内的 skill 即刻在上述所有位置生效，无需重跑本脚本。\n"
printf "  卸载：删除上述目录里指向 %s 的链接即可。\n" "${SKILLS_SOURCE}"
printf "\n"
