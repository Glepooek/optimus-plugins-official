# media-resize

> 版本：1.2.4 | 分类：tool

将视频文件转换到指定分辨率（如 1080p 转 720p）。缩放必然触发视频流重新编码（固定 CRF 18 画质档位），音频流透传不重新编码。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize（本 skill）、media-compress、media-trim、media-play、media-framerate、media-convert
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
Step 0-3  前置校验（引用 media-ffmpeg-common/PREFLIGHT.md）
          需求预告 → ffmpeg 环境 → 输入文件存在 → 输出路径 🔴 CHECKPOINT
          （输出路径校验含：父目录可写 + 输出路径 ≠ 输入路径）
   ↓
Step 4  执行前校验：放大画质损失 / 宽高比不一致 🔴 CHECKPOINT（运行条件检查）
   ↓
Step 5  执行 ffmpeg -y -vf scale=-2:H -c:v libx264 -crf 18 -c:a copy
```

## 产出物数据流

输入视频 + 目标分辨率 → 本 skill → 指定路径下的新分辨率视频文件 → 人工接手。

## Skill 依赖关系图

```
用户 ──触发──▶ media-resize ──引用──▶ media-ffmpeg-common/PREFLIGHT.md（Step 0-3）
                                  └──▶ media-ffmpeg-common/REFERENCE.md
                                  └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                  └──▶ media-ffmpeg-common/INSTALL.md
media-resize ──调用（Step4 执行前校验）──▶ media-analyze
```

不被其他 skill 调度；Step4 执行前校验中主动调用 media-analyze 的 ffprobe 命令查询原始分辨率，构成实际调用依赖。
