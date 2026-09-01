# media-compress

> 版本：1.2.4 | 分类：tool

在不改变分辨率的前提下压缩音视频文件体积，支持 CRF 画质因子模式与两轮编码目标码率模式，二选一。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress（本 skill）、media-trim、media-play、media-framerate、media-convert
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

压缩视频、压缩音频、音视频压缩、减小文件体积、CRF调画质、压缩到指定大小、压缩到多少MB。

## 业务逻辑流程图

```
Step 0-3  前置校验（引用 media-ffmpeg-common/PREFLIGHT.md）
          需求预告 → ffmpeg 环境 → 输入文件存在 → 输出路径 🔴 CHECKPOINT
          （输出路径校验含：父目录可写 + 输出路径 ≠ 输入路径）
   ↓
Step 4  确定压缩模式与参数
         ├─ CRF 模式（默认）：按用户描述映射 CRF 取值
         └─ 目标码率模式（用户指定体积时）：
             🔴 CHECKPOINT 提示 CRF 画质通常更优，确认后
             调用 media-analyze 查询时长 → 计算目标视频码率
             （硬约束：码率 ≤ 0 直接终止）
   ↓
Step 5  执行压缩
         ├─ CRF 模式：ffmpeg -y -crf <取值> -preset medium
         └─ 目标码率模式：两轮编码 -pass 1 → -pass 2（两轮均带 -y）
```

## 产出物数据流

输入文件 + 画质偏好描述或目标体积 → 本 skill → 指定路径下体积更小的音视频文件 → 人工接手；目标码率模式下 Step4 主动调用 media-analyze 查询时长以计算码率。

## Skill 依赖关系图

```
用户 ──触发──▶ media-compress ──引用──▶ media-ffmpeg-common/PREFLIGHT.md（Step 0-3）
                                    └──▶ media-ffmpeg-common/REFERENCE.md
                                    └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                    └──▶ media-ffmpeg-common/INSTALL.md
media-compress ──调用（Step4 目标码率模式计算）──▶ media-analyze
```

Step4 目标码率模式下主动调用 media-analyze 的 ffprobe 命令查询视频总时长，构成实际调用依赖；CRF 模式无此依赖。
