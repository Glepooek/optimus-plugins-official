# media-download

> 版本：1.0.2 | 分类：tool

基于 yt-dlp 下载单个在线视频/音频链接到本地指定路径，下载前查询可用格式供用户选择。

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

## 触发词

下载视频、下载这个视频、视频下载、帮我下载这个链接的视频、yt-dlp。

## 业务逻辑流程图

```
Step 0  需求预告：一次性列出缺失信息并询问（URL、输出路径；清晰度不算必需信息）；若用户描述已明确批量/合集意图则直接终止
   ↓
Step 1  确认 yt-dlp 与 ffmpeg 环境均可用（依赖检查，两者独立检测）
   ↓
Step 2  校验输入 URL 格式合法性（输入参数检查，非本地文件存在性检查）；识别纯播放列表/合集链接（无具体视频 ID）则直接终止
   ↓
Step 3  确认输出路径 🔴 CHECKPOINT + 校验输出目录可写（输出参数检查）
   ↓
Step 4  执行前校验：查询该链接所有可用格式 🔴 CHECKPOINT 用户选择 format id
         （运行条件检查，查询失败/需要登录凭据均为硬约束直接终止）
   ↓
Step 5  执行下载：yt-dlp -f <format_id> -o <output> --no-playlist <url>
```

## 产出物数据流

视频/音频 URL + 输出路径 → 本 skill → 指定路径下的媒体文件 → 人工接手；如需继续转码/压缩/截取，需用户另行触发 media-trim/media-resize/media-compress/media-framerate，本 skill 不自动衔接。

## Skill 依赖关系图

```
用户 ──触发──▶ media-download ──引用（仅 ffmpeg 部分）──▶ media-ffmpeg-common/REFERENCE.md
                              └──引用（仅 ffmpeg 部分）──▶ media-ffmpeg-common/INSTALL.md
```

yt-dlp 为本 skill 独有依赖，独立在 SKILL.md 的 `compatibility` 字段声明，不计入 `media-ffmpeg-common` 共享文档；本 skill 不接入 `media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"顺序编排。
