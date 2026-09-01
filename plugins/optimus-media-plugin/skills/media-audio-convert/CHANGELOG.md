# Changelog

## [1.0.0] - 2026-09-01

### Added
- 新增 media-audio-convert skill：纯音频到纯音频的格式转换（wav→mp3、flac→aac 等）与参数调整（码率/采样率/声道数），承接此前 media-convert 明确排除的"纯音频格式转换"能力
- Step 0-3 前置校验引用 `../media-ffmpeg-common/PREFLIGHT.md`，不重复维护流程骨架
- Step 4 以 ffprobe 查**真实编码**（不依据扩展名推断）后按 5 类损失性质分流：无损→无损、无损→有损（首次有损）、有损→有损（二次有损，重点告知）、有损→无损（无意义放大）、编码相同仅容器不同（走重封装而非转码）
- Step 5 三种命令模式：重新编码、重封装（`-c:a copy`）、带 `-ar`/`-ac` 参数调整；含 6 种输出扩展名对应的编码器与"是否接受 `-b:a`"对照表
- 概念引用指向 `knowledge-base/media/reference/` 的 `audio-container-formats.md` §2/§3（后缀≠真实编码的判断方法）、`audio-codecs.md` §1（有损/无损分类）、`audio-parameters.md` §1/§3（采样率与声道数）——此前这三份 reference 无任何 skill 消费
- 「失败处理」含 5 条特有场景（编码器缺失、重封装 codec tag 报错、体积反增、误传视频文件、二次有损音质下降）；「不要做什么」含 9 条特有反例
