# media-play

> 版本：1.0.0 | 分类：tool

使用 ffplay 播放单个音视频文件，弹出独立播放窗口，不产出任何文件。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play（本 skill）、media-framerate
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

播放视频、播放音频、预览一下这个视频、听一下这段音频、ffplay。

## 业务逻辑流程图

```
Step 0  需求预告：一次性列出缺失信息并询问（信息已齐全则跳过）
   ↓
Step 1  确认 ffplay 环境可用（依赖检查，独立检测，不复用 ffmpeg/ffprobe 检测）
   ↓
Step 2  校验输入文件是否存在（输入参数检查）
   ↓
Step 3  执行播放：后台非阻塞启动 ffplay，播放结束自动关闭窗口
```

## 产出物数据流

输入文件路径 → 本 skill → 弹出的播放窗口（无文件产出）→ 人工观看/收听后手动关闭或等待自动退出。

## Skill 依赖关系图

```
用户 ──触发──▶ media-play ──引用──▶ media-ffmpeg-common/REFERENCE.md
                            └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                            └──▶ media-ffmpeg-common/INSTALL.md
```

本 skill 为只读终态操作，不参与 media-ffmpeg-common/REFERENCE.md 的"组合请求处理约定"顺序编排，可在 trim/resize/compress 组合流程的任意步骤后按需调用以预览效果。
