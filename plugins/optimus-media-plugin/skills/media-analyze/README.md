# media-analyze

> 版本：1.0.1 | 分类：tool

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
