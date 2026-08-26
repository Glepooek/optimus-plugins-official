# Changelog

## [1.1.0] - 2026-08-26

### Added
- 新增网络流播放支持：播放目标区分为"本地文件播放"与"网络流播放"两种形态；Step 2 按含 `://` 协议头判断类型并走对应校验路径（本地文件→存在性校验，网络流 URL→格式校验）；Step 3 按类型选择命令模板（HLS/RTMP 网络流、RTSP 加 `-rtsp_transport tcp`）
- 失败处理新增网络流特有场景：连接失败/无法解析、RTSP 花屏（改 TCP）、RTMP 构建缺协议、DRM 不可解密、直播流不可回拖
- 触发词补充"播放这个链接/播放网络流/播放m3u8/播放rtsp流"；网络流协议概念引用 `knowledge-base/media/reference/streaming-protocols.md`

## [1.0.0] - 2026-08-13

### Added
- 新增 media-play skill：基于 ffplay 播放单个音视频文件，后台非阻塞启动播放窗口，播放结束自动关闭
