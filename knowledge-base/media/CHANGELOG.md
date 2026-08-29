# Changelog — 媒体处理概念

本领域自 7.2.1 起使用**独立版本号**。7.2.0 及之前为知识库统一全局版本号时代，相关条目见下方「全局版本时代」，其版本号为当时的全局版本。

## [7.2.1] - 2026-08-29

### Changed
- 领域元数据文件 `00-README.md` 改名为 `README.md`

---

## 全局版本时代（2026-08-22 .. 2026-08-29）

### 衍生自全局 1.10.4 - 2026-08-26

- `media/reference/media-parameters.md` 扩展：§2 帧率新增「提高帧率的两种方式」（复制帧 vs 运动插帧）与「降低帧率=丢帧」；§4 新增「由目标体积反推目标码率」（two-pass 场景的 `目标大小×8192÷时长−音频码率` 公式及 8192 的进制来源）
- `media/reference/video-codecs.md` §1 新增「关键帧（I/P/B 帧）与 GOP」小节：帧间预测、关键帧间隔与 seek/截取精度的权衡、`-c copy` 对齐关键帧的实际影响
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-codecs` 的 `summary`/`tags`

### 衍生自全局 1.10.3 - 2026-08-26

- `media/reference/streaming-protocols.md` 第 8 节扩展为「与 ffprobe / ffplay 的关系」：新增 ffplay 能直接播放 HLS/RTSP/RTMP 网络流的说明与命令示例，及 RTSP TCP 传输、RTMP 构建依赖、直播不可回拖、DRM 不可解密等注意点
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `tags`/`summary`（新增 `ffplay` 标签）

### 衍生自全局 1.10.2 - 2026-08-26

- `media/reference/streaming-protocols.md` 重构为面向零基础读者的通俗版：新增"为什么切分片"问题引入、播放器播放 HLS 的 4 步流程、各协议 URL 实例与一句话人话总结、CDN 说明、文末术语速查表，并在常见误区补充"扩展名非铁律"条目
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `summary`

### 衍生自全局 1.10.1 - 2026-08-26

- `media/reference/streaming-protocols.md`：标题改为"流媒体传输与分发协议：HLS、RTMP、RTSP、DASH 与 WebRTC"（去除 M3U8 平列与赘余的"与相关协议"）；将 M3U8 并入 HLS 章节作为其播放清单组件介绍，并展开 HLS 完整组成——分片、两级清单（Media/Master Playlist）、码率自适应、加密与 DRM、直播/点播差异
- `media/index.jsonl` 同步更新 `media.ref.streaming-protocols` 的 `title`/`summary`

### 衍生自全局 1.10.0 - 2026-08-26

- `media` 领域新增 `reference/streaming-protocols.md`：流媒体传输与分发协议讲解——M3U8 播放清单、HLS/DASH HTTP 分片分发、RTMP 推流、RTSP 会话控制协议、WebRTC 实时互动，及直播生态推流/分发/互动分工
- `media/index.jsonl` 登记 1 条 reference 索引记录 `media.ref.streaming-protocols`
- `media/00-README.md` 阅读路径与文件地图同步补充 streaming-protocols 条目

### 衍生自全局 1.9.1 - 2026-08-26

- `media/reference/media-parameters.md` 扩展：新增常用视频比例表（16:9/4:3/21:9/9:16/1:1）与横屏/竖屏判定方法、码率单位进制换算（码率 1000 进制 vs 存储 1024 进制、bit 与 Byte 换算）
- `media/reference/video-quality.md` 扩展：新增第 6 节 LUT（Look-Up Table）——1D/3D LUT 机制、常见文件格式、与 HDR/SDR 色调映射的关系、常见注意点
- `media/index.jsonl` 同步更新 `media.ref.media-parameters`、`media.ref.video-quality` 的 `summary`/`tags`/`title`

### 衍生自全局 1.9.0 - 2026-08-26

- 新增 `media` 领域：纯描述性知识库（无规范条款，全部为 reference），含 10 篇参考文档——媒体流结构基础、视频/音频封装格式、视频/音频编解码器、媒体参数（分辨率/帧率/码率）、音频参数（采样率/位深/声道）、视频质量（有损无损/CRF/HDR/色度采样）、字幕格式、ffprobe 字段映射
- `media/index.jsonl` 登记 10 条 reference 索引记录
