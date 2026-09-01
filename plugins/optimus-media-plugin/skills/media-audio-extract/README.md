# media-audio-extract

> 版本：1.0.3 | 分类：tool

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
Step 4  执行前校验：一条 ffprobe 列出全部流的 index/codec_type/codec_name/bit_rate
         先判流结构（三项硬门槛）：
         ├─ ① 无 codec_type=audio → 源无音频流，硬约束终止
         ├─ ② 无 codec_type=video → 输入是纯音频，终止并指向 media-audio-convert
         └─ ③ 多条 audio 流 → 🔴 CHECKPOINT 列出各轨让用户指认
         再判编码兼容性：
         ├─ ④ 编码与目标扩展名兼容 → 走流复制
         └─ ⑤ 不兼容（如 aac→.mp3）🔴 CHECKPOINT
              按源编码是否有损据实说明代价 + 对照源码率说明体积走向
              （目标为 .wav 时 ⛔ 特别当心：copy 不报错但产错配文件）
   ↓
Step 5  执行提取（-map 0:a:0 不可省略，保证与 Step 4 探测的是同一条流）
         ├─ 流复制模式：-vn -map 0:a:0 -c:a copy（无损）
         └─ 重新编码模式：-vn -map 0:a:0 -c:a <编码器> -b:a <据源码率取值>
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

media-audio-extract ──Step4 自行执行 ffprobe 列出全部流──▶ （不调用 media-analyze）
media-audio-extract ──输入是纯音频时终止并指向──▶ media-audio-convert
media-audio-extract ──用户如需继续转换──▶ media-audio-convert（人工另行触发，非自动衔接）
```

不被其他 skill 调度。Step 4 直接执行一条 ffprobe 探测命令列出全部流的 `index`/`codec_type`/`codec_name`/`bit_rate`，不调用 media-analyze 的全量 JSON 展示型命令——只需这四个字段，不需要整份流信息，但也不能更少：这四个字段分别支撑"有无音频流""有无视频流""几条音轨""编码与码率"四项判定。不参与组合请求编排。
