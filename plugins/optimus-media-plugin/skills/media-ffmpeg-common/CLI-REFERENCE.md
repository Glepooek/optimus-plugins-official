# ffmpeg 命令行参数速查

仅覆盖本插件各 skill 实际用到的参数，不是 ffmpeg 完整参数手册。覆盖范围：media-analyze、media-resize、media-compress、media-trim、media-play、media-framerate、media-convert、media-audio-extract、media-audio-convert、media-frame-extract（media-download 用 yt-dlp，参数见其 SKILL.md）。

| 参数 | 用途 | 使用场景 |
|---|---|---|
| `-i <file>` | 指定输入文件 | 全部 |
| `-c:v <编码器>` | 指定视频编码器，如 `libx264` | media-resize、media-compress、media-trim 精确模式、media-convert 转码模式、media-framerate |
| `-c:a <编码器>` | 指定音频编码器，如 `aac` | media-compress、media-trim 精确模式、media-convert 转码模式 |
| `-crf <0-51>` | 画质因子，数值越小画质越好、文件越大；0 为无损，51 为最差 | media-compress（唯一按用户画质偏好可调的 skill）、media-resize / media-trim 精确模式 / media-framerate / media-convert 转码模式（固定取 18 的画质档位，非压缩旋钮，不随用户偏好调整） |
| `-preset <速度档位>` | 编码速度与压缩率的权衡：`ultrafast`/`fast`/`medium`/`slow`/`veryslow`，越慢压缩率越高 | media-compress |
| `-vf scale=W:H` | 视频分辨率缩放；`W`或`H`填 `-2` 表示按另一边等比例计算并保证结果为偶数 | media-resize |
| `-ss <时间点>` | 起始时间点，格式 `HH:MM:SS` 或秒数；放在 `-i` 之前是快速的输入端 seek（对齐到最近关键帧），放在 `-i` 之后是精确的输出端 seek（帧精确但慢） | media-trim |
| `-to <时间点>` | 结束时间点，格式同 `-ss` | media-trim |
| `-c copy` | 流复制，不重新编码，速度极快 | media-trim 快速模式、media-resize 音频透传（`-c:a copy`）、media-convert remux 模式 |
| `-y` | 覆盖已存在的输出文件，不交互询问 | 全部产出文件的 skill，固定放在命令最前，不得省略；覆盖策略见 `PREFLIGHT.md` |
| `-window_title <标题>` | 设置 ffplay 播放窗口标题 | media-play |
| `-autoexit` | 播放结束后自动关闭窗口退出，无需手动操作 | media-play |
| `-r <帧率>` | 设定输出帧率；高于原始帧率时机械复制已有帧，低于原始帧率时均匀丢帧 | media-framerate 简单模式 |
| `-filter:v "minterpolate=fps=<帧率>"` | 运动补偿插帧滤镜，分析相邻帧运动矢量生成中间帧，仅用于提高帧率 | media-framerate 运动插帧模式 |
| `-b:v <码率>` | 指定视频目标码率，与 `-crf` 互斥，二选一 | media-compress 目标码率模式 |
| `-pass <1\|2>` | 两轮编码（two-pass）的轮次标记；第一轮分析画面复杂度分布，第二轮据此精确分配码率 | media-compress 目标码率模式 |
| `-an` | 禁用音频流，仅处理视频；用于两轮编码第一轮不产出音频以节省分析时间 | media-compress 目标码率模式第一轮 |
| `-vn` | 禁用视频流，仅保留音频；与 `-an` 互为镜像 | media-audio-extract（丢弃画面只取音轨，不可省略） |
| `-c:a copy` | 音频流复制，不解码不重编码，音频数据无损；但容器级元数据可能丢失（如 `.m4a`→`.aac` 会丢 gapless 播放信息） | media-audio-extract 默认模式、media-audio-convert 重封装模式 |
| `-b:a <码率>` | 音频目标码率，如 `192k`。无损编码器（`flac`/`pcm_s16le`/`alac`）应省略——传入不报错也不告警，属完全无效参数 | media-compress（固定 128k）、media-audio-extract / media-audio-convert 重新编码模式（依源码率取值，不固定 192k） |
| `-map 0:a:<索引>` | 显式指定处理第 N 条音频流（按索引，`0` 为第一条）。不带 `-map` 时 ffmpeg 按流的 disposition 挑"最佳"轨，与按索引取的 `a:0` 未必是同一条 | media-audio-extract（不可省略，保证探测对象与提取对象一致） |
| `-ar <采样率>` | 音频采样率，如 `44100`；不传则沿用源文件采样率，不要主动"标准化" | media-audio-convert（仅用户明确要求时） |
| `-ac <声道数>` | 音频声道数，`1` 为单声道、`2` 为立体声；缩混不可逆 | media-audio-convert（仅用户明确要求时） |
| `-frames:v <帧数>` | 输出指定帧数后停止；截图取 `1`。必须与 `-update 1` 成对使用：只带 `-update 1` 而漏掉本参数，会一路解码到结尾并把输出覆盖成末帧（退出码 0、无报错）；两者都漏则写第二帧时报错中断 | media-frame-extract 单帧模式（不可省略） |
| `-update 1` | 允许反复写入同一个输出文件名，用于产出单张图片。不带它时 image2 muxer 每次都会打印"文件名不含序号 pattern"的警告——产出正确但易被误判为执行失败 | media-frame-extract 单帧模式（不可省略，与 `-frames:v 1` 成对） |
| `-vf fps=1/<秒数>` | 滤镜层按固定时间间隔抽帧，如 `fps=1/60` 为每 60 秒一帧。与 `-r`（在输出端丢帧改变帧率）机制不同，产出张数也不同——同一 5 秒视频 `-r 0.5` 得 4 张、`-vf fps=1/2` 得 3 张 | media-frame-extract 多帧等间隔模式 |
| `%03d` | 输出文件名中的序号占位符，产出 `_001`/`_002` 递增编号。多帧输出省略会让 image2 muxer 在写第二张时报 `Error muxing a packet: Invalid argument` 并中断，残留文件是序列**第一张**（不是最后一张） | media-frame-extract 多帧等间隔模式（不可省略） |

## 概念解释

上表参数背后的媒体概念（关键帧对齐、CRF/码率控制、流复制 vs 转码、帧率与插帧）以 `knowledge-base/media/` 为唯一概念来源，参数表只做命令定位：

- `-crf` / `-preset` / `-b:v` / `-pass` 的码率控制与两轮编码概念 → [`knowledge-base/media/reference/video-quality.md`](../../../../knowledge-base/media/reference/video-quality.md) §2「码率控制模式」
- `-c copy` 流复制 / `-c:v` 转码 → [`knowledge-base/media/reference/media-stream-basics.md`](../../../../knowledge-base/media/reference/media-stream-basics.md) §3「转码、重封装、流复制」
- `-ss` 对齐到最近关键帧 → `video-codecs.md` 的「关键帧（I / P / B 帧）与 GOP」小节
- `-r` / `minterpolate` 的帧率与插帧机制 → [`knowledge-base/media/reference/media-parameters.md`](../../../../knowledge-base/media/reference/media-parameters.md) §2「帧率」
- `-b:a` / `-ar` / `-ac` 的音频码率、采样率、声道数概念 → [`knowledge-base/media/reference/audio-parameters.md`](../../../../knowledge-base/media/reference/audio-parameters.md) §1「采样率」、§3「声道数」、§4「音频码率计算」
- `-c:a <编码器>` 的音频编码选型与有损/无损性质 → [`audio-codecs.md`](../../../../knowledge-base/media/reference/audio-codecs.md) §1「音频编码分类」、§4「怎么选」
- 音频容器与真实编码的关系（`-c:a copy` 能否搬入目标扩展名）→ [`audio-container-formats.md`](../../../../knowledge-base/media/reference/audio-container-formats.md) §3「后缀 vs 编码的判断方法」
- `-ss` + `-frames:v` 截图为何无需区分快速/精确模式（关键帧与解码）→ `video-codecs.md` 的「关键帧（I / P / B 帧）与 GOP」小节
