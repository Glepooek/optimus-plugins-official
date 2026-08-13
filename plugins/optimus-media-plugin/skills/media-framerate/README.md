# media-framerate

> 版本：1.0.0 | 分类：tool

将单个视频文件转换到指定帧率，提高帧率时可选简单复制帧或运动补偿插帧两种模式。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、media-framerate（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

帧率转换、改帧率、转帧率、60fps转30fps、提高帧率、降低帧率、补帧。

## 业务逻辑流程图

```
Step 0  需求预告：一次性列出缺失信息并询问（信息已齐全则跳过）
   ↓
Step 1  确认 ffmpeg 环境可用（依赖检查）
   ↓
Step 2  校验输入文件是否存在（输入参数检查）
   ↓
Step 3  确认输出路径 🔴 CHECKPOINT + 校验输出目录可写（输出参数检查）
   ↓
Step 4  执行前校验：提高帧率时确认简单复制/运动插帧模式选择 🔴 CHECKPOINT（运行条件检查，可协商风险）
   ↓
Step 5  执行转换
         ├─ 简单复制：-r <目标帧率>
         └─ 运动插帧：-filter:v minterpolate=fps=<目标帧率>
```

## 产出物数据流

输入文件 + 目标帧率 → 本 skill → 指定路径下的帧率转换后文件 → 人工接手；Step4 执行前校验主动调用 media-analyze 查询原始帧率，判断提高/降低场景。

## Skill 依赖关系图

```
用户 ──触发──▶ media-framerate ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                └──▶ media-ffmpeg-common/INSTALL.md
media-framerate ──调用（Step4 执行前校验）──▶ media-analyze
```

Step4 执行前校验中主动调用 media-analyze 的 ffprobe 命令查询原始帧率，构成实际调用依赖。
