# media-audio-extract

> 版本：1.0.0 | 分类：tool

从视频文件中提取音频流，产出纯音频文件。默认流复制无损搬运，仅在目标格式装不下源编码时降级为重新编码。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、
│              │  media-framerate、media-convert、media-download、
│              │  media-audio-extract（本 skill）、media-audio-convert、media-frame-extract
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

提取音频、提取音轨、视频转音频、扒音频、从视频里提取声音、视频转mp3、只要声音不要画面。

## 业务逻辑流程图

```
Step 0-3  前置校验（引用 media-ffmpeg-common/PREFLIGHT.md）
          需求预告 → ffmpeg 环境 → 输入文件存在 → 输出路径 🔴 CHECKPOINT
          （输出路径校验含：父目录可写 + 输出路径 ≠ 输入路径）
          未指定输出扩展名时不擅自假定 .mp3，先询问目标格式
   ↓
Step 4  执行前校验：ffprobe -select_streams a:0 查源音频编码
         ├─ ① 输出为空 → 源无音频流，硬约束终止
         ├─ ② 编码与目标扩展名兼容 → 走流复制
         └─ ③ 不兼容（如 aac→.mp3）🔴 CHECKPOINT
              告知可能为二次有损 + 建议无损扩展名 → 用户确认后转码
   ↓
Step 5  执行提取
         ├─ 流复制模式：-vn -c:a copy（无损）
         └─ 重新编码模式：-vn -c:a <编码器> -b:a 192k
```

## 产出物数据流

输入视频 + 目标音频格式 → 本 skill → 指定路径下的纯音频文件 → **任务终态，人工接手**。

产出物为纯音频，无法再进入 trim/resize/framerate/compress/convert 的视频处理链。用户需要继续转换音频格式或调整采样率/码率时，另行触发 media-audio-convert。

## Skill 依赖关系图

```
用户 ──触发──▶ media-audio-extract ──引用──▶ media-ffmpeg-common/PREFLIGHT.md（Step 0-3）
                                        └──▶ media-ffmpeg-common/REFERENCE.md
                                        └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                        └──▶ media-ffmpeg-common/INSTALL.md
                                        └──▶ knowledge-base/media/reference/
                                              audio-container-formats.md
                                              audio-codecs.md / audio-parameters.md

media-audio-extract ──Step4 自行执行 ffprobe 查 a:0 编码──▶ （不调用 media-analyze）
media-audio-extract ──用户如需继续转换──▶ media-audio-convert（人工另行触发，非自动衔接）
```

不被其他 skill 调度。Step 4 直接执行单字段 ffprobe 探测命令查询音频编码，不调用 media-analyze 的全量 JSON 展示型命令——只需一个 `codec_name` 字段，不需要整份流信息。不参与组合请求编排。
