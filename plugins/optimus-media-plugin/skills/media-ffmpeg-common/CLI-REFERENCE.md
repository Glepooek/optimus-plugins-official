# ffmpeg 命令行参数速查

仅覆盖 media-analyze/media-resize/media-compress/media-trim/media-play/media-framerate 六个 skill 实际用到的参数，不是 ffmpeg 完整参数手册。

| 参数 | 用途 | 使用场景 |
|---|---|---|
| `-i <file>` | 指定输入文件 | 全部 |
| `-c:v <编码器>` | 指定视频编码器，如 `libx264` | media-compress、media-trim 精确模式 |
| `-c:a <编码器>` | 指定音频编码器，如 `aac` | media-compress、media-trim 精确模式 |
| `-crf <0-51>` | 画质因子，数值越小画质越好、文件越大；0 为无损，51 为最差 | media-compress |
| `-preset <速度档位>` | 编码速度与压缩率的权衡：`ultrafast`/`fast`/`medium`/`slow`/`veryslow`，越慢压缩率越高 | media-compress |
| `-vf scale=W:H` | 视频分辨率缩放；`W`或`H`填 `-2` 表示按另一边等比例计算并保证结果为偶数 | media-resize |
| `-ss <时间点>` | 起始时间点，格式 `HH:MM:SS` 或秒数；放在 `-i` 之前是快速的输入端 seek（对齐到最近关键帧），放在 `-i` 之后是精确的输出端 seek（帧精确但慢） | media-trim |
| `-to <时间点>` | 结束时间点，格式同 `-ss` | media-trim |
| `-c copy` | 流复制，不重新编码，速度极快 | media-trim 快速模式、media-resize 音频透传（`-c:a copy`） |
| `-y` | 覆盖已存在的输出文件，不交互询问 | 全部 |
| `-window_title <标题>` | 设置 ffplay 播放窗口标题 | media-play |
| `-autoexit` | 播放结束后自动关闭窗口退出，无需手动操作 | media-play |
| `-r <帧率>` | 设定输出帧率；高于原始帧率时机械复制已有帧，低于原始帧率时均匀丢帧 | media-framerate 简单模式 |
| `-filter:v "minterpolate=fps=<帧率>"` | 运动补偿插帧滤镜，分析相邻帧运动矢量生成中间帧，仅用于提高帧率 | media-framerate 运动插帧模式 |
| `-b:v <码率>` | 指定视频目标码率，与 `-crf` 互斥，二选一 | media-compress 目标码率模式 |
| `-pass <1\|2>` | 两轮编码（two-pass）的轮次标记；第一轮分析画面复杂度分布，第二轮据此精确分配码率 | media-compress 目标码率模式 |
| `-an` | 禁用音频流，仅处理视频；用于两轮编码第一轮不产出音频以节省分析时间 | media-compress 目标码率模式第一轮 |
