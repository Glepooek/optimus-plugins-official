# media-convert

> 版本：1.0.0 | 分类：tool

将单个音视频文件转换到指定容器格式（如 mp4↔mov↔mkv↔avi），默认流复制（remux）不重新编码，目标容器不支持源编码时经用户确认后降级为转码。

## 所处层级

```
┌─────────────┐
│  platform    │
├─────────────┤
│★ tool        │  media-analyze、media-resize、media-compress、media-trim、media-play、media-framerate、media-convert（本 skill）
├─────────────┤
│  quality     │
├─────────────┤
│  generator   │
├─────────────┤
│  workflow    │
└─────────────┘
```

## 触发词

格式转换、转成mp4、转成mov、转换容器、mp4转mkv、avi转mp4、换个格式。

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
Step 4  执行转换
         ├─ 默认 remux 模式：-c copy，成功则任务完成
         └─ remux 失败（编码与目标容器不兼容）🔴 CHECKPOINT → 用户确认后降级为转码模式
```

## 产出物数据流

输入文件 + 目标格式 → 本 skill → 指定路径下转换后的文件 → 人工接手；组合请求场景中位于 `trim → resize → framerate → compress → convert` 顺序末位，可作为其他 media-* skill 产出的中间文件的最终收尾环节。

## Skill 依赖关系图

```
用户 ──触发──▶ media-convert ──引用──▶ media-ffmpeg-common/REFERENCE.md
                                  └──▶ media-ffmpeg-common/CLI-REFERENCE.md
                                  └──▶ media-ffmpeg-common/INSTALL.md
```

不主动调用 media-analyze——remux 是否可行由 ffmpeg 实际执行结果驱动判断，不依赖预先查询编码信息。
