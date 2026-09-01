# media-frame-extract

> 版本：1.0.0 | 分类：tool

从视频中提取静态图片。单帧模式取指定时间点的一帧（封面图），多帧等间隔模式每 N 秒截一张（预览序列）。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、
│              │  media-framerate、media-convert、media-download、
│              │  media-audio-extract、media-audio-convert、media-frame-extract（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

视频截图、截帧、抽帧、导出封面图、截取某一帧、每隔几秒截一张、生成预览图。

## 业务逻辑流程图

```
Step 0-3  前置校验（引用 media-ffmpeg-common/PREFLIGHT.md）
          需求预告 → ffmpeg 环境 → 输入文件存在 → 输出路径 🔴 CHECKPOINT
          （输出路径校验含：父目录可写 + 输出路径 ≠ 输入路径）
          按模式区分必需信息；未给时间点时不擅自取 00:00:00
   ↓
Step 4  执行前校验：ffprobe 查总时长（失败则文件损坏，终止）
         ├─ 单帧模式：时间点 ≤ 总时长？超出 → 硬约束终止
         └─ 多帧模式：预估张数 = 总时长 ÷ 间隔
              └─ > 200 张 🔴 CHECKPOINT 告知预估数量，确认后继续
   ↓
Step 5  执行提取（只有一种 -ss 写法，不设双模式）
         ├─ 单帧：-ss <时间点> -i input -frames:v 1 out.png
         └─ 多帧：-i input -vf fps=1/<间隔> out_%03d.png
```

## 产出物数据流

输入视频 + 时间点或间隔秒数 → 本 skill → 指定路径下的图片文件（单张或序列）→ **任务终态，人工接手**。

产出物为图片，无法再进入 trim/resize/framerate/compress/convert 的视频处理链。

## Skill 依赖关系图

```
用户 ──触发──▶ media-frame-extract ──引用──▶ media-ffmpeg-common/PREFLIGHT.md（Step 0-3）
                                        └──▶ media-ffmpeg-common/REFERENCE.md
                                        └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                        └──▶ media-ffmpeg-common/INSTALL.md
                                        └──▶ knowledge-base/media/reference/
                                              video-codecs.md（关键帧与 GOP）
                                              media-parameters.md §2（帧率）
```

不被其他 skill 调度。Step 4 直接执行单字段 ffprobe 探测命令查询总时长，不调用 media-analyze 的全量 JSON 展示型命令。不参与组合请求编排。

与 media-play 的界线：media-play 是实时预览（不产出文件），本 skill 是导出静态图片（产出文件）。用户说"看一下这个视频"走 media-play，说"截一张图"走本 skill。
