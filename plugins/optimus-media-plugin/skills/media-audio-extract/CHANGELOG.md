# Changelog

## [1.0.3] - 2026-09-01

### Fixed
- 与 media-audio-convert 统一收口二次有损的表述：1.0.2 只是把"约 0.5 dB"换成了"典型 0.1–0.4 dB、最多约 3.5 dB"，仍是给固定量级。media-audio-convert 的验证 judge 用 3 素材 × 2 编码 × 5 码率共 16 组 `asdr` 测量得出真实跨度 **0.02～28.7 dB**（机制：二代信噪比被一代封顶），故 1.0.2 的区间同样不成立。现改为禁止给出任何固定量级，只保留实测中唯一无例外的方向结论"只会更差、不会更好"
- 删除 1.0.2 残留的禁令式措辞"不要声称损失比首次压缩明显"：在高码率源配置下二次降幅可达 28.7 dB，该禁令会让 agent **少报**真实风险

### Added
- Step 4 补充 `bit_rate` 探测边界说明：mkv 容器不在流头部存码率，实测其中音频流与视频流的 `bit_rate` **均为 `N/A`**（mp4 里的 aac 正常返回 59997）。明确**不得用 `format=bit_rate` 顶替**——本 skill 输入含视频流，format 级是总码率（实测同一文件 489595 bps），据此选码率会严重高估
- Step 5 码率取值表新增"取不到（`N/A`，常见于 mkv）"一档：🔴 CHECKPOINT 向用户说明源码率无法探测并询问，不得默默套用 192k
- 反例清单新增 1 条（不得用 `format=bit_rate` 顶替音频码率），并在"不要固定用 192k"一条中补充源码率为 `N/A` 时的处理

## [1.0.2] - 2026-09-01

### Fixed
- 撤销 1.0.1 引入的错误陈述「`.wav` 是唯一不会报错的不兼容目标」。验证轮 judge 跑了 6 种编码 × 7 种扩展名的完整流复制矩阵，该说法在两个方向上都被推翻：① `.wav` 并非唯一静默成功的目标——`flac`→`.opus`/`.ogg` 同样退出码 0 且无告警，产出"扩展名声称 Opus、内容是 FLAC"的文件，且解码完全正常、数据无损，比 `.wav` 错配更难发现；② `.wav` 也不一律静默——`alac`/`opus`→`.wav` 会报第四种措辞 `Codec <编码> not supported in WAVE format`。实际分布是 aac/mp3/flac 静默、alac/opus 报错
- 改写后的表述不再按扩展名区分"哪些会静默"，而是要求一律由 Step 4 的兼容表在执行前拦截，并明确规律不可按扩展名推断——这比原表述更保守也更准确
- 修正两处数字过度泛化：二次有损的额外信噪比降幅由"约 0.5 dB"改为"典型场景 0.1–0.4 dB、高码率源最多约 3.5 dB"（judge 用粉红噪声跑 6 条编码路线，4 条落在 0.09–0.39 dB，2 条达 2.9/3.5 dB；但首次有损是从无损直接掉到十几 dB 量级，故"二次损失小于首次"的结论在全部路线上都成立）；60k 源套 192k 的体积倍数由"3 倍"改为"2.6～3.1 倍（随编码器而异）"——mp3 为 3.10×、aac 为 2.59×

### Added
- 失败表新增 `Codec <编码> not supported in WAVE format` 报错串；容器/编码错配那一行从只覆盖 `.wav` 扩展到覆盖 `.opus`/`.ogg`，并说明两类错配的发现方式不同（wav 解码报错但退出码 0，opus/ogg 解码完全正常，只能核对 `format_name` 与 `codec_name` 是否匹配）
- 反例清单新增 2 条：不得预设不兼容组合会自己报错来兜底；不得把"扩展名与 `format_name` 一致"当作成功判据

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
