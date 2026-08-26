# media-trim

> 版本：1.1.3 | 分类：tool

从音视频文件中截取指定时间段，默认流复制快速截取，提供帧精确的重新编码模式作为备选。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim（本 skill）、media-play、media-framerate、media-convert
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
Step 0  需求预告：一次性列出缺失信息并询问（信息已齐全则跳过）
   ↓
Step 1  确认 ffmpeg 环境可用（依赖检查）
   ↓
Step 2  校验输入文件是否存在（输入参数检查）
   ↓
Step 3  确认输出路径与截取模式 🔴 CHECKPOINT + 校验输出目录可写（输出参数检查）
   ↓
Step 4  执行前校验：起止时间是否超过视频总时长（运行条件检查，硬约束直接终止）
   ↓
Step 5  执行截取
         ├─ 快速模式：-ss/-to 在 -i 之前 + -c copy
         └─ 精确模式：-ss/-to 在 -i 之后 + 重新编码
```

## 产出物数据流

输入文件 + 起止时间点 → 本 skill → 指定路径下的截取片段文件 → 人工接手；Step4 执行前校验主动调用 media-analyze 查询总时长，超出范围直接终止任务。

## Skill 依赖关系图

```
用户 ──触发──▶ media-trim ──引用──▶ media-ffmpeg-common/REFERENCE.md
                               └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                               └──▶ media-ffmpeg-common/INSTALL.md
media-trim ──调用（Step4 执行前校验）──▶ media-analyze
```

Step4 执行前校验中主动调用 media-analyze 的 ffprobe 命令查询总时长，构成实际调用依赖。
