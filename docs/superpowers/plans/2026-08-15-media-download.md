# media-download Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `plugins/optimus-media-plugin/skills/` 下新增 `media-download` skill，用 yt-dlp + ffmpeg 实现单视频链接下载，作为 VDH+CoApp 浏览器架构在 CLI 环境的等价替代方案。

**Architecture:** 独立的 `tool` 类 skill，与现有 6 个 `media-*` skill 同级并列，遵循相同的 Step 0-N 结构规范（需求预告 → 环境检测 → 输入校验 → 输出确认 → 执行前校验 → 执行）。yt-dlp 作为本 skill 独有依赖单独声明，不修改 `media-ffmpeg-common` 共享文档；仅复用其 ffmpeg 环境检测命令与安装指引。不接入现有的组合请求编排链条。

**Tech Stack:** yt-dlp（CLI）、ffmpeg（复用现有依赖，供 yt-dlp 内部合并音视频流）、Markdown（SKILL.md/README.md/CHANGELOG.md）、JSON（test-prompts.json）

## Global Constraints

- Skill frontmatter 必须遵循 `.claude/rules/skill-authoring.md`：仅 `name`/`description`/`license`/`allowed-tools`/`metadata`/`compatibility` 六个顶层字段；`metadata.version` 新建 skill 初始为 `"1.0.0"`；`metadata.author` 固定为 `desktop client team`；`metadata.category` 取值 `tool`
- 新增 skill 触发仓库 marketplace 版本号 **Minor** 升级（`.claude-plugin/marketplace.json` 的 `version` 字段，当前 `8.11.2` → `8.12.0`）
- CHANGELOG.md 初始版本号必须为 `[1.0.0]`，日期用今天 `2026-08-15`
- README.md 章节顺序固定：标题与元信息 → 所处层级 → 触发词 → 业务逻辑流程图 → 产出物数据流 → Skill 依赖关系图，图表全部用 ASCII box-drawing 字符，不用 Mermaid
- 编辑 SKILL.md/CHANGELOG.md/README.md 时不做无关格式化改动（不增删空行、不调整缩进）
- 严格落实设计文档 `docs/superpowers/specs/2026-08-15-media-download-design.md` 的范围边界：仅单视频下载、不支持播放列表批量下载、不支持需要登录凭据（cookies）的内容、不接入 `media-ffmpeg-common/REFERENCE.md` 的组合请求编排链条
- 提交与推送必须使用 `commit-cc-plugin` skill，禁止手动 git 工作流

---

### Task 1: 创建 media-download SKILL.md

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-download/SKILL.md`

**Interfaces:**
- Consumes: `../media-ffmpeg-common/REFERENCE.md` 的 ffmpeg 环境检测命令与通用报错处理表；`../media-ffmpeg-common/INSTALL.md` 的 ffmpeg 安装指引（仅引用链接，不修改这两个文件）
- Produces: 本 skill 的触发词集合（供 Task 3 README.md 复用一致文案）：`下载视频`、`下载这个视频`、`视频下载`、`帮我下载这个链接的视频`、`yt-dlp`

- [ ] **Step 1: 编写 frontmatter 与功能概述**

写入以下内容作为文件开头（frontmatter + 功能概述部分）：

```markdown
---
name: media-download
description: Use when user wants to download a single online video or audio by URL — 下载视频、下载这个视频、视频下载、帮我下载这个链接的视频、yt-dlp。Not for playlist/channel batch downloads, content requiring login credentials, or local file transcoding/compression/trimming.
metadata:
  version: "1.0.0"
  author: desktop client team
  category: tool
compatibility: 需要用户本机已安装 yt-dlp 并加入 PATH（见下方安装指引），以及 ffmpeg（供 yt-dlp 合并分离的音视频流），参见 ../media-ffmpeg-common/INSTALL.md。
allowed-tools: Bash
---

# 在线视频下载

## 功能概述

基于 yt-dlp 下载单个在线视频/音频链接到本地指定路径。下载前先查询该链接所有可用格式供用户选择，不臆测清晰度。仅支持单个链接，不支持播放列表/频道批量下载；仅下载用户本人有权访问且平台允许下载的公开内容，不支持需要登录凭据（cookies）才能访问的内容（会员专享、地区限制等），遇到此类内容直接报错终止，不引导用户配置 cookies。下载完成即任务终态，不自动衔接 media-trim/media-resize/media-compress/media-framerate 等后续处理，如需继续编辑请另行触发对应 skill。
```

- [ ] **Step 2: 编写 Step 0 需求预告**

紧接功能概述后追加：

```markdown
## 使用方法

### Step 0：需求预告

处理用户请求的第一步：对比本 skill 需要的信息与用户在触发语句或上下文中已提供的信息，一次性列出缺失项统一询问，不逐个 Step 反应式追问。

- 需要比对的信息：视频/音频链接 URL、输出保存路径——用户已明确提供的项不重复询问，若这两项已经齐全，跳过本步骤直接进入 Step 1
- 清晰度/格式**不参与本环节比对**：必须先在 Step 4 查询该链接实际可用格式后才能让用户选择，不能在需求预告阶段要求用户凭空报一个可能不存在的清晰度，缺失不阻塞本步骤
- yt-dlp/ffmpeg 依赖是否安装**不参与本环节比对**：这是系统状态而非用户可主动提供的信息，不作为缺失项询问用户，也不影响是否跳过本步骤的判断；依赖状态由 Step 1 实际检测

本步骤不做实际系统调用，仅做信息是否齐全的静态比对。
```

- [ ] **Step 3: 编写 Step 1 确认环境**

追加：

```markdown
### Step 1：确认环境

```bash
yt-dlp --version
```

检查失败（命令不存在）：告知用户参考 yt-dlp 官方安装方式（`pip install yt-dlp` 或访问 [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) 下载对应平台可执行文件），返回错误信息并终止任务，不进入后续步骤。

再执行 `../media-ffmpeg-common/REFERENCE.md` 中的环境检测命令确认 `ffmpeg` 可用（yt-dlp 下载到分离的视频流+音频流时需要 ffmpeg 合并封装）。检查失败：引导用户参考 `../media-ffmpeg-common/INSTALL.md` 安装，返回错误信息并终止任务。

`yt-dlp` 与 `ffmpeg`/`ffprobe` 是两个独立工具，均需检测通过才能继续，任一缺失都终止任务。
```

- [ ] **Step 4: 编写 Step 2 校验输入 URL**

追加：

```markdown
### Step 2：校验输入 URL

检查用户提供的字符串是否为合法 URL 格式（包含协议头 `http://`/`https://` 及基本结构）。这一步是**格式校验**，不是本地文件是否存在的检查——与其他 media-* skill 的"校验输入文件"步骤有本质区别，不要混用判断逻辑。

格式不合法：返回错误信息告知用户核对链接，终止任务，不进入后续步骤。
```

- [ ] **Step 5: 编写 Step 3 确认输出路径**

追加：

```markdown
### Step 3：确认输出路径

🔴 CHECKPOINT：向用户确认保存路径，不得省略直接执行；未确认前不得进入 Step 4。

确认路径后校验其父目录是否存在且可写。父目录不存在或无写权限时返回错误信息告知用户，终止任务；输出文件本身此刻不存在属正常状态，不作为失败条件。
```

- [ ] **Step 6: 编写 Step 4 执行前校验（查询可用格式）**

追加：

```markdown
### Step 4：执行前校验

执行以下命令查询该链接所有可用格式：

```bash
yt-dlp -F <url>
```

- **查询失败**（网络错误、站点不支持、链接失效、需要登录凭据）：属于硬约束——无法通过用户确认绕过。如实报告 yt-dlp 返回的具体错误原因，终止任务，不进入 Step 5：
  - 提示 `Unsupported URL`：说明该站点不在 yt-dlp 支持列表内，告知用户并终止，不尝试降级为通用网页抓取
  - 提示需要登录/年龄验证/会员专享等信息（如 `Sign in to confirm your age`）：明确告知用户本 skill 不支持需要登录凭据的内容，终止任务，不引导用户配置 cookies
- **查询成功**：向用户展示 yt-dlp 原生输出的格式列表（含 format id、分辨率、编码、文件大小等），🔴 CHECKPOINT 用户从列表中选择具体 format id 后才能进入 Step 5；用户选择的 format id 不在列表内时，提示核对列表重新选择，不代为猜测最接近的格式。
```

- [ ] **Step 7: 编写 Step 5 执行下载**

追加：

```markdown
### Step 5：执行下载

```bash
yt-dlp -f <format_id> -o <output> <url>
```

若所选格式为分离的视频流+音频流，yt-dlp 会自动调用本机 ffmpeg 合并封装，本 skill 不需要手动拼接额外的 ffmpeg 合并命令。

参数说明：`-f` 指定 Step 4 中用户选择的 format id；`-o` 指定 Step 3 确认的输出路径（yt-dlp 语法，支持模板变量，但本 skill 场景下始终传入用户确认的具体路径，不使用模板变量）。
```

- [ ] **Step 8: 编写失败处理章节**

追加：

```markdown
## 失败处理

除 Step 1-4 中已描述的终止条件外，本 skill 特有的失败场景：

| 触发条件 | 处理 |
|---|---|
| 下载中途网络中断 | 如实告知用户下载失败及具体原因，不自动重试；用户可自行决定是否重新触发本 skill |
| 输出路径所在磁盘空间不足 | 如实告知用户 yt-dlp/ffmpeg 报出的磁盘空间错误，终止任务，不做自动清理或换路径重试 |

若用户同时提出下载后的转码/压缩/截取/帧率转换诉求，不在本 skill 中衔接执行，应告知用户下载完成后另行调用 media-trim/media-resize/media-compress/media-framerate 处理；本 skill 不参与 `../media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"顺序编排。
```

- [ ] **Step 9: 编写不要做什么章节**

追加：

```markdown
## 不要做什么

- 不要在 yt-dlp 或 ffmpeg 环境检测失败时继续执行，应立即返回错误信息并终止（Step 1）
- 不要在 URL 格式不合法时继续执行，应立即返回错误信息并终止（Step 2）
- 不要在用户未确认输出路径前执行命令（Step 3 的检查点）
- 不要在输出目录不存在或不可写时继续执行，应立即返回错误信息并终止（Step 3）
- 不要跳过 Step 4 的格式查询直接下载"最佳画质"，必须让用户从实际可用列表中选择具体 format id
- 不要在 Step 4 查询格式失败时臆测原因强行重试，应如实报告 yt-dlp 返回的错误信息并终止
- 不要支持播放列表/频道批量下载，仅处理单个视频/音频链接
- 不要支持需要登录凭据（cookies）才能访问的内容，遇到直接报错终止，不引导用户提供 cookies
- 不要在下载完成后自动调用 media-trim/media-resize/media-compress/media-framerate 做后续处理，也不写入组合请求编排链条
```

- [ ] **Step 10: 校验 frontmatter YAML 语法**

用 Read 工具重新读取整个文件，人工确认：
1. frontmatter 只有 6 个允许的顶层字段（`name`/`description`/`metadata`/`compatibility`/`allowed-tools`），无多余字段
2. `metadata.version`/`metadata.author`/`metadata.category` 三个子字段缩进正确、值加了引号（version）
3. description 字段的中英文触发词、"Not for..."边界描述完整无截断

- [ ] **Step 11: 本地测试验证 skill 可被加载**

调用 `test-locally` skill 中描述的方式，在仓库根目录执行单插件加载：

```bash
claude --plugin-dir ./plugins/optimus-media-plugin
```

新开一个会话，输入触发词（如"帮我下载这个视频链接"）确认 skill 被正确注册触发，无 YAML 解析报错。确认无误后退出该测试会话。

---

### Task 2: 创建 CHANGELOG.md

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-download/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1 中 SKILL.md 的功能概述文案
- Produces: 无（叶子文件，不被其他任务消费）

- [ ] **Step 1: 编写初始版本记录**

```markdown
# Changelog

## [1.0.0] - 2026-08-15

### Added
- 新增 media-download skill：基于 yt-dlp 下载单个在线视频/音频链接，下载前查询可用格式供用户选择，通过 ffmpeg 合并分离的音视频流；不支持播放列表批量下载与需要登录凭据的内容，不接入现有组合请求编排链条
```

- [ ] **Step 2: 提交前确认格式**

对照 `.claude/rules/skill-authoring.md` 的 CHANGELOG.md 规范逐条核对：版本号格式 `[1.0.0] - 2026-08-15`、只写 `### Added` 类别（无变更的类别省略）。

---

### Task 3: 创建 README.md

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-download/README.md`
- Reference: `plugins/optimus-media-plugin/skills/media-trim/README.md`（章节结构参考样例，仅参考格式不复制内容）

**Interfaces:**
- Consumes: Task 1 SKILL.md 中确定的 Step 0-5 流程、触发词列表、依赖关系（yt-dlp 独立声明 + 引用 media-ffmpeg-common 的 REFERENCE.md/INSTALL.md/CLI-REFERENCE.md）
- Produces: 无（叶子文件）

- [ ] **Step 1: 编写标题与元信息**

```markdown
# media-download

> 版本：1.0.0 | 分类：tool

基于 yt-dlp 下载单个在线视频/音频链接到本地指定路径，下载前查询可用格式供用户选择。
```

- [ ] **Step 2: 编写所处层级**

```markdown
## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、media-framerate、media-download（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```
```

- [ ] **Step 3: 编写触发词**

```markdown
## 触发词

下载视频、下载这个视频、视频下载、帮我下载这个链接的视频、yt-dlp。
```

- [ ] **Step 4: 编写业务逻辑流程图**

```markdown
## 业务逻辑流程图

```
Step 0  需求预告：一次性列出缺失信息并询问（URL、输出路径；清晰度不算必需信息）
   ↓
Step 1  确认 yt-dlp 与 ffmpeg 环境均可用（依赖检查，两者独立检测）
   ↓
Step 2  校验输入 URL 格式合法性（输入参数检查，非本地文件存在性检查）
   ↓
Step 3  确认输出路径 🔴 CHECKPOINT + 校验输出目录可写（输出参数检查）
   ↓
Step 4  执行前校验：查询该链接所有可用格式 🔴 CHECKPOINT 用户选择 format id
         （运行条件检查，查询失败/需要登录凭据均为硬约束直接终止）
   ↓
Step 5  执行下载：yt-dlp -f <format_id> -o <output> <url>
```
```

- [ ] **Step 5: 编写产出物数据流**

```markdown
## 产出物数据流

视频/音频 URL + 输出路径 → 本 skill → 指定路径下的媒体文件 → 人工接手；如需继续转码/压缩/截取，需用户另行触发 media-trim/media-resize/media-compress/media-framerate，本 skill 不自动衔接。
```

- [ ] **Step 6: 编写 Skill 依赖关系图**

```markdown
## Skill 依赖关系图

```
用户 ──触发──▶ media-download ──引用（仅 ffmpeg 部分）──▶ media-ffmpeg-common/REFERENCE.md
                              └──引用（仅 ffmpeg 部分）──▶ media-ffmpeg-common/INSTALL.md
```

yt-dlp 为本 skill 独有依赖，独立在 SKILL.md 的 `compatibility` 字段声明，不计入 `media-ffmpeg-common` 共享文档；本 skill 不接入 `media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"顺序编排。
```

- [ ] **Step 7: 核对与 SKILL.md 一致性**

对照 Task 1 完成后的 SKILL.md，确认：版本号 `1.0.0`、分类 `tool` 与 frontmatter 一致；触发词文案与 description 字段一致；流程图 Step 编号与 SKILL.md 实际 Step 编号一一对应。

---

### Task 4: 创建 test-prompts.json

**Files:**
- Create: `plugins/optimus-media-plugin/skills/media-download/test-prompts.json`
- Reference: `plugins/optimus-media-plugin/skills/media-trim/test-prompts.json`（格式参考）

**Interfaces:**
- Consumes: Task 1 SKILL.md 的完整 Step 0-5 流程与"不要做什么"约束
- Produces: 无（叶子文件，供后续 darwin-skill 评分或人工验证使用）

- [ ] **Step 1: 编写覆盖三类场景的测试用例**

```json
[
  {
    "id": 1,
    "prompt": "帮我下载 https://example.com/watch?v=abc123 这个视频，保存到 D:/downloads/video.mp4",
    "expected": "信息已齐全（URL、输出路径都给了），跳过 Step 0 询问；依次做 yt-dlp/ffmpeg 环境检测、URL 格式校验、CHECKPOINT 确认输出路径、Step 4 查询可用格式并展示列表要求用户选择 format id，不跳过格式选择直接下载"
  },
  {
    "id": 2,
    "prompt": "帮我把这个网站上的一个视频合集全部下载下来",
    "expected": "识别为播放列表/批量下载诉求，超出本 skill 范围（仅支持单个视频链接），应告知用户不支持批量下载并终止，不尝试变通实现"
  },
  {
    "id": 3,
    "prompt": "帮我下载 https://example.com/members-only-video 这个会员专享视频",
    "expected": "Step 4 查询格式时 yt-dlp 报需要登录/会员权限，应识别为硬约束直接终止并告知用户本 skill 不支持需要登录凭据的内容，不引导用户提供 cookies 或账号密码"
  }
]
```

- [ ] **Step 2: 校验 JSON 格式合法性**

```bash
python -c "import json; json.load(open('plugins/optimus-media-plugin/skills/media-download/test-prompts.json', encoding='utf-8'))"
```

预期：无报错输出，说明 JSON 语法合法。

---

### Task 5: 版本号升级与提交推送

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: Task 1-4 产出的全部 4 个文件（SKILL.md/CHANGELOG.md/README.md/test-prompts.json）
- Produces: 无（终态任务）

- [ ] **Step 1: 升级 marketplace 版本号**

编辑 `.claude-plugin/marketplace.json`，将顶层 `"version"` 字段从 `"8.11.2"` 改为 `"8.12.0"`（新增 skill 属于 Minor 升级）。

- [ ] **Step 2: 用 darwin-skill 评估新 skill 质量**

调用 `darwin-skill` 对 `plugins/optimus-media-plugin/skills/media-download/SKILL.md` 评分，确认评分结果符合仓库质量基线（无需与"改动前"比较，因为是新建 skill，重点确认 9 维度评分无明显短板，尤其是"边界清晰度"与"前置校验完整性"两项，这是本 skill 设计重点）。

若评分发现问题，回到 Task 1 对应 Step 修正后重新评分，直至通过。

- [ ] **Step 3: 调用 commit-cc-plugin 提交并推送**

按 `commit-cc-plugin` skill 流程执行（状态检查 → `.kiro/skills` 符号链接检查【本次不涉及 `.claude/skills/`，跳过】→ 版本号决策【已在 Step 1 完成】→ 逐文件暂存 Task 1-5 的 5 个改动文件 → 原子性自查 → unpushed 提交检测 → 提交 → 推送）。

暂存文件清单：
```bash
git add .claude-plugin/marketplace.json
git add plugins/optimus-media-plugin/skills/media-download/SKILL.md
git add plugins/optimus-media-plugin/skills/media-download/CHANGELOG.md
git add plugins/optimus-media-plugin/skills/media-download/README.md
git add plugins/optimus-media-plugin/skills/media-download/test-prompts.json
```

提交消息类型用 `feat(media-plugin)`，说明新增 media-download skill 及版本号变化 `8.11.2 → 8.12.0`。

---

## Self-Review Notes

- **Spec 覆盖检查**：设计文档的 6 个执行 Step、失败处理表、不要做什么清单均已映射到 Task 1 对应 Step；range 边界（不支持播放列表/cookies/不接组合链条）在 SKILL.md description、失败处理、不要做什么三处均有落地，并在 test-prompts.json 用例 2、3 中做场景验证
- **占位符扫描**：全部 Step 均为可直接使用的完整 Markdown/JSON/Bash 内容，无 TBD/TODO
- **命名一致性**：SKILL.md 的 Step 编号（0-5）、README.md 流程图、test-prompts.json 的预期描述三者互相引用的 Step 编号一致；`format_id` 变量名在 Step 4/5 命令模板中保持一致
