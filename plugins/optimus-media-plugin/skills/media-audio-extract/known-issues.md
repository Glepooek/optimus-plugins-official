# known-issues

真实使用中暴露的问题记录。发现当下一行带过即可，不必整理成完整 bug report。"待处理"条目累积满 3 条时，发起一次 darwin-skill 优化循环（须人工在对话中显式发起）。已解决的条目改状态为"已优化"并标注版本号，**不删除**——保留可追溯的问题史。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-01 | **失败表硬编码的报错串在最典型场景下对不上**：文档写 `Could not find tag for codec aac in stream #0`，该串实测仅出现在 ipod/m4a muxer 场景（如 flac→`.m4a`）。aac→`.mp3` 的真实报错是 `Invalid audio stream. Exactly one MP3 audio stream is required.`，alac→`.aac` 是 `adts muxer supports only codec aac for type audio`——最常见的两种不兼容组合都无匹配行 | 用户要求把 mp4 里的 aac 音轨存成 `.mp3` 并保持无损 | 已优化 | 1.0.1 |
| 2026-09-01 | **`-c:a copy` 写入 `.wav` 静默成功**（退出码 0，无警告），产出 `format_name=wav` 但 `codec_name=aac` 的容器/编码错配文件，后续解码报 `Input buffer exhausted before END element found`。两名 judge 独立复现。文档未收录该现象，兼容性对照表把 wav 归入需重编码分支但无拦截 | 用户要求提取音轨为 `.wav` 且明示"不要重新编码" | 已优化 | 1.0.1 |
| 2026-09-01 | **Step 4 未探测 `bit_rate`**，导致 Step 5 只能硬编码 `-b:a 192k`。源码率 59997bps 的样本重编码后体积 **3.0×** 劣化——同一默认值在 media-audio-convert 是 +4.45dB 提升、在本 skill 是纯劣化，差别仅在源码率 | 从低码率视频（如录屏、语音录制）提取音轨且需重编码 | 已优化 | 1.0.1 |
| 2026-09-01 | **纯音频输入拦不住**：`ffprobe -select_streams a:0 -show_entries stream=codec_name` 对纯音频文件同样返回 `codec_name=aac`、退出码 0，与含视频的文件输出完全一致。"输入应为含音轨的视频"这条边界只活在「不要做什么」的文字里，无探测支撑。低成本修法：改查 `codec_type`，或同时探测 `v:0` 是否存在 | 用户误把 `.m4a` 当视频要求"提取音轨" | 已优化 | 1.0.1 |
| 2026-09-01 | **多音轨的症状描述写错**：文档称会表现为"时长不一致"，实测双轨样本两轨时长一致（5.000000 / 5.000000）。真实症状是**静默取错轨**——用户拿到的是第一条轨而非想要的那条，且无任何提示 | 多语言音轨的视频（如带国配+原声） | 已优化 | 1.0.1 |
| 2026-09-01 | Step 5 命令缺 `-map 0:a:0`。基线评估时 judge 未能构造出分歧样本，暂记为隐患；**修复轮已复现并确认为 bug**：`-map 0:a:0` 按索引取第一条音频流，而不带 `-map` 时 ffmpeg 按 disposition 挑"最佳"轨，判据不同。把 `default` 标记移到第二条轨后，不带 `-map` 复制的是第二条（196620bps）、带 `-map` 是第一条（56137bps），产物 md5 不同。后果不止"选错轨"——Step 4 探测的是 `a:0`，Step 5 复制的可能是另一条，两轨编码不同时兼容性判定会张冠李戴 | 多音轨视频，且 `default` 标记不在第一条音轨上 | 已优化 | 1.0.1 |

> 以上 6 条均来自 2026-09-01 darwin-skill 基线评估（`eval_mode=full_test`，独立 judge 用真实 ffmpeg 样本实测），dim8 得 7/10，总分 80.7（三个新 skill 中最低）。
>
> 结构维度最弱的是 dim3 失败模式（7）与 dim4 检查点（6-7）：Step 0-3 外置到 `../media-ffmpeg-common/PREFLIGHT.md` 后，本文件内的显性 🔴/⛔ 标记仅剩 2 个，而 dim4 正是靠扫描视觉标记评分的维度。修复时需注意这是**外置带来的副作用**，不是设计缺陷——不应为凑标记数量把 PREFLIGHT 内容抄回来。
