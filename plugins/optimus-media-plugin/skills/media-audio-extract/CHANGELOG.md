# Changelog

## [1.0.1] - 2026-09-01

### Fixed
- 修正失败表硬编码的报错串：原写的 `Could not find tag for codec aac in stream #0` 实测仅出现在 ipod/mov muxer 场景，aac→`.mp3` 真实报错是 `Invalid audio stream. Exactly one MP3 audio stream is required.`、alac→`.aac` 是 `adts muxer supports only codec aac for type audio`。改为并列三种 muxer 的实测串，并明确判据应是"流复制失败"这一事实而非匹配单一措辞
- 修正多音轨的症状描述：原写"提取出的音频文件时长与源视频不一致"，实测多语言音轨时长通常一致（双轨均为 5.000000），无法靠时长察觉；真实症状是取到的不是用户想要的那条轨
- 修正「无损编码器不接受 `-b:a`」的表述：实测传入不报错、不告警，属完全无效参数（带与不带产物 MD5 相同）。改为说明它无效且会误导，而非声称会失败
- 修正情况⑤对二次有损代价的描述：不再声称"音质损失比首次压缩明显"（实测二者信噪比仅差约 0.5 dB），改为"只会更差、不会更好"，并要求按源编码是否有损分别说明
- 体积走向不再给方向固定的结论，改为对照源 `bit_rate` 与目标码率据实说明

### Added
- Step 4 探测命令改为一条列出全部流的 `stream=index,codec_type,codec_name,bit_rate`，取代原先的 `-select_streams a:0 -show_entries stream=codec_name`。原命令只探一个字段，导致下列四项判定全部缺失或失守
- Step 4 新增情况②「源文件无视频流」硬约束：纯音频输入不属本 skill 语义，终止并指向 media-audio-convert。判据是有无 `codec_type=video` 行——纯音频文件同样返回退出码 0 与正常音频编码（实测 wav 返回 `pcm_s16le`），只看音频信息无法区分
- Step 4 新增情况③「多条音频流」🔴 CHECKPOINT：列出各轨索引/编码/码率/语言标签让用户指认
- Step 5 命令补 `-map 0:a:0`：不带 `-map` 时 ffmpeg 按 disposition 挑"最佳"轨，与按索引取的 `a:0` 未必同一条。实测把 `default` 标记移到第二条轨后，不带 `-map` 复制的是第二条（196620bps）、带 `-map` 是第一条（56137bps），产物 md5 不同——这会让 Step 4 的探测对象与实际提取的流不一致，兼容性判定张冠李戴
- Step 5 的 `-b:a` 由固定 192k 改为依据源码率取值，附三档取值表。实测源 60k 的音轨套用 192k，产出体积是源的 3 倍且无音质收益
- Step 4 情况⑤ 新增 `.wav` 专项 ⛔ 警告：其余容器遇到装不下的编码会报错，而 `-c:a copy` 写入 `.wav` 会以退出码 0 静默成功，产出 `format_name=wav`/`codec_name=aac` 的错配文件
- 失败表新增 3 条（`.wav` 静默错配、`Stream map '' matches no streams.`、解码报错但退出码 0）；反例清单新增 8 条

## [1.0.0] - 2026-09-01

### Added
- 新增 media-audio-extract skill：从视频中提取音频流产出纯音频文件，默认 `-vn -c:a copy` 流复制无损搬运，仅在目标扩展名装不下源音频编码时降级为重新编码
- Step 0-3 前置校验引用 `../media-ffmpeg-common/PREFLIGHT.md`，不重复维护流程骨架
- Step 4 执行前校验三分支：① 源无音频流（硬约束终止）② 源编码与目标扩展名兼容（走流复制）③ 不兼容（🔴 CHECKPOINT 告知可能为二次有损，用户确认后转码），含 7 种常见编码的无损搬运扩展名对照表
- 概念引用指向 `knowledge-base/media/reference/` 的 `audio-container-formats.md`（容器与编码关系、后缀≠编码）、`audio-codecs.md`（编码选型）、`audio-parameters.md`（码率与音质）——此前这三份 reference 无任何 skill 消费
- 「失败处理」含 4 条特有场景（codec tag 报错、音频编码器缺失、多音轨只取 a:0、静音轨）；「不要做什么」含 9 条特有反例
