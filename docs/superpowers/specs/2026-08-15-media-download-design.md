# media-download 设计文档

## 背景

用户提出需求：调研 Edge/Chrome 浏览器插件 Video DownloadHelper（VDH）与配套的 CoApp（Companion App）结合下载互联网视频的实现原理，评估是否可以做成一个 Claude Code skill。

调研结论（详见对话记录，来源 [aclap-dev/vdhcoapp](https://github.com/aclap-dev/vdhcoapp/)、[DeepWiki 架构解析](https://deepwiki.com/aclap-dev/vdhcoapp)）：

- VDH 的媒体嗅探能力（识别页面中的 HLS/DASH manifest、blob 流、直链媒体）依赖浏览器扩展的 `webRequest` 等权限，运行在浏览器进程内，观察 tab 的实时网络请求。
- CoApp 只是受 Native Messaging 协议（stdio + 长度前缀 JSON）驱动的越权代理，用来绕开浏览器沙箱做文件写入和调用内置 ffmpeg，不能独立运行、不支持命令行调用。
- 两者绑定在浏览器扩展进程模型上，Claude Code 运行在终端环境，没有等价的"观察浏览器 tab 网络请求"能力，照搬该架构等于重新实现一个浏览器扩展，成本收益不成比例。

因此确定的方向是：不复刻 VDH+CoApp 架构，而是用 **yt-dlp**（业界公认的 VDH 命令行等价物，原生支持数千个站点的 HLS/DASH 提取）替代"嗅探浏览器流量"这一步，配合仓库已有的 ffmpeg 工具链，实现"给一个视频页面/直链 URL → 下载到本地"的等价能力。

## 定位

新增 `plugins/optimus-media-plugin/skills/media-download/`，与现有 6 个 `media-*` skill（analyze/compress/resize/trim/framerate/play）同级并列，同属 `tool` 分类。

## 范围边界

**包含：**
- 单个视频/音频链接下载
- 下载前列出该视频所有可用格式/清晰度，用户挑选后再下载
- 下载后如需要合并音视频流（yt-dlp 分离下载高清视频流与音频流的常见情况），调用 ffmpeg 完成封装

**不包含（写入 description 的 "Not for..." 与 SKILL.md "不要做什么"）：**
- 播放列表/频道批量下载——仅支持单个视频链接
- 需要登录凭据（cookies）才能访问的内容——会员专享、地区限制内容一律直接报错终止，不引导用户提供 cookies
- 已下载文件的转码/压缩/截取/帧率转换——那是 trim/resize/compress/framerate 各自的职责，media-download 不重复实现，也不在自己内部自动衔接调用
- 不接入 `media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"顺序编排链条（trim→resize→framerate→compress）——该链条面向本地文件的多步编辑，media-download 产出即终态，用户若要继续编辑需另起请求

**使用范围限制方式：** 仅在 SKILL.md 中写明使用声明（仅限用户本人有权访问的内容、遵守所在平台服务条款，不用于规避版权保护措施），不做技术层面的站点白名单或额外拦截逻辑——技术限制不是这一层该做的事，也做不干净（yt-dlp 支持站点太多，白名单化不现实）。

## 依赖

- **yt-dlp**：本 skill 独有依赖，不是现有 5 个 skill 共享的 ffmpeg/ffprobe/ffplay。独立在 SKILL.md 的 `compatibility` 字段声明，不修改 `media-ffmpeg-common` 下的共享文档（INSTALL.md/REFERENCE.md/CLI-REFERENCE.md），避免这几份被 6 个 skill 共同引用的文档因一个新 skill 的专属依赖而变动，影响面降到最小。
- **ffmpeg**：复用现有 `../media-ffmpeg-common/INSTALL.md` 安装指引与 `REFERENCE.md` 的环境检测命令。用途：yt-dlp 下载到分离的视频流+音频流时，用 ffmpeg 做合并封装（yt-dlp 内部已经会调用系统 ffmpeg 做这一步，这里检测环境是为了给用户提前排障，不是本 skill 手动拼接 ffmpeg 命令）。

## 执行流程

```
Step 0  需求预告
        对比本 skill 需要的信息（视频 URL、输出路径）与用户已提供的信息，一次性列出缺失项统一询问。
        清晰度不算需求预告阶段的必需信息——必须先查询该视频实际可用格式后才能让用户选择，
        不能让用户凭空报一个可能不存在的清晰度。

Step 1  确认环境
        - yt-dlp --version（本 skill 独有依赖检测）
        - ffmpeg -version && ffprobe -version（复用 media-ffmpeg-common 检测命令）
        任一命令不存在：引导用户安装（yt-dlp 官方安装方式 / ../media-ffmpeg-common/INSTALL.md），终止任务。

Step 2  校验输入 URL
        校验用户提供的字符串是否为合法 URL 格式（协议头、基本结构），
        这一步是格式校验，不是"文件是否存在"检查——与其他 5 个 skill 的 Step 2（校验本地文件路径存在）
        有本质区别，不要混用判断逻辑。
        格式不合法：报错终止。

Step 3  确认输出路径
        🔴 CHECKPOINT：向用户确认保存路径，不得省略直接执行。
        确认后校验父目录是否存在且可写，不存在/不可写则报错终止；
        输出文件本身此刻不存在属正常状态，不作为失败条件。

Step 4  执行前校验：查询可用格式
        执行 `yt-dlp -F <url>` 列出该视频所有可用格式/清晰度。
        - 查询失败（网络错误、站点不支持、链接失效、需要登录凭据）：视为硬约束，
          返回具体错误原因，终止任务，不进入 Step 5。需要登录凭据的情形（yt-dlp 报
          "Sign in to confirm your age"/"This video is only available for registered users"
          等提示）明确告知用户本 skill 不支持此类内容，不引导配置 cookies。
        - 查询成功：向用户展示格式列表（format id、分辨率、编码、文件大小等 yt-dlp 原生输出），
          🔴 CHECKPOINT 用户选择具体 format id 后才能进入 Step 5。

Step 5  执行下载
        yt-dlp -f <format_id> -o <output> <url>
        若所选格式为分离的视频流+音频流，yt-dlp 会自动调用本机 ffmpeg 合并封装，
        本 skill 不需要手动拼接额外的 ffmpeg 合并命令。
```

## 失败处理

除 Step 1/2/3/4 中已描述的终止条件外，特有失败场景：

| 触发条件 | 处理 |
|---|---|
| yt-dlp 报 "Unsupported URL" | 说明该站点不在 yt-dlp 支持列表内，告知用户并终止，不尝试降级为通用网页抓取 |
| 下载中途网络中断 | 如实告知用户下载失败及具体原因，不自动重试；用户可自行决定是否重新触发本 skill |
| 用户选择的 format id 在 Step 4 列表之外 | 提示用户核对 Step 4 展示的可用列表重新选择，不代为猜测最接近的格式 |

## 不接入组合链条的原因

`media-ffmpeg-common/REFERENCE.md` 的组合请求编排链条（trim→resize→framerate→compress）面向的是"已有本地文件，多步编辑"场景，参与编排的前提是所有 skill 的输入输出都是本地文件路径。media-download 的输入是一个 URL 而非本地文件，语义上不属于这条编辑链的一环；产出本地文件后即完成任务，如用户要继续编辑，按现有约定另起一次请求触发 trim/resize/compress/framerate 即可，不需要 media-download 内部感知或调用它们。

## 不要做什么（预告 SKILL.md 用）

- 不支持播放列表/频道批量下载，仅处理单个视频链接
- 不支持需要登录凭据（cookies）才能访问的内容，遇到直接报错终止，不引导用户提供 cookies
- 不做站点白名单等技术层面的使用限制，仅在 SKILL.md 中做使用范围声明
- 不在 Step 4 查询格式失败时臆测原因强行重试，如实报告 yt-dlp 的错误信息
- 不跳过 Step 4 的格式选择直接下载"最佳画质"，必须让用户从实际可用列表中选择
- 不在下载完成后自动调用 trim/resize/compress/framerate 做后续处理，也不写入组合请求编排链条
