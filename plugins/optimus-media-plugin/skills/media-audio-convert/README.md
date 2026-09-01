# media-audio-convert

> 版本：1.0.2 | 分类：tool

纯音频到纯音频的格式转换与参数调整。先查清源文件真实编码，再据此告知本次转换是首次有损、二次有损，还是只需重封装。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、
│              │  media-framerate、media-convert、media-download、
│              │  media-audio-extract、media-audio-convert（本 skill）、media-frame-extract
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

音频格式转换、wav转mp3、flac转aac、音频转码、改音频码率、改采样率、音频转单声道、无损转有损。

## 业务逻辑流程图

```
Step 0-3  前置校验（引用 media-ffmpeg-common/PREFLIGHT.md）
          需求预告 → ffmpeg 环境 → 输入文件存在 → 输出路径 🔴 CHECKPOINT
          （输出路径校验含：父目录可写 + 输出路径 ≠ 输入路径）
          码率/采样率/声道数均有缺省行为，缺失不阻塞
   ↓
Step 4  执行前校验：ffprobe 查【真实编码 + 码率】（不看扩展名，不加 -select_streams）
         须同时取 stream 级与 format 级 bit_rate（FLAC 的 stream 级为 N/A）
         ├─ 查询失败 → 文件损坏/非音频文件，终止
         ├─ 出现 codec_type=video → 输入是视频，终止并指向 media-audio-extract
         └─ 按 5 类损失性质分流 🔴 CHECKPOINT
              ├─ 无损→无损            无音质损失，可直接执行
              ├─ 无损→有损            首次有损不可逆；体积走向看源码率 vs 目标码率
              ├─ 有损→有损            ⚠ 只会更差不会更好；不给固定损失量级
              ├─ 有损→无损            ⚠ 无意义放大，体积暴增音质不变
              └─ 编码同、容器不同     ⚠ 只需重封装；.m4a→.aac 另丢 gapless 元数据
   ↓
Step 5  执行转换
         ├─ 重新编码：-c:a <编码器> -b:a <据源码率取值，非固定 192k>
         ├─ 重封装：-c:a copy（音频数据无损换容器）
         └─ 按需追加 -ar <采样率> / -ac <声道数>
```

## 产出物数据流

输入音频 + 目标格式（+ 可选码率/采样率/声道数）→ 本 skill → 指定路径下的转换后音频文件 → **任务终态，人工接手**。

输入输出都是纯音频，与视频处理链无交集。

## Skill 依赖关系图

```
用户 ──触发──▶ media-audio-convert ──引用──▶ media-ffmpeg-common/PREFLIGHT.md（Step 0-3）
                                        └──▶ media-ffmpeg-common/REFERENCE.md
                                        └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                        └──▶ media-ffmpeg-common/INSTALL.md
                                        └──▶ knowledge-base/media/reference/
                                              audio-container-formats.md §2/§3
                                              audio-codecs.md §1
                                              audio-parameters.md §1/§3

media-audio-extract ──用户如需继续转换──▶ media-audio-convert（人工另行触发，非自动衔接）
```

不被其他 skill 自动调度。Step 4 直接执行一条 ffprobe 探测命令取全部流的编码/采样率/声道数/码率，不调用 media-analyze 的全量 JSON 展示型命令。上游可能是 media-audio-extract 的产出（由用户另行触发，不是自动衔接）。不参与组合请求编排。
