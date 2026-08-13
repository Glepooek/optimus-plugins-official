# Changelog

## [1.1.0] - 2026-08-13

### Added
- 新增 Step 0"需求预告"：处理请求第一步对比 skill 所需信息与用户已提供信息，一次性列出缺失项统一询问；输入/输出路径缺失则询问，CRF 偏好有默认值不阻塞；ffmpeg 依赖不参与本环节比对，由 Step 1 实际检测
- 新增 Step"校验输入文件"（输入参数检查）：输入路径不存在时报错终止
- "确认输出路径"步骤标记 🔴 CHECKPOINT 用于确认输出路径；同时新增输出目录可写校验（输出参数检查，目录不存在或不可写时报错终止，输出文件本身此刻不存在不视为失败）
- Step 1 环境检测明确失败时的报错终止行为
- 新增"不要做什么"章节，列出 4 条对应依赖/输入/输出硬约束检查的反例

### Changed
- 遵循 `.claude/rules/skill-authoring.md` 的"执行前置校验"规范，Step 编号整体调整：新增 Step0/Step2，原 Step2（输出路径）→ Step3，原 Step3（CRF取值）→ Step4，原 Step4（执行压缩）→ Step5

## [1.0.1] - 2026-08-13

### Added
- 失败处理章节新增组合请求边界说明，指向 `media-ffmpeg-common/REFERENCE.md` 的"组合请求处理约定"

## [1.0.0] - 2026-08-12

### Added
- 新增 media-compress skill：基于 ffmpeg CRF 模式压缩音视频体积，提供口语化描述到 CRF 数值的映射表
