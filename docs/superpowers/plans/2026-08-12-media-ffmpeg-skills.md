# optimus-media-plugin（ffmpeg 音视频处理 Skill 集）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新建 `optimus-media-plugin` 插件，提供四个基于 ffmpeg/ffprobe CLI 的独立 skill（分析、分辨率转换、压缩、片段截取），供非专业音视频开发者通过自然语言触发常见操作。

**Architecture:** 纯 SKILL.md 文档指导 + 直接调用系统 ffmpeg/ffprobe 命令，不封装任何 Python/Shell 脚本。四个 skill 共享同一组参考文档（`media-ffmpeg-common/` 目录，无 SKILL.md，不作为可触发 skill 注册），分别覆盖安装配置、CLI 参数速查、环境检测与报错处理。

**Tech Stack:** Markdown（SKILL.md/README.md/CHANGELOG.md/参考文档）、ffmpeg/ffprobe CLI（用户本机环境，非本仓库代码依赖）、JSON（marketplace.json 插件清单）。

## Global Constraints

- 每个 skill 目录须包含 `SKILL.md`、`CHANGELOG.md`、`README.md` 三个文件（`plugins/*/skills/` 下新增 skill 强制要求 README，参见 `.claude/rules/skill-authoring.md`）。
- SKILL.md frontmatter 只允许 `name`/`description`/`license`/`allowed-tools`/`metadata`/`compatibility` 六个顶层字段（Agent Skills 开放规范）。
- `metadata.version` 初始为 `"1.0.0"`，`metadata.author` 统一为 `desktop client team`，`metadata.category` 四个 skill 均为 `tool`。
- `compatibility` 字段必须据实描述：需要用户本机安装 ffmpeg/ffprobe 并加入 PATH。
- `allowed-tools` 只写 `Bash`（四个 skill 都只调用系统命令，不读写代码文件、不用 Read/Write/Glob/Grep）。
- CHANGELOG.md 初始版本条目为 `## [1.0.0] - 2026-08-12`。
- README.md 必须按 `.claude/rules/skill-authoring.md` 固定章节顺序：标题与元信息 → 所处层级 → 触发词 → 业务逻辑流程图 → 产出物数据流 → Skill 依赖关系图，全部用 ASCII box-drawing 字符绘制，不用 Mermaid。
- `media-ffmpeg-common/` 目录不放 SKILL.md，不算作独立 skill，因此不需要 README.md/CHANGELOG.md。
- 本仓库没有 `plugin.json` 文件——插件仅通过根 `.claude-plugin/marketplace.json` 的 `plugins` 数组声明一条 `{name, source, description}`，新插件同理，不要为它单独创建 `plugin.json`。
- 新增插件属于 `plugins/` 下新增功能，`.claude-plugin/marketplace.json` 的顶层 `"version"` 字段必须做 **Minor** 升级（当前 `8.6.4` → `8.7.0`）。
- 编辑 SKILL.md/CHANGELOG.md/README.md 时不做无关格式化改动（不增删空行、不调整缩进、不做表格对齐）。
- 提交必须使用 `commit-cc-plugin` skill，不手动执行 git 工作流。

---

### Task 1: 共享参考文档 media-ffmpeg-common

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-ffmpeg-common/INSTALL.md`
- Create: `plugins/optimus-media-plugin/skills/media-ffmpeg-common/CLI-REFERENCE.md`
- Create: `plugins/optimus-media-plugin/skills/media-ffmpeg-common/REFERENCE.md`

**Interfaces:**
- Consumes: 无（本任务是四个 skill 的公共依赖，先于 Task 2-5 完成）
- Produces: 三份文档的相对路径，供 Task 2-5 的 SKILL.md 用 `../media-ffmpeg-common/<文件名>` 引用：
  - `../media-ffmpeg-common/INSTALL.md`（安装与环境变量配置）
  - `../media-ffmpeg-common/CLI-REFERENCE.md`（参数速查表）
  - `../media-ffmpeg-common/REFERENCE.md`（环境检测命令 + 通用报错处理表）

- [ ] **Step 1: 创建目录并写入 INSTALL.md**

```markdown
# ffmpeg / ffprobe 安装与环境变量配置

本仓库的 media-* 系列 skill（media-analyze/media-resize/media-compress/media-trim）依赖用户本机已安装 ffmpeg 与 ffprobe，并加入系统 PATH。以下按平台给出安装步骤。

## Windows

**方式一：winget（推荐）**

```powershell
winget install ffmpeg
```

安装完成后重新打开终端，`ffmpeg`/`ffprobe` 命令即可直接使用（winget 会自动配置 PATH）。

**方式二：手动下载全量构建**

1. 从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 或 [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) 下载 `ffmpeg-release-full.7z`
2. 解压到固定目录，如 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 加入系统 PATH：
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑" → "新建"，填入 `C:\ffmpeg\bin`
   - 确定保存后，重新打开终端生效

## macOS

```bash
brew install ffmpeg
```

## Linux

```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# Fedora/RHEL
sudo dnf install ffmpeg
```

## 验证安装

```bash
ffmpeg -version
ffprobe -version
```

两个命令均应输出版本号（如 `ffmpeg version 6.1...`）。若提示命令不存在，说明安装未完成或 PATH 未生效，请重新打开终端或检查上述步骤。
```

- [ ] **Step 2: 写入 CLI-REFERENCE.md**

```markdown
# ffmpeg 命令行参数速查

仅覆盖 media-analyze/media-resize/media-compress/media-trim 四个 skill 实际用到的参数，不是 ffmpeg 完整参数手册。

| 参数 | 用途 | 使用场景 |
|---|---|---|
| `-i <file>` | 指定输入文件 | 全部 |
| `-c:v <编码器>` | 指定视频编码器，如 `libx264` | media-compress、media-trim 精确模式 |
| `-c:a <编码器>` | 指定音频编码器，如 `aac` | media-compress、media-trim 精确模式 |
| `-crf <0-51>` | 画质因子，数值越小画质越好、文件越大；0 为无损，51 为最差 | media-compress |
| `-preset <速度档位>` | 编码速度与压缩率的权衡：`ultrafast`/`fast`/`medium`/`slow`/`veryslow`，越慢压缩率越高 | media-compress |
| `-vf scale=W:H` | 视频分辨率缩放；`W`或`H`填 `-2` 表示按另一边等比例计算并保证结果为偶数 | media-resize |
| `-ss <时间点>` | 起始时间点，格式 `HH:MM:SS` 或秒数；放在 `-i` 之前是快速的输入端 seek（对齐到最近关键帧），放在 `-i` 之后是精确的输出端 seek（帧精确但慢） | media-trim |
| `-to <时间点>` | 结束时间点，格式同 `-ss` | media-trim |
| `-c copy` | 流复制，不重新编码，速度极快 | media-trim 快速模式、media-resize 音频透传（`-c:a copy`） |
| `-y` | 覆盖已存在的输出文件，不交互询问 | 全部 |
```

- [ ] **Step 3: 写入 REFERENCE.md**

```markdown
# 环境检测与通用报错处理

## 环境检测

执行任何 media-* skill 的命令前，先确认 ffmpeg/ffprobe 已安装：

```bash
ffmpeg -version && ffprobe -version
```

若提示命令不存在，引导用户参考 `INSTALL.md` 完成安装，不要尝试自动安装。

## 通用报错处理表

| 错误现象 | 原因 | 处理建议 |
|---|---|---|
| `Unknown encoder 'libx264'` | ffmpeg 编译时未包含该编码器 | 执行 `ffmpeg -encoders \| grep x264` 确认，提示用户更换包含完整编码器的发行版（如 Windows 用 gyan.dev 的 full 构建） |
| `Permission denied` | 输出路径无写权限，或目标文件正被其他程序（如播放器）占用 | 确认输出目录存在且当前用户有写权限；关闭占用该文件的程序后重试 |
| `Invalid data found when processing input` | 输入文件已损坏，或格式/编码不受当前 ffmpeg 构建支持 | 先用 media-analyze 对应的 `ffprobe` 命令探测确认文件是否可读 |
| 命令挂起无输出，等待用户输入 | ffmpeg 检测到输出文件已存在，交互式询问是否覆盖 | 命令中加入 `-y`（覆盖）或 `-n`（不覆盖，存在则跳过） |
```

- [ ] **Step 4: 确认三份文件内容与设计文档一致**

对照 `docs/superpowers/specs/2026-08-12-media-ffmpeg-skills-design.md` 的"共享参考文档"章节，逐条核对表格内容（参数列表、报错表条目）无遗漏、无新增内容。

- [ ] **Step 5: 提交**

不在此单独提交——本任务产出的三份文档与 Task 2-5 的 SKILL.md 属于同一逻辑任务（新增插件），一并在 Task 6 最后统一提交。

---

### Task 2: media-analyze skill

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-analyze/SKILL.md`
- Create: `plugins/optimus-media-plugin/skills/media-analyze/CHANGELOG.md`
- Create: `plugins/optimus-media-plugin/skills/media-analyze/README.md`

**Interfaces:**
- Consumes: Task 1 产出的 `../media-ffmpeg-common/REFERENCE.md`（环境检测+报错处理）
- Produces: 无下游 skill 依赖，但其表格输出格式（时长字段）被 Task 5（media-trim）的失败处理章节引用："参考 media-analyze 输出的时长字段"

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: media-analyze
description: Use when user wants to inspect a media file's codec, resolution, bitrate, frame rate, or duration — 分析视频、分析音频、查看编码格式、查看分辨率码率帧率、这个视频什么编码、ffprobe。Not for editing, converting, compressing, or trimming media.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg/ffprobe 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频信息分析

## 功能概述

分析单个音视频文件，输出容器格式、视频/音频编码、分辨率、帧率、码率、时长、文件大小。仅支持单文件分析，不支持批量目录扫描。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffprobe` 可用。若不可用，引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装。

### Step 2：执行分析

```bash
ffprobe -v quiet -print_format json -show_format -show_streams <input>
```

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

### Step 3：整理输出

解析上一步的 JSON 输出，提取以下字段整理为表格展示给用户，不直接把原始 JSON 贴给用户：

| 项目 | 值 |
|---|---|
| 容器格式 | 从 `format.format_name` 提取 |
| 视频编码 | 从视频流 `codec_name` 提取 |
| 分辨率 | 从视频流 `width`x`height` 提取 |
| 帧率 | 从视频流 `r_frame_rate` 计算（如 `30000/1001` → `29.97 fps`） |
| 视频码率 | 从视频流或 `format.bit_rate` 提取，换算为 kbps |
| 音频编码 | 从音频流 `codec_name` 提取 |
| 音频码率 | 从音频流 `bit_rate` 提取，换算为 kbps |
| 时长 | 从 `format.duration` 提取，格式化为 `HH:MM:SS` |
| 文件大小 | 从 `format.size` 提取，换算为可读单位（KB/MB/GB） |

无视频流（纯音频文件）时省略视频相关行；无音频流同理。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。
```

- [ ] **Step 2: 写入 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-08-12

### Added
- 新增 media-analyze skill：基于 ffprobe 分析音视频容器格式、编码、分辨率、帧率、码率、时长、文件大小，结构化表格输出
```

- [ ] **Step 3: 写入 README.md**

```markdown
# media-analyze

> 版本：1.0.0 | 分类：tool

分析单个音视频文件的容器格式、编解码、分辨率、帧率、码率、时长等信息，结构化表格输出。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze（本 skill）、media-resize、media-compress、media-trim
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

分析视频、分析音频、查看编码格式、查看分辨率码率帧率、这个视频什么编码、ffprobe。

## 业务逻辑流程图

```
Step 1  确认 ffprobe 环境可用
   ↓
Step 2  执行 ffprobe -show_format -show_streams
   ↓
Step 3  解析 JSON，整理为结构化表格输出
```

## 产出物数据流

音视频文件路径 → 本 skill → 结构化信息表格（容器/编码/分辨率/帧率/码率/时长/大小）→ 人工阅读；时长字段被 media-trim 的失败处理引用（核对起始时间是否超过总时长）。

## Skill 依赖关系图

```
用户 ──触发──▶ media-analyze ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                    └──▶ media-ffmpeg-common/CLI-REFERENCE.md
```

不被其他 skill 调度；`media-trim` 在失败处理中提示用户参考本 skill 的时长输出，但不构成调用依赖。
```

- [ ] **Step 4: 检查 frontmatter 六字段合规**

确认 SKILL.md frontmatter 只包含 `name`/`description`/`metadata`/`compatibility`/`allowed-tools` 五个字段（`license` 未使用，允许省略），无其他顶层字段。

- [ ] **Step 5: 提交**

不在此单独提交，随 Task 6 一并提交。

---

### Task 3: media-resize skill

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-resize/SKILL.md`
- Create: `plugins/optimus-media-plugin/skills/media-resize/CHANGELOG.md`
- Create: `plugins/optimus-media-plugin/skills/media-resize/README.md`

**Interfaces:**
- Consumes: Task 1 产出的 `../media-ffmpeg-common/REFERENCE.md`、`../media-ffmpeg-common/CLI-REFERENCE.md`、`../media-ffmpeg-common/INSTALL.md`
- Produces: 无下游依赖

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: media-resize
description: Use when user wants to change a video's resolution — 分辨率转换、1080p转720p、改分辨率、缩放视频、视频转清晰度。Not for compression at the same resolution, trimming, or codec/format analysis.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 视频分辨率转换

## 功能概述

将单个视频文件转换到指定分辨率（如 1080p → 720p），音频流直接透传不重新编码。仅支持单文件，输出路径必须由用户或 Claude 显式指定，不做隐式命名推导。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径

向用户确认或由 Claude 根据上下文给出明确的输出文件路径，不得省略 `-o`/输出参数直接执行。

### Step 3：执行转换

```bash
ffmpeg -i <input> -vf scale=-2:<目标高度> -c:a copy <output>
```

- `-2` 表示按另一边等比例自动计算并保证结果为偶数，避免用户口头描述"转 720p"时还需手动换算对应宽度
- 常见目标：1080p→720p 用 `scale=-2:720`；720p→480p 用 `scale=-2:480`
- 若用户直接给出目标宽高（而非标准分辨率名称），改为 `scale=<宽>:<高>`
- `-c:a copy`：分辨率转换不涉及音频处理，音频流直接透传，避免不必要的有损重新编码

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。
```

- [ ] **Step 2: 写入 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-08-12

### Added
- 新增 media-resize skill：基于 ffmpeg `-vf scale` 实现视频分辨率转换，音频流透传不重新编码
```

- [ ] **Step 3: 写入 README.md**

```markdown
# media-resize

> 版本：1.0.0 | 分类：tool

将视频文件转换到指定分辨率（如 1080p 转 720p），音频流透传不重新编码。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize（本 skill）、media-compress、media-trim
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

分辨率转换、1080p转720p、改分辨率、缩放视频、视频转清晰度。

## 业务逻辑流程图

```
Step 1  确认 ffmpeg 环境可用
   ↓
Step 2  确认输出路径（必须显式指定）
   ↓
Step 3  执行 ffmpeg -vf scale=-2:H -c:a copy
```

## 产出物数据流

输入视频 + 目标分辨率 → 本 skill → 指定路径下的新分辨率视频文件 → 人工接手。

## Skill 依赖关系图

```
用户 ──触发──▶ media-resize ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                  └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                  └──▶ media-ffmpeg-common/INSTALL.md
```

不被其他 skill 调度，无上下游依赖，独立使用。
```

- [ ] **Step 4: 检查 frontmatter 六字段合规**

同 Task 2 Step 4 的检查方式。

- [ ] **Step 5: 提交**

不在此单独提交，随 Task 6 一并提交。

---

### Task 4: media-compress skill

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-compress/SKILL.md`
- Create: `plugins/optimus-media-plugin/skills/media-compress/CHANGELOG.md`
- Create: `plugins/optimus-media-plugin/skills/media-compress/README.md`

**Interfaces:**
- Consumes: Task 1 产出的三份共享文档
- Produces: 无下游依赖

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: media-compress
description: Use when user wants to reduce a media file's size while keeping the same resolution — 压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质。Not for resolution changes, clip trimming, or pure codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频压缩

## 功能概述

在不改变分辨率的前提下压缩单个音视频文件体积。仅支持 CRF（画质因子）模式，不支持"压缩到指定文件大小"的目标码率模式——后者需要二次编码估算码率，复杂度与当前定位不匹配。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径

向用户确认或根据上下文给出明确的输出文件路径。

### Step 3：确定 CRF 取值

默认 CRF 23（视觉无损与体积的常见平衡点）。根据用户口语化描述调整：

| 用户描述 | CRF 取值 |
|---|---|
| 画质优先 / 画质别损失太多 | 18-20 |
| 默认 / 没有特殊要求 | 23 |
| 体积优先 / 压缩狠一点 | 26-28 |

### Step 4：执行压缩

```bash
ffmpeg -i <input> -c:v libx264 -crf <取值> -preset medium -c:a aac -b:a 128k <output>
```

`-preset medium` 是编码速度与压缩率的常见平衡点，用户明确要求"更快"可改为 `fast`，要求"压缩率更高不介意慢"可改为 `slow`。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

参见 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表。
```

- [ ] **Step 2: 写入 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-08-12

### Added
- 新增 media-compress skill：基于 ffmpeg CRF 模式压缩音视频体积，提供口语化描述到 CRF 数值的映射表
```

- [ ] **Step 3: 写入 README.md**

```markdown
# media-compress

> 版本：1.0.0 | 分类：tool

在不改变分辨率的前提下压缩音视频文件体积，使用 CRF 画质因子控制压缩程度。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress（本 skill）、media-trim
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质。

## 业务逻辑流程图

```
Step 1  确认 ffmpeg 环境可用
   ↓
Step 2  确认输出路径（必须显式指定）
   ↓
Step 3  按用户描述映射 CRF 取值
   ↓
Step 4  执行 ffmpeg -crf <取值> -preset medium
```

## 产出物数据流

输入文件 + 画质偏好描述 → 本 skill → 指定路径下体积更小的音视频文件 → 人工接手。

## Skill 依赖关系图

```
用户 ──触发──▶ media-compress ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                    └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                    └──▶ media-ffmpeg-common/INSTALL.md
```

不被其他 skill 调度，无上下游依赖，独立使用。
```

- [ ] **Step 4: 检查 frontmatter 六字段合规**

同 Task 2 Step 4 的检查方式。

- [ ] **Step 5: 提交**

不在此单独提交，随 Task 6 一并提交。

---

### Task 5: media-trim skill

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-trim/SKILL.md`
- Create: `plugins/optimus-media-plugin/skills/media-trim/CHANGELOG.md`
- Create: `plugins/optimus-media-plugin/skills/media-trim/README.md`

**Interfaces:**
- Consumes: Task 1 产出的三份共享文档；Task 2 的 media-analyze 输出格式（时长字段，用于失败处理提示文案）
- Produces: 无下游依赖

- [ ] **Step 1: 写入 SKILL.md**

```markdown
---
name: media-trim
description: Use when user wants to cut a specific segment out of a media file — 片段截取、截取视频、剪切一段、掐头去尾、截取某个时间段。Not for resolution changes, compression, or codec/format inspection.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 ffmpeg 并加入 PATH，参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 音视频片段截取

## 功能概述

从单个音视频文件中截取指定时间段。默认使用流复制（`-c copy`）快速截取，速度极快但会对齐到最近关键帧，实际起止时间可能与用户输入相差数百毫秒；如需帧精确的截取，使用重新编码的精确模式。输出路径必须由用户或 Claude 显式指定。

## 使用方法

### Step 1：确认环境

执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令，确认 `ffmpeg` 可用。

### Step 2：确认输出路径与截取模式

向用户确认输出文件路径。默认使用快速模式；仅当用户明确要求"精确到帧"或对截取点精度有要求时，才使用精确模式。

### Step 3：执行截取

**默认模式（快速，流复制）：**

```bash
ffmpeg -ss <start> -to <end> -i <input> -c copy <output>
```

**精确模式（重新编码，帧精确）：**

```bash
ffmpeg -i <input> -ss <start> -to <end> -c:v libx264 -crf 18 -c:a aac <output>
```

⚠️ **注意：`-ss` 参数在 `-i` 前后位置决定截取行为，不是可以随意调换的写法差异。** 放在 `-i` 之前是输入端 seek（快速模式所用），会对齐到最近的关键帧；放在 `-i` 之后是输出端 seek（精确模式所用），帧精确但速度慢很多。两种模式的命令模板中 `-ss`/`-to` 与 `-i` 的相对顺序不可互换。

参数说明见 `../media-ffmpeg-common/CLI-REFERENCE.md`。

## 失败处理

除 `../media-ffmpeg-common/REFERENCE.md` 的通用报错处理表外，本 skill 特有的失败场景：

| 触发条件 | 处理 |
|---|---|
| 起始时间超过视频总时长 | 提示用户核对时间戳，可用 media-analyze skill 先查看视频的准确时长 |
| 快速模式下截取起点画面出现绿屏/花屏 | 说明是因为对齐到了非关键帧附近，建议改用精确模式重新截取 |
```

- [ ] **Step 2: 写入 CHANGELOG.md**

```markdown
# Changelog

## [1.0.0] - 2026-08-12

### Added
- 新增 media-trim skill：基于 ffmpeg `-ss`/`-to` 实现音视频片段截取，默认流复制快速模式，提供帧精确的重新编码模式作为备选
```

- [ ] **Step 3: 写入 README.md**

```markdown
# media-trim

> 版本：1.0.0 | 分类：tool

从音视频文件中截取指定时间段，默认流复制快速截取，提供帧精确的重新编码模式作为备选。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

片段截取、截取视频、剪切一段、掐头去尾、截取某个时间段。

## 业务逻辑流程图

```
Step 1  确认 ffmpeg 环境可用
   ↓
Step 2  确认输出路径与截取模式（默认快速）
   ↓
Step 3  执行截取
         ├─ 快速模式：-ss/-to 在 -i 之前 + -c copy
         └─ 精确模式：-ss/-to 在 -i 之后 + 重新编码
```

## 产出物数据流

输入文件 + 起止时间点 → 本 skill → 指定路径下的截取片段文件 → 人工接手；起始时间超过总时长时提示用户参考 media-analyze 的输出核对时长。

## Skill 依赖关系图

```
用户 ──触发──▶ media-trim ──引用──▶ media-ffmpeg-common/REFERENCE.md
                               └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                               └──▶ media-ffmpeg-common/INSTALL.md
失败处理提示用户参考 media-analyze 的时长输出（非调用依赖）
```
```

- [ ] **Step 4: 检查 frontmatter 六字段合规**

同 Task 2 Step 4 的检查方式。

- [ ] **Step 5: 提交**

不在此单独提交，随 Task 6 一并提交。

---

### Task 6: 注册插件到 marketplace.json 并整体验证

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: Task 1-5 产出的全部文件路径（用于验证插件目录结构完整性）
- Produces: 无（本任务是收尾整合）

- [ ] **Step 1: 编辑 marketplace.json 追加插件条目**

在 `plugins` 数组的 `optimus-mcp-servers` 条目之后追加：

```json
    {
      "name": "optimus-media-plugin",
      "source": "./plugins/optimus-media-plugin",
      "description": "音视频处理工具集：基于 ffmpeg/ffprobe 的音视频编解码分析、分辨率转换、压缩、片段截取"
    }
```

注意 JSON 语法：`optimus-mcp-servers` 条目原有的结尾大括号后需补上逗号。

- [ ] **Step 2: 升级顶层 version 字段**

将 `.claude-plugin/marketplace.json` 第 5 行的 `"version": "8.6.4"` 改为 `"version": "8.7.0"`（新增插件，Minor 升级）。

- [ ] **Step 3: 校验 JSON 语法**

```bash
python -c "import json; json.load(open('.claude-plugin/marketplace.json', encoding='utf-8'))" && echo "JSON 合法"
```

Expected: 输出 `JSON 合法`，无异常抛出。

- [ ] **Step 4: 校验目录结构完整性**

```bash
find plugins/optimus-media-plugin -type f | sort
```

Expected 输出（顺序可能不同，但文件集合应完全一致）：

```
plugins/optimus-media-plugin/skills/media-analyze/CHANGELOG.md
plugins/optimus-media-plugin/skills/media-analyze/README.md
plugins/optimus-media-plugin/skills/media-analyze/SKILL.md
plugins/optimus-media-plugin/skills/media-compress/CHANGELOG.md
plugins/optimus-media-plugin/skills/media-compress/README.md
plugins/optimus-media-plugin/skills/media-compress/SKILL.md
plugins/optimus-media-plugin/skills/media-ffmpeg-common/CLI-REFERENCE.md
plugins/optimus-media-plugin/skills/media-ffmpeg-common/INSTALL.md
plugins/optimus-media-plugin/skills/media-ffmpeg-common/REFERENCE.md
plugins/optimus-media-plugin/skills/media-resize/CHANGELOG.md
plugins/optimus-media-plugin/skills/media-resize/README.md
plugins/optimus-media-plugin/skills/media-resize/SKILL.md
plugins/optimus-media-plugin/skills/media-trim/CHANGELOG.md
plugins/optimus-media-plugin/skills/media-trim/README.md
plugins/optimus-media-plugin/skills/media-trim/SKILL.md
```

- [ ] **Step 5: 校验四个 SKILL.md frontmatter 合法性**

```bash
for f in plugins/optimus-media-plugin/skills/media-analyze/SKILL.md \
         plugins/optimus-media-plugin/skills/media-resize/SKILL.md \
         plugins/optimus-media-plugin/skills/media-compress/SKILL.md \
         plugins/optimus-media-plugin/skills/media-trim/SKILL.md; do
  echo "=== $f ==="
  python -c "
import yaml, sys
with open('$f', encoding='utf-8') as fh:
    content = fh.read()
frontmatter = content.split('---')[1]
data = yaml.safe_load(frontmatter)
allowed = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility'}
extra = set(data.keys()) - allowed
assert not extra, f'非法顶层字段: {extra}'
assert data['metadata']['version'] == '1.0.0'
assert data['metadata']['author'] == 'desktop client team'
assert data['metadata']['category'] == 'tool'
print('OK:', data['name'])
"
done
```

Expected: 四个 skill 均输出 `OK: <name>`，无 AssertionError。

- [ ] **Step 6: 本地测试（需要用户本机已安装 ffmpeg，若未安装则跳过并在计划完成报告中注明）**

```bash
ffmpeg -version >/dev/null 2>&1 && echo "ffmpeg 可用，可执行手动测试" || echo "ffmpeg 未安装，跳过手动测试，仅完成文档交付"
```

若 ffmpeg 可用，执行以下手动验证（对照设计文档"测试方式"章节）：

```bash
ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=5 -shortest test.mp4 -y
ffprobe -v quiet -print_format json -show_format -show_streams test.mp4
ffmpeg -i test.mp4 -vf scale=-2:480 -c:a copy test_480p.mp4 -y
ffprobe -v quiet -print_format json -show_streams test_480p.mp4 | grep -A2 '"width"'
ffmpeg -i test.mp4 -c:v libx264 -crf 28 -preset medium -c:a aac -b:a 128k test_compressed.mp4 -y
ls -la test.mp4 test_compressed.mp4
ffmpeg -ss 00:00:01 -to 00:00:03 -i test.mp4 -c copy test_trim_fast.mp4 -y
ffmpeg -i test.mp4 -ss 00:00:01 -to 00:00:03 -c:v libx264 -crf 18 -c:a aac test_trim_precise.mp4 -y
```

Expected：
- `ffprobe` 输出中 `width=1280, height=720`
- 480p 转换后 `ffprobe` 显示 `width=854, height=480`（或等比例的偶数宽度）
- `test_compressed.mp4` 体积明显小于 `test.mp4`
- 两个 `test_trim_*.mp4` 时长均接近 2 秒

测试完成后清理生成的临时文件：

```bash
rm -f test.mp4 test_480p.mp4 test_compressed.mp4 test_trim_fast.mp4 test_trim_precise.mp4
```

- [ ] **Step 7: 提交**

使用 `commit-cc-plugin` skill（不手动执行 git 工作流）提交本次全部新增文件：

```
git add .claude-plugin/marketplace.json
git add plugins/optimus-media-plugin/skills/media-ffmpeg-common/
git add plugins/optimus-media-plugin/skills/media-analyze/
git add plugins/optimus-media-plugin/skills/media-resize/
git add plugins/optimus-media-plugin/skills/media-compress/
git add plugins/optimus-media-plugin/skills/media-trim/
```

提交消息类型 `feat`，scope `media-plugin`，说明新增插件与四个 skill，marketplace.json 版本 `8.6.4 → 8.7.0`（Minor）。随后按 commit-cc-plugin 流程完成 push。
