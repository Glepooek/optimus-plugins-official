# Media 领域知识库

> 版本：7.2.2

> 面向媒体处理的**描述性知识库**。当前无规范条款，全部内容为 `reference/` 下的参考文档——解释"视频封装格式、编解码器、分辨率、帧率、码率、字幕"等概念及其关系，供媒体分析、转换、压缩、播放等场景查阅。

## 文档目的

解释媒体文件处理中高频出现的概念：封装格式、编解码器、分辨率/帧率/码率等参数、字幕格式，以及它们之间的关系。目标读者通过本领域能快速建立"一个媒体文件是什么、由什么构成、各参数意味着什么"的认知，从而正确选择处理方式（转码还是重封装、压缩参数怎么定、分辨率/帧率如何调整）。

本领域**只收参考性文档，不收规范条款**——承载强制判断的 MUST/SHOULD/MAY 条款不在本领域范围内。后续若产生强制规范（如"转码必须使用某编码器"），需另行规划，本领域保持不变。

## 适用范围与读者

- **适用范围**：视频/音频文件的分析、转换、压缩、播放、下载等处理场景
- **读者**：所有参与媒体处理相关工作的成员；media 插件族（`analyze`/`convert`/`compress`/`play`/`resize`/`framerate` 等）的设计者与使用者

## 规范级别

本领域**暂无规范条款**，不定义 MUST/SHOULD/MAY 级别体系。`reference/` 下的文档全部为描述性知识，语气客观中立，不构成强制约束——内容是事实性解释（某格式支持什么、某参数如何计算、两者有何差别），不表达"必须怎样做"的判定。

## 阅读路径

| 场景 | 参考文档 |
|---|---|
| 初次理解媒体文件由什么构成 | `reference/media-stream-basics.md` |
| 判断某个文件是什么格式/编码 | `reference/media-stream-basics.md`、`reference/video-container-formats.md`、`reference/audio-container-formats.md` |
| 转码选型（用什么容器、编码器） | `reference/video-container-formats.md`、`reference/video-codecs.md`、`reference/audio-codecs.md` |
| 调整分辨率 / 帧率 / 码率 | `reference/media-parameters.md` |
| 处理音频（采样率 / 位深 / 声道） | `reference/audio-parameters.md` |
| 压缩与保画质 | `reference/video-quality.md` |
| 字幕处理 | `reference/subtitles.md` |
| 分析某个具体文件、读取各项参数 | `reference/ffprobe-field-map.md` |
| 理解网络流地址（M3U8/HLS/RTMP/RTSP） | `reference/streaming-protocols.md` |

## 文件地图

| 文件 | 主题 |
|---|---|
| `reference/media-stream-basics.md` | 媒体文件结构：容器与流、转码 / 重封装 / 流复制 |
| `reference/video-container-formats.md` | 视频封装格式与常见容器对比 |
| `reference/audio-container-formats.md` | 音频封装格式、文件后缀与真实编码辨析 |
| `reference/video-codecs.md` | 视频编解码器对比与选型 |
| `reference/audio-codecs.md` | 音频编解码器对比与选型 |
| `reference/media-parameters.md` | 分辨率、帧率、码率及其关系 |
| `reference/audio-parameters.md` | 音频采样率、位深、声道数 |
| `reference/video-quality.md` | 有损 / 无损、码率控制、色度采样、位深与 HDR |
| `reference/subtitles.md` | 视频字幕的形态与格式对比 |
| `reference/ffprobe-field-map.md` | ffprobe 输出字段与各概念的映射 |
| `reference/streaming-protocols.md` | 流媒体传输与分发协议 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。本领域全部条目为 `reference` 类型，`anchor` 字段留空。

## 更新与维护

- 新增 / 修改参考文档时，同一次提交里同步更新对应 `index.jsonl`
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" media` 做一致性自检
- 内容要求事实准确、可追溯到公开资料；格式与编码的规格数据以主流标准及 ffmpeg / ffprobe 生态实测为准

## 与仓库已有资产的关系

- `plugins/optimus-media-plugin/skills/*`：media 插件族的分析 / 转换 / 压缩 / 播放判断依据，可从本领域取得概念参考
