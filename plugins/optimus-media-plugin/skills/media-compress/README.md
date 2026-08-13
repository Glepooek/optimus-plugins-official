# media-compress

> 版本：1.1.0 | 分类：tool

在不改变分辨率的前提下压缩音视频文件体积，使用 CRF 画质因子控制压缩程度。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress（本 skill）、media-trim
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质。

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
Step 4  按用户描述映射 CRF 取值
   ↓
Step 5  执行 ffmpeg -crf <取值> -preset medium
```

## 产出物数据流

输入文件 + 画质偏好描述 → 本 skill → 指定路径下体积更小的音视频文件 → 人工接手。

## Skill 依赖关系图

```
用户 ──触发──▶ media-compress ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                    └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                    └──▶ media-ffmpeg-common/INSTALL.md
```

不被其他 skill 调度，无上下游依赖，独立使用。
