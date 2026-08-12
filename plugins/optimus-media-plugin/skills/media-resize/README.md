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
