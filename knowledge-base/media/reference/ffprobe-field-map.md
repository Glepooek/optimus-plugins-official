> **本文件在 Media 知识库中的定位**
>
> 本文件是把"概念 → 实际字段"落地的操作参考（讲解性质，不带 MUST/SHOULD/MAY 语气）。
> 前面各文件解释"什么是容器、编码、分辨率……"，本文件回答"怎么从 ffprobe 输出里读出这些值"。
>
> - **适用场景**：分析某个具体媒体文件、把概念映射到工具输出时查阅
> - **关联**：流结构见 `media-stream-basics.md`；各参数含义见 `media-parameters.md`、`audio-parameters.md`、`video-quality.md`

# ffprobe 字段映射：如何查看媒体文件的各项参数

## 1. 基本用法

ffprobe 是 ffmpeg 生态的媒体信息查看工具，只读不改：

```bash
ffprobe -show_format -show_streams <文件>          # 容器信息 + 所有流
ffprobe -show_format -show_streams -of json <文件>  # 输出为 JSON，便于解析
ffprobe -show_streams -select_streams v <文件>      # 只看视频流
ffprobe -show_streams -select_streams a <文件>      # 只看音频流
```

## 2. 概念 → 字段映射

### 2.1 容器（`-show_format`）

| 概念 | 字段 | 示例值 |
|---|---|---|
| 容器格式 | `format_name` | `matroska,webm` |
| 容器全名 | `format_long_name` | `Matroska / WebM` |
| 时长 | `duration` | `3729.680000`（秒） |
| 总码率 | `bit_rate` | `10235617`（bps） |
| 元数据 | `tags` | 标题、专辑、语言等 |

### 2.2 视频流（`-select_streams v`）

| 概念 | 字段 | 示例值 |
|---|---|---|
| 编码器 | `codec_name` | `h264` / `hevc` / `av1` |
| 编码 profile | `profile` | `High` / `Main` |
| 分辨率 | `width` × `height` | `1920` × `1080` |
| 帧率 | `r_frame_rate` / `avg_frame_rate` | `24000/1001`（≈23.976） |
| 视频码率 | `bit_rate` | `8154340`（bps，缺失时可用 `-show_frames` 估） |
| 色度采样 | `pix_fmt` | `yuv420p`（=4:2:0）、`yuv422p`（=4:2:2）、`yuv444p`（=4:4:4） |
| 位深 | `pix_fmt` 尾缀 | `yuv420p10le` 的 `10` = 10-bit |
| 色彩范围 | `color_range` | `tv`（有限）/ `pc`（完整） |
| 色彩空间 | `color_space` | `bt709`（SDR）/ `bt2020nc`（HDR 宽色域） |
| HDR 传递函数 | `color_transfer` | `smpte2084`（PQ=HDR10）、`arib-std-b67`（HLG）、`bt709`（SDR） |

> **HDR 判断**：`color_transfer=smpte2084`（或 `arib-std-b67`）+ `color_space=bt2020nc` + `pix_fmt` 含 `10` → HDR10（或 HLG）。三者齐备才是标准 HDR 信号。

### 2.3 音频流（`-select_streams a`）

| 概念 | 字段 | 示例值 |
|---|---|---|
| 编码器 | `codec_name` | `aac` / `ac3` / `flac` |
| 采样率 | `sample_rate` | `48000`（Hz = 48 kHz） |
| 位深 | `bits_per_raw_sample` / `bits_per_sample` | `16` / `24`（PCM/FLAC 有；有损编码无） |
| 声道数 | `channels` | `2`（立体声）/ `6`（5.1） |
| 声道布局 | `channel_layout` | `stereo` / `5.1` |
| 音频码率 | `bit_rate` | `192000`（bps） |

### 2.4 字幕流（`-select_streams s`）

| 概念 | 字段 | 示例值 |
|---|---|---|
| 字幕编码 | `codec_name` | `subrip`（SRT）、`ass`、`hdmv_pgs_subtitle`（PGS）、`dvd_subtitle`（VobSub） |
| 语言 | `tags.language` | `chi` / `eng` |
| 类型判断 | `codec_name` | 文本类（subrip/ass/webvtt）vs 图形类（hdmv_pgs_subtitle/dvd_subtitle） |

## 3. 完整示例

```bash
$ ffprobe -show_format -show_streams -of json movie.mkv
```

关键片段解读：

```json
"format": {
  "format_name": "matroska,webm",          // 容器 = MKV
  "duration": "3729.68",
  "bit_rate": "10235617"                    // 文件总码率 ≈ 10.2 Mbps
},
"streams": [
  {
    "index": 0,
    "codec_name": "h264",                  // 视频流：H.264
    "width": 1920, "height": 1080,         // 分辨率 1080p
    "r_frame_rate": "24000/1001",          // 帧率 ≈ 23.976 fps
    "pix_fmt": "yuv420p",                  // 色度 4:2:0，8-bit
    "color_transfer": "bt709",             // SDR（不是 HDR）
    "bit_rate": "8154340"                  // 视频码率 ≈ 8.2 Mbps
  },
  {
    "index": 1,
    "codec_name": "aac",                   // 音频流：AAC
    "sample_rate": "48000",                // 48 kHz
    "channels": 6, "channel_layout": "5.1", // 5.1 环绕
    "tags": { "language": "chi" }
  },
  {
    "index": 2,
    "codec_name": "hdmv_pgs_subtitle",     // 字幕流：PGS 图形字幕
    "tags": { "language": "chi" }
  }
]
```

这段输出说明：`movie.mkv` 是一个 MKV 容器，内含一条 H.264/1080p/23.976fps/SDR 视频流、一条 AAC 5.1 中语音频流、一条 PGS 中文字幕流。

## 4. 实用命令速查

```bash
# 只看容器格式与时长
ffprobe -v error -show_entries format=format_name,duration -of default=noprint_wrappers=1 <文件>

# 只看视频流的分辨率、帧率、编码
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 <文件>

# 列出所有流的索引与编码（判断有几条音轨/字幕）
ffprobe -v error -show_entries stream=index,codec_type,codec_name -of csv <文件>

# 判断是否 HDR
ffprobe -v error -select_streams v:0 -show_entries stream=color_space,color_transfer,pix_fmt -of default=noprint_wrappers=1 <文件>
```

> 字段名（`r_frame_rate`、`color_transfer` 等）在不同 ffprobe 版本间稳定，但个别媒体文件可能缺失部分字段（尤其是流码率 `bit_rate`）——缺失时属正常，不代表文件有问题。
