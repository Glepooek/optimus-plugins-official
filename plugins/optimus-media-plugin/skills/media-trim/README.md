# media-trim

> 版本：1.0.1 | 分类：tool

从音视频文件中截取指定时间段，默认流复制快速截取，提供帧精确的重新编码模式作为备选。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

片段截取、截取视频、剪切一段、掐头去尾、截取某个时间段。

## 业务逻辑流程图

```
Step 1  确认 ffmpeg 环境可用
   ↓
Step 2  确认输出路径与截取模式（默认快速）
   ↓
Step 3  执行截取
         ├─ 快速模式：-ss/-to 在 -i 之前 + -c copy
         └─ 精确模式：-ss/-to 在 -i 之后 + 重新编码
```

## 产出物数据流

输入文件 + 起止时间点 → 本 skill → 指定路径下的截取片段文件 → 人工接手；起始时间超过总时长时提示用户参考 media-analyze 的输出核对时长。

## Skill 依赖关系图

```
用户 ──触发──▶ media-trim ──引用──▶ media-ffmpeg-common/REFERENCE.md
                               └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                               └──▶ media-ffmpeg-common/INSTALL.md
失败处理提示用户参考 media-analyze 的时长输出（非调用依赖）
```
