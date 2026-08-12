# 新建 optimus-media-plugin：ffmpeg 音视频处理 Skill 集设计

## 背景

仓库现有 8 个插件（frontend/backend/qa/prd/feishu/office/devops/mcp-servers）中没有专门的多媒体/音视频领域。用户希望基于 ffmpeg CLI 提供四类基础能力：分析编解码信息、分辨率转换、压缩、片段截取，目标用户是"非专业音视频开发者"——不需要懂编解码原理，只需要能通过自然语言描述意图完成常见操作。

实现方式明确为：直接调用 ffmpeg/ffprobe 命令行工具，不封装 Python/Shell 脚本，SKILL.md 本身承担参数拼接和命令模板的职责。

## 插件与目录结构

新建 `optimus-media-plugin`，四个能力拆成四个独立 skill（而非一个复合 skill）——虽然都基于同一套 ffmpeg CLI，但触发场景各自独立、互不依赖，符合"每个功能足够简单，不需要跨阶段编排"的判断标准。

```
plugins/optimus-media-plugin/
├── .claude-plugin/plugin.json
└── skills/
    ├── media-analyze/          # 分析编解码格式、分辨率、码率、帧率
    │   ├── SKILL.md
    │   ├── CHANGELOG.md
    │   └── README.md
    ├── media-resize/           # 分辨率转换（如 1080p → 720p）
    │   ├── SKILL.md
    │   ├── CHANGELOG.md
    │   └── README.md
    ├── media-compress/         # 音视频压缩
    │   ├── SKILL.md
    │   ├── CHANGELOG.md
    │   └── README.md
    ├── media-trim/             # 片段截取
    │   ├── SKILL.md
    │   ├── CHANGELOG.md
    │   └── README.md
    └── media-ffmpeg-common/    # 共享参考文档，无 SKILL.md，不是可触发 skill
        ├── INSTALL.md          # ffmpeg/ffprobe 安装与环境变量配置
        ├── CLI-REFERENCE.md    # 四个 skill 实际用到的参数说明
        └── REFERENCE.md        # 环境检测命令 + 通用报错处理表
```

`media-ffmpeg-common` 目录下不放 SKILL.md，因此不会被当作独立 skill 注册、不会参与触发词匹配。四个真正的 skill 通过相对路径引用其中的文档，实现"文档级复用但不产生调用入口"。

需要在根 `.claude-plugin/marketplace.json` 的 `plugins` 数组追加：
```json
{
  "name": "optimus-media-plugin",
  "source": "./plugins/optimus-media-plugin",
  "description": "音视频处理工具集：基于 ffmpeg/ffprobe 的音视频编解码分析、分辨率转换、压缩、片段截取"
}
```
这是新增插件/skill，`marketplace.json` 的 `version` 字段按仓库规则做 **Minor** 升级。

## 共享参考文档：media-ffmpeg-common/

三份文档按"读者访问时机"拆分，而非合并成一份大文档：

### INSTALL.md（一次性、低频查阅）

按平台给出安装步骤和环境变量配置：
- Windows：`winget install ffmpeg`，或从 gyan.dev / BtbN 下载全量构建后手动将 `bin` 目录加入系统 `PATH`（含图形界面操作步骤）
- macOS：`brew install ffmpeg`
- Linux：`apt install ffmpeg` / `dnf install ffmpeg`
- 验证：`ffmpeg -version` 与 `ffprobe -version` 均能正常输出版本号

不做自动安装——安装软件是有副作用的操作（需要权限、跨平台包管理器不同），出错排查成本高，交给用户自己判断执行。

### CLI-REFERENCE.md（编写命令时高频查阅）

仅覆盖四个 skill 实际用到的参数，不做通用 ffmpeg 参数大全：

| 参数 | 用途 | 使用场景 |
|---|---|---|
| `-i` | 指定输入文件 | 全部 |
| `-c:v` / `-c:a` | 指定视频/音频编码器（如 `libx264`/`aac`） | media-compress, media-trim 精确模式 |
| `-crf` | 画质因子，0-51，越小画质越好体积越大 | media-compress |
| `-preset` | 编码速度/压缩率权衡：ultrafast ~ veryslow | media-compress |
| `-vf scale=W:H` | 分辨率缩放，`-2` 表示按比例自动计算且保证偶数 | media-resize |
| `-ss` / `-to` | 起止时间点；位置在 `-i` 前后语义不同（见 media-trim） | media-trim |
| `-c copy` | 流复制，不重新编码 | media-trim 快速模式、media-resize 音频透传 |
| `-y` | 覆盖已存在文件，不交互询问 | 全部 |

### REFERENCE.md（出错时查阅）

**环境检测**：
```bash
ffmpeg -version && ffprobe -version
```

**通用报错处理表**：

| 错误现象 | 原因 | 处理建议 |
|---|---|---|
| `Unknown encoder 'libx264'` | ffmpeg 编译时未包含该编码器 | `ffmpeg -encoders \| grep x264` 确认，提示更换全量构建版本 |
| `Permission denied` | 输出路径无写权限或文件被占用 | 确认输出目录存在且文件未被其他程序占用 |
| `Invalid data found when processing input` | 输入文件损坏或格式不受支持 | 先用 ffprobe 探测确认文件可读 |
| 命令挂起无输出 | 交互式询问是否覆盖已存在文件 | 命令加 `-y` |

## 四个 Skill 设计

### media-analyze

**触发场景**：分析视频/音频、查看编码格式/分辨率/码率/帧率、"这个视频什么编码"

**执行**：
```bash
ffprobe -v quiet -print_format json -show_format -show_streams <input>
```
解析 JSON，整理成结构化表格输出（不直接抛原始 JSON 给用户）：

| 项目 | 值 |
|---|---|
| 容器格式 / 视频编码 / 分辨率 / 帧率 / 视频码率 / 音频编码 / 音频码率 / 时长 / 文件大小 | ... |

仅支持单文件分析。

### media-resize——分辨率转换

**命令模板**：
```bash
ffmpeg -i <input> -vf scale=-2:720 -c:a copy <output>
```
- 用 `scale=-2:<height>` 而非写死宽度：`-2` 按高度等比计算宽度并保证偶数（多数编码器要求宽高为偶数）
- 音频用 `-c:a copy` 透传，不重新编码
- 输出路径必须由用户/Claude 显式指定，不做隐式命名推导

### media-compress——压缩

**命令模板**：
```bash
ffmpeg -i <input> -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k <output>
```
- 仅支持 CRF 模式，不支持"目标文件大小"模式（后者需要二次编码估算码率，复杂度和当前定位不匹配）
- 默认 CRF 23；SKILL.md 提供 CRF 取值对照表，让 Claude 能把"画质优先"（18-20）/"体积优先"（26-28）等口语化描述映射为数值
- 输出路径必须显式指定

### media-trim——片段截取

**默认模式（快速，流复制）**：
```bash
ffmpeg -ss <start> -to <end> -i <input> -c copy <output>
```
**精确模式（重新编码，帧精确）**：
```bash
ffmpeg -i <input> -ss <start> -to <end> -c:v libx264 -crf 18 -c:a aac <output>
```

⚠️ **`-ss` 参数位置直接决定截取行为**：放在 `-i` 之前是输入端 seek（快，但对齐到最近关键帧，用于快速模式）；放在 `-i` 之后是输出端 seek（慢，但帧精确，用于精确模式）。这一差异需要在 SKILL.md 中作为独立的"注意"条目呈现，而不是仅出现在命令示例里，避免被非专业用户忽略。

默认走快速模式；SKILL.md 提示"如需精确到帧，请说明使用精确模式"。输出路径必须显式指定。

**特有失败场景**（在共享报错表之外）：

| 触发条件 | 处理 |
|---|---|
| 起始时间超过视频总时长 | 提示核对时间戳，参考 media-analyze 输出的时长字段 |
| 快速模式截取起点出现绿屏/花屏 | 说明是对齐到非关键帧导致，建议改用精确模式 |

## 测试方式

不写自动化单元测试——四个 skill 没有 Python/Node 代码逻辑（纯 SKILL.md 文档指导 + 直接调用系统命令），唯一需要验证的是"命令是否按预期执行"，只能通过实际运行覆盖，单元测试会为不存在的代码分支制造虚假的安全感。

本地测试用真实小体积测试视频验证：
1. 生成测试文件：
   ```bash
   ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=5 -shortest test.mp4
   ```
2. 依次验证：
   - `media-analyze` 能否正确读出 1280x720 / 30fps
   - `media-resize` 转 480p 后能否读出新分辨率
   - `media-compress` 压缩后文件确实变小
   - `media-trim` 快速模式与精确模式各截一段，确认输出时长符合预期
