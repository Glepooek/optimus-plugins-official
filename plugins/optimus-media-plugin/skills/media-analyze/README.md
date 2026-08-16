# media-analyze

> 版本：1.1.2 | 分类：tool

分析单个音视频文件的容器格式、编解码、分辨率、帧率、码率、时长等信息，结构化表格输出。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze（本 skill）、media-resize、media-compress、media-trim、media-play、media-framerate
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
Step 0  需求预告：一次性列出缺失信息并询问（信息已齐全则跳过）
   ↓
Step 1  确认 ffprobe 环境可用（依赖检查）
   ↓
Step 2  校验输入文件是否存在（输入参数检查）
   ↓
Step 3  执行 ffprobe -show_format -show_streams
   ↓
Step 4  解析 JSON，整理为结构化表格输出
```

## 产出物数据流

音视频文件路径 → 本 skill → 结构化信息表格（容器/编码/分辨率/帧率/码率/时长/大小）→ 人工阅读；时长字段被 media-trim 的 Step4 执行前校验调用，用于判断起止时间是否超过总时长。

## Skill 依赖关系图

```
用户 ──触发──▶ media-analyze ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                    └──▶ media-ffmpeg-common/CLI-REFERENCE.md
media-trim ──调用（Step4 执行前校验）──▶ media-analyze
```

`media-trim` 在 Step4 执行前校验中主动调用本 skill 的 ffprobe 命令查询总时长，构成实际调用依赖。
